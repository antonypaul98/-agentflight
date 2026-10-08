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
