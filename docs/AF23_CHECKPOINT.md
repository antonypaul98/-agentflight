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
