"""Zero and default cardinality boundaries for tool-call verification."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import DEFAULT_MAX_ARGUMENTS, verify_call


def test_zero_bound_accepts_empty_arguments():
    assert verify_call(CallContract("lookup"), "lookup", {}, max_arguments=0) == CheckResult(True, "ok")


def test_zero_bound_rejects_single_argument_before_contract_checks():
    result = verify_call(CallContract("lookup", required=frozenset({"query"})), "lookup", {"query": "x"}, max_arguments=0)
    assert result == CheckResult(False, "too_many_arguments", "1>0")


def test_default_bound_accepts_exactly_64_optional_arguments():
    names = tuple(f"field_{i:03d}" for i in range(DEFAULT_MAX_ARGUMENTS))
    contract = CallContract("lookup", optional=frozenset(names))
    assert verify_call(contract, "lookup", dict.fromkeys(names)).passed


def test_default_bound_rejects_65_arguments_order_independently():
    names = tuple(f"field_{i:03d}" for i in range(DEFAULT_MAX_ARGUMENTS + 1))
    contract = CallContract("lookup", optional=frozenset(names))
    first = verify_call(contract, "lookup", dict.fromkeys(names))
    reversed_order = verify_call(contract, "lookup", dict.fromkeys(reversed(names)))
    assert first == reversed_order == CheckResult(False, "too_many_arguments", "65>64")
