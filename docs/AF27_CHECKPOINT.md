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
payloads or credentials. Evidence and CI receipts remain pending until the
source slice is independently verified.
