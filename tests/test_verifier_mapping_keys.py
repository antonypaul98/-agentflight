"""Defensive key-iteration regressions for custom Mapping implementations."""
from collections.abc import Mapping
from agentflight.contract import CallContract
from agentflight.verifier import verify_call

class KeysMapping(Mapping):
    def __init__(self, keys):
        self._keys = keys
    def __len__(self):
        return len(self._keys)
    def __iter__(self):
        return iter(self._keys)
    def __getitem__(self, key):
        return "value"

class HostileString(str):
    def __hash__(self):
        raise RuntimeError("hash hook must not run")
    def __eq__(self, other):
        raise RuntimeError("equality hook must not run")
    def __str__(self):
        raise RuntimeError("string hook must not run")

def test_duplicate_mapping_keys_are_rejected():
    contract = CallContract("lookup", required=frozenset({"query"}))
    malformed = KeysMapping(("query", "query"))
    result = verify_call(contract, "lookup", malformed)
    assert (result.passed, result.code, result.detail) == (False, "invalid_arguments", "unreadable_mapping")
    assert verify_call(contract, "other", malformed).code == "name_mismatch"
    assert verify_call(contract, "lookup", malformed, max_arguments=1).code == "too_many_arguments"

def test_string_subclass_keys_are_normalized_without_custom_hooks():
    contract = CallContract("lookup", required=frozenset({"query"}))
    result = verify_call(contract, "lookup", KeysMapping((HostileString("query"),)))
    assert (result.passed, result.code) == (True, "ok")
    missing = verify_call(contract, "lookup", KeysMapping((HostileString("extra"),)))
    assert (missing.passed, missing.code, missing.detail) == (False, "missing_required", "query")
