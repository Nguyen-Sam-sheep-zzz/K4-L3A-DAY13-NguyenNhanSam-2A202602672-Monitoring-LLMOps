# Day 13 Monitoring & LLMOps Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete the required observability behaviors and provide a browser demo that explains the Metrics → Logs → Traces workflow.

**Architecture:** Keep the existing FastAPI contracts and local fake LLM. Add correlation and PII-safe logging at the middleware/configuration boundary, child observations around retrieval and generation, and a static browser UI served by the same API. The UI reads the existing metrics and JSONL logs so it remains useful with or without a live Langfuse project.

**Tech Stack:** Python 3.11, FastAPI, structlog, Langfuse Python SDK v4, vanilla HTML/CSS/JavaScript, pytest, YAML.

**Spec:** Approved design in the conversation on 2026-09-29.

## Global Constraints

- Preserve `/health`, `/metrics`, and `/chat` request/response contracts.
- Never capture raw user prompts, answers, API keys, or PII in trace metadata.
- Keep `config/challenge.json` untouched and untracked.
- Keep Langfuse optional at runtime through the existing local fallback.
- Dashboard contract remains exactly six panels with a 60-minute window.

---

### Task 1: Correlation and PII-safe logging

**Files:**
- Modify: `app/middleware.py`
- Modify: `app/logging_config.py`
- Modify: `app/main.py`
- Modify: `app/pii.py`
- Test: `tests/test_logging_and_demo.py`

- [ ] Write failing tests for generated/request correlation IDs, response headers, recursive PII scrubbing, and enriched request logs.
- [ ] Implement middleware context cleanup, ID validation/generation, context binding, and response timing headers.
- [ ] Register recursive scrubbing before JSON rendering and bind request metadata before `request_received`.
- [ ] Run focused tests and then the log validator against fresh logs.

### Task 2: Child tracing observations

**Files:**
- Modify: `app/tracing.py`
- Modify: `app/agent.py`
- Test: `tests/test_tracing_adapter.py`

- [ ] Write a failing test for the child observation adapter.
- [ ] Add a no-op-safe context helper over Langfuse v4 `start_as_current_observation`.
- [ ] Wrap retrieval as a `retriever` observation and the fake model call as a `generation` observation with usage and cost.
- [ ] Run focused tracing tests and a local request smoke test.

### Task 3: Browser demo and incident walkthrough

**Files:**
- Create: `app/demo_ui.py`
- Modify: `app/main.py`
- Test: `tests/test_logging_and_demo.py`
- Modify: `README.md`

- [ ] Write failing tests for `/demo`, `/demo/summary`, and safe recent-log output.
- [ ] Implement responsive tabs for chat, observability, incident walkthrough, and presentation guide.
- [ ] Add JSON summary endpoints that expose metrics and sanitized recent logs only.
- [ ] Document the exact run commands and presentation flow.

### Task 4: SLO, alerts, runbook, and report scaffold

**Files:**
- Modify: `config/alert_rules.yaml`
- Modify: `docs/alerts.md`
- Modify: `submission/REPORT.md`

- [ ] Replace alert placeholders with three symptom-based rules and owners/runbooks.
- [ ] Document investigation and mitigation steps.
- [ ] Add a report section explaining how to use the demo and leave runtime-specific evidence fields explicit.

### Task 5: Verification

- [ ] Run `python -m pytest -q` with the available workspace interpreter.
- [ ] Run `python scripts/validate_logs.py` on fresh generated logs.
- [ ] Run `python scripts/validate_dashboard.py`.
- [ ] Run an API smoke test for `/health`, `/chat`, `/metrics`, and `/demo`.
- [ ] Inspect `git diff` and confirm no secret, `.env`, or challenge file is included.
