#!/usr/bin/env python3
"""Composite each baked beat into its own state, at its own SWAY EXTREMES, and draw
the zones over it — before a line of HTML is written.

This is the step that catches a solve that is arithmetically clean and wrong on
screen. It is deliberately not a render: it uses the baked files themselves, so what
it shows is the pixels the composition will place, in the rect it will place them in.

For each beat it picks the two frames where the presenter's face contour is furthest LEFT and
furthest RIGHT (from vid62/facebox.csv over the beat's visible spans), because a
constant crop is only ever wrong at the extremes, plus the beat's own first frame,
which is what a viewer sees on the cut.
"""
import csv, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V62 = os.path.abspath(os.path.join(HERE, "..", "vid62"))
FPS_M = 5.0
SRC_W, SRC_H = 3840, 2160

B = json.load(open(os.path.join(HERE, "beats.json")))
Z = B["zones"]
ST = B["states"]


def t_of(f):
    return round((int(f[1:].split(".")[0]) - 1) / FPS_M, 2)


def face_extremes(vis):
    lr = {}
    for r in csv.DictReader(open(os.path.join(V62, "facebox.csv"))):
        try:
            lr[t_of(r["file"])] = (float(r["contourLeft"]) * SRC_W,
                                   float(r["contourRight"]) * SRC_W)
        except (ValueError, TypeError):
            pass
    pts = [(t, v) for t, v in sorted(lr.items())
           if any(a - 0.2 <= t <= b + 0.2 for a, b in vis)]
    if not pts:
        return []
    lo = min(pts, key=lambda p: p[1][0])[0]
    hi = max(pts, key=lambda p: p[1][1])[0]
    return [lo, hi]


def main():
    out = os.path.join(HERE, "proof")
    os.makedirs(out, exist_ok=True)
    from PIL import Image, ImageDraw

    for p in B["beats"]:
        if p["state"] == "noface":
            continue
        clip = os.path.join(HERE, "assets", "%s.mp4" % p["id"])
        marks = [p["a"] + 0.02] + face_extremes(p["vis"])
        tiles = []
        for k, src_t in enumerate(marks):
            local = max(0.0, min(p["dur"] - 0.05, src_t - p["a"]))
            jpg = os.path.join(out, "%s-%d.jpg" % (p["id"], k))
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error",
                            "-ss", "%.3f" % local, "-i", clip, "-frames:v", "1",
                            jpg], check=True)
            tiles.append((src_t, Image.open(jpg).convert("RGB")))

        for k, (src_t, bake) in enumerate(tiles):
            can = Image.new("RGB", (1080, 1920), (8, 8, 12))
            st = ST[p["state"]]
            # the band/card rect, and the CARD is the same pixels clipped
            x0, y0, x1, y1 = st["rect"]
            crop = bake.crop((x0, 0, x1, y1 - y0))
            can.paste(crop, (x0, y0))
            d = ImageDraw.Draw(can)
            for y, c, lab in ((Z["top"], (90, 200, 255), "top 150"),
                              (Z["gfx"][1], (70, 90, 130), "gfx bottom 640"),
                              (Z["cap_hi"][0], (120, 220, 140), "cap 674"),
                              (Z["cap_hi"][1], (120, 220, 140), "cap 826"),
                              (Z["pic"][0], (255, 190, 60), "pic top 838"),
                              (Z["pic"][1], (255, 190, 60), "pic bot 1574"),
                              (Z["ui"], (255, 70, 60), "UI 1600")):
                d.line([(0, y), (1080, y)], fill=c, width=2)
                d.text((8, y + 4), lab, fill=c)
            d.line([(960, 900), (960, 1600)], fill=(255, 70, 60), width=2)
            d.text((10, 10), "%s  %s  src %.2fs  crop %d,%d"
                   % (p["id"], p["state"], src_t, p["crop_x"], p["crop_y"]),
                   fill=(255, 255, 255))
            can.save(os.path.join(out, "%s-proof%d.jpg" % (p["id"], k)), quality=90)
        print("  %s  %d proofs at %s" % (p["id"], len(tiles),
                                         ", ".join("%.2f" % m for m in marks)))
    # one contact sheet so all of it can be read at once
    from PIL import Image
    fs = sorted(f for f in os.listdir(out) if f.endswith(("proof0.jpg", "proof1.jpg",
                                                          "proof2.jpg")))
    ims = [Image.open(os.path.join(out, f)).resize((360, 640)) for f in fs]
    cols = 8
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 360, rows * 640), (20, 20, 26))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * 360, (i // cols) * 640))
    sheet.save(os.path.join(HERE, "proof-sheet.jpg"), quality=86)
    print("  wrote proof-sheet.jpg (%d tiles)" % len(ims))


if __name__ == "__main__":
    main()
