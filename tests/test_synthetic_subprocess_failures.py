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

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", fail_launch)
    result = run_synthetic_case("safe-case", "pass")
    assert result["status"] == "error"
    assert result["code"] == "launch_error"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert "SYNTHETIC_SECRET" not in json.dumps(result)
    assert "/private/path" not in json.dumps(result)
    assert result == run_synthetic_case("safe-case", "pass")


def test_timeout_partial_output_never_appears_in_report(monkeypatch):
    def fail_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="SYNTHETIC_SECRET", timeout=0.1,
            output=b"SYNTHETIC_SECRET", stderr=b"SYNTHETIC_SECRET"
        )

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", fail_timeout)
    result = run_synthetic_case("timeout-case", "timeout")
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

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", unexpected_spawn)
    with pytest.raises(SyntheticCaseError):
        run_synthetic_case(case_id, mode, timeout_seconds=timeout)


def test_launch_error_evidence_ignores_exception_details(monkeypatch):
    def fail_first(*args, **kwargs):
        raise subprocess.SubprocessError("SYNTHETIC_SECRET_FIRST")

    def fail_second(*args, **kwargs):
        raise subprocess.SubprocessError("SYNTHETIC_SECRET_SECOND")

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", fail_first)
    first = run_synthetic_case("same-case", "pass")
    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", fail_second)
    second = run_synthetic_case("same-case", "pass")
    assert first == second
    assert "SYNTHETIC_SECRET" not in json.dumps(second)


def test_timeout_evidence_ignores_partial_output_variants(monkeypatch):
    def timeout_first(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="first", timeout=0.1,
                                        output=b"SYNTHETIC_SECRET_FIRST")

    def timeout_second(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="second", timeout=0.2,
                                        output=b"SYNTHETIC_SECRET_SECOND",
                                        stderr=b"SYNTHETIC_SECRET_SECOND")

    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", timeout_first)
    first = run_synthetic_case("same-case", "timeout")
    monkeypatch.setattr("agentflight.synthetic_subprocess.subprocess.run", timeout_second)
    second = run_synthetic_case("same-case", "timeout")
    assert first == second
    assert "SYNTHETIC_SECRET" not in json.dumps(second)
