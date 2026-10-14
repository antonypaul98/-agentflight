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
