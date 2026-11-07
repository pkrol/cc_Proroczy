#!/usr/bin/env python3
"""Generuje wszystkie pliki z text/ po kolei (MP3 + MP4 z okladka). Pilnuje limitu znakow:
gdy zabraknie, czeka na reset licznika i wznawia. Gotowe pliki pomija.
Uzycie: ELEVENLABS_API_KEY=... python3 audiobook/run_all.py"""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import generate as g

ROOT = g.ROOT
def sub():
    r = urllib.request.Request("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": g.K})
    d = json.load(urllib.request.urlopen(r, timeout=60))
    return d["character_limit"] - d["character_count"], d["next_character_count_reset_unix"]

def video(stem):
    out = ROOT / "video" / f"{stem}.mp4"
    if out.exists(): return
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", "2",
        "-i", str(ROOT / "cover/okladka.png"), "-i", str(ROOT / "mp3" / f"{stem}.mp3"),
        "-filter_complex", "[0:v]split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=40:5,eq=brightness=-0.25[bg];[b]scale=-2:980[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]",
        "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
        "-crf", "24", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out)], check=True)

def log(m): print(time.strftime("%H:%M:%S"), m, flush=True)

for src in sorted((ROOT / "text").glob("[0-9][0-9]_*.txt")):
    stem = src.stem
    if (ROOT / "mp3" / f"{stem}.mp3").exists():
        log(f"pomijam {stem}"); continue
    need = len(src.read_text(encoding="utf-8")) + 300
    while True:
        left, reset = sub()
        if left >= need: break
        wait = max(60, reset - int(time.time()) + 90) if left < need else 60
        log(f"{stem}: potrzeba {need}, zostalo {left}; czekam {wait}s na reset"); time.sleep(min(wait, 900))
    num = int(stem[:2])
    for attempt in range(4):
        try:
            sys.argv = ["generate.py", str(num)]; g.main(); break
        except Exception as e:
            log(f"BLAD {stem} proba {attempt+1}: {e}"); time.sleep(30 * (attempt + 1))
    else:
        log(f"PORZUCAM {stem}"); continue
    video(stem); log(f"GOTOWE {stem}")
log("WSZYSTKO GOTOWE")
