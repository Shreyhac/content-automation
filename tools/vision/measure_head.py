#!/usr/bin/env python3
"""Cross-platform head measurement. A port of crown.swift + facebox.swift.

    python tools/vision/measure_head.py <dir-of-jpgs> [--csv out.csv]

Why this exists: `crown.swift` and `facebox.swift` use Apple's Vision framework
and therefore only run on macOS. This produces the same measurements from
MediaPipe so the pipeline can solve geometry on any host. Same rules, same
normalised output columns, so `build_windows.py` and `solve_card.py` consume it
unchanged.

The two rules that matter, carried over verbatim from the Swift tools:

  crown   the topmost segmentation-mask row with a run of >= 8 foreground px.
          NOT the face bounding box. CLAUDE.md and playbooks/face-geometry.md
          are explicit that a face box stops at the hairline and is not the
          head: using it crops the crown every time.

  chin    from the face contour, not the box. MediaPipe landmark 152 is the
          chin point on the FACE_OVAL contour.

Output CSV (normalised 0..1, top-left origin), one row per frame:

    file,crownY,chinY,headCX,headL,headR,faceTop,faceBot

Models live in tools/vision/models/ and are fetched once:
  face_landmarker.task    mediapipe-models/face_landmarker/face_landmarker/float16/1/
  selfie_segmenter.tflite mediapipe-models/image_segmenter/selfie_segmenter/float16/1/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

HERE = Path(__file__).resolve().parent
MODELS = HERE / "models"

# crown.swift: a row counts only once it carries a run of at least this many
# foreground pixels, which rejects stray mask speckle above the hair.
MIN_RUN = 8

# The head band crown.swift reports centre-x over: crown down to crown + 22% of
# frame height. Wide enough to cover the skull, tight enough to exclude
# shoulders, which would drag the centre sideways whenever he leans.
HEAD_BAND_FRAC = 0.22

CHIN_LANDMARK = 152  # FACE_OVAL bottom point


def _landmarker() -> vision.FaceLandmarker:
    model = MODELS / "face_landmarker.task"
    if not model.exists():
        sys.exit(f"missing {model}. See the module docstring for the fetch URL.")
    return vision.FaceLandmarker.create_from_options(
        vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
        )
    )


def _segmenter() -> vision.ImageSegmenter:
    model = MODELS / "selfie_segmenter.tflite"
    if not model.exists():
        sys.exit(f"missing {model}. See the module docstring for the fetch URL.")
    return vision.ImageSegmenter.create_from_options(
        vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.IMAGE,
            output_category_mask=True,
        )
    )


def crown_row(mask: np.ndarray) -> int | None:
    """Topmost row carrying a foreground run of >= MIN_RUN px. crown.swift's rule."""
    for y in range(mask.shape[0]):
        row = mask[y]
        if row.sum() < MIN_RUN:
            continue
        # Longest consecutive run in this row.
        best = run = 0
        for v in row:
            run = run + 1 if v else 0
            best = max(best, run)
        if best >= MIN_RUN:
            return y
    return None


def measure(path: Path, landmarker, segmenter) -> dict | None:
    bgr = cv2.imread(str(path))
    if bgr is None:
        return None
    h, w = bgr.shape[:2]
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    seg = segmenter.segment(image)
    # numpy_view() is (H, W, 1); squeeze the channel or every row indexes wrong.
    mask = np.asarray(seg.category_mask.numpy_view()).squeeze()
    # Polarity is the opposite of what the name suggests: this model labels the
    # PERSON 0 and the background 255. Verified by checking row 0 of a real
    # frame, which is entirely wall and comes back 255. Getting this backwards
    # reports crown y0 on every frame, which looks plausible enough in a CSV to
    # ship a cropped skull.
    fg = (mask == 0).astype(np.uint8)

    crown = crown_row(fg)
    if crown is None:
        return None

    band_bot = min(h, crown + int(h * HEAD_BAND_FRAC))
    band = fg[crown:band_bot]
    xs = np.where(band.any(axis=0))[0]
    if xs.size == 0:
        return None
    head_l, head_r = int(xs.min()), int(xs.max())

    res = landmarker.detect(image)
    chin = face_top = face_bot = None
    if res.face_landmarks:
        pts = res.face_landmarks[0]
        chin = pts[CHIN_LANDMARK].y
        ys = [p.y for p in pts]
        face_top, face_bot = min(ys), max(ys)

    return {
        "file": path.name,
        "crownY": crown / h,
        "chinY": chin,
        "headCX": ((head_l + head_r) / 2) / w,
        "headL": head_l / w,
        "headR": head_r / w,
        "faceTop": face_top,
        "faceBot": face_bot,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stills", type=Path, help="directory of frames")
    ap.add_argument("--csv", type=Path, help="write here instead of stdout")
    args = ap.parse_args()

    frames = sorted(p for p in args.stills.iterdir()
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not frames:
        sys.exit(f"no frames in {args.stills}")

    cols = ["file", "crownY", "chinY", "headCX", "headL", "headR", "faceTop", "faceBot"]
    lines = [",".join(cols)]

    landmarker, segmenter = _landmarker(), _segmenter()
    missed = 0
    for f in frames:
        row = measure(f, landmarker, segmenter)
        if row is None:
            missed += 1
            continue
        lines.append(",".join(
            row[c] if c == "file" else ("" if row[c] is None else f"{row[c]:.6f}")
            for c in cols
        ))

    out = "\n".join(lines) + "\n"
    if args.csv:
        args.csv.write_text(out, encoding="utf-8")
        print(f"{len(lines)-1} frames measured, {missed} without a usable mask -> {args.csv}",
              file=sys.stderr)
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
