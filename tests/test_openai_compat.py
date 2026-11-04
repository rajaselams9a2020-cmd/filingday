import json

import httpx
import pytest

from app.llm.base import LLMError, StreamResult
from app.llm.openai_compat import OpenAICompatProvider
from app.schemas import Message


@pytest.mark.anyio
async def test_openai_compatible_provider_reads_sse_and_usage():
    def handler(request):
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer secret"

        payload = {"choices": [{"delta": {"content": "Hi"}}]}
        usage = {
            "choices": [],
            "usage": {
                "prompt_tokens": 2,
                "completion_tokens": 1,
            },
        }

        body = f"data: {json.dumps(payload)}\n\ndata: {json.dumps(usage)}\n\ndata: [DONE]\n\n"
        return httpx.Response(200, text=body)

    provider = OpenAICompatProvider(
        "http://test/v1",
        "secret",
        "provider-model",
        transport=httpx.MockTransport(handler),
    )

    result = StreamResult()
    messages = [Message(role="user", content="Hello")]

    chunks = [chunk async for chunk in provider.stream_chat(messages, 0.2, result)]

    assert "".join(chunks) == "Hi"
    assert result.usage.input_tokens == 2
    assert result.usage.output_tokens == 1
    assert result.usage.estimated is False


@pytest.mark.anyio
async def test_openai_compatible_provider_preserves_status_code():
    def handler(request):
        return httpx.Response(401, text="bad key")

    provider = OpenAICompatProvider(
        "http://test/v1",
        "secret",
        "provider-model",
        max_retries=0,
        transport=httpx.MockTransport(handler),
    )

    result = StreamResult()
    messages = [Message(role="user", content="Hello")]

    with pytest.raises(LLMError):
        async for _ in provider.stream_chat(messages, 0.2, result):
            pass
