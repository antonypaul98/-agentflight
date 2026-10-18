import copy

import pytest

from agentflight.recovery_consistency import (
    AUTHORITY,
    RETRY_BUDGET_AUTHORITY,
    STATE_CHECKPOINT_AUTHORITY,
    RecoveryConsistencyError,
    evaluate_recorded_recovery,
    evaluate_recorded_retry_budget,
    evaluate_recorded_state_checkpoint,
)


H0, H1, H2, H3 = (character * 64 for character in "0123")


def record():
    return {
        "schema_version": 1,
        "recovery_id": "recovery-1",
        "failure_plan_evidence_id": H0,
        "trajectory_evidence_id": H1,
        "operation_evidence_id": H2,
        "idempotency_key_sha256": H3,
        "events": [
            {"sequence": 1, "attempt": 1, "state_before_sha256": H0,
             "state_after_sha256": H0, "outcome_code": "failed_no_commit"},
            {"sequence": 2, "attempt": 2, "state_before_sha256": H0,
             "state_after_sha256": H1, "outcome_code": "committed"},
            {"sequence": 3, "attempt": 3, "state_before_sha256": H1,
             "state_after_sha256": H1, "outcome_code": "duplicate_noop"},
        ],
    }


def test_recorded_recovery_is_deterministic_bound_and_idempotent():
    source = record()
    original = copy.deepcopy(source)
    first = evaluate_recorded_recovery(source)
    assert first == evaluate_recorded_recovery(copy.deepcopy(source))
    assert source == original
    assert first["verdict"] == "recovered"
    assert first["committed_state_sha256"] == H1
    assert first["coverage"] == {
        "recorded_events": 3,
        "commit_count": 1,
        "scope": "bounded_recorded_recovery_and_state_metadata_only",
    }
    assert first["authority"] == AUTHORITY
    assert len(first["evidence_id"]) == 64


def test_failed_only_record_is_explicitly_incomplete():
    source = record()
    source["events"] = source["events"][:1]
    report = evaluate_recorded_recovery(source)
    assert report["verdict"] == "incomplete"
    assert report["committed_state_sha256"] is None


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda value: value.update(command="retry"), "invalid_recovery_record_shape"),
        (lambda value: value["events"][0].update(payload="secret"),
         "invalid_recovery_event_shape"),
        (lambda value: value["events"][1].update(sequence=7),
         "invalid_recovery_sequence"),
        (lambda value: value["events"][1].update(attempt=3),
         "invalid_recovery_attempt"),
        (lambda value: value["events"][1].update(state_before_sha256=H2),
         "state_chain_mismatch"),
        (lambda value: value["events"][0].update(state_after_sha256=H2),
         "no_commit_state_mutation"),
        (lambda value: value["events"][0].update(outcome_code="duplicate_noop"),
         "duplicate_before_commit"),
        (lambda value: value["events"][2].update(outcome_code="committed"),
         "multiple_commits"),
        (lambda value: value["events"][2].update(state_after_sha256=H2),
         "no_commit_state_mutation"),
        (lambda value: value["events"][0].update(outcome_code="retry_now"),
         "invalid_recovery_outcome"),
        (lambda value: value.update(idempotency_key_sha256="secret"),
         "invalid_idempotency_key_hash"),
    ],
)
def test_inconsistent_or_payload_bearing_record_fails_closed(change, code):
    source = record()
    change(source)
    with pytest.raises(RecoveryConsistencyError, match=code):
        evaluate_recorded_recovery(source)


@pytest.mark.parametrize("events", [[], [record()["events"][0]] * 33])
def test_event_count_is_bounded(events):
    source = record()
    source["events"] = events
    with pytest.raises(RecoveryConsistencyError, match="invalid_recovery_event_count"):
        evaluate_recorded_recovery(source)


def test_report_contains_no_external_target_or_payload_fields():
    rendered = repr(evaluate_recorded_recovery(record()))
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered


def budget(report, max_attempts=4):
    return {
        "schema_version": 1,
        "budget_id": "retry-budget-1",
        "recovery_evidence_id": report["evidence_id"],
        "max_attempts": max_attempts,
    }


def test_recorded_retry_budget_is_exactly_bound_and_deterministic():
    recovery = evaluate_recorded_recovery(record())
    source = budget(recovery)
    first = evaluate_recorded_retry_budget(recovery, source)
    assert first == evaluate_recorded_retry_budget(
        copy.deepcopy(recovery), copy.deepcopy(source))
    assert first["used_attempts"] == 3
    assert first["remaining_attempts"] == 1
    assert first["disposition"] == "closed_recovered"
    assert first["retry_permitted"] is False
    assert first["authority"] == RETRY_BUDGET_AUTHORITY
    assert len(first["evidence_id"]) == 64


def test_incomplete_recovery_is_permitted_only_with_budget_remaining():
    source = record()
    source["events"] = source["events"][:1]
    recovery = evaluate_recorded_recovery(source)
    permitted = evaluate_recorded_retry_budget(recovery, budget(recovery, 2))
    assert permitted["disposition"] == "retry_permitted_by_recorded_budget"
    assert permitted["retry_permitted"] is True
    assert permitted["remaining_attempts"] == 1

    exhausted = evaluate_recorded_retry_budget(recovery, budget(recovery, 1))
    assert exhausted["disposition"] == "closed_exhausted"
    assert exhausted["retry_permitted"] is False
    assert exhausted["remaining_attempts"] == 0


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda recovery, source: source.update(command="retry"),
         "invalid_retry_budget_shape"),
        (lambda recovery, source: source.update(max_attempts=9),
         "invalid_max_attempts"),
        (lambda recovery, source: source.update(recovery_evidence_id=H0),
         "retry_budget_evidence_mismatch"),
        (lambda recovery, source: recovery.update(verdict="incomplete"),
         "recovery_evidence_mismatch"),
        (lambda recovery, source: recovery.update(authority="execute_retry"),
         "recovery_evidence_mismatch"),
    ],
)
def test_forged_or_payload_bearing_retry_budget_fails_closed(change, code):
    recovery = evaluate_recorded_recovery(record())
    source = budget(recovery)
    change(recovery, source)
    with pytest.raises(RecoveryConsistencyError, match=code):
        evaluate_recorded_retry_budget(recovery, source)


def test_retry_budget_rejects_attempts_beyond_bound_and_leaks_no_payload():
    recovery = evaluate_recorded_recovery(record())
    with pytest.raises(RecoveryConsistencyError, match="retry_budget_exceeded"):
        evaluate_recorded_retry_budget(recovery, budget(recovery, 2))
    rendered = repr(evaluate_recorded_retry_budget(recovery, budget(recovery, 3)))
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered


def checkpoint(report, generation=7):
    return {
        "schema_version": 1,
        "checkpoint_id": "state-checkpoint-1",
        "recovery_evidence_id": report["evidence_id"],
        "generation": generation,
        "initial_state_sha256": report["events"][0]["state_before_sha256"],
        "checkpoint_state_sha256": report["events"][-1]["state_after_sha256"],
    }


def test_recorded_state_checkpoint_is_exactly_bound_and_deterministic():
    recovery = evaluate_recorded_recovery(record())
    source = checkpoint(recovery)
    first = evaluate_recorded_state_checkpoint(recovery, source)
    assert first == evaluate_recorded_state_checkpoint(
        copy.deepcopy(recovery), copy.deepcopy(source))
    assert first["generation"] == 7
    assert first["checkpoint_state_sha256"] == H1
    assert first["recovery_verdict"] == "recovered"
    assert first["state_consistent"] is True
    assert first["authority"] == STATE_CHECKPOINT_AUTHORITY
    assert len(first["evidence_id"]) == 64


def test_incomplete_recovery_checkpoint_remains_at_initial_state():
    source = record()
    source["events"] = source["events"][:1]
    recovery = evaluate_recorded_recovery(source)
    result = evaluate_recorded_state_checkpoint(recovery, checkpoint(recovery, 1))
    assert result["recovery_verdict"] == "incomplete"
    assert result["initial_state_sha256"] == H0
    assert result["checkpoint_state_sha256"] == H0


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda recovery, source: source.update(path="/state"),
         "invalid_state_checkpoint_shape"),
        (lambda recovery, source: source.update(generation=0),
         "invalid_checkpoint_generation"),
        (lambda recovery, source: source.update(generation=True),
         "invalid_checkpoint_generation"),
        (lambda recovery, source: source.update(recovery_evidence_id=H0),
         "state_checkpoint_evidence_mismatch"),
        (lambda recovery, source: source.update(initial_state_sha256=H2),
         "checkpoint_initial_state_mismatch"),
        (lambda recovery, source: source.update(checkpoint_state_sha256=H2),
         "checkpoint_state_mismatch"),
        (lambda recovery, source: recovery.update(verdict="incomplete"),
         "recovery_evidence_mismatch"),
    ],
)
def test_forged_or_payload_bearing_state_checkpoint_fails_closed(change, code):
    recovery = evaluate_recorded_recovery(record())
    source = checkpoint(recovery)
    change(recovery, source)
    with pytest.raises(RecoveryConsistencyError, match=code):
        evaluate_recorded_state_checkpoint(recovery, source)


def test_state_checkpoint_contains_no_external_target_or_payload_fields():
    recovery = evaluate_recorded_recovery(record())
    rendered = repr(evaluate_recorded_state_checkpoint(recovery, checkpoint(recovery)))
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered
