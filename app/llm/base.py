"""The provider abstraction: the rest of the app only knows this interface."""
from collections.abc import AsyncIterator
from typing import Protocol

from app.schemas import Message, Usage


class StreamResult:
    """Collects usage while a stream is consumed."""

    def __init__(self) -> None:
        self.usage = Usage()
        self.model = ""
        self.fallback_used = False


class LLMProvider(Protocol):
    name: str
    model: str

    def stream_chat(
        self, messages: list[Message], temperature: float, result: StreamResult
    ) -> AsyncIterator[str]:
        """Yield text pieces as they arrive; set result.usage before finishing."""
        ...


class LLMError(Exception):
    """Raised when the provider fails after all retries."""


class LLMUnavailable(LLMError):
    """The provider was down, slow or rate-limited after every retry."""