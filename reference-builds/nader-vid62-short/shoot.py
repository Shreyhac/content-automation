#!/usr/bin/env python3
"""Drive the REAL timeline in Chromium and screenshot chosen beats.

usage: python3 shoot.py [sheet]

A render of this short costs minutes; this costs twenty seconds. It is not a
substitute for reading the render — the renderer's media pipeline, clip scheduling
and encoder all get their own say — but it is what stops a render round being spent
on something a still would have shown.

TWO THINGS HAVE TO BE FAKED BY HAND OR THE PREVIEW LIES:

  * SEEK WITH suppressEvents = false. `tl.pause(t)` and `tl.seek(t)` both default it
    to TRUE, so every onUpdate is skipped. The renderer seeks with it FALSE.
  * #root HAS NO SIZE on a plain page load. It carries its dimensions in
    data-width/data-height, which only the renderer reads, so it computes to height
    0 and every screenshot comes back black.

And clip scheduling is not applied on a plain load either, so every .clip element in
the document sits visible at once — all 23 captions stacked on one another. Replicate
the schedule at t before shooting or the caption band is an unreadable pile.

SAMPLED AT ITS CUTS, NOT ON A GRID. Six of the seven defects the long-form's frame QA
found were at a cut or a join; the middles of held scenes were, as usual, fine.
"""
import asyncio, os, sys
from PIL import Image
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shots")

# every entry is a CUT, a state change, a card entrance/exit, or a figure arriving.
BEATS = [
    (0.000,   "b1 COVER frame 0 — search page composed, box empty, picture in BAND"),
    (2.000,   "b1 typing the name"),
    (3.400,   "b1 name typed, pause"),
    (4.200,   "b1 typing the city"),
    (5.000,   "b1 search bar running"),
    (5.600,   "b1 results landed"),
    (6.000,   "b1 top result ringed"),
    (6.089,   "CUT b2 (wipe) — the result opens"),
    (8.100,   "b2 HOME ADDRESS prints"),
    (9.300,   "b2 PHONE prints"),
    (9.700,   "b2 MID-MOVE picture -> off"),
    (10.100,  "b2 full record landed in the rect"),
    (11.500,  "b2 RELATIVES prints"),
    (13.400,  "b2 AGE prints"),
    (13.555,  "CUT b3 (wipe) — picture still off"),
    (14.000,  "b3 record still holds the rect"),
    (14.450,  "b3 picture back, BAND"),
    (14.600,  "b3 site chrome lights on 'data broker site'"),
    (16.500,  "b3 buy button lights"),
    (16.800,  "b3 FOR SALE stamp"),
    (16.940,  "b3 HANDOFF -> stock card on the word SOLD"),
    (17.700,  "b3 conveyor settled"),
    (18.600,  "b3 stock stamp"),
    (19.700,  "b3 last frame"),
    (19.895,  "CUT b4 (wipe) — BAND"),
    (20.600,  "b4 archive card"),
    (21.400,  "b4 source stamp"),
    (22.150,  "b4 last frame with the picture ON"),
    (22.400,  "b4 MID-MOVE picture -> off"),
    (22.700,  "b4 tile field landed"),
    (24.170,  "b4 HANDOFF -> the figure"),
    (25.700,  "b4 count running"),
    (27.100,  "b4 750 parked"),
    (28.900,  "b4 source pill"),
    (30.500,  "b4 last frame"),
    (30.697,  "CUT b5 (wipe) — CARD"),
    (31.400,  "b5 request log panel"),
    (33.000,  "b5 last frame with the picture ON"),
    (33.300,  "b5 MID-MOVE picture -> off INSIDE THE CARD"),
    (33.600,  "b5 activity log at full size"),
    (35.100,  "b5 420+ lands"),
    (36.800,  "b5 unit line"),
    (38.300,  "b5 publish chip"),
    (39.000,  "b5 last frame"),
    (39.206,  "CUT b6 (wipe) — NO FACE"),
    (39.900,  "b6 step 1, scanner recording"),
    (41.700,  "b6 step 2"),
    (42.400,  "b6 recording 2"),
    (44.100,  "b6 step 3"),
    (45.600,  "b6 click accent"),
    (45.900,  "b6 last frame"),
    (46.004,  "CUT b7 (wipe) — BAND, opens on a complete sentence"),
    (46.500,  "b7 mark on the word Incogni"),
    (47.700,  "b7 recap 1"),
    (48.700,  "b7 recap 2"),
    (49.600,  "b7 recap 3"),
    (50.500,  "b7 last frame"),
    (50.717,  "JOIN b8 (the one flash) — CARD"),
    (51.800,  "b8 CODE NADER lands"),
    (52.500,  "b8 60% chip"),
    (52.950,  "b8 last frame with the picture ON"),
    (53.250,  "b8 MID-MOVE picture -> off INSIDE THE CARD"),
    (53.600,  "b8 CTA card landed"),
    (54.400,  "b8 last frame"),
    (54.888,  "CUT b9 (wipe) — THE CLOSE, FULL FRAME"),
    (55.600,  "b9 close, caption low"),
    (57.500,  "b9 close, mid push"),
    (60.700,  "b9 LAST FRAME"),
]

SEEK = """(t) => {
  const tl = window.__timelines.vid62short;
  const r = document.getElementById('root');
  r.style.width = r.dataset.width + 'px';
  r.style.height = r.dataset.height + 'px';
  // the renderer seeks with suppressEvents FALSE; the default is TRUE and skips
  // every onUpdate, so anything callback-driven looks broken here and fine there
  tl.pause();
  tl.time(t, false);
  // replicate the renderer's clip scheduling: on a plain load every .clip in the
  // document is visible at once
  document.querySelectorAll('.clip').forEach(c => {
    const a = parseFloat(c.dataset.start || '0');
    const d = parseFloat(c.dataset.duration || '0');
    c.style.display = (t >= a && t <= a + d) ? '' : 'none';
  });
}"""


async def main():
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--allow-file-access-from-files",
                                          "--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920},
                              device_scale_factor=1)
        await pg.goto("file://" + os.path.join(HERE, "index.html"))
        await pg.wait_for_timeout(2500)
        for i, (t, why) in enumerate(BEATS):
            await pg.evaluate(SEEK, t)
            await pg.wait_for_timeout(90)
            await pg.screenshot(path=os.path.join(OUT, "s%02d_%07.3f.png" % (i, t)))
            print("  %2d  t=%7.3f  %s" % (i, t, why))
        await b.close()

    # contact sheets, 6 across, at a size where type is actually readable
    shots = sorted(f for f in os.listdir(OUT) if f.endswith(".png"))
    per, cols, th = 12, 6, 620
    tw = int(1080 / 1920 * th)
    for k in range(0, len(shots), per):
        grp = shots[k:k + per]
        rows = (len(grp) + cols - 1) // cols
        sheet = Image.new("RGB", (tw * cols, th * rows), (0, 0, 0))
        for j, f in enumerate(grp):
            im = Image.open(os.path.join(OUT, f)).convert("RGB")
            sheet.paste(im.resize((tw, th), Image.LANCZOS),
                        (tw * (j % cols), th * (j // cols)))
        sheet.save(os.path.join(HERE, "sheet%d.jpg" % (k // per + 1)), quality=90)
        print("  sheet%d.jpg  %d frames" % (k // per + 1, len(grp)))


if __name__ == "__main__":
    asyncio.run(main())
