"""Tool-call contract verification."""

from .contract import CallContract
from .result import CheckResult


def verify_name(contract: CallContract, name: str) -> CheckResult:
    if name == contract.name:
        return CheckResult(True, "ok")
    return CheckResult(False, "name_mismatch", name)
