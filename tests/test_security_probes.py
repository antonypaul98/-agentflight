import copy

import pytest

from agentflight.security_probes import (
    AUTHORITY,
    INFLUENCE_LINEAGE_AUTHORITY,
    INSTRUCTION_PROVENANCE_AUTHORITY,
    SENSITIVE_SINK_AUTHORITY,
    SENSITIVE_SINK_BINDING_AUTHORITY,
    SCOPE_ATTENUATION_AUTHORITY,
    DELEGATION_VALIDITY_AUTHORITY,
    DELEGATION_CHAIN_AUTHORITY,
    DELEGATION_TIME_ATTENUATION_AUTHORITY,
    REDELEGATION_DEPTH_ATTENUATION_AUTHORITY,
    DELEGATION_REPLAY_GUARD_AUTHORITY,
    DELEGATION_AUDIENCE_BINDING_AUTHORITY,
    DELEGATION_ISSUER_BINDING_AUTHORITY,
    DELEGATION_IDENTITY_BINDING_AUTHORITY,
    DELEGATION_RESOURCE_BINDING_AUTHORITY,
    DELEGATION_ACTION_SCOPE_BINDING_AUTHORITY,
    DELEGATION_ACTION_TARGET_BINDING_AUTHORITY,
    DELEGATION_ACTION_COHERENCE_AUTHORITY,
    DELEGATION_ACTION_TUPLE_AUTHORITY,
    SecurityProbeError,
    evaluate_recorded_influence_lineage,
    evaluate_recorded_instruction_provenance,
    evaluate_recorded_security_probe,
    evaluate_recorded_sensitive_sink_boundary,
    evaluate_recorded_sensitive_sink_binding,
    evaluate_recorded_scope_attenuation,
    evaluate_recorded_delegation_validity,
    evaluate_recorded_delegation_chain,
    evaluate_recorded_delegation_time_attenuation,
    evaluate_recorded_redelegation_depth_attenuation,
    evaluate_recorded_delegation_replay_guard,
    evaluate_recorded_delegation_audience_binding,
    evaluate_recorded_delegation_issuer_binding,
    evaluate_recorded_delegation_identity_binding,
    evaluate_recorded_delegation_resource_binding,
    evaluate_recorded_delegation_action_scope_binding,
    evaluate_recorded_delegation_action_target_binding,
    evaluate_recorded_delegation_action_coherence,
    evaluate_recorded_delegation_action_tuple_binding,
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


def sensitive_sink():
    influence_lineage = lineage()
    return {
        "schema_version": 1,
        "boundary_id": "recorded-search-read-boundary",
        "influence_lineage": influence_lineage,
        "influence_lineage_evidence_id": evaluate_recorded_influence_lineage(
            influence_lineage
        )["evidence_id"],
        "sink_id": "recorded-search-results",
        "sink_class": "read_only",
        "observed_disposition": "accepted",
    }


def sensitive_sink_binding():
    boundary = sensitive_sink()
    return {
        "schema_version": 1,
        "binding_id": "recorded-search-tool-binding",
        "sensitive_sink_boundary": boundary,
        "sensitive_sink_evidence_id": evaluate_recorded_sensitive_sink_boundary(
            boundary
        )["evidence_id"],
        "sink_input_sha256": H5,
        "authorized_tool_id": "recorded-search",
        "observed_disposition": "accepted",
    }


def scope_attenuation():
    binding = sensitive_sink_binding()
    return {
        "schema_version": 1,
        "attenuation_id": "recorded-search-scope-attenuation",
        "sensitive_sink_binding": binding,
        "sensitive_sink_binding_evidence_id": (
            evaluate_recorded_sensitive_sink_binding(binding)["evidence_id"]
        ),
        "delegated_tenant_sha256": H0,
        "delegated_principal_id_sha256": H1,
        "delegated_tool_id": "recorded-search",
        "delegated_scopes": ["records.read"],
        "observed_disposition": "accepted",
    }


def delegation_validity():
    attenuation = scope_attenuation()
    return {
        "schema_version": 1,
        "validity_id": "recorded-search-delegation-validity",
        "scope_attenuation": attenuation,
        "scope_attenuation_evidence_id": evaluate_recorded_scope_attenuation(
            attenuation
        )["evidence_id"],
        "issued_at_tick": 100,
        "expires_at_tick": 200,
        "observed_at_tick": 150,
        "revoked": False,
        "observed_disposition": "accepted",
    }


def refresh_validity_evidence(validity):
    attenuation = validity["scope_attenuation"]
    binding = attenuation["sensitive_sink_binding"]
    boundary = binding["sensitive_sink_boundary"]
    lineage_value = boundary["influence_lineage"]
    for hop in lineage_value["hops"]:
        provenance_value = hop["instruction_provenance"]
        provenance_value["security_probe_evidence_id"] = (
            evaluate_recorded_security_probe(
                provenance_value["security_probe"]
            )["evidence_id"]
        )
        hop["instruction_provenance_evidence_id"] = (
            evaluate_recorded_instruction_provenance(provenance_value)[
                "evidence_id"
            ]
        )
    boundary["influence_lineage_evidence_id"] = (
        evaluate_recorded_influence_lineage(lineage_value)["evidence_id"]
    )
    binding["sensitive_sink_evidence_id"] = (
        evaluate_recorded_sensitive_sink_boundary(boundary)["evidence_id"]
    )
    attenuation["sensitive_sink_binding_evidence_id"] = (
        evaluate_recorded_sensitive_sink_binding(binding)["evidence_id"]
    )
    validity["scope_attenuation_evidence_id"] = (
        evaluate_recorded_scope_attenuation(attenuation)["evidence_id"]
    )


def delegation_chain():
    first = delegation_validity()
    first["validity_id"] = "chain-validity-one"
    second = delegation_validity()
    second["validity_id"] = "chain-validity-two"
    second["issued_at_tick"] = 151
    second["expires_at_tick"] = 190
    second["observed_at_tick"] = 175
    return {
        "schema_version": 1,
        "chain_id": "two-hop-delegation-chain",
        "hops": [
            {
                "hop_id": "delegation-hop-one",
                "delegation_validity": first,
                "delegation_validity_evidence_id": (
                    evaluate_recorded_delegation_validity(first)["evidence_id"]
                ),
            },
            {
                "hop_id": "delegation-hop-two",
                "delegation_validity": second,
                "delegation_validity_evidence_id": (
                    evaluate_recorded_delegation_validity(second)["evidence_id"]
                ),
            },
        ],
        "observed_disposition": "accepted",
    }


def delegation_time_attenuation():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "attenuation_id": "two-hop-delegation-time-attenuation",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "observed_disposition": "accepted",
    }


def redelegation_depth_attenuation():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "attenuation_id": "two-hop-redelegation-depth-attenuation",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "remaining_delegations": [1, 0],
        "observed_disposition": "accepted",
    }


def refresh_chain_evidence(attenuation):
    chain = attenuation["delegation_chain"]
    for hop in chain["hops"]:
        validity = hop["delegation_validity"]
        refresh_validity_evidence(validity)
        hop["delegation_validity_evidence_id"] = (
            evaluate_recorded_delegation_validity(validity)["evidence_id"]
        )
    attenuation["delegation_chain_evidence_id"] = (
        evaluate_recorded_delegation_chain(chain)["evidence_id"]
    )


def delegation_replay_guard():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "guard_id": "two-hop-delegation-replay-guard",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "observed_disposition": "accepted",
    }


def delegation_audience_binding():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "binding_id": "two-hop-delegation-audience-binding",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "intended_audience_sha256": [H1, H1],
        "observed_disposition": "accepted",
    }


def delegation_issuer_binding():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "binding_id": "two-hop-delegation-issuer-binding",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "issuer_principal_id_sha256": [H1, H1],
        "observed_disposition": "accepted",
    }


def delegation_identity_binding():
    issuer = delegation_issuer_binding()
    audience = delegation_audience_binding()
    return {
        "schema_version": 1,
        "binding_id": "two-hop-delegation-identity-binding",
        "issuer_binding": issuer,
        "issuer_binding_evidence_id": evaluate_recorded_delegation_issuer_binding(
            issuer
        )["evidence_id"],
        "audience_binding": audience,
        "audience_binding_evidence_id": (
            evaluate_recorded_delegation_audience_binding(audience)["evidence_id"]
        ),
        "observed_disposition": "accepted",
    }


def delegation_resource_binding():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "binding_id": "two-hop-delegation-resource-binding",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "resource_id_sha256": [H5, H5],
        "observed_disposition": "accepted",
    }


def delegation_action_scope_binding():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "binding_id": "recorded-action-scope-binding",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "action_scopes": [["records.read"], ["records.read"]],
        "observed_disposition": "accepted",
    }


def delegation_action_target_binding():
    chain = delegation_chain()
    return {
        "schema_version": 1,
        "binding_id": "recorded-action-target-binding",
        "delegation_chain": chain,
        "delegation_chain_evidence_id": evaluate_recorded_delegation_chain(
            chain
        )["evidence_id"],
        "action_target_ids": [
            "recorded-search-results",
            "recorded-search-results",
        ],
        "observed_disposition": "accepted",
    }


def delegation_action_coherence():
    scope_binding = delegation_action_scope_binding()
    target_binding = delegation_action_target_binding()
    return {
        "schema_version": 1,
        "binding_id": "recorded-action-coherence",
        "action_scope_binding": scope_binding,
        "action_scope_binding_evidence_id": (
            evaluate_recorded_delegation_action_scope_binding(scope_binding)[
                "evidence_id"
            ]
        ),
        "action_target_binding": target_binding,
        "action_target_binding_evidence_id": (
            evaluate_recorded_delegation_action_target_binding(target_binding)[
                "evidence_id"
            ]
        ),
        "observed_disposition": "accepted",
    }


def delegation_action_tuple_binding():
    coherence = delegation_action_coherence()
    return {
        "schema_version": 1,
        "binding_id": "recorded-action-tuple-binding",
        "action_coherence": coherence,
        "action_coherence_evidence_id": (
            evaluate_recorded_delegation_action_coherence(coherence)["evidence_id"]
        ),
        "action_tuples": [
            {
                "hop_id": "delegation-hop-one",
                "action_scopes": ["records.read"],
                "action_target_id": "recorded-search-results",
            },
            {
                "hop_id": "delegation-hop-two",
                "action_scopes": ["records.read"],
                "action_target_id": "recorded-search-results",
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


def test_trusted_least_privilege_sink_passes_deterministically():
    first = evaluate_recorded_sensitive_sink_boundary(sensitive_sink())
    assert first == evaluate_recorded_sensitive_sink_boundary(
        copy.deepcopy(sensitive_sink())
    )
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["required_scope"] == "records.read"
    assert first["authority"] == SENSITIVE_SINK_AUTHORITY


def test_untrusted_influence_cannot_be_laundered_at_sensitive_sink():
    source = sensitive_sink()
    first = source["influence_lineage"]["hops"][0]["instruction_provenance"]
    first["instruction_source_boundary"] = "untrusted_content"
    first["observed_disposition"] = "rejected"
    source["influence_lineage"]["hops"][0][
        "instruction_provenance_evidence_id"
    ] = evaluate_recorded_instruction_provenance(first)["evidence_id"]
    source["influence_lineage"]["observed_disposition"] = "rejected"
    source["influence_lineage_evidence_id"] = evaluate_recorded_influence_lineage(
        source["influence_lineage"]
    )["evidence_id"]
    source["observed_disposition"] = "rejected"

    report = evaluate_recorded_sensitive_sink_boundary(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "lineage_requires_rejection",
        "untrusted_influence_reaches_sink",
    ]


def test_recorded_injection_reaches_and_rejects_sensitive_sink():
    source = sensitive_sink()
    first = source["influence_lineage"]["hops"][0]["instruction_provenance"]
    first["security_probe"].update(
        injection_detected=True, observed_decision="denied"
    )
    first["security_probe_evidence_id"] = evaluate_recorded_security_probe(
        first["security_probe"]
    )["evidence_id"]
    first["observed_disposition"] = "rejected"
    source["influence_lineage"]["hops"][0][
        "instruction_provenance_evidence_id"
    ] = evaluate_recorded_instruction_provenance(first)["evidence_id"]
    source["influence_lineage"]["observed_disposition"] = "rejected"
    source["influence_lineage_evidence_id"] = evaluate_recorded_influence_lineage(
        source["influence_lineage"]
    )["evidence_id"]
    source["observed_disposition"] = "rejected"

    report = evaluate_recorded_sensitive_sink_boundary(source)
    assert report["passed"] is True
    assert "untrusted_influence_reaches_sink" in report["rejection_reasons"]


@pytest.mark.parametrize("sink_class", [
    "state_change", "external_effect", "privileged_control",
])
def test_sensitive_sink_requires_class_specific_terminal_scope(sink_class):
    source = sensitive_sink()
    source["sink_class"] = sink_class
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_sensitive_sink_boundary(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["missing_sensitive_sink_scope"]


def test_sensitive_sink_exposes_recorded_acceptance_bypass():
    source = sensitive_sink()
    source["sink_class"] = "privileged_control"
    report = evaluate_recorded_sensitive_sink_boundary(source)
    assert report["expected_disposition"] == "rejected"
    assert report["passed"] is False


def test_sensitive_sink_is_bound_to_recomputed_lineage_evidence():
    source = sensitive_sink()
    source["influence_lineage_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="influence_lineage_evidence_mismatch"
    ):
        evaluate_recorded_sensitive_sink_boundary(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_sensitive_sink_boundary_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_sensitive_sink_boundary_schema",
    ),
    (
        lambda value: value.update(sink_class="unknown"),
        "invalid_sensitive_sink_class",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_sensitive_sink_disposition",
    ),
])
def test_malformed_or_action_bearing_sensitive_sink_fails_closed(change, code):
    source = sensitive_sink()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_sensitive_sink_boundary(source)


def test_sensitive_sink_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_sensitive_sink_boundary(sensitive_sink()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential", "url"
    ):
        assert forbidden not in rendered


def test_sensitive_sink_binding_passes_deterministically():
    first = evaluate_recorded_sensitive_sink_binding(sensitive_sink_binding())
    assert first == evaluate_recorded_sensitive_sink_binding(
        copy.deepcopy(sensitive_sink_binding())
    )
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == SENSITIVE_SINK_BINDING_AUTHORITY


@pytest.mark.parametrize("field,value,reason", [
    ("sink_input_sha256", H0, "sink_input_lineage_mismatch"),
    ("authorized_tool_id", "substitute-tool", "confused_deputy_tool_substitution"),
])
def test_sensitive_sink_binding_rejects_input_or_tool_substitution(
    field, value, reason
):
    source = sensitive_sink_binding()
    source[field] = value
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_sensitive_sink_binding(source)
    assert report["passed"] is True
    assert report["expected_disposition"] == "rejected"
    assert report["rejection_reasons"] == [reason]


def test_sensitive_sink_binding_exposes_recorded_acceptance_bypass():
    source = sensitive_sink_binding()
    source["authorized_tool_id"] = "substitute-tool"
    report = evaluate_recorded_sensitive_sink_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_sensitive_sink_binding_is_bound_to_recomputed_boundary_evidence():
    source = sensitive_sink_binding()
    source["sensitive_sink_evidence_id"] = H0
    with pytest.raises(SecurityProbeError, match="sensitive_sink_evidence_mismatch"):
        evaluate_recorded_sensitive_sink_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_sensitive_sink_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_sensitive_sink_binding_schema",
    ),
    (
        lambda value: value.update(sink_input_sha256="raw-input"),
        "invalid_sink_input_hash",
    ),
    (
        lambda value: value.update(authorized_tool_id="invoke tool"),
        "invalid_authorized_tool_id",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_sensitive_sink_binding_disposition",
    ),
])
def test_malformed_or_action_bearing_sensitive_sink_binding_fails_closed(
    change, code
):
    source = sensitive_sink_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_sensitive_sink_binding(source)


def test_sensitive_sink_binding_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_sensitive_sink_binding(sensitive_sink_binding()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential", "url"
    ):
        assert forbidden not in rendered


def test_scope_attenuation_passes_deterministically():
    first = evaluate_recorded_scope_attenuation(scope_attenuation())
    assert first == evaluate_recorded_scope_attenuation(
        copy.deepcopy(scope_attenuation())
    )
    assert first["passed"] is True
    assert first["amplified_scopes"] == []
    assert first["authority"] == SCOPE_ATTENUATION_AUTHORITY


def test_scope_attenuation_accepts_strict_narrowing():
    source = scope_attenuation()
    source["delegated_scopes"] = []
    report = evaluate_recorded_scope_attenuation(source)
    assert report["passed"] is True
    assert report["expected_disposition"] == "accepted"


@pytest.mark.parametrize("field,value,reason", [
    ("delegated_tenant_sha256", H2, "cross_tenant_delegation"),
    ("delegated_principal_id_sha256", H2, "delegated_principal_substitution"),
    ("delegated_tool_id", "substitute-tool", "delegated_tool_substitution"),
])
def test_scope_attenuation_rejects_identity_substitution(field, value, reason):
    source = scope_attenuation()
    source[field] = value
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_scope_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [reason]


def test_scope_attenuation_rejects_scope_amplification():
    source = scope_attenuation()
    source["delegated_scopes"] = ["records.read", "records.write"]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_scope_attenuation(source)
    assert report["passed"] is True
    assert report["amplified_scopes"] == ["records.write"]
    assert report["rejection_reasons"] == ["delegated_scope_amplification"]


def test_scope_attenuation_exposes_recorded_acceptance_bypass():
    source = scope_attenuation()
    source["delegated_scopes"] = ["admin.execute", "records.read"]
    report = evaluate_recorded_scope_attenuation(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_scope_attenuation_recomputes_binding_evidence():
    source = scope_attenuation()
    source["sensitive_sink_binding_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="sensitive_sink_binding_evidence_mismatch"
    ):
        evaluate_recorded_scope_attenuation(source)


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_scope_attenuation_shape"),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_scope_attenuation_schema",
    ),
    (
        lambda value: value.update(delegated_scopes=["records.read"] * 2),
        "duplicate_permission_scope",
    ),
    (
        lambda value: value.update(delegated_tool_id="invoke tool"),
        "invalid_delegated_tool_id",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_scope_attenuation_disposition",
    ),
])
def test_malformed_or_action_bearing_scope_attenuation_fails_closed(change, code):
    source = scope_attenuation()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_scope_attenuation(source)


def test_scope_attenuation_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_scope_attenuation(scope_attenuation()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential", "url"
    ):
        assert forbidden not in rendered


def test_delegation_validity_passes_deterministically():
    first = evaluate_recorded_delegation_validity(delegation_validity())
    assert first == evaluate_recorded_delegation_validity(
        copy.deepcopy(delegation_validity())
    )
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_VALIDITY_AUTHORITY
    assert first["coverage"]["wall_clock_accessed"] is False


@pytest.mark.parametrize("field,value,reason", [
    ("observed_at_tick", 99, "delegation_not_yet_valid"),
    ("observed_at_tick", 200, "delegation_expired"),
    ("observed_at_tick", 201, "delegation_expired"),
    ("revoked", True, "delegation_revoked"),
])
def test_delegation_validity_rejects_outside_window_or_revoked(
    field, value, reason
):
    source = delegation_validity()
    source[field] = value
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_validity(source)
    assert report["passed"] is True
    assert report["expected_disposition"] == "rejected"
    assert report["rejection_reasons"] == [reason]


def test_delegation_validity_exposes_recorded_acceptance_bypass():
    source = delegation_validity()
    source["revoked"] = True
    report = evaluate_recorded_delegation_validity(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_validity_propagates_scope_attenuation_rejection():
    source = delegation_validity()
    attenuation = source["scope_attenuation"]
    attenuation["delegated_scopes"] = ["records.read", "records.write"]
    attenuation["observed_disposition"] = "rejected"
    source["scope_attenuation_evidence_id"] = evaluate_recorded_scope_attenuation(
        attenuation
    )["evidence_id"]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_validity(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "scope_attenuation_requires_rejection"
    ]


def test_delegation_validity_recomputes_attenuation_evidence():
    source = delegation_validity()
    source["scope_attenuation_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="scope_attenuation_evidence_mismatch"
    ):
        evaluate_recorded_delegation_validity(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_validity_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_validity_schema",
    ),
    (
        lambda value: value.update(issued_at_tick=True),
        "invalid_delegation_issued_tick",
    ),
    (
        lambda value: value.update(expires_at_tick=1_000_000_001),
        "invalid_delegation_expiry_tick",
    ),
    (
        lambda value: value.update(observed_at_tick=-1),
        "invalid_delegation_observed_tick",
    ),
    (
        lambda value: value.update(issued_at_tick=200),
        "invalid_delegation_validity_window",
    ),
    (
        lambda value: value.update(revoked=0),
        "invalid_delegation_revoked_flag",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_delegation_validity_disposition",
    ),
])
def test_malformed_or_action_bearing_delegation_validity_fails_closed(
    change, code
):
    source = delegation_validity()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_validity(source)


def test_delegation_validity_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_validity(delegation_validity()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential",
        "url", "timestamp", "datetime",
    ):
        assert forbidden not in rendered


def test_delegation_chain_passes_deterministically():
    first = evaluate_recorded_delegation_chain(delegation_chain())
    assert first == evaluate_recorded_delegation_chain(
        copy.deepcopy(delegation_chain())
    )
    assert first["passed"] is True
    assert first["hop_count"] == 2
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_CHAIN_AUTHORITY


@pytest.mark.parametrize("field,value,reason", [
    ("tenant_id_sha256", H2, "delegation_chain_tenant_discontinuity"),
    ("principal_id_sha256", H2, "delegation_chain_principal_discontinuity"),
    ("tool_id", "substitute-tool", "delegation_chain_tool_discontinuity"),
])
def test_delegation_chain_rejects_identity_discontinuity(field, value, reason):
    source = delegation_chain()
    validity = source["hops"][1]["delegation_validity"]
    terminal_probe = validity["scope_attenuation"]["sensitive_sink_binding"][
        "sensitive_sink_boundary"
    ]["influence_lineage"]["hops"][-1]["instruction_provenance"][
        "security_probe"
    ]
    terminal_probe[field] = value
    if field == "tenant_id_sha256":
        terminal_probe["authorization_tenant_sha256"] = value
    attenuation = validity["scope_attenuation"]
    delegated_field = {
        "tenant_id_sha256": "delegated_tenant_sha256",
        "principal_id_sha256": "delegated_principal_id_sha256",
        "tool_id": "delegated_tool_id",
    }[field]
    attenuation[delegated_field] = value
    if field == "tool_id":
        attenuation["sensitive_sink_binding"]["authorized_tool_id"] = value
    refresh_validity_evidence(validity)
    source["hops"][1]["delegation_validity_evidence_id"] = (
        evaluate_recorded_delegation_validity(validity)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_chain(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [reason]


def test_delegation_chain_rejects_scope_discontinuity():
    source = delegation_chain()
    validity = source["hops"][0]["delegation_validity"]
    validity["scope_attenuation"]["delegated_scopes"] = []
    refresh_validity_evidence(validity)
    source["hops"][0]["delegation_validity_evidence_id"] = (
        evaluate_recorded_delegation_validity(validity)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_chain(source)
    assert report["rejection_reasons"] == [
        "delegation_chain_scope_discontinuity"
    ]


def test_delegation_chain_propagates_rejected_hop():
    source = delegation_chain()
    validity = source["hops"][1]["delegation_validity"]
    validity["revoked"] = True
    validity["observed_disposition"] = "rejected"
    source["hops"][1]["delegation_validity_evidence_id"] = (
        evaluate_recorded_delegation_validity(validity)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_chain(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_hop_requires_rejection"]


def test_delegation_chain_recomputes_validity_evidence():
    source = delegation_chain()
    source["hops"][1]["delegation_validity_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_validity_evidence_mismatch"
    ):
        evaluate_recorded_delegation_chain(source)


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_delegation_chain_shape"),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_chain_schema",
    ),
    (lambda value: value.update(hops=[]), "invalid_delegation_chain_hops"),
    (
        lambda value: value["hops"][1].update(
            hop_id=value["hops"][0]["hop_id"]
        ),
        "duplicate_delegation_hop_id",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_delegation_chain_disposition",
    ),
])
def test_malformed_or_action_bearing_delegation_chain_fails_closed(change, code):
    source = delegation_chain()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_chain(source)


def test_delegation_chain_report_contains_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_chain(delegation_chain()))
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential",
        "url", "timestamp", "datetime",
    ):
        assert forbidden not in rendered


def test_delegation_time_attenuation_passes_deterministically():
    first = evaluate_recorded_delegation_time_attenuation(
        delegation_time_attenuation()
    )
    assert first == evaluate_recorded_delegation_time_attenuation(
        copy.deepcopy(delegation_time_attenuation())
    )
    assert first["passed"] is True
    assert first["hop_count"] == 2
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_TIME_ATTENUATION_AUTHORITY
    assert first["coverage"]["wall_clock_accessed"] is False


def test_delegation_time_attenuation_allows_equal_parent_boundaries():
    source = delegation_time_attenuation()
    child = source["delegation_chain"]["hops"][1]["delegation_validity"]
    child.update(issued_at_tick=100, expires_at_tick=200, observed_at_tick=150)
    refresh_chain_evidence(source)
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == []


def test_delegation_time_attenuation_rejects_issuance_regression():
    source = delegation_time_attenuation()
    child = source["delegation_chain"]["hops"][1]["delegation_validity"]
    child.update(issued_at_tick=90, observed_at_tick=150)
    refresh_chain_evidence(source)
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_chain_issuance_regression"
    ]


def test_delegation_time_attenuation_rejects_expiry_amplification():
    source = delegation_time_attenuation()
    child = source["delegation_chain"]["hops"][1]["delegation_validity"]
    child["expires_at_tick"] = 250
    refresh_chain_evidence(source)
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_chain_expiry_amplification"
    ]


def test_delegation_time_attenuation_rejects_issuance_after_parent_expiry():
    source = delegation_time_attenuation()
    child = source["delegation_chain"]["hops"][1]["delegation_validity"]
    child.update(issued_at_tick=200, expires_at_tick=210, observed_at_tick=205)
    refresh_chain_evidence(source)
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_chain_issuance_outside_parent_window",
        "delegation_chain_expiry_amplification",
    ]


def test_delegation_time_attenuation_detects_observation_mismatch():
    source = delegation_time_attenuation()
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["expected_disposition"] == "accepted"
    assert report["passed"] is False


def test_delegation_time_attenuation_propagates_chain_mismatch():
    source = delegation_time_attenuation()
    source["delegation_chain"]["observed_disposition"] = "rejected"
    refresh_chain_evidence(source)
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_time_attenuation(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_chain_observation_mismatch"
    ]


def test_delegation_time_attenuation_recomputes_chain_evidence():
    source = delegation_time_attenuation()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_time_attenuation(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_time_attenuation_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_time_attenuation_schema",
    ),
    (
        lambda value: value.update(observed_disposition="maybe"),
        "invalid_delegation_time_attenuation_disposition",
    ),
])
def test_malformed_or_action_bearing_time_attenuation_fails_closed(
    change, code
):
    source = delegation_time_attenuation()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_time_attenuation(source)


def test_delegation_time_attenuation_report_has_no_raw_or_action_fields():
    rendered = repr(
        evaluate_recorded_delegation_time_attenuation(
            delegation_time_attenuation()
        )
    )
    for forbidden in (
        "prompt", "payload", "instruction_text", "command", "credential",
        "url", "timestamp", "datetime",
    ):
        assert forbidden not in rendered


def test_redelegation_depth_attenuation_passes_deterministically():
    first = evaluate_recorded_redelegation_depth_attenuation(
        redelegation_depth_attenuation()
    )
    second = evaluate_recorded_redelegation_depth_attenuation(
        copy.deepcopy(redelegation_depth_attenuation())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == REDELEGATION_DEPTH_ATTENUATION_AUTHORITY


@pytest.mark.parametrize("remaining", ([2, 2], [1, 1], [0, 0], [1, 2]))
def test_redelegation_depth_rejects_preserved_or_amplified_capacity(remaining):
    source = redelegation_depth_attenuation()
    source["remaining_delegations"] = remaining
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_redelegation_depth_attenuation(source)
    assert report["passed"] is True
    assert report["expected_disposition"] == "rejected"
    assert report["rejection_reasons"] == [
        "redelegation_depth_not_attenuated"
    ]


def test_redelegation_depth_exposes_recorded_acceptance_bypass():
    source = redelegation_depth_attenuation()
    source["remaining_delegations"] = [1, 1]
    report = evaluate_recorded_redelegation_depth_attenuation(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_redelegation_depth_propagates_chain_mismatch():
    source = redelegation_depth_attenuation()
    source["delegation_chain"]["observed_disposition"] = "rejected"
    source["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        source["delegation_chain"]
    )["evidence_id"]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_redelegation_depth_attenuation(source)
    assert report["rejection_reasons"] == [
        "delegation_chain_observation_mismatch"
    ]


def test_redelegation_depth_recomputes_chain_evidence():
    source = redelegation_depth_attenuation()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(SecurityProbeError, match="delegation_chain_evidence_mismatch"):
        evaluate_recorded_redelegation_depth_attenuation(source)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (
            lambda value: value.update(command="run"),
            "invalid_redelegation_depth_attenuation_shape",
        ),
        (
            lambda value: value.update(schema_version=2),
            "unsupported_redelegation_depth_attenuation_schema",
        ),
        (
            lambda value: value.update(remaining_delegations=[1]),
            "invalid_remaining_delegations",
        ),
        (
            lambda value: value.update(remaining_delegations=[9, 0]),
            "invalid_remaining_delegations",
        ),
        (
            lambda value: value.update(remaining_delegations=[True, 0]),
            "invalid_remaining_delegations",
        ),
        (
            lambda value: value.update(observed_disposition="authorized"),
            "invalid_redelegation_depth_attenuation_disposition",
        ),
    ],
)
def test_malformed_or_action_bearing_redelegation_depth_fails_closed(
    change, code
):
    source = redelegation_depth_attenuation()
    change(source)
    with pytest.raises(SecurityProbeError, match=f"^{code}$"):
        evaluate_recorded_redelegation_depth_attenuation(source)


def test_redelegation_depth_report_has_no_raw_or_action_fields():
    rendered = repr(
        evaluate_recorded_redelegation_depth_attenuation(
            redelegation_depth_attenuation()
        )
    )
    for forbidden in (
        "command", "prompt", "payload", "credential", "secret", "url",
        "timestamp", "datetime",
    ):
        assert forbidden not in rendered


def test_delegation_replay_guard_passes_deterministically():
    first = evaluate_recorded_delegation_replay_guard(delegation_replay_guard())
    second = evaluate_recorded_delegation_replay_guard(
        copy.deepcopy(delegation_replay_guard())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_REPLAY_GUARD_AUTHORITY


@pytest.mark.parametrize("field,reason", [
    ("validity_id", "delegation_validity_identity_replayed"),
    ("evidence", "delegation_validity_evidence_replayed"),
])
def test_delegation_replay_guard_rejects_reused_validity(field, reason):
    source = delegation_replay_guard()
    first, second = source["delegation_chain"]["hops"]
    if field == "validity_id":
        second["delegation_validity"]["validity_id"] = first[
            "delegation_validity"
        ]["validity_id"]
        second["delegation_validity_evidence_id"] = (
            evaluate_recorded_delegation_validity(second["delegation_validity"])[
                "evidence_id"
            ]
        )
    else:
        second["delegation_validity"] = copy.deepcopy(
            first["delegation_validity"]
        )
        second["delegation_validity_evidence_id"] = first[
            "delegation_validity_evidence_id"
        ]
    source["delegation_chain"]["observed_disposition"] = "accepted"
    source["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        source["delegation_chain"]
    )["evidence_id"]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_replay_guard(source)
    assert report["passed"] is True
    assert reason in report["rejection_reasons"]


def test_delegation_replay_guard_exposes_false_acceptance():
    source = delegation_replay_guard()
    first, second = source["delegation_chain"]["hops"]
    second["delegation_validity"]["validity_id"] = first[
        "delegation_validity"
    ]["validity_id"]
    second["delegation_validity_evidence_id"] = (
        evaluate_recorded_delegation_validity(second["delegation_validity"])[
            "evidence_id"
        ]
    )
    source["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        source["delegation_chain"]
    )["evidence_id"]
    report = evaluate_recorded_delegation_replay_guard(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_replay_guard_recomputes_chain_evidence():
    source = delegation_replay_guard()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(SecurityProbeError, match="delegation_chain_evidence_mismatch"):
        evaluate_recorded_delegation_replay_guard(source)


@pytest.mark.parametrize("change,code", [
    (lambda value: value.update(command="run"), "invalid_delegation_replay_guard_shape"),
    (lambda value: value.update(schema_version=True), "unsupported_delegation_replay_guard_schema"),
    (lambda value: value.update(observed_disposition="maybe"), "invalid_delegation_replay_guard_disposition"),
])
def test_malformed_or_action_bearing_delegation_replay_guard_fails_closed(
    change, code
):
    source = delegation_replay_guard()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_replay_guard(source)


def test_delegation_replay_guard_report_has_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_replay_guard(
        delegation_replay_guard()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_audience_binding_passes_deterministically():
    first = evaluate_recorded_delegation_audience_binding(
        delegation_audience_binding()
    )
    second = evaluate_recorded_delegation_audience_binding(
        copy.deepcopy(delegation_audience_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_AUDIENCE_BINDING_AUTHORITY


def test_delegation_audience_binding_rejects_recipient_substitution():
    source = delegation_audience_binding()
    source["intended_audience_sha256"][1] = H2
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_audience_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_audience_mismatch"]


def test_delegation_audience_binding_exposes_false_acceptance():
    source = delegation_audience_binding()
    source["intended_audience_sha256"][0] = H2
    report = evaluate_recorded_delegation_audience_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_audience_binding_recomputes_chain_evidence():
    source = delegation_audience_binding()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_audience_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_audience_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_audience_binding_schema",
    ),
    (
        lambda value: value.update(intended_audience_sha256=[H1]),
        "invalid_delegation_audiences",
    ),
    (
        lambda value: value.update(intended_audience_sha256=[H1, "raw-user"]),
        "invalid_delegation_audiences",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_audience_binding_disposition",
    ),
])
def test_malformed_or_action_bearing_delegation_audience_binding_fails_closed(
    change, code
):
    source = delegation_audience_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_audience_binding(source)


def test_delegation_audience_binding_report_has_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_audience_binding(
        delegation_audience_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_issuer_binding_passes_deterministically():
    first = evaluate_recorded_delegation_issuer_binding(
        delegation_issuer_binding()
    )
    second = evaluate_recorded_delegation_issuer_binding(
        copy.deepcopy(delegation_issuer_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_ISSUER_BINDING_AUTHORITY


def test_delegation_issuer_binding_rejects_issuer_substitution():
    source = delegation_issuer_binding()
    source["issuer_principal_id_sha256"][1] = H2
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_issuer_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_issuer_mismatch"]


def test_delegation_issuer_binding_exposes_false_acceptance():
    source = delegation_issuer_binding()
    source["issuer_principal_id_sha256"][0] = H2
    report = evaluate_recorded_delegation_issuer_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_issuer_binding_recomputes_chain_evidence():
    source = delegation_issuer_binding()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_issuer_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_issuer_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_issuer_binding_schema",
    ),
    (
        lambda value: value.update(issuer_principal_id_sha256=[H1]),
        "invalid_delegation_issuers",
    ),
    (
        lambda value: value.update(issuer_principal_id_sha256=[H1, "raw-user"]),
        "invalid_delegation_issuers",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_issuer_binding_disposition",
    ),
])
def test_malformed_or_action_bearing_delegation_issuer_binding_fails_closed(
    change, code
):
    source = delegation_issuer_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_issuer_binding(source)


def test_delegation_issuer_binding_report_has_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_issuer_binding(
        delegation_issuer_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_identity_binding_passes_deterministically():
    first = evaluate_recorded_delegation_identity_binding(
        delegation_identity_binding()
    )
    second = evaluate_recorded_delegation_identity_binding(
        copy.deepcopy(delegation_identity_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_IDENTITY_BINDING_AUTHORITY


def test_delegation_identity_binding_rejects_mixed_chains():
    source = delegation_identity_binding()
    audience = source["audience_binding"]
    audience["delegation_chain"]["chain_id"] = "substituted-chain"
    audience["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        audience["delegation_chain"]
    )["evidence_id"]
    source["audience_binding_evidence_id"] = (
        evaluate_recorded_delegation_audience_binding(audience)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_identity_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_identity_chain_mismatch"]
    assert report["delegation_chain_evidence_id"] is None


def test_delegation_identity_binding_exposes_false_acceptance():
    source = delegation_identity_binding()
    audience = source["audience_binding"]
    audience["delegation_chain"]["chain_id"] = "substituted-chain"
    audience["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        audience["delegation_chain"]
    )["evidence_id"]
    source["audience_binding_evidence_id"] = (
        evaluate_recorded_delegation_audience_binding(audience)["evidence_id"]
    )
    report = evaluate_recorded_delegation_identity_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


@pytest.mark.parametrize("field,code", [
    (
        "issuer_binding_evidence_id",
        "delegation_issuer_binding_evidence_mismatch",
    ),
    (
        "audience_binding_evidence_id",
        "delegation_audience_binding_evidence_mismatch",
    ),
])
def test_delegation_identity_binding_recomputes_component_evidence(field, code):
    source = delegation_identity_binding()
    source[field] = H0
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_identity_binding(source)


def test_delegation_identity_binding_requires_accepted_components():
    source = delegation_identity_binding()
    audience = source["audience_binding"]
    audience["intended_audience_sha256"][0] = H2
    audience["observed_disposition"] = "rejected"
    source["audience_binding_evidence_id"] = (
        evaluate_recorded_delegation_audience_binding(audience)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_identity_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_audience_requires_rejection"
    ]


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_identity_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_identity_binding_schema",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_identity_binding_disposition",
    ),
    (
        lambda value: value.update(binding_id="raw user"),
        "invalid_delegation_identity_binding_id",
    ),
])
def test_malformed_or_action_bearing_delegation_identity_binding_fails_closed(
    change, code
):
    source = delegation_identity_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_identity_binding(source)


def test_delegation_identity_binding_report_has_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_identity_binding(
        delegation_identity_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_resource_binding_passes_deterministically():
    first = evaluate_recorded_delegation_resource_binding(
        delegation_resource_binding()
    )
    second = evaluate_recorded_delegation_resource_binding(
        copy.deepcopy(delegation_resource_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_RESOURCE_BINDING_AUTHORITY
    assert first["coverage"]["live_resource_access_checked"] is False


def test_delegation_resource_binding_rejects_resource_substitution():
    source = delegation_resource_binding()
    source["resource_id_sha256"][1] = H4
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_resource_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_resource_mismatch"]


def test_delegation_resource_binding_exposes_false_acceptance():
    source = delegation_resource_binding()
    source["resource_id_sha256"][0] = H4
    report = evaluate_recorded_delegation_resource_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_resource_binding_recomputes_chain_evidence():
    source = delegation_resource_binding()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_resource_binding(source)


def test_delegation_resource_binding_recomputes_nested_sink_evidence():
    source = delegation_resource_binding()
    sink = source["delegation_chain"]["hops"][0]["delegation_validity"][
        "scope_attenuation"
    ]["sensitive_sink_binding"]
    sink["sink_input_sha256"] = H4
    with pytest.raises(
        SecurityProbeError, match="sensitive_sink_binding_evidence_mismatch"
    ):
        evaluate_recorded_delegation_resource_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_resource_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_resource_binding_schema",
    ),
    (
        lambda value: value.update(resource_id_sha256=[H5]),
        "invalid_delegation_resources",
    ),
    (
        lambda value: value.update(resource_id_sha256=[H5, "raw-resource"]),
        "invalid_delegation_resources",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_resource_binding_disposition",
    ),
])
def test_malformed_or_action_bearing_delegation_resource_binding_fails_closed(
    change, code
):
    source = delegation_resource_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_resource_binding(source)


def test_delegation_resource_binding_report_has_no_raw_or_action_fields():
    rendered = repr(evaluate_recorded_delegation_resource_binding(
        delegation_resource_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_action_scope_binding_passes_deterministically():
    first = evaluate_recorded_delegation_action_scope_binding(
        delegation_action_scope_binding()
    )
    second = evaluate_recorded_delegation_action_scope_binding(
        copy.deepcopy(delegation_action_scope_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_ACTION_SCOPE_BINDING_AUTHORITY
    assert first["coverage"]["live_action_or_authorization_checked"] is False


def test_delegation_action_scope_binding_rejects_scope_substitution():
    source = delegation_action_scope_binding()
    source["action_scopes"][1] = ["records.write"]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_action_scope_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_action_scope_mismatch"]


def test_delegation_action_scope_binding_exposes_false_acceptance():
    source = delegation_action_scope_binding()
    source["action_scopes"][0] = []
    report = evaluate_recorded_delegation_action_scope_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_action_scope_binding_recomputes_chain_evidence():
    source = delegation_action_scope_binding()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_action_scope_binding(source)


def test_delegation_action_scope_binding_recomputes_nested_evidence():
    source = delegation_action_scope_binding()
    source["delegation_chain"]["hops"][0]["delegation_validity"][
        "scope_attenuation"
    ]["delegated_scopes"] = []
    with pytest.raises(
        SecurityProbeError, match="scope_attenuation_evidence_mismatch"
    ):
        evaluate_recorded_delegation_action_scope_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_action_scope_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_action_scope_binding_schema",
    ),
    (
        lambda value: value.update(action_scopes=[["records.read"]]),
        "invalid_delegation_action_scopes",
    ),
    (
        lambda value: value.update(
            action_scopes=[["records.read"], ["raw action"]]
        ),
        "invalid_permission_scope",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_action_scope_binding_disposition",
    ),
])
def test_malformed_delegation_action_scope_binding_fails_closed(change, code):
    source = delegation_action_scope_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_action_scope_binding(source)


def test_delegation_action_scope_binding_report_has_no_raw_action_fields():
    rendered = repr(evaluate_recorded_delegation_action_scope_binding(
        delegation_action_scope_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_action_target_binding_passes_deterministically():
    first = evaluate_recorded_delegation_action_target_binding(
        delegation_action_target_binding()
    )
    second = evaluate_recorded_delegation_action_target_binding(
        copy.deepcopy(delegation_action_target_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_ACTION_TARGET_BINDING_AUTHORITY
    assert first["coverage"]["live_action_or_target_access_checked"] is False


def test_delegation_action_target_binding_rejects_target_substitution():
    source = delegation_action_target_binding()
    source["action_target_ids"][1] = "substitute-results"
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_action_target_binding(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_action_target_mismatch"]


def test_delegation_action_target_binding_exposes_false_acceptance():
    source = delegation_action_target_binding()
    source["action_target_ids"][0] = "substitute-results"
    report = evaluate_recorded_delegation_action_target_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_action_target_binding_recomputes_chain_evidence():
    source = delegation_action_target_binding()
    source["delegation_chain_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_chain_evidence_mismatch"
    ):
        evaluate_recorded_delegation_action_target_binding(source)


def test_delegation_action_target_binding_recomputes_nested_sink_evidence():
    source = delegation_action_target_binding()
    sink = source["delegation_chain"]["hops"][0]["delegation_validity"][
        "scope_attenuation"
    ]["sensitive_sink_binding"]["sensitive_sink_boundary"]
    sink["sink_id"] = "substitute-results"
    with pytest.raises(
        SecurityProbeError, match="sensitive_sink_evidence_mismatch"
    ):
        evaluate_recorded_delegation_action_target_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_action_target_binding_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_action_target_binding_schema",
    ),
    (
        lambda value: value.update(action_target_ids=["recorded-search-results"]),
        "invalid_delegation_action_targets",
    ),
    (
        lambda value: value.update(
            action_target_ids=["recorded-search-results", "raw target"]
        ),
        "invalid_delegation_action_target_id",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_action_target_binding_disposition",
    ),
])
def test_malformed_delegation_action_target_binding_fails_closed(change, code):
    source = delegation_action_target_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_action_target_binding(source)


def test_delegation_action_target_binding_report_has_no_raw_action_fields():
    rendered = repr(evaluate_recorded_delegation_action_target_binding(
        delegation_action_target_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_action_coherence_passes_deterministically():
    first = evaluate_recorded_delegation_action_coherence(
        delegation_action_coherence()
    )
    second = evaluate_recorded_delegation_action_coherence(
        copy.deepcopy(delegation_action_coherence())
    )
    assert first == second
    assert first["passed"] is True
    assert first["expected_disposition"] == "accepted"
    assert first["rejection_reasons"] == []
    assert first["authority"] == DELEGATION_ACTION_COHERENCE_AUTHORITY
    assert first["coverage"]["live_action_or_authorization_checked"] is False


def test_delegation_action_coherence_rejects_mixed_chains():
    source = delegation_action_coherence()
    target = source["action_target_binding"]
    target["delegation_chain"]["chain_id"] = "substituted-chain"
    target["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        target["delegation_chain"]
    )["evidence_id"]
    source["action_target_binding_evidence_id"] = (
        evaluate_recorded_delegation_action_target_binding(target)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_action_coherence(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == ["delegation_action_chain_mismatch"]
    assert report["delegation_chain_evidence_id"] is None


def test_delegation_action_coherence_exposes_false_acceptance():
    source = delegation_action_coherence()
    target = source["action_target_binding"]
    target["delegation_chain"]["chain_id"] = "substituted-chain"
    target["delegation_chain_evidence_id"] = evaluate_recorded_delegation_chain(
        target["delegation_chain"]
    )["evidence_id"]
    source["action_target_binding_evidence_id"] = (
        evaluate_recorded_delegation_action_target_binding(target)["evidence_id"]
    )
    report = evaluate_recorded_delegation_action_coherence(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


@pytest.mark.parametrize("field,code", [
    (
        "action_scope_binding_evidence_id",
        "delegation_action_scope_binding_evidence_mismatch",
    ),
    (
        "action_target_binding_evidence_id",
        "delegation_action_target_binding_evidence_mismatch",
    ),
])
def test_delegation_action_coherence_recomputes_component_evidence(field, code):
    source = delegation_action_coherence()
    source[field] = H0
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_action_coherence(source)


def test_delegation_action_coherence_requires_accepted_components():
    source = delegation_action_coherence()
    target = source["action_target_binding"]
    target["action_target_ids"][0] = "substitute-results"
    target["observed_disposition"] = "rejected"
    source["action_target_binding_evidence_id"] = (
        evaluate_recorded_delegation_action_target_binding(target)["evidence_id"]
    )
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_action_coherence(source)
    assert report["passed"] is True
    assert report["rejection_reasons"] == [
        "delegation_action_target_requires_rejection"
    ]


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_action_coherence_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_action_coherence_schema",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_action_coherence_disposition",
    ),
    (
        lambda value: value.update(binding_id="raw action"),
        "invalid_delegation_action_coherence_id",
    ),
])
def test_malformed_delegation_action_coherence_fails_closed(change, code):
    source = delegation_action_coherence()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_action_coherence(source)


def test_delegation_action_coherence_report_has_no_raw_action_fields():
    rendered = repr(evaluate_recorded_delegation_action_coherence(
        delegation_action_coherence()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered


def test_delegation_action_tuple_binding_passes_deterministically():
    first = evaluate_recorded_delegation_action_tuple_binding(
        delegation_action_tuple_binding()
    )
    second = evaluate_recorded_delegation_action_tuple_binding(
        copy.deepcopy(delegation_action_tuple_binding())
    )
    assert first == second
    assert first["passed"] is True
    assert first["hop_count"] == 2
    assert first["authority"] == DELEGATION_ACTION_TUPLE_AUTHORITY
    assert len(first["action_tuple_commitments"]) == 2


@pytest.mark.parametrize("field,reason", [
    ("hop_id", "delegation_action_tuple_hop_mismatch"),
    ("action_scopes", "delegation_action_tuple_scope_mismatch"),
    ("action_target_id", "delegation_action_tuple_target_mismatch"),
])
def test_delegation_action_tuple_binding_rejects_substitution(field, reason):
    source = delegation_action_tuple_binding()
    replacements = {
        "hop_id": "substituted-hop",
        "action_scopes": ["records.write"],
        "action_target_id": "substituted-results",
    }
    source["action_tuples"][0][field] = replacements[field]
    source["observed_disposition"] = "rejected"
    report = evaluate_recorded_delegation_action_tuple_binding(source)
    assert report["passed"] is True
    assert reason in report["rejection_reasons"]
    assert report["delegation_chain_evidence_id"] is None


def test_delegation_action_tuple_binding_exposes_false_acceptance():
    source = delegation_action_tuple_binding()
    source["action_tuples"][0]["action_target_id"] = "substituted-results"
    report = evaluate_recorded_delegation_action_tuple_binding(source)
    assert report["passed"] is False
    assert report["expected_disposition"] == "rejected"


def test_delegation_action_tuple_binding_recomputes_coherence_evidence():
    source = delegation_action_tuple_binding()
    source["action_coherence_evidence_id"] = H0
    with pytest.raises(
        SecurityProbeError, match="delegation_action_coherence_evidence_mismatch"
    ):
        evaluate_recorded_delegation_action_tuple_binding(source)


@pytest.mark.parametrize("change,code", [
    (
        lambda value: value.update(command="run"),
        "invalid_delegation_action_tuple_shape",
    ),
    (
        lambda value: value.update(schema_version=True),
        "unsupported_delegation_action_tuple_schema",
    ),
    (
        lambda value: value.update(action_tuples=[]),
        "invalid_delegation_action_tuples",
    ),
    (
        lambda value: value["action_tuples"][0].update(payload="raw"),
        "invalid_delegation_action_tuple",
    ),
    (
        lambda value: value.update(observed_disposition="authorized"),
        "invalid_delegation_action_tuple_disposition",
    ),
])
def test_malformed_delegation_action_tuple_binding_fails_closed(change, code):
    source = delegation_action_tuple_binding()
    change(source)
    with pytest.raises(SecurityProbeError, match=code):
        evaluate_recorded_delegation_action_tuple_binding(source)


def test_delegation_action_tuple_report_has_no_raw_action_fields():
    rendered = repr(evaluate_recorded_delegation_action_tuple_binding(
        delegation_action_tuple_binding()
    ))
    for forbidden in ("payload", "url", "endpoint", "command", "credential"):
        assert forbidden not in rendered
