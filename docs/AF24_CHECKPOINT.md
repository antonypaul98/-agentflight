# AF-24 — Multi-step trajectory verification

Status: **IN_PROGRESS**.

The first bounded slice verifies ordered state transitions in an AF-23
authorized recorded run. Every step after the first must consume the exact
SHA-256 state emitted by its predecessor. A failed or rejected step is terminal
and produces explicit `partial_failure` evidence; later recorded steps fail
closed. Reports bind the exact registry and authorized recorded-run evidence,
initial and terminal state hashes, transition order, coverage, and a stable
evidence identifier.

The verifier retains metadata and hashes only. It does not inspect or
dereference state, prompts, tool arguments or results; import frameworks; read
projects; execute agents, tools or commands; use credentials or networks; or
claim process/OS isolation. This is one source slice, not AF-24 acceptance.

## Verified first-source receipt

- Source PR: #27
- Exact source: `5c5b2ebdad8e6c87c81eb44a81b3b938df14b3bd`
- Exact source tree: `59979a02cd3721b0cfa10439888ed9fa31e6d841`
- Source PR CI: `38477794522` — Python 3.11.17, 314 product tests
  passed, zero failed, zero skipped; infrastructure 17 passed with the one
  established memory-only skip.
- Guarded merge: `ab6584369ae381201caed15941bdc719c28adc61`
- Exact merged-main CI: `38477919301` — Python 3.11.17, 314 product
  tests passed, zero failed, zero skipped; infrastructure 17 passed with the
  one established memory-only skip.

This receipt accepts only the bounded source slice above. AF-24 remains
**IN_PROGRESS**, roadmap progress remains 1/12, and no execution or isolation
authority is added.

## Verified replay-gate source receipt

The next independently testable slice adds an exact-evidence replay gate. A
caller may provide only the SHA-256 evidence identifier from an earlier
verified trajectory; AgentFlight revalidates the registry and fixture from
scratch and fails closed if the reproduced trajectory evidence differs. This
detects recorded state, registry, ordering, terminal-status, and other evidence
drift without retaining or dereferencing payloads.

This slice remains metadata-only. It does not accept prior reports as trusted
input, execute agents or tools, read projects, use credentials or networks, or
claim process/OS isolation.

- Source PR: #29
- Exact source: `f0dfda043dd222faac95f9d8501f54ecaa6e5d9d`
- Exact source tree: `b3adc7d4d54d51623af4c72b28d0dd9f6f912c0d`
- Source PR CI: `38501273784` — Python 3.11.17, 322 product tests
  passed, zero failed, zero skipped; infrastructure 17 passed with the one
  established memory-only skip; diagnostics passed.
- Guarded merge: `2a505c674082144800ab3b0ccf301060037cde05`
- Exact merged-main CI: `38501378546` — Python 3.11.17, 322 product
  tests passed, zero failed, zero skipped; infrastructure 17 passed with the
  one established memory-only skip; diagnostics passed.

The source is merged and verified. Canonical records CI, merge verification,
and explicit bounded-slice release remain pending, so AF-24 stays
**IN_PROGRESS** and roadmap progress stays 1/12.
