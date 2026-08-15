#!/bin/bash
# Labelled contact sheet off a chunk render. Every fix in the film's round 2 came out
# of one of these: the gates cannot see an element that never enters frame, a clipped
# label, a dead cover or a caption sitting on a chin.
#
#   ./qa.sh s1 r1 0 27 78 ...        # FRAME NUMBERS, local to the chunk
#
# FRAME NUMBERS, NOT SECONDS, AND ONE DECODE PASS. `ffmpeg -ss T -i F` fast-seeks to
# the nearest keyframe and decodes forward, which on a -g 15 stream can hand back a
# neighbouring frame and invent scene-bleed bugs that are not in the file. So this
# decodes the clip ONCE and pulls the exact frames with a select expression.
#
# Overlays the safe-zone lines the deliverable has to respect, because an overlay's
# extents must be audited on EVERY round, not once per project. The green line at
# y1000 is the face band's foot; the cyan pair is the graphics zone.
set -euo pipefail
cd "$(dirname "$0")"
C=$1; TAG=$2; shift 2
F=$(ls -t "$C"/renders/*.mp4 | head -1)
S=/private/tmp/reel-factory-scratch/short/qa-$C-$TAG
rm -rf "$S"; mkdir -p "$S"
echo "source $(basename "$F")"

SEL=""
for n in "$@"; do
  [ -n "$SEL" ] && SEL="$SEL+"
  SEL="${SEL}eq(n\,$n)"
done

ffmpeg -v error -i "$F" -vf "select='$SEL',\
drawbox=y=150:h=2:w=1080:color=cyan@0.45:t=fill,\
drawbox=y=1000:h=2:w=1080:color=lime@0.75:t=fill,\
drawbox=y=1040:h=2:w=1080:color=cyan@0.35:t=fill,\
drawbox=y=1380:h=2:w=1080:color=cyan@0.35:t=fill,\
drawbox=y=1396:h=2:w=1080:color=yellow@0.45:t=fill,\
drawbox=y=1600:h=3:w=1080:color=red@0.75:t=fill,\
drawbox=x=960:y=900:w=3:h=700:color=red@0.55:t=fill,\
drawbox=x=60:y=0:w=2:h=1920:color=cyan@0.30:t=fill,\
scale=440:-1" -vsync 0 -y "$S/f_%02d.jpg"

# label each frame with its own number, in the order they were requested
i=0
for n in "$@"; do
  i=$((i+1)); p=$(printf "%s/f_%02d.jpg" "$S" $i)
  [ -f "$p" ] || { echo "MISSING frame $n"; continue; }
  ffmpeg -v error -i "$p" -vf "drawtext=text='$C f$n':fontsize=22:fontcolor=yellow:\
x=8:y=h-30:box=1:boxcolor=black@0.7:boxborderw=5" -y "${p%.jpg}_l.jpg"
  mv "${p%.jpg}_l.jpg" "$p"
done

ffmpeg -v error -pattern_type glob -i "$S/f_*.jpg" \
  -filter_complex "tile=layout=4x$(( (i+3)/4 )):margin=6:padding=6:color=#0d0d12" \
  -frames:v 1 -y "$S/sheet.jpg"
echo "$S/sheet.jpg   ($i frames)"
