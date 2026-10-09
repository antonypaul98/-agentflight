# AF-22 — Disposable synthetic subprocess adapter (first bounded slice)

Status: DEFENSIVE_SLICE_VERIFIED_ON_MAIN. AF-22 remains IN_PROGRESS; AF-21 is merged and verified.

One isolated synthetic adapter, not a general command runner: `run_synthetic_case`
executes only eight fixed, checked-in worker modes using the current Python
interpreter in isolated mode (`-I -S`) and a temporary working directory.
The caller supplies a bounded case ID, an allowlisted mode and a timeout.
No caller-supplied code, shell, command, project path, or environment is executed.

Acceptance for this first slice:

1. Pass, nonzero exit, timeout, stdout/stderr output limit and interpreter
   launch errors are classified with fixed codes and no exception text.
2. Only 1–64 character ASCII case identifiers and eight fixed modes are allowed;
   timeout must be finite and between 0.05 and 2 seconds. Reject invalid input
   before spawning any subprocess.
3. Subprocess uses `-I -S`, no shell, an empty environment, and a disposable
   directory. It does not run against external projects or access credentials.
4. Reports contain a stable, case-scoped evidence ID, fixed verdict codes and
   clamped output lengths, never stdout/stderr bytes or exception text.
5. Regressions cover boundaries, deterministic evidence, sanitization, real
   process exit/timeout behavior. Launch-failure and timeout-partial-output sanitization regressions
   are included. Exact-commit Python 3.11 CI passed for this defensive slice.

Limits: this is **not** an OS sandbox or secure runner for untrusted Python
code. The fixed synthetic worker is statically limited to 4096 bytes output;
`subprocess.run` still captures bytes in memory before checking the 1024-byte
report limit. Never replace it with arbitrary commands or live project inputs.
No project integration, filesystem/network isolation guarantee, concurrency,
process-tree isolation, real-project crash tests or hardware acceptance.

Defensive slice: combined stdout+stderr reporting budget is 1024 bytes;
subprocess setup failures return fixed `launch_error` without exception text.
Verified commit: `b15df8360993645b40076598854f44268514cb2c`.
Exact-commit push CI: https://github.com/antonypaul98/-agentflight/actions/runs/37904427569
(204 product tests passed; infrastructure and diagnostics succeeded).

Next: implement a separately scoped hard output-capture/process-tree boundary.
The current 1024-byte budget applies to reported results, NOT to bytes held
in memory by `subprocess.run`; this is not an untrusted-code sandbox.
