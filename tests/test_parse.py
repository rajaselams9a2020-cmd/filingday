from pathlib import Path

import pytest
from sample_docs import make_sample_html, make_sample_pdf

import app.ingest.parse as parse
from app.ingest.clean import clean_text


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    make_sample_pdf(tmp_path / "demo-bank_2026_policy.pdf")
    make_sample_html(tmp_path / "guide.html")
    return tmp_path


@pytest.fixture
def pdf_pages(docs: Path) -> list[dict]:
    return parse.parse_pdf(docs / "demo-bank_2026_policy.pdf")


def test_one_record_per_page_with_page_numbers(pdf_pages: list[dict]) -> None:
    assert len(pdf_pages) == 3
    assert [page["page"] for page in pdf_pages] == [1, 2, 3]
    assert all(page["source_file"].endswith("demo-bank_2026_policy.pdf") for page in pdf_pages)


def test_headings_found(pdf_pages: list[dict]) -> None:
    assert pdf_pages[0]["headings"] == [
        "1. Account opening",
        "1.1 Documents needed",
    ]
    assert pdf_pages[1]["headings"] == ["2. Fees and charges"]


def test_text_is_cleaned(pdf_pages: list[dict]) -> None:
    text = pdf_pages[0]["text"]
    assert "regulation issued" in text
    assert "Customer Policy 2026" not in text
    assert "Page 1 of 3" not in text
    assert "\n42\n" not in f"\n{text}\n"


def test_table_extracted_as_rows(pdf_pages: list[dict]) -> None:
    assert pdf_pages[1]["tables"] == [
        [
            ["Service", "Fee (Rs)"],
            ["Cheque book", "150"],
            ["Duplicate statement", "100"],
        ]
    ]
    assert "Cheque book | 150" in pdf_pages[1]["text"]
    assert pdf_pages[1]["text"].count("Cheque book") == 1


@pytest.mark.skipif(parse.TESSERACT is None, reason="Tesseract is not installed")
def test_scanned_page_goes_through_ocr(pdf_pages: list[dict]) -> None:
    page = pdf_pages[2]
    assert page["method"] == "ocr"
    assert "seven working days" in page["text"]
    assert page["headings"] == ["3. Refunds"]


def test_scanned_page_flagged_without_tesseract(docs: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parse, "TESSERACT", None)
    page = parse.parse_pdf(docs / "demo-bank_2026_policy.pdf")[2]
    assert page["method"] == "needs_ocr"
    assert page["text"] == ""
    assert page["headings"] == ["2. Fees and charges"]


def test_html_keeps_content_and_drops_noise(docs: Path) -> None:
    records = parse.parse_file(docs / "guide.html")
    page = records[0]

    assert page["method"] == "html"
    assert page["headings"] == ["GST Guide", "Registration documents"]
    assert "Menu noise" not in page["text"]
    assert "Footer noise" not in page["text"]
    assert "Ignore this script" not in page["text"]
    assert "Service | 150" in page["text"]


def test_clean_text_rules() -> None:
    text = clean_text("ﬁle\u00ad\nregu-\nlation\n\n\nPage 7 of 40\n42")
    assert text == "file\nregulation"


def test_command_line_writes_jsonl_and_sample(docs: Path, tmp_path: Path) -> None:
    output = tmp_path / "parsed" / "pages.jsonl"
    records = parse.main([str(docs), "--out", str(output), "--sample", "2"])

    assert len(records) == 4
    assert output.exists()
    assert len(output.read_text(encoding="utf-8").splitlines()) == 4
    assert output.with_name("sample_pages.json").exists()


def test_duplicate_doc_ids_are_reported(tmp_path: Path) -> None:
    first = tmp_path / "client_a" / "faq.html"
    second = tmp_path / "client_b" / "faq.html"
    first.parent.mkdir()
    second.parent.mkdir()
    make_sample_html(first)
    make_sample_html(second)

    records = parse.parse_file(first) + parse.parse_file(second)
    assert parse.duplicate_ids(records) == ["faq"]
