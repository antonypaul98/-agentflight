# AF-26 — controlled failure injection

Status: **IN PROGRESS**. This first bounded slice validates deterministic,
caller-supplied metadata for recorded network, timeout, rate-limit, and API
failure scenarios.

The plan is bound to an exact AF-25 fixture-environment evidence ID. It enforces
unique bounded call indexes, stable scenario order, enumerated redacted outcome
codes, deterministic evidence identifiers, and explicit delay semantics.

`evaluate_recorded_call` evaluates an already-recorded call hash. It does not
make requests, resolve DNS, sleep, invoke an API, execute an agent/tool/command,
read a project, inspect a host, or provide OS isolation. URLs, endpoints,
payloads, paths, credentials, environment values, and arbitrary error text are
outside the accepted schema and fail closed.

Later AF-26 slices may add bounded recorded retry/outage sequences and exact
trajectory binding. AF-27 owns recovery, retry, and durable state consistency.

## First source-slice receipt

- Source PR: [#37](https://github.com/antonypaul98/-agentflight/pull/37)
- Source SHA: `4ecadd26898f06e161322777a7b6f52c778468da`
- Pull-request CI: [38698230914](https://github.com/antonypaul98/-agentflight/actions/runs/38698230914), Python 3.11.17, 374 passed, zero product skips
- Merged main: `b90e0ea063e8ca7204d1f5f543ade18858b87161`
- Merged-main CI: [38698334703](https://github.com/antonypaul98/-agentflight/actions/runs/38698334703), Python 3.11.17, 374 passed, zero product skips

This receipt accepts only the first bounded source slice. AF-26 remains in
progress and the roadmap remains 3/12 accepted.
