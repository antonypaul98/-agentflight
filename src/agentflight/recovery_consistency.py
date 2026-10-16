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
MAX_REPORT_BYTES = 32_768
AUTHORITY = "recorded_recovery_consistency_only_no_execution"

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
