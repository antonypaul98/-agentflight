from agentflight.result import CheckResult


def test_check_result_is_immutable_and_deterministic() -> None:
    first = CheckResult(True, "ok", "verified")
    second = CheckResult(True, "ok", "verified")

    assert first == second
    assert first.passed is True
    assert first.code == "ok"
    assert first.detail == "verified"
