"""guard.py, the pre-render gate. Drives the composition timeline in a real
browser and measures what actually PAINTS at every beat.

A render round costs minutes. Every check below exists because a defect shipped
past `hyperframes lint` and `hyperframes validate`, which read the document and
the console and nothing else. The film, the beat and the fix are named on each
one so nobody deletes a check thinking it is theoretical.

  1. ASSET   a referenced file that is not on disk. `hf62/assets/shots/` did
             not exist, so 13.3s rendered as a blank white card. The card
             paints; it is the <img> inside it that is 0x0, and no structural
             check can see that. Resolved on disk AND at runtime via
             naturalWidth, because a present-but-truncated file also loads to 0.
  2. SCOPE   a guard whose reach silently missed its target. On vid62 the
             privacy gate read a JSON file that nothing ever wrote, one gate
             defaulted to a single chunk and printed one OK line that read as a
             film-wide pass, and Playwright's browser binary was missing so
             every DOM gate was crashing rather than checking. This script
             measures EVERY painting element, prints what it measured, and
             fails when an allowlist entry matches nothing.
  3. PAINT   position is not visibility. On the vid56 short the captions sat at
             exactly the right y1396 with no z-index, computing to auto (0),
             under a full-bleed <video> at z-index 2: no captions for 27 of 43
             seconds, and every gate passed. Coordinates are not a paint test.
             elementFromPoint at the element's own centre is.
  4. TXTTXT  text landing on text. Every gate on vid64 checked graphics against
             the face, the card and the band. Two graphics colliding with each
             other was unguarded, and a panel printed on top of a caption for
             the whole hook.
  5. VOID    a beat that is one element over blank paper. Passes lint, passes
             validate, passes every safe-zone rule, and reads as a hole. The
             ink-coverage floor is the only thing that catches it (vid61).
  6. CONTRA  contrast over video. `validate` compares text to its CSS
             background; over an A-roll the ground is his room. That hid 22
             bare-text elements on vid62. Measured as the FRACTION of area
             brighter than 150, never the mean: white type on a black screen
             averages dark while still colliding, and the mean rated one title
             fine at a measured bright-fraction of 59.6%.
  7. VIDWIN  a <video> painted outside its own [data-start, +data-duration]
             window renders dead grey. Seven of nine dashboard placements on
             vid62 were black, on the film whose brief was "more screen
             recordings".
  8. FACEWIN the presenter whitelist. A gate that lists the spans his face may
             NOT paint in cannot catch what its detector missed; a missing
             blacklist entry ships the defect while a missing whitelist entry
             only costs a beat of face. Choose which way the gate fails.
  9. CSS     every stylesheet the document actually loads must be covered by
             the staleness hash, or a CSS fix silently never ships. `pichash`
             hashed chunk.js and base.css but not vid62.css, which held most of
             the film's look. Also asserts each sheet parsed a nonzero rule
             count: one malformed comment drops every rule after it and lint,
             validate and inspect all pass, because none of them parse the
             cascade.
 10. TIMEDLEAK a timed element that paints OUTSIDE its own window. Every other
             check here asks "did it paint when it should"; nothing asked the
             other half. An <svg class="clip"> with data-start 15.35 painted
             for an entire film, because the framework gives visibility control
             to div/video/img clips only. The owner found it, not a gate.
 11. DOMBAL / IDGONE  a text splice that silently removed a beat. One swallowed
             a whole scene and shipped in THREE delivered versions, and an
             unbalanced <div> count closes #root early where the browser
             silently repairs it. Pass --ids to keep the baseline.

Usage
-----
    python3 tools/gates/guard.py path/to/guard.json
    python3 tools/gates/guard.py path/to/guard.json --project hf67 --beats 4.3,5.2

Nothing about a film is hardcoded here. Bootstrap the config with
`tools/gates/derive_config.py <film-dir>`, which derives what is derivable and
leaves a loud TODO on every value that is a measurement. This script REFUSES to
run while any TODO is left, because a half-finished config that silently treats
its blanks as absent prints the same PASS a real run prints. See
tools/gates/README.md and tools/gates/guard.example.json for the config.

Exit code 0 means every check RAN and passed. Read the coverage block it prints
before believing a PASS.
"""
import argparse
import json
import os
import re
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright is not installed. pip install playwright && playwright install chromium")


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

DEFAULTS = {
    "document": "index.html",
    "stage_id": "stage",
    "stage_w": 1080,
    "stage_h": 1920,
    "asset_prefix": "assets/",
    # Instagram bands in stage space. Full spec in docs/02-safe-zones.md.
    "bands": {
        "top_text": 150,     # status bar and Reels chrome, no text above this
        "band_y": 1600,      # bottom UI band, no text and no face below this
        "rail_x": 960,       # like/comment rail
        "rail_y0": 900,
        "rail_y1": 1600,
        "left_pad": 60,      # crop buffer
    },
    "face": None,
    "states": {},
    "face_windows": None,
    "void": None,
    "contrast": {"enabled": True, "bright": 150, "max_bright_frac": 0.35,
                 "min_area": 2500},
    "paint": {"enabled": True},
    "caption_replay": None,
    "stylesheets": None,
    "allow": [],
    "beats": [],
    # The renderer gives visibility control to div/video/img clips only. Anything
    # else carrying a data-start paints for the whole film.
    "root_id": "root",
    "apply_clip_schedule": True,
    "managed_tags": ["DIV", "VIDEO", "IMG"],
}


TODO = "TODO"


def find_todos(node, path=""):
    """Every unresolved TODO marker in the raw config, by dotted path.

    Keys beginning with `_` are the comment block `derive_config.py` writes, and
    those comments EXPLAIN the TODOs, so they carry the word themselves. They are
    skipped, and nothing else is.
    """
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and k.startswith("_"):
                continue
            out += find_todos(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += find_todos(v, "%s[%d]" % (path, i))
    elif isinstance(node, str) and TODO in node:
        out.append(path)
    return out


def load_config(path, args):
    with open(path) as fh:
        raw = json.load(fh)

    # A half-finished config must not be able to masquerade as a passing gate.
    # Every TODO in a derived config is a MEASUREMENT: the crown of his head, the
    # rectangle graphics are supposed to own, the windows his face may paint in.
    # Treated as absent, each one simply switches its check off, and the run
    # prints the same PASS a real one prints. That is the failure this repo has
    # made more than any other: a gate that has never run is not a gate, and a
    # green run and a gate that silently did nothing produce identical output.
    # So refuse, name the paths, and make the operator resolve or DELETE each one.
    todos = find_todos(raw)
    if todos:
        print("REFUSING TO RUN: %d unresolved TODO(s) in %s" % (len(todos), path))
        for t in todos:
            print("   %s" % t)
        print("Each TODO is a measurement, not a blank. Fill it from the take, or DELETE "
              "the key if this film genuinely has no such constraint. Deleting is a "
              "decision and is fine; leaving it is a gate that cannot fail. The "
              "`_`-prefixed keys beside each one say what the number means and how to "
              "measure it. Walkthrough: tools/gates/README.md.")
        sys.exit(2)

    cfg = dict(DEFAULTS)
    for k, v in raw.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            merged = dict(cfg[k])
            merged.update(v)
            cfg[k] = merged
        else:
            cfg[k] = v
    base = os.path.dirname(os.path.abspath(path))
    proj = args.project or cfg.get("project") or base
    cfg["project"] = proj if os.path.isabs(proj) else os.path.join(base, proj)
    if args.beats:
        cfg["beats"] = [float(x) for x in args.beats.split(",")]
    # a beat may be a bare number or {"t": 4.3, "label": "the slam"}
    cfg["beats"] = [b["t"] if isinstance(b, dict) else float(b) for b in cfg["beats"]]
    if not cfg["beats"]:
        sys.exit("config has no beats. A gate with nothing to measure is not a gate.")
    if not cfg.get("timeline"):
        sys.exit("config has no `timeline` (the key in window.__timelines).")
    return cfg


# ---------------------------------------------------------------------------
# filesystem: a broken <img> is invisible to every structural check
# ---------------------------------------------------------------------------

def check_assets(cfg):
    """Resolve every referenced asset path against the disk.

    A whole 13.3s scene once rendered as a blank white card because one
    directory did not exist. Missing DIRECTORIES are reported separately: when
    a whole folder is gone, every path under it fails and the real message is
    the folder.
    """
    doc = os.path.join(cfg["project"], cfg["document"])
    html = open(doc).read()
    pref = re.escape(cfg["asset_prefix"])
    missing, dirs = [], set()
    pats = [r'src="(%s[^"]+)"' % pref,
            r"src='(%s[^']+)'" % pref,
            r"url\('(%s[^']+)'\)" % pref,
            r'url\("(%s[^"]+)"\)' % pref,
            r"url\((%s[^)'\"]+)\)" % pref]
    for pat in pats:
        for m in re.finditer(pat, html):
            rel = m.group(1)
            p = os.path.join(cfg["project"], rel)
            if not os.path.exists(p):
                missing.append(rel)
                d = os.path.dirname(p)
                if not os.path.isdir(d):
                    dirs.add(os.path.relpath(d, cfg["project"]))
    return sorted(set(missing)), sorted(dirs)


# ---------------------------------------------------------------------------
# the probe. Runs in the page, once per beat.
# ---------------------------------------------------------------------------

def check_splice(cfg, ids_path):
    """The two checks a text splice needs, and nothing else provides.

    A marker-to-marker splice once swallowed a whole scene: the removed block
    took the GRID beat with it, its tweens kept firing at nothing, every gate
    passed, and the beat played as bare footage plus caption for THREE
    delivered versions, because the QA contact sheets sampled around 9.x and
    never inside it.

      1. Diff the ELEMENT ID LIST against the last run. A disappeared id is a
         disappeared beat.
      2. Count <div> opens against closes. An imbalance means a premature
         #root close, which browsers silently repair, so the page looks fine
         and the render is not. That one shipped too.

    The id baseline is written on first run and diffed on every run after, so
    it costs one flag and catches the class outright.
    """
    problems = []
    html = open(os.path.join(cfg["project"], cfg["document"])).read()

    opens = len(re.findall(r"<div\b", html, re.I))
    closes = len(re.findall(r"</div\s*>", html, re.I))
    if opens != closes:
        problems.append(("DOMBAL", 0.0,
                         "%d <div> opens against %d closes. An imbalance closes #root early and "
                         "the browser silently repairs it." % (opens, closes)))

    ids = sorted(set(re.findall(r'\sid="([^"]+)"', html)))
    if ids_path:
        if os.path.exists(ids_path):
            old = json.load(open(ids_path))
            gone = [i for i in old if i not in ids]
            for g in gone:
                problems.append(("IDGONE", 0.0,
                                 "element id '%s' existed at the last snapshot and does not now. "
                                 "A disappeared id is a disappeared beat." % g))
            added = [i for i in ids if i not in old]
            print("splice diff: %d ids, %d gone, %d added, baseline %s"
                  % (len(ids), len(gone), len(added), ids_path))
            # Never overwrite a baseline that just reported a disappearance, or
            # the second run silently forgets the beat the first run found.
            if gone:
                print("baseline KEPT, so the next run still reports these. Delete it "
                      "deliberately once the removal is intended.")
            else:
                with open(ids_path, "w") as fh:
                    json.dump(ids, fh, indent=0)
        else:
            print("splice diff: no baseline, writing %d ids to %s" % (len(ids), ids_path))
            with open(ids_path, "w") as fh:
                json.dump(ids, fh, indent=0)
    return problems


PROBE = r"""
(cfg) => {
  const t = cfg.t;
  const tl = window.__timelines[cfg.timeline];
  tl.time(t, false);

  // tl.time(..., false) SUPPRESSES EVENTS, so any tl.call() in the timeline
  // does not run for a gate. The caption engine writes its text from a
  // tl.call(); without replaying it here the caption element carries no text,
  // isText is false, and every caption rule below silently measures nothing.
  // The crown, band and rail rules were all inert until this was found.
  if (cfg.caption_replay) {
    const arr = window[cfg.caption_replay.array];
    const el = document.getElementById(cfg.caption_replay.target);
    if (arr && el) {
      let txt = '';
      for (const c of arr) { if (c[0] <= t + 1e-6) txt = c[1]; else break; }
      el.textContent = txt;
    }
  }

  const stage = document.getElementById(cfg.stage_id);

  // Replicate the renderer's clip scheduling BEFORE measuring anything.
  // A plain page load leaves every element with a data-start in the tree at
  // once, so a caption pattern's 22 clips stack at identical coordinates: the
  // last one in the DOM wins every hit test, reporting the other 21 as failing
  // and telling you nothing. The renderer gives visibility control to div,
  // video and img clips only, so those are what this hides, and anything else
  // carrying a data-start is left exactly as the renderer would leave it.
  // Scan for timed elements from the COMPOSITION ROOT, not from the stage. A
  // timed element can be a sibling of #stage rather than a child of it, and a
  // stage-scoped query would never look at it. Geometry below stays
  // stage-relative; this scan does not need coordinates.
  const scope = document.getElementById(cfg.root_id) || stage;
  const timed = [], MANAGED = cfg.managed_tags;
  for (const el of scope.querySelectorAll('[data-start]')) {
    if (el === stage || el === scope || el.tagName === 'AUDIO') continue;
    const s = parseFloat(el.getAttribute('data-start') || '0');
    const d = parseFloat(el.getAttribute('data-duration') || '0');
    const live = t >= s - 1e-6 && (d <= 0 || t < s + d - 1e-6);
    const managed = MANAGED.indexOf(el.tagName) >= 0;
    if (cfg.apply_clip_schedule && managed) {
      el.style.setProperty('display', live ? '' : 'none', 'important');
    }
    timed.push({ el: el, s: s, d: d, live: live, managed: managed });
  }

  // The composition is a 1080x1920 #stage under transform:scale(2). Measuring
  // through the scale is fine for geometry, but elementFromPoint takes VIEWPORT
  // coordinates, and a 2160x3840 stage in any sane viewport puts every element
  // off-screen: elementFromPoint returns null, and null reads as a pass. So the
  // probe drops the stage to 1:1 and the viewport is the stage's own size.
  stage.style.transform = 'none';
  const sb = stage.getBoundingClientRect();
  const S = sb.width / cfg.stage_w || 1;

  const out = [];
  for (const el of stage.querySelectorAll('*')) {
    if (el.hasAttribute('data-layout-ignore')) continue;
    const cs = getComputedStyle(el);

    // An element that carries its own text is ALWAYS measured, whatever its
    // position. The caption span is display:inline-block and position:static,
    // so a position-only filter skipped it, and its parent, being a wrapper,
    // has no text node of its own. Between the two the caption was invisible
    // to every rule in this file.
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

    // A DOM path, so an overlap between an element and its own ancestor can be
    // excluded by ancestry rather than guessed at from ids.
    const path = [];
    let rot = false;
    n = el;
    while (n && n !== stage) {
      path.push(n.id || n.tagName + '.' + (n.className || ''));
      const tr = getComputedStyle(n).transform;
      if (tr && tr !== 'none') {
        const m = tr.match(/matrix\(([^)]+)\)/);
        // a rotated box's axis-aligned rect is not where its ink is
        if (m) { const v = m[1].split(',').map(Number); if (Math.abs(v[1]) > 0.02) rot = true; }
      }
      n = n.parentElement;
    }

    // Does this text sit on its own opaque ground, or on the picture? A
    // background counts as a ground only at alpha >= 0.8: a gradient at .22
    // is not one, and treating it as one is how 22 bare-text elements went
    // unchecked for a whole film.
    let ground = false;
    n = el;
    while (n && n !== stage && !ground) {
      const bc = getComputedStyle(n).backgroundColor || '';
      const m = bc.match(/rgba?\(([^)]+)\)/);
      if (m) {
        const v = m[1].split(',').map(Number);
        if (v.length < 4 || v[3] >= 0.8) ground = true;
      }
      n = n.parentElement;
    }

    // Position is not visibility. Sample three points across the element's own
    // vertical centre; self or a descendant returning is a pass, an ancestor
    // returning is a pass (a parent cannot paint over its own child's text),
    // null is NOT a pass and is counted separately as an unmeasured probe.
    let hit = 'none', nulls = 0, over = null;
    for (const fx of [0.2, 0.5, 0.8]) {
      const px = r.left + r.width * fx, py = r.top + r.height / 2;
      const got = document.elementFromPoint(px, py);
      if (!got) { nulls++; continue; }
      if (got === el || el.contains(got) || got.contains(el)) { hit = 'self'; break; }
      if (hit === 'none') { hit = 'blocked'; over = got.id || got.tagName + '.' + (got.className || ''); }
    }
    if (hit === 'none' && nulls === 3) hit = 'null';

    const col = (cs.color.match(/\d+/g) || [255, 255, 255]).map(Number);
    out.push({
      id: el.id || null,
      tag: el.tagName,
      cls: typeof el.className === 'string' ? el.className : '',
      text: ownText.slice(0, 46),
      op: op, rot: rot, ground: ground, hit: hit, over: over,
      lum: (0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2]) / 255,
      x: (r.left - sb.left) / S, y: (r.top - sb.top) / S,
      w: r.width / S, h: r.height / S,
      cx: r.left + r.width / 2, cy: r.top + r.height / 2,
      path: path
    });
  }

  // A <video> painted outside its own [data-start, data-start+data-duration]
  // window renders as dead grey and nothing structural can see it.
  const vids = [];
  for (const v of stage.querySelectorAll('video')) {
    let op = 1, n = v, hidden = false;
    while (n && n !== stage) {
      const c = getComputedStyle(n);
      if (c.visibility === 'hidden' || c.display === 'none') hidden = true;
      op *= parseFloat(c.opacity || '1');
      n = n.parentElement;
    }
    vids.push({ id: v.id || v.getAttribute('src') || 'video', painted: !hidden && op > 0.06,
                s: parseFloat(v.getAttribute('data-start') || '0'),
                d: parseFloat(v.getAttribute('data-duration') || '0') });
  }

  // Every other check in this file asks "did it paint when it should".
  // Nothing asked "did it paint when it should NOT". An <svg class="clip">
  // with data-start 15.35 painted for an ENTIRE film, showing up beside chips
  // at 0:05, on cards at 0:07 and in the graph at 0:13, because the framework
  // gives visibility control to div, video and img clips only. It was found by
  // the owner watching, and the per-element contact sheet could not find it
  // either: that sheet samples an element's own window, never the rest of the
  // film where it should be absent.
  const leaks = [];
  let unmanaged = 0;
  for (const it of timed) {
    if (!it.managed) unmanaged++;
    if (it.live) continue;
    let op = 1, n = it.el, hidden = false;
    while (n && n !== scope.parentElement) {
      const c = getComputedStyle(n);
      if (c.visibility === 'hidden' || c.display === 'none') hidden = true;
      op *= parseFloat(c.opacity || '1');
      n = n.parentElement;
    }
    if (hidden || op < 0.06) continue;
    const r = it.el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    leaks.push({ id: it.el.id || null, tag: it.el.tagName,
                 cls: typeof it.el.className === 'string' ? it.el.className : '',
                 s: it.s, d: it.d, managed: it.managed });
  }

  // Images get their own pass. A broken <img> is usually a bare, unpositioned
  // child of a card that paints perfectly well, so the element filter above
  // skips it and the defect is invisible: exactly the vid62 blank-white-card
  // bug. naturalWidth 0 also catches a file that exists but is truncated.
  const imgs = [];
  for (const im of stage.querySelectorAll('img')) {
    const cs = getComputedStyle(im);
    if (cs.display === 'none') continue;
    imgs.push({ id: im.id || null, src: im.getAttribute('src') || '',
                natw: im.naturalWidth || 0 });
  }

  // Is a full-frame cover up? A wipe sheet at mid-transition legitimately owns
  // the whole frame, and measuring contrast against it reports the wipe, not a
  // defect. Seventeen WCAG failures on one film all landed at exactly
  // duration/2, the midpoint of a wipe. The face-safety pass learned the same
  // thing: skip frames where a full-frame cover is up.
  let covered = false;
  {
    const A = sb.width * sb.height;
    for (const el of stage.querySelectorAll('*')) {
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      let op = 1, n = el;
      while (n && n !== stage) { op *= parseFloat(getComputedStyle(n).opacity || '1'); n = n.parentElement; }
      if (op < 0.6) continue;
      const bc = cs.backgroundColor || '';
      const m = bc.match(/rgba?\(([^)]+)\)/);
      const opaque = m && (m[1].split(',').length < 4 || Number(m[1].split(',')[3]) >= 0.6);
      if (!opaque) continue;
      const r = el.getBoundingClientRect();
      if (r.width * r.height >= 0.9 * A) { covered = true; break; }
    }
  }

  let faceClip = null;
  if (cfg.face_el) {
    const f = document.getElementById(cfg.face_el);
    if (f) faceClip = getComputedStyle(f).clipPath;
  }
  return { els: out, faceClip: faceClip, vids: vids, imgs: imgs, leaks: leaks,
           covered: covered,
           timed: timed.length, unmanaged: unmanaged, scale: S };
}
"""

SHEETS = r"""
() => {
  const out = [];
  for (const s of document.styleSheets) {
    let n = -1;
    try { n = s.cssRules.length; } catch (e) { n = -1; }
    out.push({ href: s.href ? s.href.split('/').pop() : '<inline>', rules: n });
  }
  return out;
}
"""


# ---------------------------------------------------------------------------
# face state from clip-path
# ---------------------------------------------------------------------------

def inset_numbers(clip):
    """Expand a CSS inset() to four numbers, top right bottom left.

    Chromium collapses inset(700px 0px 0px 0px) to inset(700px 0px 0px) when
    left equals right, and collapses further from there. A guard that assumed
    four numbers came back treated every collapsed value as "no clip" and
    reported the wrong face state for the whole film. Expand the shorthand.
    """
    nums = [float(x) for x in re.findall(r"(-?[\d.]+)px", clip or "")]
    if not nums:
        return None
    if len(nums) == 1:
        return [nums[0]] * 4
    if len(nums) == 2:
        return [nums[0], nums[1], nums[0], nums[1]]
    if len(nums) == 3:
        return [nums[0], nums[1], nums[2], nums[1]]
    return nums[:4]


CMP = {">=": lambda a, b: a >= b, "<=": lambda a, b: a <= b,
       ">": lambda a, b: a > b, "<": lambda a, b: a < b,
       "==": lambda a, b: abs(a - b) < 0.51, "!=": lambda a, b: abs(a - b) >= 0.51}


def face_state(cfg, clip):
    """Name the face state from the clip-path, by the config's rules in order.

    Rules look like {"state": "split", "when": {"left": [">=", 540]}}, keyed on
    top/right/bottom/left. First match wins, so order them most specific first.
    """
    face = cfg.get("face") or {}
    rules = face.get("rules") or []
    default = face.get("default", "full")
    nums = inset_numbers(clip)
    if nums is None:
        return default
    named = dict(zip(("top", "right", "bottom", "left"), nums))
    for rule in rules:
        ok = True
        for key, (op, val) in rule.get("when", {}).items():
            if not CMP[op](named[key], val):
                ok = False
                break
        if ok:
            return rule["state"]
    return default


# ---------------------------------------------------------------------------
# union area of axis-aligned rectangles
# ---------------------------------------------------------------------------

def union_area(boxes):
    """Area covered by at least one box. Overlap is counted ONCE.

    This exists because the first version of the ink-coverage check summed each
    element's intersection with the zone separately. On any film whose picture is
    full-frame video the elements stack, so coverage came out at 212% and 241% on
    hf67 and the floor could never fail: the check that is supposed to catch a
    void was structurally incapable of firing. Summing areas is not measuring
    coverage.

    Exact, by sweeping x slabs between every distinct edge and merging the y
    intervals of the boxes that span each slab. Element counts here are in the
    low hundreds, so the O(n^2) worst case is irrelevant and being exact is worth
    more than being clever.
    """
    boxes = [b for b in boxes if b[2] > b[0] and b[3] > b[1]]
    if not boxes:
        return 0.0
    xs = sorted({b[0] for b in boxes} | {b[2] for b in boxes})
    total = 0.0
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        dx = x1 - x0
        if dx <= 0:
            continue
        spans = sorted((b[1], b[3]) for b in boxes if b[0] <= x0 and b[2] >= x1)
        if not spans:
            continue
        covered, cy0, cy1 = 0.0, spans[0][0], spans[0][1]
        for y0, y1 in spans[1:]:
            if y0 > cy1:                 # gap, bank the run and start a new one
                covered += cy1 - cy0
                cy0, cy1 = y0, y1
            elif y1 > cy1:
                cy1 = y1
        covered += cy1 - cy0
        total += dx * covered
    return total


# ---------------------------------------------------------------------------
# contrast over video: bright-pixel fraction, never the mean
# ---------------------------------------------------------------------------

def bright_fraction(img, rect, thresh):
    """Fraction of pixels in rect brighter than `thresh`.

    The MEAN is the wrong statistic and this is the whole point of the check:
    white type on a black screen averages dark while still colliding badly. One
    title measured a mean that rated it fine and a bright-fraction of 59.6%,
    and it was unreadable in the render.
    """
    x0, y0, x1, y1 = [int(round(v)) for v in rect]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    crop = img.crop((x0, y0, x1, y1)).convert("L")
    hist = crop.histogram()
    n = sum(hist)
    if not n:
        return None
    return sum(hist[int(thresh) + 1:]) / float(n)


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------

def run(cfg, verbose, ids_path=None):
    problems = []
    coverage = {"beats": 0, "elements": 0, "texts": 0, "hittests": 0,
                "nullhits": 0, "contrast_measured": 0, "states": {},
                "videos": 0, "imgs": 0, "timed": 0, "unmanaged": 0,
                "unmeasured": 0, "contrast_skipped": 0}
    allow = cfg.get("allow") or []
    allow_hits = [0] * len(allow)

    problems += check_splice(cfg, ids_path)

    missing, missing_dirs = check_assets(cfg)
    for d in missing_dirs:
        problems.append(("ASSETDIR", 0.0, "directory does not exist: %s/" % d))
    for m in missing:
        problems.append(("ASSET", 0.0, "referenced but not on disk: %s" % m))

    Image = None
    if cfg["contrast"].get("enabled"):
        try:
            from PIL import Image as _I
            Image = _I
        except ImportError:
            # A silently skipped check is exactly the scope hole this file
            # exists to prevent, so say it loudly and fail the run.
            problems.append(("CONTRA", 0.0,
                             "Pillow is not installed, the contrast-over-video check DID NOT RUN. "
                             "pip install pillow, or set contrast.enabled=false and say why."))

    doc = "file://" + os.path.join(cfg["project"], cfg["document"])
    bands = cfg["bands"]
    shot = os.path.join(cfg["project"], ".guard-frame.png")

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": cfg["stage_w"], "height": cfg["stage_h"]},
                            device_scale_factor=1)
        pg = ctx.new_page()
        # A dead page is a Playwright check. Everything below measures a page
        # that threw on load as if it were composed correctly.
        errors = []
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
        pg.wait_for_timeout(2000)

        for e in errors[:8]:
            problems.append(("PAGEERR", 0.0, e[:160]))

        # Every stylesheet the document actually loads must be covered by the
        # staleness hash, and must have parsed a nonzero rule count.
        declared = cfg.get("stylesheets")
        for s in pg.evaluate(SHEETS):
            if s["rules"] == 0:
                problems.append(("CSSDROP", 0.0,
                                 "%s parsed 0 rules. One malformed comment drops every rule after "
                                 "it and lint, validate and inspect all pass." % s["href"]))
            if declared is not None and s["href"] != "<inline>" and s["href"] not in declared:
                problems.append(("PICHASH", 0.0,
                                 "%s is loaded but is not in the staleness hash list. A CSS fix in "
                                 "an unhashed sheet invalidates nothing and ships unapplied." % s["href"]))

        for t in cfg["beats"]:
            pcfg = {"t": t, "timeline": cfg["timeline"], "stage_id": cfg["stage_id"],
                    "stage_w": cfg["stage_w"], "caption_replay": cfg.get("caption_replay"),
                    "face_el": (cfg.get("face") or {}).get("element"),
                    "root_id": cfg["root_id"],
                    "apply_clip_schedule": cfg["apply_clip_schedule"],
                    "managed_tags": cfg["managed_tags"]}
            try:
                data = pg.evaluate(PROBE, pcfg)
            except Exception as ex:
                # A gate that dies is a gate that did not run. Report the beat
                # as unmeasured and keep going, rather than exiting with a
                # traceback that says nothing about the other 40 beats. The
                # throw is usually the COMPOSITION's own code, not this probe.
                coverage["unmeasured"] += 1
                problems.append(("PROBEFAIL", t, "the probe threw, this beat was NOT measured: %s"
                                 % str(ex).splitlines()[0][:120]))
                continue
            els = data["els"]
            state = face_state(cfg, data["faceClip"]) if cfg.get("face") else None
            srules = (cfg.get("states") or {}).get(state or "", {})
            coverage["beats"] += 1
            coverage["elements"] += len(els)
            if state:
                coverage["states"][state] = coverage["states"].get(state, 0) + 1

            page_img = None
            if data.get("covered") and cfg["contrast"].get("enabled"):
                # counted, not silent: a skipped check that nobody sees is the
                # scope hole this file exists to prevent
                coverage["contrast_skipped"] += 1
            if Image is not None and cfg["contrast"].get("enabled") and not data.get("covered"):
                pg.locator("#" + cfg["stage_id"]).screenshot(path=shot)
                page_img = Image.open(shot)

            # ---- video windows -------------------------------------------
            for v in data.get("vids", []):
                coverage["videos"] += 1
                if not v["painted"]:
                    continue
                if t < v["s"] - 1e-6 or t > v["s"] + v["d"] + 1e-6:
                    problems.append(("VIDWIN", t,
                                     "<video %s> paints at %.3f but its window is %.3f to %.3f, "
                                     "it renders dead grey" % (v["id"], t, v["s"], v["s"] + v["d"])))
            painted = [v["id"] for v in data.get("vids", []) if v["painted"]]
            expect = srules.get("videos_painting")
            if expect is not None and sorted(painted) != sorted(expect):
                problems.append(("VIDSET", t, "in state %s the painting videos are %s, expected %s"
                                 % (state, painted, expect)))

            # ---- the presenter whitelist ---------------------------------
            # A whitelist, not a blacklist. A missing window costs a beat of
            # face; a missing blacklist entry ships the defect.
            wins = cfg.get("face_windows")
            if wins is not None and state and state != (cfg.get("face") or {}).get("off_state", "off"):
                if not any(w[0] - 1e-6 <= t <= w[1] + 1e-6 for w in wins):
                    problems.append(("FACEWIN", t,
                                     "the face paints in state %s at t=%.3f, outside every declared "
                                     "safe window" % (state, t)))

            # ---- a timed element that paints OUTSIDE its own window ------
            coverage["timed"] = data.get("timed", 0)
            coverage["unmanaged"] = data.get("unmanaged", 0)
            for lk in data.get("leaks", []):
                nm = lk["id"] or (lk["tag"] + "." + lk["cls"])[:28]
                why = ("the framework gives visibility control to %s only, so this tag is never "
                       "hidden" % "/".join(cfg["managed_tags"])) if not lk["managed"] else \
                      "it is a managed tag, so something is overriding the schedule"
                problems.append(("TIMEDLEAK", t,
                                 "%s paints at %.3f but its window is %.3f to %.3f: %s"
                                 % (nm, t, lk["s"], lk["s"] + lk["d"], why)))

            # ---- broken images -------------------------------------------
            for im in data.get("imgs", []):
                coverage["imgs"] += 1
                if im["natw"] == 0:
                    problems.append(("IMG0", t, "%s loaded naturalWidth 0, the card paints and its "
                                     "picture does not: %s" % (im["id"] or "<img>", im["src"])))

            texts = [e for e in els if e["text"]]
            coverage["texts"] += len(texts)

            for e in els:
                x0, y0 = e["x"], e["y"]
                x1, y1 = e["x"] + e["w"], e["y"] + e["h"]
                nm = e["id"] or (e["tag"] + "." + e["cls"])[:28]
                isText = bool(e["text"])
                tail = e["text"][:26]

                if isText:
                    if y0 < bands["top_text"]:
                        problems.append(("TOP", t, "%s text at y%.0f < %d, %s" % (nm, y0, bands["top_text"], tail)))
                    if y1 > bands["band_y"]:
                        problems.append(("BAND", t, "%s text to y%.0f > %d, %s" % (nm, y1, bands["band_y"], tail)))
                    if x0 < bands["left_pad"]:
                        problems.append(("LEFT", t, "%s text at x%.0f < %d, %s" % (nm, x0, bands["left_pad"], tail)))
                    if x1 > bands["rail_x"] and y1 > bands["rail_y0"] and y0 < bands["rail_y1"]:
                        problems.append(("RAIL", t, "%s text to x%.0f in the rail, %s" % (nm, x1, tail)))

                # ---- state rules, per face state -------------------------
                crown = srules.get("text_must_clear_y")
                if isText and crown is not None and y1 > crown:
                    problems.append(("ONCROWN", t, "%s runs to y%.0f, past the worst-case crown at %d, %s"
                                     % (nm, y1, crown, tail)))
                for rect in srules.get("text_forbidden_rects", []):
                    if isText and x1 > rect[0] and x0 < rect[2] and y1 > rect[1] and y0 < rect[3]:
                        problems.append(("ONFACE", t, "%s overlaps the reserved face rect %s, %s"
                                         % (nm, rect, tail)))
                seam = srules.get("text_must_stay_left_of_x")
                if isText and seam is not None and x1 > seam:
                    problems.append(("ONSPLIT", t, "%s crosses the split seam at x%.0f > %d, %s"
                                     % (nm, x1, seam, tail)))

                # ---- position is not visibility --------------------------
                if cfg["paint"].get("enabled") and isText:
                    coverage["hittests"] += 1
                    if e["hit"] == "blocked":
                        problems.append(("OCCLUDED", t, "%s is positioned correctly but %s paints over it, %s"
                                         % (nm, e["over"], tail)))
                    elif e["hit"] == "null":
                        coverage["nullhits"] += 1
                        problems.append(("NOPROBE", t,
                                         "%s returned null from every hit test, so it was NOT checked. "
                                         "null is not a pass." % nm))

                # ---- contrast over the picture ---------------------------
                if (page_img is not None and isText and not e["ground"]
                        and e["w"] * e["h"] >= cfg["contrast"]["min_area"]):
                    frac = bright_fraction(page_img, (x0, y0, x1, y1), cfg["contrast"]["bright"])
                    if frac is not None:
                        coverage["contrast_measured"] += 1
                        lim = cfg["contrast"]["max_bright_frac"]
                        if e["lum"] > 0.6 and frac > lim:
                            problems.append(("CONTRA", t, "%s is light type with %.1f%% of its ground "
                                             "brighter than %d, %s" % (nm, frac * 100, cfg["contrast"]["bright"], tail)))
                        if e["lum"] < 0.35 and (1 - frac) > lim:
                            problems.append(("CONTRA", t, "%s is dark type with %.1f%% of its ground "
                                             "darker than %d, %s" % (nm, (1 - frac) * 100, cfg["contrast"]["bright"], tail)))

            # ---- text on text, excluding ancestry ------------------------
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    a, c = texts[i], texts[j]
                    if a["path"][0] in c["path"] or c["path"][0] in a["path"]:
                        continue
                    if a.get("rot") or c.get("rot"):
                        continue
                    ox = min(a["x"] + a["w"], c["x"] + c["w"]) - max(a["x"], c["x"])
                    oy = min(a["y"] + a["h"], c["y"] + c["h"]) - max(a["y"], c["y"])
                    if ox > 6 and oy > 6:
                        area = ox * oy
                        small = min(a["w"] * a["h"], c["w"] * c["h"])
                        if area > 0.22 * small:
                            problems.append(("TXTTXT", t, "%s '%s' over %s '%s' (%.0f px2)"
                                             % (a["id"] or a["tag"], a["text"][:18],
                                                c["id"] or c["tag"], c["text"][:18], area)))

            # ---- a void is a defect --------------------------------------
            # One element over blank paper passes lint, validate and every
            # safe-zone rule and still reads as a hole (vid61). Ink coverage is
            # the only thing that catches it. The zone is per state, because
            # the graphics own a different rectangle when the face is carded.
            zone = srules.get("ink_zone") or (cfg.get("void") or {}).get("zone")
            if zone:
                floor = srules.get("min_ink_frac", (cfg.get("void") or {}).get("min_ink_frac", 0.14))
                after = (cfg.get("void") or {}).get("after_t", 0.0)
                boxes = []
                for e in els:
                    ox0, oy0 = max(e["x"], zone[0]), max(e["y"], zone[1])
                    ox1, oy1 = min(e["x"] + e["w"], zone[2]), min(e["y"] + e["h"], zone[3])
                    if ox1 > ox0 and oy1 > oy0:
                        boxes.append((ox0, oy0, ox1, oy1))
                ink = union_area(boxes)
                frac = ink / float((zone[2] - zone[0]) * (zone[3] - zone[1]))
                if t > after and frac < floor:
                    problems.append(("VOID", t, "graphics zone only %.1f%% covered in state %s"
                                     % (frac * 100, state)))

            if verbose:
                print("  t=%7.3f  state=%-6s els=%3d text=%2d vids=%s"
                      % (t, str(state), len(els), len(texts), painted))

        b.close()
    if os.path.exists(shot):
        os.remove(shot)

    # ---- allowlist, applied and audited ----------------------------------
    kept = []
    for kind, t, msg in problems:
        hit = False
        for i, a in enumerate(allow):
            if a.get("kind") and a["kind"] != kind:
                continue
            if a.get("match") and a["match"] not in msg:
                continue
            if "t0" in a and not (a["t0"] - 1e-6 <= t <= a.get("t1", a["t0"]) + 1e-6):
                continue
            allow_hits[i] += 1
            hit = True
            break
        if not hit:
            kept.append((kind, t, msg))

    # An allowlist entry that matches nothing is worse than no entry: it reads
    # as considered while handling nothing. One inherited entry blanket-exempted
    # a whole scene and hid 15.8s of genuine staleness, while its sibling
    # pointed past the end of a chunk and matched nothing at all. Re-derive
    # exemptions per film, from measurement.
    for i, a in enumerate(allow):
        if allow_hits[i] == 0:
            kept.append(("ALLOWDEAD", 0.0, "allow entry %s matched nothing this run: %s"
                         % (json.dumps(a), a.get("reason", "no reason given"))))

    seen, uniq = set(), []
    for kind, t, msg in kept:
        k = (kind, msg)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((kind, t, msg))

    # ---- coverage, always printed ----------------------------------------
    # A green run and a gate that silently did nothing produce the identical
    # console output. Print what was measured, not just the verdict.
    print("coverage: %d beats, %d painting elements, %d with text, %d hit tests "
          "(%d returned null), %d contrast measurements, %d <video> reads, %d <img> reads, "
          "%d timed elements (%d of them unmanaged by the framework)"
          % (coverage["beats"], coverage["elements"], coverage["texts"],
             coverage["hittests"], coverage["nullhits"], coverage["contrast_measured"],
             coverage["videos"], coverage["imgs"], coverage["timed"], coverage["unmanaged"]))
    if coverage["states"]:
        print("face states seen: " + ", ".join("%s x%d" % kv for kv in sorted(coverage["states"].items())))
    if coverage["contrast_skipped"]:
        print("contrast skipped on %d beat(s): a full-frame cover was up, which is a wipe "
              "mid-travel, not a ground." % coverage["contrast_skipped"])
    if coverage["unmeasured"]:
        print("WARNING: %d of %d beats were NOT measured, the probe threw on them."
              % (coverage["unmeasured"], len(cfg["beats"])))
    if coverage["texts"] == 0:
        print("WARNING: not one element carried text. Either the caption replay is "
              "misconfigured or this gate measured nothing.")

    if not uniq:
        print("PASS: assets resolve, everything measured paints, bands clear, no text on text, "
              "no void beats")
        return 0
    print("%d problem(s):" % len(uniq))
    for kind, t, msg in uniq:
        print("  [%-9s] t=%7.3f  %s" % (kind, t, msg))
    return 1


def main():
    ap = argparse.ArgumentParser(description="pre-render gate: measure what actually paints")
    ap.add_argument("config", help="path to the film's guard JSON")
    ap.add_argument("--project", help="override the project dir holding index.html")
    ap.add_argument("--beats", help="comma-separated beats, overrides the config")
    ap.add_argument("-v", "--verbose", action="store_true", help="print a line per beat")
    ap.add_argument("--ids", help="element-id baseline JSON. Written on first run, diffed after. "
                                  "Run it before and after any splice.")
    a = ap.parse_args()
    return run(load_config(a.config, a), a.verbose, a.ids)


if __name__ == "__main__":
    sys.exit(main())
