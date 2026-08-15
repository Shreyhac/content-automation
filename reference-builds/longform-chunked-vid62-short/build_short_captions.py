#!/usr/bin/env python3
"""Captions for the short, remapped from the SAME word stream as the long-form.

The short is nine cuts out of a 373s take, so a cue's timeline position is its source
time minus everything cut before it. Doing that by hand is how a caption track drifts
from the picture; doing it from short-beats.json is how it cannot.

It imports hf62/build_captions.py wholesale, so the short inherits every correction
the long-form's round-3 rebuild put in — "in Cogni" -> Incogni, "codewurd" -> CODEWORD,
the spelled-out C-O-D-E-W-O-R-D collapse, and the bare-number price repairs that the
regeneration pass exposed. A hand-typed caption here would silently drop all of them.

ONE BAND, NOT TWO. vid59's short needed a `.clo` band because its close was
full-bleed and the caption had to live under his jaw. This short has no full-bleed
beat — solve_short62.py rules one out on this take's own measurements — so every cue
sits in the middle band at y674-826, between the graphics zone and his crown at y838,
including on b6 where the picture is off and his dashboard occupies the picture's own
rect rather than the whole frame.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.abspath(os.path.join(HERE, "..", "hf62"))
sys.path.insert(0, LONG)
import build_captions as bc  # noqa: E402

BEATS = json.load(open(os.path.join(HERE, "..", "vid62", "short-beats.json")))
FPS_N, FPS_D = 24000, 1001

# a cue whose words are already printed large in the graphics zone is suppressed —
# never print the same words twice in one frame (the vid4/vid39 rule). Source spans.
MUTES = []

CLOSE_BEAT = 9   # b9 is the full-frame close; its cues use the .clo band
FLASH = 0.25       # a cue shorter than this is a flash, not a short caption
RUNT  = 0.62       # ...and a cue shorter than THIS, following another in the same
                   # beat, is a strobe rather than a beat of its own


def main():
    words = bc.fix_word_stream(bc.WORDS)
    out, emitted, t0, idx = [], [], 0.0, 0
    for bi, b in enumerate(BEATS, 1):
        a, z = b["a"], b["b"]
        n = int(round((z - a) * FPS_N / FPS_D))
        # A WORD MUST BEGIN INSIDE THE BEAT TO BE CAPTIONED. vid59's version admitted
        # any word ENDING within 0.30s of the cut, which is a rule about the L-cut's
        # audio tail applied to the caption track — and at b5's out-point it printed
        # "sites that" when "that" starts exactly on the cut and is never heard. A
        # caption for a word the viewer cannot hear is worse than a missing one: it
        # is the caption track disagreeing with the film.
        seg = [w for w in words
               if w["start"] >= a - 0.001 and w["start"] <= z - 0.05]
        for cur in bc.group(seg):
            cs, ce = cur[0]["start"], cur[-1]["end"]
            if ce <= a or cs >= z:
                continue
            cs, ce = max(cs, a), min(ce, z)
            local = t0 + (cs - a)
            beat_end = t0 + n * FPS_D / FPS_N
            dur = min(max(0.30, ce - cs), beat_end - local)
            if dur < 3 * FPS_D / FPS_N:
                continue
            if any(lo <= cs <= hi for lo, hi in MUTES):
                continue
            # SHORT CUES IN A ROW ARE A STROBE, NOT A CAPTION TRACK. His hook ends on
            # three sentence-final fragments — "It." / "Okay?" / "I'll wait." — and
            # the grouper breaks on every one of them, so the middle band flashed
            # three times in 1.2s. A cue under RUNT merges backwards into the cue it
            # follows, up to the grouper's own line budget; the merged cue keeps the
            # EARLIER start, so words appear no later than they are spoken.
            if (dur < RUNT and out and out[-1][0] == bi
                    and len(out[-1][3]) + len(cur) <= bc.MAXWORDS + 3
                    and local - (out[-1][1] + out[-1][2]) < 0.40):
                pb, pl, pd, pw = out[-1]
                out[-1] = (pb, pl, (local + dur) - pl, pw + cur)
                continue
            # a beat's last cue is the one that gets clipped, and a clipped cue is a
            # flash — merge the WORD LISTS back into the cue it belongs to
            if dur < FLASH and out and out[-1][0] == bi:
                pb, pl, pd, pw = out[-1]
                out[-1] = (pb, pl, (local + dur) - pl, pw + cur)
                continue
            out.append((bi, local, dur, list(cur)))
        t0 += n * FPS_D / FPS_N

    # THE EMITTED NUMBERS ARE THE CONTRACT, NOT THE COMPUTED ONES. A cue clamped to
    # its beat's end at full precision still prints as 49.6747 against a beat
    # boundary that prints as 49.6746, and `hyperframes lint` reads what is printed:
    # overlapping_clips_same_track on track 9. Clamp in the same 4-decimal space the
    # attribute is written in.
    for i, (bi, local, dur, cur) in enumerate(out):
        if i + 1 < len(out):
            nxt = round(out[i + 1][1], 4)
            if round(local, 4) + round(dur, 4) > nxt:
                out[i] = (bi, local, max(0.0, nxt - round(local, 4) - 0.0001), cur)

    for bi, local, dur, cur in out:
        idx += 1
        band = " clo" if bi >= CLOSE_BEAT else " hi"
        emitted.append('  <div id="sc%d" class="cs%s clip" data-start="%.4f" '
                       'data-duration="%.4f" data-track-index="9">%s</div>'
                       % (idx, band, local, dur, bc.render(cur)))
    print("\n".join(emitted))
    sys.stderr.write("%d caption clips over %.4fs\n" % (idx, t0))


if __name__ == "__main__":
    main()
