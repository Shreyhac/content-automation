#!/usr/bin/env python3
"""Build and inject the SFX block for a chunk, between the SFX markers.

usage: python3 sfx.py <chunk>

ROUND 2. The owner's note was "why the fuck are you just using two or three SFX,
use as many as possible ... reduce the volume of ALL the SFX a bit, it's too loud
... the Riser SFX is very weird. Same with the thud."

Round 1 measured 236 placements over what looked like 17 files, but boom.mp3 and
cboom.mp3 were byte-identical and so were riser.mp3 and riser2.mp3 — so it was 15
distinct sounds, and boom alone carried 48 hits. Top four distinct sounds were 55%
of every transient in the film. His "two or three" was a fair description.

So this file is the single source of truth for the bed, and it ENFORCES the budget
rather than trusting the author:

  * thud / riser / riser2 are not in the pool at all — he named them
  * no single file may exceed CAP_SHARE of all placements
  * median volume must land at/below MEDIAN_MAX, ceiling at CEIL_MAX
  * sustained beds (>1.5s) capped at BED_MAX

Every cue is (time, file, volume, duration). Times are LOCAL to the chunk.
"""
import sys, os, re, statistics as st, collections

CAP_SHARE  = 0.085
MEDIAN_MAX = 0.075
CEIL_MAX   = 0.11
BED_MAX    = 0.055

# ---------------------------------------------------------------------------
# c1  0.00-28.70   hook · one search · head-to-head · the question · collect+sell
# ---------------------------------------------------------------------------
C1 = [
    # hook — the redaction stack. Bars are paper-slides, locks are UI ticks.
    (0.16, "slide1", 0.078, 0.55),
    (0.22, "stick1", 0.06, 0.30),
    (0.86, "slide2", 0.078, 0.50),
    (0.92, "sui1",   0.06, 0.35),
    (2.40, "slide1", 0.078, 0.55),
    (2.46, "sclick", 0.066, 0.40),
    # cut to the search
    (3.30, "swsh1",  0.084, 0.70),
    (3.62, "type1",  0.042, 1.05),   # bed under the typing
    (4.62, "tick5",  0.072, 0.40),
    # four results, four DIFFERENT pops
    (4.78, "sacc1",  0.066, 0.30),
    (4.98, "sacc2",  0.066, 0.40),
    (5.18, "sacc3",  0.066, 0.35),
    (5.38, "pop4",   0.066, 0.40),
    (5.66, "stick1", 0.054, 0.40),
    # the lockup lands
    (6.62, "srise1", 0.054, 0.55),
    (7.12, "simp1",  0.096, 1.10),
    (7.62, "simp2",  0.072, 0.60),
    # 9.30-12.18 used to be five silent seconds on a still lockup; the picture now
    # accents "data removal" and closes the marks on "head to head", so the bed has
    # to follow. Kept quiet — this is emphasis under a continuous line, not a cut.
    (9.30, "slide2", 0.06, 0.45),   # Incogni's descriptor underlines
    (10.96, "wsh4",   0.054, 0.55),   # the two marks close on the VS
    (11.98, "simp3",  0.072, 0.70),   # they meet
    (13.02, "srev2",  0.066, 0.55),
    (14.14, "sui1",   0.06, 0.35),
    # the question
    (14.86, "wsh2",   0.084, 0.50),
    (16.90, "swsh1",  0.06, 0.45),
    # the pull quote
    (19.84, "imp2",   0.09, 0.85),
    # collect and sell
    (21.82, "wsh4",   0.078, 0.55),
    (21.90, "sgear",  0.06, 0.60),
    (23.64, "simp1",  0.078, 0.70),
    (24.30, "wsh5",   0.048, 0.95),
    (27.50, "data2",  0.06, 0.55),
    (27.72, "sclick", 0.06, 0.30),
]

# ---------------------------------------------------------------------------
# c2  28.70-54.03   buyers finish · how it's collected · the 750 wall
# ---------------------------------------------------------------------------
C2 = [
    (0.02, "data1",  0.054, 0.60),   # packet in flight
    (0.14, "sacc1",  0.066, 0.40),   # buyer 02 lands
    (2.38, "data1",  0.054, 0.55),
    (2.56, "simp2",  0.084, 0.75),   # "even scammers" - the turn
    # how it gets collected: one distinct sound per event, none reused
    (3.40, "swsh1",  0.078, 0.50),
    (3.90, "tick4",  0.066, 0.40),
    (4.02, "sacc2",  0.06, 0.30),
    (5.14, "stick1", 0.066, 0.45),
    (5.26, "sacc3",  0.06, 0.35),
    (5.40, "wsh6",   0.06, 0.90),   # the b-roll takes the card slot
    (6.36, "sui1",   0.066, 0.40),
    (6.48, "pop4",   0.06, 0.40),
    (7.64, "gl2",    0.048, 0.60),   # the three packets converge
    (8.20, "sgear",  0.054, 0.50),
    (9.00, "stamp1", 0.09, 0.85),   # FOR SALE stamps
    # the field opens
    (10.16, "srise1", 0.048, 1.30),
    (10.30, "wsh5",   0.066, 1.00),
    (12.10, "simp3",  0.078, 0.90),
    # the 750
    (13.46, "swsh1",  0.072, 0.45),
    (15.30, "scount", 0.045, 1.80),  # counting texture under the wall powering up
    (15.52, "data2",  0.054, 0.60),   # the wall powers up
    (17.14, "imp1",   0.096, 1.10),   # 750 arrives
    (17.44, "shine1", 0.06, 0.80),
    (18.12, "sclick", 0.06, 0.40),
    (20.36, "tick3",  0.054, 0.35),
    # only the registered ones
    (22.32, "wsh4",   0.072, 0.55),
    (23.02, "stick1", 0.06, 0.30),
]

# ---------------------------------------------------------------------------
# c3  54.03-83.63   coverage · one job · Deloitte seal · 420+ · types · 245M
# ---------------------------------------------------------------------------
C3 = [
    (0.12, "slide2", 0.066, 0.50),   # the Incogni mark rises
    (0.48, "wsh3",   0.06, 0.45),   # the rule draws
    (0.76, "slide1", 0.06, 0.50),   # the Aura mark rises
    (2.49, "swsh1",  0.072, 0.60),
    (2.60, "srise1", 0.048, 1.10),   # the field converges to one object
    (3.33, "simp1",  0.078, 0.70),
    (5.35, "sui1",   0.06, 0.40),
    (7.01, "wsh2",   0.072, 0.50),
    (7.69, "stamp2", 0.096, 0.90),   # the Deloitte seal PRESSES
    (8.12, "srev3",  0.066, 0.60),   # the tick draws
    (11.01, "simp2",  0.09, 1.05),   # 420 arrives
    (11.32, "sclick", 0.06, 0.35),   # the "+"
    (11.42, "shine1", 0.054, 0.75),
    (12.31, "wsh6",   0.054, 0.85),   # the b-roll card slides up
    (15.33, "swsh1",  0.072, 0.55),
    (15.73, "sacc1",  0.06, 0.30),   # each broker type
    (17.21, "sacc2",  0.06, 0.35),
    (18.87, "sacc3",  0.06, 0.40),
    (21.89, "gl1",    0.06, 0.70),
    (23.13, "simp3",  0.09, 0.80),   # 245 arrives
    (23.30, "data2",  0.048, 0.60),
    (24.87, "imp5",   0.084, 0.90),   # MILLION lands
    (25.33, "tick2",  0.06, 0.45),
    (27.37, "wsh5",   0.066, 0.60),
    (28.63, "sgear",  0.06, 0.50),
]

# ---------------------------------------------------------------------------
# c4  83.63-112.07   the coverage rail · two tests · the module stack
# ---------------------------------------------------------------------------
C4 = [
    (0.19, "stick1", 0.06, 0.35),
    (1.59, "wsh1",   0.072, 0.60),
    (3.13, "swsh1",  0.066, 0.50),   # the axis draws
    (3.34, "data2",  0.048, 0.55),   # the ticks
    (3.92, "pop2",   0.066, 0.40),   # Incogni knob
    (6.45, "sacc1",  0.066, 0.45),   # Aura knob
    (6.92, "gl1",    0.06, 0.60),   # the gap
    (7.12, "srev2",  0.06, 0.60),
    (7.77, "wsh2",   0.072, 0.50),
    (9.67, "sui1",   0.06, 0.40),   # test 1
    (9.80, "wsh6",   0.048, 0.70),
    (11.53, "sclick", 0.06, 0.40),   # test 2
    (11.66, "swsh1",  0.048, 0.70),
    (13.53, "simp1",  0.084, 0.75),   # the verdict
    (13.62, "shine1", 0.054, 0.70),
    (15.89, "wsh4",   0.066, 0.55),
    (17.99, "srise1", 0.048, 0.90),   # into the stack
    # the seven slabs: rotate three distinct impacts so a 7-hit sequence is not
    # the same sample seven times, and keep them quiet - they are a rhythm bed
    (18.59, "simp2",  0.06, 0.45),
    (19.41, "gear1",  0.06, 0.45),
    (20.55, "simp3",  0.06, 0.50),
    (22.07, "imp4",   0.06, 0.45),
    (23.91, "sgear",  0.06, 0.45),
    (26.25, "simp1",  0.06, 0.50),
    (27.35, "simp2",  0.078, 0.85),   # the last one lands heaviest
    (18.29, "wsh6",   0.054, 0.80),   # the b-roll takes the card slot
]

# ---------------------------------------------------------------------------
# c5  112.07-139.23   the ledger · paying twice · the collapse · the guarantee
# ---------------------------------------------------------------------------
C5 = [
    (2.27, "stap1",  0.072, 0.50),   # each module struck as "you already have it"
    (2.95, "slide2", 0.072, 0.50),
    (4.39, "stap1",  0.072, 0.50),
    (5.31, "swsh1",  0.072, 0.55),
    (6.35, "simp3",  0.09, 0.85),   # 2x lands
    (6.72, "wsh3",   0.054, 0.45),
    (8.29, "wsh5",   0.06, 0.80),
    # the tower empties - a descending run, then the survivor lands
    (8.38, "gl2",    0.054, 0.90),
    (8.60, "swsh1",  0.06, 0.85),
    (9.04, "simp3",  0.078, 0.70),
    (9.22, "ok3",    0.06, 0.55),
    (10.37, "tick2",  0.06, 0.45),
    (11.95, "stamp1", 0.096, 0.90),   # the ring stamps as the face card hands off
    (13.05, "shine2", 0.066, 0.80),   # "30" lands on its word
    (13.61, "srev3",  0.06, 0.55),
    (14.79, "wsh2",   0.072, 0.50),
    (16.73, "stick1", 0.054, 0.40),
    (18.63, "rise3",  0.048, 1.20),   # into the pricing act
    (18.99, "imp5",   0.084, 0.90),
    (20.17, "wsh4",   0.066, 0.55),   # the price axis draws
    (20.42, "srev3",  0.048, 0.55),
    (22.51, "wsh1",  0.054, 0.75),   # the b-roll strip
    (22.69, "sacc2",  0.066, 0.40),   # $12 arrives
    (22.80, "sui1",   0.054, 0.35),
]

# ---------------------------------------------------------------------------
# c6  139.23-168.27   the shared price rail · the verdict · the trade-off
# ---------------------------------------------------------------------------
C6 = [
    (1.23, "sacc3",  0.066, 0.40),   # $7.99 lands under the axis
    (1.32, "sclick", 0.054, 0.35),
    (1.89, "wsh6",   0.054, 0.75),   # the b-roll steps out, the face returns
    (4.37, "tick1", 0.054, 0.40),
    (8.25, "wsh3",   0.06, 0.45),
    (8.59, "tick6",  0.054, 0.40),
    (14.51, "sacc1",  0.066, 0.45),   # the Unlimited knob
    (16.03, "stick1", 0.06, 0.45),   # $14.99
    (17.45, "swsh1",  0.072, 0.60),
    (17.69, "simp1",  0.084, 0.80),   # the verdict headline
    (18.97, "srev2",  0.066, 0.55),   # tick 1
    (21.39, "srev3",  0.066, 0.55),   # tick 2
    (23.12, "sui1",   0.054, 0.35),
    (23.95, "srise1", 0.048, 1.05),   # into the trade-off act
    (24.45, "simp2",  0.078, 0.90),
    (26.43, "wsh1",  0.06, 0.50),
]

# ---------------------------------------------------------------------------
# c7  168.27-197.47   the trade-off spine · the verdict · three reasons
# ---------------------------------------------------------------------------
C7 = [
    (0.12, "wsh5",   0.06, 0.80),   # the spine grows
    (0.72, "wsh3",   0.054, 0.45),   # the left branch
    (1.65, "sclick", 0.06, 0.30),   # each item on the left
    (3.19, "tick4",  0.06, 0.40),
    (4.79, "stick1", 0.06, 0.40),
    (7.53, "sgear",  0.054, 0.50),
    (8.88, "swsh1",  0.06, 0.50),   # the right branch
    (10.89, "pop1",   0.066, 0.30),   # each item on the right
    (16.47, "sacc2",  0.066, 0.35),
    (18.17, "simp2",  0.09, 1.05),   # the verdict
    (18.61, "srev1",  0.06, 0.80),
    (21.17, "wsh1",  0.066, 0.50),
    (21.89, "srev2",  0.066, 0.55),   # reason 01
    (23.35, "ok2",    0.066, 0.55),   # reason 02
    (25.05, "srev3",  0.066, 0.55),   # reason 03
    (25.20, "shine2", 0.054, 0.75),
]

# ---------------------------------------------------------------------------
# c8  197.47-223.40   the recommendation · the coupon · the outro
# ---------------------------------------------------------------------------
C8 = [
    (0.03, "sui1",   0.054, 0.35),
    (5.93, "simp2",  0.09, 0.95),   # the one card in the film presses in
    (6.05, "srev1",  0.06, 0.80),
    (6.37, "sgear",  0.06, 0.50),   # the code chip
    (6.57, "sclick", 0.054, 0.30),   # N A D E R, one tick each
    (6.63, "stick1", 0.048, 0.30),
    (6.69, "tick1", 0.048, 0.30),
    (6.74, "tick6",  0.048, 0.30),
    (6.80, "tick2",   0.054, 0.35),
    (7.23, "imp1",  0.096, 1.05),   # 60% OFF lands
    (7.89, "sacc1",  0.054, 0.35),
    (9.13, "wsh3",   0.054, 0.45),
    (9.51, "srev3",  0.06, 0.55),   # the guarantee pill
    (10.09, "wsh1",   0.066, 0.55),
    (10.51, "srev2",  0.06, 0.55),
    (14.59, "ok1",  0.06, 0.55),
    (18.55, "srise1", 0.048, 1.20),   # into the outro
    (20.31, "simp1",  0.084, 0.85),
    (21.89, "wsh2",  0.066, 0.80),   # the crowd cut
    (22.77, "simp3",  0.078, 0.80),
    (24.33, "wsh6",   0.06, 0.70),
    (24.38, "shine2", 0.06, 0.85),
]

CUES = {"c1": C1, "c2": C2, "c3": C3, "c4": C4, "c5": C5,
        "c6": C6, "c7": C7, "c8": C8}


def check(chunk, cues):
    """Refuse to inject a bed that breaks the budget. Round 1 drifted loud one
    nudge at a time; a gate is the only thing that holds a mix spec."""
    n = len(cues)
    share = collections.Counter(f for _, f, _, _ in cues)
    vols = sorted(v for _, _, v, _ in cues)
    med, ceil = st.median(vols), max(vols)
    errs = []
    for f, c in share.most_common():
        if c / n > CAP_SHARE + 1e-9:
            errs.append(f"{f} is {c}/{n} = {100*c/n:.1f}% of placements (cap {100*CAP_SHARE:.1f}%)")
    if med > MEDIAN_MAX:  errs.append(f"median volume {med:.3f} > {MEDIAN_MAX}")
    if ceil > CEIL_MAX:   errs.append(f"ceiling volume {ceil:.3f} > {CEIL_MAX}")
    for t, f, v, d in cues:
        if d > 1.5 and v > BED_MAX:
            errs.append(f"{f} at {t}s is a {d}s bed at {v} (cap {BED_MAX})")
    for t, f, v, d in cues:
        if f in ("thud", "riser", "riser2", "boom", "cboom"):
            errs.append(f"{f} is retired — the owner named it")
    print(f"{chunk}: {n} placements · {len(share)} distinct · "
          f"median {med:.3f} · ceiling {ceil:.3f}")
    print("   top: " + ", ".join(f"{f}x{c}" for f, c in share.most_common(5)))
    return errs


def main():
    chunk = sys.argv[1]
    cues = sorted(CUES[chunk], key=lambda c: c[0])
    errs = check(chunk, cues)
    if errs:
        print("  !! SFX budget violated:")
        for e in errs: print("     " + e)
        sys.exit(1)

    here = os.path.dirname(os.path.abspath(__file__))
    import subprocess
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
            f'  <audio id="{chunk}sfx{i}" data-start="{t:.2f}" data-duration="{d:.2f}" '
            f'data-track-index="{19+i}" src="assets/sfx/{f}.mp3" data-volume="{v:.2f}"></audio>')
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
