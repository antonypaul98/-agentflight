import copy

import pytest

from agentflight.recovery_consistency import (
    AUTHORITY,
    RecoveryConsistencyError,
    evaluate_recorded_recovery,
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
