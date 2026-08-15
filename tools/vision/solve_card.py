#!/usr/bin/env python3
"""Solve the face-card transform per face-safe window from measured head geometry.

vid44 round 1 estimated crown/chin/centre by eye and the owner saw the presenter sitting
103px off-centre. Never again: every window gets its own s/x/y derived from that window's
own measured crown (person segmentation), chin (face contour) and head centre.

Card (CARD-R, this client's standing default): x2280..3660, y440..1720 in 4K.
Video source is 3840x2160 drawn at the scene origin, transform-origin 0 0:
    screen_x = s*src_x + tx      screen_y = s*src_y + ty
Targets:
    head centre X  -> card centre X
    crown          -> card top + TOP_M
    head height    -> HEAD_FRAC of card height   (caps s so a lean-in cannot crop the chin)

ROUND 2, ONE CONSTANT PER WINDOW. The tracking curve is gone.

Round 1 gave each window a smoothed tx track (+-1.4s moving average at 0.4s spacing),
reasoning that a constant is only correct at the median and the presenter sways up to
594px. The owner's read of the result was "why is the frame always moving left-right, you
have added some issue." A follow that slow does not register as camera operation; it
registers as a bug. So the transform is now constant for the whole window.

That changes which windows can be carded at all, so the self-limiting test is now
measured against the constant instead of against the track: if holding the presenter at
the window median still leaves them more than RESID_MAX off card centre, that window
plays FULL-BLEED, where the source framing already holds them.

Subdivision is also gone. Round 1 split long windows at 5.5s to keep the transform
close to the presenter, which is only safe if every sub-window boundary coincides with a cut,
otherwise the face jumps mid-shot, which is worse than the drift it was fixing. One
window, one transform, no exceptions.

Sway is measured over a ROBUST range (p05..p95), not min..max: several windows have a
single bad contour detection that would otherwise veto an otherwise stable window.
"""
import csv, json, statistics as st

CARD = dict(x0=2280, y0=440, x1=3660, y1=1720)
CARD_W = CARD["x1"] - CARD["x0"]          # 1380
CARD_H = CARD["y1"] - CARD["y0"]          # 1280
HEAD_FRAC  = 0.66      # preferred crown->chin as a fraction of card height
S_CAP      = 0.72      # never scale up past this
# HARD FLOOR: the video must still COVER the card after scaling, or the card shows
# through to the ground. s*2160 >= CARD_H and s*3840 >= CARD_W. The height is binding.
S_MIN      = max(CARD_H / 2160, CARD_W / 3840) + 0.004
CROWN_BIAS = 0.42      # crown sits at 42% of the leftover slack -> more room below the
                       # chin than above the crown, so shoulders read and the head never
                       # looks stuck to the card's top edge
RESID_MAX  = 120       # px off card centre tolerated by a constant transform.
                       # 120/1380 = 8.7% of card width. Beyond that the eye reads them
                       # as mis-framed rather than as sitting slightly off axis.

W = [tuple(x) for x in json.load(open("face-safe-windows.json"))["safe"]]

def t(f): return round((int(f.split("_")[1].split(".")[0]) - 1) / 5.0, 1)

crown = {t(r["file"]): float(r["crownY"]) * 2160
         for r in csv.DictReader(open("crown.csv")) if r["crownY"] not in ("NA","ERR","NOMASK")}
# x anchor comes from the FACE CONTOUR, not the segmentation head band: the band widens
# into the shoulders and dragged one window 230px off-centre when it was measured on the
# rendered card. The contour midpoint is what a viewer reads as "centred".
headcx = {t(r["file"]): (float(r["contourLeft"]) + float(r["contourRight"])) / 2 * 3840
          for r in csv.DictReader(open("facebox.csv")) if r["contourLeft"] not in ("NA","ERR","NOFACE")}
chin = {t(r["file"]): float(r["contourBot"]) * 2160
        for r in csv.DictReader(open("facebox.csv")) if r["contourBot"] not in ("NA","ERR","NOFACE")}

def pick(d, a, b, q=0.5):
    v = sorted(val for k, val in d.items() if a <= k <= b)
    return v[int(q * (len(v) - 1))] if v else None

out = []
print(f"card {CARD['x0']}..{CARD['x1']} x {CARD['y0']}..{CARD['y1']}  "
      f"({CARD_W}x{CARD_H})  sMin {S_MIN:.3f}  headFrac {HEAD_FRAC}  residMax {RESID_MAX}\n")
print(f"{'win':>4} {'range':>16} {'crown':>6} {'chin':>6} {'hcx':>6} {'headH':>6} "
      f"{'s':>6} {'tx':>8} {'ty':>8} {'crwn@':>6} {'chin@':>6} {'resid':>6} {'mode':>10}")
for i, (a, b) in enumerate(W, 1):
    cr = pick(crown, a, b, 0.05)          # highest crown in window -> never crop the top
    ch = pick(chin,  a, b, 0.95)          # lowest chin  in window -> never crop the bottom
    cx = pick(headcx, a, b, 0.50)
    if cr is None or ch is None or cx is None:
        print(f"  W{i:02d}  NO DATA"); continue
    headH = ch - cr
    s = max(S_MIN, min(S_CAP, HEAD_FRAC * CARD_H / headH))
    slack = CARD_H - s * headH
    top_m = max(0.0, CROWN_BIAS * slack)
    tx = CARD["x0"] + CARD_W / 2 - s * cx
    ty = CARD["y0"] + top_m - s * cr
    # clamp so the scaled frame still covers the card on every edge
    tx = min(tx, CARD["x0"])
    tx = max(tx, CARD["x1"] - s * 3840)
    ty = min(ty, CARD["y0"])
    ty = max(ty, CARD["y1"] - s * 2160)
    chin_in_card = s * ch + ty - CARD["y0"]
    crown_in_card = s * cr + ty - CARD["y0"]

    # --- self-limiting card test, against the CONSTANT -----------------------------
    lo = pick(headcx, a, b, 0.05)
    hi = pick(headcx, a, b, 0.95)
    ctr = CARD["x0"] + CARD_W / 2
    resid = max(abs(s * lo + tx - ctr), abs(s * hi + tx - ctr))
    card_ok = resid <= RESID_MAX

    out.append({"win": i, "a": a, "b": b, "s": round(s, 4),
                "tx": round(tx, 1), "ty": round(ty, 1),
                "crown": round(cr), "chin": round(ch), "hcx": round(cx),
                "crown_in_card": round(crown_in_card), "chin_in_card": round(chin_in_card),
                "sway_p05": round(lo), "sway_p95": round(hi),
                "resid": round(resid), "card_ok": card_ok})
    print(f"  W{i:02d} {a:7.2f}-{b:7.2f} {cr:6.0f} {ch:6.0f} {cx:6.0f} {headH:6.0f} "
          f"{s:6.3f} {tx:8.1f} {ty:8.1f} {crown_in_card:6.0f} {chin_in_card:6.0f} "
          f"{resid:6.0f} {'CARD' if card_ok else 'FULL-BLEED':>10}")

json.dump({"card": CARD, "s_min": round(S_MIN, 4), "crown_bias": CROWN_BIAS,
           "head_frac": HEAD_FRAC, "resid_max": RESID_MAX, "windows": out},
          open("card-transforms.json", "w"), indent=1)
nc = sum(1 for o in out if o["card_ok"])
cs = sum(o["b"] - o["a"] for o in out if o["card_ok"])
fs = sum(o["b"] - o["a"] for o in out if not o["card_ok"])
print(f"\nwrote card-transforms.json, {len(out)} windows")
print(f"s range {min(o['s'] for o in out):.3f} .. {max(o['s'] for o in out):.3f}")
print(f"{nc} card ({cs:.1f}s) · {len(out)-nc} full-bleed only ({fs:.1f}s)")
