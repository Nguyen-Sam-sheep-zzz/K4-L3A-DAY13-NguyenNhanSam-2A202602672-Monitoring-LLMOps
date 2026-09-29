from datetime import datetime, timedelta, timezone

from app.demo_data import summarize_logs


def test_dashboard_uses_recent_logs_and_computes_six_panels() -> None:
    now = datetime.now(timezone.utc)
    recent = now.isoformat()
    old = (now - timedelta(hours=2)).isoformat()
    records = [
        {"ts": old, "event": "request_received"},
        {"ts": recent, "event": "request_received", "correlation_id": "req-a1234567"},
        {"ts": recent, "event": "request_received", "correlation_id": "req-b1234567"},
        {"ts": recent, "event": "response_sent", "latency_ms": 100, "ttft_ms": 20, "cost_usd": 0.001, "tokens_in": 10, "tokens_out": 20, "quality_score": 0.8, "tool_success": True},
        {"ts": recent, "event": "request_failed", "error_type": "RuntimeError", "tool_success": False},
    ]

    result = summarize_logs(records, now=now)

    assert result["traffic"] == 2
    assert result["latency_p95"] == 100
    assert result["error_rate_pct"] == 50
    assert result["retrieval_success_rate_pct"] == 50
    assert result["total_cost_usd"] == 0.001
    assert result["tokens_in_total"] == 10
    assert result["quality_avg"] == 0.8
