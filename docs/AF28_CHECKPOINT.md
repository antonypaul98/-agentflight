# AF-28 — concurrent and multi-agent scenarios

Status: **IN PROGRESS**. The first bounded slice validates deterministic,
caller-supplied concurrent-scenario metadata.

`evaluate_recorded_concurrent_scenario` accepts two to eight registered
participants and one to sixty-four recorded events. It verifies one hashed
tenant boundary, content-addressed per-participant event chains, deterministic
`logical_time_then_participant_id` ordering, and fail-closed conflict evidence.
For events sharing one logical time and resource hash, the lexicographically
first participant is the only recorded completion; later participants must be
recorded as conflict rejections without state mutation.

This contract does not start threads, processes, agents, tools, projects,
commands or network calls. It accesses no credentials, payloads, filesystem,
durable state or external system and makes no resource-cap or OS-sandbox claim.
All tenant, adapter, resource and state identities are caller-supplied hashes.

The second bounded slice derives an exact-evidence-bound resource lineage from
that validated schedule. It requires all contenders in a logical round to share
one recorded pre-state, exactly one accepted event per resource round, and each
later round to begin at the prior accepted post-state. An isolated recorded
conflict rejection fails closed. The derived report exposes only hashes,
content-addressed event identifiers, bounded coverage, and final recorded state
hashes; it neither reads nor writes state.

The third bounded slice verifies caller-supplied cross-agent causal handoff
metadata against exact event identities from the validated schedule. It accepts
only registered distinct participants, completed source and receiver events,
strictly earlier source logical time, deterministic edge ordering, bounded
cardinality, and content-addressed handoff records. Handoff evidence is a hash;
the verifier never reads or transfers a message, artifact, payload, or state.

## Acceptance gate

The source must pass exact Python 3.11 PR-head CI with zero product skips, a
guarded merge, and exact merged-main CI. A separate canonical records receipt
and explicit writer release are required before another AF-28 source slice.
