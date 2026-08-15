"""derive_config.py, the bootstrapper for `guard.json`.

`guard.py` is the best gate in this repo and it needs a hand-authored config per
film. That config is where gates go to die. A new operator writes one that passes
trivially, or writes none at all, and the gate becomes theatre: the console output
of a green run and of a gate that measured nothing are identical.

So this script writes the config FOR the operator, from the composition itself,
and marks with a literal `TODO` string every value it is not entitled to invent.
`guard.py` refuses to run while a `TODO` is still in the file. A half-finished
config cannot masquerade as a passing gate. That refusal is the point of this
script, not a side effect of it.

WHAT IS DERIVED, AND FROM WHAT
------------------------------
  project, document      the directory you point this at
  timeline               `window.__timelines = { KEY: tl }`, cross-checked with
                         the root's `data-composition-id`
  stage_id, stage_w/h    the `#stage` rule's own `width`/`height`, cross-checked
                         with the root's `data-width`/`data-height`. A 2160x3840
                         root over a 1080x1920 stage is `transform:scale(2)`, and
                         guard.py measures in the UNSCALED 1080x1920 space.
  beats                  scene boundaries: `data-start` on picture elements, the
                         composition's own beat map (`var B = {s0:0, s1:1.4 ...}`)
                         and every call of its face `cut()` function, with symbol
                         times resolved through that map. Any gap longer than `--gap` seconds
                         gets one interior sample, because a beat that holds for
                         two seconds and is only measured at its two edges is a
                         beat nobody looked at. With a transcript, boundaries and
                         interior samples both snap to the nearest word onset:
                         scene boundaries land on word onsets in this house, so
                         the onset is the frame worth measuring.
  asset_prefix           the commonest directory prefix of the document's `src`
  stylesheets            every `<link rel=stylesheet>`. All-inline CSS derives
                         `[]`, which is correct: guard.py never PICHASHes an
                         inline sheet.
  caption_replay         the published cue array and the element the caption
                         engine writes into
  the inventories        elements by id, `<video>` windows, face states and their
                         observed clip-path strings. These go in `_`-prefixed
                         comment keys: guard.py ignores them, and they are the
                         raw material for the TODOs below.

WHAT IS NOT DERIVED, AND WHY GUESSING IS WORSE THAN A TODO
----------------------------------------------------------
  ink_zone / min_ink_frac   the rectangle graphics are supposed to OWN, and the
        fraction of it that must be covered. Nothing in the document says which
        part of the frame is meant to carry graphics: the composition looks the
        same to a parser whether a rect is the design or a hole in it. A derived
        zone would be the bounding box of whatever happens to be there, so it
        would pass by construction on the exact beat it exists to fail (vid61
        shipped one element over blank paper past lint, validate and every
        safe-zone rule).
  face rules / crown        which inset means `card` and which means `split` is
        readable off the FACE literal, but the CROWN is not: `text_must_clear_y`
        is a measurement of THE PRESENTER'S HEAD in THIS take, from Vision over
        the frames
        (tools/vision/, playbooks/face-geometry.md). vid67's 660 is the worst
        crown across 176 samples, not a layout constant. A guessed crown is a
        gate that passes text printed on the presenter's forehead.
  text_forbidden_rects      same class: the rect the presenter's face occupies
        in a state.
  face_windows              a whitelist of the windows the presenter's face MAY
        paint in.
        Derived from the composition it would list exactly the windows the
        composition already has, so it could never disagree with it.
  videos_painting           per state. Derivable only as "what happens to paint",
        which again cannot disagree with the build.

Usage
-----
    python3 tools/gates/derive_config.py <project-dir>
    python3 tools/gates/derive_config.py <project-dir> -o /tmp/guard.json
    python3 tools/gates/derive_config.py <project-dir> --print
    python3 tools/gates/derive_config.py <project-dir> --transcript transcript.json

Then open the file, work the TODOs top to bottom, and run `guard.py`. The
walkthrough with a real before and after is in tools/gates/README.md.
"""
import argparse
import json
import os
import re
import sys
from collections import OrderedDict

TODO = "TODO"


# ---------------------------------------------------------------------------
# reading the document
# ---------------------------------------------------------------------------

def read_doc(project, document):
    path = os.path.join(project, document)
    if not os.path.isfile(path):
        sys.exit("no %s in %s. Point this at the directory holding the composition."
                 % (document, project))
    return open(path, encoding="utf-8").read()


def scripts_of(html):
    """The inline script text only. A CDN <script src> has no body to read."""
    return "\n".join(re.findall(r"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>",
                                html, re.S | re.I))


def styles_of(html):
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


def markup_of(html):
    """The document with every script, style and comment removed.

    Tag inventories must read the MARKUP and nothing else. A CSS comment in
    hf67 reads `Seventeen separate <video> elements stalled the capture engine`,
    and a plain scan counted 4 videos in a film that has 2. An inventory that
    over-counts is not a harmless inventory: `videos_painting` is compared as a
    sorted set, so one phantom id fails every beat.
    """
    out = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    out = re.sub(r"<style\b.*?</style>", " ", out, flags=re.S | re.I)
    out = re.sub(r"<!--.*?-->", " ", out, flags=re.S)
    return out


def attr(tag, name):
    m = re.search(r'\s%s="([^"]*)"' % re.escape(name), tag)
    return m.group(1) if m else None


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# the root, the stage, the timeline
# ---------------------------------------------------------------------------

def find_root(markup):
    """The composition root carries data-composition-id and the frame size."""
    for m in re.finditer(r"<div\b[^>]*>", markup):
        tag = m.group(0)
        if "data-composition-id" in tag:
            return {
                "id": attr(tag, "id") or "root",
                "composition_id": attr(tag, "data-composition-id"),
                "width": num(attr(tag, "data-width")),
                "height": num(attr(tag, "data-height")),
                "duration": num(attr(tag, "data-duration")),
                "fps": num(attr(tag, "data-fps"), 30.0),
            }
    return None


def find_stage(css, root):
    """Stage id and its UNSCALED size.

    guard.py measures in stage space and divides out the scale itself, so the
    numbers that go in the config are the stage rule's own, never the root's.
    A 2160x3840 root over a 1080x1920 stage means transform:scale(2), which is
    the house default and is exactly why this is worth cross-checking: a config
    written with the root's numbers puts every band at half its real height.
    """
    best = None
    for m in re.finditer(r"#([A-Za-z][\w-]*)\s*\{([^}]*)\}", css):
        sid, body = m.group(1), m.group(2)
        w = re.search(r"(?<![\w-])width\s*:\s*(\d+(?:\.\d+)?)px", body)
        h = re.search(r"(?<![\w-])height\s*:\s*(\d+(?:\.\d+)?)px", body)
        if not (w and h):
            continue
        cand = {"id": sid, "w": float(w.group(1)), "h": float(h.group(1)),
                "scaled": "scale(" in body}
        if sid == "stage":
            return cand
        if best is None or cand["w"] * cand["h"] > best["w"] * best["h"]:
            best = cand
    return best


def find_timeline(js, root):
    m = re.search(r"window\.__timelines\s*=\s*\{\s*([A-Za-z_$][\w$]*)\s*:", js)
    if m:
        return m.group(1), None
    m = re.search(r"window\.__timelines\s*=\s*\{\s*['\"]([^'\"]+)['\"]\s*:", js)
    if m:
        return m.group(1), None
    if root and root.get("composition_id"):
        return root["composition_id"], ("no window.__timelines assignment found, fell "
                                        "back to data-composition-id")
    return None, "no window.__timelines assignment and no data-composition-id"


# ---------------------------------------------------------------------------
# the face
# ---------------------------------------------------------------------------

def find_face(js):
    """The clip-path carrier, the state names, and the clip string per state.

    A composition in this house names its face states in one object literal and
    hard-cuts between them. Read the literal for the NAMES and the observed
    inset values; the rules that map an inset to a name stay a TODO, because the
    crown that hangs off each state is a measurement of the presenter's head,
    not of the CSS.
    """
    el = None
    m = re.search(r'put\(\s*"#([\w-]+)"\s*,\s*\{\s*clipPath', js)
    if not m:
        m = re.search(r'["\']#?([\w-]+)["\']\s*,\s*\{\s*clipPath', js)
    if m:
        el = m.group(1)

    states = OrderedDict()
    obj = re.search(r"(?:var|let|const)\s+\w*FACE\w*\s*=\s*\{(.*?)\n\s*\};", js, re.S)
    if obj:
        for sm in re.finditer(r"([A-Za-z_][\w]*)\s*:\s*\{[^{}]*clip\s*:\s*"
                              r"[\"']([^\"']+)[\"']", obj.group(1)):
            states[sm.group(1)] = sm.group(2)
    if not states:
        for sm in re.finditer(r"clip\s*:\s*[\"'](inset\([^\"']+\))[\"']", js):
            states["state%d" % (len(states) + 1)] = sm.group(1)
    return el, states


def inset_of(clip):
    return [float(x) for x in re.findall(r"(-?[\d.]+)px", clip or "")][:4]


# ---------------------------------------------------------------------------
# beats
# ---------------------------------------------------------------------------

def word_onsets(path):
    if not path or not os.path.isfile(path):
        return []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except (ValueError, OSError):
        return []
    out = []
    segs = d.get("segments") if isinstance(d, dict) else d
    for s in segs or []:
        for w in s.get("words", []) or []:
            t = w.get("start")
            if isinstance(t, (int, float)):
                out.append(float(t))
    return sorted(set(out))


def snap(t, onsets, tol):
    """Move t to the nearest word onset within tol, else leave it alone."""
    if not onsets:
        return t, False
    best = min(onsets, key=lambda o: abs(o - t))
    if abs(best - t) <= tol:
        return best, abs(best - t) > 1e-9
    return t, False


def beat_maps(js, duration):
    """The composition's own beat map, as a symbol table.

    hf67 writes its cut times as literals. hf66 and hf64 write
    `var B = { s0:0.000, s1:1.400, ... end:26.515 };` and then `faceSet("card",
    B.s1)`, so a literal-only scan finds ONE cut on a film with sixteen scenes
    and derives a beat list that skips the entire film. The map is recognised by
    its shape, not by its name: at least four numeric pairs, nondecreasing, all
    inside [0, duration]. That signature is a timeline and very little else is.
    """
    out = {}
    for m in re.finditer(r"(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=\s*\{([^{}]*)\}", js):
        name, body = m.group(1), m.group(2)
        pairs = re.findall(r"([A-Za-z_$][\w$]*)\s*:\s*(-?\d+(?:\.\d+)?)\s*(?:,|$)", body)
        if len(pairs) < 4:
            continue
        if len(pairs) != len([p for p in re.split(r",", body) if p.strip()]):
            continue
        vals = [float(v) for _, v in pairs]
        if any(b < a for a, b in zip(vals, vals[1:])):
            continue
        if duration and (vals[0] < -1e-6 or vals[-1] > duration + 1e-6):
            continue
        out[name] = OrderedDict((k, float(v)) for k, v in pairs)
    return out


def cut_call_times(js, state_names, maps):
    """Calls of the composition's own state-cut function, times resolved.

    hf67 writes `cut("split", 3.240)`, hf66 writes `faceSet("card", B.s1)`. The
    function name is not a constant across films, so it is found by looking for
    any call whose first argument is one of the FACE literal's own state names,
    and the time argument is resolved through the beat map when it is a symbol.
    """
    if not state_names:
        return [], None
    names = "|".join(re.escape(n) for n in state_names)
    pat = re.compile(r"\b([A-Za-z_$][\w$]*)\(\s*[\"'](%s)[\"']\s*,\s*"
                     r"([A-Za-z_$][\w$]*\.[A-Za-z_$][\w$]*|-?\d+(?:\.\d+)?)\s*\)" % names)
    by_fn = {}
    for m in pat.finditer(js):
        raw = m.group(3)
        if "." in raw and not raw[0].isdigit():
            obj, key = raw.split(".", 1)
            if obj not in maps or key not in maps[obj]:
                continue
            t = maps[obj][key]
        else:
            t = float(raw)
        by_fn.setdefault(m.group(1), []).append(t)
    if not by_fn:
        return [], None
    fn = max(by_fn, key=lambda k: len(by_fn[k]))
    return sorted(set(by_fn[fn])), fn


def data_start_times(markup, root_id):
    """data-start on picture elements. <audio> is excluded deliberately: an sfx
    cue is a sound, not a scene boundary, and a film carries forty of them."""
    out = []
    for m in re.finditer(r"<(div|video|img|svg|canvas)\b[^>]*>", markup, re.I):
        tag = m.group(0)
        if attr(tag, "id") == root_id:
            continue
        s = num(attr(tag, "data-start"))
        if s is not None:
            out.append(s)
    return sorted(set(out))


def derive_beats(markup, js, root, states, onsets, gap, snap_tol):
    dur = (root or {}).get("duration") or 0.0
    fps = (root or {}).get("fps") or 30.0
    maps = beat_maps(js, dur)
    cuts, fn = cut_call_times(js, list(states), maps)
    starts = data_start_times(markup, (root or {}).get("id"))
    mapped = sorted(set(v for m in maps.values() for v in m.values()))
    raw = sorted(set([0.0] + cuts + starts + mapped))
    raw = [t for t in raw if -1e-6 <= t < dur - 1e-6] if dur else raw

    snapped, moved = [], 0
    for t in raw:
        s, did = snap(t, onsets, snap_tol)
        moved += 1 if did else 0
        snapped.append(round(s, 3))
    snapped = sorted(set(snapped))

    # An interior sample per long hold. A beat measured only at its two edges is
    # a beat nobody looked at: the vid62 splice that swallowed a whole scene
    # survived three delivered versions because every contact sheet sampled
    # around it and never inside it.
    edges = list(snapped) + ([round(dur, 3)] if dur else [])
    interior = []
    for a, b in zip(edges, edges[1:]):
        if b - a > gap:
            mid, _ = snap((a + b) / 2.0, onsets, (b - a) / 2.0 - 0.05)
            mid = round(mid, 3)
            if a + 0.05 < mid < b - 0.05:
                interior.append(mid)

    # The last frame is a frame. Land four frames short of the end, because the
    # exact duration is one tick past the last painted frame.
    tail = round(dur - 4.0 / fps, 3) if dur else None
    beats = sorted(set(snapped + interior + ([tail] if tail else [])))
    return beats, {"cut_fn": fn, "cuts": len(cuts), "data_starts": len(starts),
                   "interior": len(interior), "snapped": moved,
                   "onsets": len(onsets), "maps": list(maps), "mapped": len(mapped)}


# ---------------------------------------------------------------------------
# inventories
# ---------------------------------------------------------------------------

def video_inventory(markup):
    out = []
    for m in re.finditer(r"<video\b[^>]*>", markup, re.I):
        tag = m.group(0)
        out.append({"id": attr(tag, "id") or attr(tag, "src") or "video",
                    "src": attr(tag, "src"),
                    "start": num(attr(tag, "data-start"), 0.0),
                    "duration": num(attr(tag, "data-duration"), 0.0)})
    return out


def element_ids(markup):
    return sorted(set(re.findall(r'\sid="([^"]+)"', markup)))


def stylesheet_list(markup):
    out = []
    for m in re.finditer(r"<link\b[^>]*>", markup, re.I):
        tag = m.group(0)
        if "stylesheet" in (attr(tag, "rel") or ""):
            href = attr(tag, "href") or ""
            out.append(href.split("/")[-1])
    return out


def asset_prefix(markup):
    pre = {}
    for m in re.finditer(r'(?:src|href)="([^"]+/)[^"/]+"', markup):
        p = m.group(1)
        if p.startswith(("http:", "https:", "//", "data:")):
            continue
        pre[p.split("/")[0] + "/"] = pre.get(p.split("/")[0] + "/", 0) + 1
    if not pre:
        return "assets/"
    return max(pre, key=lambda k: pre[k])


def find_caption_replay(js, html):
    """The published cue array and the element the engine writes into.

    `tl.time(t, false)` suppresses events, so a `tl.call()` caption engine writes
    NOTHING for a gate. Without a replay the caption element carries no text and
    every caption rule in guard.py measures nothing while reporting a clean run.
    The composition has to publish its array on `window` for this to be
    derivable at all, which is itself the fix.
    """
    # `window.__timelines` is published by every composition in this house and is
    # not a cue array. Take a published name only when the thing it publishes is
    # declared as an ARRAY, which is what the probe iterates.
    arr = None
    for m in re.finditer(r"window\.(__[A-Za-z_]\w*)\s*=\s*([A-Za-z_$][\w$]*)\s*;", js):
        name, rhs = m.group(1), m.group(2)
        if name == "__timelines":
            continue
        if re.search(r"(?:var|let|const)\s+%s\s*=\s*\[" % re.escape(rhs), js):
            arr = name
            break
    target = None
    tm = re.search(r'getElementById\(\s*["\']([\w-]+)["\']\s*\)[\s\S]{0,400}?'
                   r'\.textContent\s*=', js)
    if tm:
        target = tm.group(1)
    else:
        tm = re.search(r'["\']#([\w-]+)["\'][\s\S]{0,120}?\.textContent\s*=', js)
        if tm:
            target = tm.group(1)
    has_engine = bool(re.search(r"tl\.call\(", js)) or bool(re.search(r"\bCAPS\b", js))
    return arr, target, has_engine


# ---------------------------------------------------------------------------
# building the config
# ---------------------------------------------------------------------------

def build(project, document, transcript, gap, snap_tol):
    html = read_doc(project, document)
    js, css, markup = scripts_of(html), styles_of(html), markup_of(html)
    root = find_root(markup)
    stage = find_stage(css, root) or {"id": "stage", "w": 1080.0, "h": 1920.0}
    timeline, tl_note = find_timeline(js, root)
    face_el, face_states = find_face(js)
    onsets = word_onsets(transcript)
    beats, bstat = derive_beats(markup, js, root, face_states, onsets, gap, snap_tol)
    vids = video_inventory(markup)
    sheets = stylesheet_list(markup)
    caps_arr, caps_target, has_engine = find_caption_replay(js, markup)

    notes = []
    if tl_note:
        notes.append(tl_note)
    if root and stage and root.get("width") and stage["w"]:
        k = root["width"] / stage["w"]
        if abs(k - round(k)) < 0.01 and round(k) != 1:
            notes.append("root is %dx%d over a %dx%d stage, so the stage is "
                         "transform:scale(%d). stage_w/stage_h below are the UNSCALED "
                         "numbers, which is what guard.py measures in."
                         % (root["width"], root["height"], stage["w"], stage["h"], round(k)))
    if not onsets:
        notes.append("no transcript word onsets, so beats sit on the composition's own "
                     "boundary numbers and interior samples are plain midpoints. Pass "
                     "--transcript to snap them to speech.")

    cfg = OrderedDict()
    cfg["_generated_by"] = ("tools/gates/derive_config.py. Every TODO below is a "
                            "measurement this script is not entitled to invent. "
                            "guard.py REFUSES to run while one is left in the file.")
    if notes:
        cfg["_notes"] = notes

    cfg["project"] = "."
    cfg["_project"] = ("relative to this file's own directory. Keep the config next to "
                       "index.html, or pass --project on the command line.")
    cfg["document"] = document
    cfg["timeline"] = timeline or TODO
    if not timeline:
        cfg["_timeline_TODO"] = ("the key in window.__timelines. The composition must "
                                 "expose it: `window.__timelines = { vid67: tl };`. "
                                 "Without it guard.py cannot seek and measures nothing.")
    cfg["stage_id"] = stage["id"]
    cfg["stage_w"] = int(stage["w"])
    cfg["stage_h"] = int(stage["h"])
    cfg["asset_prefix"] = asset_prefix(markup)

    cfg["_beats"] = ("%d beats: %d state cuts%s, %d picture data-starts, %d times from the "
                     "composition's own beat map%s, %d interior samples for holds longer "
                     "than %.2fs, and the tail frame. %d were snapped to a word onset. ADD "
                     "any frame inside a beat where something lands: an entrance that "
                     "finishes, a number that changes, a card that collapses."
                     % (len(beats), bstat["cuts"],
                        (" via %s()" % bstat["cut_fn"]) if bstat["cut_fn"] else "",
                        bstat["data_starts"], bstat["mapped"],
                        (" " + "/".join(bstat["maps"])) if bstat["maps"] else "",
                        bstat["interior"], gap, bstat["snapped"]))
    cfg["beats"] = beats

    cfg["_bands"] = ("the 2026 Instagram numbers from docs/02-safe-zones.md, in stage "
                     "space. These are the only inherited numbers in this file and they "
                     "are a platform spec, not a measurement of this film.")
    cfg["bands"] = OrderedDict([("top_text", 150), ("band_y", 1600), ("rail_x", 960),
                                ("rail_y0", 900), ("rail_y1", 1600), ("left_pad", 60)])

    if caps_arr and caps_target:
        cfg["_caption_replay"] = ("found window.%s and an element the engine writes into. "
                                  "Verify the target id: if guard.py's coverage line says "
                                  "`0 with text`, this is wrong and every caption rule is "
                                  "inert." % caps_arr)
        cfg["caption_replay"] = OrderedDict([("array", caps_arr), ("target", caps_target)])
    elif has_engine:
        cfg["_caption_replay_TODO"] = (
            "this build has a tl.call() caption engine and publishes no cue array, so "
            "the gate cannot replay it. tl.time(t, false) suppresses events: the caption "
            "element carries NO TEXT for the probe, isText is false, and the crown, band, "
            "rail, text-on-text and contrast rules all silently measure nothing. Fix the "
            "COMPOSITION first, one line: `window.__CAPS = CAPS;`, then set "
            "{\"array\": \"__CAPS\", \"target\": \"<the caption element id>\"}.")
        cfg["caption_replay"] = TODO

    if face_el or face_states:
        obs = OrderedDict()
        for name, clip in face_states.items():
            ins = inset_of(clip)
            obs[name] = {"clip": clip,
                         "inset_top_right_bottom_left": ins}
        cfg["_face_observed"] = {
            "element": face_el,
            "states": obs,
            "how_to_write_the_rules": (
                "one rule per state, most specific FIRST, keyed on top/right/bottom/left "
                "and never on a position in a list: Chromium collapses "
                "inset(700px 0px 0px 0px) to inset(700px 0px 0px) when left equals right, "
                "and a guard that assumed four numbers reported the wrong state for a "
                "whole film. Write thresholds that sit BETWEEN the observed values above, "
                "not on them, so a one-pixel rounding does not flip the state.")}
        cfg["face"] = OrderedDict([
            ("element", face_el or TODO),
            ("default", TODO),
            ("off_state", TODO),
            ("rules", TODO)])
        cfg["_face_TODO"] = (
            "`rules` maps the clip-path inset to a state NAME, `default` is the state when "
            "no rule matches, `off_state` names the state where the presenter's face is not "
            "on screen "
            "at all (guard.py skips the face whitelist there). The observed insets are in "
            "_face_observed above. Form: "
            "{\"state\": \"split\", \"when\": {\"top\": [\">=\", 610]}}.")

    states = OrderedDict()
    for name in (face_states or {"default": None}):
        states[name] = OrderedDict([
            ("_TODO", "fill or DELETE each key below. Deleting a key means this state has "
                      "no such constraint, which is a decision. Leaving a trivially wide "
                      "value is a gate that cannot fail."),
            ("text_must_clear_y", TODO),
            ("ink_zone", TODO),
            ("min_ink_frac", TODO),
            ("videos_painting", TODO)])
    cfg["states"] = states
    cfg["_states_TODO"] = {
        "text_must_clear_y": (
            "the WORST-CASE crown of the presenter's head in this state, in stage space: no "
            "text may run past it. It is a measurement of THE PRESENTER'S HEAD in THIS "
            "take, over every frame "
            "of the take, not a layout constant. Measure with tools/vision/ and "
            "playbooks/face-geometry.md, and measure the WINDOW the state covers, not the "
            "whole take: an 11-sample average missed the presenter leaning in at the CTA. A "
            "guessed crown is a gate that passes text printed on the presenter's "
            "forehead. vid67's is 660, "
            "which is 40px below its y620 seam and came off 176 Vision samples."),
        "text_forbidden_rects": (
            "add this key instead of a crown when the presenter's face occupies a RECT "
            "rather than a "
            "half of the frame, as in card mode. [[x0,y0,x1,y1], ...], stage space. Same "
            "rule: hit-test the real crop at the candidate numbers, do not model it."),
        "text_must_stay_left_of_x": (
            "the split seam, for a vertical split. Text crossing it lands on the "
            "presenter."),
        "ink_zone": (
            "[x0,y0,x1,y1], the rectangle the GRAPHICS are supposed to own in this state. "
            "This is the one value that cannot be derived even in principle: a parser "
            "cannot tell a rect that is the design from a rect that is a hole in it, and a "
            "zone derived from what happens to be on screen passes by construction on the "
            "beat it exists to fail. vid61 shipped a beat that was one element over blank "
            "paper past lint, validate and every safe-zone rule. DELETE this key for a "
            "state whose picture is full-frame video: ink is summed per element and "
            "overlapping elements double count, so a zone over the presenter's face "
            "measured 212.9% "
            "covered on vid67 and the floor can never fail. A key that cannot fail is "
            "worse than no key, because it reads as a check."),
        "min_ink_frac": (
            "the fraction of ink_zone that must be covered. 0.14 is the number this house "
            "uses. Raise it for a state whose zone is a dense panel; do not lower it to "
            "make a failing beat pass, that is the beat the check was built for."),
        "videos_painting": (
            "the exact set of <video> ids that must be painting in this state, sorted "
            "compared. The band track must show in SPLIT and be hidden in FULL and nothing "
            "structural checks that. The document's own <video> inventory is in "
            "_video_inventory below.")}

    cfg["_video_inventory"] = [
        OrderedDict([("id", v["id"]), ("src", v["src"]),
                     ("window", [v["start"], round((v["start"] or 0) + (v["duration"] or 0), 3)])])
        for v in vids]
    if vids:
        cfg["_video_inventory_note"] = (
            "a <video> painted outside its own [data-start, +data-duration] window renders "
            "DEAD GREY. Seven of nine dashboard placements shipped that way on the film "
            "whose brief was `more screen recordings`. guard.py checks the window itself; "
            "`videos_painting` per state is the half it cannot infer.")

    cfg["face_windows"] = TODO
    cfg["_face_windows_TODO"] = (
        "[[t0,t1], ...], the windows the presenter's face MAY paint in. A WHITELIST, "
        "deliberately: a "
        "gate that enumerates the known-bad spans cannot catch what its detector missed, "
        "and a gaze detector missed two real down-looks three times running on thresholds "
        "alone. A missing window costs a beat of face; a missing blacklist entry ships the "
        "defect. Derived from the composition this list would be exactly what the "
        "composition already does, so it could never disagree with it. Write it from the "
        "SHOT PLAN, or from watching the take. If the presenter's face is genuinely on "
        "screen for the "
        "whole film, say so with one window covering the duration and record WHY here.")

    cfg["void"] = OrderedDict([("after_t", 0.0), ("min_ink_frac", 0.14)])
    cfg["_void"] = ("after_t skips the hook, where a deliberately sparse frame is the "
                    "design. 0.0 checks everything, which is the strict setting; raise it "
                    "only past a hook you have looked at. This block is inert until at "
                    "least one state carries an ink_zone.")

    cfg["contrast"] = OrderedDict([("enabled", True), ("bright", 150),
                                   ("max_bright_frac", 0.35), ("min_area", 2500)])
    cfg["_contrast"] = ("bright-pixel FRACTION, never the mean: white type on a black "
                        "screen averages dark while still colliding, and a mean rated one "
                        "title fine at a measured bright-fraction of 59.6%. Needs Pillow; "
                        "guard.py FAILS rather than skipping if it is missing.")
    cfg["paint"] = {"enabled": True}

    cfg["stylesheets"] = sheets
    cfg["_stylesheets"] = (
        ("%d external stylesheet(s) found. Every sheet the page loads must also be in the "
         "staleness hash, or a CSS fix invalidates nothing and ships unapplied: pichash "
         "hashed chunk.js and base.css but not vid62.css, which held most of that film's "
         "look." % len(sheets)) if sheets else
        ("no external stylesheets, all CSS is inline in the document. That is correct as "
         "[]: guard.py only PICHASHes sheets with an href, and an inline sheet cannot go "
         "stale against the document it lives in."))

    cfg["allow"] = []
    cfg["_allow"] = ("exemptions, {\"kind\",\"match\",\"t0\",\"t1\",\"reason\"}. Start "
                     "EMPTY and add only from a measurement you have looked at. An entry "
                     "that matches nothing fails the run as ALLOWDEAD: one inherited entry "
                     "blanket-exempted a whole scene and hid 15.8s of genuine staleness "
                     "while reading as considered.")

    cfg["root_id"] = (root or {}).get("id", "root")
    cfg["_root_id"] = ("timed elements are scanned from HERE, not from the stage. A timed "
                       "element can be a SIBLING of #stage and a stage-scoped query never "
                       "looks at it.")
    cfg["apply_clip_schedule"] = True
    cfg["managed_tags"] = ["DIV", "VIDEO", "IMG"]

    report = {"root": root, "stage": stage, "timeline": timeline,
              "beats": len(beats), "bstat": bstat, "videos": len(vids),
              "ids": len(element_ids(markup)), "sheets": sheets,
              "face_el": face_el, "face_states": list(face_states),
              "caps": (caps_arr, caps_target, has_engine)}
    return cfg, report


def count_todos(o, path="", skip_comments=True):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if skip_comments and isinstance(k, str) and k.startswith("_"):
                continue
            out += count_todos(v, "%s.%s" % (path, k) if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += count_todos(v, "%s[%d]" % (path, i))
    elif isinstance(o, str) and TODO in o:
        out.append(path)
    return out


def main():
    ap = argparse.ArgumentParser(
        description="derive a guard.json skeleton from a composition, with a loud TODO "
                    "on every value that is a measurement rather than a fact")
    ap.add_argument("project", help="directory holding index.html")
    ap.add_argument("-o", "--out", help="where to write (default <project>/guard.json)")
    ap.add_argument("--document", default="index.html")
    ap.add_argument("--transcript", help="word-timestamped whisper JSON. Default: "
                                         "<project>/transcript.json if it exists.")
    ap.add_argument("--gap", type=float, default=0.9,
                    help="a hold longer than this gets one interior sample (default 0.9)")
    ap.add_argument("--snap", type=float, default=0.08,
                    help="snap a boundary to a word onset within this many seconds "
                         "(default 0.08)")
    ap.add_argument("--print", dest="to_stdout", action="store_true",
                    help="write to stdout instead of a file")
    ap.add_argument("--force", action="store_true", help="overwrite an existing file")
    a = ap.parse_args()

    project = os.path.abspath(a.project)
    tr = a.transcript
    if tr is None:
        cand = os.path.join(project, "transcript.json")
        tr = cand if os.path.isfile(cand) else None
    elif not os.path.isabs(tr):
        tr = os.path.join(project, tr)

    cfg, rep = build(project, a.document, tr, a.gap, a.snap)
    text = json.dumps(cfg, indent=2) + "\n"

    if a.to_stdout:
        sys.stdout.write(text)
    else:
        out = a.out or os.path.join(project, "guard.json")
        if os.path.exists(out) and not a.force:
            sys.exit("%s exists. Pass --force to overwrite, but read it first: a config "
                     "in place has measurements in it that this script cannot reproduce."
                     % out)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % out)

    todos = count_todos(cfg)
    print("derived: timeline=%s stage=%s %dx%d, %d beats (%d cuts%s, %d data-starts, "
          "%d from beat map %s, %d interior, %d snapped to onsets from %d words), "
          "%d element ids, %d <video>, %d stylesheet(s)"
          % (rep["timeline"], rep["stage"]["id"], rep["stage"]["w"], rep["stage"]["h"],
             rep["beats"], rep["bstat"]["cuts"],
             (" via %s()" % rep["bstat"]["cut_fn"]) if rep["bstat"]["cut_fn"] else "",
             rep["bstat"]["data_starts"], rep["bstat"]["mapped"],
             "/".join(rep["bstat"]["maps"]) or "none", rep["bstat"]["interior"],
             rep["bstat"]["snapped"], rep["bstat"]["onsets"],
             rep["ids"], rep["videos"], len(rep["sheets"])),
          file=sys.stderr)
    print("face: element=%s states=%s" % (rep["face_el"], ", ".join(rep["face_states"]) or "none"),
          file=sys.stderr)
    print("caption replay: array=%s target=%s engine_present=%s"
          % (rep["caps"][0], rep["caps"][1], rep["caps"][2]), file=sys.stderr)
    print("%d TODO(s) left, guard.py will REFUSE to run until every one is resolved:"
          % len(todos), file=sys.stderr)
    for t in todos:
        print("   %s" % t, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
