#!/bin/bash
# Render one or more chunks into THEIR OWN renders/ directory.
#
#   ./render_chunks.sh c3 c4 c5
#
# The CLI resolves -o relative to the CWD, not to the DIR argument, so
# `npx hyperframes render c5` from hf46/ writes hf46/renders/c5_*.mp4, which
# assemble.sh (globbing c5/renders/*.mp4) will never see, and which silently
# leaves the previous render in place as the "latest". Always cd in first.
#
# 4K + three.js on 8 GB pins the renderer to one worker in screenshot mode, and a
# late frame can take >60s to capture (a memory/GC hump, c3 hit it at 851/888 six
# times in one day). The CLI's default 60s no-progress watchdog reads that as a hang
# and kills a HEALTHY render; retrying just burns 4 minutes per attempt to die at
# the same frame. HF_DE_STALL_MS raises the watchdog so the slow frame can finish,
# c3 rendered in 4m flat on the first try with it set.
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
