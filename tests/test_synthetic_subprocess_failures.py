"""AF-22: fixed subprocess failures must remain sanitized and deterministic."""

import json
import subprocess

import pytest

from agentflight.synthetic_subprocess import SyntheticCaseError, run_synthetic_case


@pytest.mark.parametrize("error", [
    OSError("/private/path/SYNTHETIC_SECRET"),
    subprocess.SubprocessError("SYNTHETIC_SECRET process setup failed"),
])
def test_launch_failures_return_redacted_fixed_code(monkeypatch, error):
    def fail_launch(*args, **kwargs):
        raise error

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.Popen", fail_launch)
    result = run_synthetic_case("safe-case", "pass")
    assert result["status"] == "error"
    assert result["code"] == "launch_error"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert "/private/path" not in json.dumps(result)
    assert result == run_synthetic_case("safe-case", "pass")


def test_timeout_partial_output_never_appears_in_report():
    result = run_synthetic_case("timeout-case", "timeout_secret", timeout_seconds=0.1)
    assert result["status"] == "timeout" and result["code"] == "timeout"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert "SYNTHETIC_SECRET" not in json.dumps(result)


@pytest.mark.parametrize("case_id,mode,timeout", [
    ("../unsafe", "pass", 1.0),
    ("safe", "shell-command", 1.0),
    ("safe", "pass", float("inf")),
])
def test_invalid_input_never_spawns_process(monkeypatch, case_id, mode, timeout):
    def unexpected_spawn(*args, **kwargs):
        pytest.fail("invalid input reached subprocess")

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.Popen", unexpected_spawn)
    with pytest.raises(SyntheticCaseError):
        run_synthetic_case(case_id, mode, timeout_seconds=timeout)


def test_launch_error_evidence_ignores_exception_details(monkeypatch):
    def fail_first(*args, **kwargs):
        raise subprocess.SubprocessError("SYNTHETIC_SECRET_FIRST")

    def fail_second(*args, **kwargs):
        raise subprocess.SubprocessError("SYNTHETIC_SECRET_SECOND")

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.Popen", fail_first)
    first = run_synthetic_case("same-case", "pass")
    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.Popen", fail_second)
    second = run_synthetic_case("same-case", "pass")
    assert first == second
    assert "SYNTHETIC_SECRET" not in json.dumps(second)


def test_timeout_evidence_ignores_partial_output_variants():
    first = run_synthetic_case("same-case", "timeout", timeout_seconds=0.1)
    second = run_synthetic_case("same-case", "timeout_secret", timeout_seconds=0.1)
    # Evidence includes the allowlisted mode, but not any partial output.
    assert first["status"] == second["status"] == "timeout"
    assert (first["stdout_bytes"], first["stderr_bytes"]) == (0, 0)
    assert (second["stdout_bytes"], second["stderr_bytes"]) == (0, 0)
    assert "SYNTHETIC_SECRET" not in json.dumps(second)


def test_capture_read_error_is_redacted_and_reaps_worker(monkeypatch):
    """A pipe-read failure must not leak details or strand the worker."""
    import agentflight.synthetic_subprocess as adapter

    real_cleanup = adapter._kill_process_group
    reaped = []

    def broken_capture(process, timeout_seconds):
        raise OSError("SYNTHETIC_SECRET pipe-read failed")

    def observed_cleanup(process):
        real_cleanup(process)
        reaped.append(process.poll())

    monkeypatch.setattr(adapter, "_capture_bounded", broken_capture)
    monkeypatch.setattr(adapter, "_kill_process_group", observed_cleanup)
    result = run_synthetic_case("read-failure", "timeout")
    assert result["status"] == "error"
    assert result["code"] == "launch_error"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert len(reaped) == 1 and reaped[0] is not None
