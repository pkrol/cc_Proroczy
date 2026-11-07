#!/usr/bin/env python3
"""Tworzy niepubliczna playliste i dodaje do niej wskazane filmy (id z linku youtu.be), ustawia je jako niepubliczne.
Uzycie: python3 yt_setup_playlist.py YoIK5ZAAb7U a91r1YQAakY   (pierwszy film tworzy playliste)"""
import re, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
SH = Path(__file__).parent / "shots"; NAME = "Proroczy jak Jezus (audiobook)"
def edit(page, vid, create):
    page.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="networkidle"); page.wait_for_timeout(3000)
    t = page.locator("ytcp-video-metadata-playlists ytcp-dropdown-trigger").first
    t.scroll_into_view_if_needed(); t.click(); page.wait_for_timeout(1500)
    if create:
        page.get_by_role("button", name=re.compile("Nowa playlista")).first.click(); page.wait_for_timeout(800)
        page.get_by_text("Nowa playlista", exact=True).last.click(); page.wait_for_timeout(1200)
        tb = page.get_by_role("textbox"); tb.nth(tb.count() - 2).fill(NAME)
        page.get_by_text("Publiczna", exact=True).first.click(); page.wait_for_timeout(600)
        page.get_by_role("option", name=re.compile("Niepubliczna")).first.click(); page.wait_for_timeout(500)
        page.get_by_text(re.compile("Data opublikowania")).first.click(); page.wait_for_timeout(600)
        page.get_by_role("option", name=re.compile("Data dodania \\(od najstarszego\\)")).first.click(); page.wait_for_timeout(500)
        page.screenshot(path=str(SH / "sp_1_formularz.png"))
        assert page.locator("text=Niepubliczna >> visible=true").count() >= 1, "widocznosc playlisty != niepubliczna"
        page.get_by_role("button", name="Utwórz").last.click(); page.wait_for_timeout(3000)
    else:
        page.get_by_text(NAME, exact=True).first.click(); page.wait_for_timeout(800)
    page.screenshot(path=str(SH / f"sp_2_{vid}_wybrana.png"))
    page.get_by_role("button", name="Gotowe").last.click(); page.wait_for_timeout(800)
    page.locator("ytcp-video-metadata-visibility").first.click(); page.wait_for_timeout(1200)
    page.locator("[name=UNLISTED]").first.click(); page.wait_for_timeout(400)
    page.get_by_role("button", name="Gotowe").last.click(); page.wait_for_timeout(1500)
    page.get_by_role("button", name="Zapisz").first.click(); page.wait_for_timeout(4000)
    page.screenshot(path=str(SH / f"sp_3_{vid}_zapisane.png"))
    print("OK", vid, flush=True)
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(str(Path.home() / ".yt-upload-profile"), headless=False, viewport={"width": 1280, "height": 860},
        ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    for i, vid in enumerate(a for a in sys.argv[1:] if not a.startswith('--')):
        try: edit(page, vid, create=(i == 0 and '--new' in sys.argv))
        except Exception as e:
            page.screenshot(path=str(SH / f"sp_BLAD_{vid}.png")); print("BLAD", vid, repr(e)[:300]); break
    ctx.close()
