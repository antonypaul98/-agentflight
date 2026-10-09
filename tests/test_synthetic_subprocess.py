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
    ("secret", "passed", "ok"),
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
