"""AF-22: interruptions after pipe EOF retain the original capture deadline."""

import os
from types import SimpleNamespace

import pytest

from agentflight import synthetic_subprocess as adapter

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX pipe capture required")


@pytest.fixture
def capture_process(monkeypatch):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(adapter, "time", SimpleNamespace(monotonic=lambda: clock.now))
    streams = []
    for output in (b"synthetic-ok\n", b""):
        read_fd, write_fd = os.pipe()
        try:
            if output:
                os.write(write_fd, output)
        finally:
            os.close(write_fd)
        streams.append(os.fdopen(read_fd, "rb"))

    class Process:
        stdout, stderr = streams
        returncode = None

        def __init__(self):
            self.timeouts = []
            self.on_wait = None

        def wait(self, *, timeout):
            self.timeouts.append(timeout)
            return self.on_wait()

        def poll(self):
            return self.returncode

    process = Process()
    try:
        yield process, clock
    finally:
        for stream in streams:
            stream.close()


def test_wait_interruption_recovers_after_eof_without_resetting_deadline(capture_process):
    process, clock = capture_process

    def wait():
        if len(process.timeouts) == 1:
            clock.now += 0.2
            raise InterruptedError("synthetic transient signal")
        process.returncode = 0
        return 0

    process.on_wait = wait
    assert adapter._capture_bounded(process, 0.5) == ("completed", (13, 0))
    assert process.timeouts == pytest.approx([0.5, 0.3])


def test_repeated_wait_interruptions_stop_at_original_deadline(capture_process):
    process, clock = capture_process

    def wait():
        if len(process.timeouts) > 4:
            pytest.fail("wait interruptions extended the original deadline")
        clock.now += 0.2
        raise InterruptedError("SYNTHETIC_PRIVATE_TOKEN_931")

    process.on_wait = wait
    assert adapter._capture_bounded(process, 0.5) == ("timeout", (0, 0))
    assert 1 < len(process.timeouts) <= 4
    assert process.timeouts[-1] < process.timeouts[0]
    assert clock.now < 100.9


def test_wait_timeout_after_interruption_redacts_partial_counts(capture_process):
    process, clock = capture_process

    def wait():
        if len(process.timeouts) == 1:
            clock.now += 0.1
            raise InterruptedError("SYNTHETIC_PRIVATE_TOKEN_931")
        raise adapter.subprocess.TimeoutExpired("synthetic-worker", process.timeouts[-1])

    process.on_wait = wait
    assert adapter._capture_bounded(process, 0.5) == ("timeout", (0, 0))
    assert process.timeouts == pytest.approx([0.5, 0.4])
