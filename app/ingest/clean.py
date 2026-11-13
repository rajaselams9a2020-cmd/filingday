"""Clean text that came out of a PDF, an HTML page or OCR."""

import re
import unicodedata
from collections import Counter

# Remove soft hyphen, zero-width space and BOM.
# Keep ZWJ/ZWNJ because Indic scripts need them.
INVISIBLE = dict.fromkeys(map(ord, "\u00ad\u200b\ufeff"), None)

PAGE_NUMBER = re.compile(
    r"^(page\s*)?[-–]?\s*\d+\s*([-–]|of\s+\d+)?$",
    re.IGNORECASE,
)


def clean_text(text: str, page_numbers: bool = True) -> str:
    text = unicodedata.normalize("NFKC", text).translate(INVISIBLE)
    text = re.sub(r"([a-z])-\n([a-z])", r"\1\2", text)

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]

    if page_numbers:
        lines = [line for line in lines if not PAGE_NUMBER.match(line)]

    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def shape(line: str) -> str:
    """Remove numbers so repeated headers with page numbers match."""
    return re.sub(r"[\d\s]+", " ", line).strip()


def repeated_lines(pages: list[str], share: float = 0.5) -> set[str]:
    """Find lines repeated at the top or bottom of at least half the pages."""
    if len(pages) < 3:
        return set()

    seen = Counter()

    for text in pages:
        lines = [line for line in text.splitlines() if line.strip()]
        seen.update({shape(line) for line in lines[:2] + lines[-2:]})

    return {line for line, count in seen.items() if line and count >= share * len(pages)}


def drop_lines(text: str, unwanted: set[str]) -> str:
    return "\n".join(line for line in text.splitlines() if shape(line) not in unwanted)
