"""A deterministic provider for tests, CI and offline demos. No network, no key."""
import asyncio
from collections.abc import AsyncIterator

from app.llm.base import StreamResult
from app.schemas import Message, Usage
from app.tokens import estimate_tokens


class FakeProvider:
    name = "fake"

    def __init__(self, model: str = "fake-model", delay_seconds: float = 0.0) -> None:
        self.model = model
        self.delay_seconds = delay_seconds

    async def stream_chat(
        self, messages: list[Message], temperature: float, result: StreamResult
    ) -> AsyncIterator[str]:
        question = messages[-1].content
        reply = f"You asked: {question}. This is a fake answer for testing."

        for word in reply.split(" "):
            if self.delay_seconds:
                await asyncio.sleep(self.delay_seconds)
            yield word + " "

        result.usage = Usage(
            input_tokens=sum(estimate_tokens(m.content) for m in messages),
            output_tokens=estimate_tokens(reply),
            estimated=True,
        )