import copy

import pytest

from agentflight.concurrency_scenarios import (
    AUTHORITY,
    ConcurrencyScenarioError,
    evaluate_recorded_concurrent_scenario,
)


H0 = "0" * 64
H1 = "1" * 64
H2 = "2" * 64
H3 = "3" * 64
H4 = "4" * 64
H5 = "5" * 64


def scenario():
    return {
        "schema_version": 1,
        "scenario_id": "two-agent-conflict",
        "tenant_id_sha256": H0,
        "schedule_seed_sha256": H1,
        "participant_limit": 4,
        "event_limit": 8,
        "participants": [
            {
                "participant_id": "agent-b",
                "adapter_evidence_id": H3,
                "tenant_id_sha256": H0,
            },
            {
                "participant_id": "agent-a",
                "adapter_evidence_id": H2,
                "tenant_id_sha256": H0,
            },
        ],
        "events": [
            {
                "sequence": 1,
                "logical_time": 10,
                "participant_id": "agent-a",
                "prior_participant_event_id": None,
                "resource_key_sha256": H4,
                "state_before_sha256": H0,
                "state_after_sha256": H1,
                "outcome_code": "completed",
            },
            {
                "sequence": 2,
                "logical_time": 10,
                "participant_id": "agent-b",
                "prior_participant_event_id": None,
                "resource_key_sha256": H4,
                "state_before_sha256": H0,
                "state_after_sha256": H0,
                "outcome_code": "conflict_rejected",
            },
        ],
    }


def test_recorded_concurrent_scenario_is_deterministic_and_bounded():
    source = scenario()
    first = evaluate_recorded_concurrent_scenario(source)
    second = evaluate_recorded_concurrent_scenario(copy.deepcopy(source))
    assert first == second
    assert [p["participant_id"] for p in first["participants"]] == [
        "agent-a", "agent-b"
    ]
    assert first["coverage"] == {
        "participant_count": 2,
        "recorded_event_count": 2,
        "conflict_rejections": 1,
        "single_tenant_hash_verified": True,
        "scope": "bounded_recorded_deterministic_schedule_metadata_only",
    }
    assert first["schedule_rule"] == "logical_time_then_participant_id"
    assert first["authority"] == AUTHORITY


def test_rejects_cross_tenant_participant():
    source = scenario()
    source["participants"][0]["tenant_id_sha256"] = H5
    with pytest.raises(ConcurrencyScenarioError, match="cross_tenant_participant"):
        evaluate_recorded_concurrent_scenario(source)


def test_rejects_duplicate_or_unregistered_participants():
    source = scenario()
    source["participants"][0]["participant_id"] = "agent-a"
    with pytest.raises(ConcurrencyScenarioError, match="duplicate_participant_id"):
        evaluate_recorded_concurrent_scenario(source)

    source = scenario()
    source["events"][1]["participant_id"] = "agent-c"
    with pytest.raises(ConcurrencyScenarioError, match="unregistered_participant"):
        evaluate_recorded_concurrent_scenario(source)


def test_rejects_nondeterministic_tie_order():
    source = scenario()
    source["events"].reverse()
    source["events"][0]["sequence"] = 1
    source["events"][1]["sequence"] = 2
    with pytest.raises(ConcurrencyScenarioError, match="nondeterministic_schedule_order"):
        evaluate_recorded_concurrent_scenario(source)


def test_rejects_wrong_conflict_winner_or_mutating_rejection():
    source = scenario()
    source["events"][0]["outcome_code"] = "conflict_rejected"
    source["events"][0]["state_after_sha256"] = H0
    source["events"][1]["outcome_code"] = "completed"
    with pytest.raises(
        ConcurrencyScenarioError, match="invalid_deterministic_conflict_resolution"
    ):
        evaluate_recorded_concurrent_scenario(source)

    source = scenario()
    source["events"][1]["state_after_sha256"] = H2
    with pytest.raises(ConcurrencyScenarioError, match="rejected_conflict_mutated_state"):
        evaluate_recorded_concurrent_scenario(source)


def test_participant_event_chain_is_content_addressed():
    source = scenario()
    first = evaluate_recorded_concurrent_scenario(source)
    chained = copy.deepcopy(source["events"][0])
    chained.update({
        "sequence": 3,
        "logical_time": 11,
        "prior_participant_event_id": first["events"][0]["event_id"],
        "resource_key_sha256": H5,
        "state_before_sha256": H1,
        "state_after_sha256": H2,
    })
    source["events"].append(chained)
    report = evaluate_recorded_concurrent_scenario(source)
    assert report["events"][2]["prior_participant_event_id"] == report["events"][0]["event_id"]

    source["events"][2]["prior_participant_event_id"] = H5
    with pytest.raises(ConcurrencyScenarioError, match="participant_event_chain_mismatch"):
        evaluate_recorded_concurrent_scenario(source)


@pytest.mark.parametrize(
    "change,code",
    [
        (lambda value: value.update(command="run"), "invalid_concurrent_scenario_shape"),
        (lambda value: value.update(participant_limit=True), "invalid_participant_limit"),
        (lambda value: value.update(event_limit=65), "invalid_event_limit"),
        (lambda value: value.update(events=[]), "invalid_concurrent_event_count"),
    ],
)
def test_rejects_action_fields_boolean_and_bounds(change, code):
    source = scenario()
    change(source)
    with pytest.raises(ConcurrencyScenarioError, match=code):
        evaluate_recorded_concurrent_scenario(source)


def test_report_contains_no_external_target_payload_or_raw_tenant_fields():
    rendered = repr(evaluate_recorded_concurrent_scenario(scenario()))
    for forbidden in ("url", "endpoint", "payload", "credential", "command", "path"):
        assert forbidden not in rendered
    assert "tenant_id_sha256" in rendered
