from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=20_000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    estimated: bool = False


class StructuredAnswer(BaseModel):
    """Example of a structured output schema validated with Pydantic."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = [] 
