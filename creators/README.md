# Creators

Three creators, three complete systems. **The creator's rules override every general rule in
this repo**, including `CLAUDE.md` and `docs/`.

| Folder | Channel | Format |
|---|---|---|
| `nader/` | Nader Nadernejad, Nadernejad Media | 16:9 YouTube long-form plus 9:16 cutdowns |
| `gaurav/` | thepmfguy, also called "gaurav" | 9:16 Instagram Reels |
| `shreyansh/` | shreyansharora05, the "slot 1" creator | 9:16 Instagram Reels |

Each folder has:

- **`PROFILE.md`** Who they are, their hard rules, their delivery requirements. Read first.
- **`GRAMMAR.md`** The approved visual system with measured numbers. Read second.
- **`HISTORY.md`** Every shipped video and what each review round changed. Read the last two
  entries before starting anything new: the most recent approved grammar supersedes older ones.

---

## Identify the creator from the footage, not from the brief

A brief has arrived from one creator's account carrying another creator's A-roll. The footage
decides the entire system, so settle this before any work.

```bash
ffmpeg -i aroll.mp4 -vf fps=1 -frames:v 12 /tmp/sheet%02d.jpg
```

Compare against `reference-cuts/`. Room, framing and wardrobe settle it in one look.

**"thepmfguy" and "gaurav" are the same person.** Older files use both names. Do not confuse
either with the slot-1 creator (shreyansharora05), who is a different person.

---

## Two rules that apply to all three

1. **No em dashes** in on-screen text, captions or published copy. Grep before every delivery.
2. **Match the raw A-roll's file size on delivery** for the two Instagram creators. See
   `docs/06-delivery.md`.

---

## Work in flight, unassigned

`vid45` (a face-swap tutorial rebuild, 9:16, Michael Jackson swap taught on Masonry) was
in progress when this repo was split out and its target creator was never recorded. If it
resurfaces, confirm the creator from the A-roll before applying any system here. Source material
stays in the original repo.
