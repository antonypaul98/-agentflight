"""Regression coverage for bounded untrusted contract declarations."""

from agentflight.contract import CallContract
from agentflight.verifier import MAX_DECLARED_ARGUMENTS, verify_call


def _names(count: int) -> frozenset[str]:
    return frozenset(f"field_{index}" for index in range(count))


def test_rejects_oversized_required_contract_without_large_evidence() -> None:
    contract = CallContract(name="lookup", required=_names(MAX_DECLARED_ARGUMENTS + 1))
    result = verify_call(contract, "lookup", {})
    assert (result.passed, result.code, result.detail) == (
        False, "invalid_contract", "too_many_declared_arguments"
    )


def test_rejects_oversized_optional_contract() -> None:
    contract = CallContract(name="lookup", optional=set(_names(MAX_DECLARED_ARGUMENTS + 1)))
    result = verify_call(contract, "lookup", {})
    assert (result.passed, result.code, result.detail) == (
        False, "invalid_contract", "too_many_declared_arguments"
    )


def test_accepts_schema_at_exact_declaration_limit() -> None:
    contract = CallContract(name="lookup", optional=_names(MAX_DECLARED_ARGUMENTS))
    result = verify_call(contract, "lookup", {})
    assert (result.passed, result.code) == (True, "ok")


def test_uses_native_set_length_not_hostile_subclass_length() -> None:
    class MisreportedSet(set):
        def __len__(self):
            return 0

    contract = CallContract(name="lookup", optional=MisreportedSet(_names(MAX_DECLARED_ARGUMENTS + 1)))
    result = verify_call(contract, "lookup", {})
    assert (result.passed, result.code, result.detail) == (
        False, "invalid_contract", "too_many_declared_arguments"
    )


def test_preserves_name_and_argument_limit_precedence() -> None:
    contract = CallContract(name="lookup", optional=_names(MAX_DECLARED_ARGUMENTS + 1))
    assert verify_call(contract, "other", {}).code == "name_mismatch"
    result = verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=1)
    assert (result.code, result.detail) == ("too_many_arguments", "2>1")
