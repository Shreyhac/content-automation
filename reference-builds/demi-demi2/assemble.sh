#!/usr/bin/env bash
# Concatenate the eight chunk renders losslessly and mux the audio bed.
#
#   ./assemble.sh                -> renders/demi2-final.mp4
#
# LOSSLESS: every chunk was rendered by the same encoder at the same settings,
# resolution and frame rate, so `-c copy` re-containers them without touching a
# single pixel. That is the whole payoff of frame-exact boundaries.
#
# THE AUDIO IS NEVER CONCATENATED. bed.wav is one continuous 36.40s mix (his VO
# at unity gain + music + SFX, built by build_audio.py) laid over the finished
# picture in one pass, so none of the seven joins can produce an AAC priming gap
# or a click. This is vid44's rule and it is not negotiable.
#
# FRESHNESS: a frame-total assert alone does NOT prove a render is current --
# hf46 assembled a stale film with a correct frame count and a clean exit. Each
# chunk's render mtime is compared against its index.html mtime.
set -euo pipefail
cd "$(dirname "$0")"

CHUNKS=(c1 c2 c3 c4 c5 c6 c7 c8)
OUT="renders/demi2-final.mp4"
LIST="renders/.concat.txt"
mkdir -p renders
: > "$LIST"

echo "chunk  frames  planned  fresh  bitrate"
total=0
for c in "${CHUNKS[@]}"; do
  f=$(ls -t "$c"/renders/*.mp4 2>/dev/null | head -1) || true
  [ -n "${f:-}" ] || { echo "!! $c has no render"; exit 1; }

  # freshness: the render must be NEWER than the composition it came from
  if [ "$c/index.html" -nt "$f" ]; then
    echo "!! $c/index.html is newer than its render -- re-render $c"; exit 1
  fi

  n=$(ffprobe -v error -count_frames -select_streams v \
        -show_entries stream=nb_read_frames -of csv=p=0 "$f")
  want=$(python3 -c "import json,sys;p=json.load(open('chunks.json'));print(next(x['nframes'] for x in p if x['name']=='$c'))")
  [ "$n" = "$want" ] || { echo "!! $c rendered $n frames, planned $want"; exit 1; }

  br=$(ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of csv=p=0 "$f")
  printf "%-6s %-7s %-8s %-6s %.1f Mbps\n" "$c" "$n" "$want" "ok" "$(awk -v b="$br" 'BEGIN{print b/1e6}')"
  echo "file '$PWD/$f'" >> "$LIST"
  total=$((total + n))
done

echo
echo "total $total frames"
[ "$total" -eq 1133 ] || { echo "!! expected 1133 frames"; exit 1; }

# ── lossless concat ─────────────────────────────────────────────────────
ffmpeg -v error -y -f concat -safe 0 -i "$LIST" -c copy renders/.picture.mp4
pn=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 renders/.picture.mp4)
[ "$pn" -eq 1133 ] || { echo "!! concat produced $pn frames, not 1133"; exit 1; }

# ── mux the one continuous bed ──────────────────────────────────────────
[ -f bed.wav ] || { echo "!! bed.wav missing -- run build_audio.sh"; exit 1; }
ffmpeg -v error -y -i renders/.picture.mp4 -i bed.wav \
  -c:v copy -c:a aac -b:a 320k -ar 48000 -ac 2 -shortest \
  -movflags +faststart "$OUT"
rm -f renders/.picture.mp4 "$LIST"

# ── verify the DELIVERABLE, not the intent ──────────────────────────────
echo
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,nb_frames,bit_rate \
  -show_entries format=duration,size -of default=nw=1 "$OUT"
echo
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 "$OUT"
echo
echo "-> $OUT"
