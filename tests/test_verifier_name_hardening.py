"""Name-boundary regression tests for tool-call verification."""

import pytest

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import verify_call, verify_name


class CustomName(str):
    def __eq__(self, other):
        raise RuntimeError("equality hook called")

    def __str__(self):
        raise RuntimeError("string hook called")


class CustomObject:
    def __eq__(self, other):
        raise RuntimeError("equality hook called")

    def __str__(self):
        raise RuntimeError("string hook called")


def test_string_subclass_names_bypass_custom_hooks():
    contract = CallContract("lookup")
    assert verify_name(contract, CustomName("lookup")) == CheckResult(True, "ok")
    assert verify_name(contract, CustomName("other")) == CheckResult(False, "name_mismatch", "other")
    assert verify_call(contract, CustomName("lookup"), {}) == CheckResult(True, "ok")


def test_non_string_names_return_deterministic_string_evidence():
    for malformed in (None, 7, [], CustomObject()):
        result = verify_name(CallContract("lookup"), malformed)
        assert result == CheckResult(False, "name_mismatch", "non_string_name")
        assert verify_call(CallContract("lookup"), malformed, {}) == result


def test_invalid_contract_name_does_not_invoke_custom_equality():
    assert verify_name(CallContract(CustomObject()), "lookup") == CheckResult(False, "name_mismatch", "lookup")
    assert verify_name(CallContract(CustomName("lookup")), "lookup") == CheckResult(True, "ok")


def test_name_validation_preserves_argument_bound_precedence():
    with pytest.raises(TypeError, match="max_arguments must be an integer"):
        verify_call(CallContract("lookup"), CustomObject(), [], max_arguments=True)
    assert verify_call(CallContract("lookup"), CustomObject(), []).code == "name_mismatch"
    assert verify_call(CallContract("lookup"), "lookup", []).code == "invalid_arguments"


class HostileBound(int):
    def __lt__(self, other):
        raise AssertionError("custom comparison invoked")
    def __gt__(self, other):
        raise AssertionError("custom comparison invoked")
    def __str__(self):
        raise AssertionError("custom conversion invoked")
    def __int__(self):
        raise AssertionError("custom conversion invoked")
    def __index__(self):
        raise AssertionError("custom conversion invoked")


def test_int_subclass_bound_is_normalized_without_custom_hooks():
    contract = CallContract("lookup", optional=frozenset({"a", "b"}))
    assert verify_call(contract, "lookup", {"a": 1}, max_arguments=HostileBound(1)) == CheckResult(True, "ok")
    assert verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=HostileBound(1)) == CheckResult(False, "too_many_arguments", "2>1")


def test_negative_int_subclass_bound_raises_value_error_without_hooks():
    with pytest.raises(ValueError, match="max_arguments must be non-negative"):
        verify_call(CallContract("lookup"), "lookup", {}, max_arguments=HostileBound(-1))


def test_bound_validation_precedes_name_and_mapping_checks():
    with pytest.raises(ValueError, match="max_arguments must be non-negative"):
        verify_call(CallContract("lookup"), "other", [], max_arguments=HostileBound(-1))
    assert verify_call(CallContract("lookup"), "other", [], max_arguments=HostileBound(1)).code == "name_mismatch"
