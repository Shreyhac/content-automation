#!/usr/bin/env python3
"""The single source of truth for the short's SFX bed.

usage: python3 sfx.py <chunk>        # injects that chunk's block
       python3 sfx.py --audit        # budget report for both chunks, no writes

Carried over from hf46/sfx.py, including the budget it ENFORCES rather than trusts:

  * a retired file cannot be used at all (the owner named thud / riser / boom)
  * no single file may exceed CAP_SHARE of the chunk's placements
  * median volume at/below MEDIAN_MAX, ceiling at CEIL_MAX, sustained beds at BED_MAX
  * the OWNER'S OWN PACK must be at least OWNER_MIN of placements

The last rule is the one that took three rounds to learn: when he supplies a pack he
expects it to DOMINATE, not garnish. His files are the `s*` names (simp/srise/stick/
sui/sclick/sgear/srev/stap/swsh/scount/sacc), 17 of them, peak-normalised by
curate_saas_sfx.sh so one volume number means one loudness across the whole pool.

Volumes are the film's round-3 levels (median 0.060) and no higher: his trajectory
across three rounds was 0.20 -> 0.10 -> 0.060, halving every time he said "loud".

Every cue is (time, file, volume, duration). Times are LOCAL to the chunk.
"""
import sys, os, re, statistics as st, collections, subprocess

CAP_SHARE  = 0.085
MEDIAN_MAX = 0.062
CEIL_MAX   = 0.100
BED_MAX    = 0.042
OWNER_MIN  = 0.55
RETIRED    = ("thud", "riser", "riser2", "boom", "cboom")
OWNER = ("simp1", "simp2", "simp3", "srise1", "stick1", "sui1", "sclick", "sgear",
         "srev1", "srev2", "srev3", "stap1", "swsh1", "scount",
         "sacc1", "sacc2", "sacc3")

# ---------------------------------------------------------------------------
# s1  0.000-29.200   the record · Deloitte 420 · Aura 200 · the verdict
#
# v3 moved the bed onto vid39's grammar: the FACE MOVES (card in, card out, the
# picture opening all the way out) each get a woosh, the two band wipes get a
# heavier one, the numbers and the stamps get an impact under the frame's shake,
# and the query types itself over a keyboard bed. Volumes are the film's round-3
# levels and no higher.
# ---------------------------------------------------------------------------
S1 = [
    # A1 · the record. Three bars slide off, each with a paper-slide and a landing.
    (0.160, "stap1",  0.058, 0.45),
    (0.220, "stick1", 0.048, 0.30),
    (0.820, "slide2", 0.058, 0.50),
    (0.880, "sui1",   0.048, 0.35),
    (2.380, "slide1", 0.058, 0.55),
    (2.440, "sclick", 0.052, 0.40),
    # the three fields resolve into ONE query
    (3.600, "srev1",  0.054, 0.60),   # the rules light as one
    (3.840, "sacc1",  0.050, 0.35),   # the spine draws
    (4.020, "sacc2",  0.046, 0.30),   # the dots land on it
    (4.340, "swsh1",  0.056, 0.55),   # the search field springs in
    (4.600, "sacc3",  0.042, 0.30),   # three values pulled into it
    (4.780, "tick3",  0.042, 0.30),
    (4.960, "tick5",  0.042, 0.30),
    (5.200, "type1",  0.038, 1.00),   # the query types itself
    (5.980, "stamp1", 0.062, 0.55),   # "1 result" stamps
    (5.990, "simp2",  0.066, 0.60),   # and the frame takes the hit
    (6.720, "srise1", 0.044, 0.55),   # into the band wipe

    # A2 · b3. The seal punches, the ring sweeps, the rail draws, 420 arrives.
    (7.000, "wsh4",   0.060, 0.55),   # BAND WIPE 1
    (7.140, "sacc3",  0.048, 0.35),
    (7.660, "stamp2", 0.062, 0.50),
    (8.100, "shine1", 0.048, 1.00),
    (9.680, "sui1",   0.044, 0.35),
    (10.360, "slide2", 0.048, 0.50),
    (11.000, "sgear",  0.042, 0.90),
    (11.200, "simp3",  0.068, 0.70),  # "420" lands, frame shakes
    (12.280, "srev2",  0.048, 0.55),  # the b-roll card rises
    (12.760, "sui1",   0.042, 0.30),
    (13.960, "tick4",  0.042, 0.35),

    # A2 · b4. The same rail, quieter: Aura's side is neutral in sound too.
    (15.233, "wsh2",   0.054, 0.55),
    (17.790, "stick1", 0.046, 0.30),
    (18.300, "sacc1",  0.044, 0.30),
    (18.990, "sgear",  0.040, 0.60),
    (20.073, "pop2",   0.050, 0.40),
    (20.500, "srev3",  0.046, 0.55),

    # A3 · the rail compresses, the card grows in, the verdict stamps.
    (21.133, "swsh1",  0.050, 0.55),
    (21.433, "wsh5",   0.056, 0.55),  # THE FACE CARD GROWS IN
    (27.793, "simp2",  0.066, 0.70),
    (28.010, "ok1",    0.050, 0.45),
    (28.860, "wsh1",   0.056, 0.55),  # and closes
]

# ---------------------------------------------------------------------------
# s2  29.200-45.000   the bundle · paying twice · the code · the close
# Times are LOCAL to the chunk.
# ---------------------------------------------------------------------------
S2 = [
    # b6 · the slabs pile onto the b-roll
    (0.000, "wsh3",   0.056, 0.55),
    (0.460, "stap1",  0.050, 0.40),
    (0.820, "sacc1",  0.050, 0.40),
    (2.260, "sui1",   0.046, 0.35),   # "a VPN?" — the slab he names lights

    # b7 · the strikes land on the slabs already there, then the one flash cut
    (3.787, "tick1",  0.044, 0.30),
    (3.907, "tick2",  0.044, 0.30),
    (4.027, "tick4",  0.044, 0.30),
    (4.067, "simp1",  0.078, 0.95),   # "twice" — the short's only hard flash
    (4.150, "srev1",  0.046, 0.50),

    # b8 · the one card, behind the second band wipe
    (5.500, "wsh1",   0.058, 0.55),   # BAND WIPE 2
    (5.540, "scount", 0.038, 1.10),
    (6.120, "stamp1", 0.066, 0.55),   # NADER stamps into its box
    (6.150, "simp2",  0.062, 0.70),
    (6.780, "sacc2",  0.048, 0.35),   # 60% pulses
    (7.900, "shine2", 0.050, 0.85),

    # A5 · the card shrinks to the chip, the picture opens all the way out
    (8.980, "srev2",  0.048, 0.50),
    (9.300, "wsh5",   0.056, 0.55),   # HERO OPENS
    (12.300, "wsh2",  0.054, 0.55),   # and closes on "like it"

    # b10 · the lockup opens and holds
    (12.780, "simp3", 0.066, 0.70),
    (13.413, "sgear", 0.042, 0.60),
    (13.793, "sclick", 0.044, 0.35),
    (14.500, "shine1", 0.048, 0.95),  # the outro pass
    (14.900, "sacc3", 0.042, 0.35),
]

CUES = {"s1": S1, "s2": S2}


def check(chunk, cues):
    n = len(cues)
    share = collections.Counter(f for _, f, _, _ in cues)
    vols = [v for _, _, v, _ in cues]
    med, ceil = st.median(vols), max(vols)
    own = sum(c for f, c in share.items() if f in OWNER)
    errs = []
    for f, c in share.most_common():
        if c / n > CAP_SHARE + 1e-9:
            errs.append(f"{f} is {c}/{n} = {100*c/n:.1f}% of placements (cap {100*CAP_SHARE:.1f}%)")
    if med > MEDIAN_MAX: errs.append(f"median volume {med:.3f} > {MEDIAN_MAX}")
    if ceil > CEIL_MAX:  errs.append(f"ceiling volume {ceil:.3f} > {CEIL_MAX}")
    for t, f, v, d in cues:
        if d > 1.5 and v > BED_MAX:
            errs.append(f"{f} at {t}s is a {d}s bed at {v} (cap {BED_MAX})")
        if f in RETIRED:
            errs.append(f"{f} is retired — the owner named it")
    if own / n < OWNER_MIN:
        errs.append(f"owner's own pack is {own}/{n} = {100*own/n:.0f}% "
                    f"of placements (floor {100*OWNER_MIN:.0f}%)")
    print(f"{chunk}: {n} placements · {len(share)} distinct · median {med:.3f} · "
          f"ceiling {ceil:.3f} · owner's pack {100*own/n:.0f}%")
    print("   top: " + ", ".join(f"{f}x{c}" for f, c in share.most_common(5)))
    return errs


def main():
    if sys.argv[1] == "--audit":
        bad = 0
        for ch in ("s1", "s2"):
            for e in check(ch, sorted(CUES[ch])):
                print("   !! " + e); bad = 1
        sys.exit(bad)

    chunk = sys.argv[1]
    cues = sorted(CUES[chunk], key=lambda c: c[0])
    errs = check(chunk, cues)
    if errs:
        print("  !! SFX budget violated:")
        for e in errs: print("     " + e)
        sys.exit(1)

    here = os.path.dirname(os.path.abspath(__file__))
    medialen = {}
    for _, f, _, _ in cues:
        p = os.path.join(here, "assets", "sfx", f + ".mp3")
        if not os.path.exists(p):
            print(f"  !! missing assets/sfx/{f}.mp3"); sys.exit(1)
        if f not in medialen:
            medialen[f] = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())

    lines = []
    for i, (t, f, v, d) in enumerate(cues, 1):
        # a slot longer than its media is silently shortened at render time; clamp it
        # here so the intent in this file matches what actually plays
        d = min(d, medialen[f])
        lines.append(
            f'  <audio id="{chunk}sfx{i}" data-start="{t:.3f}" data-duration="{d:.2f}" '
            f'data-track-index="{39+i}" src="assets/sfx/{f}.mp3" data-volume="{v:.3f}"></audio>')
    block = "<!-- SFX -->\n" + "\n".join(lines) + "\n  <!-- /SFX -->"

    path = os.path.join(here, chunk, "index.html")
    src = open(path).read()
    new, n = re.subn(r"<!-- SFX -->.*?<!-- /SFX -->", lambda m: block, src, flags=re.S)
    if not n:
        print(f"{chunk}: SFX markers not found"); sys.exit(1)
    open(path, "w").write(new)
    print(f"   injected {len(lines)} cues")


if __name__ == "__main__":
    main()
