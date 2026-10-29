
import json
import time
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.cost import log_call
from app.llm.base import LLMError, StreamResult
from app.llm.factory import build_provider
from app.schemas import ChatRequest
from app.usage import get_usage

app = FastAPI(title="Examate RAG starter", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness check."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.post("/chat")
async def chat(request: ChatRequest, settings: SettingsDep) -> StreamingResponse:
    provider = build_provider(settings)
    result = StreamResult()
    started = time.perf_counter()

    async def event_stream() -> AsyncIterator[str]:
        
        ok = False

        try:
            async for piece in provider.stream_chat(
                request.messages, request.temperature, result
            ):
                
                yield f"event: token\ndata: {json.dumps({'text': piece})}\n\n"

            ok = True
            yield (
                "event: done\ndata: "
                + json.dumps(
                    {
                        "model": result.model or provider.model,
                        "provider": provider.name,
                        "usage": result.usage.model_dump(),
                        "fallback_used": result.fallback_used,
                    }
                )
                + "\n\n"
            )

        except LLMError as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            log_call(
                settings.cost_log_path,
                provider=provider.name,
                model=result.model or provider.model,
                usage=result.usage,
                latency_ms=latency_ms,
                price_in_per_m=settings.price_input_per_million,
                price_out_per_m=settings.price_output_per_million,
                ok=ok,
                fallback_used=result.fallback_used,
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/usage")
def usage(settings: SettingsDep) -> dict:
    """Daily token and cost totals."""
    return get_usage(settings.cost_log_path)
