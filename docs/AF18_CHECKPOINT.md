# AF-18 deterministic fault injection

Canonical branch: `work/af18-fault-injection-v2`.
Starting main: `bb9ef51e534df4d865880a8168ed5ed778687941` (AF-17 CI already integrated).

The implementation on the older `work/af18-deterministic-fault-injection`
branch was byte-identical to v2. All nine existing regression cases were ported;
its CI file is already on main and was not duplicated. The older branch is
superseded for AF-18 development; it remains retained as historical evidence.

Faults are selected by explicit integer call indices, with no hidden call counter.
Unknown kinds and non-integer indices fail closed. Returned replacement values
are copied so consumer mutation cannot corrupt later replays. Regression coverage
combines ReplayTape and stable evidence identifiers and preserves the original tape.

Validation: 37 full-suite tests passed locally (including 16 fault cases).
Integration passed exact-head CI and merged-main verification (receipt below); this record does not claim
any later AF checkpoint, external agent integration, or benchmark.

## Verified integration — 2026-09-30

Checkpoint **AF-18 accepted on main** through PR #2.

- Exact PR head: `1044f4308d6ea2db121b43f1c0e1a45f59be8953`; CI run `36669373850` succeeded.
- Merge: `554bfb55dce1262dcc8d52a262b2bb2359fa560a`, fetched and verified locally.
- Merged-main CI run `36669482127` succeeded.
- Local reviewed/tested source tree equals the merged implementation tree.
- This follow-up records the completed integration; it changes documentation only.
