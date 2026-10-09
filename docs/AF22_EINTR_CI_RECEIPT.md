# AF-22 interrupted pipe-read CI receipt — 2026-10-09

Active branch: main. Checkpoint: AF-22 IN_PROGRESS.

Implementation commit: 1ceee68cdbe01f8e9b0efe841c3c30ae10c096fd
CI: https://github.com/antonypaul98/-agentflight/actions/runs/37993540315
Result: success, exact implementation SHA, Python 3.11.17.
Product tests: 221 passed, 0 failed.
Infrastructure: 18 executed, one existing skip.
Environment diagnostics: passed.

Reliability change: retry InterruptedError during bounded pipe reads
without extending the existing capture deadline. Two new regressions
failed against the previous implementation and passed after the fix.
Local focused tests: 11 passed, Python 3.13.5.

Preflight: verified canonical script attempted; shell Git fetch failed
on DNS. Authorized connected GitHub publication succeeded.

CHECKPOINT_STATE.json reconciliation was attempted but rejected by
write-safety checks. This receipt preserves the exact tested SHA and CI.
Next: actual Linux descendant-termination regressions and AF-22
acceptance review. The fixed worker is not an OS sandbox.
