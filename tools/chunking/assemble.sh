#!/bin/bash
# vid46 final assembly — Incogni x Nader, 8 chunks, 6702 frames @ 3840x2160/30.
#
# ROUND 2: the re-cut dropped the two duplicated takes (91.30-95.46 and
# 124.88-136.58 in the original master), so the film is 493 frames shorter than
# round 1 and every boundary moved. See recut.sh and recut/chunks.json.
#
# Video: the 8 chunk renders concatenate with -c copy (identical encoder settings,
#        every chunk starts on a keyframe) — zero generational loss.
# Audio: rebuilt, never concatenated. The chunk renders carry ONLY the SFX bed;
#        the voice comes from one continuous cleaned master, so none of the 7
#        joins can produce an AAC priming gap or a click on the VO.
set -euo pipefail
cd "$(dirname "$0")"

OUT=../out/vid46-final.mp4
WORK=.assembly
EXPECT=6702
CHUNKS="c1 c2 c3 c4 c5 c6 c7 c8"

mkdir -p "$WORK" ../out
rm -f "$WORK"/*.wav "$WORK"/list.txt "$WORK"/sfxlist.txt "$WORK"/video.mp4

echo "--- 1. verify chunk renders ---"
TOTAL=0
for c in $CHUNKS; do
  f=$(ls -t "$c"/renders/*.mp4 2>/dev/null | head -1 || true)
  [ -n "$f" ] && [ -s "$f" ] || { echo "MISSING render for $c"; exit 1; }
  n=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$f")
  w=$(ffprobe -v error -select_streams v -show_entries stream=width -of csv=p=0 "$f")
  printf "  %-3s %5s frames  %spx  %s\n" "$c" "$n" "$w" "$(basename "$f")"
  TOTAL=$((TOTAL+n))
  echo "file '$PWD/$f'" >> "$WORK/list.txt"
done
echo "  total: $TOTAL frames (planned $EXPECT)"
# The chunk boundaries are the contract with the VO master. vid44 shipped +4.1s
# of drift because nobody asserted this, and -shortest then cut the end card off.
[ "$TOTAL" -eq "$EXPECT" ] || { echo "  !! FRAME TOTAL MISMATCH — refusing to assemble"; exit 1; }

echo "--- 2. concat video (stream copy) ---"
ffmpeg -y -f concat -safe 0 -i "$WORK/list.txt" -c:v copy -an "$WORK/video.mp4" -loglevel error
ffprobe -v error -count_frames -select_streams v \
  -show_entries stream=nb_read_frames,width,height -of csv=p=0 "$WORK/video.mp4"

echo "--- 3. build the SFX bed from sfx.py (NOT from the chunk renders) ---"
# This used to lift the audio track out of each chunk render and concatenate it,
# which coupled the bed to the picture: one volume change meant re-rendering 4K
# video to hear it. build_bed.py lays the same CUES dict sfx.py injects into the
# chunks onto one continuous timeline instead, so SFX iteration costs seconds and
# cannot drift from the injected version. Verified against a chunk render's own
# audio track: mean within 0.1 dB, peak identical.
python3 build_bed.py "$WORK/sfx.wav"
BEDSECS=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/sfx.wav")
WANT=$(awk -v d="$EXPECT" 'BEGIN{printf "%.3f", d/30}')
awk -v a="$BEDSECS" -v b="$WANT" 'BEGIN{exit (a-b<0.002 && b-a<0.002) ? 0 : 1}' \
  || { echo "  !! bed is ${BEDSECS}s, picture is ${WANT}s — refusing to assemble"; exit 1; }
echo -n "  sfx bed: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/sfx.wav")s  "
ffmpeg -i "$WORK/sfx.wav" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume" | tr '\n' ' '
echo

echo "--- 4. mix the continuous VO under the bed, master for YouTube ---"
DUR=$(awk -v d="$EXPECT" 'BEGIN{printf "%.6f", d/30}')
ffmpeg -y -i assets/vo-master.wav -i "$WORK/sfx.wav" \
  -filter_complex "[0:a]atrim=0:$DUR,asetpts=PTS-STARTPTS[vo]; \
                   [1:a]atrim=0:$DUR,asetpts=PTS-STARTPTS[sx]; \
                   [vo][sx]amix=inputs=2:duration=first:dropout_transition=0:weights='1 0.9'[m]; \
                   [m]loudnorm=I=-14:TP=-1.0:LRA=9[out]" \
  -map "[out]" -c:a pcm_s16le "$WORK/mix.wav" -loglevel error
echo "  mix: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/mix.wav")s"

echo "--- 5. mux ---"
ffmpeg -y -i "$WORK/video.mp4" -i "$WORK/mix.wav" \
  -c:v copy -c:a aac -b:a 320k -ar 48000 -ac 2 \
  -movflags +faststart -shortest "$OUT" -loglevel error

echo "--- done ---"
ffprobe -v error -show_entries format=duration,size,bit_rate \
  -show_entries stream=codec_name,width,height,r_frame_rate,channels \
  -of default=noprint_wrappers=1 "$OUT"
echo -n "  delivered loudness: "
ffmpeg -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | tail -12 | grep -E "I:|LRA:|Peak:" | tr '\n' ' '
echo
