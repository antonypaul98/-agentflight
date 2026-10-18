# AF-27 — recovery, retry, and state consistency

Status: **IN PROGRESS**. The first bounded slice validates caller-supplied,
recorded recovery metadata. It binds the evidence to exact failure-plan,
trajectory, operation, and idempotency-key hashes; enforces a contiguous state
chain; permits at most one commit; and requires failed attempts and duplicate
replays to leave state unchanged.

`evaluate_recorded_recovery` is offline and metadata-only. It does not retry,
recover, execute an agent or tool, inspect a project, access durable state, read
credentials or payloads, or claim filesystem/process/network/OS isolation.
Arbitrary untrusted execution remains outside the authorized scope.

## First source-slice receipt

- Source PR: [#42](https://github.com/antonypaul98/-agentflight/pull/42)
- Source SHA: `ca4bd35a1e5557ee9a48ecd18145b7d9ddeb7301`
- Source tree: `9b4135caafe4a752c1b4d4af57d76ed77fa32a8c`
- Pull-request CI: [38850492412](https://github.com/antonypaul98/-agentflight/actions/runs/38850492412), Python 3.11.17, 401 passed, zero product skips
- Merged main: `234678fe214f86336832d1a901a9c5be8a5581aa`
- Merged-main CI: [38850574375](https://github.com/antonypaul98/-agentflight/actions/runs/38850574375), Python 3.11.17, 401 passed, zero product skips
- Writer release: [receipt](https://github.com/antonypaul98/-agentflight/pull/42#issuecomment-6208068774)

This accepts only the first bounded source slice. AF-27 remains in progress and
the roadmap remains 4/12 accepted.

## Recorded retry-budget slice

The second bounded slice binds a fixed retry budget to the exact content hash
of a validated recovery report. It caps recorded attempts at eight, rejects a
budget smaller than the already-recorded attempt count, and distinguishes
recovered, exhausted, and retry-permitted metadata states. A completed recovery
never permits another retry, even if nominal budget remains.

The budget result is itself deterministic and content-addressed. It performs no
retry, recovery, sleeping, command or tool execution, project access, durable
state access, external call, or isolation. `retry_permitted` describes only the
caller-supplied recorded budget; it does not authorize execution.

### Retry-budget source receipt

- Source PR: [#44](https://github.com/antonypaul98/-agentflight/pull/44)
- Source SHA: `fd71cf0f1597931ed575e165a8a0b9fb76c35e39`
- Source tree: `43aa52b9353ab12141aed760b75dd520bd668c75`
- Pull-request CI: [38886756075](https://github.com/antonypaul98/-agentflight/actions/runs/38886756075), Python 3.11.17, 409 passed, zero product skips
- Merged main: `8992aa0e7dbbab05c73848694c972b3dac799a7b`
- Merged-main CI: [38886830294](https://github.com/antonypaul98/-agentflight/actions/runs/38886830294), Python 3.11.17, 409 passed, zero product skips

This is a second verified slice, not AF-27 checkpoint acceptance. Roadmap
progress remains 4/12 pending independent records CI and explicit release.

## Recorded state-checkpoint slice

The next bounded slice validates caller-supplied checkpoint metadata against an
exact, recomputed recovery report. It binds the recovery evidence ID, a bounded
positive checkpoint generation, the recorded initial state hash, and the final
recorded state hash. Recovered and incomplete transcripts are both supported;
incomplete transcripts remain at their unchanged initial hash under the
existing no-commit invariant.

The result is deterministic and content-addressed. It does not inspect, read,
write, restore, or claim persistence of durable state. It performs no project,
agent, tool, command, process, filesystem, or network action and accepts no
payloads or credentials.

### State-checkpoint source receipt

- Source PR: [#46](https://github.com/antonypaul98/-agentflight/pull/46)
- Source SHA: `c556396d3caa982e70be914cedb12010804bce73`
- Source tree: `dd0eb0c5cf5bac8f3469f85b48220b77f207939a`
- Pull-request CI: [39089907017](https://github.com/antonypaul98/-agentflight/actions/runs/39089907017), Python 3.11.17, 419 passed, zero product skips
- Merged main: `99ff09825e77613917c866591ebba37700412d40`
- Merged-main CI: [39089947965](https://github.com/antonypaul98/-agentflight/actions/runs/39089947965), Python 3.11.17, 419 passed, zero product skips

This is a third verified AF-27 slice, not checkpoint acceptance. Roadmap
progress remains 4/12 pending independent records CI and explicit release.

## Recorded resume-guard slice

The next bounded slice combines exact recovery, retry-budget, and state-checkpoint
evidence into one deterministic disposition: closed after recovery, closed after
budget exhaustion, or a recorded resume candidate with the next attempt number.
Every input is recomputed before use, and the output binds the exact three
evidence identities, checkpoint generation, checkpoint state hash, and budget
coverage.

This is metadata validation only. A resume-candidate disposition neither
authorizes nor performs retry, recovery, restore, project/agent/tool/command
execution, durable-state access, external calls, credential or payload access,
or filesystem/process/network/OS isolation.

### Resume-guard source receipt

- Source PR: [#48](https://github.com/antonypaul98/-agentflight/pull/48)
- Source SHA: `7d99425194774aab8f1d64aac1c27c744e302a45`
- Source tree: `ce8e5b691c2527955108138022ab491df0f90ab3`
- Pull-request CI: [39131567287](https://github.com/antonypaul98/-agentflight/actions/runs/39131567287), Python 3.11.17, 427 passed, zero product skips
- Merged main: `f4588406d6c7cf12d9e8893386f106533d5d6556`
- Merged-main CI: [39131630319](https://github.com/antonypaul98/-agentflight/actions/runs/39131630319), Python 3.11.17, 427 passed, zero product skips

This is a fourth verified AF-27 slice, not checkpoint acceptance. Roadmap
progress remains 4/12 pending independent records CI and explicit release.

## Recorded resume-transition continuity slice

The next bounded slice verifies that a later caller-supplied recovery snapshot
extends a prior resume candidate by exactly one recorded event. It preserves the
complete earlier event prefix and recovery bindings, advances the attempt count
and checkpoint generation exactly once, and binds both exact resume-guard
evidence identities. Replayed snapshots, skipped generations, altered history,
and action-bearing fields fail closed.

This is deterministic metadata validation only. It neither authorizes nor
performs a retry, recovery, restore, project/agent/tool/command execution,
durable-state access, external call, credential or payload access, or any form
of filesystem/process/network/OS isolation.

### Resume-transition source receipt

- Source PR: [#50](https://github.com/antonypaul98/-agentflight/pull/50)
- Source SHA: `74310a2aca5091118d4692a043ba668310b4a8ae`
- Source tree: `0e99662a7080c399088b7cdfedb6996e83e26e0d`
- Pull-request CI: [39159042557](https://github.com/antonypaul98/-agentflight/actions/runs/39159042557), Python 3.11.17, 439 passed, zero product skips
- Merged main: `d68706b245bd22a63bec854b68c08f1e1f1dc5d6`
- Merged-main CI: [39159139603](https://github.com/antonypaul98/-agentflight/actions/runs/39159139603), Python 3.11.17, 439 passed, zero product skips

This is a fifth verified AF-27 slice, not checkpoint acceptance. AF-27 remains
in progress and the roadmap remains 4/12 accepted pending independent records
CI, explicit release, and eventual bounded checkpoint acceptance.
