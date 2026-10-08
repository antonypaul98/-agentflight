"""Tool-call contract verification."""

from collections.abc import Mapping

from .contract import CallContract
from .result import CheckResult

DEFAULT_MAX_ARGUMENTS = 64


def verify_name(contract: CallContract, name: str) -> CheckResult:
    if name == contract.name:
        return CheckResult(True, "ok")
    return CheckResult(False, "name_mismatch", name)


def verify_call(contract: CallContract, name: str, arguments: Mapping[str, object], *, max_arguments: int = DEFAULT_MAX_ARGUMENTS) -> CheckResult:
    if not isinstance(max_arguments, int) or isinstance(max_arguments, bool):
        raise TypeError("max_arguments must be an integer")
    if max_arguments < 0:
        raise ValueError("max_arguments must be non-negative")

    name_result = verify_name(contract, name)
    if not name_result.passed:
        return name_result

    if not isinstance(arguments, Mapping):
        return CheckResult(False, "invalid_arguments", "expected_mapping")

    argument_count = len(arguments)
    if argument_count > max_arguments:
        return CheckResult(False, "too_many_arguments", f"{argument_count}>{max_arguments}")

    if any(not isinstance(key, str) for key in arguments):
        return CheckResult(False, "invalid_arguments", "non_string_key")

    provided = frozenset(arguments)
    missing = sorted(contract.required - provided)
    if missing:
        return CheckResult(False, "missing_required", ",".join(missing))

    allowed = contract.required | contract.optional
    unexpected = sorted(provided - allowed)
    if unexpected:
        return CheckResult(False, "unexpected_argument", ",".join(unexpected))

    return CheckResult(True, "ok")
