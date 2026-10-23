import copy

import pytest

from agentflight.security_probes import (
    AUTHORITY,
    INFLUENCE_LINEAGE_AUTHORITY,
    INSTRUCTION_PROVENANCE_AUTHORITY,
    SecurityProbeError,
    evaluate_recorded_influence_lineage,
    evaluate_recorded_instruction_provenance,
    evaluate_recorded_security_probe,
)

H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64
H5 = "5" * 64


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


def provenance():
    security_probe = probe()
    return {
        "schema_version": 1,
        "provenance_id": "trusted-policy-lineage",
        "security_probe": security_probe,
        "security_probe_evidence_id": evaluate_recorded_security_probe(
            security_probe
        )["evidence_id"],
        "trusted_instruction_sha256": H3,
        "observed_instruction_sha256": H3,
        "instruction_source_boundary": "trusted_control",
        "override_attempt_detected": False,
        "observed_disposition": "accepted",
    }


def lineage():
    first = provenance()
    first["provenance_id"] = "hop-one-provenance"
    first["trusted_instruction_sha256"] = H3
    first["observed_instruction_sha256"] = H3
    second = provenance()
    second["provenance_id"] = "hop-two-provenance"
    second["trusted_instruction_sha256"] = H4
    second["observed_instruction_sha256"] = H4
    return {
        "schema_version": 1,
        "lineage_id": "two-hop-trusted-lineage",
        "hops": [
            {
                "hop_id": "hop-one",
                "instruction_provenance": first,
                "instruction_provenance_evidence_id": (
                    evaluate_recorded_instruction_provenance(first)["evidence_id"]
                ),
                "input_sha256": H3,
                "output_sha256": H4,
            },
            {
                "hop_id": "hop-two",
                "instruction_provenance": second,
                "instruction_provenance_evidence_id": (
                    evaluate_recorded_instruction_provenance(second)["evidence_id"]
                ),
                "input_sha256": H4,
                "output_sha256": H5,
            },
        ],
        "observed_disposition": "accepted",
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


def test_matching_trusted_instruction_lineage_passes_deterministically():
    first = evaluate_recorded_instruction_provenance(provenance())
    assert first == evaluate_recorded_instruction_provenance(
        copy.deepcopy(provenance())
    )
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == INSTRUCTION_PROVENANCE_AUTHORITY


@pytest.mark.parametrize("change,reason", [
    (
        lambda value: value.update(instruction_source_boundary="untrusted_content"),
        "untrusted_instruction_source",
    ),
    (
        lambda value: value.update(observed_instruction_sha256=H2),
        "instruction_provenance_mismatch",
    ),
    (
        lambda value: value.update(override_attempt_detected=True),
        "policy_override_attempt",
    ),
])
def test_instruction_lineage_fail_closed_conditions_require_rejection(change, reason):
    source = provenance()
    change(source)
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_instruction_provenance(source)
    assert report["passed"] is True
    assert report["expected_disposition"] == "rejected"
    assert reason in report["rejection_reasons"]


def test_denied_or_inconsistent_security_probe_cannot_be_accepted():
    denied = provenance()
    denied["security_probe"].update(
        injection_detected=True, observed_decision="denied"
    )
    denied["security_probe_evidence_id"] = evaluate_recorded_security_probe(
        denied["security_probe"]
    )["evidence_id"]
    denied["observed_disposition"] = "rejected"
    report = evaluate_recorded_instruction_provenance(denied)
    assert report["rejection_reasons"] == ["security_probe_requires_denial"]

    inconsistent = provenance()
    inconsistent["security_probe"]["observed_decision"] = "denied"
    inconsistent["security_probe_evidence_id"] = evaluate_recorded_security_probe(
        inconsistent["security_probe"]
    )["evidence_id"]
    inconsistent["observed_disposition"] = "rejected"
    report = evaluate_recorded_instruction_provenance(inconsistent)
    assert report["rejection_reasons"] == ["security_probe_failed"]


def test_instruction_provenance_is_bound_to_recomputed_security_evidence():
    source = provenance()
    source["security_probe_evidence_id"] = H0
    with pytest.raises(SecurityProbeError, match="security_probe_evidence_mismatch"):
        evaluate_recorded_instruction_provenance(source)


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_instruction_provenance_shape"),
    (lambda value: value.update(schema_version=True), "unsupported_instruction_provenance_schema"),
    (lambda value: value.update(override_attempt_detected=1), "invalid_override_attempt_flag"),
    (lambda value: value.update(instruction_source_boundary="unknown"), "invalid_instruction_source_boundary"),
    (lambda value: value.update(observed_disposition="maybe"), "invalid_observed_disposition"),
])
def test_malformed_instruction_provenance_fails_closed(change, code):
    source = provenance()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_instruction_provenance(source)


def test_instruction_provenance_report_contains_no_raw_instruction_or_action_fields():
    rendered = repr(evaluate_recorded_instruction_provenance(provenance()))
    for forbidden in ("prompt", "payload", "instruction_text", "command", "credential"):
        assert forbidden not in rendered


def test_trusted_multi_hop_lineage_passes_deterministically():
    first = evaluate_recorded_influence_lineage(lineage())
    assert first == evaluate_recorded_influence_lineage(copy.deepcopy(lineage()))
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["influenced_hop_ids"] == []
    assert first["authority"] == INFLUENCE_LINEAGE_AUTHORITY


def test_untrusted_influence_propagates_to_downstream_hops_and_requires_rejection():
    source = lineage()
    first = source["hops"][0]["instruction_provenance"]
    first["instruction_source_boundary"] = "untrusted_content"
    first["observed_disposition"] = "rejected"
    source["hops"][0]["instruction_provenance_evidence_id"] = (
        evaluate_recorded_instruction_provenance(first)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_influence_lineage(source)
    assert report["passed"] is True
    assert report["influenced_hop_ids"] == ["hop-one", "hop-two"]
    assert report["rejection_reasons"] == [
        "hop-one:instruction_requires_rejection",
        "untrusted_influence_propagated",
    ]


def test_recorded_injection_taints_current_and_downstream_hops():
    source = lineage()
    first = source["hops"][0]["instruction_provenance"]
    first["security_probe"].update(
        injection_detected=True, observed_decision="denied"
    )
    first["security_probe_evidence_id"] = evaluate_recorded_security_probe(
        first["security_probe"]
    )["evidence_id"]
    first["observed_disposition"] = "rejected"
    source["hops"][0]["instruction_provenance_evidence_id"] = (
        evaluate_recorded_instruction_provenance(first)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_influence_lineage(source)
    assert report["influenced_hop_ids"] == ["hop-one", "hop-two"]
    assert report["expected_disposition"] == "rejected"


def test_lineage_exposes_bypass_when_rejection_is_recorded_as_accepted():
    source = lineage()
    first = source["hops"][0]["instruction_provenance"]
    first["instruction_source_boundary"] = "untrusted_content"
    first["observed_disposition"] = "rejected"
    source["hops"][0]["instruction_provenance_evidence_id"] = (
        evaluate_recorded_instruction_provenance(first)["evidence_id"]
    )
    report = evaluate_recorded_influence_lineage(source)
    assert report["expected_disposition"] == "rejected"
    assert report["passed"] is False


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_influence_lineage_shape"),
    (lambda value: value.update(schema_version=True), "unsupported_influence_lineage_schema"),
    (lambda value: value.update(hops=[]), "invalid_influence_hops"),
    (lambda value: value.update(observed_disposition="maybe"), "invalid_influence_lineage_disposition"),
    (lambda value: value["hops"][0].update(payload="raw"), "invalid_influence_hop_shape"),
    (lambda value: value["hops"][1].update(hop_id="hop-one"), "duplicate_influence_hop_id"),
])
def test_malformed_or_action_bearing_influence_lineage_fails_closed(change, code):
    source = lineage()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_influence_lineage(source)


def test_lineage_is_bound_to_recomputed_provenance_evidence():
    source = lineage()
    source["hops"][0]["instruction_provenance_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="instruction_provenance_evidence_mismatch"
    ):
        evaluate_recorded_influence_lineage(source)


def test_lineage_input_must_match_provenance_and_prior_output():
    source = lineage()
    source["hops"][0]["input_sha256"] = H2
    with pytest.raises(
        SecurityProbeError, match="influence_input_provenance_mismatch"
    ):
        evaluate_recorded_influence_lineage(source)

    source = lineage()
    source["hops"][0]["output_sha256"] = H2
    with pytest.raises(SecurityProbeError, match="influence_lineage_discontinuity"):
        evaluate_recorded_influence_lineage(source)


def test_influence_lineage_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_influence_lineage(lineage()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential", "url"
    ):
        assert forbidden not in rendered
