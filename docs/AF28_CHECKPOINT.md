# AF-28 — concurrent and multi-agent scenarios

Status: **MERGED AND VERIFIED** for the bounded recorded-only scope. The
checkpoint validates deterministic caller-supplied concurrent-scenario metadata.

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

The fourth bounded slice verifies caller-supplied quorum-barrier metadata against
exact completed events from the validated schedule. It requires two to eight
sorted registered participants, a non-boolean quorum of at least two, unique
completed arrivals meeting that quorum, and a completed release event strictly
after every recorded arrival. Barrier and arrival ordering is deterministic,
event roles cannot be reused, and all evidence is content-addressed. The verifier
does not wait, schedule, coordinate, execute, transfer data, or access state.

The fifth bounded slice binds per-participant event counts and distinct recorded
resource hashes to exact scenario evidence and caller-declared caps. Those caps
are verified metadata, not runtime allocation, enforcement, or isolation.

## Acceptance gate

The source must pass exact Python 3.11 PR-head CI with zero product skips, a
guarded merge, and exact merged-main CI. A separate canonical records receipt
and explicit writer release were required for every source slice. PRs #57-#66
and their exact CI receipts satisfy that gate; the final closure PR independently
re-runs the full suite before AF-29 begins.
