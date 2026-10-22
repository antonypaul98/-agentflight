"""Deterministic validation of bounded recorded concurrent scenarios.

This module validates caller-supplied metadata only. It does not start threads,
processes, agents, tools, projects, network calls, or other executable work.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
MAX_PARTICIPANTS = 8
MAX_EVENTS = 64
MAX_HANDOFFS = 32
MAX_SYNCHRONIZATIONS = 16
MAX_RESOURCE_KEYS = 32
MAX_REPORT_BYTES = 32_768
AUTHORITY = "recorded_concurrency_evidence_only_no_execution"
RESOURCE_LINEAGE_AUTHORITY = (
    "recorded_resource_state_lineage_only_no_execution_or_state_access"
)
CAUSAL_HANDOFF_AUTHORITY = (
    "recorded_cross_agent_causal_handoffs_only_no_execution_or_data_access"
)
QUORUM_BARRIER_AUTHORITY = (
    "recorded_quorum_barrier_evidence_only_no_execution_waiting_or_scheduling"
)
CAPACITY_BUDGET_AUTHORITY = (
    "recorded_capacity_budget_evidence_only_no_resource_enforcement"
)

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_OUTCOMES = frozenset({"completed", "conflict_rejected"})


class ConcurrencyScenarioError(ValueError):
    """The supplied scenario is outside the bounded recorded-only contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _exact_dict(value: object, keys: frozenset[str], code: str) -> dict:
    if type(value) is not dict or frozenset(value) != keys:
        raise ConcurrencyScenarioError(code)
    return value


def _text(value: object, pattern: re.Pattern[str], code: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise ConcurrencyScenarioError(code)
    return value


def evaluate_recorded_concurrent_scenario(scenario: Mapping[str, object]) -> dict:
    """Verify one deterministic recorded schedule without executing it."""

    root = _exact_dict(
        scenario,
        frozenset({
            "schema_version", "scenario_id", "tenant_id_sha256",
            "schedule_seed_sha256", "participant_limit", "event_limit",
            "participants", "events",
        }),
        "invalid_concurrent_scenario_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ConcurrencyScenarioError("unsupported_concurrent_scenario_schema")
    scenario_id = _text(root["scenario_id"], _IDENTIFIER, "invalid_scenario_id")
    tenant_id = _text(root["tenant_id_sha256"], _SHA256, "invalid_tenant_hash")
    schedule_seed = _text(
        root["schedule_seed_sha256"], _SHA256, "invalid_schedule_seed_hash"
    )
    participant_limit = root["participant_limit"]
    event_limit = root["event_limit"]
    if (
        type(participant_limit) is not int
        or not 2 <= participant_limit <= MAX_PARTICIPANTS
    ):
        raise ConcurrencyScenarioError("invalid_participant_limit")
    if type(event_limit) is not int or not 1 <= event_limit <= MAX_EVENTS:
        raise ConcurrencyScenarioError("invalid_event_limit")

    participants = root["participants"]
    if (
        type(participants) is not list
        or not 2 <= len(participants) <= participant_limit
    ):
        raise ConcurrencyScenarioError("invalid_participant_count")
    participant_keys = frozenset({
        "participant_id", "adapter_evidence_id", "tenant_id_sha256"
    })
    normalized_participants = []
    participant_ids = set()
    for value in participants:
        participant = _exact_dict(
            value, participant_keys, "invalid_participant_shape"
        )
        participant_id = _text(
            participant["participant_id"], _IDENTIFIER, "invalid_participant_id"
        )
        if participant_id in participant_ids:
            raise ConcurrencyScenarioError("duplicate_participant_id")
        participant_ids.add(participant_id)
        adapter_evidence = _text(
            participant["adapter_evidence_id"],
            _SHA256,
            "invalid_adapter_evidence_id",
        )
        participant_tenant = _text(
            participant["tenant_id_sha256"], _SHA256, "invalid_tenant_hash"
        )
        if participant_tenant != tenant_id:
            raise ConcurrencyScenarioError("cross_tenant_participant")
        normalized_participants.append({
            "participant_id": participant_id,
            "adapter_evidence_id": adapter_evidence,
            "tenant_id_sha256": participant_tenant,
        })
    normalized_participants.sort(key=lambda value: value["participant_id"])

    events = root["events"]
    if type(events) is not list or not 1 <= len(events) <= event_limit:
        raise ConcurrencyScenarioError("invalid_concurrent_event_count")
    event_keys = frozenset({
        "sequence", "logical_time", "participant_id",
        "prior_participant_event_id", "resource_key_sha256",
        "state_before_sha256", "state_after_sha256", "outcome_code",
    })
    normalized_events = []
    prior_by_participant = {}
    conflict_groups = {}
    prior_order = None
    conflict_rejections = 0
    for expected_sequence, value in enumerate(events, start=1):
        event = _exact_dict(value, event_keys, "invalid_concurrent_event_shape")
        if type(event["sequence"]) is not int or event["sequence"] != expected_sequence:
            raise ConcurrencyScenarioError("invalid_concurrent_sequence")
        logical_time = event["logical_time"]
        if type(logical_time) is not int or logical_time < 0:
            raise ConcurrencyScenarioError("invalid_logical_time")
        participant_id = _text(
            event["participant_id"], _IDENTIFIER, "invalid_participant_id"
        )
        if participant_id not in participant_ids:
            raise ConcurrencyScenarioError("unregistered_participant")
        order = (logical_time, participant_id)
        if prior_order is not None and order <= prior_order:
            raise ConcurrencyScenarioError("nondeterministic_schedule_order")
        prior_order = order

        supplied_prior = event["prior_participant_event_id"]
        expected_prior = prior_by_participant.get(participant_id)
        if supplied_prior is not None:
            supplied_prior = _text(
                supplied_prior, _SHA256, "invalid_prior_participant_event_id"
            )
        if supplied_prior != expected_prior:
            raise ConcurrencyScenarioError("participant_event_chain_mismatch")
        resource_key = _text(
            event["resource_key_sha256"], _SHA256, "invalid_resource_key_hash"
        )
        state_before = _text(
            event["state_before_sha256"], _SHA256, "invalid_state_before_hash"
        )
        state_after = _text(
            event["state_after_sha256"], _SHA256, "invalid_state_after_hash"
        )
        outcome = event["outcome_code"]
        if type(outcome) is not str or outcome not in _OUTCOMES:
            raise ConcurrencyScenarioError("invalid_concurrent_outcome")
        if outcome == "conflict_rejected":
            conflict_rejections += 1
            if state_before != state_after:
                raise ConcurrencyScenarioError("rejected_conflict_mutated_state")

        unsigned = {
            "sequence": expected_sequence,
            "logical_time": logical_time,
            "participant_id": participant_id,
            "prior_participant_event_id": supplied_prior,
            "resource_key_sha256": resource_key,
            "state_before_sha256": state_before,
            "state_after_sha256": state_after,
            "outcome_code": outcome,
        }
        event_id = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()
        normalized_events.append({"event_id": event_id, **unsigned})
        prior_by_participant[participant_id] = event_id
        conflict_groups.setdefault((logical_time, resource_key), []).append(
            (participant_id, outcome)
        )

    for group in conflict_groups.values():
        if len(group) == 1:
            continue
        winners = [participant for participant, outcome in group if outcome == "completed"]
        if winners != [min(participant for participant, _ in group)]:
            raise ConcurrencyScenarioError("invalid_deterministic_conflict_resolution")
        if any(
            outcome != ("completed" if participant == winners[0] else "conflict_rejected")
            for participant, outcome in group
        ):
            raise ConcurrencyScenarioError("invalid_deterministic_conflict_resolution")

    report = {
        "concurrency_schema_version": SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "tenant_id_sha256": tenant_id,
        "schedule_seed_sha256": schedule_seed,
        "participants": normalized_participants,
        "events": normalized_events,
        "coverage": {
            "participant_count": len(normalized_participants),
            "recorded_event_count": len(normalized_events),
            "conflict_rejections": conflict_rejections,
            "single_tenant_hash_verified": True,
            "scope": "bounded_recorded_deterministic_schedule_metadata_only",
        },
        "schedule_rule": "logical_time_then_participant_id",
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ConcurrencyScenarioError("concurrent_scenario_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def evaluate_recorded_resource_state_lineage(
    scenario: Mapping[str, object],
) -> dict:
    """Verify resource-state continuity in one recorded concurrent schedule."""

    concurrency_report = evaluate_recorded_concurrent_scenario(scenario)
    grouped = {}
    for event in concurrency_report["events"]:
        key = (event["logical_time"], event["resource_key_sha256"])
        grouped.setdefault(key, []).append(event)

    prior_state_by_resource = {}
    rounds = []
    for (logical_time, resource_key), events in sorted(grouped.items()):
        observed_before = {event["state_before_sha256"] for event in events}
        if len(observed_before) != 1:
            raise ConcurrencyScenarioError("contending_state_before_mismatch")
        state_before = observed_before.pop()
        if (
            resource_key in prior_state_by_resource
            and state_before != prior_state_by_resource[resource_key]
        ):
            raise ConcurrencyScenarioError("resource_state_chain_mismatch")

        completed = [event for event in events if event["outcome_code"] == "completed"]
        rejected = [
            event for event in events if event["outcome_code"] == "conflict_rejected"
        ]
        if len(events) == 1 and rejected:
            raise ConcurrencyScenarioError("isolated_conflict_rejection")
        if len(completed) != 1:
            raise ConcurrencyScenarioError("invalid_recorded_round_completion")

        accepted = completed[0]
        state_after = accepted["state_after_sha256"]
        prior_state_by_resource[resource_key] = state_after
        rounds.append({
            "logical_time": logical_time,
            "resource_key_sha256": resource_key,
            "state_before_sha256": state_before,
            "accepted_event_id": accepted["event_id"],
            "state_after_sha256": state_after,
            "rejected_event_ids": sorted(event["event_id"] for event in rejected),
        })

    report = {
        "resource_lineage_schema_version": SCHEMA_VERSION,
        "scenario_id": concurrency_report["scenario_id"],
        "concurrency_evidence_id": concurrency_report["evidence_id"],
        "rounds": rounds,
        "final_resource_states": [
            {
                "resource_key_sha256": resource_key,
                "state_sha256": state,
            }
            for resource_key, state in sorted(prior_state_by_resource.items())
        ],
        "coverage": {
            "recorded_round_count": len(rounds),
            "resource_count": len(prior_state_by_resource),
            "state_continuity_verified": True,
            "scope": "bounded_recorded_resource_state_lineage_metadata_only",
        },
        "authority": RESOURCE_LINEAGE_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ConcurrencyScenarioError("resource_lineage_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def evaluate_recorded_causal_handoffs(
    scenario: Mapping[str, object], handoff_record: Mapping[str, object]
) -> dict:
    """Verify bounded cross-agent causal edges without executing or transferring data."""

    concurrency_report = evaluate_recorded_concurrent_scenario(scenario)
    root = _exact_dict(
        handoff_record,
        frozenset({"schema_version", "handoff_set_id", "handoff_limit", "handoffs"}),
        "invalid_handoff_record_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ConcurrencyScenarioError("unsupported_handoff_schema")
    handoff_set_id = _text(
        root["handoff_set_id"], _IDENTIFIER, "invalid_handoff_set_id"
    )
    handoff_limit = root["handoff_limit"]
    if type(handoff_limit) is not int or not 1 <= handoff_limit <= MAX_HANDOFFS:
        raise ConcurrencyScenarioError("invalid_handoff_limit")
    handoffs = root["handoffs"]
    if type(handoffs) is not list or not 1 <= len(handoffs) <= handoff_limit:
        raise ConcurrencyScenarioError("invalid_handoff_count")

    participants = {
        participant["participant_id"] for participant in concurrency_report["participants"]
    }
    events = {event["event_id"]: event for event in concurrency_report["events"]}
    handoff_keys = frozenset({
        "sequence", "sender_participant_id", "receiver_participant_id",
        "source_event_id", "receiver_event_id", "handoff_evidence_sha256",
    })
    normalized = []
    seen_edges = set()
    prior_order = None
    senders = set()
    receivers = set()
    for expected_sequence, value in enumerate(handoffs, start=1):
        handoff = _exact_dict(value, handoff_keys, "invalid_handoff_shape")
        if type(handoff["sequence"]) is not int or handoff["sequence"] != expected_sequence:
            raise ConcurrencyScenarioError("invalid_handoff_sequence")
        sender = _text(
            handoff["sender_participant_id"], _IDENTIFIER, "invalid_participant_id"
        )
        receiver = _text(
            handoff["receiver_participant_id"], _IDENTIFIER, "invalid_participant_id"
        )
        if sender not in participants or receiver not in participants:
            raise ConcurrencyScenarioError("unregistered_handoff_participant")
        if sender == receiver:
            raise ConcurrencyScenarioError("self_handoff")
        source_event_id = _text(
            handoff["source_event_id"], _SHA256, "invalid_source_event_id"
        )
        receiver_event_id = _text(
            handoff["receiver_event_id"], _SHA256, "invalid_receiver_event_id"
        )
        if source_event_id not in events or receiver_event_id not in events:
            raise ConcurrencyScenarioError("unknown_handoff_event")
        source_event = events[source_event_id]
        receiver_event = events[receiver_event_id]
        if source_event["participant_id"] != sender:
            raise ConcurrencyScenarioError("handoff_sender_event_mismatch")
        if receiver_event["participant_id"] != receiver:
            raise ConcurrencyScenarioError("handoff_receiver_event_mismatch")
        if source_event["outcome_code"] != "completed":
            raise ConcurrencyScenarioError("handoff_source_not_completed")
        if receiver_event["outcome_code"] != "completed":
            raise ConcurrencyScenarioError("handoff_receiver_not_completed")
        if (
            source_event["sequence"] >= receiver_event["sequence"]
            or source_event["logical_time"] >= receiver_event["logical_time"]
        ):
            raise ConcurrencyScenarioError("noncausal_handoff_order")
        evidence = _text(
            handoff["handoff_evidence_sha256"],
            _SHA256,
            "invalid_handoff_evidence_hash",
        )
        edge = (source_event_id, receiver_event_id, evidence)
        if edge in seen_edges:
            raise ConcurrencyScenarioError("duplicate_handoff")
        seen_edges.add(edge)
        order = (
            receiver_event["sequence"], sender, source_event_id,
            receiver, receiver_event_id, evidence,
        )
        if prior_order is not None and order <= prior_order:
            raise ConcurrencyScenarioError("nondeterministic_handoff_order")
        prior_order = order

        unsigned = {
            "sequence": expected_sequence,
            "sender_participant_id": sender,
            "receiver_participant_id": receiver,
            "source_event_id": source_event_id,
            "receiver_event_id": receiver_event_id,
            "handoff_evidence_sha256": evidence,
        }
        handoff_id = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()
        normalized.append({"handoff_id": handoff_id, **unsigned})
        senders.add(sender)
        receivers.add(receiver)

    report = {
        "causal_handoff_schema_version": SCHEMA_VERSION,
        "handoff_set_id": handoff_set_id,
        "scenario_id": concurrency_report["scenario_id"],
        "concurrency_evidence_id": concurrency_report["evidence_id"],
        "handoffs": normalized,
        "coverage": {
            "recorded_handoff_count": len(normalized),
            "sender_count": len(senders),
            "receiver_count": len(receivers),
            "strict_temporal_order_verified": True,
            "scope": "bounded_recorded_cross_agent_causal_metadata_only",
        },
        "authority": CAUSAL_HANDOFF_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ConcurrencyScenarioError("causal_handoff_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def evaluate_recorded_quorum_barriers(
    scenario: Mapping[str, object], synchronization_record: Mapping[str, object]
) -> dict:
    """Verify bounded recorded quorum barriers without waiting or scheduling work."""

    concurrency_report = evaluate_recorded_concurrent_scenario(scenario)
    root = _exact_dict(
        synchronization_record,
        frozenset({
            "schema_version", "synchronization_set_id",
            "synchronization_limit", "barriers",
        }),
        "invalid_synchronization_record_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ConcurrencyScenarioError("unsupported_synchronization_schema")
    synchronization_set_id = _text(
        root["synchronization_set_id"],
        _IDENTIFIER,
        "invalid_synchronization_set_id",
    )
    synchronization_limit = root["synchronization_limit"]
    if (
        type(synchronization_limit) is not int
        or not 1 <= synchronization_limit <= MAX_SYNCHRONIZATIONS
    ):
        raise ConcurrencyScenarioError("invalid_synchronization_limit")
    barriers = root["barriers"]
    if (
        type(barriers) is not list
        or not 1 <= len(barriers) <= synchronization_limit
    ):
        raise ConcurrencyScenarioError("invalid_synchronization_count")

    registered = {
        participant["participant_id"]
        for participant in concurrency_report["participants"]
    }
    events = {event["event_id"]: event for event in concurrency_report["events"]}
    barrier_keys = frozenset({
        "sequence", "barrier_id", "participant_ids", "quorum",
        "arrivals", "release_event_id",
    })
    arrival_keys = frozenset({"participant_id", "event_id"})
    normalized = []
    seen_barrier_ids = set()
    seen_event_roles = set()
    prior_order = None
    participants_observed = set()
    for expected_sequence, value in enumerate(barriers, start=1):
        barrier = _exact_dict(value, barrier_keys, "invalid_barrier_shape")
        if type(barrier["sequence"]) is not int or barrier["sequence"] != expected_sequence:
            raise ConcurrencyScenarioError("invalid_barrier_sequence")
        barrier_id = _text(barrier["barrier_id"], _IDENTIFIER, "invalid_barrier_id")
        if barrier_id in seen_barrier_ids:
            raise ConcurrencyScenarioError("duplicate_barrier_id")
        seen_barrier_ids.add(barrier_id)

        participant_ids = barrier["participant_ids"]
        if type(participant_ids) is not list or not 2 <= len(participant_ids) <= MAX_PARTICIPANTS:
            raise ConcurrencyScenarioError("invalid_barrier_participant_count")
        normalized_participants = [
            _text(value, _IDENTIFIER, "invalid_participant_id")
            for value in participant_ids
        ]
        if (
            normalized_participants != sorted(normalized_participants)
            or len(set(normalized_participants)) != len(normalized_participants)
        ):
            raise ConcurrencyScenarioError("nondeterministic_barrier_participants")
        if any(participant not in registered for participant in normalized_participants):
            raise ConcurrencyScenarioError("unregistered_barrier_participant")

        quorum = barrier["quorum"]
        if type(quorum) is not int or not 2 <= quorum <= len(normalized_participants):
            raise ConcurrencyScenarioError("invalid_barrier_quorum")
        arrivals = barrier["arrivals"]
        if (
            type(arrivals) is not list
            or not quorum <= len(arrivals) <= len(normalized_participants)
        ):
            raise ConcurrencyScenarioError("barrier_quorum_not_met")

        release_event_id = _text(
            barrier["release_event_id"], _SHA256, "invalid_release_event_id"
        )
        release_event = events.get(release_event_id)
        if release_event is None:
            raise ConcurrencyScenarioError("unknown_release_event")
        if release_event["outcome_code"] != "completed":
            raise ConcurrencyScenarioError("barrier_release_not_completed")
        if release_event["participant_id"] not in normalized_participants:
            raise ConcurrencyScenarioError("barrier_release_participant_mismatch")

        normalized_arrivals = []
        arrival_participants = set()
        arrival_event_ids = set()
        for arrival_value in arrivals:
            arrival = _exact_dict(
                arrival_value, arrival_keys, "invalid_barrier_arrival_shape"
            )
            participant_id = _text(
                arrival["participant_id"], _IDENTIFIER, "invalid_participant_id"
            )
            event_id = _text(arrival["event_id"], _SHA256, "invalid_arrival_event_id")
            if participant_id not in normalized_participants:
                raise ConcurrencyScenarioError("arrival_participant_not_in_barrier")
            if participant_id in arrival_participants or event_id in arrival_event_ids:
                raise ConcurrencyScenarioError("duplicate_barrier_arrival")
            event = events.get(event_id)
            if event is None:
                raise ConcurrencyScenarioError("unknown_arrival_event")
            if event["participant_id"] != participant_id:
                raise ConcurrencyScenarioError("arrival_event_participant_mismatch")
            if event["outcome_code"] != "completed":
                raise ConcurrencyScenarioError("barrier_arrival_not_completed")
            if (
                event["sequence"] >= release_event["sequence"]
                or event["logical_time"] >= release_event["logical_time"]
            ):
                raise ConcurrencyScenarioError("barrier_released_before_arrival")
            arrival_participants.add(participant_id)
            arrival_event_ids.add(event_id)
            normalized_arrivals.append({
                "participant_id": participant_id,
                "event_id": event_id,
            })

        if normalized_arrivals != sorted(
            normalized_arrivals, key=lambda item: (item["participant_id"], item["event_id"])
        ):
            raise ConcurrencyScenarioError("nondeterministic_barrier_arrivals")
        event_roles = arrival_event_ids | {release_event_id}
        if release_event_id in arrival_event_ids or seen_event_roles & event_roles:
            raise ConcurrencyScenarioError("reused_synchronization_event")
        seen_event_roles.update(event_roles)
        order = (release_event["sequence"], barrier_id)
        if prior_order is not None and order <= prior_order:
            raise ConcurrencyScenarioError("nondeterministic_barrier_order")
        prior_order = order

        unsigned = {
            "sequence": expected_sequence,
            "barrier_id": barrier_id,
            "participant_ids": normalized_participants,
            "quorum": quorum,
            "arrivals": normalized_arrivals,
            "release_event_id": release_event_id,
        }
        record_id = hashlib.sha256(_canonical(unsigned).encode("utf-8")).hexdigest()
        normalized.append({"barrier_evidence_id": record_id, **unsigned})
        participants_observed.update(normalized_participants)

    report = {
        "quorum_barrier_schema_version": SCHEMA_VERSION,
        "synchronization_set_id": synchronization_set_id,
        "scenario_id": concurrency_report["scenario_id"],
        "concurrency_evidence_id": concurrency_report["evidence_id"],
        "barriers": normalized,
        "coverage": {
            "recorded_barrier_count": len(normalized),
            "recorded_arrival_count": sum(len(value["arrivals"]) for value in normalized),
            "participant_count": len(participants_observed),
            "quorum_and_release_order_verified": True,
            "scope": "bounded_recorded_quorum_barrier_metadata_only",
        },
        "authority": QUORUM_BARRIER_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ConcurrencyScenarioError("quorum_barrier_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def evaluate_recorded_capacity_budget(
    scenario: Mapping[str, object], budget_record: Mapping[str, object]
) -> dict:
    """Verify bounded recorded counts without enforcing runtime resources."""
    concurrency_report = evaluate_recorded_concurrent_scenario(scenario)
    root = _exact_dict(
        budget_record,
        frozenset({"schema_version", "budget_id", "resource_key_limit", "participant_event_limits"}),
        "invalid_capacity_budget_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise ConcurrencyScenarioError("unsupported_capacity_budget_schema")
    budget_id = _text(root["budget_id"], _IDENTIFIER, "invalid_capacity_budget_id")
    resource_limit = root["resource_key_limit"]
    if type(resource_limit) is not int or not 1 <= resource_limit <= MAX_RESOURCE_KEYS:
        raise ConcurrencyScenarioError("invalid_resource_key_limit")
    limits = root["participant_event_limits"]
    if type(limits) is not list or len(limits) != len(concurrency_report["participants"]):
        raise ConcurrencyScenarioError("invalid_participant_budget_count")
    normalized_limits = []
    for value in limits:
        item = _exact_dict(value, frozenset({"participant_id", "event_limit"}), "invalid_participant_budget_shape")
        participant_id = _text(item["participant_id"], _IDENTIFIER, "invalid_participant_id")
        event_limit = item["event_limit"]
        if type(event_limit) is not int or not 1 <= event_limit <= MAX_EVENTS:
            raise ConcurrencyScenarioError("invalid_participant_event_limit")
        normalized_limits.append({"participant_id": participant_id, "event_limit": event_limit})
    registered = [value["participant_id"] for value in concurrency_report["participants"]]
    if [value["participant_id"] for value in normalized_limits] != registered:
        raise ConcurrencyScenarioError("participant_budget_set_mismatch")
    observed = {participant_id: 0 for participant_id in registered}
    resources = set()
    for event in concurrency_report["events"]:
        observed[event["participant_id"]] += 1
        resources.add(event["resource_key_sha256"])
    if len(resources) > resource_limit:
        raise ConcurrencyScenarioError("resource_key_budget_exceeded")
    for limit in normalized_limits:
        if observed[limit["participant_id"]] > limit["event_limit"]:
            raise ConcurrencyScenarioError("participant_event_budget_exceeded")
    report = {
        "capacity_budget_schema_version": SCHEMA_VERSION,
        "budget_id": budget_id,
        "scenario_id": concurrency_report["scenario_id"],
        "concurrency_evidence_id": concurrency_report["evidence_id"],
        "resource_key_limit": resource_limit,
        "recorded_resource_key_count": len(resources),
        "participant_event_limits": [
            {**value, "recorded_event_count": observed[value["participant_id"]]}
            for value in normalized_limits
        ],
        "coverage": {
            "recorded_counts_within_declared_limits": True,
            "runtime_resource_enforcement_performed": False,
            "scope": "bounded_recorded_capacity_budget_metadata_only",
        },
        "authority": CAPACITY_BUDGET_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REPORT_BYTES:
        raise ConcurrencyScenarioError("capacity_budget_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
