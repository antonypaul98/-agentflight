# AF-22 — Disposable synthetic subprocess adapter

Status: **IN_PROGRESS**. AF-21 remains merged and verified.

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

## Remaining limits and next work

**Not an OS sandbox or safe runner for untrusted code.** The fixed worker is
allowlisted and does not establish filesystem, network, or credential
isolation guarantees. No arbitrary project execution, real-project crash
testing, hardware acceptance, or cross-platform process-tree isolation is
claimed. AF-22 acceptance remains open.

Next: strengthen Linux descendant-termination assertions, cover additional
exceptional cleanup paths, and review AF-22 acceptance without expanding
the runner to untrusted inputs.
