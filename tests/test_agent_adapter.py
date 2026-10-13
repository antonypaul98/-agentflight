import copy

import pytest

from agentflight.agent_adapter import MAX_STEPS, RecordedAdapterError, normalize_recorded_run


H0 = "0" * 64
H1 = "1" * 64


def fixture(framework="recorded-mock"):
    return {
        "schema_version": 1,
        "adapter": {"adapter_id": "fixture-adapter", "framework": framework},
        "run_id": "run-001",
        "steps": [
            {
                "sequence": 0,
                "step_id": "plan",
                "kind": "model",
                "input_sha256": H0,
                "output_sha256": H1,
                "status": "passed",
            }
        ],
    }


def test_normalizes_recorded_metadata_deterministically():
    first = normalize_recorded_run(fixture())
    second = normalize_recorded_run(fixture())
    assert first == second
    assert first["authority"] == "recorded_fixture_only"
    assert len(first["evidence_id"]) == 64


def test_contract_is_framework_neutral():
    assert normalize_recorded_run(fixture("langgraph"))["framework"] == "langgraph"
    assert normalize_recorded_run(fixture("custom-sdk"))["framework"] == "custom-sdk"


def test_does_not_mutate_the_fixture():
    source = fixture()
    original = copy.deepcopy(source)
    normalize_recorded_run(source)
    assert source == original


@pytest.mark.parametrize("field", ["prompt", "arguments", "result", "command", "path", "env"])
def test_rejects_payload_or_execution_fields(field):
    source = fixture()
    source["steps"][0][field] = "private-or-executable-value"
    with pytest.raises(RecordedAdapterError, match="invalid_step_shape"):
        normalize_recorded_run(source)


def test_rejects_unsupported_version_before_normalization():
    source = fixture()
    source["schema_version"] = 2
    with pytest.raises(RecordedAdapterError, match="unsupported_schema_version"):
        normalize_recorded_run(source)


@pytest.mark.parametrize("field", ["input_sha256", "output_sha256"])
def test_rejects_noncanonical_hashes(field):
    source = fixture()
    source["steps"][0][field] = "A" * 64
    with pytest.raises(RecordedAdapterError, match="invalid_.*_hash"):
        normalize_recorded_run(source)


def test_rejects_ambiguous_or_duplicate_ordering():
    source = fixture()
    duplicate = dict(source["steps"][0], sequence=1)
    source["steps"].append(duplicate)
    with pytest.raises(RecordedAdapterError, match="duplicate_step_id"):
        normalize_recorded_run(source)


def test_rejects_sequence_gaps():
    source = fixture()
    source["steps"][0]["sequence"] = 1
    with pytest.raises(RecordedAdapterError, match="invalid_step_sequence"):
        normalize_recorded_run(source)


def test_rejects_unbounded_step_count():
    source = fixture()
    source["steps"] = [dict(source["steps"][0], sequence=i, step_id=f"s-{i}") for i in range(MAX_STEPS + 1)]
    with pytest.raises(RecordedAdapterError, match="invalid_step_count"):
        normalize_recorded_run(source)


def test_rejects_mapping_subclasses():
    class Fixture(dict):
        pass

    with pytest.raises(RecordedAdapterError, match="invalid_fixture_shape"):
        normalize_recorded_run(Fixture(fixture()))
