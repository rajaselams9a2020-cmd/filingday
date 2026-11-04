"""Extract text from PDF files for the GST RAG pipeline."""

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: str | Path) -> list[dict]:
    """Extract non-empty page text and preserve page numbers and source name."""
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(str(path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        if text:
            pages.append(
                {
                    "source": path.name,
                    "page": page_number,
                    "text": text,
                }
            )

    return pages
