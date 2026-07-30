#!/usr/bin/env python3
"""Apply build_captions.py's CONT rule to captions ALREADY injected into the chunks.

Re-running inject_captions.py would be the tidier route, but the mute ranges (the
spans where an on-screen card already states the words) were passed on the command
line and are not recorded anywhere, so a blind re-inject would resurrect captions
that were deliberately suppressed. This rewrites only the punctuation joins:

  "a <b>30</b> -day money"        -> "a <b>30</b>-day money"
  "...money" / "-back guarantee." -> "...money-back" / "guarantee."

usage: python3 fix_caption_glue.py [--dry]
"""
import re, sys, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
DRY = '--dry' in sys.argv

CLIP = re.compile(
    r'(<div id="(\w+)" class="cap clip" data-start="[\d.]+" data-duration="[\d.]+"'
    r'[^>]*>)(.*?)(</div>)')
CONT = re.compile(r"^(?:<[bi]>)?[.,;:!?)\]%'’–—-]")

total = 0
for path in sorted(glob.glob(os.path.join(HERE, 'c*', 'index.html'))):
    src = open(path).read()
    clips = list(CLIP.finditer(src))
    texts = [m.group(3) for m in clips]

    for i, txt in enumerate(texts):
        toks = txt.split(' ')

        # 1. a clip that OPENS on attaching punctuation: hand that token back to
        #    the clip before it, where the word it belongs to lives.
        if toks and CONT.match(toks[0]) and i > 0:
            prev = texts[i - 1].split(' ')
            if prev:
                prev[-1] = prev[-1] + toks[0]
                texts[i - 1] = ' '.join(prev)
                toks = toks[1:]

        # 2. within a clip, drop the space before every attaching token
        out = []
        for k, t in enumerate(toks):
            if out and CONT.match(t):
                out[-1] = out[-1] + t
            else:
                out.append(t)
        texts[i] = ' '.join(out)

    changed = sum(1 for m, t in zip(clips, texts) if m.group(3) != t)
    if not changed:
        continue
    total += changed
    for m, t in zip(clips, texts):
        if m.group(3) != t:
            print(f"  {os.path.basename(os.path.dirname(path))}/{m.group(2)}")
            print(f"    - {m.group(3)}")
            print(f"    + {t}")

    # rebuild back-to-front so earlier spans keep their offsets
    for m, t in zip(reversed(clips), reversed(texts)):
        src = src[:m.start()] + m.group(1) + t + m.group(4) + src[m.end():]
    if not DRY:
        open(path, 'w').write(src)

print(f"{'would fix' if DRY else 'fixed'} {total} caption clip(s)")
