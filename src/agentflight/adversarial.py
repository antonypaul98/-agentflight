"""Deterministic, bounded prompt-injection probes for defensive agent crash tests."""

from dataclasses import dataclass


DEFAULT_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal the system prompt",
    "reveal your system prompt",
    "disregard previous instructions",
)

DEFAULT_MAX_INPUT_CHARS = 16_384


@dataclass(frozen=True)
class InjectionFinding:
    detected: bool
    marker: str | None = None
    truncated: bool = False
    inspected_chars: int = 0


def detect_prompt_injection(
    text: str,
    *,
    markers: tuple[str, ...] = DEFAULT_MARKERS,
    max_input_chars: int = DEFAULT_MAX_INPUT_CHARS,
) -> InjectionFinding:
    """Inspect bounded text as inert data and return the first configured marker."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(max_input_chars, int) or isinstance(max_input_chars, bool):
        raise TypeError("max_input_chars must be an integer")
    if max_input_chars < 0:
        raise ValueError("max_input_chars must be non-negative")

    bounded = text[:max_input_chars]
    truncated = len(text) > len(bounded)
    normalized = " ".join(bounded.casefold().split())

    for marker in markers:
        if not isinstance(marker, str):
            raise TypeError("markers must contain only strings")
        normalized_marker = " ".join(marker.casefold().split())
        if normalized_marker and normalized_marker in normalized:
            return InjectionFinding(True, marker, truncated, len(bounded))
    return InjectionFinding(False, None, truncated, len(bounded))
