# AF-20 - Bounded tool-call argument envelope

Status: ACCEPTANCE DEFINED

Goal: harden tool-call verification against malformed or excessive argument envelopes while preserving deterministic failure evidence.

Scope:
- Add a default maximum of 64 argument keys to verify_call.
- Validate the bound before inspecting arguments.
- Boolean and non-integer bounds raise TypeError.
- Negative bounds raise ValueError.
- Calls above the bound return CheckResult(False, "too_many_arguments", "<actual>><maximum>").
- Existing name, required-argument, and unexpected-argument behavior remains unchanged within the bound.
- Argument values are never executed or interpreted.

Acceptance:
1. Existing verifier tests remain green.
2. Exactly-at-limit input remains valid when otherwise allowed.
3. Over-limit input has deterministic too_many_arguments evidence.
4. Reordered over-limit mappings return equal evidence.
5. Invalid bound types and negative bounds are covered.
6. Full project suite passes on exact PR head.
7. Exact-head CI is green before merge.
