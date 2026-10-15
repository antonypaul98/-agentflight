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
