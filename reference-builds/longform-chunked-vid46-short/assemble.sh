#!/bin/bash
# Concatenate the two chunk renders, lay the VO under the rendered SFX bed, and
# write the deliverable.
#
# It ASSERTS the frame total before it will concatenate. On the film, a chunk that
# had silently not re-rendered produced a film that was the right length but the
# wrong content, and nothing downstream noticed.
set -euo pipefail
cd "$(dirname "$0")"
BASE="$PWD"
OUT=../out
mkdir -p "$OUT"
WANT=1350
S=/private/tmp/reel-factory-scratch/short
mkdir -p "$S"

: > "$S/cat.txt"
tot=0
for c in s1 s2; do
  f=$(ls -t "$BASE/$c"/renders/*.mp4 2>/dev/null | head -1) || true
  [ -n "${f:-}" ] || { echo "no render for $c"; exit 1; }
  n=$(ffprobe -v error -count_frames -select_streams v \
        -show_entries stream=nb_read_frames -of csv=p=0 "$f")
  age=$(( $(date +%s) - $(stat -f %m "$f") ))
  printf "  %s  %5s frames  %6ss old  %s\n" "$c" "$n" "$age" "$(basename "$f")"
  echo "file '$f'" >> "$S/cat.txt"
  tot=$((tot + n))
done
echo "total $tot frames (want $WANT)"
[ "$tot" = "$WANT" ] && echo "  frame count OK" || { echo "  FRAME COUNT MISMATCH"; exit 1; }

# video + the rendered SFX bed, stream-copied: both chunks share one encode setting
ffmpeg -v error -f concat -safe 0 -i "$S/cat.txt" -c copy -y "$S/video.mp4"

# the VO sits under the bed. The bed comes from the render (so it matches the picture
# frame for frame); the VO is the spliced master. Mix, then two-pass loudnorm to the
# platform spec, so the short lands at the same loudness as the film.
ffmpeg -v error -i "$S/video.mp4" -i assets/vo.wav \
  -filter_complex "[0:a]volume=1.0[bed];[1:a]volume=1.0[vo];\
[vo][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mx]" \
  -map 0:v -map "[mx]" -c:v copy -c:a pcm_s16le -y "$S/mixed.wav.mp4"

M=$(ffmpeg -v info -i "$S/mixed.wav.mp4" -af \
      loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json -f null - 2>&1 \
    | python3 -c "import sys,json;s=sys.stdin.read();print(json.dumps(json.loads(s[s.rindex('{'):s.rindex('}')+1])))")
echo "  pass 1: $M"
read -r I TP LRA TH OFF <<<"$(python3 -c "
import json,sys
j=json.loads('''$M''')
print(j['input_i'],j['input_tp'],j['input_lra'],j['input_thresh'],j['target_offset'])")"

ffmpeg -v error -i "$S/mixed.wav.mp4" \
  -af "loudnorm=I=-14:TP=-1.0:LRA=9:linear=true:measured_I=$I:measured_TP=$TP:\
measured_LRA=$LRA:measured_thresh=$TH:offset=$OFF" \
  -map 0:v -map 0:a -c:v copy -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -y "$OUT/vid46-short.mp4"

cp captions.srt "$OUT/vid46-short.srt"

echo
ffprobe -v error -count_frames -select_streams v \
  -show_entries stream=nb_read_frames,width,height,r_frame_rate \
  -show_entries format=duration,size -of default=nw=1 "$OUT/vid46-short.mp4"
ffmpeg -v error -i "$OUT/vid46-short.mp4" -af \
  ebur128=framelog=quiet -f null - 2>&1 | tail -6
echo "wrote $OUT/vid46-short.mp4 and $OUT/vid46-short.srt"
