"""Bounded, data-only replay suites with deterministic, privacy-conscious reports."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from .contract import CallContract
from .recording import RecordedToolExchange
from .replay_check import replay_exchange
from .verifier import MAX_DECLARED_ARGUMENTS

MAX_CASES = 256
MAX_FIXTURE_BYTES = 1_048_576
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 50_000
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}\Z")
_CODES = frozenset({"ok", "name_mismatch", "invalid_arguments", "too_many_arguments",
                    "invalid_contract", "missing_required", "unexpected_argument"})
_GUIDANCE = {
    "ok": "The recorded call satisfied its contract; inspect the expected rejection.",
    "name_mismatch": "Compare the recorded tool name with the declared contract name.",
    "invalid_arguments": "Inspect the recorded argument object privately.",
    "too_many_arguments": "Reduce the recorded argument count to the verifier's supported bound.",
    "invalid_contract": "Check argument declarations for overlap or excessive schema size.",
    "missing_required": "Compare the required declarations with the recorded argument keys.",
    "unexpected_argument": "Compare recorded argument keys with the allowed declarations.",
}


class FixtureError(ValueError):
    """Invalid test input, distinct from a failed test or a replay error."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _validate_json(value: object) -> None:
    # Exact built-in types avoid executing custom collection/serialization hooks.
    stack = [(value, 0)]
    nodes = characters = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise FixtureError("json_structure_limit")
        kind = type(item)
        if kind is dict:
            if len(item) + nodes + len(stack) > MAX_JSON_NODES:
                raise FixtureError("json_structure_limit")
            for key, child in item.items():
                if type(key) is not str:
                    raise FixtureError("invalid_json_type")
                characters += len(key)
                stack.append((child, depth + 1))
        elif kind is list:
            if len(item) + nodes + len(stack) > MAX_JSON_NODES:
                raise FixtureError("json_structure_limit")
            stack.extend((child, depth + 1) for child in item)
        elif kind is str:
            characters += len(item)
        elif kind is float:
            if not math.isfinite(item):
                raise FixtureError("invalid_json_number")
        elif kind is int:
            if item.bit_length() > 4096:
                raise FixtureError("invalid_json_number")
        elif kind not in (bool, type(None)):
            raise FixtureError("invalid_json_type")
        if characters > MAX_FIXTURE_BYTES:
            raise FixtureError("fixture_too_large")
    if len(_canonical(value).encode("utf-8")) > MAX_FIXTURE_BYTES:
        raise FixtureError("fixture_too_large")


def _object(value: object, required: set[str], optional: set[str] = frozenset()) -> dict:
    if type(value) is not dict or not required <= value.keys() or value.keys() - required - optional:
        raise FixtureError("invalid_fields")
    return value


def _identifier(value: object) -> str:
    if type(value) is not str or not _IDENTIFIER.fullmatch(value):
        raise FixtureError("invalid_identifier")
    return value


def _fields(value: object) -> frozenset[str]:
    if type(value) is not list or len(value) > MAX_DECLARED_ARGUMENTS or any(type(v) is not str for v in value):
        raise FixtureError("invalid_schema_fields")
    if len(set(value)) != len(value):
        raise FixtureError("duplicate_schema_field")
    return frozenset(value)


def run_suite(fixture: dict) -> dict:
    """Compare explicit expectations with existing replay checks; execute no tools."""
    _validate_json(fixture)
    document = _object(fixture, {"schema_version", "suite_id", "cases"})
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise FixtureError("unsupported_schema_version")
    suite_id = _identifier(document["suite_id"])
    cases = document["cases"]
    if type(cases) is not list or not 1 <= len(cases) <= MAX_CASES:
        raise FixtureError("case_count_limit")

    prepared = []
    identifiers = set()
    # Validate the entire fixture before replaying any case.
    for raw in cases:
        case = _object(raw, {"case_id", "contract", "exchange", "expected"})
        case_id = _identifier(case["case_id"])
        if case_id in identifiers:
            raise FixtureError("duplicate_case_id")
        identifiers.add(case_id)
        contract = _object(case["contract"], {"name"}, {"required", "optional"})
        exchange = _object(case["exchange"], {"name", "arguments"}, {"result"})
        if type(contract["name"]) is not str or type(exchange["name"]) is not str or type(exchange["arguments"]) is not dict:
            raise FixtureError("invalid_recording")
        expected = _object(case["expected"], {"passed", "code"})
        if (type(expected["passed"]) is not bool or type(expected["code"]) is not str
                or expected["code"] not in _CODES or expected["passed"] != (expected["code"] == "ok")):
            raise FixtureError("invalid_expectation")
        prepared.append((case_id, CallContract(contract["name"], _fields(contract.get("required", [])),
                                              _fields(contract.get("optional", []))),
                         RecordedToolExchange(exchange["name"], exchange["arguments"], exchange.get("result")),
                         dict(expected)))

    results = []
    for case_id, contract, exchange, expected in sorted(prepared, key=lambda case: case[0]):
        try:
            replayed = replay_exchange(contract, exchange)
        except Exception:
            # Exception text/tracebacks may contain private data. Never count an
            # unverified replay as an expected rejection or fabricate evidence.
            results.append({"case_id": case_id, "status": "error", "expected": expected,
                            "observed": None, "evidence_id": None,
                            "diagnostic": "Replay verification failed; inspect the fixture and verifier privately."})
            continue
        observed = {"passed": replayed.check.passed, "code": replayed.check.code}
        matched = observed == expected
        scoped = {"suite_id": suite_id, "case_id": case_id, "verification_evidence_id": replayed.evidence_id}
        results.append({"case_id": case_id, "status": "passed" if matched else "failed",
                        "expected": expected, "observed": observed,
                        "evidence_id": hashlib.sha256(_canonical(scoped).encode("utf-8")).hexdigest(),
                        "diagnostic": "" if matched else _GUIDANCE.get(replayed.check.code, "Inspect the verification verdict privately.")})
    summary = {"total": len(results), **{status: sum(r["status"] == status for r in results)
                                        for status in ("passed", "failed", "error")}}
    return {"schema_version": 1, "suite_id": suite_id,
            "status": "passed" if summary["passed"] == summary["total"] else "failed",
            "summary": summary, "cases": results}


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise FixtureError("duplicate_json_key")
        result[key] = value
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", help="UTF-8 JSON recorded-call suite; data only")
    args = parser.parse_args(argv)
    try:
        with Path(args.fixture).open("rb") as stream:
            content = stream.read(MAX_FIXTURE_BYTES + 1)
        if len(content) > MAX_FIXTURE_BYTES:
            raise FixtureError("fixture_too_large")
        fixture = json.loads(content.decode("utf-8"), object_pairs_hook=_unique_object)
        report = run_suite(fixture)
    except (FixtureError, OSError, ValueError, RecursionError, UnicodeError) as exc:
        code = str(exc) if isinstance(exc, FixtureError) else "unreadable_or_invalid_json"
        print(_canonical({"schema_version": 1, "status": "invalid_fixture", "error": code,
                          "diagnostic": "Provide a bounded data-only suite matching the documented schema."}))
        return 2
    print(_canonical(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
