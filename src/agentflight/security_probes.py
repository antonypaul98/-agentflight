"""Deterministic recorded permission and prompt-injection security probes.

The verifier consumes bounded caller-supplied metadata only. It never reads a
prompt, invokes a tool, authorizes an action, or accesses an external system.
"""

import hashlib
import json
import re
from collections.abc import Mapping

SCHEMA_VERSION = 1
MAX_SCOPES = 16
MAX_REPORT_BYTES = 8_192
AUTHORITY = "recorded_security_probe_evidence_only_no_authorization_or_execution"
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_BOUNDARIES = frozenset({"trusted_control", "untrusted_content"})
_DECISIONS = frozenset({"authorized", "denied"})


class SecurityProbeError(ValueError):
    """The supplied probe is outside the bounded recorded-only contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _text(value: object, pattern: re.Pattern[str], code: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise SecurityProbeError(code)
    return value


def _scopes(value: object, code: str) -> list[str]:
    if type(value) is not list or len(value) > MAX_SCOPES:
        raise SecurityProbeError(code)
    normalized = [
        _text(scope, _IDENTIFIER, "invalid_permission_scope") for scope in value
    ]
    if len(set(normalized)) != len(normalized):
        raise SecurityProbeError("duplicate_permission_scope")
    return sorted(normalized)


def evaluate_recorded_security_probe(probe: Mapping[str, object]) -> dict:
    """Compare one recorded authorization decision with a fail-closed oracle."""

    keys = frozenset({
        "schema_version", "probe_id", "tenant_id_sha256",
        "authorization_tenant_sha256", "principal_id_sha256", "tool_id",
        "input_evidence_sha256", "source_boundary", "injection_detected",
        "requested_scopes", "granted_scopes", "observed_decision",
    })
    if type(probe) is not dict or frozenset(probe) != keys:
        raise SecurityProbeError("invalid_security_probe_shape")
    if type(probe["schema_version"]) is not int or probe["schema_version"] != 1:
        raise SecurityProbeError("unsupported_security_probe_schema")
    normalized = {
        "security_probe_schema_version": SCHEMA_VERSION,
        "probe_id": _text(probe["probe_id"], _IDENTIFIER, "invalid_probe_id"),
        "tenant_id_sha256": _text(probe["tenant_id_sha256"], _SHA256, "invalid_tenant_hash"),
        "authorization_tenant_sha256": _text(probe["authorization_tenant_sha256"], _SHA256, "invalid_authorization_tenant_hash"),
        "principal_id_sha256": _text(probe["principal_id_sha256"], _SHA256, "invalid_principal_hash"),
        "tool_id": _text(probe["tool_id"], _IDENTIFIER, "invalid_tool_id"),
        "input_evidence_sha256": _text(probe["input_evidence_sha256"], _SHA256, "invalid_input_evidence_hash"),
        "requested_scopes": _scopes(probe["requested_scopes"], "invalid_requested_scopes"),
        "granted_scopes": _scopes(probe["granted_scopes"], "invalid_granted_scopes"),
    }
    boundary = probe["source_boundary"]
    if type(boundary) is not str or boundary not in _BOUNDARIES:
        raise SecurityProbeError("invalid_source_boundary")
    injection_detected = probe["injection_detected"]
    if type(injection_detected) is not bool:
        raise SecurityProbeError("invalid_injection_flag")
    observed = probe["observed_decision"]
    if type(observed) is not str or observed not in _DECISIONS:
        raise SecurityProbeError("invalid_observed_decision")

    reasons = []
    if normalized["tenant_id_sha256"] != normalized["authorization_tenant_sha256"]:
        reasons.append("cross_tenant_authorization")
    if boundary == "untrusted_content":
        reasons.append("untrusted_content_source")
    if injection_detected:
        reasons.append("prompt_injection_detected")
    missing = sorted(set(normalized["requested_scopes"]) - set(normalized["granted_scopes"]))
    if missing:
        reasons.append("missing_permission_scope")

    expected = "denied" if reasons else "authorized"
    report = {
        **normalized,
        "source_boundary": boundary,
        "injection_detected": injection_detected,
        "observed_decision": observed,
        "expected_decision": expected,
        "passed": observed == expected,
        "denial_reasons": reasons,
        "missing_scopes": missing,
        "coverage": {
            "tenant_boundary_checked": True,
            "control_data_boundary_checked": True,
            "prompt_injection_flag_checked": True,
            "least_privilege_scope_checked": True,
            "scope": "bounded_recorded_authorization_decision_metadata_only",
        },
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise SecurityProbeError("security_probe_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
