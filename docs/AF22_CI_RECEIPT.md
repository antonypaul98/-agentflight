# AF-22 CI receipt

Baseline main: 68272773baa70937aa68fea89ea96f8d8a49efd1
Feature commit: 92688dc71c74d846c961473aa29688141d4bd62e
CI run: 37884091332
CI event: push
CI conclusion: success
Python: 3.11.17
Product tests: 192 passed
Infrastructure: 18 executed, 1 skipped
Local AF-22 regressions: 32 passed (Python 3.13.5)
Next: reconcile CHECKPOINT_STATE.json and add a hard output-capture bound.

## AF-22 defensive reliability follow-up — 2026-10-09

Published commit: b15df8360993645b40076598854f44268514cb2c
CI run: 37904427569 (push, completed, success)
CI URL: https://github.com/antonypaul98/-agentflight/actions/runs/37904427569
Python: 3.11.17
Product tests: 204 passed, 0 failed
Infrastructure: 18 executed, 1 existing skip; diagnostics passed
Local isolated focused tests: 44 passed (Python 3.13.5)
Scope: combined stdout/stderr reporting budget, sanitized launch errors,
redacted timeout output, deterministic failure evidence. AF-22 remains open.

## AF-22 completed-parent process-group cleanup — 2026-10-09

Published source commit: 02c28dfd38b5d522c96bd710362aaf986087b3bc
CI: https://github.com/antonypaul98/-agentflight/actions/runs/37943589019
Result: success, push, exact source SHA, Python 3.11.17.
Product tests: 215 passed, 0 failed (+2 versus previous 213).
Infrastructure: 18 executed, 1 baseline skip; diagnostics passed.
Local focused: 46 passed, repeated three times on Python 3.13.5.
Scope: clean up isolated process groups even after a successful parent exit;
regressions verify orphaned-pipe EOF and completed-parent cleanup.
AF-22 remains IN_PROGRESS; no untrusted-code sandbox acceptance.

## Accepted wait-EINTR repair — 2026-10-10 UTC

Source commit: `16365db581f9ed1019f466575187685d2b97a481`.
PR: https://github.com/antonypaul98/-agentflight/pull/7
Exact source push CI:
https://github.com/antonypaul98/-agentflight/actions/runs/38083240626
Exact source PR-event CI:
https://github.com/antonypaul98/-agentflight/actions/runs/38083268347
Merged main: `a2195a74fc49de43eadbc468c73e4c77d5e926aa`.
Exact merged-main CI:
https://github.com/antonypaul98/-agentflight/actions/runs/38083310755

All three runs succeeded on Python 3.11.17: **243 product tests passed,
0 failed, 0 skipped**. Infrastructure: 18 executed, 17 passed and 1 existing
Memory-only skip; dependency/import diagnostics passed.

After pipe EOF, interrupted `process.wait()` now retries within the original
monotonic deadline. Three synthetic regressions cover transient recovery,
repeated interruptions exhausting that deadline, and a later TimeoutExpired
with redacted counts. Existing worker modes, security boundaries and Linux
descendant assertions remain unchanged. The prior recovery ZIP was unavailable
in accessible storage; the defect was reproduced against the canonical source.

Local canonical Python 3.11.17 results: 3 focused failures before the fix and
3 passes after it. The full local suite reported 241 passed and 2 existing
descendant-observation failures. Both also fail on unchanged baseline
`36913ae7ff1d7aaae2e179bc675f1f0be248dd2c`: this execution environment's
reported child PID maps to a different `/proc` entry. GitHub Linux CI runs and
passes those unchanged tests. A full local pass is not claimed.

This accepts only the existing wait-EINTR reliability repair. Overall AF-22
remains IN_PROGRESS; no arbitrary-code sandbox or physical acceptance is claimed.
The next hourly writer reviews existing AF-22 acceptance after the records
PR/main CI and explicit release, without repeating accepted slices.
