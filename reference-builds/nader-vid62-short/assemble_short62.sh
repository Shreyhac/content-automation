#!/usr/bin/env bash
# vid62 short — 1080x1920, 1432 frames @ 24000/1001 (59.7263s).
#
# Same split as the long-form: the render supplies PICTURE only and the audio is
# rebuilt beside it. The VO is cut from the SAME cleaned master the long-form uses,
# at the same eight ranges the picture was baked from, so the two cannot drift.
set -euo pipefail
cd "$(dirname "$0")"

OUT=../out/vid62-short.mp4
WORK=.assembly
FRAMES=1460
FPS_N=24000; FPS_D=1001
DUR=$(awk -v f=$FRAMES -v n=$FPS_N -v d=$FPS_D 'BEGIN{printf "%.6f", f*d/n}')

mkdir -p "$WORK" ../out
rm -f "$WORK"/vo.wav "$WORK"/sfx.wav "$WORK"/tails.wav "$WORK"/mix.wav

SRC=$(ls -t renders/*.mp4 2>/dev/null | head -1)
[ -n "$SRC" ] || { echo "no render found"; exit 1; }
N=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$SRC")
[ "$N" -eq "$FRAMES" ] || { echo "!! render is $N frames, planned $FRAMES"; exit 1; }
echo "--- render: $N frames, $(basename "$SRC") ---"

echo "--- 1. VO, cut from the long-form's master at the beat ranges ---"
python3 - "$WORK/vo.wav" <<'PY'
import json, os, subprocess, sys
out = sys.argv[1]
beats = json.load(open("beats.json"))["beats"]
parts = []
for p in beats:
    d = p["n"] * 1001 / 24000.0
    f = ".assembly/vo_%02d.wav" % p["i"]
    # -ss BEFORE -i so the seek is on the input; the cut is frame-derived, never
    # taken from the whisper mark, because whisper sentence-ends undershoot
    # b7's in-point has NO silence in front of it — "point" ends on the frame
    # "Incogni" begins, which is the price of dropping the dangling "And on that
    # specific outcome" the client marked. A hard start on a vowel clicks, so its
    # own head gets 45ms of fade. st=0 here is the head of THIS SEGMENT; the same
    # filter with an absolute st on the assembled track silences everything before
    # it, which is how the first 46 seconds of the film went quiet once.
    af = ["-af", "afade=t=in:st=0:d=0.045:curve=qsin"] if p["id"] == "b7" else []
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                    "-ss", "%.6f" % p["a"], "-i", "../hf62/assets/vo-master.wav",
                    "-t", "%.6f" % d, *af, "-c:a", "pcm_s16le", f], check=True)
    parts.append(f)
lst = ".assembly/vo_list.txt"
open(lst, "w").write("".join("file '%s'\n" % os.path.abspath(x) for x in parts))
subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat",
                "-safe", "0", "-i", lst, "-c:a", "pcm_s16le", out], check=True)
got = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
print("    nine beats -> %ss" % got)
PY

echo "--- 1b. word tails across the joins (vid58 round 2, notes 1 and 2) ---"
python3 - "$WORK/tails.wav" "$DUR" <<'TAILPY'
"""A beat's out-point lands on a word ONSET, and a word's SOUND does not stop where
whisper says the word stops. At the b2/b3 join his "every one" was still at 0.129 RMS
on the last sample and hit digital silence on the next. The owner's note was "the word
everyone has weird cut in the audio", and he was exactly right.

The fix is not to move the cut — the picture is locked to it. It is an L-CUT: the tail
of the outgoing beat carries a little way over the incoming one, faded, which is what
an editor would do by hand and what makes a hard join sound intentional rather than
chopped.

The tail length is MEASURED per join rather than chosen, and it is capped TWICE:

  1. by SILENCE  — extend until the signal has been under the noise floor for three
     consecutive 20ms windows, max 0.22s;
  2. by the NEXT WORD'S ONSET — minus a 50ms guard.

The second cap is not belt-and-braces, it is the whole thing. The first version had
only the silence test, and at the b6/b7 join there IS no 60ms of silence to find:
"That's" starts 146ms after the out-point, so the scan ran to its 220ms cap and laid
124ms of a word that belongs to the next sentence over the close. A fragment of a word
appearing where no word should be is heard as a word being cut.

vid58/short-beats.json already says this about the beat plan's own out-points — "a
tail scan that can cross a word boundary is not recovering a tail, it is stealing a
word" — and this scan could cross a word boundary. The rule belongs to any scan that
walks forward from a cut, not just to the one that first needed it.
"""
import json, os, subprocess, sys, numpy as np
sys.path.insert(0, os.path.abspath("../hf62"))
import build_captions as bc
out, dur = sys.argv[1], float(sys.argv[2])
beats = json.load(open("beats.json"))["beats"]
WORDS = bc.fix_word_stream(bc.WORDS)
GUARD = 0.05


def next_onset(t):
    """When does the next word actually start? The tail may not reach it."""
    w = next((w for w in WORDS if w["start"] > t + 0.002), None)
    return w["start"] if w else 1e9
subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                "-i", "../hf62/assets/vo-master.wav", "-ac", "1", "-ar", "48000",
                "-f", "f32le", ".assembly/vo_mono.raw"], check=True)
a = np.fromfile(".assembly/vo_mono.raw", dtype=np.float32)
sr, FLOOR, WIN, CAP = 48000, 0.008, 0.020, 0.22


def tail_len(t):
    quiet = 0
    for k in range(int(CAP / WIN)):
        seg = a[int((t + k * WIN) * sr):int((t + (k + 1) * WIN) * sr)]
        r = float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0
        quiet = quiet + 1 if r < FLOOR else 0
        if quiet >= 3:
            return round((k + 1) * WIN, 3)
    return CAP


ins, fl, mix, n = [], [], [], 0
for p in beats[:-1]:
    src_out, at = p["a"] + p["dur"], p["t"] + p["dur"]
    room = max(0.0, next_onset(src_out) - src_out - GUARD)
    e = min(tail_len(src_out), room)
    # 40ms WAS THE FLOOR AND IT WAS TOO HIGH. b1's join is the only out-point in this
    # cut with less than that of room — "…and sell it." is cut at 0.0677 RMS and the
    # next sentence's "They" starts 89ms later, leaving 39ms after the 50ms word
    # guard. The envelope says the word is DONE inside that window (0.046 -> 0.016 ->
    # 0.009 -> 0.002 across four 20ms frames), so 39ms is not a scrap, it is the whole
    # remaining tail. Refusing to write it left the film's OPENING join measuring a
    # 5.5x step in the delivered mux — the largest of the seven, on the join a viewer
    # hears first, in a film whose last two client notes were both chopped words.
    if e < 0.02:
        print("    b%d join at %.3f: no tail (%.0fms of room)" % (p["i"], at, room * 1000))
        continue
    f = ".assembly/tail_%02d.wav" % p["i"]
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", "%.6f" % src_out,
                    "-i", "../hf62/assets/vo-master.wav", "-t", "%.6f" % e,
                    # HOLD, then fade. An exponential fade from t=0 is already
                    # well down by 100ms, which attenuated the release of
                    # "automatically" — whisper-medium heard the delivered word as
                    # "automatic". The tail is the same voice continuing, so it plays
                    # at full level for the first 60% and only fades so its own END is
                    # not a second hard stop.
                    "-af", "afade=t=out:st=%.6f:d=%.6f:curve=qsin" % (e * 0.6, e * 0.4),
                    "-c:a", "pcm_s16le", f], check=True)
    ins += ["-i", f]
    fl.append("[%d:a]adelay=%d|%d,volume=1.0[t%d]" % (n, int(at * 1000),
                                                       int(at * 1000), n))
    mix.append("[t%d]" % n)
    n += 1
    print("    b%d join at %.3f: %.0fms tail, faded out (silence %.0f, next word %.0f)"
          % (p["i"], at, e * 1000, tail_len(src_out) * 1000, room * 1000))
if not n:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=48000:cl=stereo", "-t", "%.6f" % dur,
                    "-c:a", "pcm_s16le", out], check=True)
    raise SystemExit
fl.append("".join(mix) + "amix=inputs=%d:normalize=0:dropout_transition=0[m]" % n)
fl.append("[m]apad=whole_dur=%.6f,atrim=0:%.6f,aformat=sample_fmts=s16:"
          "sample_rates=48000:channel_layouts=stereo[out]" % (dur, dur))
subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", *ins,
                "-filter_complex", ";".join(fl), "-map", "[out]",
                "-t", "%.6f" % dur, "-c:a", "pcm_s16le", out], check=True)
TAILPY

echo "--- 2. SFX bed from index.html (never from the render) ---"
python3 - "$WORK/sfx.wav" "$DUR" <<'PY'
import re, subprocess, sys
out, dur = sys.argv[1], float(sys.argv[2])
html = open("index.html").read()
cues = re.findall(r'<audio\b[^>]*?src="(assets/sfx/[^"]+)"[^>]*?data-start="([0-9.]+)"'
                  r'[^>]*?data-volume="([0-9.]+)"', html, re.S)
if not cues:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "anullsrc=r=48000:cl=stereo", "-t", "%.6f" % dur,
                    "-c:a", "pcm_s16le", out], check=True)
    print("    no cues declared; silent bed"); raise SystemExit
ins, fl, mix = [], [], []
for i, (src, t, v) in enumerate(cues):
    ins += ["-i", src]
    fl.append("[%d:a]adelay=%d|%d,volume=%s[a%d]" % (i, int(float(t)*1000),
                                                     int(float(t)*1000), v, i))
    mix.append("[a%d]" % i)
fl.append("".join(mix) + "amix=inputs=%d:normalize=0:dropout_transition=0[m]" % len(cues))
# `apad` with no length is an INFINITE source, and a bare `atrim` downstream does
# not reliably end the graph: the thirteen-cue version of this mix spun at 99% CPU
# for nine minutes and wrote a short file. Bound the pad itself AND put -t on the
# output, so termination does not depend on a filter noticing it is done.
fl.append("[m]apad=whole_dur=%.6f,atrim=0:%.6f,aformat=sample_fmts=s16:"
          "sample_rates=48000:channel_layouts=stereo[out]" % (dur, dur))
subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", *ins,
                "-filter_complex", ";".join(fl), "-map", "[out]",
                "-t", "%.6f" % dur, "-c:a", "pcm_s16le", out], check=True)
print("    %d cues" % len(cues))
PY

echo "--- 3. mix, two-pass loudnorm ---"
MIXF="[0:a]atrim=0:$DUR,asetpts=PTS-STARTPTS[vo]; \
      [1:a]atrim=0:$DUR,asetpts=PTS-STARTPTS[sx]; \
      [2:a]atrim=0:$DUR,asetpts=PTS-STARTPTS[tl]; \
      [vo][sx][tl]amix=inputs=3:duration=first:dropout_transition=0:weights='1 0.9 1'[m]"
LN=$(ffmpeg -hide_banner -nostats -i "$WORK/vo.wav" -i "$WORK/sfx.wav" -i "$WORK/tails.wav" \
      -filter_complex "$MIXF; [m]loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json[out]" \
      -map "[out]" -f null - 2>&1 | awk '/^\{/{f=1} f{print} /^\}/{if(f)exit}')
read -r I_I I_TP I_LRA I_TH I_OFF <<<"$(printf '%s' "$LN" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d['input_i'],d['input_tp'],d['input_lra'],d['input_thresh'],d['target_offset'])")"
echo "    measured I=$I_I TP=$I_TP LRA=$I_LRA"
ffmpeg -y -i "$WORK/vo.wav" -i "$WORK/sfx.wav" -i "$WORK/tails.wav" \
  -filter_complex "$MIXF; [m]loudnorm=I=-14:TP=-1.0:LRA=9:measured_I=$I_I:measured_TP=$I_TP:measured_LRA=$I_LRA:measured_thresh=$I_TH:offset=$I_OFF:linear=true[out]" \
  -map "[out]" -c:a pcm_s16le "$WORK/mix.wav" -loglevel error

echo "--- 4. mux (no -shortest: it cost vid56 its last frame) ---"
ffmpeg -y -i "$SRC" -i "$WORK/mix.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart \
  "$OUT" -loglevel error

FINAL=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$OUT")
echo "--- done: $FINAL frames (want $FRAMES) ---"
[ "$FINAL" -eq "$FRAMES" ] || { echo "!! delivered frame count is wrong"; exit 1; }
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate \
  -of default=noprint_wrappers=1 "$OUT"
echo -n "  delivered loudness: "
ffmpeg -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | tail -12 | grep -E "I:|LRA:" | tr '\n' ' '; echo
