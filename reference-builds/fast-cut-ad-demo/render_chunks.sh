#!/usr/bin/env bash
# Render hfad2's chunks SEQUENTIALLY at 4K.
#
#   ./render_chunks.sh          (all eight)
#   ./render_chunks.sh c3 c4    (just those)
#
# WHY CHUNKS AT ALL
#   The whole composition is 28 <video> elements at 2160x3840 / 60-100 Mbps.
#   `hyperframes render` pre-extracts frames from EVERY video before capturing a
#   single frame, and on 2026-08-13 that stage hard-reset this 8 GB M2 Air three
#   times (`wdog,reset_in_1` in ResetCounter-*.diag; blank screen, no panic file).
#   Chunking caps the decoders per page at FIVE. Nothing else does.
#
# --resolution portrait-4k
#   The composition root is 1080x1920; without this flag the render lands at
#   1080p and quietly delivers a quarter of the pixels. Chrome raises its DPR
#   rather than the composition changing, so nothing in the HTML needs to know.
#
# -w 1, NOT auto
#   `-w auto` resolves to 6 on this machine and each worker is a separate Chrome
#   process that loads the WHOLE page. Note --low-memory-mode already auto-enables
#   at <=8 GB RAM and pins 1 worker, which is why the crashed logs read
#   `workerCount:1` under "auto workers" -- so worker count was never what killed
#   the machine. The VIDEO EXTRACTION stage loads every <video> in the page
#   regardless of workers, and that is the stage render-probe4k.log died in.
#   Chunking is the fix; -w 1 is just belt-and-braces.
#
# The three env settings were each earned on an earlier film and are not optional:
#   HF_DE_STALL_MS           the no-frame-progress watchdog defaults to 60s and
#                            kills a render whose slow 4K frame legitimately
#                            takes longer (this is what failed render-v1e.log at
#                            frame 915/1092).
#   FFMPEG_ENCODE_TIMEOUT_MS the default 600s budget for the FINAL encode is not
#                            enough for 4K; vid46 lost finished captures to it.
#   PRODUCER_ENABLE_CHUNKED_ENCODE  encodes in smaller passes so a slow machine
#                            cannot blow one wall-clock budget.
#
# --video-bitrate 90M, NOT -q high and NOT --crf.
#   The 28 source shots run 52.0 / 64.7 / 99.9 Mbps (min/median/max). A CRF is a
#   quality target whose BITRATE moves with content -- measured across vid60/61,
#   one CRF gave 36.8 Mbps on a busy act and 24.9 on a quiet one -- and the
#   owner's standing complaint has been the delivered NUMBER ("very much
#   compressed"). So the ceiling is pinned from the hardest shot and the easy
#   acts are left to undershoot it. Verify with ffprobe after assemble, every round.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

CHUNKS=("$@")
[ ${#CHUNKS[@]} -eq 0 ] && CHUNKS=(c1 c2 c3 c4 c5 c6 c7 c8)

HF="${HF:-$HOME/.npm/_npx/702923228c2ce1e6/node_modules/.bin/hyperframes}"
[ -x "$HF" ] || HF="npx --yes hyperframes"

export HF_DE_STALL_MS=420000
export FFMPEG_ENCODE_TIMEOUT_MS=3600000
export PRODUCER_ENABLE_CHUNKED_ENCODE=true

# preflight: refuse to start a 4K run that the disk cannot hold
FREE=$(df -g . | awk 'NR==2{print $4}')
[ "$FREE" -lt 12 ] && { echo "!! only ${FREE}GB free — a 4K chunk needs ~1GB of transient frames"; exit 1; }
echo "disk: ${FREE}GB free"

for c in "${CHUNKS[@]}"; do
  [ -f "$c/index.html" ] || { echo "!! $c/index.html missing — run build_chunks.py"; exit 1; }
done

for c in "${CHUNKS[@]}"; do
  echo "=================== $c ==================="
  ( cd "$c"
    rm -rf renders/work-* renders/.*hf-transaction* 2>/dev/null || true
    ls renders/*.mp4 >/dev/null 2>&1 && rm -f renders/*.mp4
    "$HF" render . --resolution portrait-4k --video-bitrate 90M -f 30 -w 1 \
        > "$ROOT/$c-render.log" 2>&1 || {
      echo "  !! $c FAILED — tail of log:"; tail -25 "$ROOT/$c-render.log"; exit 1; }
    f=$(ls -t renders/*.mp4 | head -1)
    n=$(ffprobe -v error -count_frames -select_streams v \
          -show_entries stream=nb_read_frames -of csv=p=0 "$f")
    br=$(ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of csv=p=0 "$f")
    wh=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$f")
    echo "  $c -> $(basename "$f")  ${n} frames  ${wh}  $(awk -v b="$br" 'BEGIN{printf "%.1f", b/1e6}') Mbps"
  )
done
echo "all requested chunks rendered"
