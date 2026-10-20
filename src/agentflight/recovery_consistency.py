"""Deterministic validation of recorded recovery and state-consistency evidence.

The validator accepts only caller-supplied hashes and enumerated outcomes.  It
does not retry, recover, execute, inspect a project, or read durable state.
"""

import hashlib
import json
import re
from collections.abc import Iterable, Mapping


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
RESUME_GUARD_AUTHORITY = (
    "recorded_resume_guard_only_no_retry_recovery_or_execution"
)
RESUME_TRANSITION_AUTHORITY = (
    "recorded_resume_transition_only_no_retry_recovery_or_execution"
)
RESUME_LINEAGE_AUTHORITY = (
    "recorded_resume_lineage_only_no_retry_recovery_or_execution"
)
RESUME_CLOSURE_AUTHORITY = (
    "recorded_resume_closure_only_no_retry_recovery_or_execution"
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


def evaluate_recorded_resume_guard(
    recovery_report: Mapping[str, object],
    retry_budget: Mapping[str, object],
    state_checkpoint: Mapping[str, object],
) -> dict:
    """Combine exact recorded recovery, budget, and checkpoint evidence.

    A ``resume_candidate`` disposition describes metadata consistency only. It
    neither authorizes nor performs a retry, recovery, restore, or execution.
    """

    report = _verified_recovery_report(recovery_report)
    budget_result = evaluate_recorded_retry_budget(report, retry_budget)
    checkpoint_result = evaluate_recorded_state_checkpoint(report, state_checkpoint)

    if report["verdict"] == "recovered":
        disposition = "closed_recovered"
        next_attempt = None
    elif budget_result["retry_permitted"]:
        disposition = "resume_candidate"
        next_attempt = budget_result["used_attempts"] + 1
    else:
        disposition = "closed_exhausted"
        next_attempt = None

    result = {
        "resume_guard_schema_version": SCHEMA_VERSION,
        "recovery_evidence_id": report["evidence_id"],
        "retry_budget_evidence_id": budget_result["evidence_id"],
        "state_checkpoint_evidence_id": checkpoint_result["evidence_id"],
        "checkpoint_generation": checkpoint_result["generation"],
        "checkpoint_state_sha256": checkpoint_result["checkpoint_state_sha256"],
        "used_attempts": budget_result["used_attempts"],
        "remaining_attempts": budget_result["remaining_attempts"],
        "next_attempt": next_attempt,
        "disposition": disposition,
        "coverage": {
            "recovery_report_verified": True,
            "retry_budget_verified": True,
            "state_checkpoint_verified": True,
            "scope": "bounded_recorded_resume_guard_metadata_only",
        },
        "authority": RESUME_GUARD_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("resume_guard_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def _verified_resume_guard(resume_guard: Mapping[str, object]) -> dict:
    guard = _exact_dict(
        resume_guard,
        frozenset({
            "resume_guard_schema_version", "recovery_evidence_id",
            "retry_budget_evidence_id", "state_checkpoint_evidence_id",
            "checkpoint_generation", "checkpoint_state_sha256",
            "used_attempts", "remaining_attempts", "next_attempt",
            "disposition", "coverage", "authority", "evidence_id",
        }),
        "invalid_resume_guard_shape",
    )
    supplied_evidence_id = _text(
        guard["evidence_id"], _SHA256, "invalid_resume_guard_evidence_id")
    unsigned = {key: value for key, value in guard.items() if key != "evidence_id"}
    expected_evidence_id = hashlib.sha256(
        _canonical(unsigned).encode("utf-8")
    ).hexdigest()
    if supplied_evidence_id != expected_evidence_id:
        raise RecoveryConsistencyError("resume_guard_evidence_mismatch")
    if (type(guard["resume_guard_schema_version"]) is not int
            or guard["resume_guard_schema_version"] != SCHEMA_VERSION):
        raise RecoveryConsistencyError("invalid_resume_guard")
    for key in (
        "recovery_evidence_id", "retry_budget_evidence_id",
        "state_checkpoint_evidence_id", "checkpoint_state_sha256",
    ):
        _text(guard[key], _SHA256, "invalid_resume_guard")
    generation = guard["checkpoint_generation"]
    used = guard["used_attempts"]
    remaining = guard["remaining_attempts"]
    if (type(generation) is not int
            or not 1 <= generation <= MAX_CHECKPOINT_GENERATION
            or type(used) is not int or not 1 <= used <= MAX_RETRY_ATTEMPTS
            or type(remaining) is not int
            or not 0 <= remaining <= MAX_RETRY_ATTEMPTS - used):
        raise RecoveryConsistencyError("invalid_resume_guard")
    disposition = guard["disposition"]
    if disposition == "resume_candidate":
        if guard["next_attempt"] != used + 1 or remaining < 1:
            raise RecoveryConsistencyError("invalid_resume_guard")
    elif disposition in {"closed_recovered", "closed_exhausted"}:
        if guard["next_attempt"] is not None:
            raise RecoveryConsistencyError("invalid_resume_guard")
    else:
        raise RecoveryConsistencyError("invalid_resume_guard")
    if guard["coverage"] != {
        "recovery_report_verified": True,
        "retry_budget_verified": True,
        "state_checkpoint_verified": True,
        "scope": "bounded_recorded_resume_guard_metadata_only",
    } or guard["authority"] != RESUME_GUARD_AUTHORITY:
        raise RecoveryConsistencyError("invalid_resume_guard")
    return guard


def evaluate_recorded_resume_transition(
    prior_resume_guard: Mapping[str, object],
    prior_recovery_report: Mapping[str, object],
    current_recovery_report: Mapping[str, object],
    current_retry_budget: Mapping[str, object],
    current_state_checkpoint: Mapping[str, object],
    transition: Mapping[str, object],
) -> dict:
    """Verify one exact recorded resume step without performing it.

    The current recovery transcript must append exactly one event to the prior
    transcript, preserve the full prefix, and advance the checkpoint generation
    exactly once. The returned disposition remains metadata-only.
    """

    prior_guard = _verified_resume_guard(prior_resume_guard)
    prior_report = _verified_recovery_report(prior_recovery_report)
    if prior_guard["recovery_evidence_id"] != prior_report["evidence_id"]:
        raise RecoveryConsistencyError("prior_resume_guard_recovery_mismatch")
    if prior_guard["disposition"] != "resume_candidate":
        raise RecoveryConsistencyError("prior_resume_guard_not_candidate")
    if prior_guard["used_attempts"] != len(prior_report["events"]):
        raise RecoveryConsistencyError("prior_resume_guard_attempt_mismatch")
    if (prior_guard["checkpoint_state_sha256"]
            != prior_report["events"][-1]["state_after_sha256"]):
        raise RecoveryConsistencyError("prior_resume_guard_state_mismatch")

    current_report = _verified_recovery_report(current_recovery_report)
    prior_events = prior_report["events"]
    current_events = current_report["events"]
    if (len(current_events) != len(prior_events) + 1
            or current_events[:-1] != prior_events):
        raise RecoveryConsistencyError("invalid_resume_event_advance")
    if current_report["recovery_id"] != prior_report["recovery_id"]:
        raise RecoveryConsistencyError("resume_recovery_id_mismatch")
    for key in (
        "failure_plan_evidence_id", "trajectory_evidence_id",
        "operation_evidence_id", "idempotency_key_sha256",
    ):
        if current_report[key] != prior_report[key]:
            raise RecoveryConsistencyError("resume_recovery_binding_mismatch")

    current_guard = evaluate_recorded_resume_guard(
        current_report, current_retry_budget, current_state_checkpoint)
    if current_guard["used_attempts"] != prior_guard["next_attempt"]:
        raise RecoveryConsistencyError("invalid_resume_attempt_advance")
    if (current_guard["checkpoint_generation"]
            != prior_guard["checkpoint_generation"] + 1):
        raise RecoveryConsistencyError("invalid_resume_generation_advance")

    root = _exact_dict(
        transition,
        frozenset({
            "schema_version", "transition_id",
            "prior_resume_guard_evidence_id",
            "current_resume_guard_evidence_id",
        }),
        "invalid_resume_transition_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecoveryConsistencyError("unsupported_resume_transition_schema_version")
    transition_id = _text(
        root["transition_id"], _IDENTIFIER, "invalid_resume_transition_id")
    prior_evidence_id = _text(
        root["prior_resume_guard_evidence_id"], _SHA256,
        "invalid_resume_guard_evidence_id")
    current_evidence_id = _text(
        root["current_resume_guard_evidence_id"], _SHA256,
        "invalid_resume_guard_evidence_id")
    if prior_evidence_id != prior_guard["evidence_id"]:
        raise RecoveryConsistencyError("prior_resume_guard_evidence_mismatch")
    if current_evidence_id != current_guard["evidence_id"]:
        raise RecoveryConsistencyError("current_resume_guard_evidence_mismatch")

    result = {
        "resume_transition_schema_version": SCHEMA_VERSION,
        "transition_id": transition_id,
        "prior_resume_guard_evidence_id": prior_evidence_id,
        "current_resume_guard_evidence_id": current_evidence_id,
        "prior_attempts": prior_guard["used_attempts"],
        "current_attempts": current_guard["used_attempts"],
        "prior_checkpoint_generation": prior_guard["checkpoint_generation"],
        "current_checkpoint_generation": current_guard["checkpoint_generation"],
        "disposition": current_guard["disposition"],
        "coverage": {
            "prior_resume_guard_verified": True,
            "current_resume_guard_recomputed": True,
            "recorded_event_advance": 1,
            "checkpoint_generation_advance": 1,
            "scope": "bounded_recorded_resume_transition_metadata_only",
        },
        "authority": RESUME_TRANSITION_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("resume_transition_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def _verified_resume_transition_report(value: Mapping[str, object]) -> dict:
    report = _exact_dict(
        value,
        frozenset({
            "resume_transition_schema_version", "transition_id",
            "prior_resume_guard_evidence_id", "current_resume_guard_evidence_id",
            "prior_attempts", "current_attempts", "prior_checkpoint_generation",
            "current_checkpoint_generation", "disposition", "coverage",
            "authority", "evidence_id",
        }),
        "invalid_resume_transition_report_shape",
    )
    supplied = _text(
        report["evidence_id"], _SHA256, "invalid_resume_transition_evidence_id")
    unsigned = {key: item for key, item in report.items() if key != "evidence_id"}
    if supplied != hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest():
        raise RecoveryConsistencyError("resume_transition_evidence_mismatch")
    if (type(report["resume_transition_schema_version"]) is not int
            or report["resume_transition_schema_version"] != SCHEMA_VERSION):
        raise RecoveryConsistencyError("invalid_resume_transition_report")
    _text(report["transition_id"], _IDENTIFIER, "invalid_resume_transition_report")
    _text(report["prior_resume_guard_evidence_id"], _SHA256,
          "invalid_resume_transition_report")
    _text(report["current_resume_guard_evidence_id"], _SHA256,
          "invalid_resume_transition_report")
    for prior_key, current_key, upper in (
        ("prior_attempts", "current_attempts", MAX_RETRY_ATTEMPTS),
        ("prior_checkpoint_generation", "current_checkpoint_generation",
         MAX_CHECKPOINT_GENERATION),
    ):
        prior = report[prior_key]
        current = report[current_key]
        if (type(prior) is not int or type(current) is not int
                or not 1 <= prior < current <= upper or current != prior + 1):
            raise RecoveryConsistencyError("invalid_resume_transition_report")
    if report["disposition"] not in {
        "resume_candidate", "closed_recovered", "closed_exhausted",
    }:
        raise RecoveryConsistencyError("invalid_resume_transition_report")
    if report["coverage"] != {
        "prior_resume_guard_verified": True,
        "current_resume_guard_recomputed": True,
        "recorded_event_advance": 1,
        "checkpoint_generation_advance": 1,
        "scope": "bounded_recorded_resume_transition_metadata_only",
    } or report["authority"] != RESUME_TRANSITION_AUTHORITY:
        raise RecoveryConsistencyError("invalid_resume_transition_report")
    return report


def evaluate_recorded_resume_lineage(
    transition_reports: Iterable[Mapping[str, object]],
) -> dict:
    """Verify a bounded ordered lineage of recorded resume transitions.

    This validates content-addressed metadata continuity only. It does not
    perform or authorize a retry, recovery, restore, or execution.
    """

    try:
        reports = tuple(transition_reports)
    except TypeError:
        raise RecoveryConsistencyError("invalid_resume_lineage") from None
    if not 1 <= len(reports) <= MAX_RETRY_ATTEMPTS - 1:
        raise RecoveryConsistencyError("invalid_resume_lineage_count")

    verified = []
    transition_ids = set()
    evidence_ids = set()
    for index, value in enumerate(reports):
        report = _verified_resume_transition_report(value)
        if report["transition_id"] in transition_ids:
            raise RecoveryConsistencyError("duplicate_resume_transition_id")
        if report["evidence_id"] in evidence_ids:
            raise RecoveryConsistencyError("duplicate_resume_transition_evidence")
        transition_ids.add(report["transition_id"])
        evidence_ids.add(report["evidence_id"])
        if index:
            prior = verified[-1]
            if (report["prior_resume_guard_evidence_id"]
                    != prior["current_resume_guard_evidence_id"]
                    or report["prior_attempts"] != prior["current_attempts"]
                    or report["prior_checkpoint_generation"]
                    != prior["current_checkpoint_generation"]):
                raise RecoveryConsistencyError("resume_lineage_discontinuity")
            if prior["disposition"] != "resume_candidate":
                raise RecoveryConsistencyError("resume_transition_after_terminal")
        verified.append(report)

    first = verified[0]
    last = verified[-1]
    result = {
        "resume_lineage_schema_version": SCHEMA_VERSION,
        "transition_evidence_ids": [item["evidence_id"] for item in verified],
        "first_resume_guard_evidence_id": first["prior_resume_guard_evidence_id"],
        "last_resume_guard_evidence_id": last["current_resume_guard_evidence_id"],
        "transition_count": len(verified),
        "initial_attempts": first["prior_attempts"],
        "final_attempts": last["current_attempts"],
        "initial_checkpoint_generation": first["prior_checkpoint_generation"],
        "final_checkpoint_generation": last["current_checkpoint_generation"],
        "final_disposition": last["disposition"],
        "coverage": {
            "transition_reports_verified": len(verified),
            "scope": "bounded_recorded_resume_lineage_metadata_only",
        },
        "authority": RESUME_LINEAGE_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("resume_lineage_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result


def _verified_resume_lineage_report(value: Mapping[str, object]) -> dict:
    report = _exact_dict(
        value,
        frozenset({
            "resume_lineage_schema_version", "transition_evidence_ids",
            "first_resume_guard_evidence_id", "last_resume_guard_evidence_id",
            "transition_count", "initial_attempts", "final_attempts",
            "initial_checkpoint_generation", "final_checkpoint_generation",
            "final_disposition", "coverage", "authority", "evidence_id",
        }),
        "invalid_resume_lineage_report_shape",
    )
    supplied = _text(
        report["evidence_id"], _SHA256, "invalid_resume_lineage_evidence_id")
    unsigned = {key: item for key, item in report.items() if key != "evidence_id"}
    if supplied != hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest():
        raise RecoveryConsistencyError("resume_lineage_evidence_mismatch")
    if (type(report["resume_lineage_schema_version"]) is not int
            or report["resume_lineage_schema_version"] != SCHEMA_VERSION):
        raise RecoveryConsistencyError("invalid_resume_lineage_report")
    evidence_ids = report["transition_evidence_ids"]
    count = report["transition_count"]
    if (type(evidence_ids) is not list or type(count) is not int
            or not 1 <= count <= MAX_RETRY_ATTEMPTS - 1
            or len(evidence_ids) != count or len(set(evidence_ids)) != count):
        raise RecoveryConsistencyError("invalid_resume_lineage_report")
    for evidence_id in evidence_ids:
        _text(evidence_id, _SHA256, "invalid_resume_lineage_report")
    for key in ("first_resume_guard_evidence_id", "last_resume_guard_evidence_id"):
        _text(report[key], _SHA256, "invalid_resume_lineage_report")
    initial_attempts = report["initial_attempts"]
    final_attempts = report["final_attempts"]
    initial_generation = report["initial_checkpoint_generation"]
    final_generation = report["final_checkpoint_generation"]
    if (type(initial_attempts) is not int or type(final_attempts) is not int
            or not 1 <= initial_attempts < final_attempts <= MAX_RETRY_ATTEMPTS
            or final_attempts - initial_attempts != count
            or type(initial_generation) is not int or type(final_generation) is not int
            or not 1 <= initial_generation < final_generation <= MAX_CHECKPOINT_GENERATION
            or final_generation - initial_generation != count):
        raise RecoveryConsistencyError("invalid_resume_lineage_report")
    if report["final_disposition"] not in {
        "resume_candidate", "closed_recovered", "closed_exhausted",
    }:
        raise RecoveryConsistencyError("invalid_resume_lineage_report")
    if report["coverage"] != {
        "transition_reports_verified": count,
        "scope": "bounded_recorded_resume_lineage_metadata_only",
    } or report["authority"] != RESUME_LINEAGE_AUTHORITY:
        raise RecoveryConsistencyError("invalid_resume_lineage_report")
    return report


def evaluate_recorded_resume_closure(
    lineage_report: Mapping[str, object], closure: Mapping[str, object]
) -> dict:
    """Certify only a terminal recorded resume lineage.

    Closure is content-addressed metadata, not permission to retry, recover,
    restore, or execute. An unfinished ``resume_candidate`` fails closed.
    """

    lineage = _verified_resume_lineage_report(lineage_report)
    if lineage["final_disposition"] == "resume_candidate":
        raise RecoveryConsistencyError("resume_lineage_not_terminal")
    root = _exact_dict(
        closure,
        frozenset({
            "schema_version", "closure_id", "resume_lineage_evidence_id",
            "expected_terminal_disposition",
        }),
        "invalid_resume_closure_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecoveryConsistencyError("unsupported_resume_closure_schema_version")
    closure_id = _text(root["closure_id"], _IDENTIFIER, "invalid_resume_closure_id")
    lineage_evidence_id = _text(
        root["resume_lineage_evidence_id"], _SHA256,
        "invalid_resume_lineage_evidence_id")
    if lineage_evidence_id != lineage["evidence_id"]:
        raise RecoveryConsistencyError("resume_closure_lineage_evidence_mismatch")
    expected = root["expected_terminal_disposition"]
    if expected not in {"closed_recovered", "closed_exhausted"}:
        raise RecoveryConsistencyError("invalid_expected_terminal_disposition")
    if expected != lineage["final_disposition"]:
        raise RecoveryConsistencyError("resume_closure_disposition_mismatch")

    result = {
        "resume_closure_schema_version": SCHEMA_VERSION,
        "closure_id": closure_id,
        "resume_lineage_evidence_id": lineage_evidence_id,
        "terminal_disposition": expected,
        "final_attempts": lineage["final_attempts"],
        "final_checkpoint_generation": lineage["final_checkpoint_generation"],
        "closed": True,
        "coverage": {
            "resume_lineage_verified": True,
            "transition_reports_verified": lineage["transition_count"],
            "scope": "bounded_recorded_resume_closure_metadata_only",
        },
        "authority": RESUME_CLOSURE_AUTHORITY,
    }
    canonical = _canonical(result)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise RecoveryConsistencyError("resume_closure_report_too_large")
    result["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return result
