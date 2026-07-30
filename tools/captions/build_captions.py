#!/usr/bin/env python3
"""Generate caption clips (HTML) for one vid46 chunk from the word-level transcript.

usage: python3 build_captions.py <chunk_start> <chunk_end> <prefix> [mute_ranges]
  mute_ranges: comma list of absolute a-b spans where an on-screen card already
               states the words, so the caption is suppressed (the vid39 rule —
               never print the same words twice in one frame).

Captions are GENERATED, never hand-typed: the only way they can stay in sync with
the VO across 709 words is to come from the same timing data the edit is cut to.
"""
import json, sys, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, 'transcript.json')))

# --- whisper corrections, proofed against the live sources -------------------
# Whisper hears his own name and the coupon as "NAUTTER"/"NAUTER"; incogni.com/nader
# returns 200 and the partner page reads "Use coupon code NADER at checkout".
SEQ_FIX = [
    (['NAUTTER'],            ['NADER']),
    (['NAUTER'],             ['NADER']),
    (['NAUTTER,'],           ['NADER,']),
    (['Nauter'],             ['NADER']),
    (['Nautter'],            ['NADER']),
    (['in', 'Cogniz'],       ['Incogni']),
    (['Cogniz'],             ['Incogni']),
    (['Incogni,'],           ['Incogni,']),
    (['Aura,'],              ['Aura,']),
]
WORD_FIX = {
    'incogni': 'Incogni', 'aura': 'Aura', 'nautter': 'NADER', 'nauter': 'NADER',
    'deloitte': 'Deloitte', 'eff': 'EFF',
}

# Words rendered in BLUE (the system accent). Rationed: brand names and quantities.
BLUE = re.compile(
    r'^(incogni|deloitte|nader|[^a-z]*[\$€]?\d[\d,\.]*[a-z%\+]*)[\.,\?!:;]?$', re.I)
# Words rendered in GREEN (removed / verified / winner).
GREEN = re.compile(r'^(removal|removals|removed|verified|guarantee|free)[\.,\?!:;]?$', re.I)

MAXCHARS = 42
MAXWORDS = 7

# Whisper emits "$7.99" as the two tokens "$7" + ".99" and "30-day" as "30" + "-day".
# Joining the stream with a plain space then prints "$7 .99" and "30 -day", which
# shipped into c5/c6/c8 and reads as a typo at 4K. A token that OPENS with attaching
# punctuation belongs to the word before it: no space, and never across a clip break.
CONT = re.compile(r"^[.,;:!?)\]%'’–—-]")


def fix_word_stream(ws):
    out, i = [], 0
    while i < len(ws):
        hit = False
        for src, dst in SEQ_FIX:
            n = len(src)
            if [w['word'] for w in ws[i:i + n]] == src:
                a, b = ws[i]['start'], ws[i + n - 1]['end']
                step = (b - a) / max(1, len(dst))
                for k, t in enumerate(dst):
                    out.append({'word': t, 'start': a + k * step, 'end': a + (k + 1) * step})
                i += n; hit = True; break
        if hit:
            continue
        w = dict(ws[i])
        bare = re.sub(r'[^A-Za-z]', '', w['word']).lower()
        if bare in WORD_FIX:
            w['word'] = re.sub(re.escape(bare), WORD_FIX[bare], w['word'], flags=re.I)
        out.append(w); i += 1
    return out


def group(ws):
    """Break the stream into caption clips on punctuation, length and pauses."""
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        txt = ' '.join(x['word'] for x in cur)
        gap = (ws[i + 1]['start'] - w['end']) if i + 1 < len(ws) else 99
        # never break between a word and its attaching tail — "money" / "-back"
        # split across two clips left c5cap8 opening on a bare hyphen
        if i + 1 < len(ws) and CONT.match(ws[i + 1]['word']):
            continue
        if (len(txt) >= MAXCHARS or len(cur) >= MAXWORDS
                or re.search(r'[\.\?!]$', w['word']) or gap > 0.34):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def render(cur):
    parts = []
    for w in cur:
        t = html.escape(w['word'])
        if BLUE.match(w['word']):
            frag = '<b>%s</b>' % t
        elif GREEN.match(w['word']):
            frag = '<i>%s</i>' % t
        else:
            frag = t
        # splitWords() glues a token with no whitespace before it onto the previous
        # mask, so emitting it unspaced also keeps the pair rising as ONE word
        parts.append(frag if (parts and CONT.match(w['word'])) else ' ' + frag)
    return ''.join(parts).lstrip()


def main():
    a, b, prefix = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    mutes = []
    if len(sys.argv) > 4 and sys.argv[4].strip():
        for span in sys.argv[4].split(','):
            lo, hi = span.split('-')
            mutes.append((float(lo), float(hi)))

    ws = fix_word_stream([w for w in WORDS if w['end'] > a and w['start'] < b])
    n = 0
    for cur in group(ws):
        st, en = cur[0]['start'], cur[-1]['end']
        if any(st < hi and en > lo for lo, hi in mutes):
            continue
        st = max(st, a); en = min(en, b)
        if en - st < 0.10:
            continue
        n += 1
        print('  <div id="%scap%d" class="cap clip" data-start="%.2f" data-duration="%.2f" '
              'data-track-index="9">%s</div>'
              % (prefix, n, st - a, en - st, render(cur)))


if __name__ == '__main__':
    main()
