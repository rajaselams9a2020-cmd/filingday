
"""Read cost logs and aggregate LLM usage by UTC date."""
import json
from collections import defaultdict
from pathlib import Path


def get_usage(path: str) -> dict:
    daily = defaultdict(
        lambda: {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0,
        }
    )

    log_path = Path(path)
    if not log_path.exists():
        return {"daily": {}}

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            date = record.get("timestamp", "")[:10]
            if not date:
                continue

            day = daily[date]
            day["calls"] += 1
            day["input_tokens"] += record.get("input_tokens", 0)
            day["output_tokens"] += record.get("output_tokens", 0)
            day["cost"] += record.get("cost", 0.0)

    return {"daily": dict(sorted(daily.items()))}
