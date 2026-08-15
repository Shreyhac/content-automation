# `deliver/`

## The CTA document is a required deliverable

If the script says **"comment AGENT and I'll send you the link"**, the thing you send is a
deliverable at **first delivery**, alongside the MP4 and the caption. Not later, not when
the owner asks for it. The reel starts collecting comments the hour it posts, and until the doc
exists there is nothing to send.

```bash
python3 tools/deliver/make_cta_doc.py hf67/cta.json -o out/vid67-launch-your-agent.docx

# python-docx needs the homebrew expat shim on this machine:
DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib python3 tools/deliver/make_cta_doc.py ...
```

`cta.example.json` is the real vid67 payload, kept as the worked example. Copy it and
replace the content.

## What the doc is actually for

It is where the reel's overstatements get corrected. A hook is allowed to be a hook; the
document is what the viewer acts on, so it carries the caveats forty seconds could not.
Every one of these was a real correction:

- **vid64**: the blog said `masonry init claude-code`; the CLI itself marks `init`
  deprecated. The doc taught the current command.
- **vid65**: the MCP server runs on Bun. The reel never mentions it, and it is the single
  most likely reason someone follows the six commands and gets nothing.
- **vid67**: the VO says "without ever touching the terminal" and the repo's own
  Quickstart is three terminal commands. The doc says so in its **first** section rather
  than burying it, and adds that runs cost money, because the reference reel's own
  recording fails on "your credit balance is too low" while its voiceover says the agent
  deployed.

So: the honest caveats come **second**, right after the one-line what-it-is, never at the
bottom where nobody reads. The `rich` block with a bold lead-in exists for that ("You will
use the terminal. ...") because a caveat reads as a caveat only when the first three words
are bold.

**Every claim is read out of the primary source on the day it is written**: the repo via
the GitHub API, the CLI's own `--help`, the product's own docs. Never from memory, never
from the reference video, never from third-party posts. Put the provenance in the JSON's
`sources` field, and the verification date in `footer_note`. It prints nowhere useful; it
is there so the next person knows what was checked and when. A doc that was true in June
is a support ticket in August.

## Content schema

Top level: `keyword`, `out`, `sources`, `title`, `subtitle`, `blocks`, `footer_link`,
`footer_note`.

| Block | Fields |
|---|---|
| `h` | `text`, a 16pt bold terracotta heading |
| `h3` | `text`, 12pt bold |
| `para` | `text`, `after`, `italic`, `color` (`ink`/`mute`/`accent`) |
| `rich` | `parts`: `[["bold lead-in ", true], ["the rest", false]]` |
| `bullet` | `text`, or `parts` for a bold lead-in |
| `step` | `text`, numbered |
| `code` | `lines`, Consolas 10.5 indented 0.25in |
| `table` | `header`, `rows`, `widths`, `mono_col` |
| `space` | `after` |

## House format, locked across the portfolio

US Letter, 1.25in side margins, Calibri 11pt body at 1.15 line spacing, 28pt bold title,
16pt bold headings in terracotta `#B24A32` (the palette terracotta darkened for print),
Consolas 10.5pt for code, ink `#1A1A17`, mute `#6E685C`. Do not restyle per film: the
docs go to the same audience and they should look like one series.
