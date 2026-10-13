import copy

import pytest

from agentflight.agent_adapter import (
    MAX_REGISTERED_ADAPTERS,
    RecordedAdapterError,
    normalize_adapter_registry,
    normalize_authorized_recorded_run,
)
from test_agent_adapter import H0, H1, fixture


def registry(*adapters):
    return {
        "schema_version": 1,
        "registry_id": "synthetic-registry",
        "adapters": list(adapters) or [
            {
                "adapter_id": "fixture-adapter",
                "framework": "recorded-mock",
                "adapter_version": "v1",
                "contract_sha256": H0,
                "mode": "recorded_fixture",
            }
        ],
    }


def test_registry_is_deterministic_bounded_metadata_only_authority():
    value = registry()
    first = normalize_adapter_registry(value)
    second = normalize_adapter_registry(copy.deepcopy(value))
    assert first == second
    assert first["authority"] == "authorized_registry_metadata_only_no_execution"
    assert len(first["registry_evidence_id"]) == 64


def test_registry_order_does_not_change_evidence_identity():
    first = registry()["adapters"][0]
    second = dict(first, adapter_id="second-adapter", contract_sha256=H1)
    forward = normalize_adapter_registry(registry(first, second))
    reverse = normalize_adapter_registry(registry(second, first))
    assert forward == reverse
    assert [item["adapter_id"] for item in forward["adapters"]] == [
        "fixture-adapter", "second-adapter"
    ]


def test_authorized_run_binds_registry_contract_and_recorded_evidence():
    report = normalize_authorized_recorded_run(registry(), fixture())
    assert report["authority"] == "authorized_recorded_fixture_only_no_execution"
    assert report["adapter"] == normalize_adapter_registry(registry())["adapters"][0]
    assert report["recorded_run"]["authority"] == "recorded_fixture_only"
    assert report["recorded_run"]["steps"][0]["input_sha256"] == H0
    assert len(report["evidence_id"]) == 64


def test_authorized_normalization_does_not_mutate_inputs():
    registry_source, fixture_source = registry(), fixture()
    original_registry, original_fixture = copy.deepcopy(registry_source), copy.deepcopy(fixture_source)
    normalize_authorized_recorded_run(registry_source, fixture_source)
    assert registry_source == original_registry
    assert fixture_source == original_fixture


def test_registry_contract_changes_authorized_evidence_identity():
    original = normalize_authorized_recorded_run(registry(), fixture())
    changed = registry()
    changed["adapters"][0]["contract_sha256"] = H1
    updated = normalize_authorized_recorded_run(changed, fixture())
    assert original["registry_evidence_id"] != updated["registry_evidence_id"]
    assert original["evidence_id"] != updated["evidence_id"]


def test_unknown_adapter_fails_closed():
    source = fixture()
    source["adapter"]["adapter_id"] = "unregistered-adapter"
    with pytest.raises(RecordedAdapterError, match="adapter_not_authorized"):
        normalize_authorized_recorded_run(registry(), source)


def test_framework_mismatch_fails_closed():
    source = fixture("different-framework")
    with pytest.raises(RecordedAdapterError, match="authorized_framework_mismatch"):
        normalize_authorized_recorded_run(registry(), source)


@pytest.mark.parametrize(
    "field", ["module", "entrypoint", "command", "path", "callback", "credentials", "config"]
)
def test_registry_rejects_runtime_or_execution_fields(field):
    source = registry()
    source["adapters"][0][field] = "not-allowed"
    with pytest.raises(RecordedAdapterError, match="invalid_registered_adapter_shape"):
        normalize_adapter_registry(source)


def test_registry_rejects_unsupported_mode():
    source = registry()
    source["adapters"][0]["mode"] = "live"
    with pytest.raises(RecordedAdapterError, match="unsupported_adapter_mode"):
        normalize_adapter_registry(source)


def test_registry_rejects_duplicate_adapter_identity():
    item = registry()["adapters"][0]
    with pytest.raises(RecordedAdapterError, match="duplicate_registered_adapter_id"):
        normalize_adapter_registry(registry(item, copy.deepcopy(item)))


def test_registry_rejects_unbounded_adapter_count():
    template = registry()["adapters"][0]
    adapters = [dict(template, adapter_id=f"adapter-{index}")
                for index in range(MAX_REGISTERED_ADAPTERS + 1)]
    with pytest.raises(RecordedAdapterError, match="invalid_registered_adapter_count"):
        normalize_adapter_registry(registry(*adapters))


@pytest.mark.parametrize("field", ["adapter_version", "contract_sha256"])
def test_registry_rejects_noncanonical_contract_identity(field):
    source = registry()
    source["adapters"][0][field] = "A" * 64 if field == "contract_sha256" else "bad version"
    with pytest.raises(RecordedAdapterError, match="invalid_(adapter_version|contract_hash)"):
        normalize_adapter_registry(source)


def test_registry_rejects_mapping_subclasses():
    class Registry(dict):
        pass

    with pytest.raises(RecordedAdapterError, match="invalid_registry_shape"):
        normalize_adapter_registry(Registry(registry()))


def test_report_cannot_contain_private_or_executable_payloads():
    report = normalize_authorized_recorded_run(registry(), fixture())
    serialized = str(report)
    for forbidden in ("prompt", "arguments", "command", "credentials", "private-value"):
        assert forbidden not in serialized
