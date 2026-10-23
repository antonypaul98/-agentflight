# AF-29 — permission and prompt-injection testing

Status: **IN PROGRESS**. The first bounded slice verifies caller-supplied,
recorded authorization decisions against a deterministic fail-closed oracle.

The oracle denies cross-tenant authorization, untrusted-content control,
caller-recorded injection findings, and requests exceeding exact granted scopes.
Reports bind only hashed principal, tenant and input-evidence identities plus
bounded scope identifiers. Raw prompts, payloads and credentials are excluded.

This is synthetic recorded-metadata verification, not an authorization system.
It does not read prompts, inspect projects, invoke tools, execute agents or
commands, access filesystems or networks, grant permissions, or establish an OS
sandbox. Exact Python 3.11 PR and merged-main CI is required before recording
or accepting this slice. AF-29 remains in progress at 6/12.

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
