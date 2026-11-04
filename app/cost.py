
"""Append one JSON record per LLM call for cost tracking."""
import json
from datetime import UTC, datetime
from pathlib import Path

from app.schemas import Usage


def cost_usd(
    usage: Usage,
    price_in_per_m: float,
    price_out_per_m: float,
) -> float:
    return (
        usage.input_tokens * price_in_per_m
        + usage.output_tokens * price_out_per_m
    ) / 1_000_000
def log_call(
    path: str,
    *,
    provider: str,
    model: str,
    usage: Usage,
    latency_ms: int,
    price_in_per_m: float,
    price_out_per_m: float,
    ok: bool,
    fallback_used: bool = False,
) -> dict:
    cost = cost_usd(usage, price_in_per_m, price_out_per_m)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "estimated": usage.estimated,
        "latency_ms": latency_ms,
        "cost": cost,
        "ok": ok,
        "fallback_used": fallback_used,
    }

    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    return record