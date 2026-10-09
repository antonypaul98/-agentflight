"""AF-22 fixed-workload subprocess adapter acceptance regressions."""
import json

import pytest

from agentflight.synthetic_subprocess import SyntheticCaseError, run_synthetic_case


@pytest.mark.parametrize("mode,status,code", [
    ("pass", "passed", "ok"),
    ("fail", "failed", "nonzero_exit"),
    ("timeout", "timeout", "timeout"),
    ("stdout_overflow", "failed", "output_limit"),
    ("stderr_overflow", "failed", "output_limit"),
    ("combined_boundary", "passed", "ok"),
    ("combined_overflow", "failed", "output_limit"),
    ("secret", "passed", "ok"),
    ("burst_overflow", "failed", "output_limit"),
    ("timeout_secret", "timeout", "timeout"),
])
def test_fixed_modes(mode, status, code):
    result = run_synthetic_case("synthetic-case", mode, timeout_seconds=0.5)
    assert result["status"] == status and result["code"] == code
    assert result["schema_version"] == 1
    assert len(result["evidence_id"]) == 64
    assert "PRIVATE" not in json.dumps(result)
    assert "synthetic-error" not in json.dumps(result)


def test_report_output_sizes_are_clamped():
    result = run_synthetic_case("bounded", "stdout_overflow")
    assert result["stdout_bytes"] == 1025
    assert result["stderr_bytes"] == 0


def test_evidence_is_deterministic_and_case_scoped():
    first = run_synthetic_case("case-a", "pass")
    assert first == run_synthetic_case("case-a", "pass")
    assert first["evidence_id"] != run_synthetic_case("case-b", "pass")["evidence_id"]
    assert first["evidence_id"] != run_synthetic_case("case-a", "fail")["evidence_id"]


@pytest.mark.parametrize("case_id", ["", "../other", "a b", "a/../b", "a" * 65, None, 3, True])
def test_invalid_case_id(case_id):
    with pytest.raises(SyntheticCaseError, match="invalid_case_id"):
        run_synthetic_case(case_id, "pass")


@pytest.mark.parametrize("mode", ["", "unlisted mode", "pass;unexpected", "PASS", None, 7, True])
def test_invalid_mode(mode):
    with pytest.raises(SyntheticCaseError, match="invalid_mode"):
        run_synthetic_case("case", mode)


@pytest.mark.parametrize("timeout", [0, -1, 0.049, 2.01, float("nan"), float("inf"), True, "1", None])
def test_invalid_timeout(timeout):
    with pytest.raises(SyntheticCaseError, match="invalid_timeout"):
        run_synthetic_case("case", "pass", timeout_seconds=timeout)


def test_combined_output_budget_exact_boundary():
    result = run_synthetic_case("both-exact", "combined_boundary")
    assert result["status"] == "passed"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (512, 512)


def test_combined_output_budget_rejects_split_overflow():
    result = run_synthetic_case("both-over", "combined_overflow")
    assert result["status"] == "failed" and result["code"] == "output_limit"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (512, 513)


def test_large_burst_is_stopped_at_capture_budget():
    result = run_synthetic_case("streaming", "burst_overflow", timeout_seconds=0.5)
    assert result["status"] == "failed" and result["code"] == "output_limit"
    assert result["stdout_bytes"] == 1025
    assert result["stderr_bytes"] == 0


def test_timeout_discards_secret_partial_capture():
    result = run_synthetic_case("partial", "timeout_secret", timeout_seconds=0.1)
    assert result["status"] == "timeout" and result["code"] == "timeout"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert "PRIVATE_TOKEN" not in json.dumps(result)


@pytest.mark.parametrize("mode,expected", [
    ("burst_overflow", "output_limit"),
    ("timeout", "timeout"),
])
def test_early_exit_reaps_worker_process_group(monkeypatch, mode, expected):
    import agentflight.synthetic_subprocess as adapter

    real_cleanup = adapter._kill_process_group
    cleaned = []

    def observed_cleanup(process):
        real_cleanup(process)
        cleaned.append(process.poll())

    monkeypatch.setattr(adapter, "_kill_process_group", observed_cleanup)
    result = run_synthetic_case("cleanup", mode, timeout_seconds=0.2)
    assert result["code"] == expected
    assert len(cleaned) == 1
    assert cleaned[0] is not None


def test_timeout_kills_orphaned_pipe_holding_descendant(monkeypatch):
    """An exited parent must not prevent killing its still-running process group."""
    import agentflight.synthetic_subprocess as adapter

    real_cleanup = adapter._kill_process_group
    parent_exited_before_cleanup = []

    def observed_cleanup(process):
        parent_exited_before_cleanup.append(process.poll() is not None)
        real_cleanup(process)

    monkeypatch.setattr(adapter, "_kill_process_group", observed_cleanup)
    result = run_synthetic_case("orphan-pipe", "orphan_pipe", timeout_seconds=0.25)
    assert result["status"] == "timeout" and result["code"] == "timeout"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert parent_exited_before_cleanup == [True]


def test_timeout_cleanup_is_not_limited_to_live_parent(monkeypatch):
    """The group cleanup is invoked even when a parent exited before timeout."""
    import agentflight.synthetic_subprocess as adapter

    calls = []
    real_cleanup = adapter._kill_process_group

    def observed_cleanup(process):
        calls.append((process.pid, process.poll()))
        real_cleanup(process)

    monkeypatch.setattr(adapter, "_kill_process_group", observed_cleanup)
    result = run_synthetic_case("orphan-again", "orphan_pipe", timeout_seconds=0.25)
    assert result["code"] == "timeout"
    assert len(calls) == 1 and calls[0][1] is not None


def test_orphan_pipe_descendant_really_releases_pipes(monkeypatch):
    """After the parent exits, group cleanup must close a living child's pipes."""
    import os
    import selectors
    import agentflight.synthetic_subprocess as adapter

    real_cleanup = adapter._kill_process_group
    observed = []

    def checked_cleanup(process):
        assert process.poll() is not None  # parent has already exited
        with selectors.DefaultSelector() as selector:
            for stream in (process.stdout, process.stderr):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ)
            # The orphan is still holding both pipes open before cleanup.
            assert selector.select(0) == []
            real_cleanup(process)
            ready = selector.select(0.8)
            assert len(ready) == 2
            for key, _ in ready:
                assert os.read(key.fileobj.fileno(), 1) == b""
        observed.append(True)

    monkeypatch.setattr(adapter, "_kill_process_group", checked_cleanup)
    result = run_synthetic_case("orphan-pipe-eof", "orphan_pipe", timeout_seconds=0.25)
    assert result["code"] == "timeout"
    assert observed == [True]


def test_completed_parent_still_cleans_live_descendant(monkeypatch):
    """A detached-from-pipes child must not survive a successful parent exit."""
    import os
    import agentflight.synthetic_subprocess as adapter

    real_cleanup = adapter._kill_process_group
    observed = []

    def checked_cleanup(process):
        assert process.poll() is not None
        os.killpg(process.pid, 0)  # live descendant holds group open
        real_cleanup(process)
        observed.append(True)

    monkeypatch.setattr(adapter, "_kill_process_group", checked_cleanup)
    result = run_synthetic_case("orphan-closed", "orphan_closed_pipes", timeout_seconds=0.5)
    assert result["status"] == "passed" and result["code"] == "ok"
    assert observed == [True]
