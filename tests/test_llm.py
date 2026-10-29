
import asyncio
import json

import httpx

from app.cost import log_call
from app.llm.base import LLMError, LLMUnavailable, StreamResult
from app.llm.fake import FakeProvider
from app.llm.fallback import FallbackProvider
from app.llm.openai_compat import OpenAICompatProvider
from app.schemas import Message, Usage
from app.tokens import estimate_tokens
from app.usage import get_usage


def test_fake_provider_streams_answer():
    async def run_test():
        provider = FakeProvider()
        result = StreamResult()
        messages = [Message(role="user", content="What is GST?")]

        pieces = [
            piece
            async for piece in provider.stream_chat(messages, 0.2, result)
        ]

        assert "What is GST?" in "".join(pieces)
        assert result.usage.input_tokens > 0
        assert result.usage.output_tokens > 0
        assert result.usage.estimated is True

    asyncio.run(run_test())


def test_estimate_tokens():
    assert estimate_tokens("12345678") == 2
    assert estimate_tokens("") == 1


def test_cost_logging_and_usage_aggregation(tmp_path):
    path = str(tmp_path / "cost.jsonl")
    usage = Usage(input_tokens=100, output_tokens=50, estimated=False)

    record = log_call(
        path,
        provider="fake",
        model="fake-model",
        usage=usage,
        latency_ms=120,
        price_in_per_m=2.0,
        price_out_per_m=4.0,
        ok=True,
    )

    assert record["cost"] == 0.0004

    summary = get_usage(path)
    day = next(iter(summary["daily"].values()))
    assert day["calls"] == 1
    assert day["input_tokens"] == 100
    assert day["output_tokens"] == 50
    assert day["cost"] == 0.0004


def test_usage_handles_missing_file(tmp_path):
    assert get_usage(str(tmp_path / "missing.jsonl")) == {"daily": {}}


def test_usage_skips_malformed_json(tmp_path):
    path = tmp_path / "cost.jsonl"
    path.write_text("{bad json}\n", encoding="utf-8")
    assert get_usage(str(path)) == {"daily": {}}


def test_backoff_delay_stays_within_bounds():
    from app.llm.openai_compat import backoff_delay

    for attempt in range(5):
        delay = backoff_delay(attempt, 0.5)
        assert 0 <= delay <= min(8.0, 0.5 * (2**attempt))


def test_openai_compat_retries_server_error():
    async def run_test():
        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(503)
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                text=(
                    'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
                    'data: [DONE]\n\n'
                ),
            )

        provider = OpenAICompatProvider(
            base_url="http://test/v1",
            api_key="test",
            model="test-model",
            max_retries=1,
            backoff_base_seconds=0,
            transport=httpx.MockTransport(handler),
        )
        result = StreamResult()
        messages = [Message(role="user", content="Hi")]

        pieces = [
            piece
            async for piece in provider.stream_chat(messages, 0.2, result)
        ]

        assert calls == 2
        assert "".join(pieces) == "Hello"
        assert result.usage.estimated is True

    asyncio.run(run_test())


def test_openai_compat_does_not_retry_unauthorized():
    async def run_test():
        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            return httpx.Response(401)

        provider = OpenAICompatProvider(
            base_url="http://test/v1",
            api_key="bad-key",
            model="test-model",
            max_retries=2,
            backoff_base_seconds=0,
            transport=httpx.MockTransport(handler),
        )

        try:
            async for _ in provider.stream_chat(
                [Message(role="user", content="Hi")], 0.2, StreamResult()
            ):
                pass
        except LLMError:
            pass
        else:
            raise AssertionError("Expected LLMError")

        assert calls == 1

    asyncio.run(run_test())


def test_openai_compat_retries_timeout_before_output():
    async def run_test():
        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            raise httpx.ReadTimeout("timeout")

        provider = OpenAICompatProvider(
            base_url="http://test/v1",
            api_key="test",
            model="test-model",
            max_retries=2,
            backoff_base_seconds=0,
            transport=httpx.MockTransport(handler),
        )

        try:
            async for _ in provider.stream_chat(
                [Message(role="user", content="Hi")], 0.2, StreamResult()
            ):
                pass
        except LLMUnavailable:
            pass
        else:
            raise AssertionError("Expected LLMUnavailable")

        assert calls == 3

    asyncio.run(run_test())


def test_fallback_used_when_primary_unavailable():
    class BrokenProvider:
        name = "broken"
        model = "broken-model"

        async def stream_chat(self, messages, temperature, result):
            if False:
                yield ""
            raise LLMUnavailable("temporary outage")

    async def run_test():
        primary = BrokenProvider()
        fallback = FakeProvider(model="fallback-model")
        provider = FallbackProvider(primary, fallback)
        result = StreamResult()

        pieces = [
            piece
            async for piece in provider.stream_chat(
                [Message(role="user", content="GST?")], 0.2, result
            )
        ]

        assert "GST?" in "".join(pieces)
        assert result.fallback_used is True
        assert result.model == "fallback-model"

    asyncio.run(run_test())


def test_fallback_not_used_for_non_retryable_error():
    class InvalidRequestProvider:
        name = "invalid"
        model = "invalid-model"

        async def stream_chat(self, messages, temperature, result):
            if False:
                yield ""
            raise LLMError("bad request")

    async def run_test():
        provider = FallbackProvider(
            InvalidRequestProvider(), FakeProvider(model="fallback-model")
        )

        try:
            async for _ in provider.stream_chat(
                [Message(role="user", content="GST?")], 0.2, StreamResult()
            ):
                pass
        except LLMError:
            pass
        else:
            raise AssertionError("Expected LLMError")

    asyncio.run(run_test())


def test_fallback_not_switched_after_output():
    class PartialThenBrokenProvider:
        name = "partial"
        model = "partial-model"

        async def stream_chat(self, messages, temperature, result):
            yield "partial"
            raise LLMUnavailable("connection lost")

    async def run_test():
        provider = FallbackProvider(
            PartialThenBrokenProvider(), FakeProvider(model="fallback-model")
        )
        result = StreamResult()
        pieces = []

        try:
            async for piece in provider.stream_chat(
                [Message(role="user", content="GST?")], 0.2, result
            ):
                pieces.append(piece)
        except LLMUnavailable:
            pass
        else:
            raise AssertionError("Expected LLMUnavailable")

        assert pieces == ["partial"]
        assert result.fallback_used is False

    asyncio.run(run_test())


def test_cost_log_is_append_only(tmp_path):
    path = str(tmp_path / "cost.jsonl")
    usage = Usage(input_tokens=10, output_tokens=5)

    for _ in range(2):
        log_call(
            path,
            provider="fake",
            model="fake-model",
            usage=usage,
            latency_ms=10,
            price_in_per_m=0,
            price_out_per_m=0,
            ok=True,
        )

    lines = (tmp_path / "cost.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all(isinstance(json.loads(line), dict) for line in lines)


def test_chat_request_validation():
    from pydantic import ValidationError

    from app.schemas import ChatRequest

    try:
        ChatRequest(messages=[])
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected ValidationError")
