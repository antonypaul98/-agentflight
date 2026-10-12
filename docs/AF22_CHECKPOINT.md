# AF-22 — Disposable synthetic subprocess adapter

Status: **MERGED_AND_VERIFIED**. AF-21 remains merged and verified.

This adapter runs only twelve fixed, checked-in synthetic worker modes. It
validates a 1–64 character ASCII case identifier, an allowlisted mode, and a
finite 0.05–2.0 second timeout before spawning anything. No caller-supplied
code, shell command, environment, project path, or external project is run.

## Verified defensive boundaries

- Worker invocation uses the current Python interpreter with `-I -S`, an
  empty environment, a temporary working directory, closed stdin, and
  an isolated POSIX process session.
- Combined stdout/stderr capture is bounded to 1,025 bytes to detect a
  1,024-byte budget overflow without buffering arbitrary worker output.
- Timeouts and oversized output return fixed verdict codes and bounded counts;
  partial timeout output and exception text are never included in reports.
- The isolated process group is terminated on success, failure, timeout,
  and capture exceptions, including after the parent exits but descendants
  remain alive. POSIX-specific regressions verify orphaned-pipe EOF.
- Selector ValueError and subprocess/OS failures are sanitized to a fixed
  `launch_error` verdict, with deterministic case-scoped evidence.
- Invalid inputs are rejected before subprocess creation.

## Exact-commit verification

Implementation: `9a3dffaa2a12e358f7323d1f0a58ed226dd841fd`.
GitHub Actions push CI:
https://github.com/antonypaul98/-agentflight/actions/runs/37951723157

Python 3.11.17: **217 product tests passed**, 0 failed; infrastructure
18 executed with 1 baseline skip; environment diagnostics passed.
Local isolated Python 3.13.5: **57 focused tests passed**, including two
new regressions that failed against the pre-fix selector exception path.

Earlier implementation and CI receipts remain in `docs/AF22_CI_RECEIPT.md`.

## Accepted scope and remaining limits

**Not an OS sandbox or safe runner for untrusted code.** The fixed worker is
allowlisted and does not establish filesystem, network, or credential
isolation guarantees. No arbitrary project execution, real-project crash
testing, hardware acceptance, or cross-platform process-tree isolation is
claimed. Those capabilities require separately authorized future checkpoints;
they are not missing acceptance conditions for this fixed synthetic adapter.

Linux descendant observations now require both the fixed worker's process group
and isolated session, while retaining PID start-time continuity to reject reused
identities. The fixed adapter's input, capture, redaction, timeout, cleanup,
EINTR, fallback, descendant-termination, and deterministic-evidence boundaries
are covered by exact-commit Python 3.11 CI. AF-22 is accepted without expanding
the runner to untrusted inputs.

## Final acceptance review — 2026-10-12 UTC

The acceptance review found every original AF-22 criterion satisfied and no
remaining scoped runtime invariant requiring another repair. PRs #7–#18 retain
the exact source, merge, CI, and acceptance evidence for the defensive slices.
Current accepted main before this records-only closure is
`eb070d2e150dbadaa8f393a0d5f72e15711a18a5`; exact merged-main CI
[#38191409187](https://github.com/antonypaul98/-agentflight/actions/runs/38191409187)
passed 251 product tests with zero failures or product skips on Python 3.11.17.
Infrastructure passed 17 tests with one established Memory-only skip, and
diagnostics passed.

AF-22 therefore closes only the bounded, checked-in synthetic subprocess
adapter. It does not authorize caller-supplied code, commands, projects,
credentials, network access, private data, hardware, or production execution.
