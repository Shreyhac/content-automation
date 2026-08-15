"""Model calls: creator identification, beat planning, composition authoring.

The user supplies their own model id and API key per job, so a client is built
per call and never cached. The key is passed in from the in-memory job record
and is never written to disk.

Uses the official Anthropic SDK (`anthropic`), per the project's language.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import anthropic

from config import REPO, TEMPLATES, KNOWN_CREATORS, creator_context, house_rules

DEFAULT_MODEL = "claude-opus-5"

# Thinking is on by default on Opus 5 and max_tokens caps thinking + text
# together, so leave real headroom or the composition truncates mid-scene.
MAX_TOKENS = 32000


def _client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def _call(api_key: str, model: str, *, max_tokens: int, system: str | None, content):
    """One model call.

    Streamed: the SDK refuses a non-streaming request whose max_tokens it
    estimates could exceed the ~10 minute HTTP timeout, and the plan and
    compose calls are well past that line. `.get_final_message()` gives the
    accumulated response without handling individual events.
    """
    kwargs = {
        "model": model or DEFAULT_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        kwargs["system"] = system
    with _client(api_key).messages.stream(**kwargs) as stream:
        return stream.get_final_message()


def _text(response) -> str:
    """Collect the text blocks. Guard stop_reason first: a refusal returns 200
    with empty content, and indexing content[0] would raise."""
    if response.stop_reason == "refusal":
        detail = getattr(response, "stop_details", None)
        raise RuntimeError(f"model declined the request ({getattr(detail, 'category', 'unknown')})")
    return "".join(b.text for b in response.content if b.type == "text")


def _json_from(raw: str) -> dict:
    """Parse a JSON object out of a model response."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def identify_creator(api_key: str, model: str, frames: list[Path]) -> dict:
    """Pipeline stage 0. Compare a contact sheet against the three creators.

    docs/01-pipeline.md: the footage decides the creator, never the brief.
    """
    content: list[dict] = []
    for f in frames[:6]:
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(f.read_bytes()).decode(),
                },
            }
        )
    profiles = "\n\n".join(
        f"## {c}\n{(REPO / 'creators' / c / 'PROFILE.md').read_text(encoding='utf-8', errors='replace')[:2500]}"
        for c in KNOWN_CREATORS
        if (REPO / "creators" / c / "PROFILE.md").exists()
    )
    content.append(
        {
            "type": "text",
            "text": (
                "These frames are from one A-roll. Identify which of the three creators "
                f"below is on camera, using room, framing and wardrobe.\n\n{profiles}\n\n"
                'Reply with JSON only: {"creator": "nader|gaurav|shreyansh", '
                '"confidence": 0.0-1.0, "reasoning": "one sentence"}'
            ),
        }
    )

    r = _call(api_key, model, max_tokens=2000, system=None, content=content)
    data = _json_from(_text(r))
    if data.get("creator") not in KNOWN_CREATORS:
        raise ValueError(f"model returned an unknown creator: {data.get('creator')!r}")
    return data


def plan_beats(api_key: str, model: str, creator: str, transcript: dict, script: str,
               probe: dict, geometry: dict | None = None, breakdown: dict | None = None) -> dict:
    """Pipeline stage 4. Transcript + brief -> a beat plan.

    CLAUDE.md: the audio is the source of truth, so the whisper transcript wins
    over the pasted script wherever they disagree.
    """
    words = transcript.get("words") or []
    word_lines = "\n".join(f"{w['start']:.2f}-{w['end']:.2f} {w['word']}" for w in words[:1200])

    system = (
        "You are the editor described in CLAUDE.md. Produce a beat plan for one video.\n\n"
        + house_rules()[:20000]
        + "\n\n"
        + creator_context(creator)[:30000]
    )
    # The face rules are the most expensive class of mistake in this repo, so
    # the planner is told plainly whether the head was actually measured.
    if geometry:
        geo_block = ("MEASURED HEAD GEOMETRY (Vision, this take, in pixels):\n"
                     + json.dumps(geometry, indent=2)
                     + "\nSolve every rect against these numbers. Never copy constants from another video.")
    else:
        geo_block = ("MEASURED HEAD GEOMETRY: unavailable (Vision tools are macOS only and did not run).\n"
                     "Do NOT invent crown or chin values. Prefer CARD mode beats, where the A-roll owns "
                     "its own rect and graphics never overlap it.")

    ref_block = ""
    if breakdown:
        ref_block = ("\nREFERENCE BREAKDOWN (measured from the supplied reference video, "
                     "match its grammar):\n" + json.dumps(breakdown, indent=2)[:8000] + "\n")

    user = f"""Source A-roll: {probe.get('width')}x{probe.get('height')}, {probe.get('duration')}s, {probe.get('fps')}fps.

{geo_block}
{ref_block}

WHISPER TRANSCRIPT (the source of truth):
{word_lines}

PASTED SCRIPT (may differ from the recorded take; the audio wins):
{script[:6000]}

Produce a beat plan. Scene boundaries land on word onsets with a 0.20s lead.
Nothing static over ~1s. Every beat is either CARD mode or FULL-BLEED mode.

Reply with JSON only:
{{"beats": [{{"index": 0, "start": 0.0, "end": 3.4, "mode": "CARD|FULL_BLEED",
  "line": "the spoken words", "visual": "the physical event to animate",
  "carrier": "the carrier shape"}}],
 "notes": "anything the composer must know"}}"""

    r = _call(api_key, model, max_tokens=MAX_TOKENS, system=system, content=user)
    return _json_from(_text(r))


def compose(api_key: str, model: str, creator: str, plan: dict, aroll_name: str, probe: dict) -> str:
    """Pipeline stage 5. Beat plan -> a HyperFrames composition.

    Scaffolds from library/templates/vertical-reel rather than a blank file,
    per docs/01-pipeline.md stage 4.
    """
    template = (TEMPLATES / "vertical-reel" / "index.html").read_text(encoding="utf-8", errors="replace")
    system = (
        "You are the editor described in CLAUDE.md. Write one HyperFrames composition.\n\n"
        + house_rules()[:20000]
        + "\n\n"
        + creator_context(creator)[:30000]
    )
    user = f"""Scaffold (keep its structure, fonts and conventions):

```html
{template}
```

A-roll: assets/{aroll_name} ({probe.get('width')}x{probe.get('height')}, {probe.get('duration')}s)

BEAT PLAN:
{json.dumps(plan, indent=2)[:20000]}

Rules that have cost render rounds here:
- Every media element needs a stable `id`, or video renders frozen and audio silent.
- Initial hidden states go in `gsap.set()` OUTSIDE the timeline. Never `tl.set(...,0)`.
- Frame 0 is the cover. Compose full-screen scenes roughly y400 to y1500.
- No em dashes anywhere in on-screen text.
- Layout before animation: correct static hero frame per scene, then entrances.

Output the complete index.html and nothing else. No prose, no code fence."""

    r = _call(api_key, model, max_tokens=MAX_TOKENS, system=system, content=user)
    html = _text(r).strip()
    if html.startswith("```"):
        html = re.sub(r"^```(?:html)?\s*|\s*```$", "", html, flags=re.S)
    return html
