#!/usr/bin/env python3
"""Otwiera Chromium z trwalym profilem (~/.yt-upload-profile) na YouTube Studio.
Zaloguj sie recznie, potem zamknij okno: sesja zostaje w profilu dla yt_upload.py."""
from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE = Path.home() / ".yt-upload-profile"
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE), headless=False, viewport={"width": 1280, "height": 860},
        ignore_default_args=["--enable-automation"],
        args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://studio.youtube.com")
    print("OKNO OTWARTE - zaloguj sie i zamknij okno", flush=True)
    try:
        page.wait_for_event("close", timeout=0)
    except Exception:
        pass
    ctx.close()
