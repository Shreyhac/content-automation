#!/usr/bin/env python3
"""Collect Pexels video candidates for vid46's six b-roll themes.

Pexels rate-limits to roughly ONE search per browser session: the second query in a
reused context comes back empty or challenged. So every query gets its own
sync_playwright() block and a ~20s gap, which is the only pattern that has worked here.

Writes vid46/broll/pexels.json — {theme: [ids...]} — for pexels_fetch.py to download.
"""
import json, os, re, sys, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "broll")
os.makedirs(OUT, exist_ok=True)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# One theme per act. Each must connect to the line it plays under — the vid39 rule:
# b-roll that does not illustrate the claim is worse than no b-roll.
THEMES = {
    "brokers":   "server room data center racks",       # A2 — where the records live
    "collect":   "woman shopping online phone credit card",  # A2 — how it gets collected
    "buyers":    "call center telemarketing office",    # A2 — who buys it
    "bundle":    "laptop screen night working alone",   # A4 — the security bundle
    "pricing":   "credit card payment closeup hands",   # A5 — the price act
    "outro":     "crowd walking street anonymous",      # A8 — your data is already out there
}


def search(theme, query):
    ids = []
    with sync_playwright() as p:
        b = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"])
        ctx = b.new_context(user_agent=UA, viewport={"width": 1440, "height": 2400},
                            locale="en-US")
        pg = ctx.new_page()
        url = "https://www.pexels.com/search/videos/%s/?orientation=landscape" % (
            query.replace(" ", "%20"))
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(4500)
            pg.mouse.wheel(0, 4000)
            pg.wait_for_timeout(2500)
            html = pg.content()
            # /video/<slug>-<id>/ is the canonical result link
            for m in re.finditer(r"/video/[a-z0-9\-]*?(\d{5,9})/", html):
                i = m.group(1)
                if i not in ids:
                    ids.append(i)
        except Exception as e:
            print("  !! %s: %s" % (theme, e), flush=True)
        b.close()
    return ids


def main():
    path = os.path.join(OUT, "pexels.json")
    data = json.load(open(path)) if os.path.exists(path) else {}
    todo = [t for t in THEMES if not data.get(t)]
    for n, theme in enumerate(todo):
        if n:
            time.sleep(21)
        ids = search(theme, THEMES[theme])
        print("%-9s %-46s -> %d ids  %s" % (theme, THEMES[theme], len(ids), ids[:12]),
              flush=True)
        data[theme] = ids[:14]
        json.dump(data, open(path, "w"), indent=1)
    print("wrote %s" % path, flush=True)


if __name__ == "__main__":
    main()
