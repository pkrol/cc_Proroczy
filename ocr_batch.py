#!/usr/bin/env python3
"""
OCR batch script dla zdjęć HEIC -> tekst -> DOCX
Używa Claude API (vision, temperature=0) do OCR polskiego tekstu.

Użycie:
  # pobierz zdjęcia z Google Photos i zrób OCR:
  python3 ocr_batch.py --gphoto

  # lub podaj lokalny folder:
  python3 ocr_batch.py --photos FOLDER_ZE_ZDJECIAMI

  # z zakresem plików:
  python3 ocr_batch.py --gphoto --start IMG_0446 --end IMG_0600

Wyniki:
  ocr_txt/  - jeden plik .txt na stronę (do ręcznej kontroli jakości)
  ProroczyJakJezus_txt_WIP.docx - tekst dopisany do istniejącego dokumentu

Skrypt jest restart-safe: pomija już przetworzone strony.
"""

import os
import sys
import base64
import argparse
import time
import subprocess
from pathlib import Path

# ---- konfiguracja ----
GOOGLE_PHOTOS_ALBUM_URL = "https://photos.app.goo.gl/yPXAACafmnp86Q6K9"
DOWNLOAD_DIR = Path("gphoto_downloads")

MODEL = "claude-opus-4-6"
TEMPERATURE = 0
JPG_QUALITY = 85
TXT_DIR = Path("ocr_txt")
JPG_DIR = Path("/tmp/ocr_jpg")
DOCX_OUT = Path("ProroczyJakJezus_txt_WIP.docx")

OCR_PROMPT = """Przepisz DOKŁADNIE cały tekst widoczny na tym zdjęciu strony książki.

Pierwsza linia odpowiedzi musi mieć format:
[STRONA: X]
gdzie X to numer strony widoczny na zdjęciu. Jeśli numer strony nie jest widoczny, napisz: [STRONA: ?]

Następnie przepisz tekst według zasad:
- Przepisuj słowo w słowo, literka po literce — bez żadnych zmian, poprawek, parafraz
- Zachowaj podział na akapity (pusta linia między akapitami)
- Jeśli widzisz nagłówek (większa czcionka, pogrubienie, caps) — poprzedź go znacznikiem: [NAGLOWEK1], [NAGLOWEK2] lub [NAGLOWEK3]
- Jeśli widzisz element listy numerowanej — poprzedź: [LISTA_NUM]
- Jeśli widzisz element listy punktowanej — poprzedź: [LISTA_PNK]
- Jeśli tekst jest ucięty na górze lub dole strony (strona jest kontynuacją) — przepisz go tak jak jest
- Jeśli coś jest nieczytelne — napisz [NIECZYTELNE]
- Nie dodawaj żadnych komentarzy od siebie, tylko tekst ze strony"""


# ---- zależności ----
def check_dependencies():
    missing = []
    try:
        import anthropic
    except ImportError:
        missing.append("anthropic")
    try:
        import pillow_heif
        from PIL import Image
    except ImportError:
        missing.append("pillow-heif")
    try:
        from docx import Document
    except ImportError:
        missing.append("python-docx")
    if missing:
        print(f"Brak bibliotek: {', '.join(missing)}")
        print(f"Uruchom: pip install {' '.join(missing)} --break-system-packages")
        sys.exit(1)

check_dependencies()

import anthropic
import pillow_heif
from PIL import Image
from docx import Document
pillow_heif.register_heif_opener()


# ---- pobieranie z Google Photos ----
def ensure_gallery_dl():
    """Sprawdza czy gallery-dl jest zainstalowane, jeśli nie — instaluje."""
    try:
        result = subprocess.run(["gallery-dl", "--version"], capture_output=True, text=True)
        print(f"gallery-dl: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("Instaluję gallery-dl...")
        ret = subprocess.run(
            [sys.executable, "-m", "pip", "install", "gallery-dl", "--break-system-packages", "-q"],
            capture_output=True, text=True
        )
        if ret.returncode != 0:
            print(f"BŁĄD instalacji gallery-dl: {ret.stderr}")
            return False
        print("gallery-dl zainstalowane.")
        return True


def download_google_photos(url: str, dest_dir: Path) -> bool:
    """Pobiera zdjęcia z albumu Google Photos przez gallery-dl."""
    if url == "TUTAJ_WKLEJ_LINK_DO_ALBUMU":
        print("BŁĄD: Nie ustawiono linku do albumu Google Photos.")
        print("Edytuj skrypt i wstaw link w zmiennej GOOGLE_PHOTOS_ALBUM_URL")
        return False

    if not ensure_gallery_dl():
        return False

    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nPobieram zdjęcia z Google Photos...")
    print(f"Album: {url}")
    print(f"Cel: {dest_dir}/\n")

    result = subprocess.run(
        ["gallery-dl", "--dest", str(dest_dir), url],
        text=True
    )

    if result.returncode != 0:
        print(f"BŁĄD pobierania. Sprawdź link do albumu.")
        return False

    downloaded = list(dest_dir.rglob("*.jpg")) + list(dest_dir.rglob("*.JPG")) + \
                 list(dest_dir.rglob("*.heic")) + list(dest_dir.rglob("*.HEIC")) + \
                 list(dest_dir.rglob("*.jpeg"))
    print(f"Pobrano {len(downloaded)} plików.")
    return True


# ---- konwersja i OCR ----
def heic_to_jpg(src: Path, jpg_path: Path) -> bool:
    """Konwertuje HEIC (lub JPG) do znormalizowanego JPG."""
    try:
        img = Image.open(src)
        jpg_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(jpg_path, "JPEG", quality=JPG_QUALITY)
        return True
    except Exception as e:
        print(f"  BŁĄD konwersji {src.name}: {e}")
        return False


def image_to_base64(jpg_path: Path) -> str:
    with open(jpg_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def ocr_image(client: anthropic.Anthropic, jpg_path: Path, filename: str) -> str | None:
    """Wywołuje Claude API i zwraca przepisany tekst."""
    try:
        b64 = image_to_base64(jpg_path)
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": OCR_PROMPT,
                        },
                    ],
                }
            ],
        )
        return response.content[0].text
    except anthropic.RateLimitError:
        print(f"  Rate limit — czekam 30s...")
        time.sleep(30)
        return ocr_image(client, jpg_path, filename)
    except Exception as e:
        print(f"  BŁĄD API dla {filename}: {e}")
        return None


# ---- formatowanie inline (bold/italic) ----
def parse_inline(text: str) -> list[tuple[str, bool, bool]]:
    """Parsuje **bold** i *italic*, zwraca listę (tekst, bold, italic)."""
    import re
    segments = []
    pattern = r'(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|([^*]+|\*))'
    for m in re.finditer(pattern, text, re.DOTALL):
        if m.group(2):
            segments.append((m.group(2), True, True))
        elif m.group(3):
            segments.append((m.group(3), True, False))
        elif m.group(4):
            segments.append((m.group(4), False, True))
        elif m.group(5):
            segments.append((m.group(5), False, False))
    return segments


def add_formatted_paragraph(doc: Document, text: str, style: str = "Normal"):
    """Dodaje akapit z obsługą **bold** i *italic*."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    if style.startswith("Heading"):
        p = doc.add_heading("", level=int(style[-1]))
    else:
        p = doc.add_paragraph("", style=style)

    # usuń pusty run który add_heading/add_paragraph tworzy
    for r in p._element.findall(qn('w:r')):
        p._element.remove(r)

    for segment_text, bold, italic in parse_inline(text):
        if not segment_text:
            continue
        run = p.add_run(segment_text)
        if bold:
            run.bold = True
        if italic:
            run.italic = True


# ---- budowanie DOCX ----
def parse_text_to_docx_paragraphs(text: str) -> list[tuple[str, str]]:
    result = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[NAGLOWEK1]"):
            result.append(("Heading 1", line[11:].strip()))
        elif line.startswith("[NAGLOWEK2]"):
            result.append(("Heading 2", line[11:].strip()))
        elif line.startswith("[NAGLOWEK3]"):
            result.append(("Heading 3", line[11:].strip()))
        elif line.startswith("[LISTA_NUM]") or line.startswith("[LISTA_PNK]"):
            result.append(("List Paragraph", line[11:].strip()))
        else:
            result.append(("Normal", line))
    return result


def append_page_to_docx(doc: Document, txt_path: Path, page_label: str):
    text = txt_path.read_text(encoding="utf-8")
    for style, content in parse_text_to_docx_paragraphs(text):
        add_formatted_paragraph(doc, content, style)


def get_sorted_image_files(photos_dir: Path, start: str | None, end: str | None) -> list[Path]:
    exts = ["*.HEIC", "*.heic", "*.JPG", "*.jpg", "*.jpeg", "*.JPEG"]
    files = []
    for ext in exts:
        files.extend(photos_dir.rglob(ext))
    files = sorted(set(files), key=lambda p: p.stem)
    if start:
        files = [f for f in files if f.stem >= start]
    if end:
        files = [f for f in files if f.stem <= end]
    return files


# ---- main ----
def main():
    parser = argparse.ArgumentParser(description="OCR zdjęć HEIC przez Claude API → WIP DOCX")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--gphoto", action="store_true", help="Pobierz z Google Photos (wymaga ustawionego GOOGLE_PHOTOS_ALBUM_URL)")
    group.add_argument("--photos", help="Lokalny folder ze zdjęciami")
    parser.add_argument("--start", default=None, help="Pierwsza nazwa pliku (bez rozszerzenia), np. IMG_0446")
    parser.add_argument("--end", default=None, help="Ostatnia nazwa pliku (bez rozszerzenia), np. IMG_0600")
    parser.add_argument("--api-key", default=None, help="Klucz Anthropic API (domyślnie z ANTHROPIC_API_KEY)")
    parser.add_argument("--skip-docx", action="store_true", help="Tylko OCR do txt, bez budowania DOCX")
    args = parser.parse_args()

    # --- pobieranie z Google Photos ---
    if args.gphoto:
        if not download_google_photos(GOOGLE_PHOTOS_ALBUM_URL, DOWNLOAD_DIR):
            sys.exit(1)
        photos_dir = DOWNLOAD_DIR
    else:
        photos_dir = Path(args.photos)
        if not photos_dir.exists():
            print(f"BŁĄD: folder {photos_dir} nie istnieje")
            sys.exit(1)

    # --- API ---
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("BŁĄD: brak klucza API. Ustaw ANTHROPIC_API_KEY lub podaj --api-key")
        sys.exit(1)

    TXT_DIR.mkdir(exist_ok=True)
    JPG_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic(api_key=api_key)

    files = get_sorted_image_files(photos_dir, args.start, args.end)
    if not files:
        print("Nie znaleziono plików zdjęć w podanym folderze/zakresie.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Znaleziono {len(files)} zdjęć do przetworzenia")
    print(f"Model: {MODEL}, temperature: {TEMPERATURE}")
    print(f"Wyniki txt: {TXT_DIR}/")
    print(f"Docelowy DOCX: {DOCX_OUT}")
    print(f"{'='*60}\n")

    # --- pętla OCR ---
    processed = []
    errors = []

    for i, img_path in enumerate(files, 1):
        stem = img_path.stem
        txt_path = TXT_DIR / f"{stem}.txt"
        jpg_path = JPG_DIR / f"{stem}.jpg"

        print(f"[{i}/{len(files)}] {stem}", end="", flush=True)

        if txt_path.exists() and txt_path.stat().st_size > 50:
            print(f" → już gotowe (pomijam)")
            processed.append((stem, txt_path))
            continue

        print(f" → konwersja...", end="", flush=True)
        if not jpg_path.exists():
            if not heic_to_jpg(img_path, jpg_path):
                errors.append(stem)
                print()
                continue

        print(f" → OCR...", end="", flush=True)
        text = ocr_image(client, jpg_path, stem)
        if text is None:
            errors.append(stem)
            print(f" BŁĄD")
            continue

        # wyciągnij numer strony z pierwszej linii i zmień nazwę pliku
        page_num = "?"
        lines = text.splitlines()
        if lines and lines[0].startswith("[STRONA:"):
            import re
            m = re.search(r"\[STRONA:\s*(\S+)\]", lines[0])
            if m:
                page_num = m.group(1)
            clean_text = "\n".join(lines[1:]).lstrip("\n")
        else:
            clean_text = text

        txt_path = TXT_DIR / f"{stem}_p{page_num.replace('?', 'X')}.txt"
        txt_path.write_text(clean_text, encoding="utf-8")
        print(f" → OK (str. {page_num}, {len(clean_text)} znaków)")
        processed.append((stem, txt_path))
        time.sleep(0.5)

    # --- DOCX ---
    if not args.skip_docx and processed:
        print(f"\n{'='*60}")
        print(f"Dopisuję {len(processed)} stron do DOCX...")

        if DOCX_OUT.exists():
            doc = Document(str(DOCX_OUT))
            print(f"Istniejący plik: {DOCX_OUT}")
        else:
            doc = Document()
            print(f"Nowy plik: {DOCX_OUT}")

        for stem, txt_path in sorted(processed, key=lambda x: x[0]):
            append_page_to_docx(doc, txt_path, stem)

        doc.save(str(DOCX_OUT))
        print(f"Zapisano: {DOCX_OUT}")

    # --- podsumowanie ---
    print(f"\n{'='*60}")
    print(f"GOTOWE: {len(processed)} stron przetworzono")
    if errors:
        print(f"BŁĘDY ({len(errors)}): {', '.join(errors)}")
        print(f"Uruchom ponownie — pominie gotowe, spróbuje błędnych")
    print(f"{'='*60}")
    print(f"\nKontrola jakości: sprawdź pliki w {TXT_DIR}/")


if __name__ == "__main__":
    main()
