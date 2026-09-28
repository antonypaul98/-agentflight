"""Stable identifiers for reproducible AgentFlight evidence."""

import hashlib
import json
from collections.abc import Mapping

from .result import CheckResult


def evidence_id(
    check: CheckResult,
    *,
    tool_name: str = "",
    arguments: Mapping[str, object] | None = None,
) -> str:
    """Return a deterministic identifier for equivalent verification evidence."""
    payload = {
        "arguments": dict(arguments or {}),
        "check": {
            "code": check.code,
            "detail": check.detail,
            "passed": check.passed,
        },
        "tool_name": tool_name,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
