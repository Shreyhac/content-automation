#!/usr/bin/env python3
"""Solve THE ONE A-roll placement for the vertical short from measured head geometry.

Source: vid46/r2/{crown,facebox}.csv - the RE-CUT measurement pass, 1117 rows at 5fps
(t = (n-1)/5 on the 223.400s re-cut timeline, the same timeline as hf46/words.json).

WHY THERE IS ONE PICTURE WITH TWO STATES
----------------------------------------
v1 had two (a near-full-bleed FULL and a floating CARD) and changed placement five
times in forty seconds. The owner: "the a roll cuts are weird ... jump cuts are not
perfect". The presenter's head changed size every time the presenter appeared.

More fundamentally, v1's measurement was backwards. It put graphics at y1000-1346 over
a full-bleed face "because the presenter's chin is at y1560, so a stack above it crosses the presenter's
chest". The chin is the BOTTOM of the face: everything above it IS the face. And the
source is a tight close-up (crown y221, chin y1921 of 2160 - the head is 79% of frame
height with only 239px of collar below it), so:

  * a cover crop to 9:16 needs s >= 1920/2160 = 0.889 -> chin at y1708, inside
    Instagram's bottom UI band;
  * v1's s = 0.794 cleared that band but put the chin at y1560, which is exactly
    where the caption band is.

There is NO 9:16 COVER crop of this A-roll that leaves room for graphics or captions.
So the picture is placed rather than covered, in two states that the timeline moves
between as a visible camera move (vid39's device, which the owner asked for by name):

  HERO   1080 x 1210 at y0, s = 0.56. Crown y138, chin y1004 (worst y1100), so the
         caption band at y1396 is 296px clear of the presenter's jaw even on the presenter's most forward
         frame. Used for the sign-off.
  CARD   the SAME pixels, scaled 0.6786 and translated, clipped to a rounded portrait
         at x260-820, y838-1574. vid39 used x216-864 / y1020-1880 for a source that
         had chest in frame; this head has 239px of collar and nothing else, so the
         card is re-solved rather than copied.
  OFF    collapsed. Graphics beats: the gaze map forbids the presenter's face there.

and the zones follow the state:

  SPLIT beat            GFX beat              HERO beat
  y150 graphics         y150 graphics         y0   picture (to y1210)
  y640 ...                                    y1250 chip
  y690 caption          y1380 ...             y1350 ...
  y826 ...              y1396 caption         y1396 caption
  y838 FACE CARD        y1560 ...             y1560 ...
  y1574 ...
  y1600 Instagram UI band. No FACE below this line, in any state.

ONE CONSTANT tx PER FACE BLOCK. Never a tracking tween: a smoothed follow reads as a
glitch, not as camera operation (vid46 round 2). The x anchor is the FACE CONTOUR, not
the segmentation band, because the band widens with shoulders and hair and drags the
centre off the face.
"""
import csv, json, statistics as st
from beats import resolve, FACE_CLIPS

R2 = "../vid46/r2"
SRC_W, SRC_H = 3840, 2160
CAN_W, CAN_H = 1080, 1920

# ---- HERO ------------------------------------------------------------------------
S = 0.56                      # the ONE bake scale; CARD is a transform of these pixels
HERO_H = round(SRC_H * S)     # 1210
VID_W = round(SRC_W * S)      # 2150
CROP_MAX = VID_W - CAN_W      # 1070

# ---- CARD ------------------------------------------------------------------------
CARD = dict(x0=260, y0=838, x1=820, y1=1574)      # 560 x 736
CARD_K = 0.6786               # scale applied to the HERO pixels, origin 0 0
CARD_TX = 173.0               # so the head centre (x540 in the bake) lands at x540
CARD_TY = 799.0               # so the median chin lands at y1480

HERO_CHIN_MAX = 1240          # hero: chin must clear the chip zone at y1250
CARD_CHIN_MAX = 1580          # card: the presenter's chin must stay above the Instagram UI line
CROWN_MIN = 30                # and the presenter's crown must be inside whichever rect the presenter is in
RESID_MAX = 110               # px the constant may leave the presenter's face centre off the
                              # canvas centre at the 5th/95th percentile. 110/1080 =
                              # 10%: past that the frame reads as mis-framed and the
                              # block needs its own tx.


def load():
    crown, chin, hcx = {}, {}, {}

    def t(f):
        return round((int(f.split("_")[1].split(".")[0]) - 1) / 5.0, 1)

    for r in csv.DictReader(open(f"{R2}/crown.csv")):
        if r["crownY"] not in ("NA", "ERR", "NOMASK"):
            crown[t(r["file"])] = float(r["crownY"]) * SRC_H
    for r in csv.DictReader(open(f"{R2}/facebox.csv")):
        if r["contourLeft"] not in ("NA", "ERR", "NOFACE"):
            hcx[t(r["file"])] = (float(r["contourLeft"])
                                 + float(r["contourRight"])) / 2 * SRC_W
        if r["contourBot"] not in ("NA", "ERR", "NOFACE"):
            chin[t(r["file"])] = float(r["contourBot"]) * SRC_H
    return crown, chin, hcx


def samples(a, b, d):
    return [v for t, v in sorted(d.items()) if a - 0.2 <= t <= b + 0.2]


def pct(v, p):
    v = sorted(v)
    if not v:
        return None
    i = min(len(v) - 1, max(0, int(round(p / 100 * (len(v) - 1)))))
    return v[i]


resolve()
crown, chin, hcx = load()

out = {"canvas": [CAN_W, CAN_H],
       "source": [SRC_W, SRC_H],
       "hero": {"x": 0, "y": 0, "w": CAN_W, "h": HERO_H,
                "s": round(S, 6), "vid_w": VID_W, "vid_h": HERO_H},
       "card": {"rect": CARD, "k": CARD_K, "tx": CARD_TX, "ty": CARD_TY,
                "radius": 30},
       "zones": {"split_gfx": [150, 640], "split_cap": [690, 826],
                 "gfx": [150, 1380], "hero_chip": [1250, 1350],
                 "caption": [1396, 1560], "ui": 1600},
       "clips": {}}

print(f"HERO {CAN_W}x{HERO_H} at y0   s={S:.6f}   bake {VID_W}x{HERO_H}   "
      f"crop_x range 0..{CROP_MAX}")
print(f"CARD x{CARD['x0']}-{CARD['x1']} y{CARD['y0']}-{CARD['y1']}   "
      f"k={CARD_K}  tx={CARD_TX}  ty={CARD_TY}")
print()
bad = 0
for c in FACE_CLIPS:
    a, b = c["src_a"], c["src_b"]
    cr, ch, cx = samples(a, b, crown), samples(a, b, chin), samples(a, b, hcx)
    hx = st.median(cx)
    crop_x = min(CROP_MAX, max(0, round(hx * S - CAN_W / 2)))

    lo = pct(cx, 5) * S - crop_x
    hi = pct(cx, 95) * S - crop_x
    resid = round(max(abs(lo - CAN_W / 2), abs(hi - CAN_W / 2)))

    # HERO: the baked pixels, placed 1:1 at y0
    h_crown = round(pct(cr, 5) * S)
    h_chin = round(pct(ch, 95) * S)
    # CARD: the same pixels through the card transform (origin 0 0)
    def card_y(v):
        return round(v * CARD_K + CARD_TY)
    c_crown, c_chin = card_y(pct(cr, 5) * S), card_y(pct(ch, 95) * S)
    c_chin_med = card_y(st.median(ch) * S)

    rec = dict(src_a=a, src_b=b, frames=c["frames"], at=c["at"], beat=c["beat"],
               crop_x=crop_x, crop_y=0, crop_w=CAN_W, crop_h=HERO_H,
               scale_w=VID_W, scale_h=HERO_H,
               hero=dict(crown=h_crown, chin=h_chin),
               card=dict(crown=c_crown, chin=c_chin, chin_median=c_chin_med),
               head_h=round((st.median(ch) - pct(cr, 50)) * S),
               sway=round((pct(cx, 95) - pct(cx, 5)) * S), resid=resid,
               n=len(cx))
    out["clips"][c["clip"]] = rec

    flags = []
    if h_chin > HERO_CHIN_MAX:
        flags.append(f"HERO CHIN {h_chin} > {HERO_CHIN_MAX}")
    if h_crown < CROWN_MIN:
        flags.append(f"HERO CROWN {h_crown} < {CROWN_MIN}")
    if c_chin > CARD_CHIN_MAX:
        flags.append(f"CARD CHIN {c_chin} > {CARD_CHIN_MAX}")
    if c_crown < CARD["y0"] + CROWN_MIN:
        flags.append(f"CARD CROWN {c_crown} < {CARD['y0'] + CROWN_MIN}")
    if resid > RESID_MAX:
        flags.append(f"RESID {resid} > {RESID_MAX}")
    if flags:
        bad = 1
    print(f"{c['clip']:3} {a:8.3f}-{b:8.3f} n={rec['n']:3} crop_x={crop_x:4}  "
          f"HERO crown y{h_crown:<4} chin y{h_chin:<5} | CARD crown y{c_crown:<4} "
          f"chin y{c_chin_med:<4} (worst y{c_chin})  sway={rec['sway']:3} "
          f"resid={resid:3}  {'  '.join(flags) or 'OK'}")

# the card must be COVERED by the transformed picture in both axes
_x0, _y0 = CARD_TX, CARD_TY
_x1, _y1 = CAN_W * CARD_K + CARD_TX, HERO_H * CARD_K + CARD_TY
assert _x0 <= CARD["x0"] and _x1 >= CARD["x1"], (_x0, _x1, CARD)
assert _y0 <= CARD["y0"] and _y1 >= CARD["y1"], (_y0, _y1, CARD)
print(f"\ncard coverage: picture spans x{_x0:.0f}-{_x1:.0f} y{_y0:.0f}-{_y1:.0f} "
      f"against a card at x{CARD['x0']}-{CARD['x1']} y{CARD['y0']}-{CARD['y1']}  OK")

assert not bad, "a face block fails the hero/card geometry gates"
json.dump(out, open("short-transforms.json", "w"), indent=1)
print("\nwrote short-transforms.json")
