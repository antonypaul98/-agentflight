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
