"""AF-22: spurious nonblocking EAGAIN regression."""
import errno
import os
import time
import pytest
import agentflight.synthetic_subprocess as adapter

class ReadRaceOS:
    def __init__(self, read):
        self.read = read
    def __getattr__(self, name):
        return getattr(os, name)

@pytest.mark.skipif(os.name != "posix", reason="POSIX worker required")
def test_eagain_once(monkeypatch):
    calls = []
    def flaky_read(fd, size):
        calls.append(size)
        if len(calls) == 1:
            raise BlockingIOError(errno.EAGAIN, "private transient read error")
        return os.read(fd, size)
    monkeypatch.setattr(adapter, "os", ReadRaceOS(flaky_read))
    result = adapter.run_synthetic_case("eagain-once", "pass", timeout_seconds=0.5)
    assert result["code"] == "ok" and len(calls) >= 2

@pytest.mark.skipif(os.name != "posix", reason="POSIX worker required")
def test_eagain_repeated_bounded(monkeypatch):
    calls = []
    def blocked_read(fd, size):
        calls.append(size)
        raise BlockingIOError(errno.EAGAIN, "private persistent read error")
    monkeypatch.setattr(adapter, "os", ReadRaceOS(blocked_read))
    start = time.monotonic()
    result = adapter.run_synthetic_case("eagain-loop", "pass", timeout_seconds=0.25)
    assert result["code"] == "timeout"
    assert result["stdout_bytes"] == result["stderr_bytes"] == 0
    assert len(calls) >= 2
    assert time.monotonic() - start < 1.5
