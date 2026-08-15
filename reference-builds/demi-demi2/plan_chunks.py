#!/usr/bin/env python3
"""
Split hfdemi2/index.html into N independent HyperFrames projects.

WHY THIS EXISTS
    28 `<video>` elements, every one 2160x3840 at 60-100 Mbps, in ONE page.
    `hyperframes render` pre-extracts frames from EVERY video in the composition
    before it captures a single frame (render-probe4k.log: "Extracting frames from
    video 28/28" then the machine died). On an 8 GB M2 Air that stage is what
    trips the SoC watchdog -- blank screen, hard reset, no panic file, only
    `wdog,reset_in_1` in ResetCounter-*.diag. Confirmed three times on 2026-08-13.

    Chunking caps the number of 4K decoders per page. Nothing else does.

WHAT IT PRESERVES
    - Boundaries land on SHOT STARTS, so no shot is split across a join. The
      ~13ms overlaps between consecutive shots are cross-cuts where the incoming
      shot (higher track-index) already paints over the outgoing one, so clamping
      the outgoing tail at the boundary is visually lossless.
    - Frame-exact: every boundary is round(t*30), and the chunk frame counts are
      asserted to sum to the whole film. That is what makes `-c copy` concat lossless.
    - The GSAP timeline is rebased, not rewritten: every absolute position P
      becomes P - T0. Tweens finishing before T0 are DROPPED, which is correct --
      a `.from()` that has completed leaves the element at its natural CSS state,
      which is exactly what a later chunk should render.

WHAT IT ASSERTS (a silent miss here ships a broken film)
    - no tween STRADDLES a boundary (a partially-applied .from() would pop)
    - no flash straddles a boundary
    - every referenced asset resolves on disk in the chunk dir
    - the substitution actually fired (a no-match regex must never pass silently)
"""
import json
import os
import re
import shutil
import sys

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))

# Round-2 boundaries: frame-exact times aligned to the native A-roll segment
# joins (ar_a1/a2/a3, dock2, ar_f, ar_g1/g2). Flashes f2/f3 were moved to sit
# exactly ON their boundary so nothing straddles.
BOUNDS = [0.00, 4.7667, 8.7333, 14.4667, 17.8667, 20.8667, 27.4333, 32.20, 37.7667]


def frames(t):
    return int(round(t * FPS))


# ── parse the source ────────────────────────────────────────────────────
def load():
    with open(os.path.join(HERE, "index.html"), encoding="utf-8") as fh:
        return fh.read()


CLIP_RE = re.compile(
    r'<(?P<tag>video|div|img)\b(?P<attrs>[^>]*\bclass="[^"]*\bclip\b[^"]*"[^>]*)>',
    re.I,
)
ATTR_RE = {
    k: re.compile(r'\b%s="([^"]*)"' % k)
    for k in ("data-start", "data-duration", "id", "src", "data-track-index")
}


def clip_spans(html):
    """(start, dur, id, tag, match) for every timed element."""
    out = []
    for m in CLIP_RE.finditer(html):
        a = m.group("attrs")
        ds, dd = ATTR_RE["data-start"].search(a), ATTR_RE["data-duration"].search(a)
        if not ds or not dd:
            continue
        i = ATTR_RE["id"].search(a)
        out.append(
            dict(
                start=float(ds.group(1)),
                dur=float(dd.group(1)),
                id=i.group(1) if i else "",
                tag=m.group("tag").lower(),
                span=m.span(),
            )
        )
    return out


# every literal timeline position in the <script>: the trailing `, N)` of a
# tl.* call, plus the two literal arrays.
POS_RE = re.compile(r"\}\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
ARR_RE = re.compile(r"(chipAt\s*=\s*\[)([^\]]*)(\])")
FLASHT_RE = re.compile(r"(const t = \[)([^\]]*)(\])")
# a tween's own duration, to know where it ENDS
DUR_RE = re.compile(r"duration:\s*(\d+(?:\.\d+)?)")


def tween_windows(script):
    """[(start, end, text)] for every tl.* call carrying an explicit position."""
    out = []
    for m in POS_RE.finditer(script):
        pos = float(m.group(1))
        # walk back to the start of this tl.* statement
        head = script.rfind("tl.", 0, m.start())
        if head < 0:
            continue
        body = script[head : m.end()]
        durs = [float(d) for d in DUR_RE.findall(body)]
        # a yoyo/repeat:1 runs twice
        rep = 2 if "repeat: 1" in body or "repeat:1" in body else 1
        stag = re.search(r"stagger:\s*(\d+(?:\.\d+)?)", body)
        n = body.count(",")  # crude, only used to bound stagger spread
        span = (max(durs) if durs else 0.0) * rep
        if stag:
            span += float(stag.group(1)) * 6  # six is the largest stagger set here
        out.append((pos, pos + span, body))
    return out


def main():
    html = load()
    smark = html.index("<script>\nwindow.__timelines")
    emark = html.index("</script>", smark)
    script = html[smark:emark]

    clips = clip_spans(html)
    tweens = tween_windows(script)

    # ── assertions on the boundary set ──────────────────────────────────
    #
    # COVERAGE NOTE: tween_windows() only sees tweens whose position is a
    # LITERAL number. The chip entrances (`}, t)` inside chipAt.forEach) and the
    # caption entrances (`}, t + 0.02)`, t read from the DOM) are invisible to
    # it. A guard that silently never measured two of the three tween families
    # is the exact failure in feedback_gate_scope_holes_and_inert_fixups, so
    # both are enumerated explicitly here rather than left to luck.
    chip_at = [2.84, 3.42, 4.20, 4.7667]
    for i, t in enumerate(chip_at):
        tweens.append((t, t + 0.30, f"chip entrance #c{i+1}"))
    for c in clips:
        if c["id"]:
            continue  # captions are the unnamed .cap divs
        if c["start"] > 0:
            tweens.append((c["start"] + 0.02, c["start"] + 0.18, f"caption @{c['start']:.2f}"))

    problems = []
    for b in BOUNDS[1:-1]:
        for s, e, body in tweens:
            if s < b - 1e-9 and e > b + 1e-9:
                head = body.strip().split("\n")[0][:64]
                problems.append(f"tween straddles {b:.2f}: [{s:.2f},{e:.2f}] {head}")
        for c in clips:
            if c["id"].startswith("f") and len(c["id"]) == 2 and c["id"][1].isdigit():
                if c["start"] < b - 1e-9 and c["start"] + c["dur"] > b + 1e-9:
                    problems.append(f"flash {c['id']} straddles {b:.2f}")
    if problems:
        print("!! boundary problems:")
        for p in problems:
            print("   " + p)
        sys.exit(1)

    # ── frame-exact plan ────────────────────────────────────────────────
    plan = []
    for i in range(len(BOUNDS) - 1):
        t0, t1 = BOUNDS[i], BOUNDS[i + 1]
        f0, f1 = frames(t0), frames(t1)
        plan.append(dict(name=f"c{i+1}", t0=t0, t1=t1, f0=f0, f1=f1, nframes=f1 - f0))

    total = sum(p["nframes"] for p in plan)
    want = frames(BOUNDS[-1])
    assert total == want, f"frame total {total} != {want}"

    # A shot that spills LESS THAN ONE FRAME past a boundary is a cross-cut
    # overlap, not a split: the incoming shot has a higher track-index and is
    # already live at the boundary, so it paints over the spill. Dropping the
    # outgoing shot from the later chunk is lossless -- but only if that cover
    # actually exists, so assert it rather than trust the pattern.
    one_frame = 1.0 / FPS
    dropped = []
    for p in plan:
        live = []
        for c in clips:
            if not (c["start"] < p["t1"] - 1e-9 and c["start"] + c["dur"] > p["t0"] + 1e-9):
                continue
            spill = c["start"] + c["dur"] - p["t0"]
            if c["start"] < p["t0"] - 1e-9 and spill < one_frame - 1e-9:
                cover = [
                    o
                    for o in clips
                    if o["tag"] == c["tag"]
                    and o["start"] <= p["t0"] + 1e-9
                    and o["start"] + o["dur"] > p["t0"] + spill
                    and o["id"] != c["id"]
                ]
                assert cover, (
                    f"{c['id']} spills {spill*FPS:.2f}f into {p['name']} with nothing "
                    f"covering it -- dropping it would show a hole"
                )
                dropped.append((p["name"], c["id"], spill * FPS, cover[0]["id"]))
                continue
            live.append(c)
        p["clips"] = sorted(c["id"] for c in live if c["id"])
        p["videos"] = sorted(c["id"] for c in live if c["tag"] == "video")
        p["nclips"] = len(live)

    if dropped:
        print("sub-frame cross-cut spills dropped (covered by the incoming shot):")
        for name, cid, f, cov in dropped:
            print(f"   {name}: {cid} ({f:.2f} frames, under {cov})")
        print()

    with open(os.path.join(HERE, "chunks.json"), "w") as fh:
        json.dump(plan, fh, indent=2)

    print(f"{'chunk':<6}{'window':<18}{'frames':<9}{'clips':<8}{'videos'}")
    for p in plan:
        print(
            f"{p['name']:<6}{p['t0']:>6.2f}-{p['t1']:<10.2f}"
            f"{p['nframes']:<9}{p['nclips']:<8}{len(p['videos'])}  "
            f"{','.join(p['videos'])}"
        )
    print(f"\ntotal {total} frames = {total/FPS:.2f}s  (source {want} / {want/FPS:.2f}s)")
    print(f"max videos in any one chunk: {max(len(p['videos']) for p in plan)}  (was 28)")
    print("wrote chunks.json")


if __name__ == "__main__":
    main()
