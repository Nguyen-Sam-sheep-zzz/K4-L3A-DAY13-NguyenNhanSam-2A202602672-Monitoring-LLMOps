from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from app import logging_config
from app.main import app


def _request(path: str, method: str = "GET", **kwargs) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def test_request_id_is_generated_and_returned_with_timing_header(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _request(
        "/chat",
        "POST",
        json={
            "user_id": "student-01",
            "session_id": "session-01",
            "feature": "qa",
            "message": "Explain monitoring",
        },
    )

    assert response.status_code == 200
    correlation_id = response.headers["x-request-id"]
    assert correlation_id.startswith("req-")
    assert len(correlation_id) == 12
    assert response.headers["x-response-time-ms"].isdigit()
    assert response.json()["correlation_id"] == correlation_id


def test_supplied_request_id_is_preserved(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _request(
        "/health",
        headers={"x-request-id": "req-abcdef12"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-abcdef12"


def test_scrubber_removes_pii_from_nested_and_top_level_fields() -> None:
    scrubbed = logging_config.scrub_event(
        None,
        "info",
        {
            "event": "contact student@example.com",
            "detail": "Call 090 123 4567",
            "payload": {"nested": "CCCD 012345678901"},
        },
    )

    rendered = json.dumps(scrubbed, ensure_ascii=False)
    assert "student@example.com" not in rendered
    assert "090 123 4567" not in rendered
    assert "012345678901" not in rendered
    assert "REDACTED_EMAIL" in rendered
    assert "REDACTED_PHONE_VN" in rendered
    assert "REDACTED_CCCD" in rendered


def test_demo_endpoints_expose_safe_summary_and_html() -> None:
    page = _request("/demo")
    summary = _request("/demo/summary")

    assert page.status_code == 200
    assert "Monitoring & LLMOps Demo" in page.text
    assert summary.status_code == 200
    payload = summary.json()
    assert set(payload) == {"metrics", "recent_logs", "tracing_enabled", "langfuse_base_url"}
    assert isinstance(payload["recent_logs"], list)
    assert all("LANGFUSE_SECRET_KEY" not in json.dumps(item) for item in payload["recent_logs"])
