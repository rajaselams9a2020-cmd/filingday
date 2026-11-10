import asyncio

import pytest

from app.structured import StructuredOutputError, ask_structured


class ScriptedProvider:
    """Return prepared answers without calling a real model."""

    name = "scripted"
    model = "test-model"

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.calls = 0

    async def stream_chat(self, messages, temperature, result):
        self.calls += 1
        yield self.replies.pop(0)


def test_valid_json_is_accepted():
    provider = ScriptedProvider(
        '{"answer": "GST registration is required", "confidence": 0.9, "sources": ["FAQ, page 2"]}'
    )

    answer = asyncio.run(ask_structured(provider, "When is GST registration required?"))

    assert answer.answer == "GST registration is required"
    assert answer.confidence == 0.9
    assert answer.sources == ["FAQ, page 2"]
    assert provider.calls == 1


def test_invalid_json_is_retried_once():
    provider = ScriptedProvider(
        '{"answer": "Maybe", "confidence": 7}',
        '{"answer": "Check the official document", "confidence": 0.8, "sources": []}',
    )

    answer = asyncio.run(ask_structured(provider, "What is the filing rule?"))

    assert answer.confidence == 0.8
    assert provider.calls == 2


def test_still_invalid_after_retry_raises_error():
    provider = ScriptedProvider(
        "not JSON",
        '{"answer": "Maybe", "confidence": 7}',
    )

    with pytest.raises(StructuredOutputError):
        asyncio.run(ask_structured(provider, "What is the filing rule?"))

    assert provider.calls == 2
