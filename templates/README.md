# Templates

Four templates, four complete systems. **The template's rules override every general rule in
this repo**, including `CLAUDE.md` and `docs/`.

| Folder | Grammar | Format |
|---|---|---|
| `longform-chunked/` | Chunked long-form: scripted episodes rendered and revised chunk by chunk | 16:9 YouTube long-form plus 9:16 cutdowns |
| `paper-split/` | Paper ground with a split-screen presenter and premium motion | 9:16 Instagram Reels |
| `card-reel/` | Paper ground with a floating presenter card and machine-event scenes | 9:16 Instagram Reels |
| `fast-cut-ad/` | Sub-1.5s static crop-cuts for a client product, not a personal channel | 9:16 paid Meta ads |

Each folder has:

- **`PROFILE.md`** What the template is, its hard rules, its delivery requirements. Read first.
- **`GRAMMAR.md`** The approved visual system with measured numbers. Read second.
- **`HISTORY.md`** Every shipped video and what each review round changed. Read the last two
  entries before starting anything new: the most recent approved grammar supersedes older ones.

---

## Identify the template from the footage, not from the brief

A brief has arrived under one template carrying another template's A-roll. The footage
decides the entire system, so settle this before any work.

```bash
ffmpeg -i aroll.mp4 -vf fps=1 -frames:v 12 /tmp/sheet%02d.jpg
```

Compare against `reference-cuts/`. Room, framing and wardrobe settle it in one look.

**`paper-split` and `card-reel` are two different presenters in two different rooms.** Older
files sometimes use legacy folder names for them. Do not merge the two systems: their face
geometry, theme and motion grammar are separately derived and are not interchangeable.

---

## Two rules that apply to all four

1. **No em dashes** in on-screen text, captions or published copy. Grep before every delivery.
2. **Match the raw A-roll's file size on delivery** for the two Instagram Reels templates. See
   `docs/06-delivery.md`. `longform-chunked` is exempt, and `fast-cut-ad` pins a bitrate floor
   instead (`templates/fast-cut-ad/PROFILE.md`).

---

## Work in flight, unassigned

`vid45` (a face-swap tutorial rebuild, 9:16, Michael Jackson swap taught on Masonry) was
in progress when this repo was split out and its target template was never recorded. If it
resurfaces, confirm the template from the A-roll before applying any system here. Source material
stays in the original repo.
