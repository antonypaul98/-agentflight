from agentflight.contract import CallContract
from agentflight.verifier import verify_call, verify_name


def test_verify_name_accepts_expected_name() -> None:
    result = verify_name(CallContract(name="lookup"), "lookup")
    assert result.passed is True
    assert result.code == "ok"


def test_verify_name_rejects_mismatch() -> None:
    result = verify_name(CallContract(name="lookup"), "other")
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"


def test_verify_call_accepts_required_and_optional_arguments() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query"}),
        optional=frozenset({"limit"}),
    )
    result = verify_call(contract, "lookup", {"query": "agentflight", "limit": 3})
    assert result.passed is True
    assert result.code == "ok"


def test_verify_call_rejects_missing_required_arguments_deterministically() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query", "tenant_id"}),
    )
    result = verify_call(contract, "lookup", {})
    assert result.passed is False
    assert result.code == "missing_required"
    assert result.detail == "query,tenant_id"


def test_verify_call_rejects_unexpected_arguments_deterministically() -> None:
    contract = CallContract(
        name="lookup",
        required=frozenset({"query"}),
        optional=frozenset({"limit"}),
    )
    result = verify_call(
        contract,
        "lookup",
        {"query": "agentflight", "z_extra": True, "a_extra": False},
    )
    assert result.passed is False
    assert result.code == "unexpected_argument"
    assert result.detail == "a_extra,z_extra"


def test_verify_call_propagates_name_mismatch() -> None:
    contract = CallContract(name="lookup", required=frozenset({"query"}))
    result = verify_call(contract, "other", {"query": "agentflight"})
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"


def test_verify_call_accepts_exact_argument_limit() -> None:
    contract = CallContract(name="lookup", optional=frozenset({"a", "b"}))
    result = verify_call(contract, "lookup", {"a": 1, "b": 2}, max_arguments=2)
    assert result.passed is True
    assert result.code == "ok"


def test_verify_call_rejects_over_limit_deterministically() -> None:
    contract = CallContract(name="lookup", optional=frozenset({"a", "b", "c"}))
    first = verify_call(contract, "lookup", {"a": 1, "b": 2, "c": 3}, max_arguments=2)
    second = verify_call(contract, "lookup", {"c": 3, "a": 1, "b": 2}, max_arguments=2)
    assert first == second
    assert first.passed is False
    assert first.code == "too_many_arguments"
    assert first.detail == "3>2"


def test_verify_call_rejects_boolean_argument_bound() -> None:
    import pytest

    with pytest.raises(TypeError, match="max_arguments must be an integer"):
        verify_call(CallContract(name="lookup"), "lookup", {}, max_arguments=True)


def test_verify_call_rejects_non_integer_argument_bound() -> None:
    import pytest

    with pytest.raises(TypeError, match="max_arguments must be an integer"):
        verify_call(CallContract(name="lookup"), "lookup", {}, max_arguments=1.5)


def test_verify_call_rejects_negative_argument_bound() -> None:
    import pytest

    with pytest.raises(ValueError, match="max_arguments must be non-negative"):
        verify_call(CallContract(name="lookup"), "lookup", {}, max_arguments=-1)

def test_verify_call_rejects_non_mapping_arguments_deterministically() -> None:
    import pytest

    contract = CallContract(name="lookup", required=frozenset({"query"}))
    for malformed in ([], ["query"], (), ("query",), None, "query", 7):
        result = verify_call(contract, "lookup", malformed)
        assert result.passed is False
        assert result.code == "invalid_arguments"
        assert result.detail == "expected_mapping"


def test_verify_call_preserves_name_mismatch_precedence_for_malformed_arguments() -> None:
    result = verify_call(CallContract(name="lookup"), "other", ["not", "a", "mapping"])
    assert result.passed is False
    assert result.code == "name_mismatch"
    assert result.detail == "other"


def test_verify_call_preserves_bound_validation_precedence_for_malformed_arguments() -> None:
    import pytest

    with pytest.raises(TypeError, match="max_arguments must be an integer"):
        verify_call(CallContract(name="lookup"), "lookup", [], max_arguments=True)


def test_verify_call_rejects_non_string_mapping_keys_deterministically() -> None:
    import pytest

    contract = CallContract(name="lookup", required=frozenset({"query"}))
    for malformed in ({"query": "ok", 1: True}, {"query": "ok", None: True}, {(1, 2): "ok"}):
        result = verify_call(contract, "lookup", malformed)
        assert result.passed is False
        assert result.code == "invalid_arguments"
        assert result.detail == "non_string_key"


def test_verify_call_preserves_name_and_size_precedence_for_non_string_keys() -> None:
    contract = CallContract(name="lookup")
    assert verify_call(contract, "other", {1: "x"}).code == "name_mismatch"
    over_limit = verify_call(contract, "lookup", {1: "x", 2: "y"}, max_arguments=1)
    assert over_limit.code == "too_many_arguments"
    assert over_limit.detail == "2>1"


def test_verify_call_rejects_mapping_that_raises_on_length_or_iteration() -> None:
    from collections.abc import Mapping
    from unittest.mock import MagicMock

    contract = CallContract(name="lookup")
    for method, error in (("__len__", RuntimeError), ("__iter__", ValueError)):
        malformed = MagicMock(spec=Mapping)
        malformed.__len__.return_value = 1
        getattr(malformed, method).side_effect = error("bad mapping")
        result = verify_call(contract, "lookup", malformed)
        assert (result.passed, result.code, result.detail) == (
            False, "invalid_arguments", "unreadable_mapping"
        )
        assert verify_call(contract, "other", malformed).code == "name_mismatch"
