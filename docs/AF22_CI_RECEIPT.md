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
