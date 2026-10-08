"""Regressions for unexpected exceptions from adversarial Mapping hooks."""

from collections.abc import Mapping

from agentflight.contract import CallContract
from agentflight.verifier import verify_call


class ExplodingMapping(Mapping):
    def __init__(self, failure_at, error):
        self.failure_at = failure_at
        self.error = error

    def __len__(self):
        if self.failure_at == "length":
            raise self.error("untrusted length")
        return 2

    def __iter__(self):
        if self.failure_at == "iteration":
            raise self.error("untrusted iterator")
        yield "query"
        if self.failure_at == "mid_iteration":
            raise self.error("untrusted iterator after one key")
        yield "extra"

    def __getitem__(self, key):
        return "value"


def test_mapping_hook_errors_become_deterministic_failure_evidence():
    contract = CallContract("lookup", required=frozenset({"query"}), optional=frozenset({"extra"}))
    for failure_at in ("length", "iteration", "mid_iteration"):
        for error in (KeyError, OSError, OverflowError):
            result = verify_call(contract, "lookup", ExplodingMapping(failure_at, error))
            assert (result.passed, result.code, result.detail) == (
                False, "invalid_arguments", "unreadable_mapping"
            )


def test_mapping_hook_errors_preserve_name_mismatch_precedence():
    contract = CallContract("lookup")
    malformed = ExplodingMapping("length", KeyError)
    assert verify_call(contract, "other", malformed).code == "name_mismatch"


def test_mapping_hook_errors_preserve_argument_limit_precedence():
    contract = CallContract("lookup")
    malformed = ExplodingMapping("iteration", OSError)
    result = verify_call(contract, "lookup", malformed, max_arguments=1)
    assert (result.code, result.detail) == ("too_many_arguments", "2>1")


def test_valid_mapping_is_unaffected():
    contract = CallContract("lookup", required=frozenset({"query"}))
    result = verify_call(contract, "lookup", {"query": "value"}, max_arguments=1)
    assert (result.passed, result.code) == (True, "ok")
