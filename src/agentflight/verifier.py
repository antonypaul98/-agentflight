"""Tool-call contract verification."""

from collections.abc import Mapping

from .contract import CallContract
from .result import CheckResult


def verify_name(contract: CallContract, name: str) -> CheckResult:
    if name == contract.name:
        return CheckResult(True, "ok")
    return CheckResult(False, "name_mismatch", name)


def verify_call(
    contract: CallContract,
    name: str,
    arguments: Mapping[str, object],
) -> CheckResult:
    name_result = verify_name(contract, name)
    if not name_result.passed:
        return name_result

    provided = frozenset(arguments)
    missing = sorted(contract.required - provided)
    if missing:
        return CheckResult(False, "missing_required", ",".join(missing))

    allowed = contract.required | contract.optional
    unexpected = sorted(provided - allowed)
    if unexpected:
        return CheckResult(False, "unexpected_argument", ",".join(unexpected))

    return CheckResult(True, "ok")
