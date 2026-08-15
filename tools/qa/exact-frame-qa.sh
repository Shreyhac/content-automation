#!/bin/bash
# vid47 frame QA, EXACT frames.
# `-ss` before `-i` fast-seeks to a keyframe and silently hands back a frame up
# to half a GOP early, which in round 2 looked exactly like a scene-bleed bug.
# A single decode pass with a select expression is exact and only costs seconds.
set -e
V="$1"; OUT="$2"; mkdir -p "$OUT"; rm -f "$OUT"/*.png
FRAMES="$3"   # comma-separated frame numbers
EXPR=$(python3 -c "import sys;print('+'.join('eq(n\,%s)'%f for f in sys.argv[1].split(',')))" "$FRAMES")
ffmpeg -y -v error -i "$V" -vf "select='$EXPR'" -vsync 0 "$OUT/f%03d.png"
python3 - "$OUT" "$FRAMES" <<'PY'
import os,sys
out,fr=sys.argv[1],sys.argv[2].split(',')
got=sorted(f for f in os.listdir(out) if f.endswith('.png'))
for i,f in enumerate(got):
    if i < len(fr):
        os.rename(os.path.join(out,f), os.path.join(out,'x%03d_n%s_t%.2f.png'%(i,fr[i],int(fr[i])/30.0)))
print(len(got),"frames")
PY
