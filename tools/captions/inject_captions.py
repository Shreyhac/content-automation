#!/usr/bin/env python3
"""Regenerate the caption block inside a chunk, between the CAPTIONS markers.

usage: python3 inject_captions.py <chunk> <abs_start> <abs_end> [mute_ranges]

Keeping this a script (rather than pasted output) means a transcript correction
propagates to every chunk with one command instead of by hand.
"""
import subprocess, sys, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
chunk, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
mutes = sys.argv[4] if len(sys.argv) > 4 else ""

caps = subprocess.run(
    ["python3", os.path.join(HERE, "build_captions.py"), a, b, chunk, mutes],
    capture_output=True, text=True, check=True).stdout.rstrip()

path = os.path.join(HERE, chunk, "index.html")
src = open(path).read()
new, n = re.subn(r"<!-- CAPTIONS -->.*?<!-- /CAPTIONS -->",
                 lambda m: "<!-- CAPTIONS -->\n" + caps + "\n  <!-- /CAPTIONS -->",
                 src, flags=re.S)
if not n:
    print(f"{chunk}: CAPTIONS markers not found"); sys.exit(1)
open(path, "w").write(new)
print(f"{chunk}: injected {len(caps.splitlines())} caption clips ({a}–{b})")
