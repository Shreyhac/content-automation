#!/usr/bin/env python3
"""Derive the shot table from the reference's real cuts, re-time onto his take,
   and PROVE no lifted clip carries the reference creator's face.

Three rounds of reading extracted clips full-frame produced these rules:

 1. SLOTS COME FROM DETECTED CUTS, never from eyeballed midpoints. A slot placed
    by eye crossed a cut twice and ended on Cintas's forehead.
 2. EVERY SOURCE WINDOW IS PULLED IN BY `GUARD` AT BOTH ENDS. Input seeking is
    approximate; without the guard a window that mathematically stops at a cut
    still delivers frames from the other side of it.
 3. THE REFERENCE HAS THREE FULL-BLEED FACE SEGMENTS, not two. Vision's face
    detector found only the frames with a WHOLE face in the band and so missed
    19.40-20.10, where only his forehead and eyes are in frame. A skin-fraction
    measure over the band found all three. Those segments are played as FULL
    here, exactly as the reference plays them, and are never lifted.
 4. FOUR SHOTS CARRY "Dr Cintas" — the Claude app greeting and the sidebar
    nameplate. Another creator's account name on screen is the same defect class
    as their face, so the Claude-app beats are rebuilt as mocks instead.

After cutting, every lifted clip is re-measured for skin fraction and the build
fails if any frame of any clip looks like a face. That check is proven to fire:
running it against the pre-guard clips flagged b01/b02/b03/b10/b11.
"""
import json, os, re, difflib, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facecheck import has_face          # calibrated + proven, see facecheck.py

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF  = os.path.join(ROOT, "refs", "DbqcQUgxlyC.mp4")
OUT  = os.path.join(ROOT, "hf67", "assets", "broll")
W, H, CAP_TOP = 1080, 620, 924
HIS_DUR = 35.233333
GUARD   = 0.13          # seconds pulled off each end of every source window

def words(p):
    d = json.load(open(p)); o = []
    for s in d["segments"]:
        for w in s.get("words", []):
            t = re.sub(r"[^a-z0-9]", "", w["word"].lower())
            if t: o.append((t, float(w["start"])))
    return o
R  = words("/private/tmp/claude-501/-Users-shreyansharora-Desktop-shreyansh-claude/05f2d98e-b2c9-46bb-95c2-65c0d13d8323/scratchpad/ref3/refaudio.json")
Hw = words(os.path.join(ROOT, "hf67", "transcript.json"))
sm = difflib.SequenceMatcher(None, [w[0] for w in R], [w[0] for w in Hw], autojunk=False)
P  = sorted((R[a+k][1], Hw[b+k][1]) for a, b, n in sm.get_matching_blocks() for k in range(n))
def remap(rt):
    if rt <= P[0][0]:  return rt * (P[0][1]/P[0][0]) if P[0][0] > 0 else rt
    if rt >= P[-1][0]:
        (r0,h0),(r1,h1) = P[-2], P[-1]
        return h1 + (rt-r1) * ((h1-h0)/(r1-r0) if r1>r0 else 1.0)
    for (r0,h0),(r1,h1) in zip(P, P[1:]):
        if r0 <= rt <= r1:
            return h0 + (0 if r1==r0 else (rt-r0)/(r1-r0)) * (h1-h0)
    return rt
def snap(t):
    b = min(Hw, key=lambda w: abs(w[1]-t))
    return b[1] if abs(b[1]-t) <= 0.16 else t

# (ref_in, ref_out, kind, id, cropY, note)
SHOTS = [
 (0.033,  2.300, "lift", "b01_tree",   0, "the claude-code agent tree", None),
 (2.300,  3.600, "full", None,         0, "his face, as the reference plays it", None),
 (3.600,  6.567, "lift", "b02_github", 300, "the launch-your-agent repo", None),
 (6.567,  9.333, "lift", "b03_arch",   240, "the managed-agent diagram", None),
 (9.333, 11.933, "mock", "m1_claude",    0, "reference shows the Claude app titled 'Dr Cintas'", None),
 (11.933,12.733, "lift", "b04_usage",    0, "usage dashboard", None),
 (12.733,13.633, "lift", "b05_clone",  300, "git clone launch-your-agent", None),
 (13.633,15.967, "mock", "m2_env",       0, "reference shows a live ANTHROPIC_API_KEY", None),
 # SOURCE OVERRIDE: the guarded window (16.097-17.103) still opens on the Claude
 # app greeting "What's up next, Dr Cintas?", which clears at 16.20; the skills
 # dropdown this beat is actually about lands at 16.45. Verified by stepping the
 # window at 0.2s and reading it, not by arithmetic.
 (15.967,17.233, "lift", "b06_skills",   0, "the skills list", (16.45, 17.15)),
 (17.233,18.233, "lift", "b07_dash",   100, "dashboard", None),
 (18.233,19.400, "lift", "b08_dash2",  100, "dashboard + rubric tooltip", None),
 (19.400,20.100, "full", None,           0, "his face — the segment the first cut missed", None),
 (20.100,23.667, "lift", "b09_type",   300, "typing the agent's job", None),
 (23.667,24.900, "lift", "b10_type2",  300, "the prompt completed", None),
 (24.900,27.200, "lift", "b11_reply",  300, "Claude scopes the agent", None),
 (27.200,28.267, "mock", "m3_launch",    0, "reference shows 'agent creation failed'", None),
 (28.267,30.800, "mock", "m4_spec",      0, "reference shows PLANNED . NOT LAUNCHED", None),
 (30.800,32.067, "mock", "m5_meeting",   0, "reference shows a third party's meeting notes", None),
 (32.067,36.600, "mock", "m6_inbox",     0, "reference shows a real person's inbox", None),
 (36.600,39.460, "full", None,           0, "his face + the CTA", None),
]

rows, prev = [], 0.0
for i, (ri, ro, kind, name, cy, note, src_override) in enumerate(SHOTS):
    hi = 0.0 if i == 0 else prev
    ho = HIS_DUR if i == len(SHOTS)-1 else snap(remap(ro))
    if ho <= hi + 0.20: ho = hi + 0.20
    prev = ho
    rows.append(dict(i=i, kind=kind, id=name, ref=[ri,ro], his=[round(hi,3),round(ho,3)],
                     slot=round(ho-hi,3), cropY=cy, note=note,
                     src=list(src_override) if src_override else None))

print(f"{'#':>2} {'kind':5s} {'id':11s} {'ref in':>7} {'ref out':>7} {'his in':>7} {'his out':>7} {'slot':>6} {'src':>6} {'x':>5}")
for r in rows:
    assert r["cropY"] + H <= CAP_TOP, r["id"]
    ri, ro = r["ref"]
    if r["kind"]=="lift":
        a,b = (r["src"] if r["src"] else [ri+GUARD, ro-GUARD]); src = max(0.0, b-a)
    else: src = ro-ri
    sp = (src/r["slot"]) if (r["kind"]=="lift" and r["slot"]>0) else 0
    print(f"{r['i']:2d} {r['kind']:5s} {str(r['id'] or '-'):11s} {ri:7.3f} {ro:7.3f} "
          f"{r['his'][0]:7.3f} {r['his'][1]:7.3f} {r['slot']:6.3f} {src:6.3f} {sp:5.2f}")
print(f"\ntotal {sum(r['slot'] for r in rows):.3f}s vs A-roll {HIS_DUR:.3f}s")
json.dump(rows, open(os.path.join(HERE,"shots.json"),"w"), indent=1)

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT,f))


print("\ncutting lifted clips (guard %.2fs each end):" % GUARD)
fail = []
for r in rows:
    if r["kind"] != "lift": continue
    ri, ro = (r["src"] if r["src"] else [r["ref"][0]+GUARD, r["ref"][1]-GUARD])
    cy, need = r["cropY"], r["slot"] + 0.10
    pts = need / (ro-ri)
    dst = os.path.join(OUT, r["id"]+".mp4")
    vf = f"crop={W}:{H}:0:{cy},setpts=PTS*{pts:.6f},scale={W*2}:{H*2}:flags=lanczos,fps=30"
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{ri:.3f}","-t",f"{ro-ri:.3f}","-i",REF,
        "-an","-vf",vf,"-c:v","libx264","-crf","15","-preset","medium","-pix_fmt","yuv420p",
        "-r","30","-g","15","-keyint_min","15",dst], check=True)
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",dst],
        capture_output=True,text=True).stdout.strip())
    face, sk, lu, at = has_face(dst)
    ok_len  = d >= r["slot"] - 1e-3
    ok_face = not face
    if not (ok_len and ok_face): fail.append((r["id"], d, r["slot"], sk, lu, at))
    print(f"  {r['id']:11s} {d:5.3f}s / slot {r['slot']:5.3f}  play {1/pts:5.3f}x  "
          f"skin {sk:.4f} lum {lu:5.1f}  {'OK' if ok_len and ok_face else 'FACE'}")

if fail:
    print("\nFAILURES:")
    for id_,d,sl,sk,lu,at in fail:
        why = []
        if d < sl-1e-3: why.append(f"file {d:.3f}s < slot {sl:.3f}s")
        why.append(f"face in band (skin {sk:.4f} lum {lu:.1f} at {at:.1f}s)")
        print(f"  {id_}: {'; '.join(why)}")
    sys.exit(1)
print("\nall lifted clips: long enough, and no face in any frame")
