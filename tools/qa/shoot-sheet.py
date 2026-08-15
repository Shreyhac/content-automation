"""shoot-sheet.py, a beat contact sheet taken from the live page before any render.

Shoot the sheet BEFORE you believe the film is composed. A single element over
blank paper passes lint, passes validate, passes every safe-zone rule and still
reads as a void, and a geometry gate cannot see a colour that dies, a mascot
standing in the wrong place, or a beat that simply looks empty. A render round
costs minutes; this costs seconds.

Three things make it honest, and each was found by the sheet lying first:

  1. Replicate the renderer's clip scheduling. On a plain page load every
     element with a data-start sits in the tree at once, so the sheet shows
     twenty-two stacked clips at every beat and is meaningless. Elements
     outside [data-start, data-start+data-duration] are hidden before the shot.
  2. Seek every <video> by hand. Nothing is playing here, so each clip is
     parked at (t minus its own data-start) and the shot waits for `seeked`.
     Without this every beat shows frame 0 of the A-roll.
  3. tl.time(t, false) suppresses events, so a caption written by a tl.call()
     is absent from every frame. Replay it from the caption array.

The stage is dropped to scale(1) and the viewport is the stage's own size, so
one screenshot is one delivered frame at 1:1.

Usage
-----
    python3 tools/qa/shoot-sheet.py path/to/guard.json
    python3 tools/qa/shoot-sheet.py path/to/guard.json --beats 4.96,6.4
    python3 tools/qa/shoot-sheet.py path/to/guard.json --out hf67/qa --cols 6

Reads the same JSON as tools/gates/guard.py: project, document, timeline,
stage_id, stage_w, stage_h, beats, caption_replay. Beats may be bare numbers or
{"t": 4.3, "label": "the slam"}; labels are burned under each tile so a note
can name the beat rather than a pixel coordinate.

Then READ the sheets as images. The tool does not judge anything.
"""
import argparse
import json
import os
import subprocess
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is not installed. pip install playwright && playwright install chromium")


SEEK = r"""
(cfg) => {
  const t = cfg.t;

  // 1. the renderer's clip scheduling. Without this every clip is in the tree
  //    at once and the sheet shows a pile, not a beat.
  document.querySelectorAll('[data-start]').forEach(el => {
    if (el.id === cfg.stage_id || el.id === 'root' || el.tagName === 'AUDIO') return;
    const s = parseFloat(el.dataset.start || '0');
    const d = parseFloat(el.dataset.duration || '0');
    const live = t >= s - 1e-6 && (d <= 0 || t < s + d - 1e-6);
    el.style.setProperty('display', live ? '' : 'none', 'important');
  });

  window.__timelines[cfg.timeline].time(t, false);

  // 2. the caption, which seeking suppressed along with every other tl.call()
  if (cfg.caption_replay) {
    const arr = window[cfg.caption_replay.array];
    const el = document.getElementById(cfg.caption_replay.target);
    if (arr && el) {
      let txt = '';
      for (const c of arr) { if (c[0] <= t + 1e-6) txt = c[1]; else break; }
      el.textContent = txt;
    }
  }

  // 3. park every video on its own local time and wait for the decode
  const ps = [];
  for (const v of document.querySelectorAll('video')) {
    const s = parseFloat(v.getAttribute('data-start') || '0');
    const d = parseFloat(v.getAttribute('data-duration') || '999');
    let lt = t - s;
    if (lt < 0) lt = 0;
    if (lt > d) lt = Math.max(0, d - 0.05);
    if (lt > (v.duration || 999)) lt = Math.max(0, (v.duration || 0) - 0.05);
    ps.push(new Promise(res => {
      const done = () => { v.removeEventListener('seeked', done); res(); };
      v.addEventListener('seeked', done);
      try { v.currentTime = lt; } catch (e) { res(); }
      setTimeout(res, 900);          // never hang the sheet on one dead clip
    }));
  }
  return Promise.all(ps).then(() => true);
}
"""


CLIPS = r"""
(cfg) => {
  // Every composition element's own window, read out of the DOM. A fixed beat
  // grid never samples an element whose window falls between two beats: a
  // spliced-out GRID beat shipped in THREE delivered versions because the
  // sheets in those rounds sampled around 9.x and never inside it.
  const scope = document.getElementById(cfg.root_id) || document.body;
  const out = [];
  for (const el of scope.querySelectorAll('[data-start]')) {
    if (el === scope || el.tagName === 'AUDIO' || el.id === cfg.stage_id) continue;
    const s = parseFloat(el.getAttribute('data-start') || '0');
    const d = parseFloat(el.getAttribute('data-duration') || '0');
    out.push({ id: el.id || el.tagName.toLowerCase() + '.' + (el.className || ''),
               s: s, d: d });
  }
  return out;
}
"""


def clip_beats(pg, cfg, dedupe):
    """One sample inside every element's own window.

    Samples at start + 0.30s (past the entrance ease, which keeps opacity near
    zero for most of a short scene) and, for a window longer than 1.2s, again
    at its midpoint. Beats closer together than `dedupe` collapse to one shot.
    """
    clips = pg.evaluate(CLIPS, {"root_id": cfg.get("root_id", "root"),
                                "stage_id": cfg["stage_id"]})
    want = []
    for c in clips:
        end = c["s"] + c["d"] if c["d"] > 0 else c["s"] + 0.6
        want.append((min(c["s"] + 0.30, max(c["s"], end - 0.05)), c["id"]))
        if c["d"] > 1.2:
            want.append(((c["s"] + end) / 2.0, c["id"] + " mid"))
    want.sort()
    out = []
    for t, lab in want:
        if out and abs(out[-1][0] - t) < dedupe:
            continue
        out.append((t, lab))
    print("clip windows: %d elements, %d samples after dedupe at %.2fs" %
          (len(clips), len(out), dedupe))
    return out


def load(path, args):
    with open(path) as fh:
        cfg = json.load(fh)
    base = os.path.dirname(os.path.abspath(path))
    proj = args.project or cfg.get("project") or base
    cfg["project"] = proj if os.path.isabs(proj) else os.path.join(base, proj)
    cfg.setdefault("document", "index.html")
    cfg.setdefault("stage_id", "stage")
    cfg.setdefault("stage_w", 1080)
    cfg.setdefault("stage_h", 1920)
    beats = cfg.get("beats") or []
    if args.beats:
        beats = [float(x) for x in args.beats.split(",")]
    out = []
    for b in beats:
        if isinstance(b, dict):
            out.append((float(b["t"]), b.get("label", "")))
        else:
            out.append((float(b), ""))
    if not out and not args.from_clips:
        sys.exit("no beats. Shoot the beats, not a random sample.")
    cfg["_beats"] = out
    return cfg


def tile_pil(shots, sheet_dir, cols, per_sheet):
    """Labelled contact sheet. Labels matter: a note that says 'the beat at
    22.98' is actionable, a note that says 'tile 7' is not."""
    from PIL import Image, ImageDraw, ImageFont
    try:
        ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 13)
    except Exception:
        ft = ImageFont.load_default()
    made = []
    W, H, LAB = 268, 476, 18
    for i in range(0, len(shots), per_sheet):
        chunk = shots[i:i + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (W * cols, (H + LAB) * rows), (26, 26, 26))
        d = ImageDraw.Draw(sheet)
        for k, (f, t, lab) in enumerate(chunk):
            im = Image.open(f).convert("RGB").resize((W, H))
            x, y = (k % cols) * W, (k // cols) * (H + LAB)
            sheet.paste(im, (x, y))
            d.text((x + 4, y + H + 3), ("%.2f %s" % (t, lab)).strip(), fill=(255, 218, 90), font=ft)
        p = os.path.join(sheet_dir, "sheet%02d.jpg" % (i // per_sheet))
        sheet.save(p, quality=88)
        made.append(p)
    return made


def tile_ffmpeg(shots, sheet_dir, cols, per_sheet):
    """Fallback when Pillow is missing. No labels, so prefer Pillow."""
    made = []
    for i in range(0, len(shots), per_sheet):
        chunk = shots[i:i + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        lst = os.path.join(sheet_dir, "_l%d.txt" % i)
        with open(lst, "w") as fh:
            fh.write("".join("file '%s'\n" % c[0] for c in chunk))
        p = os.path.join(sheet_dir, "sheet%02d.jpg" % (i // per_sheet))
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-frames:v", str(len(chunk)),
                        "-vf", "scale=270:480,tile=%dx%d" % (cols, rows),
                        p, "-loglevel", "error"], check=False)
        os.remove(lst)
        made.append(p)
    return made


def main():
    ap = argparse.ArgumentParser(description="shoot a labelled contact sheet of every beat")
    ap.add_argument("config", help="the film's guard JSON (same file guard.py reads)")
    ap.add_argument("--project", help="override the project dir holding index.html")
    ap.add_argument("--beats", help="comma-separated beats, overrides the config")
    ap.add_argument("--out", help="output dir, default <project>/qa")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=2, help="rows per sheet, keep it readable as one image")
    ap.add_argument("--from-clips", action="store_true",
                    help="derive the beats from every element's own data-start window instead of "
                         "the config's beat list. Use this for the per-delivery sheet.")
    ap.add_argument("--dedupe", type=float, default=0.20,
                    help="collapse clip samples closer together than this, seconds")
    a = ap.parse_args()

    cfg = load(a.config, a)
    out = a.out or os.path.join(cfg["project"], "qa")
    os.makedirs(out, exist_ok=True)
    doc = "file://" + os.path.join(cfg["project"], cfg["document"])
    per_sheet = a.cols * a.rows

    shots, errors = [], []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": cfg["stage_w"], "height": cfg["stage_h"]},
                           device_scale_factor=1).new_page()
        # A dead page screenshots perfectly well. Read the errors before the sheet.
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        pg.goto(doc, wait_until="domcontentloaded", timeout=90000)
        ok = False
        for _ in range(40):
            pg.wait_for_timeout(500)
            if pg.evaluate("(n) => !!(window.__timelines && window.__timelines[n])", cfg["timeline"]):
                ok = True
                break
        if not ok:
            print("FAIL, window.__timelines.%s never became available" % cfg["timeline"])
            for e in errors[:8]:
                print("   ", e)
            b.close()
            return 1
        pg.wait_for_timeout(2500)
        # 1:1, so one screenshot is one delivered frame
        pg.evaluate("(id) => { document.getElementById(id).style.transform = 'none'; }", cfg["stage_id"])

        beats = clip_beats(pg, cfg, a.dedupe) if a.from_clips else cfg["_beats"]

        scfg = {"timeline": cfg["timeline"], "stage_id": cfg["stage_id"],
                "caption_replay": cfg.get("caption_replay")}
        for t, lab in beats:
            scfg["t"] = t
            pg.evaluate(SEEK, scfg)
            pg.wait_for_timeout(260)
            f = os.path.join(out, "b_%08.3f.png" % t)
            pg.locator("#" + cfg["stage_id"]).screenshot(path=f)
            shots.append((f, t, lab))
            print("shot %7.3f  %s" % (t, lab))
        b.close()

    if errors:
        print("PAGE ERRORS, the sheet below is of a broken page:")
        for e in errors[:8]:
            print("   ", e)

    try:
        import PIL  # noqa: F401
        made = tile_pil(shots, out, a.cols, per_sheet)
    except ImportError:
        print("Pillow missing, tiling with ffmpeg and losing the labels")
        made = tile_ffmpeg(shots, out, a.cols, per_sheet)

    for m in made:
        print("sheet ->", m)
    print("%d beats shot. Now READ them as images, one question first: is anything empty?"
          % len(shots))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
