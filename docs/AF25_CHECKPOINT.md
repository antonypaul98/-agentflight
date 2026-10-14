# AF-25 — Reproducible environments and fixtures

Status: **MERGED_AND_VERIFIED** for bounded recorded fixture environments.

The first bounded slice defines a versioned, metadata-only manifest for a
synthetic fixture environment. It binds the exact Python version, platform,
dependency versions and artifact hashes, plus fixture versions, content hashes,
and bounded sizes into deterministic provenance evidence. Equivalent manifests
normalize identically regardless of input ordering.

A deterministic comparison reports environment, runtime, dependency, and
fixture drift using stable categories and identifiers. Unknown fields fail
closed, including paths, URLs, commands, environment values, credentials, and
fixture payloads. The implementation does not read files or host state, install
packages, execute setup/cleanup, run agents or tools, access projects or
networks, or claim filesystem/process/OS isolation.

This is one independently testable AF-25 source slice, not checkpoint
acceptance. Later slices must address deterministic setup/cleanup evidence and
the remaining acceptance review without widening execution authority.

## Verified first-source receipt — 2026-10-14

- Source PR: #32
- Exact source: `c19c81f3c44cbb14b6516570002a5a30c460899d`
- Exact source tree: `4595315dd15c31b23ad9fe47966bbd702e899ac4`
- Source PR CI: `38528669015` — Python 3.11.17, 341 product tests
  passed, zero failed, zero skipped; infrastructure 17 passed with the one
  established Memory-only skip, and diagnostics passed.
- Guarded merge: `ea36c18fff741a90e5322bd3e13cc3d789e2203e`
- Exact merged-main CI: `38528790850` — Python 3.11.17, 341 product
  tests passed, zero failed, zero skipped; infrastructure and diagnostics
  passed.

This receipt accepts only the bounded metadata-manifest and drift-evidence
source slice. AF-25 remains **IN_PROGRESS**, roadmap progress remains 2/12, and
no setup/cleanup execution, live project access, or isolation authority is
added.

## Recorded lifecycle evidence slice

`verify_fixture_lifecycle` binds caller-supplied setup and cleanup outcome
metadata to one exact normalized environment evidence ID. It requires contiguous
sequence numbers, setup-before-cleanup ordering, both phases, unique phase/step
identities, bounded event counts, exact operation hashes, and explicit success
or failure outcomes. Failures remain redacted to phase and step identifiers.

The verifier executes nothing and accepts no commands, paths, URLs, payloads,
logs, environment values, credentials, or callbacks. It proves only the
consistency of recorded metadata; it does not prove that setup or cleanup ran,
that a host is isolated, or that arbitrary fixture execution is safe. AF-25
remains in progress pending exact-head CI and its remaining acceptance review.

## Verified lifecycle-source receipt — 2026-10-14

- Source PR: #34
- Exact source: `2982797a4112681e3a53c82b46e80311e668d416`
- Exact source tree: `ecc701860154181252a2a72dd215497ce2a134a9`
- Source PR CI: `38535427969` — Python 3.11.17, 354 product tests
  passed, zero failed, zero skipped; infrastructure 17 passed with the one
  established Memory-only skip, and diagnostics passed.
- Guarded merge: `ab4f1478ed53feab510f043fd20e3c2471f0e781`
- Exact merged-main CI: `38535509996` — Python 3.11.17, 354 product
  tests passed, zero failed, zero skipped; infrastructure and diagnostics
  passed.

This receipt accepts only the recorded lifecycle-evidence source slice. AF-25
remains **IN_PROGRESS**, roadmap progress remains 2/12, and no setup/cleanup
execution or isolation authority is added.

## Final scoped acceptance review — 2026-10-14

The roadmap requires versioned synthetic fixtures, deterministic setup/cleanup,
provenance, and environment-drift evidence. The accepted implementation supplies
each required invariant for the bounded recorded-only scope: exact version and
SHA-256 provenance binding, deterministic manifest normalization and drift
classification, plus ordered and complete setup/cleanup outcome evidence bound
to one exact normalized environment.

Source PRs #32 and #34 and records PRs #33 and #35 passed exact-head and
merged-main Linux CI. Final accepted main `6847a346c8249d6d4620613576ba92aef0b5201b`
passed 354 product tests with zero failures or product skips. No additional
AF-25 runtime work is justified for this metadata-only recorded-evidence scope.

AF-25 does not execute setup or cleanup commands, read host state, install
dependencies, run agents or tools, access projects, credentials, networks or
hardware, or establish filesystem, process or OS isolation. Those capabilities
remain separately gated by later checkpoints and specific authorization.

AF-25 is **MERGED_AND_VERIFIED** subject to this records-only closure passing
exact PR-head and merged-main CI. Roadmap progress is 3/12 accepted. AF-26
controlled failure injection is next.
