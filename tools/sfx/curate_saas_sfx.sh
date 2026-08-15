#!/bin/bash
# vid46, fold the owner's "saas sfx" pack into the curated pool (2026-07-30).
#
# 17 new files, supplied mid-round. They arrive at peaks between -2.3 and -19.8 dBFS,
# so they get exactly the treatment the rest of the pool got: leading silence trimmed
# (a late transient reads as a missed hit) and normalised, so one `data-volume` number
# means the same loudness for every file in the film.
#
# Names are assigned from MEASURED character, not from the source filenames, half of
# them were just "sfx 4.mp3". Band energy and envelope shape were measured per file:
#   low-dominant + fast decay -> impact      rising envelope -> riser
#   high-dominant + fast decay -> click      flat + long     -> sustained texture
# The `s` prefix marks the provenance so the pack stays identifiable in sfx.py.
set -euo pipefail
cd "$(dirname "$0")"

SRC="../saas sfx"
OUT=assets/sfx
mkdir -p "$OUT"

copy() {
  local name="$1" src="$2"
  [ -f "$src" ] || { echo "  MISSING: $src"; return 1; }
  ffmpeg -y -v error -i "$src" \
    -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0:detection=peak,\
aformat=sample_fmts=fltp,\
loudnorm=I=-18:TP=-3.0:LRA=7:print_format=summary" \
    -ar 48000 -ac 1 -c:a libmp3lame -q:a 3 "$OUT/$name.mp3" 2>/dev/null \
  || ffmpeg -y -v error -i "$src" \
    -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0:detection=peak" \
    -ar 48000 -ac 1 -c:a libmp3lame -q:a 3 "$OUT/$name.mp3"
  printf "  %-9s %6ss  <- %s\n" "$name" \
    "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/$name.mp3" | cut -c1-4)" \
    "$(basename "$src")"
}

echo "--- impacts (low-dominant, fast decay) ---"
copy simp1 "$SRC/sfx 1 .mp3"            # low, -19.0 -> -42.6
copy simp2 "$SRC/sfx 3..mp3"            # low, -19.2 -> -70.4, tightest of the three
copy simp3 "$SRC/sfx 5.mp3"             # low/mid, -22.1 -> -46.5

echo "--- riser (the only rising envelope in the pack) ---"
copy srise1 "$SRC/sfx 13.mp3"           # -38.5 -> -20.8, lands on a low hit

echo "--- ticks / clicks / UI ---"
copy stick1 "$SRC/sfx 11.mp3"           # short mechanical thunk, 0.87s
copy sui1   "$SRC/sfx 12 ui .mp3"       # mid UI tick, 0.58s
copy sclick "$SRC/sfx 15 click.mp3"     # high-dominant crisp click
copy sgear  "$SRC/sfx 9 scifi gear.mp3" # mechanical gear movement

echo "--- reveals / taps (mid, with a tail) ---"
copy srev1 "$SRC/sfx 8 reveal.mp3"
copy srev2 "$SRC/sfx 10 tap and reveal.mp3"
copy srev3 "$SRC/sfx 17 reveal.mp3"
copy stap1 "$SRC/sfx 7 tap.mp3"

echo "--- air / texture ---"
copy swsh1 "$SRC/sfx 14.mp3"            # mid/high, 1.70s

echo "--- sustained (BED use only - capped at BED_MAX) ---"
copy scount "$SRC/sfx 16 counter combo.mp3"   # flat across 2.98s, low+high

echo "--- quiet short accents (mean -46 to -50 dB at source) ---"
copy sacc1 "$SRC/sfx 2.mp3"
copy sacc2 "$SRC/sfx 4.mp3"
copy sacc3 "$SRC/sfx 6.mp3"

echo
echo "pool now: $(ls "$OUT"/*.mp3 | wc -l | tr -d ' ') files"
