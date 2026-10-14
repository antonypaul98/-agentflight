# AgentFlight competitive roadmap — AF-23 through AF-34

Status: **AUTHORIZED, 3/12 ACCEPTED**. AF-23 through AF-25 are merged and
verified for their bounded recorded-only scopes; AF-26 is next. The 13–18 week range is
a planning estimate and will be recalibrated from measured checkpoint throughput.

Each checkpoint requires synthetic regressions, exact-head PR CI, guarded
merge, merged-main CI, canonical acceptance records, and explicit writer
release. A written plan is not implementation or acceptance.

## Phase 1 — agent test foundations

- **AF-23 Framework-neutral agent adapter:** normalize bounded recorded/mock
  trajectories without importing frameworks or executing tools. Later slices
  may add specifically authorized adapters only after isolation review.
- **AF-24 Multi-step trajectory verification:** verify ordered state and evidence
  transitions, partial failures, and deterministic replay across multiple steps.
- **AF-25 Reproducible environments and fixtures:** versioned synthetic fixtures,
  deterministic setup/cleanup, provenance, and environment-drift evidence.

## Phase 2 — failure and concurrency

- **AF-26 Controlled failure injection:** bounded synthetic network, timeout,
  rate-limit, and API faults with no real external calls.
- **AF-27 Recovery, retry, and state consistency:** verify idempotency, crash
  recovery, retry budgets, and durable state invariants.
- **AF-28 Concurrent and multi-agent scenarios:** deterministic scheduling,
  conflict evidence, tenant separation, and bounded resource use.

## Phase 3 — security and diagnosis

- **AF-29 Permission and prompt-injection testing:** fail-closed privilege,
  indirect-injection, data-boundary, and tool-authorization regressions.
- **AF-30 Metrics, budgets, and regressions:** explicit cost/step/time budgets,
  coverage, uncertainty, thresholds, and reproducible change detection.
- **AF-31 Failure classification and diagnosis:** evidence-backed root-cause
  candidates that distinguish correlation from proof and produce replay cases.

## Phase 4 — integrations and release

- **AF-32 CI/CD and authorized project adapters:** least-privilege, read-only
  integrations first; no project data, credentials, or execution without
  separate specific permission.
- **AF-33 Interactive crash-test dashboard:** reviewable runs, evidence, budgets,
  comparisons, and approvals without weakening backend enforcement.
- **AF-34 Security, benchmarks, and beta acceptance:** adversarial validation,
  competitive benchmarks, performance envelopes, documentation, and release
  gates. Beta acceptance is not a production-execution authorization.

## Safety boundary

Recorded/mock adapters come first. AgentFlight must not claim safe arbitrary
untrusted execution until a separately reviewed design proves permission and
resource boundaries, filesystem and network isolation, credential exclusion,
process cleanup, and adversarial tests. No current checkpoint authorizes access
to private projects, networks, hardware, credentials, or external systems.
