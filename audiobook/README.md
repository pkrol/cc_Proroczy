# Audiobook "Proroczy jak Jezus" (ElevenLabs v3)

Pipeline na uzytek prywatny. Tekst ksiazki, audio i okladka nie sa w repo (prawa autorskie), patrz .gitignore.

1. `prepare.py`: Word -> `text/NN_*.txt` (rozdzialy; sygnatury biblijne slownie, bez przypisow, bez skrotow). Latka strony: `patches/183.txt`.
2. `cast.py` / `sample.py`: lista polskich glosow i probki. Wybrany: Piotr - Engaging, Reassuring Storyteller (`o2xdfKUpc1Bwq7RchZuW`), model `eleven_v3`, stability 0.5.
3. `generate.py NN`: MP3 per plik (kawalki do 4500 znakow, wznawianie po kawalkach). `run_all.py`: wszystkie po kolei, pilnuje limitu znakow, robi tez MP4 z okladka (ffmpeg).
4. `yt_login.py` (reczne logowanie do profilu Playwright), `yt_upload.py` (wgrywanie jako niepubliczne do playlisty), `yt_setup_playlist.py` (tworzenie playlisty).

Klucz: zmienna `ELEVENLABS_API_KEY` (nie zapisywac w repo).

## Stan (2026-11-07)
- Wygenerowane pliki 01-23 (do Rozdzialu 14). Brakuja 24 (Rozdz. 15), 25 (Rozdz. 16), 26 (Rozdz. 17): ok. 52,7 tys. znakow, limit ElevenLabs wyczerpany do 7.12 (zostalo ok. 23 tys.).
- YouTube: wgrane 01-10; dzienny limit wgrywania, dalej od filmu 11 po weryfikacji kanalu.
