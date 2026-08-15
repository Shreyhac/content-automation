#!/usr/bin/env python3
"""Assert that no word is chopped, and that no chopped word is smuggled in.

usage: python3 audio_guard.py [delivered.mp4]

WHY THIS EXISTS
---------------
A short is eight ranges cut out of a 352-second take, so every one of its seven joins is
a place where a word can be damaged, in two opposite ways — and the repo has now
shipped both of them, one round apart:

  * THE OUT-POINT CHOPS A WORD. At b2/b3 the presenter's "every one" was still at 0.129 RMS on the
    last sample and hit digital silence on the next. The beat plan was careful about
    this and still missed it, because it capped its tail scan at whisper's next-word
    MARK, and whisper's marks undershoot.

  * THE FIX FOR THAT SMUGGLES IN A WORD. The L-cut tail added to repair it measured
    only silence, so at b6/b7 — where there is no 60ms of silence to find, because
    "That's" starts 146ms after the cut — it ran to its cap and laid 124ms of the NEXT
    sentence's word over the close. A fragment of a word appearing where no word
    belongs is heard as a word being cut, which is how it was reported.

Both are inaudible to every other gate: the frame count is right, the loudness is
right, the captions match, and there is no drift. So this asks the four questions that
actually settle it, three against the MASTER and one against the DELIVERED mux.

The rule underneath both failures is one rule: ANY scan that walks forward from a cut
must be capped by the next word's onset, not by silence. vid58/short-beats.json says
it about the beat plan's own out-points; it belongs to every such scan.
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "hf59")))
import build_captions as bc  # noqa: E402

SR = 48000
FLOOR = 0.008          # noise floor of the cleaned master
SPEECH = 0.030         # above this at a cut edge, a word is being chopped
GUARD = 0.05           # a tail must stop this far short of the next word
MASTER = os.path.join(HERE, "..", "hf59", "assets", "vo-master.wav")


def load(path, raw):
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-i", path,
                    "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", raw], check=True)
    return np.fromfile(raw, dtype=np.float32)


def rms(a, t0, t1):
    s = a[int(t0 * SR):int(t1 * SR)]
    return float(np.sqrt((s ** 2).mean())) if len(s) else 0.0


def tail_len(a, t, cap=0.22, win=0.020):
    quiet = 0
    for k in range(int(cap / win)):
        quiet = quiet + 1 if rms(a, t + k * win, t + (k + 1) * win) < FLOOR else 0
        if quiet >= 3:
            return round((k + 1) * win, 3)
    return cap


def main():
    delivered = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "out",
                                                                   "vid59-short.mp4")
    beats = json.load(open(os.path.join(HERE, "beats.json")))["beats"]
    words = bc.fix_word_stream(bc.WORDS)
    m = load(MASTER, "/tmp/_ag_m.raw")
    d = load(delivered, "/tmp/_ag_d.raw")
    fail = []

    def onset_after(t):
        w = next((w for w in words if w["start"] > t + 0.002), None)
        return w["start"] if w else 1e9, (w["word"].strip() if w else "-")

    print("1. OUT-POINTS — is a word still sounding when the beat ends?\n")
    for p in beats[:-1]:
        out = p["a"] + p["dur"]
        pre = rms(m, out - 0.030, out)
        need = pre > SPEECH
        print("   b%-2d out %9.3f   %.4f RMS   %s"
              % (p["i"], out, pre, "chops a word -> needs a tail" if need else "clean"))

    print("\n2. TAILS — does any tail reach into the next word?\n")
    # Measure the tails the assembler ACTUALLY WROTE, not a recomputation of them.
    # The first version of this section recomputed the capped length and compared it
    # against its own cap, which is a test that cannot fail — the exact shape of the
    # bug that let `band_guard` report PASS having tested nothing at all.
    for p in beats[:-1]:
        out, at = p["a"] + p["dur"], p["t"] + p["dur"]
        ons, w = onset_after(out)
        room = max(0.0, ons - out - GUARD)
        f = os.path.join(HERE, ".assembly", "tail_%02d.wav" % p["i"])
        if not os.path.exists(f):
            print("   b%-2d join %8.3f   no tail emitted   next word %-12r at +%.0fms"
                  % (p["i"], at, w, (ons - out) * 1000))
            continue
        e = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                  "format=duration", "-of", "csv=p=0", f],
                                 capture_output=True, text=True).stdout.strip())
        bad = e > room + 0.002
        if bad:
            fail.append("b%d's %.0fms tail crosses into %r (only %.0fms of room)"
                        % (p["i"], e * 1000, w, room * 1000))
        print("   b%-2d join %8.3f   tail %3.0fms   next word %-12r at +%.0fms   %s"
              % (p["i"], at, e * 1000, w, (ons - out) * 1000,
                 "<<< STEALS %.0fms OF IT" % ((e - room) * 1000) if bad else "clear"))

    print("\n3. IN-POINTS — does a beat start inside a word already sounding?\n")
    for p in beats:
        t = p["a"]
        # only counts if the sound belongs to a word we KEEP; the decay of the
        # discarded sentence before it is not a clipped attack
        first = next((w for w in words if w["start"] >= t - 0.001), None)
        starts_on_word = first is not None and (first["start"] - t) < 0.02
        pre = rms(m, t - 0.030, t)
        bad = starts_on_word and pre > SPEECH
        if bad:
            fail.append("b%d in-point clips %r" % (p["i"], first["word"].strip()))
        print("   b%-2d in  %9.3f   %.4f RMS before   first word %-14r %s"
              % (p["i"], t, pre, first["word"].strip() if first else "-",
                 "<<< CLIPPED ATTACK" if bad else ""))

    print("\n4. DELIVERED — is any join still a cliff?\n")
    for i in range(len(beats) - 1):
        t = beats[i + 1]["t"]
        pre, post = rms(d, t - 0.030, t), rms(d, t, t + 0.020)
        ratio = pre / max(post, 1e-9)
        bad = pre > SPEECH and ratio > 6
        if bad:
            fail.append("b%d/b%d join is still a cliff" % (beats[i]["i"], beats[i + 1]["i"]))
        print("   b%d/b%d %8.3f   %.4f -> %.4f   x%.1f   %s"
              % (beats[i]["i"], beats[i + 1]["i"], t, pre, post, ratio,
                 "<<< CLIFF" if bad else "smooth"))

    print()
    if fail:
        print("  FAIL — %d problem(s):" % len(fail))
        for f in fail:
            print("    ✗ " + f)
        return 1
    print("  PASS — no word chopped at a cut, no word smuggled across one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
