import json
import os
import threading
import time
from collections import Counter
from typing import Any

from utils.path_tools import get_abs_path

_METRICS_FILE = get_abs_path("logs/metrics_events.jsonl")
_LOCK = threading.Lock()


def _ensure_parent():
    os.makedirs(os.path.dirname(_METRICS_FILE), exist_ok=True)


def track_event(event: dict[str, Any]):
    _ensure_parent()
    row = {"ts": time.time(), **event}
    with _LOCK:
        with open(_METRICS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_events(limit: int = 500) -> list[dict[str, Any]]:
    if not os.path.exists(_METRICS_FILE):
        return []

    with open(_METRICS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[-limit:]

    events = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def summarize_metrics(limit: int = 500) -> dict[str, Any]:
    events = load_events(limit=limit)

    query_events = [e for e in events if e.get("type") == "query"]
    tool_events = [e for e in events if e.get("type") == "tool"]

    total_queries = len(query_events)
    success_queries = sum(1 for e in query_events if e.get("status") == "success")
    success_rate = (success_queries / total_queries * 100) if total_queries else 0.0

    latencies = [float(e.get("latency_ms", 0)) for e in query_events if e.get("latency_ms") is not None]
    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0

    tool_counter = Counter([e.get("tool", "unknown") for e in tool_events])

    return {
        "total_queries": total_queries,
        "success_queries": success_queries,
        "success_rate": success_rate,
        "avg_latency_ms": avg_latency,
        "tool_counts": dict(tool_counter),
    }
