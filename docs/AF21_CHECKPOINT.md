# AF-21 — Structured replay-suite reporting

Status: ACCEPTANCE DEFINED. AF-20 remains merged and verified; no old primitive
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
