#!/usr/bin/env python3
"""Rewrite the `const Wn = {...}` face-window constants in every chunk from the
solved card-transforms.json.

The transforms are measurements, not taste — they must never be typed by hand into a
composition. This regenerates them in place so the HTML can only ever carry what
solve_card.py actually computed.
"""
import json, re, sys, glob, os

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "card-transforms.json")))
wins = {w["win"]: w for w in data["windows"]}

def js(w):
    # ROUND 2: no `track`. One constant tx per window — the smoothed follow read as a
    # glitch to the owner. `resid` rides along so a composition can be read against
    # the reason a window is card or full-bleed without opening the solver.
    return ("const W%d={a:%.2f,b:%.2f,s:%.4f,tx:%.1f,ty:%.1f,ok:%s,resid:%d};"
            % (w["win"], w["a"], w["b"], w["s"], w["tx"], w["ty"],
               "true" if w["card_ok"] else "false", w["resid"]))

targets = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "c*/index.html")))
for path in targets:
    src = open(path).read()
    found = re.findall(r"^\s*const W(\d+)\s*=\s*\{.*?\};\s*$", src, re.M)
    if not found:
        print(f"{os.path.basename(os.path.dirname(path))}: no window constants"); continue
    out, n = src, 0
    for num in found:
        w = wins.get(int(num))
        if not w:
            print(f"  !! W{num} not in card-transforms.json"); continue
        out = re.sub(r"^\s*const W%s\s*=\s*\{.*?\};\s*$" % num,
                     "  " + js(w), out, count=1, flags=re.M)
        n += 1
    open(path, "w").write(out)
    tag = os.path.basename(os.path.dirname(path))
    print(f"{tag}: injected {n} windows -> " +
          ", ".join(f"W{k}({'card' if wins[int(k)]['card_ok'] else 'FULL'})" for k in found))
