# AF-21 — Structured replay-suite reporting

Status: MERGED AND VERIFIED. AF-20 remains merged and verified; no old primitive
is reimplemented by this checkpoint.

One capability: run a bounded suite of recorded synthetic tool exchanges and
emit deterministic JSON results suitable for automated gates. Reuse
`replay_exchange`, `CallContract`, and existing evidence identifiers.

Acceptance:

1. Each case has an explicit expected verification verdict; expected rejections
   count as passing tests only when both the boolean and reason code match.
2. Failed cases identify their case, expected/observed verdict, stable evidence,
   and fixed diagnostic guidance. Raw argument values, results, and verifier
   detail are not copied into reports.
3. Suites and cases have unique bounded identifiers. Canonical case ordering
   and JSON serialization produce stable reports; evidence is scoped to suite
   and case so reports cannot silently mix projects.
4. Empty, malformed, duplicate, oversized, and unsupported fixtures fail closed.
   The CLI exits 0 for matched suites, 1 for mismatches, and 2 for invalid input.
5. JSON fixtures are data only. No commands, plugins, network requests, or
   external repositories are executed or changed. No production credentials.
6. Meaningful tests cover stable output, negative expectations, actionable
   failures, privacy, input bounds, and real CLI exit behavior.
7. Local Python 3.11 checks and exact-head CI must pass. Merge and exact
   merged-main CI must be verified before marking the checkpoint accepted.

Explicit limits: this is recorded-call verification, not execution of arbitrary
project test commands, a sandbox, external-project integration, hardware
acceptance, or a production crash test. Future project adapters must be scoped
and isolated separately.

Next smallest checkpoint after acceptance: a single disposable synthetic
subprocess adapter with bounded execution and timeout/failure reporting. Do not
attach it to a live project or add several adapters in this checkpoint.

## Fixture and report contract

The checked-in `examples/replay-suite.json` demonstrates schema version 1.
A fixture contains only `schema_version`, `suite_id`, and `cases`. Each case
contains `case_id`, `contract`, `exchange`, and `expected`. Contract fields are
`name` and optional `required`/`optional` string arrays; exchange fields are
`name`, `arguments`, and optional JSON `result`. Expected fields are `passed`
and the verifier reason `code`; `ok` requires true, all other reasons false.
Unknown fields and duplicate JSON keys are rejected. Entire fixtures validate
before any replay runs. Duplicate declarations inside a field array are invalid
fixtures; overlapping required/optional declarations remain verifier test cases.

Bounds: 1 MiB input and canonical JSON, 1–256 cases, 32 JSON levels, 50,000 JSON
value nodes, and 1–64 ASCII identifier characters (letters/digits plus `_.-`).
Only exact built-in JSON types and finite numbers are accepted. Existing
verifier argument/schema bounds remain unchanged. Reports have stable case
ordering, expected/observed boolean and code, scoped evidence ID, and fixed
diagnostic guidance. A replay exception yields an error with null observed
verdict and evidence, never a fabricated rejection or successful expectation.
Reports verify contract verdicts, not recorded return-value correctness.

## Local validation

Python 3.11.17: 34 new suite tests passed; all 160 product tests passed with
zero failures. Infrastructure: 18 tests executed, 17 passed and one pre-existing
skip. Environment diagnostics, package dependency checks, and diff whitespace
checks passed. These are local feature-source results; exact-head and merged-main
CI confirmation follows below. No new
dependencies or CI check changes.

## Verified acceptance — 2026-10-09 UTC

- Previous checkpoint: AF-20 was merged and verified; current baseline main
  `8dc07a0b927a0c412a5595c6af08d43c523be94a` had successful CI `37878490104`
  with 126 product tests. Historical AF-20 work was not reimplemented.
- AF-21 exact source/PR head: `81d435cf6dd17253d5c9924537458b612f030c3a`.
  PR #6: https://github.com/antonypaul98/-agentflight/pull/6
- Exact push CI: https://github.com/antonypaul98/-agentflight/actions/runs/37880641379
- Exact PR-head CI: https://github.com/antonypaul98/-agentflight/actions/runs/37880666599
- Merge: `8066bbcc8127c12c528f4d355d1029f894355c95`; exact merged-main CI:
  https://github.com/antonypaul98/-agentflight/actions/runs/37880827835
- All three runs succeeded on Python 3.11.17: 160 product tests passed, zero
  failures; infrastructure 18 executed, 17 passed and one unchanged baseline
  skip; environment diagnostics passed. Product suite grew by 34 tests.
- Local source commit `fa41cd86f56a292d9bd348c9c23432e1f7a65a3f`, remote
  source and merged main share tree `14ee27b417525d209241c703eacf0bb32b20c21a`.
  Local scope/implementation branches and historical remote branches remain.
- No credentials, private user data, external project changes, destructive live
  tests, new dependencies, or CI check changes were introduced.
- Actual remaining Astra/Work allowance was inaccessible. This run was limited
  to one capability, with validation and preservation completed.
- No Antony intervention is required for AF-21. Shell Git credentials and gh
  are unavailable; verified connector publication is the working route.

Next smallest safe checkpoint: AF-22, one disposable synthetic subprocess
adapter with bounded execution, timeout classification and sanitized diagnostics.
Do not attach live project credentials or real project adapters yet.
