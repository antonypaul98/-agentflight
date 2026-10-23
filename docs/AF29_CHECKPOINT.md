# AF-29 — permission and prompt-injection testing

Status: **IN PROGRESS**. The first bounded slice verifies caller-supplied,
recorded authorization decisions against a deterministic fail-closed oracle.
The current bounded candidate adds exact, content-addressed instruction
provenance over that recomputed authorization evidence.

The oracle denies cross-tenant authorization, untrusted-content control,
caller-recorded injection findings, and requests exceeding exact granted scopes.
Reports bind only hashed principal, tenant and input-evidence identities plus
bounded scope identifiers. Raw prompts, payloads and credentials are excluded.

This is synthetic recorded-metadata verification, not an authorization system.
It does not read prompts, inspect projects, invoke tools, execute agents or
commands, access filesystems or networks, grant permissions, or establish an OS
sandbox. Exact Python 3.11 PR and merged-main CI is required before recording
or accepting this slice. AF-29 remains in progress at 6/12.

## Recorded instruction-provenance candidate

The candidate accepts only a trusted-control instruction hash matching the
recorded trusted hash, an exact recomputed security-probe evidence identifier,
an underlying authorization decision that passes and permits authorization,
and no caller-recorded policy-override attempt. Untrusted instruction sources,
hash substitution, denial-required probes, inconsistent decisions, override
attempts, malformed metadata and action-bearing fields fail closed.

Only hashes, bounded identifiers, booleans and dispositions are processed. The
verifier never reads instruction or prompt text, detects injections itself,
authorizes or invokes a tool, or accesses a project, filesystem, network,
credential, payload or external system. Exact Python 3.11 PR and merged-main CI
remain required before a source receipt can be recorded or the writer released.

## Recorded instruction-provenance source receipt

PR #70 head `18d326c096671988f34162d98f2ed48e0344f2e9`, tree
`c6bd70346fdf515bbbf29c781a7c6db381a4bb95`, passed exact-head run
39939002114 on Python 3.11.17 with 516 product tests and zero product
skips. Guarded merge produced main `d3f8723f2269d22e905533df8aaeb3187af92dea`;
exact push run 39939139774 passed the same 516-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped.

The slice remains limited to deterministic fail-closed verification of bounded,
caller-supplied recorded hashes and dispositions. It reads no raw instruction,
prompt, payload or credential; grants no permission; and performs no project
inspection, injection detection, tool/agent/command execution,
filesystem/network access, external action, resource enforcement or OS-sandbox
validation. AF-29 remains in progress and roadmap acceptance remains 6/12.

## Permission-boundary source receipt

PR #68 head `01d73281f39afb7338137f3df10d6d29a8cf8b59`, tree
`7f6ba51744545bfc10902e4f907439afa73b0545`, passed exact-head run
39900570012 on Python 3.11.17 with 504 product tests and zero product
skips. Guarded merge produced main `5330726fd81bf1b6071fdd72b825e89ed47edd6b`;
exact push run 39900701428 passed the same 504-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped.

The slice is limited to deterministic fail-closed verification of caller-supplied
recorded tenant, scope, trust-boundary and injection decisions. It reads no raw
prompts, payloads or credentials; grants no permissions; and performs no
project inspection, tool/agent/command execution, filesystem/network access,
external action, resource enforcement or OS-sandbox validation. AF-29 remains
in progress and roadmap acceptance remains 6/12.
