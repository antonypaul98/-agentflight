"""Framework-neutral normalization for bounded, recorded agent runs.

This module validates metadata-only fixtures.  It never imports an agent
framework, executes a tool, reads a project, or dereferences recorded hashes.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
MAX_STEPS = 64
MAX_FIXTURE_BYTES = 32_768
AUTHORITY = "recorded_fixture_only"

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_KINDS = frozenset({"model", "tool", "decision", "handoff"})
_STATUSES = frozenset({"passed", "failed", "rejected"})


class RecordedAdapterError(ValueError):
    """The recorded fixture is outside the bounded adapter contract."""


def _exact_keys(value: object, expected: frozenset[str], code: str) -> dict:
    if type(value) is not dict or frozenset(value) != expected:
        raise RecordedAdapterError(code)
    return value


def _identifier(value: object, code: str) -> str:
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise RecordedAdapterError(code)
    return value


def _digest(value: object, code: str) -> str:
    if type(value) is not str or not _SHA256.fullmatch(value):
        raise RecordedAdapterError(code)
    return value


def normalize_recorded_run(fixture: Mapping[str, object]) -> dict:
    """Validate and normalize one metadata-only recorded agent run.

    The returned report retains identifiers, step kinds, verdicts, and exact
    caller-supplied content hashes.  Raw prompts, tool arguments, results,
    paths, commands, environment values, and framework objects are not part of
    the accepted schema and therefore cannot appear in the report.
    """

    root = _exact_keys(
        fixture,
        frozenset({"schema_version", "adapter", "run_id", "steps"}),
        "invalid_fixture_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise RecordedAdapterError("unsupported_schema_version")

    adapter = _exact_keys(
        root["adapter"], frozenset({"adapter_id", "framework"}), "invalid_adapter_shape"
    )
    adapter_id = _identifier(adapter["adapter_id"], "invalid_adapter_id")
    framework = _identifier(adapter["framework"], "invalid_framework")
    run_id = _identifier(root["run_id"], "invalid_run_id")

    steps = root["steps"]
    if type(steps) is not list or not 1 <= len(steps) <= MAX_STEPS:
        raise RecordedAdapterError("invalid_step_count")

    normalized_steps = []
    seen = set()
    step_keys = frozenset(
        {"sequence", "step_id", "kind", "input_sha256", "output_sha256", "status"}
    )
    for expected_sequence, item in enumerate(steps):
        step = _exact_keys(item, step_keys, "invalid_step_shape")
        if type(step["sequence"]) is not int or step["sequence"] != expected_sequence:
            raise RecordedAdapterError("invalid_step_sequence")
        step_id = _identifier(step["step_id"], "invalid_step_id")
        if step_id in seen:
            raise RecordedAdapterError("duplicate_step_id")
        seen.add(step_id)
        kind = step["kind"]
        status = step["status"]
        if type(kind) is not str or kind not in _KINDS:
            raise RecordedAdapterError("invalid_step_kind")
        if type(status) is not str or status not in _STATUSES:
            raise RecordedAdapterError("invalid_step_status")
        normalized_steps.append(
            {
                "sequence": expected_sequence,
                "step_id": step_id,
                "kind": kind,
                "input_sha256": _digest(step["input_sha256"], "invalid_input_hash"),
                "output_sha256": _digest(step["output_sha256"], "invalid_output_hash"),
                "status": status,
            }
        )

    report = {
        "schema_version": SCHEMA_VERSION,
        "adapter_id": adapter_id,
        "framework": framework,
        "run_id": run_id,
        "steps": normalized_steps,
        "authority": AUTHORITY,
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
    if len(canonical.encode("utf-8")) > MAX_FIXTURE_BYTES:
        raise RecordedAdapterError("fixture_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
