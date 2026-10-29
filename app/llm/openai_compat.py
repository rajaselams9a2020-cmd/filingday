
import asyncio
import json
import random
from collections.abc import AsyncIterator

import httpx

from app.llm.base import LLMError, LLMUnavailable, StreamResult
from app.schemas import Message, Usage
from app.tokens import estimate_tokens

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def backoff_delay(attempt: int, base: float, cap: float = 8.0) -> float:
    return random.uniform(0, min(cap, base * (2**attempt)))


class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float,
        result: StreamResult,
    ) -> AsyncIterator[str]:
        timeout = httpx.Timeout(self.timeout_seconds, connect=5.0)
        payload = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        input_text = "\n".join(message.content for message in messages)
        output_text = ""
        last_error: Exception | None = None

        async with httpx.AsyncClient(
            timeout=timeout,
            transport=self.transport,
        ) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    ) as response:
                        if response.status_code in RETRYABLE_STATUS:
                            last_error = LLMUnavailable(
                                f"Retryable provider status: {response.status_code}"
                            )
                            if attempt < self.max_retries:
                                await asyncio.sleep(
                                    backoff_delay(
                                        attempt, self.backoff_base_seconds
                                    )
                                )
                                continue
                            raise LLMUnavailable(
                                "Provider unavailable after retries"
                            )

                        if response.status_code >= 400:
                            raise LLMError(
                                f"Provider request failed: {response.status_code}"
                            )

                        async for line in response.aiter_lines():
                            if not line.startswith("data:"):
                                continue

                            data = line[5:].strip()
                            if data == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue

                            usage_data = chunk.get("usage")
                            if usage_data:
                                result.usage = Usage(
                                    input_tokens=usage_data.get(
                                        "prompt_tokens", 0
                                    ),
                                    output_tokens=usage_data.get(
                                        "completion_tokens", 0
                                    ),
                                    estimated=False,
                                )

                            choices = chunk.get("choices") or []
                            if choices:
                                delta = choices[0].get("delta") or {}
                                piece = delta.get("content")
                                if piece:
                                    output_text += piece
                                    yield piece

                        result.model = self.model

                        if (
                            result.usage.input_tokens == 0
                            and result.usage.output_tokens == 0
                        ):
                            result.usage = Usage(
                                input_tokens=estimate_tokens(input_text),
                                output_tokens=estimate_tokens(output_text),
                                estimated=True,
                            )
                        return

                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = exc

                    if output_text:
                        raise LLMUnavailable(
                            "Provider connection failed after streaming began"
                        ) from exc

                    if attempt < self.max_retries:
                        await asyncio.sleep(
                            backoff_delay(
                                attempt, self.backoff_base_seconds
                            )
                        )
                        continue

                    raise LLMUnavailable(
                        "Provider unavailable after retries"
                    ) from exc

        raise LLMUnavailable(
            "Provider unavailable after retries"
        ) from last_error
