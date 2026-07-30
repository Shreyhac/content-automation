#!/usr/bin/env python3
"""vid47 — capture the real product surfaces + real GitHub repo headers."""
import os, sys
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
os.makedirs(OUT, exist_ok=True)

# name, url, scroll_y, full_page
PAGES = [
    ("live-coolify",    "https://coolify.io/",                    0,    True),
    ("live-coolify-2",  "https://coolify.io/",                    1200, False),
    ("live-maxun",      "https://www.maxun.dev/",                 0,    True),
    ("live-browseruse", "https://browser-use.com/",               0,    True),
    ("live-langflow",   "https://www.langflow.org/",              0,    True),
    ("live-langflow-2", "https://www.langflow.org/",              900,  False),
    ("live-supabase",   "https://supabase.com/",                  0,    True),
    ("live-supabase-db","https://supabase.com/database",          600,  False),
    ("live-supabase-au","https://supabase.com/auth",              600,  False),
    ("live-dify",       "https://dify.ai/",                       0,    True),
    ("live-crawl4ai",   "https://crawl4ai.com/",                  0,    True),
    ("live-stirling",   "https://stirling.com/",                  0,    True),
    ("live-openhands",  "https://openhands.dev/",                 0,    True),
    ("live-openwebui",  "https://openwebui.com/",                 0,    True),
]

REPOS = [
    ("gh-coolify",   "https://github.com/coollabsio/coolify"),
    ("gh-openhands", "https://github.com/OpenHands/OpenHands"),
    ("gh-maxun",     "https://github.com/getmaxun/maxun"),
    ("gh-openwebui", "https://github.com/open-webui/open-webui"),
    ("gh-browseruse","https://github.com/browser-use/browser-use"),
    ("gh-langflow",  "https://github.com/langflow-ai/langflow"),
    ("gh-supabase",  "https://github.com/supabase/supabase"),
    ("gh-stirling",  "https://github.com/Stirling-Tools/Stirling-PDF"),
    ("gh-crawl4ai",  "https://github.com/unclecode/crawl4ai"),
    ("gh-dify",      "https://github.com/langgenius/dify"),
]

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900},
                        device_scale_factor=2, color_scheme="dark")
    pg = ctx.new_page()

    for name, url, sy, full in PAGES:
        try:
            pg.goto(url, wait_until="networkidle", timeout=45000)
        except Exception as e:
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=30000)
            except Exception as e2:
                print(f"FAIL {name}: {e2}"); continue
        pg.wait_for_timeout(2600)
        if sy:
            pg.mouse.wheel(0, sy); pg.wait_for_timeout(1400)
        try:
            pg.screenshot(path=os.path.join(OUT, name + ".png"), full_page=full)
            print("ok", name)
        except Exception as e:
            print(f"SHOTFAIL {name}: {e}")

    ctx2 = b.new_context(viewport={"width": 1440, "height": 1000},
                         device_scale_factor=2, color_scheme="dark")
    pg2 = ctx2.new_page()
    for name, url in REPOS:
        try:
            pg2.goto(url, wait_until="domcontentloaded", timeout=45000)
            pg2.wait_for_timeout(2600)
            pg2.screenshot(path=os.path.join(OUT, name + ".png"))
            print("ok", name)
        except Exception as e:
            print(f"FAIL {name}: {e}")
    b.close()
print("done")
