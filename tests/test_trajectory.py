import copy

import pytest

from agentflight.agent_adapter import RecordedAdapterError
from agentflight.trajectory import TrajectoryVerificationError, verify_recorded_trajectory
from test_agent_adapter import H0, H1, fixture
from test_agent_adapter_registry import registry


H2 = "2" * 64
H3 = "3" * 64


def trajectory(status="passed"):
    value = fixture()
    value["steps"] = [
        dict(value["steps"][0], step_id="plan", input_sha256=H0, output_sha256=H1),
        dict(
            value["steps"][0],
            sequence=1,
            step_id="act",
            kind="tool",
            input_sha256=H1,
            output_sha256=H2,
        ),
        dict(
            value["steps"][0],
            sequence=2,
            step_id="review",
            kind="decision",
            input_sha256=H2,
            output_sha256=H3,
            status=status,
        ),
    ]
    return value


def test_verifies_ordered_hash_linked_trajectory_deterministically():
    first = verify_recorded_trajectory(registry(), trajectory())
    second = verify_recorded_trajectory(registry(), copy.deepcopy(trajectory()))
    assert first == second
    assert first["verdict"] == "complete"
    assert first["coverage"] == {
        "observed_steps": 3,
        "verified_transitions": 2,
        "scope": "recorded_hash_linkage_only",
    }
    assert [item["state_sha256"] for item in first["transitions"]] == [H1, H2]
    assert first["initial_state_sha256"] == H0
    assert first["terminal_state_sha256"] == H3
    assert first["authority"] == "recorded_trajectory_verification_only_no_execution"
    assert len(first["evidence_id"]) == 64


@pytest.mark.parametrize("status", ["failed", "rejected"])
def test_terminal_failure_is_explicit_partial_failure_evidence(status):
    report = verify_recorded_trajectory(registry(), trajectory(status))
    assert report["verdict"] == "partial_failure"
    assert report["terminal"] == {
        "sequence": 2,
        "step_id": "review",
        "step_status": status,
    }


def test_rejects_state_transition_discontinuity():
    value = trajectory()
    value["steps"][1]["input_sha256"] = H3
    with pytest.raises(TrajectoryVerificationError, match="state_transition_mismatch"):
        verify_recorded_trajectory(registry(), value)


def test_rejects_steps_after_terminal_failure():
    value = trajectory()
    value["steps"][1]["status"] = "failed"
    with pytest.raises(TrajectoryVerificationError, match="steps_after_terminal_failure"):
        verify_recorded_trajectory(registry(), value)


def test_rejects_single_step_run_as_not_multi_step():
    with pytest.raises(TrajectoryVerificationError, match="invalid_trajectory_step_count"):
        verify_recorded_trajectory(registry(), fixture())


def test_binds_exact_registry_and_recorded_run_evidence():
    first = verify_recorded_trajectory(registry(), trajectory())
    changed_registry = registry()
    changed_registry["adapters"][0]["contract_sha256"] = H1
    second = verify_recorded_trajectory(changed_registry, trajectory())
    assert first["registry_evidence_id"] != second["registry_evidence_id"]
    assert first["recorded_run_evidence_id"] != second["recorded_run_evidence_id"]
    assert first["evidence_id"] != second["evidence_id"]


def test_upstream_authorization_still_fails_closed():
    value = trajectory()
    value["adapter"]["adapter_id"] = "unregistered-adapter"
    with pytest.raises(RecordedAdapterError, match="adapter_not_authorized"):
        verify_recorded_trajectory(registry(), value)


def test_does_not_mutate_inputs_or_retain_payload_fields():
    registered, value = registry(), trajectory()
    original_registry, original_value = copy.deepcopy(registered), copy.deepcopy(value)
    report = verify_recorded_trajectory(registered, value)
    assert registered == original_registry
    assert value == original_value
    serialized = str(report)
    for forbidden in ("prompt", "arguments", "result", "command", "credentials"):
        assert forbidden not in serialized
