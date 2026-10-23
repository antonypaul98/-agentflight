import copy

import pytest

from agentflight.security_probes import AUTHORITY, SecurityProbeError, evaluate_recorded_security_probe

H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64


def probe():
    return {
        "schema_version": 1,
        "probe_id": "least-privilege-read",
        "tenant_id_sha256": H0,
        "authorization_tenant_sha256": H0,
        "principal_id_sha256": H1,
        "tool_id": "recorded-search",
        "input_evidence_sha256": H2,
        "source_boundary": "trusted_control",
        "injection_detected": False,
        "requested_scopes": ["records.read"],
        "granted_scopes": ["records.read"],
        "observed_decision": "authorized",
    }


def test_trusted_least_privilege_decision_passes_deterministically():
    first = evaluate_recorded_security_probe(probe())
    assert first == evaluate_recorded_security_probe(copy.deepcopy(probe()))
    assert first["passed"] is True
    assert first["expected_decision"] == "authorized"
    assert first["denial_reasons"] == []
    assert first["authority"] == AUTHORITY


@pytest.mark.parametrize("change,reason", [
    (lambda value: value.update(source_boundary="untrusted_content"), "untrusted_content_source"),
    (lambda value: value.update(injection_detected=True), "prompt_injection_detected"),
    (lambda value: value.update(authorization_tenant_sha256=H3), "cross_tenant_authorization"),
    (lambda value: value.update(requested_scopes=["records.read", "records.write"]), "missing_permission_scope"),
])
def test_fail_closed_conditions_require_denial(change, reason):
    source = probe()
    change(source)
    source["observed_decision"] = "denied"
    report = evaluate_recorded_security_probe(source)
    assert report["passed"] is True
    assert report["expected_decision"] == "denied"
    assert reason in report["denial_reasons"]


def test_privilege_escalation_and_injection_bypass_are_exposed():
    source = probe()
    source.update(source_boundary="untrusted_content", injection_detected=True,
                  requested_scopes=["admin.execute"], observed_decision="authorized")
    report = evaluate_recorded_security_probe(source)
    assert report["passed"] is False
    assert report["expected_decision"] == "denied"
    assert report["denial_reasons"] == [
        "untrusted_content_source", "prompt_injection_detected", "missing_permission_scope"
    ]


def test_scope_order_is_normalized_and_evidence_bound():
    source = probe()
    source["requested_scopes"] = ["records.write", "records.read"]
    source["granted_scopes"] = ["records.read", "records.write"]
    report = evaluate_recorded_security_probe(source)
    assert report["requested_scopes"] == ["records.read", "records.write"]
    changed = copy.deepcopy(source)
    changed["input_evidence_sha256"] = H3
    assert evaluate_recorded_security_probe(changed)["evidence_id"] != report["evidence_id"]


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_security_probe_shape"),
    (lambda value: value.update(schema_version=True), "unsupported_security_probe_schema"),
    (lambda value: value.update(injection_detected=1), "invalid_injection_flag"),
    (lambda value: value.update(source_boundary="unknown"), "invalid_source_boundary"),
    (lambda value: value.update(observed_decision="maybe"), "invalid_observed_decision"),
    (lambda value: value.update(requested_scopes=["records.read"] * 2), "duplicate_permission_scope"),
    (lambda value: value.update(granted_scopes=["scope"] * 17), "invalid_granted_scopes"),
])
def test_malformed_or_action_bearing_metadata_fails_closed(change, code):
    source = probe()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_security_probe(source)


def test_report_contains_no_raw_input_target_or_action_fields():
    rendered = repr(evaluate_recorded_security_probe(probe()))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered
