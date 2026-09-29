"""Capture matching CP3 metric, log, and Langfuse trace evidence.

Run after the challenge load test, passing its printed correlation IDs.
The private challenge file and credentials stay outside submission/evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from app.challenge import load_challenge


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("correlation_ids", nargs="+", help="IDs printed by the incident load test")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    challenge = load_challenge(ROOT / "config/challenge.json")
    ids = set(args.correlation_ids)
    if len(ids) != len(args.correlation_ids):
        raise SystemExit("Correlation IDs must be unique")

    log_path = ROOT / "data/logs.jsonl"
    logs = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    responses = [r for r in logs if r.get("event") == "response_sent" and r.get("correlation_id") in ids]
    if len(responses) != len(ids):
        raise SystemExit(f"Found {len(responses)}/{len(ids)} response logs")
    responses.sort(key=lambda r: r["ts"])
    slow = [r for r in responses if r["latency_ms"] > challenge.latency_threshold_ms]
    if not slow:
        raise SystemExit("No response exceeds the challenge threshold")

    from langfuse import get_client

    observations = get_client().api.observations.get_many(
        limit=500,
        fields="core,basic,metadata,metrics,model,usage,prompt",
        from_start_time=datetime.now(timezone.utc) - timedelta(hours=2),
    ).data
    selected = None
    for response in slow:
        cid = response["correlation_id"]
        root = next(
            (o for o in observations if o.name == "lab-agent-run" and (o.metadata or {}).get("correlation_id") == cid),
            None,
        )
        if root is None:
            continue
        children = [o for o in observations if str(o.trace_id) == str(root.trace_id) and str(o.parent_observation_id) == str(root.id)]
        if {"retrieval", "llm-generation"}.issubset({o.name for o in children}):
            selected = (response, root, children)
            break
    if selected is None:
        raise SystemExit("No matching Langfuse root with retrieval and generation children")

    response, root, children = selected
    evidence = ROOT / "submission/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    times = f'{responses[0]["ts"]} to {responses[-1]["ts"]}'
    metric = (
        f"Official challenge ID: {challenge.challenge_id}\n"
        f"Cohort: {challenge.cohort}; incident: {challenge.incident}; affected feature: {challenge.affected_feature}\n"
        f"UTC response window: {times}\n"
        f"Affected requests: {len(slow)}/{len(responses)} above {challenge.latency_threshold_ms} ms threshold\n"
        f"Server latency range: {min(r['latency_ms'] for r in responses)}-{max(r['latency_ms'] for r in responses)} ms\n"
        f"Correlation IDs: {', '.join(r['correlation_id'] for r in responses)}\n"
    )
    log = "Official challenge response log (sanitized):\n" + json.dumps(response, ensure_ascii=False, indent=2) + "\n"
    trace = f"Official challenge Langfuse trace ID: {root.trace_id}\nCorrelation ID: {response['correlation_id']}\nRoot: {root.name} ({root.id})\n"
    root_metadata = root.metadata or {}
    trace += (
        f"Prompt source: {root_metadata.get('prompt_source')}\n"
        f"Prompt name/label/version: {root_metadata.get('prompt_name')}/"
        f"{root_metadata.get('prompt_label')}/{root_metadata.get('prompt_version')}\n"
    )
    for child in sorted(children, key=lambda o: o.name):
        trace += f"Child: {child.name}; parent={child.parent_observation_id}; latency_s={getattr(child, 'latency', None)}\n"
        if child.name == "llm-generation":
            trace += (
                f"Model: {getattr(child, 'model', None)}\n"
                f"Usage: {getattr(child, 'usage_details', None)}\n"
                f"Cost: {getattr(child, 'cost_details', None)}\n"
            )
    (evidence / "12-incident-metric.txt").write_text(metric, encoding="utf-8")
    (evidence / "13-incident-log.txt").write_text(log, encoding="utf-8")
    (evidence / "14-incident-trace.txt").write_text(trace, encoding="utf-8")
    print(metric)
    print(trace)


if __name__ == "__main__":
    main()
