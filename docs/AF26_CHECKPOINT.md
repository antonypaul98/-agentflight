# AF-26 — controlled failure injection

Status: **MERGED AND VERIFIED** for the bounded recorded-only scope. AF-26
validates deterministic caller-supplied metadata for recorded network, timeout,
rate-limit, and API failure scenarios plus bounded retry/outage sequences.

The plan is bound to an exact AF-25 fixture-environment evidence ID. It enforces
unique bounded call indexes, stable scenario order, enumerated redacted outcome
codes, deterministic evidence identifiers, and explicit delay semantics.

`evaluate_recorded_call` evaluates an already-recorded call hash. It does not
make requests, resolve DNS, sleep, invoke an API, execute an agent/tool/command,
read a project, inspect a host, or provide OS isolation. URLs, endpoints,
payloads, paths, credentials, environment values, and arbitrary error text are
outside the accepted schema and fail closed.

`evaluate_recorded_sequence` binds an ordered sequence to the exact normalized
failure plan, fixture environment, and trajectory evidence. It accepts at most
four attempts per call, reports recovery, exhaustion or incompleteness, and
fails closed on gaps, reordering, unknown outcomes, extra fields, or binding
mismatches. It verifies records only: it does not retry, wait, recover, or act.

AF-27 owns recovery, retry, and durable state consistency.

## First source-slice receipt

- Source PR: [#37](https://github.com/antonypaul98/-agentflight/pull/37)
- Source SHA: `4ecadd26898f06e161322777a7b6f52c778468da`
- Pull-request CI: [38698230914](https://github.com/antonypaul98/-agentflight/actions/runs/38698230914), Python 3.11.17, 374 passed, zero product skips
- Merged main: `b90e0ea063e8ca7204d1f5f543ade18858b87161`
- Merged-main CI: [38698334703](https://github.com/antonypaul98/-agentflight/actions/runs/38698334703), Python 3.11.17, 374 passed, zero product skips

## Retry-sequence source receipt

- Source PR: [#39](https://github.com/antonypaul98/-agentflight/pull/39)
- Source SHA: `02beb959f5357168cdf4a04bdeaf0a90e26cbf21`
- Source tree: `595c08d6bf25d6f93bcf6941013a8c29b0e9b977`
- Pull-request CI: [38734703918](https://github.com/antonypaul98/-agentflight/actions/runs/38734703918), Python 3.11.17, 385 passed, zero product skips
- Merged main: `e89a1afd4ad2998854cfd6c6387234c794134863`
- Merged-main CI: [38734820602](https://github.com/antonypaul98/-agentflight/actions/runs/38734820602), Python 3.11.17, 385 passed, zero product skips
- Records PR: [#40](https://github.com/antonypaul98/-agentflight/pull/40)
- Records-main SHA: `833495376f75ea8606b078fd27737b7dd987283c`
- Records PR/main CI: [38777475825](https://github.com/antonypaul98/-agentflight/actions/runs/38777475825) / [38777568067](https://github.com/antonypaul98/-agentflight/actions/runs/38777568067), 385 passed, zero product skips

Together the two independently tested slices cover every AF-26 roadmap fault
kind and the bounded recorded retry/outage evidence needed to close the scoped
checkpoint. The roadmap is 4/12 accepted. This is not arbitrary execution,
network or process isolation, real-project access, or production authority.
