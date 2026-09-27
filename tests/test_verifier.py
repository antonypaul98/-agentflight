from agentflight.contract import CallContract
from agentflight.verifier import verify_name


def test_verify_name_accepts_expected_name() -> None:
    result = verify_name(CallContract(name="lookup"), "lookup")
    assert result.passed is True
    assert result.code == "ok"


def test_verify_name_rejects_mismatch() -> None:
    result = verify_name(CallContract(name="lookup"), "other")
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"
