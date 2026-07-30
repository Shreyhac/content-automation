#!/bin/bash
# Build a QA preview of one chunk WITH THE VOICEOVER IN IT.
#
# Judging a chunk silent is how the c1 review missed that the SFX bed was thin
# (mean -36 dB across 30s). Every QA pass from here on gets the real VO under the
# picture, at delivery loudness, so beats can be heard landing on their words.
#
#   ./preview.sh c3 60.966667 [outname]
#
# The chunk render carries the SFX bed only; the voice comes from the one
# continuous cleaned master, sliced to this chunk's absolute span.
set -euo pipefail
cd "$(dirname "$0")"

C="$1"; T0="$2"; OUT="${3:-../out/vid46-$C-preview.mp4}"
SRC=$(ls -t "$C"/renders/*.mp4 | head -1)
DUR=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$SRC")
SECS=$(awk -v d="$DUR" 'BEGIN{printf "%.6f", d/30}')
echo "  $C: $SRC  ${DUR}f  ${SECS}s  vo@${T0}"

W=".preview_$C"
mkdir -p "$W" ../out

# The bed comes from sfx.py via build_bed.py, NOT from this render's audio track, for
# the same reason assemble.sh stopped using it: the render may predate the current cue
# list, and then the preview would sound like a film that is not being delivered.
BED=.assembly/sfx.wav
if [ ! -s "$BED" ] || [ sfx.py -nt "$BED" ]; then
  python3 build_bed.py "$BED" >/dev/null
fi
ffmpeg -y -nostdin -ss "$T0" -t "$SECS" -i "$BED" -ac 2 -ar 48000 \
  -c:a pcm_s16le "$W/sfx.wav" -loglevel error

ffmpeg -y -ss "$T0" -t "$SECS" -i assets/vo-master.wav -i "$W/sfx.wav" \
  -filter_complex "[0:a]asetpts=PTS-STARTPTS[vo]; \
                   [1:a]asetpts=PTS-STARTPTS[sx]; \
                   [vo][sx]amix=inputs=2:duration=first:dropout_transition=0:weights='1 0.9'[m]; \
                   [m]loudnorm=I=-14:TP=-1.0:LRA=9[out]" \
  -map "[out]" -c:a pcm_s16le "$W/mix.wav" -loglevel error

ffmpeg -y -i "$SRC" -i "$W/mix.wav" -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart -shortest \
  "$OUT" -loglevel error

echo "  -> $OUT"
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height \
  -of default=noprint_wrappers=1 "$OUT" | head -8
# what the SFX bed actually measures, so "the bed is thin" is a number not a feeling
echo -n "  sfx bed mean/peak: "
ffmpeg -i "$W/sfx.wav" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume" | tr '\n' ' '
echo
