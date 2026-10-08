"""Regressions for duplicate normalized contract argument names."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import verify_call


class AlternateHash(str):
    def __new__(cls, value, salt):
        instance = str.__new__(cls, value)
        instance.salt = salt
        return instance

    def __hash__(self):
        return self.salt


def duplicated_names():
    return frozenset({AlternateHash("query", 41), AlternateHash("query", 42)})


def test_duplicate_normalized_required_names_rejected():
    contract = CallContract("lookup", required=duplicated_names())
    assert verify_call(contract, "lookup", {"query": 1}) == CheckResult(
        False, "invalid_contract", "duplicate_argument_name"
    )


def test_duplicate_normalized_optional_names_rejected():
    contract = CallContract("lookup", optional=duplicated_names())
    assert verify_call(contract, "lookup", {}) == CheckResult(
        False, "invalid_contract", "duplicate_argument_name"
    )


def test_duplicate_names_preserve_earlier_validation_precedence():
    contract = CallContract("lookup", required=duplicated_names())
    assert verify_call(contract, "wrong", {}).code == "name_mismatch"
    assert verify_call(contract, "lookup", []).detail == "expected_mapping"
    assert verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=1).code == "too_many_arguments"
    assert verify_call(contract, "lookup", {1: 1}).detail == "non_string_key"


def test_distinct_string_subclass_fields_remain_valid():
    contract = CallContract(
        "lookup",
        required=frozenset({AlternateHash("query", 41)}),
        optional=frozenset({AlternateHash("limit", 42)}),
    )
    assert verify_call(contract, "lookup", {"query": 1, "limit": 2}) == CheckResult(True, "ok")
