# AF-23 — Framework-neutral agent adapter

Status: **IN_PROGRESS**.

The first bounded slice validates and normalizes metadata-only recorded agent
runs. It accepts one exact schema shared by recorded fixtures from different
frameworks, binds every step to caller-supplied SHA-256 input/output digests,
enforces deterministic sequence and unique identifiers, and emits a stable
evidence identifier.

The accepted fixture schema has no field for prompts, tool arguments, results,
commands, paths, environment values, credentials, callbacks, or framework
objects. Unknown fields fail closed. Runs are limited to 64 steps and reports
carry `recorded_fixture_only` authority.

This slice does not import an agent framework, execute an agent or tool, read a
project, dereference a digest, access a network, or provide an OS sandbox.
Later AF-23 slices must define authorized adapter registration and verify
adapter conformance without weakening these boundaries before the checkpoint
can be accepted.

## Authorized recorded-adapter registry

The second bounded slice adds a fail-closed registry for metadata-only recorded
adapters. Each entry binds an adapter identifier and framework to a versioned,
externally reviewed contract SHA-256 digest and the sole supported mode
`recorded_fixture`. Registries are deterministically ordered, limited to 32
unique adapters, and carry their own stable evidence identity.

`normalize_authorized_recorded_run` requires the recorded fixture's adapter and
framework to match an exact registry entry, then binds the registry evidence,
contract version/hash, and normalized recorded-run evidence into one stable
report. Registry fields for modules, entry points, commands, paths, callbacks,
credentials, configuration, or other runtime objects fail closed.

This remains an offline conformance boundary. It does not resolve the contract
digest, import a framework, access a project, execute an agent/tool, use a
network or credential, or claim process/OS isolation. AF-23 remains in progress;
versioned conformance fixtures and adversarial compatibility evidence are still
required before checkpoint acceptance.

## First source slice verified — 2026-10-13

Source head `e527f30390c6ca2f0fdf9455fee2048d4198066e`, exact tree
`d07a115d3f285fdfc32aecff41661a8e39e4d574`, passed exact PR-event CI
[#38390138733](https://github.com/antonypaul98/-agentflight/actions/runs/38390138733).
Python 3.11.17 reported 267 product tests passed, zero failed, and zero skipped;
infrastructure passed 17 tests with one established Memory-only skip, and
diagnostics passed. Guarded PR #20 merge
`a4471303d92047ed027c46a223e48f0a1747336a` passed exact merged-main CI
[#38390222096](https://github.com/antonypaul98/-agentflight/actions/runs/38390222096)
with the same 267/0/0 product result.

Pinned local Python 3.11.17 validation passed 16 focused AF-23 tests and 265
product tests with the two established container-specific `/proc` observation
cases excluded; dependency, diagnostics, compilation and whitespace checks
passed. This receipt verifies one bounded source slice, not AF-23 completion.

## Second source slice verified — 2026-10-13

Source head `3adf61f11bd3d216703f06eac28b33932b64d5f4`, exact tree
`be57f590aec92552cfb481998b707a0045f09f7d`, passed exact PR-event CI
[#38430295837](https://github.com/antonypaul98/-agentflight/actions/runs/38430295837).
Python 3.11.17 reported 288 product tests passed, zero failed, and zero skipped;
infrastructure passed 17 tests with one established Memory-only skip, and
diagnostics passed. Guarded PR #22 merge
`06ca355b85c56a54c725b05e38d0de9a3de05bbf` passed exact merged-main CI
[#38430473722](https://github.com/antonypaul98/-agentflight/actions/runs/38430473722)
with the same 288/0/0 product result.

Pinned local Python 3.11.17 validation passed 37 focused AF-23 tests and 286
product tests with the two established container-specific `/proc` observation
cases excluded; dependency, diagnostics, compilation and whitespace checks
passed. This receipt verifies the bounded recorded-adapter registry and exact
contract/run binding only. It grants no live adapter, framework import, project
access, credential, network, execution, or sandbox authority, and AF-23 remains
in progress.
