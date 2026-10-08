"""Contract-field validation regressions for adversarial argument schemas."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import verify_call


class HostileName(str):
    def __hash__(self):
        raise AssertionError("custom hash must not execute")

    def __eq__(self, other):
        raise AssertionError("custom equality must not execute")

    def __str__(self):
        raise AssertionError("custom str must not execute")


def test_non_string_required_and_optional_names_fail_deterministically():
    for contract in (
        CallContract("lookup", required=frozenset({"query", 3})),
        CallContract("lookup", optional=frozenset({None})),
    ):
        assert verify_call(contract, "lookup", {"query": 1}) == CheckResult(
            False, "invalid_contract", "non_string_argument_name"
        )


def test_non_set_argument_schemas_fail_without_throwing():
    for contract in (
        CallContract("lookup", required=["query"]),
        CallContract("lookup", optional=None),
    ):
        assert verify_call(contract, "lookup", {}) == CheckResult(
            False, "invalid_contract", "expected_argument_sets"
        )


def test_hostile_string_subclass_contract_names_are_normalized():
    # Build a frozenset while hashing is still safe; only later swap in the hostile hooks.
    class MutableHostileName(str):
        pass

    required_name = MutableHostileName("query")
    optional_name = MutableHostileName("limit")
    required = frozenset({required_name})
    optional = frozenset({optional_name})
    MutableHostileName.__hash__ = HostileName.__hash__
    MutableHostileName.__eq__ = HostileName.__eq__
    MutableHostileName.__str__ = HostileName.__str__

    contract = CallContract("lookup", required=required, optional=optional)
    assert verify_call(contract, "lookup", {"query": 1, "limit": 2}) == CheckResult(True, "ok")
    assert verify_call(contract, "lookup", {}) == CheckResult(False, "missing_required", "query")


def test_contract_validation_preserves_earlier_failure_precedence():
    malformed = CallContract("lookup", required=["query"])
    assert verify_call(malformed, "wrong", {}).code == "name_mismatch"
    assert verify_call(malformed, "lookup", []).detail == "expected_mapping"
    assert verify_call(malformed, "lookup", {"a": 1, "b": 2}, max_arguments=1).code == "too_many_arguments"
    assert verify_call(malformed, "lookup", {1: 1}).detail == "non_string_key"


def test_valid_mutable_sets_still_work():
    contract = CallContract("lookup", required={"query"}, optional={"limit"})
    assert verify_call(contract, "lookup", {"query": "ok"}) == CheckResult(True, "ok")


def test_set_subclass_iteration_hooks_are_not_invoked():
    class HostileSet(set):
        def __iter__(self):
            raise AssertionError("custom set iteration must not execute")

    contract = CallContract("lookup", required=HostileSet({"query"}))
    assert verify_call(contract, "lookup", {"query": 1}) == CheckResult(True, "ok")


def test_valid_contract_preserves_missing_unexpected_and_bound_evidence():
    contract = CallContract("lookup", required=frozenset({"query"}), optional=frozenset({"limit"}))
    assert verify_call(contract, "lookup", {}) == CheckResult(False, "missing_required", "query")
    assert verify_call(contract, "lookup", {"query": 1, "extra": 2}) == CheckResult(False, "unexpected_argument", "extra")
    assert verify_call(contract, "lookup", {"query": 1, "extra": 2}, max_arguments=1) == CheckResult(False, "too_many_arguments", "2>1")
