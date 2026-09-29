from app.mock_llm import FakeLLM


def test_demo_answer_uses_retrieved_monitoring_context() -> None:
    prompt = "Feature=qa\nDocs=Metrics detect incidents, logs identify affected requests, traces localize the root cause.\nQuestion=Explain monitoring"

    result = FakeLLM().generate(prompt)

    assert "metrics" in result.text.lower()
    assert "logs" in result.text.lower()
    assert "traces" in result.text.lower()
    assert "starter answer" not in result.text.lower()
