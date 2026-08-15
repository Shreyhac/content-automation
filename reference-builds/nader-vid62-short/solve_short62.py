#!/usr/bin/env python3
"""vid62 short — one band bake, one close bake, solved from his own crown and chin.

WHAT IS THE SAME AS vid59's SOLVER
----------------------------------
The format is Nader's, and it has not changed: animations on TOP (y150-640),
captions in the MIDDLE (y674-826), his picture on the BOTTOM (y838-1574) in a BAND
or a CARD that share ONE camera and differ only by clip-path, so his head is the
same size in both and a state change is a widen rather than a resize. The close is
its own shot with its own bake.

WHAT IS DIFFERENT, AND WHY IT MATTERS MORE HERE
-----------------------------------------------
1. ONE TIMELINE. vid59's CSVs were measured on the RAW take while its beats were
   timed against a CUT master 18.41s shorter, and the first solve framed two beats
   against footage six seconds of speech away. vid62 has no retake cuts —
   chunks.json runs 0 -> 373.081 continuously against the same master crown.csv and
   facebox.csv were measured on — so cut_to_raw() is identity and is absent rather
   than written as a no-op.

2. THE CROP IS SOLVED OVER THE SPAN HE IS ACTUALLY ON SCREEN, NOT THE BEAT.
   Five of the nine beats show him for only part of their runtime, because
   hf62/camera-windows.json says he is reading for the rest and the client's note
   (four times on the long-form) is that the picture comes off when he reads. A
   median head position taken over a whole beat is a median over frames the viewer
   never sees — the general form of [[feedback_measure_the_window_not_the_take]],
   which cost vid59 a beat that had to move from CARD to BAND after the fact.
   So each beat carries `vis`: the spans it is visible for, and every percentile
   below is computed on those spans alone.

3. THE CLOSE IS MEASURED ON ITS OWN 29 SAMPLES. The long-form's c17 already ships
   this take full-bleed, so full-bleed is established for this footage — but
   "established" is not a measurement, and b9 is a different five seconds.
"""
import csv, json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
V62 = os.path.abspath(os.path.join(HERE, "..", "vid62"))

SRC_W, SRC_H = 3840, 2160
CAN_W, CAN_H = 1080, 1920
FPS_M = 5.0                        # crown.csv / facebox.csv are 5fps on the master

# ---- zones (identical to vid59's short; this is Nader's format, not a per-film choice)
UI          = 1600
TOP         = 150
GFX         = (150, 640)
CAP_HI      = (674, 826)
PIC         = (838, 1574)
CARD_X      = (260, 820)
CLOSE_PIC   = (0, 1920)
CAP_LOW     = (1490, 1590)

CROWN_INSET    = 34
CHIN_TARGET    = 1450
CHIN_MAX       = 1560
CLOSE_CHIN_MAX = 1488
RESID_MAX      = 150
FACE_MARGIN    = 40


def t_of(f):
    return round((int(f.split("_")[1].split(".")[0]) - 1) / FPS_M, 2) \
        if "_" in f else round((int(f[1:].split(".")[0]) - 1) / FPS_M, 2)


def load():
    crown, chin, hcx, hlr = {}, {}, {}, {}
    for r in csv.DictReader(open(os.path.join(V62, "crown.csv"))):
        try:
            crown[t_of(r["file"])] = float(r["crownY"]) * SRC_H
        except (ValueError, TypeError):
            pass
    for r in csv.DictReader(open(os.path.join(V62, "facebox.csv"))):
        t = t_of(r["file"])
        try:
            l, rr = float(r["contourLeft"]) * SRC_W, float(r["contourRight"]) * SRC_W
            hcx[t], hlr[t] = (l + rr) / 2, (l, rr)
        except (ValueError, TypeError):
            pass
        try:
            chin[t] = float(r["contourBot"]) * SRC_H
        except (ValueError, TypeError):
            pass
    return crown, chin, hcx, hlr


def samples(vis, d):
    """Sample a CSV over the spans the picture is ON SCREEN, not over the beat."""
    out = []
    for a, b in vis:
        out += [v for t, v in sorted(d.items()) if a - 0.2 <= t <= b + 0.2]
    return out


def pct(v, p):
    v = sorted(v)
    i = min(len(v) - 1, max(0, int(round(p / 100.0 * (len(v) - 1)))))
    return v[i]


def main():
    beats = json.load(open(os.path.join(V62, "short-beats.json")))
    crown, chin, hcx, hlr = load()
    shown = [b for b in beats if b["vis"]]
    band = [b for b in shown if b["state"] in ("BAND", "CARD")]

    # ONE scale across every band/card beat: his head cannot change size from one
    # band beat to the next. Solved over the union of the spans he is visible in.
    all_cr, all_ch = [], []
    for b in band:
        all_cr += samples(b["vis"], crown)
        all_ch += samples(b["vis"], chin)
    cr03, ch_med = pct(all_cr, 3), st.median(all_ch)
    head = ch_med - cr03
    S_BAND = (CHIN_TARGET - (PIC[0] + CROWN_INSET)) / head

    BW = CAN_W
    BH = int((PIC[1] - PIC[0]) / 2 + 12) * 2

    S_CLOSE = CAN_H / float(SRC_H)
    CW = int(round(CAN_W / S_CLOSE))

    print("ONE BAND BAKE   (%d band/card beats, %d samples)" % (len(band), len(all_cr)))
    print("  BAND / CARD  s=%.6f  k=1.000000  bake %dx%d, crown row %d"
          % (S_BAND, BW, BH, CROWN_INSET))
    print("               head %.0fpx  picture y%d-%d" % (head * S_BAND, PIC[0], PIC[1]))

    # ---- WHY THERE IS NO FULL-BLEED CLOSE IN THIS SHORT ---------------------------
    # vid59's close was a genuine 1215x2160 crop scaled to the canvas, and vid58's
    # client note asked for exactly that ("show nader in full frame here"). It is
    # ruled out here by THIS take's own measurements rather than by preference, and
    # the reason is the framing of the take, not the beat:
    #
    #   his head measures 1371 source px tall and 1110 wide (63% of frame height) —
    #   this is a tighter shot than vid59's. A 9:16 window of a 16:9 frame is 1215px
    #   wide, so his face alone occupies 91% of it before he moves at all, and over
    #   b9 he sways 274px. Solved full-bleed, his contour ran x-13..1154 of 1080:
    #   BOTH cheeks outside the frame in the same beat, and his chin landed at y1574
    #   with the caption band opening at y1490.
    #
    # Cropping his head is the single defect this client has raised most often
    # (three rounds on the long-form), so the close plays as a BAND on the same
    # camera as every other beat, bare of new animation, with a slow push. The
    # numbers are printed here so the next production does not re-derive them.
    # ---- CLOSEW: the full-frame close, as a full-WIDTH picture --------------------
    # The client asked for his A-roll "in full screen" on the closing beat. A true
    # 9:16 crop of a 16:9 frame is 1215px wide and, measured on THIS beat with the
    # crop centred as well as it can be, his face contour runs x-43..1123 of 0..1080
    # — 43px of cheek outside the frame on BOTH sides — with his worst chin at y1601,
    # one pixel inside the Instagram UI band, and no room left for a caption.
    #
    # So "full screen" is built as a full-WIDTH picture instead: a 1440x2160 crop
    # (the source's whole height) scaled to 1080x1620. It fills the frame edge to
    # edge horizontally, shows his entire head, and leaves a caption band under his
    # chin and above y1600. Its lower edge lands on y1574 — the same picture floor
    # every other beat uses — so the close reads as the band opening up rather than
    # as a different rig.
    # s=0.68 rather than 0.75: at 0.75 the crop is 1440 wide and his face SPAN over
    # this beat — head width plus 640px of sway — is 1312, leaving 44px at his worst
    # frame. Read on the render that is not a crop but it is a wander: he drifts into
    # the frame edge and the close reads tighter than every other beat in the cut.
    # 0.68 gives 1588 of source width, ~94px of margin at both extremes, and a
    # picture 1080x1469 whose top lands at y105 and whose bottom lands on the same
    # y1574 floor as the band.
    S_CLOSEW = 0.68
    # BOTH bake dimensions have to be EVEN or libx264 refuses the yuv420p chroma
    # plane: 2160*0.68 is 1469 and the first bake exited 187 on it. Rounded to 1470,
    # which makes the vertical scale 0.68056 against 0.68009 horizontal — a 0.07%
    # anamorphic difference, four hundredths of a pixel across his face.
    CW_W = int(round(CAN_W / S_CLOSEW / 2)) * 2          # 1588
    PH_W = int(round(SRC_H * S_CLOSEW / 2)) * 2          # 1470
    CH_W = SRC_H
    TY_W = 1574 - PH_W                                   # bottom edge on the floor
    CAP_W = (1390, 1560)

    S_CLOSE_HYP = CAN_H / float(SRC_H)
    cl = [b for b in beats if b["id"] == "b9"][0]
    c_ch, c_lr = samples(cl["vis"], chin), samples(cl["vis"], hlr)
    print("  CLOSE        RULED OUT by measurement, not preference: at s=%.4f a "
          "full-bleed" % S_CLOSE_HYP)
    print("               crop puts his contour at x%d..%d of 0..1080 and his worst "
          "chin at y%d"
          % (round((min(v[0] for v in c_lr) - (st.median([(v[0] + v[1]) / 2
                                                          for v in c_lr]) - CW / 2))
                   * S_CLOSE_HYP),
             round((max(v[1] for v in c_lr) - (st.median([(v[0] + v[1]) / 2
                                                          for v in c_lr]) - CW / 2))
                   * S_CLOSE_HYP),
             round(max(c_ch) * S_CLOSE_HYP)))
    print("               (caption band opens at y%d). b9 plays as a BAND.\n"
          % CAP_LOW[0])

    out = dict(canvas=[CAN_W, CAN_H], source=[SRC_W, SRC_H],
               bake=dict(s=round(S_BAND, 6), w=BW, h=BH, crown_row=CROWN_INSET),
               close_bake=dict(s=round(S_CLOSE, 6), crop_w=CW, crop_h=SRC_H,
                               w=CAN_W, h=CAN_H),
               states=dict(
                   band=dict(rect=[0, PIC[0], CAN_W, PIC[1]], k=1.0, tx=0.0,
                             ty=float(PIC[0])),
                   card=dict(rect=[CARD_X[0], PIC[0], CARD_X[1], PIC[1]], radius=30,
                             k=1.0, tx=0.0, ty=float(PIC[0])),
                   closew=dict(rect=[0, TY_W, CAN_W, 1574], k=1.0, tx=0.0,
                               ty=float(TY_W))),
               closew_bake=dict(s=S_CLOSEW, crop_w=CW_W, crop_h=CH_W, w=CAN_W,
                                h=PH_W, ty=TY_W),
               zones=dict(gfx=list(GFX), cap_hi=list(CAP_HI), pic=list(PIC),
                          close_pic=list(CLOSE_PIC), cap_low=list(CAP_W),
                          top=TOP, ui=UI, gfx_x=[70, 960]),
               beats=[])

    print("  %-3s %-46s %6s %6s   %s" % ("b", "beat", "crop_x", "resid", "clearances"))
    bad = []
    for b in beats:
        close = b["state"] == "CLOSEW"
        if not b["vis"]:
            out["beats"].append(dict(id=b["id"], why=b["why"], src_a=b["a"],
                                     src_b=b["b"], state="noface"))
            print("  %-3s %-46s %6s %6s   picture off for the whole beat"
                  % (b["id"], b["why"][:46], "-", "-"))
            continue
        cr, ch = samples(b["vis"], crown), samples(b["vis"], chin)
        cx, lr = samples(b["vis"], hcx), samples(b["vis"], hlr)
        S = S_CLOSEW if close else S_BAND
        cw, chh = (CW_W, CH_W) if close else (BW, BH)
        chin_max = CAP_W[0] - 12 if close else CHIN_MAX
        pic_top = TY_W if close else PIC[0]

        if close:
            # full width, centred on the MIDPOINT OF HIS EXTREMES: with no card edge
            # to read him against, what the eye notices is how near he comes to the
            # screen edge, and that is what this value balances.
            mid_w = (min(v[0] for v in lr) + max(v[1] for v in lr)) / 2.0
            cx0 = max(0, min(SRC_W - CW_W, int(round(mid_w - CW_W / 2.0))))
            cy0 = 0
            to_can = lambda v: v * (PH_W / float(SRC_H)) + TY_W
            to_can_x = lambda v: (v - cx0) * S_CLOSEW
        else:
            # A CARD is 560 wide and his face contour measures ~468 at this scale, so
            # the whole horizontal slack is 92px — 46 a side against a 40px margin.
            # Centring the crop on his MEDIAN head centre spends that slack on
            # whichever side he happens to sit for most of the beat: b3 came out at
            # x252-720 against a card at x260-820 and failed on the left while
            # leaving 100px unused on the right. So a card centres on the MIDPOINT OF
            # HIS EXTREMES, which is the value that maximises the smaller margin —
            # the constraint FACE_MARGIN actually states. Bands keep the median,
            # because a full-width rect has margin to spare and the median is what
            # keeps his head near the canvas centre where the eye expects it.
            if b["state"] == "CARD":
                mid = (min(v[0] for v in lr) + max(v[1] for v in lr)) / 2.0
                aim = mid * S - (CARD_X[0] + CARD_X[1]) / 2.0
            else:
                aim = st.median(cx) * S - BW / 2.0
            cx0 = max(0, min(round(SRC_W * S) - BW, int(round(aim))))
            cy0 = max(0, min(round(SRC_H * S) - BH,
                             int(round(pct(cr, 3) * S - CROWN_INSET))))
            to_can = lambda v: v * S - cy0 + PIC[0]
            to_can_x = lambda v: v * S - cx0

        c_crown, c_chin = round(to_can(pct(cr, 3))), round(to_can(pct(ch, 97)))
        c_chin_med, c_chin_worst = round(to_can(st.median(ch))), round(to_can(max(ch)))
        resid = round(max(abs(to_can_x(pct(cx, 5)) - CAN_W / 2),
                          abs(to_can_x(pct(cx, 95)) - CAN_W / 2)))

        f = []
        if c_chin_worst > chin_max:
            f.append("CHIN worst %d > %d" % (c_chin_worst, chin_max))
        if c_chin_worst > UI:
            f.append("!! CHIN IN THE UI BAND")
        if c_crown < pic_top + (0 if close else 20):
            f.append("CROWN %d above picture top %d" % (c_crown, pic_top))
        # RESID is a PROXY for "does his face leave the rect", and on a full-width
        # close the rect is the whole frame, so the thing it stands in for is measured
        # directly by FACE_MARGIN below and the proxy has nothing left to say. b9
        # sways 231px and still keeps 264px of margin either side. Same reasoning
        # vid59's solver used when it raised the bound for b6 — with the difference
        # that here the direct test is not merely also-run, it is the only one that
        # can fail.
        if not close and resid > RESID_MAX:
            f.append("RESID %d > %d" % (resid, RESID_MAX))
        rx0, rx1 = CARD_X if b["state"] == "CARD" else (0, CAN_W)
        f_l = min(to_can_x(v[0]) for v in lr)
        f_r = max(to_can_x(v[1]) for v in lr)
        if f_l < rx0 + FACE_MARGIN or f_r > rx1 - FACE_MARGIN:
            f.append("FACE x%d-%d inside rect x%d-%d by <%dpx"
                     % (round(f_l), round(f_r), rx0, rx1, FACE_MARGIN))
        if f:
            bad.append((b["id"], f))

        out["beats"].append(dict(
            id=b["id"], why=b["why"], src_a=b["a"], src_b=b["b"], vis=b["vis"],
            state=b["state"].lower(),
            crop_x=cx0, crop_y=cy0, crop_w=cw, crop_h=chh, s=round(S, 6),
            crown=c_crown, chin=c_chin, chin_median=c_chin_med,
            chin_worst=c_chin_worst,
            sway=round((pct(cx, 95) - pct(cx, 5)) * S), resid=resid, n=len(cx),
            face_x=[round(f_l), round(f_r)]))

        print("  %-3s %-46s %6d %5dpx   crown %4d  chin med %4d / p97 %4d / worst %4d "
              "(%s, %d samples)%s"
              % (b["id"], b["why"][:46], cx0, resid, c_crown, c_chin_med, c_chin,
                 c_chin_worst, b["state"].lower(), len(cx),
                 "   <<< " + "; ".join(f) if f else ""))

    json.dump(out, open(os.path.join(V62, "short-transforms.json"), "w"), indent=1)
    print("\n  wrote vid62/short-transforms.json")
    if bad:
        raise SystemExit("\n!! %d beat(s) violate the solve" % len(bad))
    print("  every visible beat clears the UI band, the caption band and its rect edges")


if __name__ == "__main__":
    main()
