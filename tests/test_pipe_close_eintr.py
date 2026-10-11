"""AF-22: pipe cleanup must handle EINTR without leaking or hanging."""

import json

import agentflight.synthetic_subprocess as adapter


class InterruptingClose:
    def __init__(self, stream, interruptions):
        self.stream = stream
        self.interruptions = interruptions
        self.close_calls = 0

    def fileno(self):
        return self.stream.fileno()

    def close(self):
        self.close_calls += 1
        if self.close_calls <= self.interruptions:
            raise InterruptedError("SYNTHETIC_PRIVATE_TOKEN_931")
        self.stream.close()


def test_transient_pipe_close_eintr_preserves_verdict(monkeypatch):
    real_popen = adapter.subprocess.Popen
    wrapped = []

    def observed_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        process.stdout = InterruptingClose(process.stdout, interruptions=1)
        wrapped.append(process.stdout)
        return process

    monkeypatch.setattr(adapter.subprocess, "Popen", observed_popen)
    result = adapter.run_synthetic_case("close-eintr", "pass")

    assert result["status"] == "passed" and result["code"] == "ok"
    assert wrapped[0].close_calls == 2
    assert wrapped[0].stream.closed


def test_persistent_pipe_close_eintr_is_bounded_and_redacted(monkeypatch):
    real_popen = adapter.subprocess.Popen
    seen = []

    def observed_popen(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        process.stdout = InterruptingClose(process.stdout, interruptions=3)
        seen.append(process)
        return process

    monkeypatch.setattr(adapter.subprocess, "Popen", observed_popen)
    result = adapter.run_synthetic_case("close-eintr-limit", "pass")

    assert result["status"] == "error" and result["code"] == "launch_error"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert seen[0].stdout.close_calls == 3
    assert seen[0].stderr.closed
    assert "PRIVATE_TOKEN" not in json.dumps(result)
