#!/usr/bin/env python3
"""music.py, licensed music: find it, fetch it, audition it, fit it to the cut.

    python3 tools/generative/music.py search --tag technology
    python3 tools/generative/music.py fetch  https://assets.mixkit.co/music/<id>/<id>.mp3 -o bed-src.mp3
    python3 tools/generative/music.py transients bed-src.mp3
    python3 tools/generative/music.py treat bed-src.mp3 bed.mp3 --src-bpm 129 --length 41.5

No API key. Mixkit needs no auth, only a browser user agent.

AI-GENERATED MUSIC GETS REJECTED. An ElevenLabs bed was generated, tempo
matched and sidechain ducked carefully to the cut's beat grid, and came back as
"too shitty music bro, eww", followed by "can't you find one pre-existing
non-copyright music". The production effort counted for nothing because the
objection was to the CATEGORY. A real royalty-free track is the default, and
there is no version of the AI bed that wins this argument.

Mixkit licence: Stock Music Free License, commercial use including paid ads, no
attribution required. Pixabay does not script: its music pages return 403 to
automated fetching even on public search URLs, its SFX downloads are login
walled (a full hover-and-click crawl returned 0 files), and its stock pages
stay JS locked to curl.

AND AUDITION FOR TICKS BEFORE CHOOSING. The track that replaced the AI bed on
one film was itself swapped later because it carried a metronomic 0.465s
percussion tick on a 129 BPM grid that three rounds of SFX purges got blamed
for. `transients` is that audition: the winner measured 30 transients against
75 for the one it replaced, and verified at 4 non-VO transients, none periodic.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _audio  # noqa: E402

UA = "Mozilla/5.0"
TAG_URL = "https://mixkit.co/free-stock-music/tag/{tag}/"
DISCOVER_URL = "https://mixkit.co/free-stock-music/discover/{slug}/"
ASSET_RE = re.compile(r"https://assets\.mixkit\.co/music/[^\"'\s>]+?\.mp3")


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def cmd_search(a):
    url = a.url or TAG_URL.format(tag=a.tag)
    if a.dry_run:
        print(f"GET {url}")
        print(f"  User-Agent: {UA}")
        print("  follow redirects, then regex the page for "
              r"https://assets\.mixkit\.co/music/.+\.mp3")
        return
    html = get(url).decode("utf-8", "replace")
    seen = []
    for m in ASSET_RE.findall(html):
        if m not in seen:
            seen.append(m)
    for u in seen[:a.limit]:
        print(u)
    print(f"\n{len(seen)} asset urls on {url}")
    if not seen:
        print("none found. Track pages 301 to "
              + DISCOVER_URL.format(slug="<slug>")
              + " ; the tag page is the one that embeds asset urls.")


def cmd_fetch(a):
    url = a.url
    if not url.startswith("http"):
        # A bare id: the direct mp3 sits at /music/<id>/<id>.mp3.
        url = f"https://assets.mixkit.co/music/{url}/{url}.mp3"
    if a.dry_run:
        print(f"GET {url}")
        print(f"  User-Agent: {UA}")
        print(f"  -> would write {a.out}")
        return
    data = get(url, timeout=300)
    with open(a.out, "wb") as f:
        f.write(data)
    print(f"SAVED {a.out}  {len(data) / 1e6:.2f} MB  {_audio.duration(a.out):.2f}s")


def onsets(path, sr=22050, hop=0.010, min_gap=0.10, k=2.0):
    """Onset times from the RMS envelope.

    Envelope, not a transcriber and not the eye. A spectral-flux count over the
    whole file is what exposes a metronomic tick that nobody can name while
    listening; three rounds of SFX purges were spent blaming the wrong thing.
    """
    x = _audio.decode_mono(path, sr)
    n = int(sr * hop)
    frames = len(x) // n
    rms = np.sqrt((x[:frames * n].reshape(frames, n) ** 2).mean(axis=1) + 1e-12)
    flux = np.diff(rms, prepend=rms[:1])
    flux[flux < 0] = 0
    thr = flux.mean() + k * flux.std()
    times, last = [], -1e9
    for i, v in enumerate(flux):
        t = i * hop
        if v > thr and t - last >= min_gap:
            times.append(round(t, 3))
            last = t
    return times, len(x) / sr


def cmd_transients(a):
    if a.dry_run:
        print(f"would decode {a.file} to mono 22050 and count RMS-flux onsets "
              f"at hop 10 ms, min gap {a.min_gap}s, threshold mean + "
              f"{a.sensitivity} sd")
        print("then quantise the inter-onset gaps to 5 ms and report the "
              "dominant interval, its share and the implied BPM")
        return
    times, dur = onsets(a.file, min_gap=a.min_gap, k=a.sensitivity)
    print(f"{a.file}  {dur:.2f}s  {len(times)} transients  "
          f"{60 * len(times) / dur:.1f} per minute")
    if len(times) < 3:
        print("too few to test for periodicity")
        return
    iv = np.diff(times)
    # Periodicity is the disqualifier, not the count. A dense but irregular
    # texture sits under a VO; one repeating click at a fixed interval reads as
    # a fault in the edit and gets reported as one.
    q = np.round(iv / 0.005) * 0.005
    vals, counts = np.unique(q, return_counts=True)
    top = int(np.argmax(counts))
    share = counts[top] / len(iv)
    print(f"dominant interval {vals[top]:.3f}s, {counts[top]} of {len(iv)} gaps "
          f"({100 * share:.0f}%), implied {60 / max(vals[top], 1e-6):.1f} BPM")
    if share >= a.periodic_share and vals[top] > 0:
        print("PERIODIC. This is the 0.465s tick class of fault. Audition "
              "another track rather than trying to notch it out.")
        sys.exit(1)
    print("not periodic at the reporting threshold")


def atempo_chain(rate):
    """ffmpeg's atempo takes 0.5 to 2.0 per instance. Chain it for anything
    outside that, or the filter graph errors out after the download."""
    parts = []
    r = rate
    while r > 2.0:
        parts.append("atempo=2.0")
        r /= 2.0
    while r < 0.5:
        parts.append("atempo=0.5")
        r /= 0.5
    parts.append(f"atempo={r:.6f}")
    return ",".join(parts)


def cmd_treat(a):
    """Tempo match, high pass, loudnorm, fades, trim.

    Stretch to the cut's own grid so every scene change lands within a quarter
    beat. The target BPM is the EDIT's, not a genre default: pass the grid the
    beats were cut on.

    loudnorm I=-20 is a BED, sitting under a VO mastered at I=-16. A bed at the
    same integrated loudness as the voice is the "music too loud" note before
    anyone plays it. A client's own supplied clip keeps its own audio at unity
    with the music fading underneath, and probe that clip before designing a
    handover to it: one client outro's track was digital silence at -240 dBFS.
    """
    rate = a.target_bpm / a.src_bpm if a.src_bpm else 1.0
    fade_out_at = max(a.length - a.fade_out, 0.0)
    chain = ",".join([
        atempo_chain(rate),
        f"highpass=f={a.highpass}",
        f"loudnorm=I={a.lufs}:TP={a.tp}:LRA={a.lra}",
        f"afade=t=in:st=0:d={a.fade_in}",
        f"afade=t=out:st={fade_out_at}:d={a.fade_out}",
        f"atrim=0:{a.length}",
        "asetpts=N/SR/TB",
    ])
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a.offset), "-i", a.src,
           "-af", chain, "-c:a", "libmp3lame", "-q:a", "2", a.out]
    if a.dry_run:
        print(" ".join(cmd))
        print(f"\ntempo {a.src_bpm} -> {a.target_bpm} BPM (rate {rate:.4f})")
        print(f"bed length {a.length}s from offset {a.offset}s, "
              f"fade in {a.fade_in}s, fade out {a.fade_out}s ending at {a.length}s")
        return
    subprocess.run(cmd, check=True)
    print(f"SAVED {a.out}  {_audio.duration(a.out):.2f}s")
    t, dur = onsets(a.out)
    print(f"post-treatment transients: {len(t)} over {dur:.2f}s")
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(dict(src=a.src, out=a.out, src_bpm=a.src_bpm,
                           target_bpm=a.target_bpm, rate=round(rate, 5),
                           filter=chain, transients=len(t)), f, indent=2)
        print("wrote", a.json_out)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="list mixkit asset urls on a tag page")
    s.add_argument("--tag", default="technology")
    s.add_argument("--url", help="any mixkit page, overrides --tag")
    s.add_argument("--limit", type=int, default=40)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_search)

    f = sub.add_parser("fetch", help="download an asset url or a bare track id")
    f.add_argument("url")
    f.add_argument("-o", "--out", required=True)
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(fn=cmd_fetch)

    t = sub.add_parser("transients", help="audition a candidate for ticks")
    t.add_argument("file")
    t.add_argument("--min-gap", type=float, default=0.10)
    t.add_argument("--sensitivity", type=float, default=2.0,
                   help="threshold in standard deviations above mean flux")
    t.add_argument("--periodic-share", type=float, default=0.40,
                   help="fraction of gaps at one interval that counts as a tick")
    t.add_argument("--dry-run", action="store_true")
    t.set_defaults(fn=cmd_transients)

    r = sub.add_parser("treat", help="tempo match and master a bed for one cut")
    r.add_argument("src")
    r.add_argument("out")
    r.add_argument("--src-bpm", type=float, required=True,
                   help="the track's own BPM, off its mixkit page or measured")
    r.add_argument("--target-bpm", type=float, default=120.0,
                   help="the EDIT's grid, not a genre default")
    r.add_argument("--offset", type=float, default=0.0,
                   help="seconds into the track to start, to skip an intro")
    r.add_argument("--length", type=float, required=True,
                   help="the cut's duration, post tempo change")
    r.add_argument("--fade-in", type=float, default=1.0)
    r.add_argument("--fade-out", type=float, default=1.5)
    r.add_argument("--highpass", type=int, default=45)
    r.add_argument("--lufs", type=float, default=-20.0)
    r.add_argument("--tp", type=float, default=-2.0)
    r.add_argument("--lra", type=float, default=6.0)
    r.add_argument("--json-out")
    r.add_argument("--dry-run", action="store_true")
    r.set_defaults(fn=cmd_treat)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
