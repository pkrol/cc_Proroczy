#!/usr/bin/env python3
"""Generuje MP3 z plikow audiobook/text/NN_*.txt (ElevenLabs v3, glos Piotr Engaging).

Uzycie: ELEVENLABS_API_KEY=... python3 audiobook/generate.py 05 [06 07 ...]
Wznawianie: gotowe kawalki (mp3/NN/part_XX.mp3) sa pomijane.
"""
import json, os, re, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOICE = "o2xdfKUpc1Bwq7RchZuW"          # Piotr - Engaging, Reassuring Storyteller
MODEL = "eleven_v3"
SETTINGS = {"stability": 0.5}
MAX = 4500                              # limit v3: 5000 znakow na zadanie
K = os.environ["ELEVENLABS_API_KEY"]


def tag_paragraphs(text: str) -> list[str]:
    """Regulowe znaczniki v3: pauza po naglowku (linia konczaca sie kropka, krotka, bez przecinka)."""
    out = []
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        is_head = len(para) < 90 and para.endswith(".") and "," not in para and "\n" not in para
        out.append(f"{para}\n[long pause]" if is_head else para)
    return out


def chunks(paras: list[str]) -> list[str]:
    res, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 2 > MAX:
            res.append(cur); cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        res.append(cur)
    return res


def tts(text: str) -> bytes:
    body = {"text": text, "model_id": MODEL, "voice_settings": SETTINGS}
    r = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), method="POST",
        headers={"xi-api-key": K, "Content-Type": "application/json"})
    return urllib.request.urlopen(r, timeout=300).read()


def main() -> None:
    for num in sys.argv[1:]:
        src = next((ROOT / "text").glob(f"{int(num):02d}_*.txt"))
        parts = chunks(tag_paragraphs(src.read_text(encoding="utf-8")))
        d = ROOT / "mp3" / f"{int(num):02d}"; d.mkdir(parents=True, exist_ok=True)
        print(f"{src.name}: {sum(map(len, parts))} znakow, {len(parts)} kawalkow", flush=True)
        files = []
        for i, part in enumerate(parts, 1):
            f = d / f"part_{i:02d}.mp3"
            if not f.exists():
                f.write_bytes(tts(part))
            print("  ok", f.name, flush=True)
            files.append(f)
        final = ROOT / "mp3" / (src.stem + ".mp3")
        if shutil.which("ffmpeg"):
            lst = d / "list.txt"
            lst.write_text("".join(f"file '{f.as_posix()}'\n" for f in files))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                            "-i", str(lst), "-c", "copy", str(final)], check=True)
        else:
            final.write_bytes(b"".join(f.read_bytes() for f in files))
        print("GOTOWE", final, flush=True)


if __name__ == "__main__":
    main()
