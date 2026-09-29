from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Any

from .metrics import percentile


def summarize_logs(records: list[dict[str, Any]], *, now: datetime | None = None) -> dict[str, Any]:
    """Build the six dashboard panels from the last 60 minutes of JSONL events."""
    current = now or datetime.now(timezone.utc)
    cutoff = current - timedelta(minutes=60)
    recent: list[dict[str, Any]] = []
    for record in records:
        try:
            timestamp = datetime.fromisoformat(str(record["ts"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            continue
        if timestamp.tzinfo is None:
            continue
        if cutoff <= timestamp <= current:
            recent.append(record)

    incoming = [r for r in recent if r.get("event") == "request_received"]
    responses = [r for r in recent if r.get("event") == "response_sent"]
    failures = [r for r in recent if r.get("event") == "request_failed"]
    retrieval = [r for r in responses + failures if r.get("tool_success") is not None]

    def numeric(field: str) -> list[float]:
        return [float(r[field]) for r in responses if isinstance(r.get(field), (int, float))]

    latencies = numeric("latency_ms")
    ttfts = numeric("ttft_ms")
    costs = numeric("cost_usd")
    qualities = numeric("quality_score")
    error_breakdown = Counter(str(r.get("error_type", "Unknown")) for r in failures)
    count = len(incoming)
    retrieval_success = sum(r.get("tool_success") is True for r in retrieval)
    return {
        "traffic": count,
        "rate_per_minute": round(count / 60, 3),
        "latency_p50": percentile(latencies, 50),
        "latency_p95": percentile(latencies, 95),
        "latency_p99": percentile(latencies, 99),
        "ttft_p95": percentile(ttfts, 95),
        "error_rate_pct": round(len(failures) / count * 100, 2) if count else 0.0,
        "error_breakdown": dict(error_breakdown),
        "retrieval_success_rate_pct": round(retrieval_success / len(retrieval) * 100, 2) if retrieval else 0.0,
        "total_cost_usd": round(sum(costs), 6),
        "tokens_in_total": sum(numeric("tokens_in")),
        "tokens_out_total": sum(numeric("tokens_out")),
        "quality_avg": round(mean(qualities), 3) if qualities else 0.0,
    }
