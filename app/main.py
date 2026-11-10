import json
import time
from collections.abc import AsyncIterator
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import Settings, get_settings
from app.cost import log_call
from app.llm.base import LLMError, StreamResult
from app.llm.factory import build_provider
from app.rag.context import build_context, build_rag_messages
from app.rag.ingest import extract_pdf_text
from app.rag.retriever import retrieve
from app.schemas import ChatRequest
from app.usage import get_usage

app = FastAPI(title="Examate RAG starter", version="0.1.0")
@app.get("/")
def root() -> dict:
    return {
        "message": "You are on FilingDay root page",
        "status": "ok",
    }


SettingsDep = Annotated[Settings, Depends(get_settings)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness check."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/ready")
def ready(settings: SettingsDep):
    """Readiness check for the database."""
    if not settings.database_url:
        return {"status": "ready", "database": "not configured"}

    try:
        with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": "unavailable"},
        )


@app.post("/chat")
async def chat(request: ChatRequest, settings: SettingsDep) -> StreamingResponse:

    pdf_path = "data/gst_docs/faqs-registration.pdf"
    pages = extract_pdf_text(pdf_path)

    user_questions = [message.content for message in request.messages if message.role == "user"]

    if user_questions:
        relevant_pages = retrieve(user_questions[-1], pages, top_k=3)
    else:
        relevant_pages = []

    context = build_context(relevant_pages)
    rag_messages = build_rag_messages(request.messages, context)

    provider = build_provider(settings)
    result = StreamResult()
    started = time.perf_counter()

    async def event_stream() -> AsyncIterator[str]:
        ok = False

        try:
            async for piece in provider.stream_chat(
                rag_messages,
                request.temperature,
                result,
            ):
                yield f"event: token\ndata: {json.dumps({'text': piece})}\n\n"

            ok = True

        except LLMError as exc:
            yield f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n"

        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            record = log_call(
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

        yield (
            "event: done\ndata: "
            + json.dumps(
                {
                    "model": result.model or provider.model,
                    "provider": provider.name,
                    "usage": result.usage.model_dump(),
                    "cost_usd": record["cost"],
                    "fallback_used": result.fallback_used,
                }
            )
            + "\n\n"
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
