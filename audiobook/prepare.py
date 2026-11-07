#!/usr/bin/env python3
"""Word -> pliki tekstowe per rozdzial, gotowe pod ElevenLabs (normalizacja pod lektora).

Uzycie:  python3 audiobook/prepare.py [plik.docx]
Wynik:   audiobook/text/NN_slug.txt  +  audiobook/text/_report.txt
"""
import re
import sys
import unicodedata
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent
DEFAULT_DOCX = ROOT.parent / "ProroczyJakJezus_txt_WIP - 15.03.wieczor-poprawione-pauzy.docx"
import os
OUT = Path(os.environ["PREPARE_OUT"]) if os.environ.get("PREPARE_OUT") else ROOT / "text"

SKIP_H1 = {"OPINIE", "SPIS TREŚCI"}

# ---------- liczebniki porzadkowe ----------
U = {1: "pierwszy", 2: "drugi", 3: "trzeci", 4: "czwarty", 5: "piąty", 6: "szósty",
     7: "siódmy", 8: "ósmy", 9: "dziewiąty"}
T = {10: "dziesiąty", 11: "jedenasty", 12: "dwunasty", 13: "trzynasty", 14: "czternasty",
     15: "piętnasty", 16: "szesnasty", 17: "siedemnasty", 18: "osiemnasty", 19: "dziewiętnasty",
     20: "dwudziesty", 30: "trzydziesty", 40: "czterdziesty", 50: "pięćdziesiąty",
     60: "sześćdziesiąty", 70: "siedemdziesiąty", 80: "osiemdziesiąty", 90: "dziewięćdziesiąty"}


def ordinal(n: int) -> str:
    if n in U:
        return U[n]
    if n in T:
        return T[n]
    if n < 100:
        return f"{T[n // 10 * 10]} {U[n % 10]}"
    if n == 100:
        return "setny"
    if n < 200:
        return f"sto {ordinal(n - 100)}"
    if n == 200:
        return "dwusetny"
    return f"dwieście {ordinal(n - 200)}" if n < 300 else str(n)


def genitive(phrase: str) -> str:
    out = []
    for w in phrase.split():
        if w in ("sto", "dwieście"):
            out.append(w)
        elif w.endswith("y"):
            out.append(w[:-1] + "ego")
        elif w.endswith("i"):
            out.append(w + "ego")
        else:
            out.append(w)
    return " ".join(out)


# ---------- ksiegi biblijne ----------
BOOKS = {
    "Rdz": "Księga Rodzaju", "Wj": "Księga Wyjścia", "Lb": "Księga Liczb", "Pwt": "Księga Powtórzonego Prawa",
    "1 Sm": "Pierwsza Księga Samuela", "2 Sm": "Druga Księga Samuela", "Est": "Księga Estery",
    "Ps": "Psalm", "Prz": "Księga Przysłów", "Pnp": "Pieśń nad Pieśniami", "Iz": "Księga Izajasza",
    "Jr": "Księga Jeremiasza", "Ez": "Księga Ezechiela", "Dn": "Księga Daniela", "Oz": "Księga Ozeasza",
    "Jl": "Księga Joela", "Mi": "Księga Micheasza", "So": "Księga Sofoniasza", "Za": "Księga Zachariasza",
    "Ml": "Księga Malachiasza", "Mt": "Ewangelia Mateusza", "Mk": "Ewangelia Marka", "Łk": "Ewangelia Łukasza",
    "J": "Ewangelia Jana", "Dz": "Dzieje Apostolskie", "Rz": "List do Rzymian",
    "1 Kor": "Pierwszy List do Koryntian", "2 Kor": "Drugi List do Koryntian", "Ga": "List do Galatów",
    "Ef": "List do Efezjan", "Flp": "List do Filipian", "Kol": "List do Kolosan",
    "1 Tes": "Pierwszy List do Tesaloniczan", "2 Tes": "Drugi List do Tesaloniczan",
    "1 Tm": "Pierwszy List do Tymoteusza", "2 Tm": "Drugi List do Tymoteusza", "Hbr": "List do Hebrajczyków",
    "Jk": "List Jakuba", "1 P": "Pierwszy List Piotra", "2 P": "Drugi List Piotra",
    "1 J": "Pierwszy List Jana", "2 J": "Drugi List Jana", "3 J": "Trzeci List Jana", "Jud": "List Judy",
    "Ap": "Apokalipsa",
}
_book_alt = "|".join(sorted((re.escape(b).replace(r"\ ", r"\s?") for b in BOOKS), key=len, reverse=True))
NUM = r"\d+"
RNG = rf"{NUM}(?:\s*[-–]\s*{NUM})?"
REF_RE = re.compile(
    rf"(?<![\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ])(?P<book>{_book_alt})\s+"
    rf"(?P<body>{NUM}\s*,\s*{RNG}(?:\s*[.;]\s*(?:{NUM}\s*,\s*)?{RNG})*)"
)


def _verses(spec: str) -> str:
    items = []
    for part in [p for p in re.split(r"\s*\.\s*", spec) if p]:
        m = re.match(rf"(\d+)\s*[-–]\s*(\d+)", part)
        items.append(("r", int(m[1]), int(m[2])) if m else ("v", int(part), 0))
    if len(items) == 1 and items[0][0] == "r":
        return f"wersety od {genitive(ordinal(items[0][1]))} do {genitive(ordinal(items[0][2]))}"
    parts = [f"od {genitive(ordinal(a))} do {genitive(ordinal(b))}" if k == "r" else ordinal(a)
             for k, a, b in items]
    label = "werset" if len(items) == 1 else "wersety"
    if len(parts) > 1:
        return f"{label} " + ", ".join(parts[:-1]) + " i " + parts[-1]
    return f"{label} {parts[0]}"


CH_RE = re.compile(
    rf"(?<![\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ])(?P<book>{_book_alt})\s+(?P<ch>\d{{1,3}})(?!\s*[,\d]|\s*[-–]\s*\d)"
)
FULL_RE = re.compile(
    r"(?<![\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ])(?P<w>[A-ZŁŚŻ][a-ząćęłńóśźż]+)\s+"
    rf"(?P<body>{NUM}\s*,\s*{RNG}(?:\s*[.;]\s*(?:{NUM}\s*,\s*)?{RNG})*)"
)
NOT_BOOK = {"Rozdział", "Strona", "Cena", "Godzina", "Godz"}


def render_chapter(m: re.Match) -> str:
    book = re.sub(r"\s+", " ", m["book"]).strip()
    book = re.sub(r"^(\d)([A-Za-zŁł])", r"\1 \2", book)
    name = BOOKS.get(book, book)
    ch = int(m["ch"])
    return f"{name} {ordinal(ch)}" if name == "Psalm" else f"{name}, rozdział {ordinal(ch)}"


def render_full(m: re.Match) -> str:
    if m["w"] in NOT_BOOK:
        return m[0]
    fake = re.match(r"(?P<book>.*?)\s*(?P<body>\d.*)", m[0])
    out = render_ref(type("M", (), {"__getitem__": lambda self, k: {"book": "Psalm_", "body": m["body"]}[k]})())
    return f"{m['w']}, " + out.split(", ", 1)[1] if ", " in out else m[0]


def render_ref(m: re.Match) -> str:
    book = re.sub(r"\s+", " ", m["book"]).strip()
    book = re.sub(r"^(\d)([A-Za-zŁł])", r"\1 \2", book)
    name = BOOKS.get(book, book)
    chunks, chapter = [], None
    for tok in m["body"].split(";"):
        tok = tok.strip()
        if "," in tok:
            ch, v = [x.strip() for x in tok.split(",", 1)]
            chapter = int(ch)
            chunks.append((chapter, _verses(v)))
        elif chapter is not None:
            chunks.append((chapter, _verses(tok)))
    out = []
    for i, (ch, v) in enumerate(chunks):
        if name == "Psalm":
            out.append(f"{name} {ordinal(ch)}, {v}" if i == 0 else f"Psalm {ordinal(ch)}, {v}")
        else:
            head = f"{name}, " if i == 0 else ""
            out.append(f"{head}rozdział {ordinal(ch)}, {v}")
    return "; ".join(out)


# ---------- czyszczenie ----------
SUP = "¹²³⁴⁵⁶⁷⁸⁹⁰"
ABBR = [
    (r"\btzn\.", "to znaczy"), (r"\bnp\.", "na przykład"), (r"\bitd\.", "i tak dalej"),
    (r"\bitp\.", "i tym podobne"), (r"\btj\.", "to jest"), (r"\bm\.in\.", "między innymi"),
    (r"(?<=\d) r\.", " roku"), (r"\bks\.", "ksiądz"), (r"\bwł\.", ""),
]


def saint(m: re.Match) -> str:
    nxt = m["next"]
    form = "świętemu" if nxt.endswith("owi") else "świętym" if nxt.endswith(("em", "ym")) else "świętego"
    return f"{form} {nxt}"


def clean(t: str) -> str:
    t = t.replace(" ", " ")
    t = re.sub(rf"(?<=\S)[{SUP}]+", "", t)          # znaczniki przypisow
    t = re.sub(rf"^\s*[{SUP}]+\s*", "", t)
    t = REF_RE.sub(render_ref, t)
    t = FULL_RE.sub(render_full, t)
    t = CH_RE.sub(render_chapter, t)
    t = re.sub(r"\b(?:zob|por)\.\s*", "", t, flags=re.I)
    t = re.sub(r"\bśw\.\s+(?P<next>[A-ZŁŚŻ]\w+)", saint, t)
    for pat, rep in ABBR:
        t = re.sub(pat, rep, t)
    t = t.replace("(...)", "…").replace("...", "…")
    t = re.sub(r"\[([^\]]+)\]", r"\1", t)           # [jeszcze] -> jeszcze
    t = re.sub(r"\*+", "", t)
    t = re.sub(r"\s*\(\s*\)", "", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def is_footnote(t: str) -> bool:
    return bool(re.match(rf"^\s*[{SUP}]", t))


def heading_text(t: str, level: int) -> str:
    t = clean(t)
    m = re.match(r"^Rozdział\s+(\d+)\b\s*(.*)$", t, re.I)
    if m:
        rest = m[2].strip()
        t = f"Rozdział {ordinal(int(m[1]))}" + (f". {rest.lower().capitalize()}" if rest else "")
    elif t.isupper() or sum(c.isupper() for c in t) > 0.7 * max(1, sum(c.isalpha() for c in t)):
        t = t.lower().capitalize()
        t = re.sub(r"\b(bóg|boga|bogu|bogiem|ojciec|ojca|ojcu|jezus|jezusa|duch|ducha|duchu|abba|pan|pana|panu|chrystus|chrystusa|izrael|izraela)\b",
                   lambda m: m[1].capitalize(), t)
    else:
        m = re.search(r"\b[A-ZŁŚŻĄĆĘÓŃŹ]{3,}\b", t)
        if m and m.start() > 0:
            t = t[:m.start()].rstrip() + ". " + t[m.start():].lower().capitalize()
            t = re.sub(r"\b(bóg|boga|bogu|bogiem|ojciec|ojca|ojcu|jezus|jezusa|duch|ducha|duchu|abba|pan|pana|panu|chrystus|chrystusa|izrael|izraela)\b",
                       lambda m: m[1].capitalize(), t)
    t = re.sub(r"\b(Koryntian|Tesaloniczan)\s+(\d+)\b", lambda m: f"{m[1]} {ordinal(int(m[2]))}", t)
    return t.rstrip(".:") + "."


def slug(s: str) -> str:
    s = s.replace("ł", "l").replace("Ł", "L")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "x"


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DOCX
    doc = Document(src)
    units, cur, skipping = [], None, False

    def has_body(u):
        return any(k == "p" for k, _ in u["items"])

    for p in doc.paragraphs:
        raw, style = p.text.strip(), p.style.name
        if not raw:
            continue
        lvl = int(style[-1]) if style.startswith("Heading") else 0
        if lvl == 1:
            skipping = raw.upper() in SKIP_H1
            if skipping:
                continue
            if cur is None or has_body(cur):
                cur = {"title": raw, "items": []}
                units.append(cur)
            cur["items"].append(("h", heading_text(raw, 1)))
            continue
        if skipping or cur is None:
            continue
        if raw.startswith("[DO UZUPEŁNIENIA str.183"):
            patch = ROOT / "patches" / "183.txt"
            if patch.exists():
                for para in patch.read_text(encoding="utf-8").split("\n\n"):
                    c = clean(para.strip())
                    if c:
                        cur["items"].append(("p", c))
            continue
        if raw.startswith("[DO UZUPEŁNIENIA") or is_footnote(raw):
            continue
        if lvl:
            if lvl == 2 and re.match(r"^Rozdział\s+\d+", raw, re.I) and has_body(cur):
                cur = {"title": raw, "items": []}
                units.append(cur)
            cur["items"].append(("h", heading_text(raw, lvl)))
        else:
            c = clean(raw)
            if c:
                cur["items"].append(("p", c))

    for u in units:
        merged = []
        for kind, text in u["items"]:
            if (kind == "p" and merged and merged[-1][0] == "p"
                    and re.search(r"[a-ząćęłńóśźż]-$", merged[-1][1]) and text[:1].islower()):
                merged[-1] = ("p", merged[-1][1][:-1] + text)
            else:
                merged.append((kind, text))
        u["items"] = merged

    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.txt"):
        f.unlink()
    report, total = [], 0
    for i, u in enumerate(units, 1):
        name = f"{i:02d}_{slug(u['title'])}.txt"
        lines = []
        for kind, text in u["items"]:
            lines.append(text if kind == "p" else f"\n{text}\n")
        body = "\n\n".join(lines).replace("\n\n\n", "\n\n").strip() + "\n"
        (OUT / name).write_text(body, encoding="utf-8")
        total += len(body)
        report.append(f"{name:60s} {len(body):7d}")
    report.append(f"{'RAZEM':60s} {total:7d}")
    (OUT / "_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
