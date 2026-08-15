#!/usr/bin/env python3
"""Render the whole film's SFX bed to one WAV, straight from sfx.py's cue list.

WHY THIS EXISTS. assemble.sh used to reconstruct the bed by pulling the audio track
out of each chunk render. That coupled the bed to the picture: changing one volume
meant re-rendering 4K video to hear it, ~6 minutes a chunk. When the owner supplied
a new SFX pack mid-round, that coupling would have cost a full 45-minute re-render
for a change that touches no pixel.

The bed is now built here instead, from the same CUES dict sfx.py injects into the
chunks, so the two cannot disagree, and SFX iteration costs seconds.

Cue times in sfx.py are LOCAL to a chunk; absolute time is chunks.json's t0 plus the
local time, which is exactly the mapping the injected <audio data-start> uses.

usage: python3 build_bed.py [out.wav]
"""
import json, os, subprocess, sys, array, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sfx  # noqa: E402

SR = 48000
FADE = int(0.008 * SR)          # 8ms out-ramp so a clipped tail cannot click


def decode(path):
    """Decode one file to mono float samples at SR."""
    raw = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", path,
         "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True, check=True).stdout
    a = array.array("h")
    a.frombytes(raw)
    return [s / 32768.0 for s in a]


def main():
    chunks = json.load(open(os.path.join(HERE, "recut", "chunks.json")))
    total = chunks["total_frames"]
    fps = chunks["fps"]
    t0 = {c["name"]: c["t0"] for c in chunks["chunks"]}
    n_out = int(round(total / fps * SR))
    buf = [0.0] * n_out

    cache, placed, clipped = {}, 0, 0
    for name in sorted(sfx.CUES):
        if name not in t0:
            print(f"  !! {name} has cues but is not in chunks.json"); sys.exit(1)
        for t, f, v, d in sfx.CUES[name]:
            path = os.path.join(HERE, "assets", "sfx", f + ".mp3")
            if f not in cache:
                if not os.path.exists(path):
                    print(f"  !! missing assets/sfx/{f}.mp3"); sys.exit(1)
                cache[f] = decode(path)
            src = cache[f]
            start = int(round((t0[name] + t) * SR))
            length = min(int(round(d * SR)), len(src))
            if start < 0:
                continue
            end = min(start + length, n_out)
            if end <= start:
                continue
            length = end - start
            for i in range(length):
                g = v
                # ramp the last 8ms only when the cue is cutting the file short
                if length < len(src) and i > length - FADE:
                    g *= (length - i) / FADE
                buf[start + i] += src[i] * g
            placed += 1

    peak = max(abs(s) for s in buf) or 1.0
    if peak > 1.0:
        clipped = 1
        buf = [s / peak for s in buf]

    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, ".assembly", "sfx.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pcm = array.array("h", (int(max(-1.0, min(1.0, s)) * 32767) for s in buf))
    # write as stereo so the mix stage sees the same layout it always did
    st = array.array("h")
    for s in pcm:
        st.append(s); st.append(s)
    body = st.tobytes()
    with open(out, "wb") as fh:
        fh.write(b"RIFF" + (36 + len(body)).to_bytes(4, "little") + b"WAVEfmt ")
        fh.write((16).to_bytes(4, "little") + (1).to_bytes(2, "little"))
        fh.write((2).to_bytes(2, "little") + SR.to_bytes(4, "little"))
        fh.write((SR * 4).to_bytes(4, "little") + (4).to_bytes(2, "little"))
        fh.write((16).to_bytes(2, "little") + b"data")
        fh.write(len(body).to_bytes(4, "little") + body)

    rms = math.sqrt(sum(s * s for s in buf) / len(buf)) if buf else 0
    print(f"  bed: {placed} cues, {len(cache)} distinct files, {n_out/SR:.3f}s")
    print(f"       peak {20*math.log10(peak):.1f} dBFS"
          f"{'  (normalised down - cues were summing over 0 dBFS)' if clipped else ''}"
          f", rms {20*math.log10(rms) if rms else -99:.1f} dBFS")
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
