# AF-25 — Reproducible environments and fixtures

Status: **IN_PROGRESS**.

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
