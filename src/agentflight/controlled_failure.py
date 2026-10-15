"""Bounded, offline failure-injection evidence for recorded agent calls.

This module validates caller-supplied metadata and emits deterministic evidence.
It never performs a network request, sleeps, imports an agent framework, or
executes the recorded operation.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
MAX_SCENARIOS = 64
MAX_DELAY_MS = 300_000
MAX_REPORT_BYTES = 32_768
MAX_ATTEMPTS_PER_CALL = 4
AUTHORITY = "recorded_failure_injection_only_no_external_execution"

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OUTCOMES = {
    "network_error": frozenset({"dns_unavailable", "connection_reset"}),
    "timeout": frozenset({"deadline_exceeded"}),
    "rate_limit": frozenset({"http_429"}),
    "api_error": frozenset(
        {"http_400", "http_401", "http_403", "http_404", "http_409",
         "http_500", "http_502", "http_503", "http_504"}
    ),
}


class ControlledFailureError(ValueError):
    """The supplied failure plan is outside the offline contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _exact_dict(value: object, keys: frozenset[str], code: str) -> dict:
    if type(value) is not dict or frozenset(value) != keys:
        raise ControlledFailureError(code)
    return value


def _text(value: object, pattern: re.Pattern[str], code: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise ControlledFailureError(code)
    return value


def normalize_failure_plan(plan: Mapping[str, object]) -> dict:
    """Normalize one deterministic failure plan without retaining payloads."""

    root = _exact_dict(
        plan,
        frozenset({"schema_version", "plan_id", "environment_evidence_id", "scenarios"}),
        "invalid_failure_plan_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ControlledFailureError("unsupported_failure_plan_schema_version")
    scenarios = root["scenarios"]
    if type(scenarios) is not list or not 1 <= len(scenarios) <= MAX_SCENARIOS:
        raise ControlledFailureError("invalid_failure_scenario_count")

    normalized = []
    seen_calls = set()
    scenario_keys = frozenset(
        {"sequence", "fault_id", "call_index", "kind", "outcome_code", "delay_ms"}
    )
    for expected_sequence, item in enumerate(scenarios, start=1):
        scenario = _exact_dict(item, scenario_keys, "invalid_failure_scenario_shape")
        if type(scenario["sequence"]) is not int or scenario["sequence"] != expected_sequence:
            raise ControlledFailureError("invalid_failure_sequence")
        call_index = scenario["call_index"]
        if type(call_index) is not int or not 0 <= call_index < MAX_SCENARIOS:
            raise ControlledFailureError("invalid_failure_call_index")
        if call_index in seen_calls:
            raise ControlledFailureError("duplicate_failure_call_index")
        seen_calls.add(call_index)
        kind = scenario["kind"]
        if type(kind) is not str or kind not in _OUTCOMES:
            raise ControlledFailureError("unsupported_failure_kind")
        outcome = scenario["outcome_code"]
        if type(outcome) is not str or outcome not in _OUTCOMES[kind]:
            raise ControlledFailureError("invalid_failure_outcome")
        delay_ms = scenario["delay_ms"]
        if type(delay_ms) is not int or not 0 <= delay_ms <= MAX_DELAY_MS:
            raise ControlledFailureError("invalid_failure_delay")
        if (kind in {"timeout", "rate_limit"}) != (delay_ms > 0):
            raise ControlledFailureError("failure_delay_semantics_mismatch")
        normalized.append(
            {
                "sequence": expected_sequence,
                "fault_id": _text(scenario["fault_id"], _IDENTIFIER, "invalid_fault_id"),
                "call_index": call_index,
                "kind": kind,
                "outcome_code": outcome,
                "delay_ms": delay_ms,
            }
        )

    report = {
        "failure_plan_schema_version": SCHEMA_VERSION,
        "plan_id": _text(root["plan_id"], _IDENTIFIER, "invalid_failure_plan_id"),
        "environment_evidence_id": _text(
            root["environment_evidence_id"], _SHA256, "invalid_environment_evidence_id"
        ),
        "scenarios": normalized,
        "coverage": {
            "scenario_count": len(normalized),
            "kinds": sorted({item["kind"] for item in normalized}),
            "scope": "caller_supplied_recorded_metadata_only",
        },
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ControlledFailureError("failure_plan_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def evaluate_recorded_call(
    plan: Mapping[str, object], call_index: int, observed_sha256: str
) -> dict:
    """Evaluate a recorded call against a plan without executing the call."""

    normalized = normalize_failure_plan(plan)
    if type(call_index) is not int or not 0 <= call_index < MAX_SCENARIOS:
        raise ControlledFailureError("invalid_recorded_call_index")
    observed = _text(observed_sha256, _SHA256, "invalid_observed_call_hash")
    scenario = next(
        (item for item in normalized["scenarios"] if item["call_index"] == call_index), None
    )
    result = {
        "failure_plan_evidence_id": normalized["evidence_id"],
        "environment_evidence_id": normalized["environment_evidence_id"],
        "call_index": call_index,
        "observed_sha256": observed,
        "verdict": "injected" if scenario else "not_injected",
        "scenario": scenario,
        "authority": AUTHORITY,
    }
    result["evidence_id"] = hashlib.sha256(_canonical(result).encode("utf-8")).hexdigest()
    return result


def evaluate_recorded_sequence(
    plan: Mapping[str, object], attempts: list[Mapping[str, object]]
) -> dict:
    """Verify bounded recorded retry/outage metadata without executing anything."""

    normalized = normalize_failure_plan(plan)
    if type(attempts) is not list or not 1 <= len(attempts) <= MAX_SCENARIOS:
        raise ControlledFailureError("invalid_recorded_attempt_count")
    scenarios = {item["call_index"]: item for item in normalized["scenarios"]}
    expected_keys = frozenset(
        {"sequence", "call_index", "attempt", "observed_sha256",
         "outcome_code", "trajectory_evidence_id"}
    )
    rows = []
    previous_call = -1
    next_attempt = 1
    trajectory_id = None
    terminal_calls = set()
    for sequence, item in enumerate(attempts, start=1):
        row = _exact_dict(item, expected_keys, "invalid_recorded_attempt_shape")
        if type(row["sequence"]) is not int or row["sequence"] != sequence:
            raise ControlledFailureError("invalid_recorded_attempt_sequence")
        call_index = row["call_index"]
        if type(call_index) is not int or call_index not in scenarios:
            raise ControlledFailureError("attempt_not_bound_to_planned_fault")
        if call_index < previous_call or call_index in terminal_calls:
            raise ControlledFailureError("invalid_retry_order")
        if call_index != previous_call:
            next_attempt = 1
        attempt = row["attempt"]
        if type(attempt) is not int or attempt != next_attempt or attempt > MAX_ATTEMPTS_PER_CALL:
            raise ControlledFailureError("invalid_retry_attempt")
        scenario = scenarios[call_index]
        outcome = row["outcome_code"]
        allowed = _OUTCOMES[scenario["kind"]] | {"ok"}
        if type(outcome) is not str or outcome not in allowed:
            raise ControlledFailureError("invalid_recorded_retry_outcome")
        if attempt == 1 and outcome != scenario["outcome_code"]:
            raise ControlledFailureError("initial_outcome_plan_mismatch")
        current_trajectory = _text(
            row["trajectory_evidence_id"], _SHA256, "invalid_trajectory_evidence_id")
        if trajectory_id is None:
            trajectory_id = current_trajectory
        elif current_trajectory != trajectory_id:
            raise ControlledFailureError("trajectory_binding_mismatch")
        rows.append({
            "sequence": sequence,
            "call_index": call_index,
            "attempt": attempt,
            "observed_sha256": _text(
                row["observed_sha256"], _SHA256, "invalid_observed_call_hash"),
            "outcome_code": outcome,
            "fault_id": scenario["fault_id"],
            "decision": "stop_retrying" if outcome == "ok" else (
                "retry_budget_exhausted" if attempt == MAX_ATTEMPTS_PER_CALL
                else "retry_permitted"),
        })
        if outcome == "ok" or attempt == MAX_ATTEMPTS_PER_CALL:
            terminal_calls.add(call_index)
        previous_call = call_index
        next_attempt = attempt + 1

    calls = []
    for call_index in sorted({row["call_index"] for row in rows}):
        call_rows = [row for row in rows if row["call_index"] == call_index]
        calls.append({
            "call_index": call_index,
            "attempts": len(call_rows),
            "verdict": (
                "recovered" if call_rows[-1]["outcome_code"] == "ok"
                else "exhausted" if len(call_rows) == MAX_ATTEMPTS_PER_CALL
                else "incomplete"
            ),
        })
    report = {
        "failure_plan_evidence_id": normalized["evidence_id"],
        "environment_evidence_id": normalized["environment_evidence_id"],
        "trajectory_evidence_id": trajectory_id,
        "attempts": rows,
        "calls": calls,
        "coverage": {
            "recorded_attempts": len(rows),
            "recorded_calls": len(calls),
            "scope": "bounded_recorded_retry_and_outage_metadata_only",
        },
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ControlledFailureError("failure_sequence_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
