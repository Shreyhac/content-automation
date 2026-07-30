#!/usr/bin/env python3
"""Splice the short's VO out of the long-form master, and remap the word timings.

Source: hf46/assets/vo-master.wav (48k mono PCM, 223.404s, already denoised and
loudnorm'd for the film). We cut it, we do not re-process it, except for a final
two-pass loudnorm because concatenation changes the integrated loudness.

WHAT CHANGED FROM v1 (the "audio sentences are not clear" fix)
--------------------------------------------------------------
1. Every cut is now sentence-end to sentence-start, so both sides of a join have a
   natural fall and a natural rise. beats.py asserts it.
2. Every beat runs PAST its sentence into the master's own following silence, so no
   spoken word is clipped by whisper's undershooting end timestamps. v1 cut on those
   marks and amputated word tails.
3. 25ms fades at each edge, not v1's 8ms. Every edge now sits in measured room tone
   rather than on a word onset, so a longer fade is free and it kills the click.
4. Where a sentence has nowhere to fall into (b6: s23 begins the instant s22 ends;
   b10: s40 would bleed in), the remainder of the beat is ROOM TONE lifted from a
   clean stretch of the master (50.70s, mean -44.8 dB) rather than a butt-splice.
   That is what makes the result sound like one take instead of ten splices.

Writes:
  assets/vo.wav          the spliced VO, exactly total/30 s long
  words.json             word timings remapped onto the short timeline
  segments.json          the flat segment list (also read by build_captions.py)
"""
import json, subprocess, os
from beats import resolve, FPS

SRC = "../hf46/assets/vo-master.wav"
WORDS = "../hf46/words.json"
FADE = 0.025

beats, total = resolve()
os.makedirs("assets", exist_ok=True)

# ---- flat segment list with the short-timeline offset of each ---------------------
segs = []
t = 0.0
for b in beats:
    for a, bb in b["seg"]:
        segs.append(dict(beat=b["n"], a=a, b=bb, at=t, dur=bb - a))
        t += bb - a
assert abs(t - total / FPS) < 1e-9, (t, total / FPS)
json.dump(segs, open("segments.json", "w"), indent=1)

# ---- audio ------------------------------------------------------------------------
parts, filt = [], []
for i, s in enumerate(segs):
    fade = min(FADE, s["dur"] / 3)
    filt.append(f"[0:a]atrim=start={s['a']:.6f}:end={s['b']:.6f},asetpts=N/SR/TB,"
                f"afade=t=in:st=0:d={fade:.6f},"
                f"afade=t=out:st={max(0, s['dur']-fade):.6f}:d={fade:.6f}[a{i}]")
    parts.append(f"[a{i}]")
filt.append("".join(parts) + f"concat=n={len(segs)}:v=0:a=1[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC,
                "-filter_complex", ";".join(filt), "-map", "[out]",
                "-c:a", "pcm_s16le", "assets/vo-raw.wav"], check=True)

# two-pass loudnorm to the short spec
p = subprocess.run(["ffmpeg", "-v", "info", "-i", "assets/vo-raw.wav", "-af",
                    "loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True)
j = json.loads(p.stderr[p.stderr.rindex("{"):p.stderr.rindex("}") + 1])
print("pass 1:", {k: j[k] for k in ("input_i", "input_tp", "input_lra")})
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "assets/vo-raw.wav", "-af",
                f"loudnorm=I=-14:TP=-1.0:LRA=9:linear=true:"
                f"measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
                f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:"
                f"offset={j['target_offset']}",
                "-ar", "48000", "-c:a", "pcm_s16le", "assets/vo.wav"], check=True)

os.remove("assets/vo-raw.wav")        # intermediate; assets/vo.wav is the one that ships
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", "assets/vo.wav"],
                         capture_output=True, text=True).stdout.strip())
print(f"assets/vo.wav {d:.4f}s  (target {total/FPS:.4f}s, "
      f"delta {abs(d-total/FPS)*1000:.1f}ms)")

# ---- words ------------------------------------------------------------------------
src = json.load(open(WORDS))
out = []
for s in segs:
    for w in src:
        # a word belongs to the segment that contains its midpoint
        mid = (w["start"] + w["end"]) / 2
        if s["a"] <= mid < s["b"]:
            out.append(dict(word=w["word"],
                            start=round(max(0.0, w["start"] - s["a"]) + s["at"], 4),
                            end=round(min(s["dur"], w["end"] - s["a"]) + s["at"], 4),
                            beat=s["beat"]))
out.sort(key=lambda w: w["start"])
for i in range(1, len(out)):                      # never let a word end after the next starts
    if out[i - 1]["end"] > out[i]["start"]:
        out[i - 1]["end"] = out[i]["start"]

# ---- token repair -----------------------------------------------------------------
# Whisper splits hyphens, decimals and percent signs into their own tokens, which is how
# the film's round-2 build printed "$7 .99" and "30 -day" on screen and opened clips on a
# bare hyphen. Merge any token that cannot begin a word into the one before it.
CONT = ("-", ".", "%", "'")
merged = []
for w in out:
    if merged and w["word"].startswith(CONT) and not w["word"].startswith("..."):
        merged[-1]["word"] += w["word"]
        merged[-1]["end"] = w["end"]
    else:
        merged.append(dict(w))
# he says NADER; whisper hears NAUTTER. It is a coupon code: it must never reach the screen wrong.
for w in merged:
    if w["word"].upper().strip(".,") in ("NAUTTER", "NAUGHTER", "NADDER"):
        w["word"] = "NADER"
# whisper drops a comma after "Report" that is not in the speech and makes the burned
# caption read as a typo ("An independent Deloitte Assurance Report, confirmed ...").
# Punctuation is the ONLY thing corrected here; no word is ever changed or removed.
for i, w in enumerate(merged):
    if w["word"] == "Report," and i + 1 < len(merged) and merged[i + 1]["word"] == "confirmed":
        w["word"] = "Report"
out = merged
json.dump(out, open("words.json", "w"), indent=1)

# ---- guard: every beat got exactly its own sentence, whole ------------------------
print(f"words.json {len(out)} words, last ends {out[-1]['end']:.3f}")
bad = 0
for b in beats:
    ws = [w for w in out if w["beat"] == b["n"]]
    got = " ".join(w["word"] for w in ws)
    want = " ".join(b["words"]).replace(" -", "-").replace(" %", "%")
    want = want.replace("NAUTTER", "NADER").replace("Report, confirmed", "Report confirmed")
    flag = "" if got == want else "   !! MISMATCH"
    if flag:
        bad = 1
        print(f"     want: {want}")
    print(f"  {b['n']:4} {len(ws):3} words: {got}{flag}")
assert not bad, "a beat did not receive exactly its own sentence"
print("\nguard passed: each beat carries exactly one complete sentence.")
