"""Prevent split required/optional declarations from bypassing the schema cap."""

from agentflight.contract import CallContract
from agentflight.verifier import MAX_DECLARED_ARGUMENTS, verify_call


def names(start: int, count: int) -> frozenset[str]:
    return frozenset(f"field_{index:04d}" for index in range(start, start + count))


def test_combined_required_and_optional_exceed_ceiling():
    contract = CallContract("lookup", required=names(0, 512), optional=names(512, 513))
    result = verify_call(contract, "lookup", {})
    assert (result.passed, result.code, result.detail) == (
        False, "invalid_contract", "too_many_declared_arguments"
    )


def test_combined_declarations_at_exact_ceiling_remain_valid():
    contract = CallContract("lookup", required=names(0, 1), optional=names(1, MAX_DECLARED_ARGUMENTS - 1))
    assert verify_call(contract, "lookup", {"field_0000": 1}).passed


def test_overlap_precedes_combined_size_check():
    contract = CallContract("lookup", required=names(0, 512), optional=names(511, 513))
    result = verify_call(contract, "lookup", {})
    assert (result.code, result.detail) == ("invalid_contract", "duplicate_argument_name")


def test_name_and_argument_limit_precedence_preserved():
    contract = CallContract("lookup", required=names(0, 512), optional=names(512, 513))
    assert verify_call(contract, "wrong", {}).code == "name_mismatch"
    assert verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=1).code == "too_many_arguments"
