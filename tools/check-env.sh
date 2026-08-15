#!/usr/bin/env bash
# Verify every binary and asset the pipeline needs.
# Usage: bash tools/check-env.sh

FAIL=0
ok()   { printf '  \033[32mok\033[0m    %s\n' "$1"; }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$1"; }
bad()  { printf '  \033[31mMISS\033[0m  %s\n' "$1"; FAIL=1; }

need() { # need <binary> <install hint>
  if command -v "$1" >/dev/null 2>&1; then ok "$1"; else bad "$1  ->  $2"; fi
}
want() { # optional
  if command -v "$1" >/dev/null 2>&1; then ok "$1 (optional)"; else warn "$1 not found (optional) -> $2"; fi
}

echo
echo "Required binaries"
need ffmpeg  "brew install ffmpeg"
need ffprobe "brew install ffmpeg"
need node    "brew install node"
need npx     "brew install node"
need python3 "brew install python@3.12"
need whisper "pip3 install --user openai-whisper"
need swift   "xcode-select --install"

echo
echo "Optional binaries"
want yt-dlp "pip3 install --user yt-dlp   (prefix runs with DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib)"
want git    "brew install git"

echo
echo "Python packages"
if python3 -c "import playwright" 2>/dev/null; then
  ok "playwright"
  if python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p: p.chromium.launch().close()
" 2>/dev/null; then ok "playwright chromium browser"
  else bad "playwright chromium  ->  python3 -m playwright install chromium"; fi
else
  bad "playwright  ->  pip3 install --user playwright && python3 -m playwright install chromium"
fi

# Pillow: the contrast check in tools/gates/guard.py and the whole contact sheet.
# Without it guard.py reports the contrast pass as a failure rather than skipping it silently,
# which is deliberate: a gate that quietly stops checking is worse than one that stops.
if python3 -c "import PIL" 2>/dev/null; then ok "Pillow"
else bad "Pillow  ->  pip3 install --user Pillow   (tools/gates contrast + tools/qa/shoot-sheet.py)"; fi

# python-docx: the CTA .docx, which is a required deliverable at first delivery.
if python3 -c "import docx" 2>/dev/null; then ok "python-docx"
else bad "python-docx  ->  pip3 install --user python-docx   (tools/deliver/make_cta_doc.py)"; fi

echo
echo "Node / HyperFrames"
if command -v node >/dev/null 2>&1; then
  major=$(node -v | sed 's/^v\([0-9]*\).*/\1/')
  if [ "${major:-0}" -ge 18 ] 2>/dev/null; then ok "node $(node -v) (>= 18)"
  else bad "node $(node -v) is too old, need >= 18"; fi
fi
if command -v npx >/dev/null 2>&1; then
  if npx --yes hyperframes --version >/dev/null 2>&1; then
    ok "npx hyperframes ($(npx --yes hyperframes --version 2>/dev/null | head -1))"
  else
    warn "npx hyperframes could not run (first run downloads it; check network)"
  fi
fi

echo
echo "Repo assets"
R="$(cd "$(dirname "$0")/.." && pwd)"
for d in library/fonts library/sfx/house library/sfx/saas library/vendor .claude/skills \
         tools/gates tools/deliver tools/review reference-builds reference-cuts; do
  n=$(find "$R/$d" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" -gt 0 ]; then ok "$d ($n files)"; else bad "$d is empty"; fi
done
[ -f "$R/library/vendor/three.min.js" ] && ok "three.min.js vendored" || bad "library/vendor/three.min.js missing"
for s in hyperframes hyperframes-cli gsap; do
  [ -d "$R/.claude/skills/$s" ] && ok "skill: $s" || bad "skill: $s  ->  npx hyperframes skills"
done

echo
echo "Environment"
if [ -n "${HF_DE_STALL_MS:-}" ]; then ok "HF_DE_STALL_MS=$HF_DE_STALL_MS"
else warn "HF_DE_STALL_MS unset  ->  export HF_DE_STALL_MS=420000 (see docs/07-troubleshooting.md)"; fi

free=$(df -g "$R" 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "$free" ]; then
  if [ "$free" -ge 10 ]; then ok "free disk ${free}Gi"
  elif [ "$free" -ge 3 ]; then warn "free disk ${free}Gi (a 4K round costs ~800MB)"
  else bad "free disk ${free}Gi is too low; renders fail under ~1GB"; fi
fi

if [ -d /opt/homebrew/opt/expat/lib ]; then
  ok "expat present (prefix yt-dlp/pip with DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib)"
else
  warn "expat not at /opt/homebrew/opt/expat/lib; if pip/yt-dlp fail with a pyexpat error, brew install expat"
fi

echo
if [ "$FAIL" -eq 0 ]; then
  printf '\033[32mALL CHECKS PASSED\033[0m\n\n'
else
  printf '\033[31mSOME CHECKS FAILED\033[0m  see SETUP.md\n\n'
fi
exit $FAIL
