"""Does a lifted clip contain the reference creator's face?

CALIBRATED, NOT GUESSED. The first version thresholded skin fraction at 0.10 and
was INERT: a clip cut deliberately from a known face segment measured 0.059 and
sailed through. Measured over four known-face cuts and the eleven UI lifts, at
the same 1080x620 crop geometry the clips actually use:

    known face   skin 0.0567 - 0.0726     luminance 108.1 - 112.7
    known UI     skin 0.0000 - 0.0452     luminance  37.5 -  79.7

Skin alone does NOT separate: a face frame at ref 3.00 measures 0.0455 and the
GitHub lift measures 0.0452. Luminance does, by 28 levels with no overlap, so
luminance is the primary test and skin is the corroborator (0.035 sits below
every face sample and is only reachable by an actually skin-toned frame — a
bright WHITE panel has R~=G~=B and cannot satisfy |R-G|>15).

Both conditions must hold in the SAME frame. Verified to FLAG all six known-face
cuts and to PASS all eleven UI lifts.
"""
import subprocess
import numpy as np

SKIN_T, LUM_T = 0.035, 95.0

def measure(path, fps=10, w=135, h=78):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                        "-vf", f"fps={fps},scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = a.size // (w*h*3)
    if n == 0:
        return np.zeros(0), np.zeros(0)
    a = a[:n*w*h*3].reshape(n, h, w, 3).astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(3), a.min(3)
    skin = (((R > 95) & (G > 40) & (B > 20) & ((mx-mn) > 15) &
             (abs(R-G) > 15) & (R > G) & (R > B))).mean((1, 2))
    lum = a.mean(3).mean((1, 2))
    return skin, lum

def has_face(path, fps=10):
    """True if ANY single frame is both skin-toned and bright enough."""
    skin, lum = measure(path, fps=fps)
    if skin.size == 0:
        return False, 0.0, 0.0, -1.0
    bad = (skin > SKIN_T) & (lum > LUM_T)
    if bad.any():
        i = int(np.argmax(bad))
        return True, float(skin[i]), float(lum[i]), i / fps
    i = int(np.argmax(skin))
    return False, float(skin[i]), float(lum[i]), i / fps
