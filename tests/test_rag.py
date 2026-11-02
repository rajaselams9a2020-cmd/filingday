from app.rag.context import build_context, build_rag_messages
from app.rag.ingest import extract_pdf_text
from app.rag.retriever import retrieve, tokenize
from app.schemas import Message


def test_tokenize_converts_to_lowercase():
    assert tokenize("GST India") == {"gst", "india"}


def test_retrieve_returns_matching_page():
    pages = [
        {
            "source": "gst.pdf",
            "page": 1,
            "text": "GST registration and GSTIN requirements",
        },
        {
            "source": "gst.pdf",
            "page": 2,
            "text": "Income tax deductions",
        },
    ]

    results = retrieve("GST registration", pages)

    assert results
    assert results[0]["page"] == 1


def test_retrieve_returns_empty_when_nothing_matches():
    assert retrieve("customs tariff", []) == []


def test_extract_pdf_text_missing_file(tmp_path):
    missing_file = tmp_path / "missing.pdf"

    try:
        extract_pdf_text(missing_file)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Expected FileNotFoundError")


def test_retrieve_from_gst_pdf():
    pages = extract_pdf_text("data/gst_docs/faqs-registration.pdf")

    results = retrieve("GST registration", pages, top_k=3)

    assert len(results) > 0
    assert any("registration" in page["text"].lower() for page in results)
def test_build_context_includes_source_and_page():
    pages = [
        {
            "source": "gst.pdf",
            "page": 5,
            "text": "GST registration requirements",
        }
    ]

    context = build_context(pages)

    assert "gst.pdf" in context
    assert "Page: 5" in context
    assert "GST registration requirements" in context


def test_build_context_handles_empty_pages():
    context = build_context([])

    assert context == "No relevant information found in the GST documents."
def test_build_rag_messages_adds_system_context():
    messages = [
        Message(role="user", content="How to register for GST?")
    ]

    context = "[Source: gst.pdf, Page: 5]\nGST registration requirements"

    results = build_rag_messages(messages, context)

    assert results[0].role == "system"
    assert "GST DOCUMENT CONTEXT" in results[0].content
    assert results[1].content == "How to register for GST?"


def test_build_rag_messages_preserves_existing_system_message():
    messages = [
        Message(role="system", content="You are a helpful assistant."),
        Message(role="user", content="Explain GST registration."),
    ]

    results = build_rag_messages(messages, "GST context")

    assert len(results) == 2
    assert "You are a helpful assistant." in results[0].content
    assert "GST context" in results[0].content