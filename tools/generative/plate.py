#!/usr/bin/env python3
"""plate.py, image to video and talking avatar generation through FAL.

    python3 tools/generative/plate.py avatar    plate.jpg vo.mp3 out.mp4
    python3 tools/generative/plate.py avatar4   plate.jpg vo.mp3 out.mp4 --style expressive
    python3 tools/generative/plate.py omnihuman plate.jpg vo.mp3 out.mp4
    python3 tools/generative/plate.py lipsync   clip.mp4  vo.mp3 out.mp4
    python3 tools/generative/plate.py i2v       still.jpg out.mp4 --last-image approved.jpg

Key: read from the environment only.

    export FAL_KEY=...

`fal_client` is imported lazily, so --help and --dry-run work on a machine that
has never installed it.

WHICH MODEL, measured on the same plate and the same audio:

  HeyGen Avatar IV `expressive`   the LEAST expressive option available, despite
                                  the name.
  OmniHuman v1.5                  wins lip-sync on a neutral plate, then drifts
                                  the background in the last third.
  Kling ai-avatar/v2/pro          holds the room locked.

Pick for the failure you cannot fix in post. Background drift is unfixable; a
slightly softer lip-sync is not visible at reel scale.

AND THE PLATE DECIDES THE PERFORMANCE. The instinct when a generated
performance is flat is to change the video model. The input still was the
problem. Regenerating the plate as mid-sentence and engaged, brows lifted,
mouth open mid-word, eyes live, lifted brow motion +17% and lip-sync +8% on the
same model with the same audio. A deadpan plate produces a deadpan clip,
whatever the model. But asking an image model for a new expression makes it
silently redress the room: two of three variants did, so diff the background
against the approved plate, not just the face (see drift.py --ref-image).

Cost and latency, recorded on the Demi UGC build 2026 at FAL list price:
Kling ai-avatar v2 pro about $1.40 for a 10s clip, 4 to 9 minutes in queue.
HeyGen Avatar IV similar money, 3 to 6 minutes. Budget a failed take per beat.
"""
import argparse
import json
import os
import subprocess
import urllib.request

QUEUE = "https://queue.fal.run"

ENDPOINTS = {
    "avatar":    "fal-ai/kling-video/ai-avatar/v2/pro",
    "avatar4":   "fal-ai/heygen/avatar4/image-to-video",
    "lipsync":   "fal-ai/kling-video/lipsync/audio-to-video",
    # OmniHuman has been renamed under FAL more than once. Try the list in
    # order rather than hardcoding one name and losing a session to a 404.
    "omnihuman": ["fal-ai/bytedance/omnihuman/v1.5",
                  "fal-ai/bytedance/omnihuman",
                  "fal-ai/omnihuman/v1.5"],
}

# i2v models, and the ONE property that picks between them. Kling 2.6 i2v has
# no last-image control; seedance does. Pick for the keyframe control, not the
# house habit: the only way to generate a shot that ENDS on an approved take's
# first frame is a model that takes a last image.
I2V = {
    "seedance": dict(endpoint="fal-ai/bytedance/seedance/v1/pro/image-to-video",
                     last_image=True),
    "kling":    dict(endpoint="fal-ai/kling-video/v2.6/pro/image-to-video",
                     last_image=False),
}

# The identity and lock-off block. Every clause here is load bearing: without
# the PRESERVE sentence the model beautifies the face, without the background
# sentence it redresses the room, without the locked-off sentence it invents a
# push-in that no cut in the timeline expects.
IDENTITY_PROMPT = (
    "The SAME person from the input image speaks warmly and conversationally "
    "straight to camera, natural friendly expression, subtle believable "
    "lip-sync to the audio. Relaxed confident delivery with small natural head "
    "movement and gentle eyebrow and cheek motion; they blink naturally. Calm, "
    "candid, authentic UGC energy, not stiff, not exaggerated. "
    "PRESERVE THE EXACT FACE AND IDENTITY at all times: identical facial "
    "structure, face shape, jawline, cheekbones, nose, eyes, eyebrows, lips, "
    "skin tone and hairstyle as the input photo. Do NOT reshape, slim, "
    "beautify, morph, age or change the face in any frame. Keep the head and "
    "shoulders in the SAME position and the SAME framing as the photo. Keep "
    "the background completely stable and identical to the photo. "
    "Locked-off camera, no zoom, no pan, no cuts."
)

# i2v has no audio, so it gets its own default: the avatar block's lip-sync
# clauses are noise to a model that is not being handed a voice track, and a
# prompt that asks for speech from a silent generation buys mouth flapping.
I2V_PROMPT = (
    "The SAME person and the SAME room as the input image, continuing to move "
    "naturally. Subtle believable motion only: small head movement, natural "
    "blinks, gentle shifts of weight. "
    "PRESERVE THE EXACT FACE AND IDENTITY at all times: identical facial "
    "structure, jawline, nose, eyes, eyebrows, lips, skin tone and hairstyle "
    "as the input photo. Do NOT reshape, slim, beautify, morph or age the "
    "face. Hands and arms hold their position; no limb crosses or uncrosses. "
    "The background is identical to the photo and completely stable. "
    "Locked-off camera, no zoom, no pan, no cuts."
)

# The default negative prompt exists because Kling's reference image drags the
# REFERENCE POSE along with the likeness, and a held pose then drifts mid-clip
# in the opposite direction: on vid15 her arms uncrossed and a hand melted into
# her sweater within 1 second. Name the target pose in the prompt AND the
# reference pose in the negative prompt. Both halves, or neither works.
DEFAULT_NEGATIVE = ("changing pose, arms moving, hands morphing, extra fingers, "
                    "extra face, camera zoom, camera pan, cut, background change, "
                    "face morphing, beautification")


def fal_key():
    k = os.environ.get("FAL_KEY")
    if not k:
        raise SystemExit("FAL_KEY is not set. Export it; do not put it in a file.")
    return k


def load_prompt(a, default):
    if getattr(a, "prompt_file", None):
        with open(a.prompt_file) as f:
            return f.read().strip()
    return getattr(a, "prompt", None) or default


def emit(endpoint, args, out):
    eps = endpoint if isinstance(endpoint, list) else [endpoint]
    for ep in eps:
        print(f"POST {QUEUE}/{ep}")
    print("  Authorization: Key <from FAL_KEY>")
    print("  Content-Type: application/json")
    print(json.dumps(args, indent=2))
    print(f"  -> would download the result video to {out}\n")


def submit(endpoint, args, out, upload_map):
    """upload_map: {argument_name: local_path} uploaded and substituted."""
    fal_key()
    import fal_client                      # lazy: keeps --dry-run dependency free

    for arg_name, path in upload_map.items():
        print(f"uploading {path} ...")
        args[arg_name] = fal_client.upload_file(path)

    def on_q(u):
        for log in getattr(u, "logs", []) or []:
            print("  ", log.get("message", ""))

    eps = endpoint if isinstance(endpoint, list) else [endpoint]
    last = None
    for ep in eps:
        try:
            print("submitting", ep)
            r = fal_client.subscribe(ep, arguments=args, with_logs=True,
                                     on_queue_update=on_q)
            v = r.get("video") or (r.get("videos") or [{}])[0]
            url = v.get("url") if isinstance(v, dict) else v
            print("video url:", url)
            urllib.request.urlretrieve(url, out)
            print("SAVED", out, "via", ep)
            return out
        except Exception as exc:                       # noqa: BLE001
            last = exc
            print("  failed:", str(exc)[:160])
    raise SystemExit(f"all endpoints failed: {last}")


def fit(path, spec):
    """Scale-then-crop into a delivery frame, lanczos, keyframe every 15.

    Scale to the frame's width and slightly OVER its height, then crop. A
    direct scale to 1080x1920 from a 9:16-ish generation letterboxes by a few
    pixels and the black edge survives every gate.
    """
    w, h = (int(v) for v in spec.lower().split("x"))
    over = h + 14
    out = path.rsplit(".", 1)[0] + f"-{w}x{h}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-vf",
                    f"scale={w}:{over}:flags=lanczos,crop={w}:{h}", "-r", "30",
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
                    "-g", "15", "-keyint_min", "15", "-c:a", "aac",
                    "-b:a", "192k", out], check=True)
    print("SAVED", out)
    return out


def run(a, endpoint, args, out, uploads):
    if a.dry_run:
        # Show the local paths where the uploaded URLs will go, so the body you
        # read is the body that gets sent apart from the substitution.
        shown = dict(args)
        for name, path in uploads.items():
            shown[name] = f"<uploaded {os.path.abspath(path)}>"
        emit(endpoint, shown, out)
        return
    submit(endpoint, args, out, uploads)
    if a.fit:
        fit(out, a.fit)


def cmd_avatar(a):
    run(a, ENDPOINTS["avatar"],
        {"prompt": load_prompt(a, IDENTITY_PROMPT)}, a.out,
        {"image_url": a.image, "audio_url": a.audio})


def cmd_avatar4(a):
    run(a, ENDPOINTS["avatar4"],
        {"talking_style": a.style, "aspect_ratio": a.aspect,
         "resolution": a.resolution, "caption": False}, a.out,
        {"image_url": a.image, "audio_url": a.audio})


def cmd_omnihuman(a):
    run(a, ENDPOINTS["omnihuman"],
        {"prompt": load_prompt(a, IDENTITY_PROMPT)}, a.out,
        {"image_url": a.image, "audio_url": a.audio})


def cmd_lipsync(a):
    """Lip-sync an EXISTING clip to new audio.

    Reach for this before regenerating. Re-mastering audio onto an approved
    picture saves a full generation per audio revision and keeps a picture the
    client has already signed off. If only the master changed and not the
    words, do not even lip-sync: mux with -c:v copy and re-seat by
    cross-correlating against the old track (+10 ms on the case that produced
    this rule).
    """
    run(a, ENDPOINTS["lipsync"], {}, a.out,
        {"video_url": a.video, "audio_url": a.audio})


def cmd_i2v(a):
    """Plain image to video, with the last-image keyframe.

    The backwards-extension trick: when a note asks for an earlier shot to
    cover a gap and there is no footage left, generate a take that ENDS on the
    approved take's first frame. Pass a slightly tighter crop of the source
    still as --image and the source still itself as --last-image. Because the
    approved take was i2v'd from that same still, its frame 0 IS the still, so
    the two clips join with no cut at all: measured average colour across the
    join 86766b against 877569, one to two levels per channel. The start frame
    is a real crop of the source, never an outpaint, so nothing is invented at
    either end.

    The cost of --last-image: setting it to the INPUT still also forces the
    framing to return, which kills a push-in that a negative prompt could not.
    """
    spec = I2V.get(a.model)
    if not spec:
        raise SystemExit(f"--model must be one of {', '.join(I2V)}")
    endpoint = a.endpoint or spec["endpoint"]
    if a.last_image and not spec["last_image"]:
        raise SystemExit(f"{a.model} has no last-image control. Use --model "
                         f"seedance, which does.")
    if not a.negative_prompt and not a.no_negative:
        raise SystemExit(
            "refusing: no --negative-prompt. Kling's reference drags the "
            "reference POSE along with the likeness, and the fix is both "
            "halves: the target pose in the prompt AND the reference pose "
            "named in the negative prompt. Pass --negative-prompt, or "
            "--no-negative to override deliberately.")
    args = {"prompt": load_prompt(a, I2V_PROMPT),
            "negative_prompt": a.negative_prompt or DEFAULT_NEGATIVE,
            "duration": a.duration, "resolution": a.resolution}
    uploads = {"image_url": a.image}
    if a.last_image:
        uploads["end_image_url"] = a.last_image
    run(a, endpoint, args, a.out, uploads)


def common(p, dry=True):
    p.add_argument("--prompt")
    p.add_argument("--prompt-file")
    p.add_argument("--fit", help="post-encode into a delivery frame, eg 1080x1920")
    if dry:
        p.add_argument("--dry-run", action="store_true")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    a1 = sub.add_parser("avatar", help="Kling ai-avatar v2 pro, holds the room locked")
    a1.add_argument("image")
    a1.add_argument("audio")
    a1.add_argument("out")
    common(a1)
    a1.set_defaults(fn=cmd_avatar)

    a4 = sub.add_parser("avatar4", help="HeyGen Avatar IV, the least expressive option")
    a4.add_argument("image")
    a4.add_argument("audio")
    a4.add_argument("out")
    a4.add_argument("--style", default="expressive", choices=["stable", "expressive"])
    a4.add_argument("--aspect", default="9:16")
    a4.add_argument("--resolution", default="1080p")
    common(a4)
    a4.set_defaults(fn=cmd_avatar4)

    om = sub.add_parser("omnihuman", help="OmniHuman v1.5, best lip-sync, drifts late")
    om.add_argument("image")
    om.add_argument("audio")
    om.add_argument("out")
    common(om)
    om.set_defaults(fn=cmd_omnihuman)

    ls = sub.add_parser("lipsync", help="re-sync an approved clip to new audio")
    ls.add_argument("video")
    ls.add_argument("audio")
    ls.add_argument("out")
    common(ls)
    ls.set_defaults(fn=cmd_lipsync)

    iv = sub.add_parser("i2v", help="image to video, with the last-image keyframe")
    iv.add_argument("image")
    iv.add_argument("out")
    iv.add_argument("--model", default="seedance", choices=sorted(I2V))
    iv.add_argument("--endpoint", help="override a renamed FAL endpoint")
    iv.add_argument("--last-image")
    iv.add_argument("--negative-prompt")
    iv.add_argument("--no-negative", action="store_true")
    iv.add_argument("--duration", default="5")
    iv.add_argument("--resolution", default="1080p")
    common(iv)
    iv.set_defaults(fn=cmd_i2v)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
