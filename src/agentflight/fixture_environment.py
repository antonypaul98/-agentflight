"""Deterministic metadata for versioned synthetic fixture environments.

This validates caller-supplied metadata only. It never reads fixture files,
inspects a host, installs dependencies, runs setup/cleanup, or executes code.
"""

import hashlib
import json
import re
from collections.abc import Mapping


SCHEMA_VERSION = 1
MAX_DEPENDENCIES = 64
MAX_FIXTURES = 128
MAX_MANIFEST_BYTES = 65_536
AUTHORITY = "synthetic_fixture_metadata_only_no_environment_execution"
DRIFT_AUTHORITY = "synthetic_environment_drift_evidence_only_no_execution"

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_VERSION = re.compile(r"[0-9][A-Za-z0-9_.+-]{0,31}\Z")
_PYTHON_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class FixtureEnvironmentError(ValueError):
    """The manifest is outside the bounded synthetic-fixture contract."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _exact_keys(value: object, expected: frozenset[str], code: str) -> dict:
    if type(value) is not dict or frozenset(value) != expected:
        raise FixtureEnvironmentError(code)
    return value


def _text(value: object, pattern: re.Pattern[str], code: str) -> str:
    if type(value) is not str or not pattern.fullmatch(value):
        raise FixtureEnvironmentError(code)
    return value


def _bounded_list(value: object, maximum: int, code: str) -> list:
    if type(value) is not list or not 1 <= len(value) <= maximum:
        raise FixtureEnvironmentError(code)
    return value


def normalize_fixture_environment(manifest: Mapping[str, object]) -> dict:
    """Normalize a bounded, versioned synthetic-fixture manifest.

    Only identifiers, versions, sizes, and caller-supplied SHA-256 digests are
    accepted. Paths, URLs, payloads, commands, environment values, credentials,
    callbacks, and executable objects have no place in the schema.
    """

    root = _exact_keys(
        manifest,
        frozenset({"schema_version", "environment_id", "environment_version",
                   "runtime", "dependencies", "fixtures"}),
        "invalid_environment_shape",
    )
    if type(root["schema_version"]) is not int or root["schema_version"] != SCHEMA_VERSION:
        raise FixtureEnvironmentError("unsupported_environment_schema_version")

    runtime = _exact_keys(
        root["runtime"], frozenset({"python_version", "platform"}), "invalid_runtime_shape"
    )
    normalized_runtime = {
        "python_version": _text(
            runtime["python_version"], _PYTHON_VERSION, "invalid_python_version"
        ),
        "platform": _text(runtime["platform"], _IDENTIFIER, "invalid_platform"),
    }

    dependencies = []
    seen_dependencies = set()
    dependency_keys = frozenset({"name", "version", "artifact_sha256"})
    for item in _bounded_list(root["dependencies"], MAX_DEPENDENCIES, "invalid_dependency_count"):
        dependency = _exact_keys(item, dependency_keys, "invalid_dependency_shape")
        name = _text(dependency["name"], _IDENTIFIER, "invalid_dependency_name")
        if name in seen_dependencies:
            raise FixtureEnvironmentError("duplicate_dependency_name")
        seen_dependencies.add(name)
        dependencies.append({
            "name": name,
            "version": _text(dependency["version"], _VERSION, "invalid_dependency_version"),
            "artifact_sha256": _text(
                dependency["artifact_sha256"], _SHA256, "invalid_dependency_hash"
            ),
        })
    dependencies.sort(key=lambda item: item["name"])

    fixtures = []
    seen_fixtures = set()
    fixture_keys = frozenset({"fixture_id", "version", "content_sha256", "size_bytes"})
    for item in _bounded_list(root["fixtures"], MAX_FIXTURES, "invalid_fixture_count"):
        fixture = _exact_keys(item, fixture_keys, "invalid_fixture_shape")
        fixture_id = _text(fixture["fixture_id"], _IDENTIFIER, "invalid_fixture_id")
        if fixture_id in seen_fixtures:
            raise FixtureEnvironmentError("duplicate_fixture_id")
        seen_fixtures.add(fixture_id)
        size_bytes = fixture["size_bytes"]
        if type(size_bytes) is not int or not 0 <= size_bytes <= MAX_MANIFEST_BYTES:
            raise FixtureEnvironmentError("invalid_fixture_size")
        fixtures.append({
            "fixture_id": fixture_id,
            "version": _text(fixture["version"], _VERSION, "invalid_fixture_version"),
            "content_sha256": _text(
                fixture["content_sha256"], _SHA256, "invalid_fixture_hash"
            ),
            "size_bytes": size_bytes,
        })
    fixtures.sort(key=lambda item: item["fixture_id"])

    report = {
        "environment_schema_version": SCHEMA_VERSION,
        "environment_id": _text(root["environment_id"], _IDENTIFIER, "invalid_environment_id"),
        "environment_version": _text(
            root["environment_version"], _VERSION, "invalid_environment_version"
        ),
        "runtime": normalized_runtime,
        "dependencies": dependencies,
        "fixtures": fixtures,
        "provenance": {"source": "caller_supplied_synthetic_metadata", "content_binding": "sha256"},
        "authority": AUTHORITY,
    }
    canonical = _canonical(report)
    if len(canonical.encode("utf-8")) > MAX_MANIFEST_BYTES:
        raise FixtureEnvironmentError("environment_manifest_too_large")
    report["evidence_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return report


def compare_fixture_environments(
    baseline: Mapping[str, object], observed: Mapping[str, object]
) -> dict:
    """Return deterministic drift evidence for two validated manifests."""

    expected = normalize_fixture_environment(baseline)
    actual = normalize_fixture_environment(observed)
    if expected["environment_id"] != actual["environment_id"]:
        raise FixtureEnvironmentError("environment_identity_mismatch")

    drift = []
    if expected["environment_version"] != actual["environment_version"]:
        drift.append({"kind": "environment_version", "subject": expected["environment_id"]})
    for field in ("python_version", "platform"):
        if expected["runtime"][field] != actual["runtime"][field]:
            drift.append({"kind": f"runtime_{field}", "subject": "runtime"})

    for collection, singular, identity, fields in (
        ("dependencies", "dependency", "name", ("version", "artifact_sha256")),
        ("fixtures", "fixture", "fixture_id", ("version", "content_sha256", "size_bytes")),
    ):
        expected_items = {item[identity]: item for item in expected[collection]}
        actual_items = {item[identity]: item for item in actual[collection]}
        for subject in sorted(expected_items.keys() - actual_items.keys()):
            drift.append({"kind": f"missing_{singular}", "subject": subject})
        for subject in sorted(actual_items.keys() - expected_items.keys()):
            drift.append({"kind": f"unexpected_{singular}", "subject": subject})
        for subject in sorted(expected_items.keys() & actual_items.keys()):
            for field in fields:
                if expected_items[subject][field] != actual_items[subject][field]:
                    drift.append({"kind": f"{singular}_{field}", "subject": subject})

    drift.sort(key=lambda item: (item["kind"], item["subject"]))
    report = {
        "environment_schema_version": SCHEMA_VERSION,
        "environment_id": expected["environment_id"],
        "baseline_evidence_id": expected["evidence_id"],
        "observed_evidence_id": actual["evidence_id"],
        "verdict": "reproducible" if not drift else "drift_detected",
        "drift": drift,
        "coverage": {"dependencies": len(expected["dependencies"]),
                     "fixtures": len(expected["fixtures"]),
                     "scope": "caller_supplied_metadata_only"},
        "authority": DRIFT_AUTHORITY,
    }
    report["evidence_id"] = hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()
    return report
