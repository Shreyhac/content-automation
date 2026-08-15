#!/usr/bin/env python3
"""voice.py, the ElevenLabs clone and take pipeline.

    python3 tools/generative/voice.py clone   --sample ref.mp3 --name "Creator X" -o voice.json
    python3 tools/generative/voice.py takes   --config takes.json
    python3 tools/generative/voice.py sweep   --voice-id V --text-file line.txt
    python3 tools/generative/voice.py eqfit   --source real.wav --generated cand.mp3 -o eq-chain.txt
    python3 tools/generative/voice.py master  --in cand.mp3 --out vo.mp3 --eq eq-chain.txt

Key: read from the environment only, never from a file in the repo.

    export ELEVENLABS_API_KEY=...

`clone` needs a key carrying the `create_instant_voice_clone` permission. A
shared engine key generally does not have that scope, and the failure is a 401
at the /v1/voices/add call, not at TTS. Set ELEVENLABS_CLONE_API_KEY if the
clone-scoped key is a different one from the TTS key.

Every subcommand takes --dry-run, which prints the exact URL and request body
and sends nothing. Use it to check a config before spending a generation.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audio  # noqa: E402

import numpy as np  # noqa: E402

API = "https://api.elevenlabs.io/v1"

# eleven_v3 is mandatory the moment the text carries audio tags or breaks.
# eleven_multilingual_v2 SPEAKS THE TAGS ALOUD. v3 also dramatises short
# full-stop sentences, so a line of three-word sentences reads as a movie
# trailer: join them with commas before blaming stability.
DEFAULT_MODEL = "eleven_v3"
FALLBACK_MODEL = "eleven_multilingual_v2"

# Tuned on the client voice clone to keep a natural conversational cadence rather than
# smoothing it out. similarity_boost stays high because the point of a clone is
# the person, not a pleasant voice.
DEFAULT_SETTINGS = dict(stability=0.35, similarity_boost=0.85,
                        style=0.20, use_speaker_boost=True)

# Cost and latency measured on the fast-cut-ad UGC build, 2026: a 12 to 20 second line
# on eleven_v3 returned in 8 to 20s and billed roughly 1 credit per character.
# A four-candidate sweep of one line is therefore about 4x the line length in
# credits and under two minutes of wall time. A clone is free on a paid plan.


def key(clone=False):
    name = "ELEVENLABS_CLONE_API_KEY" if clone else "ELEVENLABS_API_KEY"
    k = os.environ.get(name) or os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        raise SystemExit(f"{name} is not set. Export it; do not put it in a file.")
    return k


def post_json(url, body, api_key, accept="audio/mpeg", timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "xi-api-key": api_key, "Content-Type": "application/json", "Accept": accept})
    return urllib.request.urlopen(req, timeout=timeout).read()


def show_request(url, body, headers_note="xi-api-key: <from ELEVENLABS_API_KEY>"):
    print(f"POST {url}")
    print(f"  {headers_note}")
    print("  Content-Type: application/json")
    print(json.dumps(body, indent=2))


# ---------------------------------------------------------------- clone -----

def cmd_clone(a):
    """Instant voice clone from ONE untouched reference file.

    NEVER pre-process the reference. Denoising a 20.8s sample with afftdn
    before upload cost 19% of its consonant energy, and the clone sounded
    muffled in a way no EQ recovered; re-cloning from the untouched audio on
    identical settings doubled consonant energy. The cleanup chain in
    docs/05-audio-and-sfx.md is for a take that SHIPS. A clone reference is
    training data, and every artefact you remove is detail the model then
    cannot reproduce.
    """
    url = f"{API}/voices/add"
    if a.dry_run:
        print(f"POST {url}")
        print("  xi-api-key: <from ELEVENLABS_CLONE_API_KEY or ELEVENLABS_API_KEY>")
        print("  Content-Type: multipart/form-data; boundary=----EL<hex>")
        print(json.dumps({
            "name": a.name,
            "description": a.description,
            "files": [a.sample],
        }, indent=2))
        return

    if not a.i_did_not_denoise:
        # A guard, not a nag. This exact mistake cost a full re-clone cycle.
        print("refusing: pass --i-did-not-denoise to confirm the sample is the "
              "untouched recording (no afftdn, no highpass, no loudnorm).")
        raise SystemExit(2)

    cons = _audio.consonant_share(a.sample)
    print(f"reference 2-5kHz consonant share: {cons:.2f}%  "
          f"({_audio.duration(a.sample):.1f}s)")
    print("  record this. If a later re-clone measures materially higher, the "
          "sample you used here was pre-processed.")

    b = "----EL" + uuid.uuid4().hex

    def part(n, v):
        return (f'--{b}\r\nContent-Disposition: form-data; name="{n}"'
                f'\r\n\r\n{v}\r\n').encode()

    body = part("name", a.name) + part("description", a.description)
    fn = os.path.basename(a.sample)
    body += (f'--{b}\r\nContent-Disposition: form-data; name="files"; '
             f'filename="{fn}"\r\nContent-Type: audio/mpeg\r\n\r\n').encode()
    with open(a.sample, "rb") as f:
        body += f.read()
    body += f"\r\n--{b}--\r\n".encode()

    req = urllib.request.Request(url, data=body, headers={
        "xi-api-key": key(clone=True),
        "Content-Type": f"multipart/form-data; boundary={b}"})
    d = json.load(urllib.request.urlopen(req, timeout=300))
    rec = {"voice_id": d["voice_id"], "name": a.name,
           "sample": a.sample, "sample_consonant_pct": round(cons, 2)}
    print("cloned voice_id:", d["voice_id"])
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=2)
    print("wrote", a.out)


# ---------------------------------------------------------------- takes -----

def tts(voice_id, text, model, stability, style, out, api_key,
        similarity=0.85, speaker_boost=True, dry_run=False):
    url = f"{API}/text-to-speech/{voice_id}"
    body = {"text": text, "model_id": model, "voice_settings": {
        "stability": stability, "similarity_boost": similarity,
        "style": style, "use_speaker_boost": speaker_boost}}
    if dry_run:
        show_request(url, body)
        print(f"  -> would write {out}\n")
        return False
    try:
        data = post_json(url, body, api_key)
    except urllib.error.HTTPError as e:
        if model == DEFAULT_MODEL and e.code in (400, 422):
            # v3 access is gated on some accounts. Fall back rather than lose
            # the run, but SAY SO: the fallback model speaks audio tags aloud,
            # so a tagged text under it is garbage even though the call is 200.
            print(f"  {out}: {model} failed ({e.code}), falling back to "
                  f"{FALLBACK_MODEL}. Tags in this text WILL be spoken aloud.")
            body["model_id"] = FALLBACK_MODEL
            data = post_json(url, body, api_key)
        else:
            raise
    with open(out, "wb") as f:
        f.write(data)
    return True


def score_candidate(path, target_plain, target_rate, source_consonant,
                    asr_model, skip_asr=False):
    """Transcript first, everything else after. See _audio.whisper_text."""
    word_count = len(target_plain.split())
    dur, pz, rate = _audio.speech_rate(path, word_count)
    cons = _audio.consonant_share(path)
    heard = "" if skip_asr else _audio.whisper_text(path, asr_model)
    ok = (skip_asr or
          _audio.normalise_words(heard) == _audio.normalise_words(target_plain))
    over = [p for p in pz if p > 0.60]      # a pause past 0.60s reads as a stall
    penalty = 0.0
    penalty += abs(rate - target_rate) if target_rate else 0.0
    penalty += 0.5 * len(over)
    if source_consonant:
        penalty += abs(cons - source_consonant) * 0.25
    return dict(path=path, dur=round(dur, 2), pauses=pz, rate=round(rate, 2),
                consonant_pct=round(cons, 2), transcript_ok=bool(ok),
                heard=heard, over_long=over, penalty=round(penalty, 3))


def run_candidates(cands, a, api_key):
    """cands: list of dicts with name/model/text/stability/style."""
    results = []
    for c in cands:
        out = os.path.join(a.outdir, f"cand-{c['name']}.mp3")
        text = c["text"]
        plain = _audio.plain_text(c.get("target") or text)
        sent = tts(c.get("voice_id") or a.voice_id, text,
                   c.get("model", DEFAULT_MODEL), c.get("stability", 0.35),
                   c.get("style", 0.20), out, api_key,
                   similarity=c.get("similarity_boost", 0.85),
                   dry_run=a.dry_run)
        if not sent:
            continue
        r = score_candidate(out, plain, a.target_rate, a.source_consonant,
                            a.asr_model, a.no_asr)
        r["name"] = c["name"]
        results.append(r)
        flag = "OK" if r["transcript_ok"] else "MANGLED"
        print(f"{c['name']:22} {r['dur']:5.2f}s  rate {r['rate']:.2f} w/s  "
              f"cons {r['consonant_pct']:5.2f}%  pauses {r['pauses']}  "
              f"text {flag}")
        if not r["transcript_ok"]:
            print(f"{'':22} heard: {r['heard'][:100]}")
    if not results:
        return results
    usable = [r for r in results if r["transcript_ok"]]
    if not usable:
        print("\nNO CANDIDATE SURVIVED TRANSCRIPT VERIFICATION. Do not score "
              "these on timbre; fix the text or the model first.")
    else:
        usable.sort(key=lambda r: r["penalty"])
        b = usable[0]
        print(f"\nBEST {b['name']}  {b['path']}  rate {b['rate']:.2f}  "
              f"cons {b['consonant_pct']:.2f}%  penalty {b['penalty']}")
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(results, f, indent=2)
        print("wrote", a.json_out)
    return results


def cmd_takes(a):
    """Generate the candidates named in a JSON config, verify, score.

    Config shape (see takes.example.json):
      {"voice_id": "...", "target_rate": 3.62, "source_consonant": 4.80,
       "candidates": [{"name": "v3-tagged-035", "model": "eleven_v3",
                       "text": "[casual] ... <break time=\\"0.45s\\" /> ...",
                       "stability": 0.35, "style": 0.20}]}
    Anything on the command line overrides the file.
    """
    cfg = {}
    if a.config:
        with open(a.config) as f:
            cfg = json.load(f)
    a.voice_id = a.voice_id or cfg.get("voice_id")
    a.target_rate = a.target_rate if a.target_rate is not None else cfg.get("target_rate")
    a.source_consonant = (a.source_consonant if a.source_consonant is not None
                          else cfg.get("source_consonant"))
    cands = cfg.get("candidates", [])
    if not cands:
        raise SystemExit("no candidates in config")
    if not a.voice_id:
        raise SystemExit("no voice_id (config or --voice-id)")
    if not a.dry_run:
        os.makedirs(a.outdir, exist_ok=True)
    run_candidates(cands, a, None if a.dry_run else key())


def cmd_sweep(a):
    """Cross model x stability on one line, on one or more voices.

    The sweep that mattered was raw clone against denoised clone: same text,
    same settings, and the raw clone won on consonant retention by 2x. Run it
    once per creator, then stop sweeping and start writing text.
    """
    text = a.text
    if a.text_file:
        with open(a.text_file) as f:
            text = f.read().strip()
    if not text:
        raise SystemExit("give --text or --text-file")
    voices = [v for v in (a.voice_id or "").split(",") if v]
    if not voices:
        raise SystemExit("--voice-id takes one id or a comma separated list")
    cands = []
    for vi, vid in enumerate(voices):
        for model in a.models.split(","):
            for stab in [float(s) for s in a.stabilities.split(",")]:
                cands.append(dict(
                    name=f"v{vi}-{model.split('_')[-1]}-{stab}", voice_id=vid,
                    model=model, text=text, stability=stab, style=a.style))
    if not a.dry_run:
        os.makedirs(a.outdir, exist_ok=True)
    a.voice_id = voices[0]
    run_candidates(cands, a, None if a.dry_run else key())


# ---------------------------------------------------------------- eqfit -----

def chain_from_gains(gains, bands=_audio.BANDS, highpass=80):
    """gains: list of dB per band, same order as bands. 0 means no filter."""
    parts = [f"highpass=f={highpass}"]
    for (lo, hi), g in zip(bands, gains):
        if abs(g) < 0.05:
            continue
        centre = int(round((lo * hi) ** 0.5))     # geometric mean, not the mean
        width = 1.2
        parts.append(f"equalizer=f={centre}:t=q:w={width}:g={g:.2f}")
    parts.append("loudnorm=I=-16:TP=-1.5:LRA=9")
    parts.append("alimiter=limit=0.97")
    return ",".join(parts)


def apply_chain(src, dst, chain):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src,
                    "-af", chain, "-ar", "44100", "-ac", "1",
                    "-c:a", "libmp3lame", "-q:a", "0", dst], check=True)


def cmd_eqfit(a):
    """Fit an EQ chain by iteration against the source's own band profile.

    Measure, compare, adjust, repeat. DO NOT choose frequencies by ear. Seven
    rounds on the client voice clone took total band deviation from 44.9 to 7.2, and
    the decisive move was -7.7 dB at 900 Hz, a frequency nobody would have
    picked by listening.

    Cuts only, by default. Adding body to match a percentage backfires: a
    +2 dB shelf at 190 Hz, added to lift the 400 to 700 Hz share toward the source's,
    spilled upward into 250 to 400 Hz and CAUSED the mud it was meant to fix.
    Cut the excess; do not boost the deficit.

    Know what the fit costs before you run it: reshaping the envelope this way
    dropped the lip-sync correlation metric from 0.310 to 0.243. If the clip is
    going through an avatar model, both numbers belong in front of you.
    """
    if a.dry_run:
        # Plan only. Everything eqfit does is local ffmpeg work, so the useful
        # dry run is the shape of the fit, not a request body.
        print(f"measure band shares of {a.source} (the real voice) and "
              f"{a.generated} (the candidate), both at 32 kHz mono")
        print("bands: " + ", ".join(f"{lo}-{hi}" for lo, hi in _audio.BANDS))
        print(f"up to {a.rounds} rounds, correcting any band more than "
              f"{a.tolerance} points of share above the source, damping "
              f"{a.damping}, cuts clamped to -{a.max_cut} dB, "
              f"boosts {'allowed to +%.1f dB' % a.max_boost if a.allow_boost else 'DISABLED'}, "
              f"stopping at total deviation {a.stop_at}")
        print("each round runs: ffmpeg -i <generated> -af '<chain>' "
              "-ar 44100 -ac 1 -c:a libmp3lame -q:a 0 <round file>")
        print("chain template: " + chain_from_gains([-1.0] * len(_audio.BANDS),
                                                    highpass=a.highpass))
        print(f"best chain is written to {a.out}")
        return

    src = _audio.band_shares(a.source)
    print("band            source   gen   dev")
    gains = [0.0] * len(_audio.BANDS)
    best = None
    work = a.generated
    scratch = tempfile.mkdtemp(prefix="eqfit-")
    for rnd in range(a.rounds):
        gen = _audio.band_shares(work)
        dev = sum(abs(g - s) for g, s in zip(gen, src))
        if best is None or dev < best[0]:
            best = (dev, list(gains), work)
        print(f"--- round {rnd}  total deviation {dev:.1f}")
        for (lo, hi), s, g in zip(_audio.BANDS, src, gen):
            print(f"{lo:5d}-{hi:<5d}  {s:6.2f} {g:6.2f} {g - s:+6.2f}")
        if dev <= a.stop_at:
            print(f"deviation {dev:.1f} is at or under --stop-at {a.stop_at}")
            break
        moved = False
        for i, (s, g) in enumerate(zip(src, gen)):
            excess = g - s
            if excess > a.tolerance:
                # Convert a share excess into dB and take a fraction of it, so
                # the fit converges instead of ringing between over and under.
                step = -a.damping * 10.0 * np.log10(max(g, 1e-6) / max(s, 1e-6))
                gains[i] = float(np.clip(gains[i] + step, -a.max_cut, 0.0))
                moved = True
            elif a.allow_boost and excess < -a.tolerance:
                step = a.damping * 10.0 * np.log10(max(s, 1e-6) / max(g, 1e-6))
                gains[i] = float(np.clip(gains[i] + step, 0.0, a.max_boost))
                moved = True
        if not moved:
            print("no band exceeds the tolerance, stopping")
            break
        chain = chain_from_gains(gains, highpass=a.highpass)
        work = os.path.join(scratch, f"r{rnd}.mp3")
        apply_chain(a.generated, work, chain)

    shutil.rmtree(scratch, ignore_errors=True)
    chain = chain_from_gains(best[1] if best else gains, highpass=a.highpass)
    if best:
        print(f"\nbest total deviation {best[0]:.1f}")
    print(chain)
    with open(a.out, "w") as f:
        f.write(chain)
    print("wrote", a.out)


# --------------------------------------------------------------- master -----

def cmd_master(a):
    """Apply the fitted chain, then nudge toward the creator's measured rate.

    atempo only ever SPEEDS UP, clipped at 0.88. Slowing a TTS read down to hit
    a rate target makes it sound drugged, and the reason a take is slow is
    almost always that v3 dramatised a short sentence, which is a text fix, not
    a tempo fix.
    """
    with open(a.eq) as f:
        chain = f.read().strip()
    tmp = a.out + ".eq.mp3"
    if a.dry_run:
        print(f"ffmpeg -i {a.inp} -af '{chain}' {tmp}")
        print(f"then atempo toward --target-rate {a.target_rate} (cap 1/0.88)")
        return
    apply_chain(a.inp, tmp, chain)
    words = a.words
    if a.text_file:
        with open(a.text_file) as f:
            words = len(_audio.plain_text(f.read()).split())
    if not words or not a.target_rate:
        os.replace(tmp, a.out)
        print(f"{a.out}: EQ applied, no rate nudge (need --words and --target-rate)")
        return
    dur, pz, rate = _audio.speech_rate(tmp, words)
    ratio = float(np.clip(rate / a.target_rate, 0.88, 1.0))
    tempo = 1 / ratio if ratio < 1 else 1.0
    if tempo > 1.005:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af",
                        f"atempo={tempo:.4f}", "-ar", "44100", "-ac", "1",
                        "-c:a", "libmp3lame", "-q:a", "0", a.out], check=True)
        os.remove(tmp)
    else:
        os.replace(tmp, a.out)
    d2, pz2, r2 = _audio.speech_rate(a.out, words)
    print(f"{a.out}  {d2:5.2f}s  rate {r2:.2f} w/s (atempo {tempo:.3f})  "
          f"pauses {pz2}")


# ----------------------------------------------------------------- main -----

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("clone", help="instant voice clone from an untouched sample")
    c.add_argument("--sample", required=True, help="the RAW reference recording")
    c.add_argument("--name", required=True)
    c.add_argument("--description", default="")
    c.add_argument("-o", "--out", default="voice.json")
    c.add_argument("--i-did-not-denoise", action="store_true",
                   help="confirm the sample was not cleaned up first")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(fn=cmd_clone)

    for name, fn in (("takes", cmd_takes), ("sweep", cmd_sweep)):
        t = sub.add_parser(name, help=f"{name}: generate, verify, score")
        t.add_argument("--voice-id")
        t.add_argument("--outdir", default="audio")
        t.add_argument("--target-rate", type=float, default=None,
                       help="the creator's measured words/sec of speech, eg 3.62")
        t.add_argument("--source-consonant", type=float, default=None,
                       help="the real voice's 2-5kHz share, eg 4.80")
        t.add_argument("--asr-model", default="small")
        t.add_argument("--no-asr", action="store_true",
                       help="skip transcript verification. You are choosing to "
                            "score audio that may be speaking its own tags.")
        t.add_argument("--json-out")
        t.add_argument("--dry-run", action="store_true")
        if name == "takes":
            t.add_argument("--config", required=True)
        else:
            t.add_argument("--text")
            t.add_argument("--text-file")
            t.add_argument("--models",
                           default=f"{DEFAULT_MODEL},{FALLBACK_MODEL}")
            t.add_argument("--stabilities", default="0.35,0.60")
            t.add_argument("--style", type=float, default=0.20)
        t.set_defaults(fn=fn)

    e = sub.add_parser("eqfit", help="fit an EQ chain against the real voice")
    e.add_argument("--source", required=True, help="the REAL voice recording")
    e.add_argument("--generated", required=True, help="the TTS candidate")
    e.add_argument("-o", "--out", default="eq-chain.txt")
    e.add_argument("--rounds", type=int, default=8)
    e.add_argument("--tolerance", type=float, default=0.8,
                   help="percentage points of share before a band is corrected")
    e.add_argument("--damping", type=float, default=0.6)
    e.add_argument("--max-cut", type=float, default=9.0)
    e.add_argument("--max-boost", type=float, default=3.0)
    e.add_argument("--allow-boost", action="store_true",
                   help="boost deficits too. Read cmd_eqfit's docstring first.")
    e.add_argument("--stop-at", type=float, default=8.0)
    e.add_argument("--highpass", type=int, default=80)
    e.add_argument("--dry-run", action="store_true")
    e.set_defaults(fn=cmd_eqfit)

    m = sub.add_parser("master", help="apply the chain and nudge the rate")
    m.add_argument("--in", dest="inp", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--eq", required=True)
    m.add_argument("--words", type=int, default=0)
    m.add_argument("--text-file", help="count words from the tagged text instead")
    m.add_argument("--target-rate", type=float, default=0.0)
    m.add_argument("--dry-run", action="store_true")
    m.set_defaults(fn=cmd_master)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
