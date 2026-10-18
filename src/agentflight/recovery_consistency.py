"""Deterministic validation of recorded recovery and state-consistency evidence.

The validator accepts only caller-supplied hashes and enumerated outcomes.  It
does not retry, recover, execute, inspect a project, or read durable state.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
MAX_EVENTS = 32
MAX_RETRY_ATTEMPTS = 8
MAX_CHECKPOINT_GENERATION = 1_000_000
MAX_REPORT_BYTES = 32_768
AUTHORITY = "recorded_recovery_consistency_only_no_execution"
RETRY_BUDGET_AUTHORITY = "recorded_retry_budget_only_no_retry_or_execution"
STATE_CHECKPOINT_AUTHORITY = (
    "recorded_state_checkpoint_only_no_storage_access_or_execution"
)

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OUTCOMES = frozenset({"failed_no_commit", "committed", "duplicate_noop"})


class RecoveryConsistencyError(ValueError):
    """The supplied recovery record is outside the offline contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _exact_dict(value: object, keys: frozenset[str], code: str) -> dict:
    if type(value) is not dict or frozenset(value) != keys:
        raise RecoveryConsistencyError(code)
    return value


def _text(value: object, pattern: re.Pattern[str], code: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise RecoveryConsistencyError(code)
    return value


def evaluate_recorded_recovery(record: Mapping[str, object]) -> dict:
    """Verify one bounded recorded recovery sequence without performing it."""

    root = _exact_dict(
        record,
        frozenset({
            "schema_version", "recovery_id", "failure_plan_evidence_id",
            "trajectory_evidence_id", "operation_evidence_id",
            "idempotency_key_sha256", "events",
        }),
        "invalid_recovery_record_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecoveryConsistencyError("unsupported_recovery_schema_version")
    events = root["events"]
    if type(events) is not list or not 1 <= len(events) <= MAX_EVENTS:
        raise RecoveryConsistencyError("invalid_recovery_event_count")

    recovery_id = _text(root["recovery_id"], _IDENTIFIER, "invalid_recovery_id")
    failure_plan_id = _text(
        root["failure_plan_evidence_id"], _SHA256, "invalid_failure_plan_evidence_id")
    trajectory_id = _text(
        root["trajectory_evidence_id"], _SHA256, "invalid_trajectory_evidence_id")
    operation_id = _text(
        root["operation_evidence_id"], _SHA256, "invalid_operation_evidence_id")
    idempotency_hash = _text(
        root["idempotency_key_sha256"], _SHA256, "invalid_idempotency_key_hash")

    expected_keys = frozenset({
        "sequence", "attempt", "state_before_sha256", "state_after_sha256", "outcome_code"
    })
    normalized = []
    prior_after = None
    committed_state = None
    commit_count = 0
    for expected, value in enumerate(events, start=1):
        event = _exact_dict(value, expected_keys, "invalid_recovery_event_shape")
        if type(event["sequence"]) is not int or event["sequence"] != expected:
            raise RecoveryConsistencyError("invalid_recovery_sequence")
        if type(event["attempt"]) is not int or event["attempt"] != expected:
            raise RecoveryConsistencyError("invalid_recovery_attempt")
        before = _text(event["state_before_sha256"], _SHA256, "invalid_state_before_hash")
        after = _text(event["state_after_sha256"], _SHA256, "invalid_state_after_hash")
        if prior_after is not None and before != prior_after:
            raise RecoveryConsistencyError("state_chain_mismatch")
        outcome = event["outcome_code"]
        if type(outcome) is not str or outcome not in _OUTCOMES:
            raise RecoveryConsistencyError("invalid_recovery_outcome")
        if outcome in {"failed_no_commit", "duplicate_noop"} and before != after:
            raise RecoveryConsistencyError("no_commit_state_mutation")
        if outcome == "duplicate_noop" and committed_state is None:
            raise RecoveryConsistencyError("duplicate_before_commit")
        if outcome == "committed":
            commit_count += 1
            if commit_count > 1:
                raise RecoveryConsistencyError("multiple_commits")
            committed_state = after
        elif committed_state is not None and after != committed_state:
            raise RecoveryConsistencyError("post_commit_state_mismatch")
        normalized.append({
            "sequence": expected,
            "attempt": expected,
            "state_before_sha256": before,
            "state_after_sha256": after,
            "outcome_code": outcome,
        })
        prior_after = after

    verdict = "recovered" if committed_state is not None else "incomplete"
    report = {
        "recovery_schema_version": SCHEMA_VERSION,
        "recovery_id": recovery_id,
        "failure_plan_evidence_id": failure_plan_id,
        "trajectory_evidence_id": trajectory_id,
        "operation_evidence_id": operation_id,
        "idempotency_key_sha256": idempotency_hash,
        "events": normalized,
        "verdict": verdict,
        "committed_state_sha256": committed_state,
        "coverage": {
            "recorded_events": len(normalized),
            "commit_count": commit_count,
            "scope": "bounded_recorded_recovery_and_state_metadata_only",
        },
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("recovery_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def _verified_recovery_report(recovery_report: Mapping[str, object]) -> dict:
    report = _exact_dict(
        recovery_report,
        frozenset({
            "recovery_schema_version", "recovery_id", "failure_plan_evidence_id",
            "trajectory_evidence_id", "operation_evidence_id",
            "idempotency_key_sha256", "events", "verdict",
            "committed_state_sha256", "coverage", "authority", "evidence_id",
        }),
        "invalid_recovery_report_shape",
    )
    supplied_evidence_id = _text(
        report["evidence_id"], _SHA256, "invalid_recovery_evidence_id")
    unsigned = {key: value for key, value in report.items() if key != "evidence_id"}
    expected_evidence_id = hashlib.sha256(
        _canonical(unsigned).encode("utf-8")
    ).hexdigest()
    if supplied_evidence_id != expected_evidence_id:
        raise RecoveryConsistencyError("recovery_evidence_mismatch")
    source_record = {
        "schema_version": report["recovery_schema_version"],
        "recovery_id": report["recovery_id"],
        "failure_plan_evidence_id": report["failure_plan_evidence_id"],
        "trajectory_evidence_id": report["trajectory_evidence_id"],
        "operation_evidence_id": report["operation_evidence_id"],
        "idempotency_key_sha256": report["idempotency_key_sha256"],
        "events": report["events"],
    }
    try:
        recomputed = evaluate_recorded_recovery(source_record)
    except RecoveryConsistencyError:
        raise RecoveryConsistencyError("invalid_recovery_report") from None
    if recomputed != report:
        raise RecoveryConsistencyError("invalid_recovery_report")
    return report


def evaluate_recorded_retry_budget(
    recovery_report: Mapping[str, object], budget: Mapping[str, object]
) -> dict:
    """Bind one fixed retry budget to an exact recorded recovery report."""

    report = _verified_recovery_report(recovery_report)
    supplied_evidence_id = report["evidence_id"]
    events = report["events"]

    root = _exact_dict(
        budget,
        frozenset({
            "schema_version", "budget_id", "recovery_evidence_id", "max_attempts"
        }),
        "invalid_retry_budget_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecoveryConsistencyError("unsupported_retry_budget_schema_version")
    budget_id = _text(root["budget_id"], _IDENTIFIER, "invalid_retry_budget_id")
    bound_evidence_id = _text(
        root["recovery_evidence_id"], _SHA256, "invalid_recovery_evidence_id")
    if bound_evidence_id != supplied_evidence_id:
        raise RecoveryConsistencyError("retry_budget_evidence_mismatch")
    max_attempts = root["max_attempts"]
    if (type(max_attempts) is not int
            or not 1 <= max_attempts <= MAX_RETRY_ATTEMPTS):
        raise RecoveryConsistencyError("invalid_max_attempts")
    used_attempts = len(events)
    if used_attempts > max_attempts:
        raise RecoveryConsistencyError("retry_budget_exceeded")

    remaining_attempts = max_attempts - used_attempts
    if report["verdict"] == "recovered":
        disposition = "closed_recovered"
        retry_permitted = False
    elif remaining_attempts == 0:
        disposition = "closed_exhausted"
        retry_permitted = False
    else:
        disposition = "retry_permitted_by_recorded_budget"
        retry_permitted = True
    result = {
        "retry_budget_schema_version": SCHEMA_VERSION,
        "budget_id": budget_id,
        "recovery_evidence_id": supplied_evidence_id,
        "max_attempts": max_attempts,
        "used_attempts": used_attempts,
        "remaining_attempts": remaining_attempts,
        "recovery_verdict": report["verdict"],
        "disposition": disposition,
        "retry_permitted": retry_permitted,
        "coverage": {
            "budget_bound": True,
            "recovery_report_verified": True,
            "scope": "bounded_recorded_retry_budget_metadata_only",
        },
        "authority": RETRY_BUDGET_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("retry_budget_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def evaluate_recorded_state_checkpoint(
    recovery_report: Mapping[str, object], checkpoint: Mapping[str, object]
) -> dict:
    """Bind one recorded state checkpoint to an exact recovery report.

    All hashes and the generation are caller-supplied metadata.  This function
    does not read from or write to durable storage.
    """

    report = _verified_recovery_report(recovery_report)
    root = _exact_dict(
        checkpoint,
        frozenset({
            "schema_version", "checkpoint_id", "recovery_evidence_id",
            "generation", "initial_state_sha256", "checkpoint_state_sha256",
        }),
        "invalid_state_checkpoint_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecoveryConsistencyError("unsupported_state_checkpoint_schema_version")
    checkpoint_id = _text(
        root["checkpoint_id"], _IDENTIFIER, "invalid_checkpoint_id")
    recovery_evidence_id = _text(
        root["recovery_evidence_id"], _SHA256, "invalid_recovery_evidence_id")
    if recovery_evidence_id != report["evidence_id"]:
        raise RecoveryConsistencyError("state_checkpoint_evidence_mismatch")
    generation = root["generation"]
    if (type(generation) is not int
            or not 1 <= generation <= MAX_CHECKPOINT_GENERATION):
        raise RecoveryConsistencyError("invalid_checkpoint_generation")
    initial_state = _text(
        root["initial_state_sha256"], _SHA256, "invalid_initial_state_hash")
    checkpoint_state = _text(
        root["checkpoint_state_sha256"], _SHA256, "invalid_checkpoint_state_hash")
    events = report["events"]
    if initial_state != events[0]["state_before_sha256"]:
        raise RecoveryConsistencyError("checkpoint_initial_state_mismatch")
    if checkpoint_state != events[-1]["state_after_sha256"]:
        raise RecoveryConsistencyError("checkpoint_state_mismatch")

    result = {
        "state_checkpoint_schema_version": SCHEMA_VERSION,
        "checkpoint_id": checkpoint_id,
        "recovery_evidence_id": recovery_evidence_id,
        "generation": generation,
        "initial_state_sha256": initial_state,
        "checkpoint_state_sha256": checkpoint_state,
        "recovery_verdict": report["verdict"],
        "state_consistent": True,
        "coverage": {
            "recovery_report_verified": True,
            "recorded_events": len(events),
            "scope": "bounded_recorded_state_checkpoint_metadata_only",
        },
        "authority": STATE_CHECKPOINT_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("state_checkpoint_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result
