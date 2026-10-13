"""Framework-neutral normalization for bounded, recorded agent runs.

This module validates metadata-only fixtures.  It never imports an agent
framework, executes a tool, reads a project, or dereferences recorded hashes.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
REGISTRY_SCHEMA_VERSION = 1
CONFORMANCE_SCHEMA_VERSION = 1
MAX_STEPS = 64
MAX_REGISTERED_ADAPTERS = 32
MAX_CONFORMANCE_CASES = 64
MAX_FIXTURE_BYTES = 32_768
MAX_REGISTRY_BYTES = 32_768
AUTHORITY = "recorded_fixture_only"
REGISTRY_AUTHORITY = "authorized_registry_metadata_only_no_execution"
AUTHORIZED_AUTHORITY = "authorized_recorded_fixture_only_no_execution"
CONFORMANCE_AUTHORITY = "conformance_evidence_only_no_execution"

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_KINDS = frozenset({"model", "tool", "decision", "handoff"})
_STATUSES = frozenset({"passed", "failed", "rejected"})


class RecordedAdapterError(ValueError):
    """The recorded fixture is outside the bounded adapter contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


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
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_FIXTURE_BYTES:
        raise RecordedAdapterError("fixture_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def normalize_adapter_registry(registry: Mapping[str, object]) -> dict:
    """Validate an explicit registry of metadata-only recorded adapters.

    Registration describes identity and an externally reviewed contract digest.
    There is deliberately no module, entry point, command, callback, path,
    credential, configuration, or runtime object in this schema.
    """

    root = _exact_keys(
        registry,
        frozenset({"schema_version", "registry_id", "adapters"}),
        "invalid_registry_shape",
    )
    if (type(root["schema_version"]) is not int
            or root["schema_version"] != REGISTRY_SCHEMA_VERSION):
        raise RecordedAdapterError("unsupported_registry_schema_version")
    registry_id = _identifier(root["registry_id"], "invalid_registry_id")
    adapters = root["adapters"]
    if (type(adapters) is not list
            or not 1 <= len(adapters) <= MAX_REGISTERED_ADAPTERS):
        raise RecordedAdapterError("invalid_registered_adapter_count")

    adapter_keys = frozenset(
        {"adapter_id", "framework", "adapter_version", "contract_sha256", "mode"}
    )
    normalized = []
    seen = set()
    for item in adapters:
        adapter = _exact_keys(item, adapter_keys, "invalid_registered_adapter_shape")
        adapter_id = _identifier(adapter["adapter_id"], "invalid_registered_adapter_id")
        if adapter_id in seen:
            raise RecordedAdapterError("duplicate_registered_adapter_id")
        seen.add(adapter_id)
        if type(adapter["mode"]) is not str or adapter["mode"] != "recorded_fixture":
            raise RecordedAdapterError("unsupported_adapter_mode")
        normalized.append(
            {
                "adapter_id": adapter_id,
                "framework": _identifier(adapter["framework"], "invalid_registered_framework"),
                "adapter_version": _identifier(
                    adapter["adapter_version"], "invalid_adapter_version"
                ),
                "contract_sha256": _digest(
                    adapter["contract_sha256"], "invalid_contract_hash"
                ),
                "mode": "recorded_fixture",
            }
        )

    normalized.sort(key=lambda item: item["adapter_id"])
    report = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_id": registry_id,
        "adapters": normalized,
        "authority": REGISTRY_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_REGISTRY_BYTES:
        raise RecordedAdapterError("registry_too_large")
    report["registry_evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def normalize_authorized_recorded_run(
    registry: Mapping[str, object], fixture: Mapping[str, object]
) -> dict:
    """Bind one recorded run to an exact authorized registry entry.

    This function only validates metadata.  It does not import the named
    framework, resolve the contract digest, read a project, or execute anything.
    """

    normalized_registry = normalize_adapter_registry(registry)
    normalized_run = normalize_recorded_run(fixture)
    matched = [
        adapter for adapter in normalized_registry["adapters"]
        if adapter["adapter_id"] == normalized_run["adapter_id"]
    ]
    if not matched:
        raise RecordedAdapterError("adapter_not_authorized")
    adapter = matched[0]
    if adapter["framework"] != normalized_run["framework"]:
        raise RecordedAdapterError("authorized_framework_mismatch")

    report = {
        "registry_schema_version": REGISTRY_SCHEMA_VERSION,
        "registry_id": normalized_registry["registry_id"],
        "registry_evidence_id": normalized_registry["registry_evidence_id"],
        "adapter": adapter,
        "recorded_run": normalized_run,
        "authority": AUTHORIZED_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_FIXTURE_BYTES + MAX_REGISTRY_BYTES:
        raise RecordedAdapterError("authorized_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def normalize_conformance_suite(
    registry: Mapping[str, object], suite: Mapping[str, object]
) -> dict:
    """Verify versioned positive and adversarial recorded-fixture cases.

    A conformance suite can prove only that metadata fixtures satisfy or fail
    the local validator as declared. It cannot load the named framework,
    resolve a contract digest, inspect a project, or execute an agent or tool.
    Rejected fixture content is never copied into the returned evidence.
    """

    normalized_registry = normalize_adapter_registry(registry)
    root = _exact_keys(
        suite,
        frozenset(
            {
                "schema_version",
                "suite_id",
                "registry_evidence_id",
                "adapter_id",
                "adapter_version",
                "contract_sha256",
                "cases",
            }
        ),
        "invalid_conformance_suite_shape",
    )
    if (type(root["schema_version"]) is not int
            or root["schema_version"] != CONFORMANCE_SCHEMA_VERSION):
        raise RecordedAdapterError("unsupported_conformance_schema_version")
    suite_id = _identifier(root["suite_id"], "invalid_conformance_suite_id")
    registry_evidence_id = _digest(
        root["registry_evidence_id"], "invalid_registry_evidence_id"
    )
    if registry_evidence_id != normalized_registry["registry_evidence_id"]:
        raise RecordedAdapterError("conformance_registry_mismatch")

    adapter_id = _identifier(root["adapter_id"], "invalid_conformance_adapter_id")
    matches = [
        item for item in normalized_registry["adapters"]
        if item["adapter_id"] == adapter_id
    ]
    if not matches:
        raise RecordedAdapterError("conformance_adapter_not_authorized")
    adapter = matches[0]
    adapter_version = _identifier(
        root["adapter_version"], "invalid_conformance_adapter_version"
    )
    contract_sha256 = _digest(
        root["contract_sha256"], "invalid_conformance_contract_hash"
    )
    if adapter_version != adapter["adapter_version"]:
        raise RecordedAdapterError("conformance_adapter_version_mismatch")
    if contract_sha256 != adapter["contract_sha256"]:
        raise RecordedAdapterError("conformance_contract_mismatch")

    cases = root["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= MAX_CONFORMANCE_CASES:
        raise RecordedAdapterError("invalid_conformance_case_count")
    case_keys = frozenset(
        {"sequence", "case_id", "expectation", "expected_error", "fixture"}
    )
    normalized_cases = []
    seen = set()
    accepted = rejected = 0
    for expected_sequence, item in enumerate(cases):
        case = _exact_keys(item, case_keys, "invalid_conformance_case_shape")
        if type(case["sequence"]) is not int or case["sequence"] != expected_sequence:
            raise RecordedAdapterError("invalid_conformance_case_sequence")
        case_id = _identifier(case["case_id"], "invalid_conformance_case_id")
        if case_id in seen:
            raise RecordedAdapterError("duplicate_conformance_case_id")
        seen.add(case_id)
        expectation = case["expectation"]
        expected_error = case["expected_error"]
        if expectation == "accept":
            if expected_error is not None:
                raise RecordedAdapterError("invalid_conformance_expectation")
        elif expectation == "reject":
            expected_error = _identifier(
                expected_error, "invalid_conformance_expected_error"
            )
        else:
            raise RecordedAdapterError("invalid_conformance_expectation")

        try:
            authorized = normalize_authorized_recorded_run(registry, case["fixture"])
        except RecordedAdapterError as exc:
            actual_error = str(exc)
            if expectation != "reject":
                raise RecordedAdapterError("conformance_acceptance_failed") from exc
            if actual_error != expected_error:
                raise RecordedAdapterError("conformance_error_mismatch") from exc
            rejected += 1
            normalized_cases.append(
                {
                    "sequence": expected_sequence,
                    "case_id": case_id,
                    "expectation": "reject",
                    "observed_error": actual_error,
                    "status": "passed",
                }
            )
        else:
            if expectation != "accept":
                raise RecordedAdapterError("conformance_rejection_not_observed")
            accepted += 1
            normalized_cases.append(
                {
                    "sequence": expected_sequence,
                    "case_id": case_id,
                    "expectation": "accept",
                    "recorded_run_evidence_id": authorized["evidence_id"],
                    "status": "passed",
                }
            )

    report = {
        "conformance_schema_version": CONFORMANCE_SCHEMA_VERSION,
        "suite_id": suite_id,
        "registry_evidence_id": registry_evidence_id,
        "adapter": adapter,
        "cases": normalized_cases,
        "coverage": {
            "total": len(normalized_cases),
            "accepted": accepted,
            "rejected": rejected,
        },
        "authority": CONFORMANCE_AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_FIXTURE_BYTES + MAX_REGISTRY_BYTES:
        raise RecordedAdapterError("conformance_report_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report
