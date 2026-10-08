"""Tool-call contract verification."""

from collections.abc import Mapping

from .contract import CallContract
from .result import CheckResult

DEFAULT_MAX_ARGUMENTS = 64
MAX_DECLARED_ARGUMENTS = 1024  # Hard ceiling for untrusted contract schemas.
MAX_NAME_MISMATCH_DETAIL = 256  # Bound evidence from untrusted tool names.


def _contract_fields(fields: object) -> tuple[frozenset[str] | None, str]:
    """Read declared argument names without invoking set-subclass or str hooks."""
    if isinstance(fields, frozenset):
        if frozenset.__len__(fields) > MAX_DECLARED_ARGUMENTS:
            return None, "too_many_declared_arguments"
        iterator = frozenset.__iter__(fields)
    elif isinstance(fields, set):
        if set.__len__(fields) > MAX_DECLARED_ARGUMENTS:
            return None, "too_many_declared_arguments"
        iterator = set.__iter__(fields)
    else:
        return None, "expected_argument_sets"
    names = []
    for field in iterator:
        if not isinstance(field, str):
            return None, "non_string_argument_name"
        names.append(str.__str__(field))
    normalized = frozenset(names)
    if len(normalized) != len(names):
        return None, "duplicate_argument_name"
    return normalized, ""


def verify_name(contract: CallContract, name: str) -> CheckResult:
    if isinstance(name, str) and isinstance(contract.name, str) and str.__str__(name) == str.__str__(contract.name):
        return CheckResult(True, "ok")
    if not isinstance(name, str):
        return CheckResult(False, "name_mismatch", "non_string_name")
    normalized = str.__str__(name)
    if str.__len__(normalized) > MAX_NAME_MISMATCH_DETAIL:
        marker = "<truncated>"
        normalized = str.__getitem__(normalized, slice(0, MAX_NAME_MISMATCH_DETAIL - len(marker))) + marker
    return CheckResult(False, "name_mismatch", normalized)


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
        # Built-in dict storage is authoritative even when subclasses lie about length.
        argument_count = dict.__len__(arguments) if isinstance(arguments, dict) else len(arguments)
    except Exception:
        # Third-party Mapping hooks may raise arbitrary ordinary exceptions.
        return CheckResult(False, "invalid_arguments", "unreadable_mapping")

    if argument_count > max_arguments:
        return CheckResult(False, "too_many_arguments", f"{argument_count}>{max_arguments}")

    # Never trust a custom Mapping length to bound key iteration.
    try:
        keys = []
        # Avoid subclass iterator hooks that can fabricate or conceal real dict keys.
        iterator = dict.__iter__(arguments) if isinstance(arguments, dict) else iter(arguments)
        for key in iterator:
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
    required, required_error = _contract_fields(contract.required)
    optional, optional_error = _contract_fields(contract.optional)
    if required_error or optional_error:
        return CheckResult(False, "invalid_contract", required_error or optional_error)
    # Required and optional schemas must not declare the same normalized name.
    if not required.isdisjoint(optional):
        return CheckResult(False, "invalid_contract", "duplicate_argument_name")

    missing = sorted(required - provided)
    if missing:
        return CheckResult(False, "missing_required", ",".join(missing))

    allowed = required | optional
    unexpected = sorted(provided - allowed)
    if unexpected:
        return CheckResult(False, "unexpected_argument", ",".join(unexpected))

    return CheckResult(True, "ok")
