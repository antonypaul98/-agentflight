"""AF-22: transient pipe-read interruptions must not fail or hang fixed workers."""

import os
import time

import pytest

from agentflight import synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="POSIX worker required")
def test_one_interrupted_read_recovers_without_exposing_error(monkeypatch):
    real_read = adapter.os.read
    interrupted = []

    def read_once_interrupted(fd, count):
        if not interrupted:
            interrupted.append(True)
            raise InterruptedError("transient signal")
        return real_read(fd, count)

    real_capture = adapter._capture_bounded

    def capture_with_interruption(process, timeout_seconds):
        monkeypatch.setattr(adapter.os, "read", read_once_interrupted)
        try:
            return real_capture(process, timeout_seconds)
        finally:
            monkeypatch.setattr(adapter.os, "read", real_read)

    monkeypatch.setattr(adapter, "_capture_bounded", capture_with_interruption)
    result = adapter.run_synthetic_case("eintr-recover", "pass", timeout_seconds=0.5)
    assert interrupted
    assert result["status"] == "passed"
    assert result["code"] == "ok"
    assert result["stdout_bytes"] == len("synthetic-ok\n")


@pytest.mark.skipif(os.name != "posix", reason="POSIX worker required")
def test_repeated_interrupted_reads_obey_deadline_and_redact(monkeypatch):
    interruptions = []

    def always_interrupted(fd, count):
        interruptions.append(True)
        raise InterruptedError("transient signal")

    real_read = adapter.os.read
    real_capture = adapter._capture_bounded

    def capture_with_interruptions(process, timeout_seconds):
        monkeypatch.setattr(adapter.os, "read", always_interrupted)
        try:
            return real_capture(process, timeout_seconds)
        finally:
            monkeypatch.setattr(adapter.os, "read", real_read)

    monkeypatch.setattr(adapter, "_capture_bounded", capture_with_interruptions)
    start = time.monotonic()
    result = adapter.run_synthetic_case("eintr-timeout", "pass", timeout_seconds=0.1)
    elapsed = time.monotonic() - start
    assert interruptions
    assert result["status"] == "timeout"
    assert result["code"] == "timeout"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert elapsed < 1.5
