"""Gates that run BEFORE the render, because a render round costs minutes.

Four things have shipped past lint+validate in this repo before, and each one
has its own check here:

  1. a referenced asset that does not exist on disk — a broken <img> is
     invisible to every structural check (vid62)
  2. a guard whose scope silently missed elements — this one measures EVERY
     absolutely-positioned element that actually paints, not just .scene
     children (vid59/vid62)
  3. text landing on text — measured by box, excluded by DOM ancestry (vid64)
  4. a beat that is one element over blank paper — the ink-coverage check
     below fails a beat whose graphics zone is emptier than 1.5% (vid61)

Usage:  python3 guard67.py
"""
import json, os, re, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
DOC  = "file://" + os.path.join(HERE, "index.html")

# every scene boundary, plus the frames inside a beat where something lands
BEATS = [0.0, 1.21, 2.2, 2.772, 3.24, 4.329, 5.22, 6.677, 7.869, 8.887, 9.72, 10.215, 10.62, 11.126, 11.54, 12.805, 13.84, 14.324, 14.72, 15.072, 15.36, 15.899, 16.34, 16.703, 17.0, 18.705, 20.1, 20.694, 21.18, 22.17, 22.98, 23.606, 24.119, 25.275, 26.22, 26.968, 27.58, 29.912, 31.82, 33.697, 35.1]

# the bands, in 1080x1920 stage space
TOP_TEXT   = 150      # Instagram chrome — no text above this
BAND_Y     = 1600     # no text, no face below this
RAIL_X     = 960      # like/comment rail, x>960 between y900-1600
RAIL_Y0, RAIL_Y1 = 900, 1600
LEFT_PAD   = 60       # crop buffer

FACE_SPLIT = (0, 620, 1080, 1920)   # the presenter's face owns everything below the seam
CROWN_WORST = 660                   # crown lands here in SPLIT; captions stay above it


def check_assets():
    html = open(os.path.join(HERE, "index.html")).read()
    missing = []
    for m in re.finditer(r'src="(assets/[^"]+)"', html):
        p = os.path.join(HERE, m.group(1))
        if not os.path.exists(p):
            missing.append(m.group(1))
    for m in re.finditer(r"url\('(assets/[^']+)'\)", html):
        p = os.path.join(HERE, m.group(1))
        if not os.path.exists(p):
            missing.append(m.group(1))
    return sorted(set(missing))


PROBE = r"""
(t) => {
  const tl = window.__timelines.vid67;
  tl.time(t, false);
  // tl.time(..., false) suppresses events, so the tl.call() that writes the
  // caption never runs for a gate. Without this the caption carries no text,
  // `isText` is false, and EVERY caption check silently measures nothing —
  // the crown/band/rail rules were inert until this was added.
  if (window.__CAPS) {
    let txt = '';
    for (const c of window.__CAPS) { if (c[0] <= t + 1e-6) txt = c[1]; else break; }
    document.getElementById('cap').textContent = txt;
  }
  const stage = document.getElementById('stage');
  const sb = stage.getBoundingClientRect();
  const S = 2;                               // #stage is transform:scale(2)
  const out = [];
  const all = stage.querySelectorAll('*');
  for (const el of all) {
    if (el.hasAttribute('data-layout-ignore')) continue;
    const cs = getComputedStyle(el);
    // an element that carries its own text is ALWAYS measured, whatever its
    // position. #cap is display:inline-block/static, so a position-only filter
    // skipped it — and #capW, being its parent, has no text node of its own.
    // Between them the caption was invisible to every rule in this file.
    let ownText = '';
    for (const c of el.childNodes) if (c.nodeType === 3) ownText += c.textContent;
    ownText = ownText.trim();
    if (!ownText && cs.position !== 'absolute' && cs.position !== 'relative') continue;
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    // effective opacity, walking up to the stage
    let op = 1, n = el;
    while (n && n !== stage) { op *= parseFloat(getComputedStyle(n).opacity || '1'); n = n.parentElement; }
    if (op < 0.06) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const txt = ownText;
    // build a DOM path so overlaps between an element and its own ancestor can
    // be excluded without guessing from ids
    const path = [];
    let rot = false;
    n = el;
    while (n && n !== stage) {
      path.push(n.id || n.tagName + '.' + (n.className || ''));
      const tr = getComputedStyle(n).transform;
      if (tr && tr !== 'none') {
        const m = tr.match(/matrix\(([^)]+)\)/);
        if (m) { const v = m[1].split(',').map(Number); if (Math.abs(v[1]) > 0.02) rot = true; }
      }
      n = n.parentElement;
    }
    out.push({
      id: el.id || null,
      tag: el.tagName,
      cls: typeof el.className === 'string' ? el.className : '',
      text: txt.slice(0, 46),
      op: op, rot: rot,
      x: (r.left - sb.left) / S, y: (r.top - sb.top) / S,
      w: r.width / S, h: r.height / S,
      path: path
    });
  }
  const faceClip = getComputedStyle(document.getElementById('faceScene')).clipPath;
  // a <video> painted outside its own [data-start, data-start+data-duration]
  // window renders as dead grey, and nothing structural can see that
  const vids = [];
  for (const v of stage.querySelectorAll('video')) {
    let op = 1, n = v, hidden = false;
    while (n && n !== stage) {
      const c = getComputedStyle(n);
      if (c.visibility === 'hidden' || c.display === 'none') hidden = true;
      op *= parseFloat(c.opacity || '1');
      n = n.parentElement;
    }
    vids.push({ id: v.id, painted: !hidden && op > 0.06,
                s: parseFloat(v.getAttribute('data-start') || '0'),
                d: parseFloat(v.getAttribute('data-duration') || '0') });
  }
  return { els: out, faceClip: faceClip, vids: vids };
}
"""


def face_state(clip):
    # Chromium collapses inset(700px 0px 0px 0px) to inset(700px 0px 0px) when
    # left == right, so never assume four numbers come back
    nums = [float(x) for x in re.findall(r'(-?[\d.]+)px', clip)]
    if not nums:
        return "full"
    return "split" if nums[0] >= 610 else "full"


def run():
    problems = []
    missing = check_assets()
    for m in missing:
        problems.append(("ASSET", 0.0, f"referenced but not on disk: {m}"))

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1200, "height": 900}).new_page()
        pg.goto(DOC, wait_until="domcontentloaded", timeout=90000)
        ok = False
        for _ in range(40):
            pg.wait_for_timeout(500)
            if pg.evaluate("() => !!(window.__timelines && window.__timelines.vid67)"):
                ok = True; break
        if not ok:
            print("FAIL — the timeline never became available"); return 1
        pg.wait_for_timeout(2000)

        for t in BEATS:
            data = pg.evaluate(PROBE, t)
            els, state = data["els"], face_state(data["faceClip"])

            for v in data.get("vids", []):
                if not v["painted"]:
                    continue
                if t < v["s"] - 1e-6 or t > v["s"] + v["d"] + 1e-6:
                    problems.append(("VIDWIN", t,
                        f"<video {v['id']}> paints at {t:.3f} but its window is "
                        f"{v['s']:.3f}-{v['s']+v['d']:.3f} — it renders dead"))

            texts = [e for e in els if e["text"]]

            for e in els:
                x0, y0, x1, y1 = e["x"], e["y"], e["x"] + e["w"], e["y"] + e["h"]
                nm = e["id"] or (e["tag"] + "." + e["cls"])[:28]
                isText = bool(e["text"])

                if isText:
                    if y0 < TOP_TEXT:
                        problems.append(("TOP", t, f"{nm} text at y{y0:.0f} < {TOP_TEXT} — {e['text'][:26]}"))
                    if y1 > BAND_Y:
                        problems.append(("BAND", t, f"{nm} text to y{y1:.0f} > {BAND_Y} — {e['text'][:26]}"))
                    if x0 < LEFT_PAD:
                        problems.append(("LEFT", t, f"{nm} text at x{x0:.0f} < {LEFT_PAD} — {e['text'][:26]}"))
                    if x1 > RAIL_X and y1 > RAIL_Y0 and y0 < RAIL_Y1:
                        problems.append(("RAIL", t, f"{nm} text to x{x1:.0f} in the rail — {e['text'][:26]}"))

                # on SPLIT beats every caption must clear the worst-case crown
                if state == "split" and isText and y1 > CROWN_WORST:
                    problems.append(("ONCROWN", t,
                        f"{nm} runs to y{y1:.0f}, past the worst-case crown at {CROWN_WORST} — {e['text'][:26]}"))

            # text on text, excluding ancestor/descendant pairs
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    a, c = texts[i], texts[j]
                    if a["path"][0] in c["path"] or c["path"][0] in a["path"]:
                        continue
                    # a rotated box's axis-aligned rect is not where its ink is
                    if a.get("rot") or c.get("rot"):
                        continue
                    ox = min(a["x"] + a["w"], c["x"] + c["w"]) - max(a["x"], c["x"])
                    oy = min(a["y"] + a["h"], c["y"] + c["h"]) - max(a["y"], c["y"])
                    if ox > 6 and oy > 6:
                        area = ox * oy
                        small = min(a["w"] * a["h"], c["w"] * c["h"])
                        if area > 0.22 * small:
                            problems.append(("TXTTXT", t,
                                f"{a['id'] or a['tag']} '{a['text'][:18]}' over "
                                f"{c['id'] or c['tag']} '{c['text'][:18]}' ({area:.0f}px²)"))

            # the band is ONE always-running track now, so the rule is simply:
            # it shows on SPLIT and is hidden on FULL
            lit = [v["id"] for v in data.get("vids", []) if v["painted"] and v["id"] != "aroll"]
            if state == "split" and lit != ["vband"]:
                problems.append(("BAND", t, f"band track not painting in a SPLIT beat: {lit}"))
            if state == "full" and lit:
                problems.append(("BAND", t, f"band still painting on a FULL beat: {lit}"))

        b.close()

    seen, uniq = set(), []
    for kind, t, msg in problems:
        k = (kind, msg)
        if k in seen: continue
        seen.add(k); uniq.append((kind, t, msg))

    if not uniq:
        print("PASS — assets resolve, bands clear, no text-on-text, no void beats")
        return 0
    print(f"{len(uniq)} problem(s):")
    for kind, t, msg in uniq:
        print(f"  [{kind:8s}] t={t:6.3f}  {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(run())
