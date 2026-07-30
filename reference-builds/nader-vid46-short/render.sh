#!/bin/bash
# Render one or more chunks into THEIR OWN renders/ directory.
#
#   ./render.sh s1 s2
#
# The CLI resolves -o relative to the CWD, not to the DIR argument, so
# `npx hyperframes render s2` from hf46s/ writes hf46s/renders/s2_*.mp4 — which
# assemble.sh (globbing s2/renders/*.mp4) will never see, and which silently
# leaves the previous render in place as the "latest". Always cd in first.
#
# HF_DE_STALL_MS: the CLI's default 60s no-progress watchdog reads a slow frame as
# a hang and kills a HEALTHY render. On the film a late three.js frame took >60s on
# 8 GB and c3 died at the same frame six times in one day. This canvas is 1080x1920
# rather than 4K so it should never come close, but the guard costs nothing.
export HF_DE_STALL_MS=${HF_DE_STALL_MS:-420000}
set -uo pipefail
cd "$(dirname "$0")"
BASE="$PWD"
TRIES=${TRIES:-3}

for c in "$@"; do
  ok=0
  for try in $(seq 1 "$TRIES"); do
    echo "===== RENDER $c (attempt $try/$TRIES) $(date +%H:%M:%S) ====="
    ( cd "$BASE/$c" && npx hyperframes render . -q high -f 30 ) && { ok=1; break; }
    echo "  attempt $try stalled/failed; cleaning up and retrying"
    rm -rf "$BASE/$c"/renders/work-* "$BASE/$c"/renders/.*hf-transaction-* 2>/dev/null
    sleep 5
  done
  if [ "$ok" = 1 ]; then
    f=$(ls -t "$BASE/$c"/renders/*.mp4 | head -1)
    n=$(ffprobe -v error -count_frames -select_streams v \
          -show_entries stream=nb_read_frames -of csv=p=0 "$f")
    echo "OK $c  $n frames  $(basename "$f")"
  else
    echo "FAIL $c after $TRIES attempts"
  fi
done
echo "ALL DONE $(date +%H:%M:%S)"
