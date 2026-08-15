#!/usr/bin/env python3
"""
Emit c1..c8 as independent HyperFrames projects from index.html + chunks.json.

THE THREE THINGS THAT MAKE THIS SAFE

1. Positions are rebased STATICALLY, and out-of-window tweens are DROPPED at
   generation time -- never passed to GSAP as negatives. A tween placed at a
   negative position does not clamp, it SHIFTS THE WHOLE TIMELINE
   (feedback_beats_must_live_in_their_own_chunk). Dropping is also semantically
   right: plan_chunks.py has already asserted no tween straddles a boundary, so
   a tween before T0 has FINISHED, and a finished `.from()` leaves the element
   at its natural CSS state -- which is what the chunk should paint.

2. The caption loop needs no rewriting at all. It reads `data-start` off the DOM,
   which this script has already rebased, and its existing `if (t <= 0) return;`
   guard -- written so the caption live on the cover frame is pre-painted --
   does exactly the right thing for a caption live at a chunk's frame 0.

3. Every referenced asset is resolved on disk after the chunk is written. A
   broken <img>/<video> src is invisible to lint and renders as a hole
   (feedback_a_missing_asset_dir_passes_every_gate).
"""
import json
import os
import re
import shutil
import sys

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))
EPS = 1e-9


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


# ── locate the timed elements ───────────────────────────────────────────
TAG_RE = re.compile(
    r'<(?P<tag>video|div|img)\b(?P<attrs>[^>]*?\bclass="[^"]*\bclip\b[^"]*"[^>]*?)>',
    re.I | re.S,
)


def attr(a, k):
    m = re.search(r'\b%s="([^"]*)"' % re.escape(k), a)
    return m.group(1) if m else None


def element_blocks(html):
    """(start, end, id, open_tag_span, full_element_span) for each timed clip."""
    out = []
    for m in TAG_RE.finditer(html):
        a = m.group("attrs")
        ds, dd = attr(a, "data-start"), attr(a, "data-duration")
        if ds is None or dd is None:
            continue
        tag = m.group("tag").lower()
        # find the matching close tag (these are never nested same-tag)
        if tag == "img":
            end = m.end()
        else:
            close = f"</{tag}>"
            depth, i = 1, m.end()
            while depth:
                nxt_o = html.find(f"<{tag}", i)
                nxt_c = html.find(close, i)
                if nxt_c < 0:
                    raise SystemExit(f"unclosed <{tag}> for {attr(a,'id')}")
                if 0 <= nxt_o < nxt_c:
                    depth += 1
                    i = nxt_o + 1
                else:
                    depth -= 1
                    i = nxt_c + len(close)
            end = i
        out.append(
            dict(
                id=attr(a, "id") or "",
                tag=tag,
                start=float(ds),
                dur=float(dd),
                open=m.span(),
                full=(m.start(), end),
            )
        )
    return out


# ── the script: statement-level split ───────────────────────────────────
def split_statements(script):
    """Every top-level `tl.*(...);` statement with its literal position."""
    stmts = []
    i = 0
    while True:
        h = script.find("tl.", i)
        if h < 0:
            break
        # walk to the balanced close of this call, then to the ';'
        depth, j, instr, q = 0, h, False, ""
        while j < len(script):
            ch = script[j]
            if instr:
                if ch == "\\":
                    j += 2
                    continue
                if ch == q:
                    instr = False
            elif ch in "\"'":
                instr, q = True, ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        end = script.find(";", j)
        body = script[h : end + 1]
        m = re.search(r",\s*(-?\d+(?:\.\d+)?)\s*\)\s*;\s*$", body)
        stmts.append(dict(text=body, pos=float(m.group(1)) if m else None, span=(h, end + 1)))
        i = end + 1
    return stmts


DUR_RE = re.compile(r"duration:\s*(\d+(?:\.\d+)?)")


def stmt_end(s):
    if s["pos"] is None:
        return None
    durs = [float(d) for d in DUR_RE.findall(s["text"])]
    rep = 2 if re.search(r"repeat:\s*1", s["text"]) else 1
    span = (max(durs) if durs else 0.0) * rep
    st = re.search(r"stagger:\s*(\d+(?:\.\d+)?)", s["text"])
    if st:
        span += float(st.group(1)) * 6
    return s["pos"] + span


def rebase_stmt(s, t0):
    """Return the statement with its position rebased, or None to drop it."""
    if s["pos"] is None:
        return s["text"]
    new = round(s["pos"] - t0, 4)
    if new < -EPS:
        return None  # finished before this chunk started
    return re.sub(
        r"(,\s*)(-?\d+(?:\.\d+)?)(\s*\)\s*;\s*)$",
        lambda m: f"{m.group(1)}{new:g}{m.group(3)}",
        s["text"],
    )


def main():
    html = load("index.html")
    plan = json.loads(load("chunks.json"))

    smark = html.index("<script>\nwindow.__timelines")
    emark = html.index("</script>", smark)
    head, script, tail = html[:smark], html[smark:emark], html[emark:]

    els = element_blocks(html)
    by_id = {e["id"]: e for e in els if e["id"]}
    stmts = split_statements(script)

    # the two literal-array loops need their arrays filtered in lockstep
    chip_times = [2.84, 3.42, 4.20, 4.7667]
    flash_ids = ["#f1", "#f2", "#f3", "#f4"]
    flash_times = [8.7333, 14.4667, 20.8667, 33.78]

    made = []
    for p in plan:
        c, t0, t1 = p["name"], p["t0"], p["t1"]
        # HyperFrames CEILS duration*fps to get the frame count, so a duration
        # that rounds even a hair HIGH yields one extra frame -- c1 at 4.7667
        # rendered 144 frames against a planned 143, which would desync the
        # concat exactly as vid44's +4.1s did. Bias a thousandth of a frame LOW
        # so the ceil always lands on the planned count. Naive rounding is not
        # safe here: 126/30 is 4.2, and 4.2*30 is 126.00000000000001 in binary
        # float, which ceils to 127.
        clen = (p["nframes"] - 0.001) / FPS
        cdir = os.path.join(HERE, c)
        os.makedirs(cdir, exist_ok=True)

        keep = set(p["clips"])
        out = head

        # drop every element not in this chunk, back to front so spans hold
        for e in sorted(els, key=lambda e: -e["full"][0]):
            if e["id"] and e["id"] in keep:
                continue
            if not e["id"]:
                # unnamed caption divs: keep by window
                if e["start"] < t1 - EPS and e["start"] + e["dur"] > t0 + EPS:
                    continue
            out = out[: e["full"][0]] + out[e["full"][1] :]

        # rebase the survivors' data-start / data-duration
        def rebase_attrs(m):
            a = m.group("attrs")
            ds, dd = attr(a, "data-start"), attr(a, "data-duration")
            if ds is None or dd is None:
                return m.group(0)
            s, d = float(ds), float(dd)
            ns = round(max(0.0, s - t0), 4)
            ne = round(min(clen, s + d - t0), 4)
            a = re.sub(r'\bdata-start="[^"]*"', f'data-start="{ns:g}"', a)
            a = re.sub(r'\bdata-duration="[^"]*"', f'data-duration="{ne-ns:g}"', a)
            return f'<{m.group("tag")}{a}>'

        out = TAG_RE.sub(rebase_attrs, out)

        # the root composition
        out = re.sub(
            r'(<div id="root"[^>]*?)data-start="[^"]*"\s*data-duration="[^"]*"',
            lambda m: f'{m.group(1)}data-start="0" data-duration="{clen:g}"',
            out,
            count=1,
        )
        assert f'data-duration="{clen:g}"' in out, f"{c}: root duration substitution missed"

        # ── the script ────────────────────────────────────────────────
        ns = script
        for s in sorted(stmts, key=lambda s: -s["span"][0]):
            if "chipAt.forEach" in s["text"] or "flash" in s["text"]:
                continue
            r = rebase_stmt(s, t0)
            a, b = s["span"]
            ns = ns[:a] + (r if r is not None else "") + ns[b:]

        live_chip = [
            (round(t - t0, 4), i)
            for i, t in enumerate(chip_times)
            if t - t0 >= -EPS and f"c{i+1}" in html
        ]
        ns = re.sub(
            r"const chipAt = \[[^\]]*\];",
            f"const chipAt = {json.dumps([t for t, _ in live_chip])};\n"
            f"const chipIx = {json.dumps([i for _, i in live_chip])};",
            ns,
            count=1,
        )
        ns = ns.replace('"#c" + (i + 1)', '"#c" + (chipIx[i] + 1)')

        lf = [
            (fid, round(t - t0, 4))
            for fid, t in zip(flash_ids, flash_times)
            if fid.lstrip("#") in keep
        ]
        ns = re.sub(
            r'\["#f1", "#f2", "#f3", "#f4"\]',
            json.dumps([f for f, _ in lf]),
            ns,
            count=1,
        )
        ns = re.sub(
            r"const t = \[[^\]]*\]\[i\];",
            f"const t = {json.dumps([t for _, t in lf])}[i];",
            ns,
            count=1,
        )

        # `out` was seeded from `head`, which ends where the <script> begins, so
        # the rebuilt script and the closing tail append directly.
        out = out + ns + tail

        with open(os.path.join(cdir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(out)
        with open(os.path.join(cdir, "package.json"), "w") as fh:
            fh.write(json.dumps({"name": f"hfad2-{c}", "private": True, "type": "module"}) + "\n")
        with open(os.path.join(cdir, "meta.json"), "w") as fh:
            fh.write(json.dumps({"id": f"hf-ugc-{c}", "name": f"hf-ugc-{c}"}) + "\n")
        shutil.copy(os.path.join(HERE, "hyperframes.json"), os.path.join(cdir, "hyperframes.json"))

        # ── assets: HARDLINK only what this chunk references ──────────
        # BOTH attribute refs (src="assets/...") AND CSS refs (url("assets/...")).
        # The first version matched only the attribute form, so @font-face files
        # were never linked into any chunk and Chrome silently rendered every
        # caption in a fallback font across two delivered cuts — caught by the
        # owner's "is this IBM flex font?" note, not by any gate
        # (feedback_a_missing_asset_dir_passes_every_gate).
        refs = sorted(
            set(re.findall(r'(?:src|href)="(assets/[^"]+)"', out))
            | set(re.findall(r'url\("(assets/[^"]+)"\)', out))
        )
        missing = []
        for r in refs:
            src = os.path.join(HERE, r)
            dst = os.path.join(cdir, r)
            if not os.path.exists(src):
                missing.append(r)
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst):
                os.remove(dst)
            os.link(src, dst)
        if missing:
            raise SystemExit(f"!! {c} references assets that do not exist: {missing}")

        vids = [r for r in refs if r.endswith(".mp4")]
        made.append((c, clen, p["nframes"], len(refs), len(vids)))
        print(f"{c:<4} {clen:>6.2f}s {p['nframes']:>5}f  {len(refs):>3} assets ({len(vids)} video)")

    tot = sum(m[2] for m in made)
    print(f"\n{len(made)} chunks, {tot} frames = {tot/FPS:.2f}s")
    assert tot == 1133, f"frame total {tot} != 1133"


if __name__ == "__main__":
    main()
