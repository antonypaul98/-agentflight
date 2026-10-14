import copy

import pytest

from agentflight.fixture_environment import (
    FixtureEnvironmentError,
    compare_fixture_environments,
    normalize_fixture_environment,
)


H0, H1, H2, H3 = (character * 64 for character in "0123")


def manifest():
    return {
        "schema_version": 1,
        "environment_id": "synthetic-agent-lab",
        "environment_version": "1.0.0",
        "runtime": {"python_version": "3.11.17", "platform": "linux-x86_64"},
        "dependencies": [
            {"name": "pytest", "version": "8.4.2", "artifact_sha256": H0},
            {"name": "agentflight", "version": "0.1.0", "artifact_sha256": H1},
        ],
        "fixtures": [
            {"fixture_id": "trajectory-success", "version": "1.0.0",
             "content_sha256": H2, "size_bytes": 384},
            {"fixture_id": "trajectory-failure", "version": "1.0.0",
             "content_sha256": H3, "size_bytes": 512},
        ],
    }


def test_normalizes_manifest_deterministically_without_mutation():
    first_input = manifest()
    original = copy.deepcopy(first_input)
    first = normalize_fixture_environment(first_input)
    reversed_input = manifest()
    reversed_input["dependencies"].reverse()
    reversed_input["fixtures"].reverse()
    assert first == normalize_fixture_environment(reversed_input)
    assert first_input == original
    assert [item["name"] for item in first["dependencies"]] == ["agentflight", "pytest"]
    assert [item["fixture_id"] for item in first["fixtures"]] == [
        "trajectory-failure", "trajectory-success"
    ]
    assert first["provenance"] == {
        "source": "caller_supplied_synthetic_metadata", "content_binding": "sha256"
    }
    assert first["authority"] == "synthetic_fixture_metadata_only_no_environment_execution"
    assert len(first["evidence_id"]) == 64


def test_identical_manifests_are_reproducible():
    report = compare_fixture_environments(manifest(), copy.deepcopy(manifest()))
    assert report["verdict"] == "reproducible"
    assert report["drift"] == []
    assert report["baseline_evidence_id"] == report["observed_evidence_id"]
    assert report["coverage"] == {
        "dependencies": 2, "fixtures": 2, "scope": "caller_supplied_metadata_only"
    }


@pytest.mark.parametrize(
    ("change", "expected_kind", "subject"),
    [
        (lambda value: value.update(environment_version="1.0.1"),
         "environment_version", "synthetic-agent-lab"),
        (lambda value: value["runtime"].update(python_version="3.11.18"),
         "runtime_python_version", "runtime"),
        (lambda value: value["dependencies"][0].update(version="8.4.3"),
         "dependency_version", "pytest"),
        (lambda value: value["dependencies"][0].update(artifact_sha256=H3),
         "dependency_artifact_sha256", "pytest"),
        (lambda value: value["fixtures"][0].update(content_sha256=H0),
         "fixture_content_sha256", "trajectory-success"),
        (lambda value: value["fixtures"][0].update(size_bytes=385),
         "fixture_size_bytes", "trajectory-success"),
    ],
)
def test_reports_exact_drift_category_without_payloads(change, expected_kind, subject):
    observed = manifest()
    change(observed)
    report = compare_fixture_environments(manifest(), observed)
    assert report["verdict"] == "drift_detected"
    assert {"kind": expected_kind, "subject": subject} in report["drift"]


def test_reports_missing_and_unexpected_items_in_stable_order():
    observed = manifest()
    observed["dependencies"].pop(0)
    observed["fixtures"].append(
        {"fixture_id": "new-case", "version": "1.0.0",
         "content_sha256": H0, "size_bytes": 1}
    )
    report = compare_fixture_environments(manifest(), observed)
    assert report["drift"] == [
        {"kind": "missing_dependency", "subject": "pytest"},
        {"kind": "unexpected_fixture", "subject": "new-case"},
    ]


@pytest.mark.parametrize(
    ("group", "key", "value", "code"),
    [
        ("root", "command", "echo unsafe", "invalid_environment_shape"),
        ("runtime", "env", "SECRET", "invalid_runtime_shape"),
        ("dependency", "url", "https://example.invalid", "invalid_dependency_shape"),
        ("fixture", "path", "/private/project/case.json", "invalid_fixture_shape"),
    ],
)
def test_rejects_execution_or_payload_bearing_fields(group, key, value, code):
    item = manifest()
    target = {"root": item, "runtime": item["runtime"],
              "dependency": item["dependencies"][0], "fixture": item["fixtures"][0]}[group]
    target[key] = value
    with pytest.raises(FixtureEnvironmentError, match=code):
        normalize_fixture_environment(item)


@pytest.mark.parametrize(
    ("change", "code"),
    [
        (lambda value: value["dependencies"].append(copy.deepcopy(value["dependencies"][0])),
         "duplicate_dependency_name"),
        (lambda value: value["fixtures"].append(copy.deepcopy(value["fixtures"][0])),
         "duplicate_fixture_id"),
        (lambda value: value["fixtures"][0].update(content_sha256="A" * 64),
         "invalid_fixture_hash"),
        (lambda value: value["fixtures"][0].update(size_bytes=-1),
         "invalid_fixture_size"),
        (lambda value: value["runtime"].update(python_version="3.11"),
         "invalid_python_version"),
    ],
)
def test_invalid_manifest_fails_closed(change, code):
    item = manifest()
    change(item)
    with pytest.raises(FixtureEnvironmentError, match=code):
        normalize_fixture_environment(item)


def test_comparison_rejects_different_environment_identity():
    observed = manifest()
    observed["environment_id"] = "other-lab"
    with pytest.raises(FixtureEnvironmentError, match="environment_identity_mismatch"):
        compare_fixture_environments(manifest(), observed)
