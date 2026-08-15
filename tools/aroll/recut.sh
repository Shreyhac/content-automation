#!/bin/bash
# vid46 ROUND 2, the A-roll re-cut.
#
# The owner reversed the round-1 "keep both takes" decision, so the two duplicated
# passages come out. Both splices are expressed in ORIGINAL frame numbers on the
# 30fps grid, so nothing here depends on float seconds surviving a seek:
#
#   cut A  frames 2733-2869  (91.100000 - 95.666667)  Aura coverage, take 2
#   cut B  frames 3743-4098  (124.766667 - 136.633333) Incogni focus, take 1
#          137 + 356 = 493 frames removed -> 7195 - 493 = 6702 frames = 223.400s
#
# Both splice points sit inside note-reading runs (down_runs 85.4-91.0 and
# 127.4-136.6), so the face is hidden across both joins and neither can show as a
# jump cut. That is why these particular in/out points were chosen over tighter ones.
#
# Each splice keeps a slice of the real room silence on both sides, so the joined
# sentence break has the pacing he actually spoke:
#   A: 0.30s after "sites." + 0.21s before "So"   = 0.51s
#   B: 0.13s after "need."  + 0.11s before "Now," = 0.24s (the original was 0.24s)
set -euo pipefail
cd "$(dirname "$0")"

SRC="/Volumes/Shreyansh/nader new video/incogni edited.mp4"
[ -f "$SRC" ] || { echo "master not mounted: $SRC"; exit 1; }

# keep-ranges in original frames / seconds
A_OUT_F=2733; A_IN_F=2870
B_OUT_F=3743; B_IN_F=4099
A_OUT=91.100000; A_IN=95.666667
B_OUT=124.766667; B_IN=136.633333

VSEL="not(between(n,${A_OUT_F},$((A_IN_F-1))))*not(between(n,${B_OUT_F},$((B_IN_F-1))))"
ATRIM="[0:a]atrim=end=${A_OUT},asetpts=N/SR/TB[a0];\
[0:a]atrim=start=${A_IN}:end=${B_OUT},asetpts=N/SR/TB[a1];\
[0:a]atrim=start=${B_IN},asetpts=N/SR/TB[a2];\
[a0][a1][a2]concat=n=3:v=0:a=1[ac]"

mkdir -p recut

case "${1:-all}" in

audio)
  # 1. the cleaned VO master, spliced. Sample-accurate atrim, not packet-level
  #    aselect, a 21ms packet rounding at each join would drift the whole film.
  echo "--- spliced VO master ---"
  ffmpeg -y -nostdin -v error -i "$SRC" -filter_complex \
    "${ATRIM};[ac]highpass=f=75,afftdn=nr=14:nf=-28:tn=1,adeclick,aresample=48000[out]" \
    -map "[out]" -vn -ac 1 -c:a pcm_s16le recut/vo-master.wav
  # INSTALL it: assemble.sh and preview.sh both read assets/vo-master.wav, and leaving
  # the previous cut's master sitting there is a silent, film-length A/V desync.
  cp recut/vo-master.wav assets/vo-master.wav
  ffprobe -v error -show_entries format=duration -of csv=p=0 assets/vo-master.wav
  ;;

frames)
  # 2. 5fps stills off the SPLICED video, for the Vision detectors. Extracted with
  #    the same frame-select expression, so the gaze/box/crown maps are measured on
  #    exactly the footage that ships, no remapping of the round-1 CSVs, which
  #    would have had to resample a 5fps signal across two non-multiple-of-6 cuts.
  echo "--- 5fps detection stills ---"
  rm -rf recut/frames5; mkdir -p recut/frames5
  ffmpeg -y -nostdin -v error -i "$SRC" \
    -vf "select='${VSEL}',setpts=N/FRAME_RATE/TB,fps=5,scale=1280:-1" \
    -q:v 3 recut/frames5/f_%05d.jpg
  ls recut/frames5 | wc -l
  ;;

video)
  # 3. the 8 chunk videos, cut straight from the original master. Building an
  #    intermediate spliced master first would cost a second full 4K encode and a
  #    generation of quality for nothing.
  #
  #    Each chunk resolves to one or two ORIGINAL frame runs. Only c4 and c5 span a
  #    splice (cut A lands at new frame 2733, cut B at new frame 3606); the other six
  #    are contiguous. Runs are seeked with -ss BEFORE -i so ffmpeg does not decode
  #    the whole 1GB HEVC master once per chunk, and cut to an exact frame count with
  #    -frames:v so the boundary contract with the VO master cannot drift.
  #
  #    Boundaries come from chunks.txt (name:new_start:new_end), written by
  #    plan_chunks.py after the new transcript lands.
  [ -f recut/chunks.txt ] || { echo "recut/chunks.txt missing - run plan_chunks.py"; exit 1; }
  mkdir -p assets/aroll recut/seg
  echo "--- chunk videos ---"
  while IFS=: read -r name a b; do
    [ -n "$name" ] || continue
    want=$((b-a))
    python3 - "$a" "$b" > recut/_runs.txt <<'PY'
import sys
A_OUT, A_LEN = 2733, 137
B_OUT_NEW    = 3743 - 137        # cut B out-point, expressed in NEW frames
B_LEN        = 356
a, b = int(sys.argv[1]), int(sys.argv[2])
def o(n):                        # new frame -> original frame
    if n < A_OUT:     return n
    if n < B_OUT_NEW: return n + A_LEN
    return n + A_LEN + B_LEN
runs, s, prev = [], o(a), o(a)
for n in range(a + 1, b):
    c = o(n)
    if c != prev + 1:
        runs.append((s, prev - s + 1)); s = c
    prev = c
runs.append((s, prev - s + 1))
for st, ct in runs: print(f"{st}:{ct}")
PY
    nruns=$(wc -l < recut/_runs.txt | tr -d " ")
    if [ "$nruns" = "1" ]; then
      IFS=: read -r st ct < recut/_runs.txt
      ss=$(awk -v f="$st" 'BEGIN{printf "%.6f", f/30}')
      ffmpeg -y -nostdin -v error -ss "$ss" -i "$SRC" -frames:v "$ct" \
        -vf "scale=3840:2160,setsar=1" -an -r 30 \
        -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p \
        -g 15 -keyint_min 15 -movflags +faststart "assets/aroll/${name}.mp4"
    else
      # spliced chunk: encode each run then concat. Identical encoder settings on
      # both sides, so the concat is a stream copy and the join is a keyframe cut.
      rm -f recut/seg/list.txt
      k=0
      while IFS=: read -r st ct; do
        k=$((k+1))
        ss=$(awk -v f="$st" 'BEGIN{printf "%.6f", f/30}')
        ffmpeg -y -nostdin -v error -ss "$ss" -i "$SRC" -frames:v "$ct" \
          -vf "scale=3840:2160,setsar=1" -an -r 30 \
          -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p \
          -g 15 -keyint_min 15 -movflags +faststart "recut/seg/${name}_$k.mp4"
        echo "file '$PWD/recut/seg/${name}_$k.mp4'" >> recut/seg/list.txt
        printf "     run %d: orig f%s +%s frames\n" "$k" "$st" "$ct"
      done < recut/_runs.txt
      ffmpeg -y -nostdin -v error -f concat -safe 0 -i recut/seg/list.txt \
        -c copy "assets/aroll/${name}.mp4"
    fi
    n=$(ffprobe -v error -count_frames -select_streams v \
        -show_entries stream=nb_read_frames -of csv=p=0 "assets/aroll/${name}.mp4")
    printf "  %-3s frames %4s (want %4s) runs %s  %s\n" "$name" "$n" "$want" "$nruns" \
      "$(du -h "assets/aroll/${name}.mp4" | cut -f1)"
    [ "$n" -eq "$want" ] || { echo "  !! frame count mismatch on $name"; exit 1; }
  done < recut/chunks.txt
  ;;

all) "$0" audio; "$0" frames ;;
esac
