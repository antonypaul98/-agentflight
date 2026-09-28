from agentflight.contract import CallContract
from agentflight.verifier import verify_call, verify_name


def test_verify_name_accepts_expected_name() -> None:
    result = verify_name(CallContract(name="lookup"), "lookup")
    assert result.passed is True
    assert result.code == "ok"


def test_verify_name_rejects_mismatch() -> None:
    result = verify_name(CallContract(name="lookup"), "other")
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"


def test_verify_call_accepts_required_and_optional_arguments() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query"}),
        optional=frozenset({"limit"}),
    )
    result = verify_call(contract, "lookup", {"query": "agentflight", "limit": 3})
    assert result.passed is True
    assert result.code == "ok"


def test_verify_call_rejects_missing_required_arguments_deterministically() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query", "tenant_id"}),
    )
    result = verify_call(contract, "lookup", {})
    assert result.passed is False
    assert result.code == "missing_required"
    assert result.detail == "query,tenant_id"


def test_verify_call_rejects_unexpected_arguments_deterministically() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query"}),
        optional=frozenset({"limit"}),
    )
    result = verify_call(
        contract,
        "lookup",
        {"query": "agentflight", "z_extra": True, "a_extra": False},
    )
    assert result.passed is False
    assert result.code == "unexpected_argument"
    assert result.detail == "a_extra,z_extra"


def test_verify_call_propagates_name_mismatch() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    result = verify_call(contract, "other", {"query": "agentflight"})
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"
