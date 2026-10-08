"""Bound mismatch evidence from untrusted tool names without changing short names."""

from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import MAX_NAME_MISMATCH_DETAIL, verify_call, verify_name


class HostileSlice(str):
    def __getitem__(self, index):
        raise AssertionError("untrusted slice hook must not run")

    def __str__(self):
        raise AssertionError("untrusted str hook must not run")


def test_short_mismatch_detail_remains_exact():
    assert verify_name(CallContract("lookup"), "wrong") == CheckResult(False, "name_mismatch", "wrong")


def test_exact_detail_boundary_remains_exact():
    name = "x" * MAX_NAME_MISMATCH_DETAIL
    assert verify_name(CallContract("lookup"), name).detail == name


def test_oversized_mismatch_detail_is_bounded_and_marked():
    name = "x" * (MAX_NAME_MISMATCH_DETAIL + 10_000)
    result = verify_name(CallContract("lookup"), name)
    assert result.code == "name_mismatch"
    assert result.detail == "x" * (MAX_NAME_MISMATCH_DETAIL - len("<truncated>")) + "<truncated>"
    assert len(result.detail) == MAX_NAME_MISMATCH_DETAIL


def test_hostile_string_subclass_hooks_are_not_invoked():
    name = HostileSlice("x" * (MAX_NAME_MISMATCH_DETAIL + 1))
    assert verify_name(CallContract("lookup"), name).detail.endswith("<truncated>")


def test_verify_call_name_precedence_and_non_string_behavior():
    contract = CallContract("lookup")
    result = verify_call(contract, "x" * 10_000, [], max_arguments=0)
    assert result.code == "name_mismatch"
    assert len(result.detail) == MAX_NAME_MISMATCH_DETAIL
    assert verify_name(contract, 42) == CheckResult(False, "name_mismatch", "non_string_name")
