"""Shared audio measurement for the generative tools.

Nothing here calls an API. Every function is a measurement, because the rule the
whole `playbooks/generative-assets.md` doctrine rests on is: measure the
generated asset against the real thing it stands in for, band by band. An
eyeball pass approves a clone that is 17 percentage points of energy off in the
400 to 700 Hz band.
"""
import json
import re
import subprocess
import wave

import numpy as np

# Eight narrow bands, not one wide "consonant" band. A first fix on the client voice
# clone measured a single 2 to 5 kHz share, looked solved, and missed that the
# TTS was piling energy either side of the source voice: 250 to 400 Hz +6.5%,
# 700 to 1200 Hz +8%, 1200 to 2000 Hz +6.3%, while the source's own 400 to 700 Hz band
# carried 50% of total energy against the model's 33%.
BANDS = [
    (80, 250),
    (250, 400),
    (400, 700),
    (700, 1200),
    (1200, 2000),
    (2000, 3000),
    (3000, 5000),
    (5000, 8000),
]

# Total energy window. Everything below 80 Hz is room, everything above 15 kHz
# is mp3 cutoff, and neither belongs in a share denominator.
TOTAL_LO, TOTAL_HI = 80, 15000

SILENCE_NOISE_DB = -33
SILENCE_MIN_S = 0.13


def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", path])
    return float(out.decode().strip())


def decode_mono(path, sr=32000, tmp="/tmp/_genaudio.wav"):
    """Decode to mono float32 in [-1, 1]. ffmpeg does the resampling, not us."""
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path,
                    "-ac", "1", "-ar", str(sr), tmp], check=True)
    with wave.open(tmp) as f:
        raw = f.readframes(f.getnframes())
    return np.frombuffer(raw, dtype="<i2").astype(float) / 32768.0


def psd(path, sr=32000):
    """Welch-ish average power spectrum over voiced samples only.

    Silence is dropped before the FFT (|x| > 1e-4). Leaving it in drags every
    band share toward the noise floor's shape, which is exactly the thing the
    comparison is trying to see through.
    """
    x = decode_mono(path, sr)
    x = x[np.abs(x) > 1e-4]
    n = 1 << 14
    acc = np.zeros(n // 2 + 1)
    count = 0
    win = np.hanning(n)
    for i in range(0, len(x) - n, n // 2):
        acc += np.abs(np.fft.rfft(x[i:i + n] * win)) ** 2
        count += 1
    if count == 0:
        raise SystemExit(f"{path}: no voiced audio above the -80 dBFS floor")
    return acc / count, np.fft.rfftfreq(n, 1 / sr)


def band_shares(path, bands=BANDS, sr=32000):
    """Percentage of total 80 Hz to 15 kHz energy inside each band."""
    p, fr = psd(path, sr)
    total = p[(fr >= TOTAL_LO) & (fr < TOTAL_HI)].sum()
    return [100.0 * p[(fr >= lo) & (fr < hi)].sum() / total for lo, hi in bands]


def consonant_share(path, sr=32000):
    """The 2 to 5 kHz share. Kept because it is the single number that ranks
    clone references: denoising a 20.8s reference with afftdn before handing it
    to ElevenLabs cost 19% of this, and re-cloning from the untouched file on
    identical settings doubled it."""
    p, fr = psd(path, sr)
    total = p[(fr >= TOTAL_LO) & (fr < TOTAL_HI)].sum()
    return 100.0 * p[(fr >= 2000) & (fr < 5000)].sum() / total


def pauses(path, dur=None):
    """Interior silences, in seconds. Leading and trailing silence is excluded
    (0.15s margin) because it is an encode artefact, not delivery."""
    dur = dur if dur is not None else duration(path)
    log = subprocess.run(
        ["ffmpeg", "-i", path, "-af",
         f"silencedetect=noise={SILENCE_NOISE_DB}dB:d={SILENCE_MIN_S}",
         "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(v) for v in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(v) for v in re.findall(r"silence_end: ([\d.]+)", log)]
    return [round(e - s, 2) for s, e in zip(starts, ends)
            if s > 0.15 and e < dur - 0.15]


def speech_rate(path, word_count):
    """Words per second of ACTUAL SPEECH, pauses removed.

    Rate over wall duration is not comparable between takes: a take with four
    tagged breaks and a flat take with one 0.13s pause can read the same. The
    client's presenter measured 3.62 w/s of speech with clause pauses 0.20 to 0.54s,
    median 0.26s.
    """
    dur = duration(path)
    pz = pauses(path, dur)
    speech = max(dur - sum(pz), 0.01)
    return dur, pz, word_count / speech


TAG_RE = re.compile(r"<break[^>]*>|\[[a-zA-Z ]+\]")


# U+2014, written as an escape so the repo's no-em-dash grep stays at zero. It
# is data here, not prose: a script line that uses one gets counted as a word
# otherwise, and the words/sec measurement comes out low.
EM_DASH = "\u2014"


def plain_text(tagged):
    """Strip audio tags and break markers, leaving what should be SPOKEN."""
    return " ".join(TAG_RE.sub(" ", tagged).replace(EM_DASH, " ").split())


def normalise_words(text):
    t = re.sub(r"[^a-z' ]", " ", text.lower())
    return "".join(t.split())


def whisper_text(path, model="small", workdir="/tmp/_genvo_asr"):
    """Transcribe a candidate. Returns the heard text, lowercased.

    This runs BEFORE any quality scoring, always. eleven_multilingual_v2 speaks
    audio tags aloud: whisper caught it reading `<break time="0.45s"/>` as
    "you're a king". A candidate that loses on timbre but says the right words
    is fixable; one that says the wrong words is not, and sorting by quality
    first means auditioning nonsense.
    """
    subprocess.run(["whisper", path, "--model", model, "--output_format", "json",
                    "--output_dir", workdir, "--language", "en"],
                   capture_output=True)
    stem = path.split("/")[-1].rsplit(".", 1)[0]
    with open(f"{workdir}/{stem}.json") as f:
        return json.load(f)["text"].strip()
