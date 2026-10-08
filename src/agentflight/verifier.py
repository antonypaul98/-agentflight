"""Tool-call contract verification."""

from collections.abc import Mapping

from .contract import CallContract
from .result import CheckResult

DEFAULT_MAX_ARGUMENTS = 64


def _contract_fields(fields: object) -> frozenset[str] | None:
    """Read declared argument names without invoking set-subclass or str hooks."""
    if isinstance(fields, frozenset):
        iterator = frozenset.__iter__(fields)
    elif isinstance(fields, set):
        iterator = set.__iter__(fields)
    else:
        return None
    names = []
    for field in iterator:
        if not isinstance(field, str):
            return None
        names.append(str.__str__(field))
    return frozenset(names)


def verify_name(contract: CallContract, name: str) -> CheckResult:
    if isinstance(name, str) and isinstance(contract.name, str) and str.__str__(name) == str.__str__(contract.name):
        return CheckResult(True, "ok")
    return CheckResult(False, "name_mismatch", str.__str__(name) if isinstance(name, str) else "non_string_name")


def verify_call(contract: CallContract, name: str, arguments: Mapping[str, object], *, max_arguments: int = DEFAULT_MAX_ARGUMENTS) -> CheckResult:
    if not isinstance(max_arguments, int) or isinstance(max_arguments, bool):
        raise TypeError("max_arguments must be an integer")
    # Normalize int subclasses without invoking their custom hooks.
    max_arguments = int.__int__(max_arguments)
    if max_arguments < 0:
        raise ValueError("max_arguments must be non-negative")

    name_result = verify_name(contract, name)
    if not name_result.passed:
        return name_result

    if not isinstance(arguments, Mapping):
        return CheckResult(False, "invalid_arguments", "expected_mapping")

    try:
        argument_count = len(arguments)
    except Exception:
        # Third-party Mapping hooks may raise arbitrary ordinary exceptions.
        return CheckResult(False, "invalid_arguments", "unreadable_mapping")

    if argument_count > max_arguments:
        return CheckResult(False, "too_many_arguments", f"{argument_count}>{max_arguments}")

    # Never trust a custom Mapping length to bound key iteration.
    try:
        keys = []
        for key in arguments:
            if len(keys) == argument_count:
                return CheckResult(False, "invalid_arguments", "unreadable_mapping")
            keys.append(key)
    except Exception:
        return CheckResult(False, "invalid_arguments", "unreadable_mapping")
    if len(keys) != argument_count:
        return CheckResult(False, "invalid_arguments", "unreadable_mapping")

    if any(not isinstance(key, str) for key in keys):
        return CheckResult(False, "invalid_arguments", "non_string_key")

    # Normalize str subclasses without invoking their custom hooks.
    provided = frozenset(str.__str__(key) for key in keys)
    if len(provided) != argument_count:
        return CheckResult(False, "invalid_arguments", "unreadable_mapping")
    if not isinstance(contract.required, (set, frozenset)) or not isinstance(contract.optional, (set, frozenset)):
        return CheckResult(False, "invalid_contract", "expected_argument_sets")
    required = _contract_fields(contract.required)
    optional = _contract_fields(contract.optional)
    if required is None or optional is None:
        return CheckResult(False, "invalid_contract", "non_string_argument_name")

    missing = sorted(required - provided)
    if missing:
        return CheckResult(False, "missing_required", ",".join(missing))

    allowed = required | optional
    unexpected = sorted(provided - allowed)
    if unexpected:
        return CheckResult(False, "unexpected_argument", ",".join(unexpected))

    return CheckResult(True, "ok")
