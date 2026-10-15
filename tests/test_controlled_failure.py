import copy

import pytest

from agentflight.controlled_failure import (
    AUTHORITY,
    ControlledFailureError,
    evaluate_recorded_call,
    evaluate_recorded_sequence,
    normalize_failure_plan,
)


H0, H1 = (character * 64 for character in "01")


def plan():
    return {
        "schema_version": 1,
        "plan_id": "offline-api-faults",
        "environment_evidence_id": H0,
        "scenarios": [
            {"sequence": 1, "fault_id": "network-0", "call_index": 0,
             "kind": "network_error", "outcome_code": "connection_reset", "delay_ms": 0},
            {"sequence": 2, "fault_id": "timeout-2", "call_index": 2,
             "kind": "timeout", "outcome_code": "deadline_exceeded", "delay_ms": 1500},
            {"sequence": 3, "fault_id": "rate-limit-4", "call_index": 4,
             "kind": "rate_limit", "outcome_code": "http_429", "delay_ms": 2000},
            {"sequence": 4, "fault_id": "api-6", "call_index": 6,
             "kind": "api_error", "outcome_code": "http_503", "delay_ms": 0},
        ],
    }


def test_plan_is_deterministic_and_does_not_mutate_input():
    source = plan()
    original = copy.deepcopy(source)
    first = normalize_failure_plan(source)
    assert first == normalize_failure_plan(copy.deepcopy(source))
    assert source == original
    assert first["authority"] == AUTHORITY
    assert first["coverage"] == {
        "scenario_count": 4,
        "kinds": ["api_error", "network_error", "rate_limit", "timeout"],
        "scope": "caller_supplied_recorded_metadata_only",
    }
    assert len(first["evidence_id"]) == 64


@pytest.mark.parametrize("call_index,kind", [(0, "network_error"), (2, "timeout"),
                                               (4, "rate_limit"), (6, "api_error")])
def test_injects_each_supported_offline_failure(call_index, kind):
    result = evaluate_recorded_call(plan(), call_index, H1)
    assert result["verdict"] == "injected"
    assert result["scenario"]["kind"] == kind
    assert result["observed_sha256"] == H1
    assert result["authority"] == AUTHORITY


def test_unplanned_call_is_explicitly_not_injected():
    result = evaluate_recorded_call(plan(), 1, H1)
    assert result["verdict"] == "not_injected"
    assert result["scenario"] is None


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda value: value.update(url="https://example.invalid"), "invalid_failure_plan_shape"),
        (lambda value: value["scenarios"][0].update(payload="secret"),
         "invalid_failure_scenario_shape"),
        (lambda value: value["scenarios"][1].update(sequence=9), "invalid_failure_sequence"),
        (lambda value: value["scenarios"][1].update(call_index=0),
         "duplicate_failure_call_index"),
        (lambda value: value["scenarios"][0].update(kind="shell"),
         "unsupported_failure_kind"),
        (lambda value: value["scenarios"][0].update(outcome_code="http_503"),
         "invalid_failure_outcome"),
        (lambda value: value["scenarios"][0].update(delay_ms=1),
         "failure_delay_semantics_mismatch"),
        (lambda value: value["scenarios"][1].update(delay_ms=0),
         "failure_delay_semantics_mismatch"),
        (lambda value: value.update(environment_evidence_id="A" * 64),
         "invalid_environment_evidence_id"),
    ],
)
def test_invalid_or_payload_bearing_plan_fails_closed(change, code):
    source = plan()
    change(source)
    with pytest.raises(ControlledFailureError, match=code):
        normalize_failure_plan(source)


@pytest.mark.parametrize("call_index", [-1, True, 64])
def test_invalid_recorded_call_index_fails_closed(call_index):
    with pytest.raises(ControlledFailureError, match="invalid_recorded_call_index"):
        evaluate_recorded_call(plan(), call_index, H1)


def test_invalid_observed_hash_fails_closed():
    with pytest.raises(ControlledFailureError, match="invalid_observed_call_hash"):
        evaluate_recorded_call(plan(), 0, "not-a-hash")


def test_result_contains_no_external_target_or_payload_fields():
    result = evaluate_recorded_call(plan(), 0, H1)
    rendered = repr(result)
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered


def attempts():
    return [
        {"sequence": 1, "call_index": 0, "attempt": 1,
         "observed_sha256": H1, "outcome_code": "connection_reset",
         "trajectory_evidence_id": H0},
        {"sequence": 2, "call_index": 0, "attempt": 2,
         "observed_sha256": H1, "outcome_code": "ok",
         "trajectory_evidence_id": H0},
        {"sequence": 3, "call_index": 2, "attempt": 1,
         "observed_sha256": H1, "outcome_code": "deadline_exceeded",
         "trajectory_evidence_id": H0},
    ]


def test_recorded_retry_and_outage_sequence_is_deterministic_and_bound():
    source = attempts()
    first = evaluate_recorded_sequence(plan(), source)
    assert first == evaluate_recorded_sequence(copy.deepcopy(plan()), copy.deepcopy(source))
    assert first["calls"] == [
        {"call_index": 0, "attempts": 2, "verdict": "recovered"},
        {"call_index": 2, "attempts": 1, "verdict": "incomplete"},
    ]
    assert first["attempts"][0]["decision"] == "retry_permitted"
    assert first["attempts"][1]["decision"] == "stop_retrying"
    assert first["trajectory_evidence_id"] == H0
    assert first["coverage"]["scope"] == "bounded_recorded_retry_and_outage_metadata_only"
    assert first["authority"] == AUTHORITY


def test_four_failed_attempts_exhaust_the_fixed_budget():
    rows = [
        {"sequence": index, "call_index": 0, "attempt": index,
         "observed_sha256": H1, "outcome_code": "connection_reset",
         "trajectory_evidence_id": H0}
        for index in range(1, 5)
    ]
    report = evaluate_recorded_sequence(plan(), rows)
    assert report["calls"] == [{"call_index": 0, "attempts": 4, "verdict": "exhausted"}]
    assert report["attempts"][-1]["decision"] == "retry_budget_exhausted"


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda rows: rows[0].update(payload="secret"), "invalid_recorded_attempt_shape"),
        (lambda rows: rows[1].update(sequence=7), "invalid_recorded_attempt_sequence"),
        (lambda rows: rows[0].update(call_index=1), "attempt_not_bound_to_planned_fault"),
        (lambda rows: rows[1].update(attempt=3), "invalid_retry_attempt"),
        (lambda rows: rows[1].update(outcome_code="http_503"),
         "invalid_recorded_retry_outcome"),
        (lambda rows: rows[0].update(outcome_code="ok"), "initial_outcome_plan_mismatch"),
        (lambda rows: rows[1].update(trajectory_evidence_id=H1),
         "trajectory_binding_mismatch"),
        (lambda rows: rows.reverse(), "invalid_recorded_attempt_sequence"),
    ],
)
def test_invalid_retry_or_outage_metadata_fails_closed(change, code):
    rows = attempts()
    change(rows)
    with pytest.raises(ControlledFailureError, match=code):
        evaluate_recorded_sequence(plan(), rows)


def test_recorded_sequence_retains_no_payload_or_external_target():
    rendered = repr(evaluate_recorded_sequence(plan(), attempts()))
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered
