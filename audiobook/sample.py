#!/usr/bin/env python3
"""Probka tego samego akapitu na kilku glosach (v3). Klucz: ELEVENLABS_API_KEY."""
import json, os, urllib.request
from pathlib import Path
K = os.environ["ELEVENLABS_API_KEY"]
H = {"xi-api-key": K, "Content-Type": "application/json"}
OUT = Path(__file__).parent / "samples"; OUT.mkdir(exist_ok=True)
TEXT = ("[warmly] Pamiętam, że szedłem korytarzem i natychmiast zwrócił moją uwagę automat ze słodyczami. "
        "Podszedłem do maszyny i wyciągnąłem drobniaki. Ale zanim zacząłem wrzucać monety do otworu, "
        "usłyszałem w głowie łagodny, ale stanowczy szept. [softly] Ten głos powiedział: „Niepotrzebny ci ten batonik”. "
        "[pause] Od razu to odrzuciłem. A jednocześnie dobrze wiedziałem, że to nie jest mój głos.")
VOICES = {  # nazwa: (voice_id, public_owner_id lub None gdy juz w bibliotece)
    "Piotr_Engaging": ("o2xdfKUpc1Bwq7RchZuW", None),
    "Piotr_DeepKindRich": ("S1uaQ66tHSeCjgsWYpGI", None),
    "Marcin_WarmLow": ("h4BzQY1NEHGhFFLDU8WQ", None),
    "MichalK_CalmWarm": ("1nUkvoDFCcCTjJk9U8mL", None),
    "TomaszZ_Intimate": ("BGhujeSc87HLfgxDj4tu", None),
    "Magdalena_WarmLow_F": ("fEfGdiGJK4l3imI70mtC", "75c2ea9401829ab90c9b37039f1776ae28b1730c4ba5fabdc7b040133ebd76e5"),
}
def call(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method="POST")
    return urllib.request.urlopen(r, timeout=180).read()
for name, (vid, owner) in VOICES.items():
    try:
        if owner:
            try: call(f"https://api.elevenlabs.io/v1/voices/add/{owner}/{vid}", {"new_name": name})
            except Exception as e: print("add:", name, getattr(e, "read", lambda: b"")()[:120])
        audio = call(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128",
                     {"text": TEXT, "model_id": "eleven_v3", "voice_settings": {"stability": 0.5}})
        (OUT / f"{name}.mp3").write_bytes(audio); print("OK", name, len(audio))
    except Exception as e:
        print("ERR", name, e, getattr(e, "read", lambda: b"")()[:200])
