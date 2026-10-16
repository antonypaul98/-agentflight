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
