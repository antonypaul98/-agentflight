"""Dict subclasses cannot spoof argument cardinality or names."""
from agentflight.contract import CallContract
from agentflight.result import CheckResult
from agentflight.verifier import verify_call

class LyingDict(dict):
    def __len__(self):
        return 0
    def __iter__(self):
        return iter(("query",))

class ExplodingDict(dict):
    def __len__(self):
        raise AssertionError("custom len must not run")
    def __iter__(self):
        raise AssertionError("custom iter must not run")

def test_dict_subclass_cannot_fabricate_required_key():
    contract = CallContract("lookup", required=frozenset({"query"}))
    assert verify_call(contract, "lookup", LyingDict({"secret": 1})) == CheckResult(False, "missing_required", "query")

def test_dict_subclass_cannot_hide_over_limit_keys():
    contract = CallContract("lookup")
    assert verify_call(contract, "lookup", LyingDict({"a": 1, "b": 2}), max_arguments=1) == CheckResult(False, "too_many_arguments", "2>1")

def test_dict_subclass_hooks_not_invoked_for_valid_input():
    contract = CallContract("lookup", required=frozenset({"query"}))
    assert verify_call(contract, "lookup", ExplodingDict({"query": 1})) == CheckResult(True, "ok")

def test_dict_subclass_preserves_validation_precedence():
    contract = CallContract("lookup", required=frozenset({"query"}))
    malformed = LyingDict({"secret": 1, "extra": 2})
    assert verify_call(contract, "other", malformed).code == "name_mismatch"
    assert verify_call(contract, "lookup", malformed, max_arguments=1).code == "too_many_arguments"
