"""Regressions for untrusted frozenset-subclass contract declarations."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import MAX_DECLARED_ARGUMENTS, verify_call


class HostileFrozen(frozenset):
    def __len__(self):
        raise AssertionError("untrusted frozenset length hook must not run")

    def __iter__(self):
        raise AssertionError("untrusted frozenset iteration hook must not run")

    def __contains__(self, value):
        raise AssertionError("untrusted frozenset membership hook must not run")


def test_required_frozenset_subclass_is_read_using_native_storage():
    contract = CallContract("lookup", required=HostileFrozen({"query"}))
    assert verify_call(contract, "lookup", {"query": 1}) == CheckResult(True, "ok")
    assert verify_call(contract, "lookup", {}) == CheckResult(False, "missing_required", "query")


def test_optional_frozenset_subclass_rejects_oversized_schema():
    names = HostileFrozen(f"field_{index}" for index in range(MAX_DECLARED_ARGUMENTS + 1))
    contract = CallContract("lookup", optional=names)
    assert verify_call(contract, "lookup", {}) == CheckResult(False, "invalid_contract", "too_many_declared_arguments")


def test_frozenset_subclass_accepts_exact_schema_limit():
    names = HostileFrozen(f"field_{index}" for index in range(MAX_DECLARED_ARGUMENTS))
    contract = CallContract("lookup", optional=names)
    assert verify_call(contract, "lookup", {}) == CheckResult(True, "ok")


def test_frozenset_subclass_rejects_non_string_declarations():
    contract = CallContract("lookup", required=HostileFrozen({"query", 42}))
    assert verify_call(contract, "lookup", {}) == CheckResult(False, "invalid_contract", "non_string_argument_name")


def test_earlier_name_and_cardinality_checks_keep_precedence():
    names = HostileFrozen(f"field_{index}" for index in range(MAX_DECLARED_ARGUMENTS + 1))
    contract = CallContract("lookup", optional=names)
    assert verify_call(contract, "wrong", {}).code == "name_mismatch"
    assert verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=1) == CheckResult(False, "too_many_arguments", "2>1")
