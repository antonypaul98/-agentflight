# AF-22 — Disposable synthetic subprocess adapter (first bounded slice)

Status: IMPLEMENTED_AWAITING_EXACT_COMMIT_CI. AF-21 remains merged and verified.

One isolated synthetic adapter, not a general command runner: `run_synthetic_case`
executes only six fixed, checked-in worker modes using the current Python
interpreter in isolated mode (`-I -S`) and a temporary working directory.
The caller supplies a bounded case ID, an allowlisted mode and a timeout.
No caller-supplied code, shell, command, project path, or environment is executed.

Acceptance for this first slice:

1. Pass, nonzero exit, timeout, stdout/stderr output limit and interpreter
   launch errors are classified with fixed codes and no exception text.
2. Only 1–64 character ASCII case identifiers and six fixed modes are allowed;
   timeout must be finite and between 0.05 and 2 seconds. Reject invalid input
   before spawning any subprocess.
3. Subprocess uses `-I -S`, no shell, an empty environment, and a disposable
   directory. It does not run against external projects or access credentials.
4. Reports contain a stable, case-scoped evidence ID, fixed verdict codes and
   clamped output lengths, never stdout/stderr bytes or exception text.
5. Regressions cover boundaries, deterministic evidence, sanitization, real
   process exit/timeout behavior. A launch-failure injection regression remains
   for a later bounded slice. Exact-commit Python 3.11
   CI is required before acceptance.

Limits: this is **not** an OS sandbox or secure runner for untrusted Python
code. The fixed synthetic worker is statically limited to 4096 bytes output;
`subprocess.run` still captures bytes in memory before checking the 1024-byte
report limit. Never replace it with arbitrary commands or live project inputs.
No project integration, filesystem/network isolation guarantee, concurrency,
process-tree isolation, real-project crash tests or hardware acceptance.

Next: verify exact-commit CI, reconcile `CHECKPOINT_STATE.json`, and only then
consider a separately scoped hard output-capture/process-tree boundary.
