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
