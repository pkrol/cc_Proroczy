# OCR Proroczy — instrukcja obsługi

Skrypt `ocr_batch.py` pobiera zdjęcia z Google Photos, robi OCR przez Claude API i dopisuje tekst do docelowego dokumentu Word.

---

## Wymagania wstępne (jednorazowe)

Otwórz terminal WSL i zainstaluj biblioteki:

```bash
pip install anthropic pillow-heif python-docx --break-system-packages
```

Klucz API jest już zapisany w systemie (`~/.bashrc`), nie trzeba go podawać.

---

## Gdzie są ważne pliki

| Plik | Opis |
|------|------|
| `ocr_batch.py` | główny skrypt |
| `ProroczyJakJezus_txt_WIP.docx` | docelowy dokument Word — tu trafia przepisany tekst |
| `ocr_txt/` | folder z plikami txt (jeden na stronę) — tu sprawdzasz jakość |
| `gphoto_downloads/` | pobrane zdjęcia z Google Photos |

---

## Uruchamianie

### 1. Przejdź do folderu projektu

```bash
cd /mnt/c/Users/krolp/Downloads/cc_Proroczy
```

### 2. Pobierz zdjęcia z Google Photos i zrób OCR

```bash
python3 ocr_batch.py --gphoto
```

To wykona po kolei: pobranie zdjęć → konwersja HEIC→JPG → OCR → dopisanie do DOCX.

### 3. Tylko lokalny folder (jeśli masz już zdjęcia na dysku)

```bash
python3 ocr_batch.py --photos NAZWA_FOLDERU/
```

### 4. Zakres zdjęć (jeśli chcesz przetworzyć tylko część)

```bash
python3 ocr_batch.py --gphoto --start IMG_0446 --end IMG_0500
```

### 5. Tylko OCR bez zapisywania do DOCX (najpierw sprawdź jakość)

```bash
python3 ocr_batch.py --gphoto --skip-docx
```

---

## Kontrola jakości

Po uruchomieniu skryptu sprawdź pliki w folderze `ocr_txt/`.

Każdy plik nazywa się np. `IMG_0446_p61.txt` gdzie:
- `IMG_0446` = nazwa zdjęcia
- `p61` = numer strony z książki

Otwórz kilka plików i porównaj ze zdjęciami. Jeśli jakiś tekst jest źle przepisany:
1. Popraw ręcznie plik `.txt`
2. Uruchom skrypt ponownie — pominie już przetworzone i odświeży DOCX

### Znaczniki w plikach txt

| Znacznik | Znaczenie |
|----------|-----------|
| `[NAGLOWEK1]` | Nagłówek rozdziału (duży) |
| `[NAGLOWEK2]` | Podrozdział (średni) |
| `[NAGLOWEK3]` | Nagłówek podpunktu (mały) |
| `[LISTA_NUM]` | Element listy numerowanej |
| `[LISTA_PNK]` | Element listy punktowanej |
| `[NIECZYTELNE]` | Fragment nieczytelny na zdjęciu |

---

## Jeśli skrypt przerwie się w połowie

Uruchom go ponownie tym samym poleceniem. Automatycznie pominie już przetworzone strony (te które mają plik `.txt`) i wznowi od miejsca gdzie skończył.

---

## Zmiana docelowego pliku Word

Otwórz `ocr_batch.py` w edytorze i zmień linię:

```python
DOCX_OUT = Path("ProroczyJakJezus_txt_WIP.docx")
```

na pełną ścieżkę jeśli plik jest w innym miejscu, np.:

```python
DOCX_OUT = Path("/mnt/c/Users/krolp/Documents/MojaKsiazka.docx")
```

---

## Zmiana albumu Google Photos

Otwórz `ocr_batch.py` i zmień linię:

```python
GOOGLE_PHOTOS_ALBUM_URL = "https://photos.app.goo.gl/yPXAACafmnp86Q6K9"
```
