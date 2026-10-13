# AF-24 — Multi-step trajectory verification

Status: **IN_PROGRESS**.

The first bounded slice verifies ordered state transitions in an AF-23
authorized recorded run. Every step after the first must consume the exact
SHA-256 state emitted by its predecessor. A failed or rejected step is terminal
and produces explicit `partial_failure` evidence; later recorded steps fail
closed. Reports bind the exact registry and authorized recorded-run evidence,
initial and terminal state hashes, transition order, coverage, and a stable
evidence identifier.

The verifier retains metadata and hashes only. It does not inspect or
dereference state, prompts, tool arguments or results; import frameworks; read
projects; execute agents, tools or commands; use credentials or networks; or
claim process/OS isolation. This is one source slice, not AF-24 acceptance.
