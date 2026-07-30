#!/usr/bin/env python3
"""THE single source of truth for the vid46 vertical short — v2.

v1 was rejected. The main fault (see vid46-short-v2-brief.md §1.2) was that 9 of its
12 beats were sentence FRAGMENTS: the cut was made on word onsets inside sentences, so
beats opened mid-clause and closed on commas. The owner heard that as "audio sentences
are not clear".

  v2 RULE, ABSOLUTE: a beat is one or more COMPLETE SENTENCES from the film.
  Never a fragment, never an internal lift, never a trim.

`sent` cites an index into the film's 41-sentence list, which is regenerated from
../hf46/words.json at import and ASSERTED against every beat. If a beat's audio does
not begin exactly at its sentence's first word and cover its last word, this module
raises. That is the guard that makes 1.2 impossible to repeat.

TIMES are source times on the RE-CUT long-form timeline (223.400s), the same timeline
as hf46/words.json, hf46/face-safe-windows.json and vid46/r2/*.csv.

THE TIMELINE IS DEFINED IN FRAMES. Each beat's frame count is fixed; the audio
out-point is derived from it, so audio and video cannot drift.

WHY EACH BEAT IS LONGER THAN ITS SENTENCE
-----------------------------------------
Whisper's sentence-end timestamps UNDERSHOOT: "databases." is marked ending at 68.92
but the word is still decaying at -28 dB until 69.24, and s18's fall runs 0.28s past
its marked end. v1 cut on those marks and clipped the ends off spoken words. So every
beat runs past its sentence into the master's own following silence, measured with
volumedetect at 40ms resolution (see the `tail` note on each beat). Two beats cannot
do that because the next sentence starts immediately (b6) or would bleed in (b10);
those two get ROOM TONE lifted from a clean stretch of the master instead of a
butt-splice. That, plus 25ms edge fades, is what makes ten sentences sound like one
take rather than ten splices.

ACTS, AND THE FACE'S THREE STATES (v3)
--------------------------------------
v1 changed the face's placement 5 times, by CUTS, and his head changed size every time
he appeared. v2 answered that with one fixed band. v3 keeps the discipline but adopts
vid39's device, which the owner asked for by name: the face is ONE video with two
designed states, and it only ever moves between them as a visible, tweened camera move
(clip-path + scale together, 0.34s), never as a cut.

  HERO   the picture fills y0-1210 at s=0.56; chin sits at y1004 (worst y1100)
  CARD   the same picture scaled 0.6786 into a rounded portrait at x260-820,
         y850-1574 - vid39's floating card, re-solved for THIS head
  OFF    collapsed to nothing (graphics beats: the gaze map forbids his face)

SPLIT beats run CARD with the graphics above it (y150-640) and the caption in the gap
(y690-826), which is vid39's split-screen exactly. GFX beats run OFF and the graphics
own y150-1380 with the caption low. The sign-off runs HERO.

  A1  b1 b2      SPLIT  the hook: the record above, the face card below
  A2  b3 b4      GFX    Deloitte 420 vs Aura 200, on one rail
  A3  b5         SPLIT  the verdict, over the compressed rail
  A4  b6 b7 b8   GFX    the bundle, paying twice, the code
  A5  b9 HERO -> b10 GFX   the sign-off full, then the offer lockup

`mode` drives the face state, the graphics zone AND the caption position; `broll`
names a clip in hf46/assets/broll that is carded into the beat (never full-bleed).
"""
import json

FPS = 30
CANVAS = (1080, 1920)
WORDS_SRC = "../hf46/words.json"

# A clean stretch of the master with no speech in it: room tone, not digital silence.
# Measured mean -44.8 dB / peak -31.2 dB, the same floor as every other pause.
ROOM = 50.70

# name  sent  frames  audio in   face act    what
BEATS = [
 dict(n="b1", sent=0, f=99, a=0.00, act="A1", face=True, mode="SPLIT",
      say="your name, your address, and even your phone number.",
      tail="natural, to 3.30 (his own pause; s1 starts there, so A1 has NO internal "
           "splice at all and the picture cannot jump)",
      art="the record: NAME / ADDRESS / PHONE bars slide off on their word onsets, "
          "in the TALK graphics zone BELOW his face"),

 dict(n="b2", sent=1, f=111, a=3.30, act="A1", face=True, mode="SPLIT",
      say="Somebody can be pulling it all up in a single search.",
      tail="natural, to 7.00 (silence from 6.98; s2 starts 7.12)",
      art="the three rules light as one on 'pulling it all up'; the values collapse "
          "into one result row on 'single search'"),

 dict(n="b3", sent=13, f=247, a=61.04, act="A2", face=False, mode="GFX",
      broll="aisle",
      say="An independent Deloitte Assurance Report confirmed Incogni covers at "
          "least 420 data broker websites and private databases.",
      tail="natural, to 69.273. WHISPER CLIPPED THIS ONE: it marks 'databases.' "
           "ending at 68.92 but the word decays to -28 dB until 69.24",
      art="the seal stamps, then the shared rail draws and Incogni's knob travels "
          "to 420+, label right-aligned INTO frame"),

 dict(n="b4", sent=18, f=177, a=85.22, act="A2", face=False, mode="GFX",
      say="But when you look specifically at broker coverage, third-party reviews "
          "put Aura's list at over 200 sites.",
      tail="natural, to 91.12 (whisper marks 90.84; the fall runs to 91.08)",
      art="the SAME rail, never redrawn. Aura's knob at 200 in neutral, real "
          "wordmark, and the gap between the knobs becomes a measured length"),

 dict(n="b5", sent=19, f=242, a=91.40, act="A3", face=True, mode="SPLIT",
      say="So if your goal is getting your name off as many sites as possible and "
          "as many types of sites as possible, Incogni currently covers more ground.",
      tail="natural, to 99.467 (s20 starts 99.52; measured onset 99.50)",
      art="J-CUT: audio in at 91.40, face band wipes in at 91.70 per the gaze data. "
          "The rail compresses into the TALK zone so the verdict lands over its "
          "own evidence; a green seal stamps on 'covers more ground'"),

 dict(n="b6", sent=22, f=83, a=112.06, act="A4", face=False, room=True,
      mode="GFX", broll="bundle",
      say="Now, that sounds good on paper, but don't you already have a VPN?",
      tail="ROOM TONE, 5 frames. s23 begins the instant s22 ends (114.66), so this "
           "is the one beat with nowhere to fall into",
      art="Aura's bundle slabs pile with perspective"),

 dict(n="b7", sent=24, f=82, a=117.38, act="A4", face=False, mode="GFX",
      broll="pricing",
      say="If you do, you're basically paying twice for tools you don't need.",
      tail="natural, to 120.113 (dip at 120.12; s25's onset measures 120.32)",
      art="THE ONE HARD FLASH OF THE SHORT, on 'paying twice'. The strikes land on "
          "the slabs already on screen; nothing new arrives"),

 dict(n="b8", sent=36, f=123, a=203.40, act="A4", face=False, mode="GFX",
      say="You can use the code NADER for 60% off Incogni's annual plan.",
      tail="natural, to 207.50 (s37 starts 207.56)",
      art="the coupon: the ONE card in the short. NADER stamps on the word. It "
          "carries ANNUAL PLAN and the 30-DAY GUARANTEE because neither is spoken"),

 dict(n="b9", sent=38, f=100, a=216.02, act="A5", face=True, mode="HERO",
      say="Your data is already out there whether you like it or not.",
      tail="natural, to 219.353 (s39 starts 219.36, so A5 is continuous)",
      art="the face returns for the sign-off; the coupon holds as a chip below it. "
          "The band wipes out from 218.72, just before his gaze drops"),

 dict(n="b10", sent=39, f=86, a=219.36, act="A5", face=False, room=True,
      mode="GFX",
      say="So the question is, what are you going to do about it?",
      tail="ROOM TONE, 6 frames. s40 ('we'll see you in the next video') starts at "
           "222.08 and must not bleed in; the tone also gives the end card a hold",
      art="face out (gaze-forced: safe does not resume until 221.7). The chip "
          "expands into the full offer lockup and holds to the last frame"),
]

# chunks: (name, first beat index, last beat index inclusive)
# The rail spans beats 3-5, so those must share a chunk.
CHUNKS = [("s1", 0, 4), ("s2", 5, 9)]

# ---------------------------------------------------------------------------
# THE FACE BAND — one placement, three blocks. Source ranges are CONTINUOUS: a
# face block never contains an audio splice, so the picture can never jump-cut
# inside one. (This is why b1 runs to 3.30 rather than to 2.92: dropping his
# natural 0.38s pause would have put a 0.3s jump in the middle of the hook.)
#
#   src_a, src_b   source range, continuous
#   at             short-timeline start (derived below; must equal src_a's map)
#   clip           baked file name (1080x1210, the HERO crop; CARD is a transform
#                  of the same pixels, so both states come off one lanczos bake)
FACE_CLIPS = [
    dict(clip="a1", src_a=0.00,   src_b=7.0000,   beat="b1",
         note="whole of A1, 210 frames, no internal cut"),
    dict(clip="a3", src_a=91.70,  src_b=99.4667,  beat="b5",
         note="starts 0.30s into b5: gaze safe window is [91.7, 101.9], so the "
              "audio leads the picture by 9 frames. The only J-cut in the short."),
    dict(clip="a5", src_a=215.72, src_b=219.0533, beat="b9",
         note="starts 0.30s BEFORE b9's audio (safe from 215.3), so his face is "
              "already settled when the sign-off begins. It ends at 219.053, "
              "one frame past the end of the conceal wipe: his gaze drops from "
              "218.9, and the wipe starts at 218.72 and eats the band TOP-DOWN, so "
              "his eyes are already out of frame before the first downcast frame."),
]


# ---------------------------------------------------------------------------
def sentences():
    """The film's 41 sentences, straight off the master transcript."""
    w = json.load(open(WORDS_SRC))
    out, cur = [], []
    for x in w:
        cur.append(x)
        if x["word"].rstrip().endswith((".", "?", "!")):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def resolve():
    """Fill in every derived number and ASSERT the cut against the sentence list."""
    S = sentences()
    bounds = {i: (round(s[0]["start"], 3), round(s[-1]["end"], 3))
              for i, s in enumerate(S)}
    starts = sorted(b[0] for b in bounds.values())

    t = 0
    for b in BEATS:
        i = b["sent"]
        sa, sb = bounds[i]
        b["dur"] = b["f"] / FPS
        b["fa"], b["fb"] = t, t + b["f"]
        b["ta"], b["tb"] = t / FPS, (t + b["f"]) / FPS
        t += b["f"]

        assert abs(b["a"] - sa) < 1e-6, \
            f"{b['n']}: audio in {b['a']} != sentence {i} start {sa}"

        if b.get("room"):
            # sentence exactly, then room tone for the remainder of the frame count
            fill = b["dur"] - (sb - sa)
            assert fill > 0, (b["n"], fill)
            b["seg"] = [(sa, sb), (ROOM, ROOM + fill)]
            b["tail_to"] = sb
        else:
            end = sa + b["dur"]
            assert end >= sb - 1e-9, \
                f"{b['n']}: beat ends {end} before its sentence ends {sb}"
            nxt = min([s for s in starts if s > sa + 1e-6], default=1e9)
            assert end <= nxt + 1e-9, \
                f"{b['n']}: beat ends {end}, into sentence starting {nxt}"
            b["seg"] = [(sa, end)]
            b["tail_to"] = end

        got = sum(y - x for x, y in b["seg"])
        assert abs(got - b["dur"]) < 1e-9, (b["n"], got, b["dur"])
        b["words"] = [x["word"] for x in S[i]]
        b["sent_a"], b["sent_b"] = sa, sb

    # the face clips must map onto beats that actually show the face
    fmap = {b["n"]: b for b in BEATS}
    for c in FACE_CLIPS:
        b = fmap[c["beat"]]
        assert b["face"], c
        c["at"] = round(b["ta"] + (c["src_a"] - b["a"]), 6)
        c["frames"] = round((c["src_b"] - c["src_a"]) * FPS)
        c["dur"] = c["frames"] / FPS
        assert abs(c["dur"] - (c["src_b"] - c["src_a"])) < 1e-4, c
    return BEATS, t


def chunk_of(i):
    for name, lo, hi in CHUNKS:
        if lo <= i <= hi:
            return name
    raise KeyError(i)


def chunk_t0(name):
    beats, _ = resolve()
    for n, lo, hi in CHUNKS:
        if n == name:
            return beats[lo]["ta"]
    raise KeyError(name)


if __name__ == "__main__":
    beats, total = resolve()
    print(f"{'beat':5} {'sent':>4} {'frames':>6} {'short in':>9} {'dur':>6} "
          f"{'act':4} {'face':5} {'chunk':5} source")
    for i, b in enumerate(beats):
        segs = " + ".join(f"{a:.3f}-{bb:.3f}" for a, bb in b["seg"])
        print(f"{b['n']:5} {b['sent']:4} {b['f']:6} {b['ta']:9.3f} {b['dur']:6.3f} "
              f"{b['act']:4} {'FACE' if b['face'] else '-':5} {chunk_of(i):5} {segs}")
    print(f"\nTOTAL {total} frames = {total/FPS:.3f}s")
    for name, lo, hi in CHUNKS:
        f0, f1 = beats[lo]["fa"], beats[hi]["fb"]
        print(f"  {name}: frames {f0}-{f1}  {f1-f0} frames  {(f1-f0)/FPS:.3f}s  "
              f"beats {beats[lo]['n']}..{beats[hi]['n']}  (t0 {beats[lo]['ta']:.3f})")
    faced = sum(b["f"] for b in beats if b["face"])
    print(f"\nface on screen {faced} frames = {faced/FPS:.2f}s = {faced/total*100:.1f}%")
    print("\nface clips:")
    for c in FACE_CLIPS:
        print(f"  {c['clip']:3} src {c['src_a']:8.3f}-{c['src_b']:8.3f}  "
              f"{c['frames']:4}f  at short {c['at']:7.3f}  ({c['beat']})")
    print("\nacts:")
    cur, run = None, []
    for b in beats:
        if b["act"] != cur:
            if run:
                print(f"  {cur}  {sum(x['f'] for x in run):4}f "
                      f"{sum(x['f'] for x in run)/FPS:6.2f}s  "
                      f"{' '.join(x['n'] for x in run)}")
            cur, run = b["act"], []
        run.append(b)
    print(f"  {cur}  {sum(x['f'] for x in run):4}f "
          f"{sum(x['f'] for x in run)/FPS:6.2f}s  {' '.join(x['n'] for x in run)}")
    print("\nASSERTIONS PASSED: every beat is one complete sentence, in full, "
          "with a measured tail.")
