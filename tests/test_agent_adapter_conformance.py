import copy

import pytest

from agentflight.agent_adapter import (
    MAX_CONFORMANCE_CASES,
    RecordedAdapterError,
    normalize_adapter_registry,
    normalize_conformance_suite,
)
from test_agent_adapter import H0, H1, fixture
from test_agent_adapter_registry import registry


def rejected_fixture():
    value = fixture()
    value["steps"][0]["command"] = "must-never-run"
    return value


def suite(*cases):
    registered = registry()
    return registered, {
        "schema_version": 1,
        "suite_id": "synthetic-conformance-v1",
        "registry_evidence_id": normalize_adapter_registry(registered)[
            "registry_evidence_id"
        ],
        "adapter_id": "fixture-adapter",
        "adapter_version": "v1",
        "contract_sha256": H0,
        "cases": list(cases) or [
            {
                "sequence": 0,
                "case_id": "accept-canonical",
                "expectation": "accept",
                "expected_error": None,
                "fixture": fixture(),
            },
            {
                "sequence": 1,
                "case_id": "reject-runtime-field",
                "expectation": "reject",
                "expected_error": "invalid_step_shape",
                "fixture": rejected_fixture(),
            },
        ],
    }


def test_conformance_evidence_is_deterministic_bounded_and_payload_free():
    registered, value = suite()
    first = normalize_conformance_suite(registered, value)
    second = normalize_conformance_suite(copy.deepcopy(registered), copy.deepcopy(value))
    assert first == second
    assert first["authority"] == "conformance_evidence_only_no_execution"
    assert first["coverage"] == {"total": 2, "accepted": 1, "rejected": 1}
    assert len(first["evidence_id"]) == 64
    serialized = str(first)
    assert "must-never-run" not in serialized
    assert "command" not in serialized


def test_conformance_does_not_mutate_inputs():
    registered, value = suite()
    original_registry, original_suite = copy.deepcopy(registered), copy.deepcopy(value)
    normalize_conformance_suite(registered, value)
    assert registered == original_registry
    assert value == original_suite


def test_accepted_fixture_evidence_change_changes_suite_evidence():
    registered, value = suite()
    first = normalize_conformance_suite(registered, value)
    value["cases"][0]["fixture"]["steps"][0]["output_sha256"] = H0
    second = normalize_conformance_suite(registered, value)
    assert first["evidence_id"] != second["evidence_id"]


@pytest.mark.parametrize(
    ("field", "replacement", "error"),
    [
        ("registry_evidence_id", H1, "conformance_registry_mismatch"),
        ("adapter_id", "unknown-adapter", "conformance_adapter_not_authorized"),
        ("adapter_version", "v2", "conformance_adapter_version_mismatch"),
        ("contract_sha256", H1, "conformance_contract_mismatch"),
    ],
)
def test_exact_registry_and_contract_bindings_fail_closed(field, replacement, error):
    registered, value = suite()
    value[field] = replacement
    with pytest.raises(RecordedAdapterError, match=error):
        normalize_conformance_suite(registered, value)


def test_declared_rejection_must_be_observed():
    registered, value = suite()
    value["cases"][1]["fixture"] = fixture()
    with pytest.raises(RecordedAdapterError, match="conformance_rejection_not_observed"):
        normalize_conformance_suite(registered, value)


def test_rejection_code_must_match_exactly():
    registered, value = suite()
    value["cases"][1]["expected_error"] = "invalid_fixture_shape"
    with pytest.raises(RecordedAdapterError, match="conformance_error_mismatch"):
        normalize_conformance_suite(registered, value)


def test_declared_acceptance_must_validate():
    registered, value = suite()
    value["cases"][0]["fixture"] = rejected_fixture()
    with pytest.raises(RecordedAdapterError, match="conformance_acceptance_failed"):
        normalize_conformance_suite(registered, value)


@pytest.mark.parametrize("field", ["module", "entrypoint", "callback", "credentials"])
def test_conformance_suite_rejects_runtime_fields(field):
    registered, value = suite()
    value[field] = "not-allowed"
    with pytest.raises(RecordedAdapterError, match="invalid_conformance_suite_shape"):
        normalize_conformance_suite(registered, value)


def test_rejects_duplicate_or_reordered_cases():
    registered, value = suite()
    value["cases"][1]["case_id"] = value["cases"][0]["case_id"]
    with pytest.raises(RecordedAdapterError, match="duplicate_conformance_case_id"):
        normalize_conformance_suite(registered, value)
    registered, value = suite()
    value["cases"][1]["sequence"] = 2
    with pytest.raises(RecordedAdapterError, match="invalid_conformance_case_sequence"):
        normalize_conformance_suite(registered, value)


def test_rejects_unbounded_case_count():
    case = suite()[1]["cases"][0]
    cases = [dict(case, sequence=index, case_id=f"case-{index}")
             for index in range(MAX_CONFORMANCE_CASES + 1)]
    registered, value = suite(*cases)
    with pytest.raises(RecordedAdapterError, match="invalid_conformance_case_count"):
        normalize_conformance_suite(registered, value)


def test_rejects_mapping_subclasses():
    class Suite(dict):
        pass

    registered, value = suite()
    with pytest.raises(RecordedAdapterError, match="invalid_conformance_suite_shape"):
        normalize_conformance_suite(registered, Suite(value))
