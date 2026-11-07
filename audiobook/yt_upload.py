#!/usr/bin/env python3
"""Wgrywa filmy z video/ na YouTube jako PRYWATNE (profil z yt_login.py).
Uzycie: python3 yt_upload.py [--headless] 01 05 07 ...   (numery plikow)
Wgrane numery zapisuje w uploaded.json i pomija przy kolejnych uruchomieniach."""
import json, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent
PROFILE = Path.home() / ".yt-upload-profile"
DONE = ROOT / "uploaded.json"
SHOTS = ROOT / "shots"; SHOTS.mkdir(exist_ok=True)
DESC = ("Audiobook: Jeff Eggers, „Proroczy jak Jezus”. Wersja do odsłuchu przez link.")

def title_for(num: int) -> str:
    src = next((ROOT / "text").glob(f"{num:02d}_*.txt"))
    paras = [p.strip() for p in src.read_text(encoding="utf-8").split("\n\n") if p.strip()]
    heads = []
    for p in paras[:3]:
        if len(p) < 90 and p.endswith(".") and "," not in p: heads.append(p.rstrip("."))
        else: break
    head = heads[0] if heads else paras[0][:60]
    if len(heads) > 1 and re.match(r"^(Rozdział|Część)\s+\w+$", heads[0]): head += ". " + heads[1]
    return f"Proroczy jak Jezus {num:02d}: {head}"[:100]

PLAYLIST = "Proroczy jak Jezus (audiobook)"

def pick_playlist(page, num) -> None:
    t = page.locator("ytcp-video-metadata-playlists ytcp-dropdown-trigger").first
    t.scroll_into_view_if_needed(); t.click(); page.wait_for_timeout(1500)
    cb = page.get_by_role("checkbox", name=re.compile(re.escape(PLAYLIST)))
    (cb.first if cb.count() else page.get_by_text(PLAYLIST, exact=True).last).click(timeout=10000); page.wait_for_timeout(700)
    page.screenshot(path=str(SHOTS / f"{num:02d}_pl.png") if isinstance(num, int) else str(SHOTS / "pl_tmp.png"))
    page.get_by_role("button", name="Gotowe").last.click(); page.wait_for_timeout(800)

def readd_05(page) -> None:
    """Wyjmij i dodaj ponownie film 05 do playlisty, zeby wypadl po 04 (sortowanie: data dodania)."""
    vid = "a91r1YQAakY"
    for _ in range(2):
        page.goto(f"https://studio.youtube.com/video/{vid}/edit", wait_until="networkidle"); page.wait_for_timeout(2500)
        pick_playlist(page, "x")
        page.wait_for_timeout(1500)
        try: page.wait_for_selector("tp-yt-iron-overlay-backdrop.opened", state="hidden", timeout=8000)
        except Exception: page.keyboard.press("Escape"); page.wait_for_timeout(800)
        page.screenshot(path=str(SHOTS / f"readd_{_}.png"))
        page.get_by_role("button", name="Zapisz").first.click(); page.wait_for_timeout(4000)

def wait_ready(num: int) -> None:
    log = ROOT / "run_all.log"
    while f"GOTOWE {num:02d}_" not in (log.read_text(errors="ignore") if log.exists() else ""):
        time.sleep(20)

def upload(page, num: int) -> None:
    wait_ready(num)
    video = next((ROOT / "video").glob(f"{num:02d}_*.mp4"))
    page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded")
    page.wait_for_selector("input[type=file]", state="attached", timeout=60000)
    page.set_input_files("input[type=file]", str(video))
    box = page.locator("#title-textarea #textbox").first
    box.wait_for(timeout=120000)
    box.click(); page.keyboard.press("Control+A"); page.keyboard.type(title_for(num))
    page.locator("#description-textarea #textbox").first.click()
    page.keyboard.type(DESC)
    page.locator("[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").first.click()
    try:
        pick_playlist(page, num)
    except Exception as e:
        print("  playlista NIE ustawiona:", repr(e)[:200], flush=True)
        page.screenshot(path=str(SHOTS / f"{num:02d}_pl_BLAD.png"))
        page.keyboard.press("Escape")
    page.screenshot(path=str(SHOTS / f"{num:02d}_1_szczegoly.png"))
    for _ in range(3):                                   # szczegoly -> elementy -> kontrola -> widocznosc
        page.locator("#next-button").click(); page.wait_for_timeout(1500)
    page.locator("[name=UNLISTED]").first.click()
    page.screenshot(path=str(SHOTS / f"{num:02d}_2_widocznosc.png"))
    done = page.locator("#done-button")
    for _ in range(240):                                 # czekaj az przetwarzanie pozwoli zapisac
        if done.get_attribute("aria-disabled") != "true": break
        page.wait_for_timeout(2000)
    done.click(); page.wait_for_timeout(4000)
    page.screenshot(path=str(SHOTS / f"{num:02d}_3_po_zapisie.png"))

def main() -> None:
    args = sys.argv[1:]; headless = "--headless" in args
    nums = [int(a) for a in args if a.isdigit()]
    state_init = None
    state = json.loads(DONE.read_text()) if DONE.exists() else []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=headless, viewport={"width": 1280, "height": 860},
            ignore_default_args=["--enable-automation"], args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for n in nums:
            if n in state: print("pomijam", n); continue
            if n >= 6 and "readd05" not in state:
                readd_05(page); state.append("readd05"); DONE.write_text(json.dumps(state)); print("05 dodane ponownie", flush=True)
            try:
                upload(page, n); state.append(n); DONE.write_text(json.dumps(state)); print("WGRANE", n, flush=True)
            except Exception as e:
                page.screenshot(path=str(SHOTS / f"{n:02d}_BLAD.png")); print("BLAD", n, repr(e)[:300], flush=True); break
        ctx.close()

if __name__ == "__main__":
    main()
