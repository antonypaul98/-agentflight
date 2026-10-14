"""Deterministic verification for bounded, recorded multi-step trajectories.

This module consumes AF-23 metadata-only evidence. It never executes an agent,
tool, framework, command, or recorded payload and does not provide isolation.
"""

import hashlib
import json
import re
from collections.abc import Mapping

from .agent_adapter import normalize_authorized_recorded_run


TRAJECTORY_SCHEMA_VERSION = 1
TRAJECTORY_AUTHORITY = "recorded_trajectory_verification_only_no_execution"
MAX_TRAJECTORY_REPORT_BYTES = 32_768

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class TrajectoryVerificationError(ValueError):
    """The recorded run violates the bounded trajectory contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def verify_recorded_trajectory(
    registry: Mapping[str, object], fixture: Mapping[str, object]
) -> dict:
    """Verify state continuity and terminal-failure semantics for a recorded run.

    Each step after the first must consume the exact SHA-256 state emitted by
    its predecessor. A failed or rejected step is terminal: it may be retained
    as deterministic partial-failure evidence, but no later step is accepted.
    """

    authorized = normalize_authorized_recorded_run(registry, fixture)
    recorded = authorized["recorded_run"]
    steps = recorded["steps"]
    if len(steps) < 2:
        raise TrajectoryVerificationError("invalid_trajectory_step_count")

    transitions = []
    previous = steps[0]
    for current in steps[1:]:
        if previous["status"] != "passed":
            raise TrajectoryVerificationError("steps_after_terminal_failure")
        if current["input_sha256"] != previous["output_sha256"]:
            raise TrajectoryVerificationError("state_transition_mismatch")
        transitions.append(
            {
                "sequence": current["sequence"] - 1,
                "from_step_id": previous["step_id"],
                "to_step_id": current["step_id"],
                "state_sha256": current["input_sha256"],
            }
        )
        previous = current

    terminal = steps[-1]
    report = {
        "trajectory_schema_version": TRAJECTORY_SCHEMA_VERSION,
        "registry_evidence_id": authorized["registry_evidence_id"],
        "recorded_run_evidence_id": authorized["evidence_id"],
        "adapter_id": authorized["adapter"]["adapter_id"],
        "run_id": recorded["run_id"],
        "initial_state_sha256": steps[0]["input_sha256"],
        "terminal_state_sha256": terminal["output_sha256"],
        "transitions": transitions,
        "terminal": {
            "sequence": terminal["sequence"],
            "step_id": terminal["step_id"],
            "step_status": terminal["status"],
        },
        "verdict": "complete" if terminal["status"] == "passed" else "partial_failure",
        "coverage": {
            "observed_steps": len(steps),
            "verified_transitions": len(transitions),
            "scope": "recorded_hash_linkage_only",
        },
        "authority": TRAJECTORY_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_TRAJECTORY_REPORT_BYTES:
        raise TrajectoryVerificationError("trajectory_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def verify_recorded_trajectory_replay(
    registry: Mapping[str, object],
    fixture: Mapping[str, object],
    expected_evidence_id: str,
) -> dict:
    """Replay verification and fail closed unless exact evidence is reproduced.

    The expected value is only the SHA-256 evidence identifier from an earlier
    verified trajectory. The fixture is revalidated from scratch; no prior
    report, recorded payload, framework, or executable object is accepted.
    """

    if type(expected_evidence_id) is not str or not _SHA256.fullmatch(
        expected_evidence_id
    ):
        raise TrajectoryVerificationError(
            "invalid_expected_trajectory_evidence_id"
        )
    report = verify_recorded_trajectory(registry, fixture)
    if report["evidence_id"] != expected_evidence_id:
        raise TrajectoryVerificationError("trajectory_replay_mismatch")
    return report
