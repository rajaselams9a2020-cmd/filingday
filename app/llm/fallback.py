
"""Fallback to a secondary provider only for transient failures before output."""
from collections.abc import AsyncIterator

from app.llm.base import LLMUnavailable, StreamResult
from app.schemas import Message


class FallbackProvider:
    def __init__(self, primary, fallback) -> None:
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name
        self.model = primary.model

    async def stream_chat(
        self,
        messages: list[Message],
        temperature: float,
        result: StreamResult,
    ) -> AsyncIterator[str]:
        yielded = False

        try:
            async for piece in self.primary.stream_chat(
                messages, temperature, result
            ):
                yielded = True
                yield piece

        except LLMUnavailable:
            if yielded:
                raise

            result.fallback_used = True
            result.usage = type(result.usage)()
            result.model = self.fallback.model

            async for piece in self.fallback.stream_chat(
                messages, temperature, result
            ):
                yield piece

            result.model = self.fallback.model
