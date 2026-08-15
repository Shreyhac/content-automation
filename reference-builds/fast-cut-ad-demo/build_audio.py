#!/usr/bin/env python3
"""
The client film 2 ("six tools") — audio bed.

Built here, NOT in the renderer: HyperFrames leaks video tracks when <video> and
<audio> point at the same file, so the composition renders picture-only and this
WAV is muxed on afterwards.

Three branches:
  VO     assets/vo/aroll.m4a laid at 0, UNITY GAIN, NO FILTERS. The presenter's A-roll audio is
         not denoised, EQ'd or loudnormed — that is the standing rule and the plan's
         own commitment. The composition clock is the A-roll clock 1:1 (verified by
         frame-matching every shot back to the master), so it lands at 0 and stays.
  MUSIC  assets/music/bed.mp3 from 15.99s. That offset puts the track's lift at 30.45s
         onto composition 14.46 — the frame the client product is first revealed — so the whole back
         half of the film rides the strong section and carries into the endcard.
         Ducked under the VO by a sidechain keyed off the voice.
  SFX    cue table below. Every cue is trimmed to its own attack: these one-shots have
         up to 236ms of lead-in and several SWELL rather than hit, so a naive placement
         lands the audible part late. mode="hit" aligns the attack to the cue,
         mode="peak" aligns the loudest moment to it (used for whooshes and the
         endcard impact, which have to bloom ON the cut, not after it).
"""
import json
import subprocess
import sys
import numpy as np

A = "assets"
OUT = "bed.wav"
DUR = 37.7667         # extended for the client outro clip (33.8667 + 3.90)
# Round-3: the "typing sfx still there" was the MUSIC — the old bed.mp3 carries a
# metronomic 0.465s tick pattern through the whole back half (measured: 75
# transients, 39% metronomic). Swapped to gear.mp3, video 1's own approved bed
# (30 transients, the least ticky of the four candidates). 41.5s >= DUR, so it
# plays from 0 with no offset.
MUSIC = "gear.mp3"
MUSIC_SS = 0.5   # skip the track's soft head — music must be present immediately
SR = 48000

# ── SFX cues ────────────────────────────────────────────────────────────────
# Round-2 note, verbatim: "told you to remove the typing sfx from the whole
# video". Every cue in the click/tick family (sclick, sui1, stick1, sacc3 —
# classified by measured envelope: <=0.13s audible or <=50ms attack) is GONE
# from the whole film. Only whooshes, impacts, the riser and the shine remain.
# Do not reintroduce any of the four files.
# (file, composition time, volume, mode)  volumes stay in the 0.09–0.30 band.
CUES = []
# Round-5, and FINAL: five timestamped notes (14.32, 17.31, 19.03, 21.43, 33.85)
# landed exactly on the five remaining whoosh/impact cues. To the owner, every
# audible cue IS "the typing sfx". The bed is now VOICE + MUSIC ONLY. Do not add
# any SFX cue back into this film, of any kind, ever.

# Round-2 note, verbatim: "remove the typing audio". The keyboard bed that ran
# 21.98-23.91 under the composer is GONE — do not reintroduce it. The typing
# stays visual-only.


def envelope(path):
    """attack onset and loudest-moment time, in seconds from file start."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if x.size == 0:
        raise SystemExit(f"empty audio: {path}")
    a = np.abs(x)
    pk = a.max()
    above = np.where(a > 0.12 * pk)[0]
    onset = max(0.0, (above[0] / SR) - 0.012) if above.size else 0.0
    w = int(SR * 0.03)
    sm = np.convolve(a, np.ones(w) / w, "same")
    peak_t = float(sm.argmax()) / SR
    return round(onset, 4), round(max(peak_t, onset), 4)


def main():
    # ROUND 7: the whole mix is computed in numpy. ffmpeg's sidechaincompress in
    # this build truncates its output near the KEY's real (unpadded) end no
    # matter how the key is padded (bisected: main 37.77s + key 39.77s -> out
    # 34.81s), which silently cut the music at ~35s — the client's "why did the
    # music end here" note. Sample math has no such quirk and every branch is
    # verifiable. The outro clip's audio track was probed and is DIGITAL SILENCE,
    # so it is deliberately not mixed.
    import numpy as np

    def decode(path, ss=None):
        a = ["-ss", str(ss)] if ss else []
        raw = subprocess.run(["ffmpeg", "-v", "error"] + a + ["-i", path,
            "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
            capture_output=True).stdout
        return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).astype(np.float64)

    N = int(round(DUR * SR))
    out = np.zeros((N, 2))

    # VO — untouched, unity, laid at 0 (the standing rule: no filters, no gain)
    vo = decode(f"{A}/vo/aroll.m4a")[:N]
    out[: len(vo)] += vo

    # music: static gain to a bed level ~13 dB under the voice (matches the old
    # loudnorm I=-27 target within ~1 dB for this steady track), ducked under
    # the VO by an envelope follower, faded in 0.9s and out over the last 0.85s.
    mus = decode(f"{A}/music/{MUSIC}", ss=MUSIC_SS if MUSIC_SS else None)[:N]
    if len(mus) < N:
        mus = np.vstack([mus, np.zeros((N - len(mus), 2))])
    target_rms = 10 ** (-27 / 20)
    mus *= target_rms / (np.sqrt((mus ** 2).mean()) + 1e-12)

    # envelope follower on the VO (attack 18ms, release 380ms), then gain
    e = np.abs(vo).mean(axis=1)
    if len(e) < N:
        e = np.concatenate([e, np.zeros(N - len(e))])
    env = np.empty(N)
    a_at = np.exp(-1.0 / (SR * 0.018)); a_rl = np.exp(-1.0 / (SR * 0.380))
    prev = 0.0
    for i in range(N):
        c = a_at if e[i] > prev else a_rl
        prev = c * prev + (1 - c) * e[i]
        env[i] = prev
    TH, RATIO = 0.055, 5.0
    over = np.maximum(env / TH, 1.0)
    gain = over ** (-(RATIO - 1) / RATIO)          # 1.0 below threshold
    mus *= gain[:, None]

    t = np.arange(N) / SR
    fade = np.clip(t / 0.35, 0, 1) * np.clip((DUR - t) / 0.85, 0, 1)
    mus *= np.clip(fade, 0, 1)[:, None]
    out += mus

    # (outro2.mp4 audio: measured -240 dBFS across its 3.9s — nothing to add)

    peak = np.abs(out).max()
    if peak > 0.97:
        out *= 0.97 / peak
    pcm = (np.clip(out, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(OUT, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", OUT], capture_output=True, text=True).stdout.strip()
    print(f"bed.wav built — {dur}s · numpy mix · music from {MUSIC_SS}s · music runs to the end")


if __name__ == "__main__":
    sys.exit(main())
