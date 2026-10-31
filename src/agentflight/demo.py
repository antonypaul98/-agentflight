"""Offline, data-only AgentFlight crash-test demo."""

import argparse
import hashlib
import json
from pathlib import Path

from .adversarial import detect_prompt_injection
from .suite import (
    MAX_FIXTURE_BYTES,
    FixtureError,
    _canonical,
    _identifier,
    _object,
    _unique_object,
    _validate_json,
    run_suite,
)


MAX_INJECTION_PROBES = 64
_CHANNELS = frozenset({"retrieved_document", "tool_output", "user_input"})


def _report_hash(report: dict) -> str:
    return hashlib.sha256(_canonical(report).encode("utf-8")).hexdigest()


def run_demo(manifest: dict) -> dict:
    """Evaluate one bounded recorded run without invoking an agent or tool."""
    _validate_json(manifest)
    document = _object(
        manifest,
        {"schema_version", "demo_id", "recorded_call_suite", "injection_probes"},
    )
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise FixtureError("unsupported_schema_version")
    demo_id = _identifier(document["demo_id"])
    suite_report = run_suite(document["recorded_call_suite"])

    probes = document["injection_probes"]
    if type(probes) is not list or not 1 <= len(probes) <= MAX_INJECTION_PROBES:
        raise FixtureError("injection_probe_count_limit")

    prepared = []
    identifiers = set()
    for raw in probes:
        probe = _object(raw, {"probe_id", "channel", "text", "expected_detected"})
        probe_id = _identifier(probe["probe_id"])
        if probe_id in identifiers:
            raise FixtureError("duplicate_probe_id")
        identifiers.add(probe_id)
        channel = probe["channel"]
        if type(channel) is not str or channel not in _CHANNELS:
            raise FixtureError("invalid_probe_channel")
        if type(probe["text"]) is not str or type(probe["expected_detected"]) is not bool:
            raise FixtureError("invalid_probe")
        prepared.append((probe_id, channel, probe["text"], probe["expected_detected"]))

    results = []
    for probe_id, channel, text, expected_detected in sorted(prepared):
        finding = detect_prompt_injection(text)
        observed = {
            "detected": finding.detected,
            "truncated": finding.truncated,
            "inspected_chars": finding.inspected_chars,
        }
        evidence = {
            "demo_id": demo_id,
            "probe_id": probe_id,
            "channel": channel,
            "observed": observed,
            "marker_digest": (
                hashlib.sha256(finding.marker.encode("utf-8")).hexdigest()
                if finding.marker is not None
                else None
            ),
        }
        matched = finding.detected is expected_detected
        results.append(
            {
                "probe_id": probe_id,
                "channel": channel,
                "status": "passed" if matched else "failed",
                "expected_detected": expected_detected,
                "observed": observed,
                "evidence_id": _report_hash(evidence),
                "diagnostic": (
                    ""
                    if matched
                    else "The bounded injection verdict differed from the explicit expectation."
                ),
            }
        )

    injection_summary = {
        "total": len(results),
        "passed": sum(result["status"] == "passed" for result in results),
        "failed": sum(result["status"] == "failed" for result in results),
    }
    status = (
        "passed"
        if suite_report["status"] == "passed" and injection_summary["failed"] == 0
        else "failed"
    )
    report = {
        "schema_version": 1,
        "demo_id": demo_id,
        "status": status,
        "recorded_calls": suite_report,
        "injection_probes": {
            "summary": injection_summary,
            "cases": results,
        },
        "safety_boundary": {
            "data_only": True,
            "agent_execution": False,
            "tool_execution": False,
            "network_access": False,
        },
    }
    return {**report, "report_hash": _report_hash(report)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="UTF-8 JSON demo manifest; data only")
    args = parser.parse_args(argv)
    try:
        with Path(args.manifest).open("rb") as stream:
            content = stream.read(MAX_FIXTURE_BYTES + 1)
        if len(content) > MAX_FIXTURE_BYTES:
            raise FixtureError("fixture_too_large")
        manifest = json.loads(content.decode("utf-8"), object_pairs_hook=_unique_object)
        report = run_demo(manifest)
    except (FixtureError, OSError, ValueError, RecursionError, UnicodeError) as exc:
        code = str(exc) if isinstance(exc, FixtureError) else "unreadable_or_invalid_json"
        print(
            _canonical(
                {
                    "schema_version": 1,
                    "status": "invalid_fixture",
                    "error": code,
                    "diagnostic": "Provide a bounded data-only demo manifest matching the documented schema.",
                }
            )
        )
        return 2
    print(_canonical(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
