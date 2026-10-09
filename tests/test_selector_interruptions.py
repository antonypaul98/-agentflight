"""AF-22 regressions: selector EINTR must not change the capture deadline."""
import os
import time

import pytest

import agentflight.synthetic_subprocess as adapter


@pytest.mark.skipif(os.name != "posix", reason="fixed worker requires POSIX")
def test_one_selector_interruption_is_retried(monkeypatch):
    factory = adapter.selectors.DefaultSelector
    calls = []

    def interrupted_factory():
        selector = factory()
        real_select = selector.select

        def interrupted_once(timeout=None):
            calls.append(timeout)
            if len(calls) == 1:
                raise InterruptedError("private selector diagnostic must not leak")
            return real_select(timeout)

        selector.select = interrupted_once
        return selector

    monkeypatch.setattr(adapter.selectors, "DefaultSelector", interrupted_factory)
    result = adapter.run_synthetic_case("selector-eintr-once", "pass", timeout_seconds=0.5)
    assert result["status"] == "passed" and result["code"] == "ok"
    assert len(calls) >= 2
    assert "private" not in str(result)


@pytest.mark.skipif(os.name != "posix", reason="fixed worker requires POSIX")
def test_repeated_selector_interruptions_obey_original_deadline(monkeypatch):
    factory = adapter.selectors.DefaultSelector
    calls = []

    def interrupted_factory():
        selector = factory()

        def always_interrupted(timeout=None):
            calls.append(timeout)
            raise InterruptedError("private selector diagnostic must not leak")

        selector.select = always_interrupted
        return selector

    monkeypatch.setattr(adapter.selectors, "DefaultSelector", interrupted_factory)
    start = time.monotonic()
    result = adapter.run_synthetic_case("selector-eintr-loop", "timeout", timeout_seconds=0.1)
    elapsed = time.monotonic() - start
    assert result["status"] == "timeout" and result["code"] == "timeout"
    assert (result["stdout_bytes"], result["stderr_bytes"]) == (0, 0)
    assert len(calls) > 1
    assert elapsed < 1.5
    assert "private" not in str(result)
