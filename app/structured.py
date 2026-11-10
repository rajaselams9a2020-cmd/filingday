"""Ask the LLM for JSON and validate its answer with Pydantic."""

import json

from pydantic import ValidationError

from app.llm.base import LLMError, StreamResult
from app.schemas import Message, StructuredAnswer

JSON_INSTRUCTIONS = (
    "Reply with JSON only, no markdown or extra text, in this shape: "
    '{"answer": "<text>", "confidence": <number from 0 to 1>, '
    '"sources": ["<source>", ...]}'
)


class StructuredOutputError(LLMError):
    """Raised when the model returns invalid JSON after one retry."""


def extract_json(text: str) -> str:
    """Extract a JSON object if the model wrapped it in extra text."""
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        return text

    return text[start : end + 1]


async def complete(provider, messages: list[Message], temperature: float) -> str:
    """Collect the text pieces returned by a provider."""
    result = StreamResult()
    pieces = []

    async for piece in provider.stream_chat(messages, temperature, result):
        pieces.append(piece)

    return "".join(pieces)


async def ask_structured(
    provider,
    question: str,
    context: str = "",
) -> StructuredAnswer:
    """Ask for a structured answer, retry once if validation fails."""
    prompt = JSON_INSTRUCTIONS

    if context:
        prompt += f"\nUse this context and cite its sources:\n{context}"

    messages = [
        Message(role="system", content=prompt),
        Message(role="user", content=question),
    ]

    for attempt in range(2):
        text = await complete(provider, messages, temperature=0.0)

        try:
            return StructuredAnswer.model_validate_json(extract_json(text))
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            if attempt == 1:
                raise StructuredOutputError(f"Model returned invalid structured output: {exc}") from exc

            messages.extend(
                [
                    Message(role="assistant", content=text),
                    Message(
                        role="user",
                        content=f"Your previous answer was invalid: {exc}. {JSON_INSTRUCTIONS}",
                    ),
                ]
            )

    raise AssertionError("Unreachable")
