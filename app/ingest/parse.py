"""Turn PDFs, HTML and text files into one clean JSON record per page.

Record: {doc_id, source_file, page, headings, text, tables, method}
"""

import argparse
import json
import os
import re
import shutil
import statistics
from collections import Counter
from pathlib import Path

import pdfplumber
from bs4 import BeautifulSoup

from app.ingest.clean import clean_text, drop_lines, repeated_lines, shape

MIN_CHARS = 25
HEADING_SIZE = 1.15
TESSERACT = os.getenv("TESSERACT_CMD") or shutil.which("tesseract")
NUMBERED = re.compile(r"^\d+(\.\d+)*\.?\s+[^\W\d]")


def make_record(path, page, headings, text, tables, method):
    return {
        "doc_id": re.sub(r"[^a-z0-9_-]+", "-", path.stem.lower()).strip("-"),
        "source_file": path.as_posix(),
        "page": page,
        "headings": headings,
        "text": text,
        "tables": tables,
        "method": method,
    }


def with_tables(text, tables):
    """Add tables as rows so search can find their contents."""
    for i, rows in enumerate(tables, start=1):
        text += f"\n\nTable {i}:\n" + "\n".join(" | ".join(row) for row in rows)
    return text.strip()


def clean_rows(rows):
    def cell(value):
        return clean_text(value or "", page_numbers=False).replace("\n", " ")

    rows = [[cell(value) for value in row] for row in rows]
    return [row for row in rows if any(row)]


def outside(page, boxes):
    """Exclude table areas so table text is not extracted twice."""

    def keep(obj):
        x = (obj["x0"] + obj["x1"]) / 2
        y = (obj["top"] + obj["bottom"]) / 2
        return not any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes)

    return page.filter(keep)


def line_styles(page):
    """Return each line with its font size and whether it is bold."""
    styles = []

    for line in page.extract_text_lines(return_chars=True, use_text_flow=True):
        chars = [char for char in line["chars"] if char["text"].strip()]
        if chars:
            size = statistics.median(char["size"] for char in chars)
            bold = all("bold" in char["fontname"].lower() for char in chars)
            styles.append((line["text"].strip(), size, bold))

    return styles


def ocr(page, lang):
    if not TESSERACT:
        return "", "needs_ocr"

    import pytesseract  # OCR thevai irukkira pages-ku mattum

    pytesseract.pytesseract.tesseract_cmd = TESSERACT
    image = page.to_image(resolution=300).original
    return pytesseract.image_to_string(image, lang=lang), "ocr"


def is_heading(text, size, bold, body_size, noise):
    looks_big = size >= body_size * HEADING_SIZE or bold
    short = 2 < len(text) <= 100 and text[-1] not in ".,;" and any(char.isalpha() for char in text)
    return looks_big and short and shape(text) not in noise


def parse_pdf(path: Path, lang: str = "eng") -> list[dict]:
    pages = []

    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            found = page.find_tables()
            tables = [clean_rows(table.extract()) for table in found]
            body = outside(page, [table.bbox for table in found])
            text = body.extract_text(use_text_flow=True) or ""
            styles = line_styles(body)
            method = "text"

            if len(text.strip()) < MIN_CHARS and page.images:
                text, method = ocr(page, lang)
                lines = [line.strip() for line in text.splitlines()]
                styles = [(line, 0, True) for line in lines if NUMBERED.match(line)]

            pages.append(
                {
                    "page": number,
                    "text": text,
                    "styles": styles,
                    "tables": tables,
                    "method": method,
                }
            )
            page.close()

    sizes = Counter(round(size) for page in pages for _, size, _ in page["styles"])
    body_size = sizes.most_common(1)[0][0] if sizes else 10
    noise = repeated_lines([page["text"] for page in pages])
    style_pages = ["\n".join(line for line, _, _ in page["styles"]) for page in pages]
    noise.update(repeated_lines(style_pages))
    style_counts = Counter(shape(line) for page in pages for line, _, _ in page["styles"])
    noise.update(line for line, count in style_counts.items() if line and count >= len(pages) * 0.5)
    records = []
    current = []

    for page in pages:
        headings = [
            text for text, size, bold in page["styles"] if is_heading(text, size, bold, body_size, noise)
        ]

        numbered_headings = [
            line.strip()
            for line in page["text"].splitlines()
            if NUMBERED.match(line.strip()) and not re.search(r"\.{3,}", line)
        ]

        if numbered_headings:
            headings = numbered_headings
        current = headings[-1:] or current
        text = with_tables(
            clean_text(drop_lines(page["text"], noise)),
            page["tables"],
        )
        method = page["method"] if text or page["method"] == "needs_ocr" else "empty"

        records.append(
            make_record(
                path,
                page["page"],
                headings or current,
                text,
                page["tables"],
                method,
            )
        )

    return records


NOT_CONTENT = [
    "script",
    "style",
    "noscript",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
]
BLOCKS = ["p", "div", "li", "br", "tr", "h1", "h2", "h3", "h4", "h5", "h6"]


def parse_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_bytes(), "html.parser")

    for tag in soup(NOT_CONTENT):
        tag.decompose()

    root = soup.find("main") or soup.find("article") or soup.body or soup
    tables = []

    for table in root.find_all("table"):
        rows = [[cell.get_text(" ") for cell in row.find_all(["th", "td"])] for row in table.find_all("tr")]
        tables.append(clean_rows(rows))
        table.decompose()

    headings = [clean_text(heading.get_text(" ")) for heading in root.find_all(["h1", "h2", "h3"])]

    for tag in root.find_all(BLOCKS):
        tag.append("\n")

    text = with_tables(clean_text(root.get_text()), tables)
    return [make_record(path, 1, headings, text, tables, "html")]


def parse_text(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headings = [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]
    headings = headings if path.suffix == ".md" else []
    return [make_record(path, 1, headings, clean_text(text), [], "text")]


CODE = {
    ".py",
    ".java",
    ".js",
    ".ts",
    ".go",
    ".c",
    ".cpp",
    ".cs",
    ".kt",
    ".rb",
    ".php",
}
DEFINITION = re.compile(r"^\s*(class|def|func|function|interface|public|private)\b")


def parse_code(path: Path) -> list[dict]:
    """Keep code indentation; use class and function lines as headings."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    headings = [line.strip()[:100] for line in text.splitlines() if DEFINITION.match(line)]
    return [make_record(path, 1, headings[:30], text, [], "code")]


PARSERS = {
    ".pdf": parse_pdf,
    ".html": parse_html,
    ".htm": parse_html,
    ".md": parse_text,
}


def parse_file(path: Path) -> list[dict]:
    suffix = path.suffix.lower()

    if suffix in CODE:
        return parse_code(path)
    if suffix == ".txt":
        return parse_text(path)

    parser = PARSERS.get(suffix)
    return parser(path) if parser else []


def summary(records):
    methods = Counter(record["method"] for record in records)
    parts = [
        f"docs: {len({record['doc_id'] for record in records})}",
        f"pages: {len(records)}",
    ]
    parts += [f"{method}: {count}" for method, count in sorted(methods.items())]
    parts.append(f"tables: {sum(len(record['tables']) for record in records)}")
    return " | ".join(parts)


def duplicate_ids(records):
    """Find doc IDs shared by different files."""
    files = {}

    for record in records:
        files.setdefault(record["doc_id"], set()).add(record["source_file"])

    return sorted(doc_id for doc_id, paths in files.items() if len(paths) > 1)


def main(argv=None) -> list[dict]:
    parser = argparse.ArgumentParser(description="One clean JSON record per page.")
    parser.add_argument("folder", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/parsed/pages.jsonl"),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="stop after N pages (0 = all)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=5,
        help="records in sample_pages.json",
    )
    args = parser.parse_args(argv)
    records = []

    for path in sorted(item for item in args.folder.rglob("*") if item.is_file()):
        try:
            records += parse_file(path)
        except Exception as exc:
            print(f"BROKEN  {path}  {type(exc).__name__}: {exc}")

        if args.limit and len(records) >= args.limit:
            records = records[: args.limit]
            break

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    sample = args.out.with_name("sample_pages.json")
    sample_json = json.dumps(
        records[: args.sample],
        ensure_ascii=False,
        indent=2,
    )
    sample.write_text(sample_json, encoding="utf-8")

    print(summary(records))

    for doc_id in duplicate_ids(records):
        print(f"WARNING  two files share doc_id {doc_id}: rename one")

    print(f"wrote {args.out} and {sample}")
    return records


if __name__ == "__main__":
    main()
