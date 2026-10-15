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
