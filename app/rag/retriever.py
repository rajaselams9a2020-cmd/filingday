"""Keyword-based retrieval with stopword removal and IDF scoring."""

import math
import re
from collections import Counter

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "do",
    "does",
    "required",
}


def tokenize(text: str) -> set[str]:
    """Convert text into lowercase tokens and remove common words."""
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return {word for word in words if word not in STOPWORDS}


def retrieve(
    question: str,
    pages: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """Return relevant pages using inverse document frequency scoring."""
    if top_k <= 0 or not pages:
        return []

    question_tokens = tokenize(question)

    if not question_tokens:
        return []

    page_tokens = [tokenize(page.get("text", "")) for page in pages]

    document_frequency = Counter(token for tokens in page_tokens for token in tokens)

    scored_pages = []

    for page, tokens in zip(pages, page_tokens, strict=True):
        matched_tokens = question_tokens & tokens

        if not matched_tokens:
            continue

        score = sum(math.log(1 + len(pages) / (1 + document_frequency[token])) for token in matched_tokens)

        scored_pages.append((score, page))

    scored_pages.sort(key=lambda item: item[0], reverse=True)

    return [page for _, page in scored_pages[:top_k]]
