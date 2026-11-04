import pytest

from app.llm.base import LLMUnavailable, StreamResult
from app.llm.fake import FakeProvider
from app.llm.fallback import FallbackProvider
from app.schemas import Message


class FailingProvider:
    name = "primary"
    model = "primary-model"

    async def stream_chat(self, messages, temperature, result):
        raise LLMUnavailable("Primary provider unavailable")
        yield  # Makes this an async generator.


@pytest.mark.anyio
async def test_fallback_runs_when_primary_is_unavailable():
    primary = FailingProvider()
    fallback = FakeProvider(model="fallback-model")
    provider = FallbackProvider(primary, fallback)

    result = StreamResult()
    messages = [Message(role="user", content="Hello")]

    chunks = [chunk async for chunk in provider.stream_chat(messages, 0.2, result)]

    assert "".join(chunks).startswith("You asked: Hello")
    assert result.fallback_used is True
    assert result.model == "fallback-model"


@pytest.mark.anyio
async def test_fallback_does_not_run_after_partial_output():
    class PartialFailureProvider:
        name = "primary"
        model = "primary-model"

        async def stream_chat(self, messages, temperature, result):
            yield "Partial"
            raise LLMUnavailable("Connection lost")

    fallback = FakeProvider(model="fallback-model")
    provider = FallbackProvider(PartialFailureProvider(), fallback)

    result = StreamResult()
    messages = [Message(role="user", content="Hello")]
    received = []

    with pytest.raises(LLMUnavailable):
        async for chunk in provider.stream_chat(messages, 0.2, result):
            received.append(chunk)

    assert received == ["Partial"]
    assert result.fallback_used is False
