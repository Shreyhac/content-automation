#!/usr/bin/env python3
"""Lift the reference's own B-roll, one clip per shot.

WHY EACH NUMBER IS WHAT IT IS
  - The reference burns its word-captions into the picture at y924-975
    (measured, not guessed), so no crop may extend past y920.
  - The band in this composition is 620px tall (solved from THE PRESENTER'S crown/chin,
    see index.html), so every window is 1080x620 with a per-shot y offset in
    [0,300] chosen so that shot's payload survives.
  - Output is 2160x1240 = exactly 2x, which is the size the 1080x620 element
    rasterises to on a scale(2) stage. Lanczos, so the upscale is clean rather
    than double-resampled by the renderer.
  - The reference is 1080x1920 VP9, so lifted footage carries half this
    composition's detail. That is a property of the source, not of the crop.

SHOTS THAT ARE NOT LIFTED are absent from this table on purpose:
  ref 13.633-15.967  Cintas's live ANTHROPIC_API_KEY, fully legible
  ref 26.300-28.267  "agent creation failed - insufficient credit balance"
  ref 28.267-30.800  the spec page stamped PLANNED . NOT LAUNCHED
  ref 30.800-32.067  a third party's meeting notes (BISOLA CATERING / MR YOMI)
  ref 32.067-36.600  a real person's inbox (Sidhant / Alvaro)
Those six are rebuilt in mocks/ instead.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF  = os.path.join(ROOT, "refs", "DbqcQUgxlyC.mp4")
OUT  = os.path.join(ROOT, "hf67", "assets", "broll")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 620          # the band, in stage space
CAP_TOP = 924             # the reference's own caption band starts here

# name, his_in, his_out, ref_in, ref_out, crop_y
SHOTS = [
 ("b01_tree_a",    0.000,  1.040,  0.000,  1.150,   0),
 ("b02_tree_b",    1.040,  2.200,  1.150,  2.300,   0),
 # 2.200-3.240 is FULL face, as in the reference
 ("b03_gh_repo",   3.240,  4.200,  3.600,  5.100, 300),
 ("b04_gh_readme", 4.200,  5.220,  5.100,  6.567, 300),
 ("b05_gh_desc",   5.220,  6.640,  6.567,  8.000, 300),
 ("b06_arch",      6.640,  7.869,  8.000,  9.333, 240),
 ("b07_claude_app",7.869,  8.660,  9.333, 10.400,   0),
 ("b08_menu",      8.660,  9.420, 10.400, 11.300,   0),
 ("b09_usage",     9.420, 10.380, 11.300, 12.400,   0),
 ("b10_clone",    10.380, 11.540, 12.400, 13.633, 300),
 # 11.540-13.840 -> mock M1 (.env, the API key is real in the reference)
 ("b11_skills",   13.840, 14.960, 15.967, 17.500,   0),
 ("b12_dash",     14.960, 16.340, 17.500, 19.367, 100),
 ("b13_type1",    16.340, 17.000, 19.367, 20.067, 300),
 ("b14_type2",    17.000, 18.020, 20.067, 21.200, 300),
 ("b15_type3",    18.020, 19.040, 21.200, 22.300, 300),
 ("b16_type4",    19.040, 19.820, 22.300, 23.400, 300),
 ("b17_type5",    19.820, 21.180, 23.400, 24.900, 300),
 ("b18_reply",    21.180, 22.280, 24.900, 26.300, 300),
 # 22.280-31.820 -> mocks M2..M6
]

def main():
    man = []
    for name, hi, ho, ri, ro, cy in SHOTS:
        assert cy + H <= CAP_TOP, f"{name}: crop reaches y{cy+H}, into the caption band"
        need = ho - hi                     # how long the composition will play it
        have = ro - ri                     # how long the reference's shot is
        # take the whole reference shot; if the slot is longer than the shot,
        # the last frame holds rather than the clip running out mid-beat
        dur = max(need, have) if have >= need else have
        dst = os.path.join(OUT, name + ".mp4")
        vf = (f"crop={W}:{H}:0:{cy},scale={W*2}:{H*2}:flags=lanczos")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{ri:.3f}", "-i", REF,
               "-t", f"{have:.3f}", "-an", "-vf", vf,
               "-c:v", "libx264", "-crf", "15", "-preset", "medium",
               "-pix_fmt", "yuv420p", "-r", "30", "-g", "15", "-keyint_min", "15", dst]
        subprocess.run(cmd, check=True)
        man.append({"id": name, "start": hi, "dur": round(ho - hi, 3),
                    "ref": [ri, ro], "cropY": cy, "shot_len": round(have, 3),
                    "short_by": round(max(0.0, (ho - hi) - have), 3)})
        print(f"{name:16s} take {hi:6.3f}-{ho:6.3f} ({ho-hi:5.3f}s)  "
              f"ref {ri:6.3f}-{ro:6.3f} ({have:5.3f}s)  cropY {cy:3d}"
              + ("   SHORT" if have < (ho - hi) - 1e-6 else ""))
    json.dump(man, open(os.path.join(HERE, "broll-manifest.json"), "w"), indent=1)
    print(f"\n{len(man)} clips -> {OUT}")

if __name__ == "__main__":
    main()
