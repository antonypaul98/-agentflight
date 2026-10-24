# AF-29 — permission and prompt-injection testing

Status: **IN PROGRESS**. The first bounded slice verifies caller-supplied,
recorded authorization decisions against a deterministic fail-closed oracle.
The latest bounded source candidate verifies that an exact, content-addressed
multi-hop lineage and its terminal authorization are safe for one recorded
sensitive sink class.

The oracle denies cross-tenant authorization, untrusted-content control,
caller-recorded injection findings, and requests exceeding exact granted scopes.
Reports bind only hashed principal, tenant and input-evidence identities plus
bounded scope identifiers. Raw prompts, payloads and credentials are excluded.

This is synthetic recorded-metadata verification, not an authorization system.
It does not read prompts, inspect projects, invoke tools, execute agents or
commands, access filesystems or networks, grant permissions, or establish an OS
sandbox. The sensitive-sink source PR and merged-main CI are verified; canonical
records and their independent CI remain required. AF-29 remains in progress at
6/12.

## Recorded sensitive-sink boundary candidate

The candidate recomputes an embedded influence lineage and binds its exact
evidence identifier. It then recomputes the terminal recorded authorization
decision and maps one of four fixed sink classes to its required scope:
`read_only`, `state_change`, `external_effect`, or `privileged_control`.
Acceptance requires a verified accepted lineage with no untrusted influence,
an internally consistent authorized terminal decision, and the exact required
scope among the terminal requested scopes. Upstream untrusted instructions or
caller-recorded injection findings cannot be laundered by a later trusted hop.

Only bounded caller-supplied hashes, identifiers, booleans, dispositions, and
scope names are processed. The verifier reads no prompt, instruction, payload,
credential, project, filesystem, or network; it detects no injection, grants no
permission, invokes nothing, and performs no external action. Exact Python 3.11
source PR and merged-main CI are complete. Canonical records and their
independent PR/merged-main CI remain required before writer release.

## Recorded sensitive-sink boundary source receipt

PR #74 exact head `4ff776c745f496b3d1774b617e42c48f10250756`
passed run 40045081892 on Python 3.11.17 with 542 product tests and zero
product skips. Guarded merge produced exact main
`da712d3da89d0a6bb2b4e31cf4a19231163c847a`; push run 40045159092 passed
the same 542-test suite with zero product skips. Both runs executed all 18
infrastructure guards: 17 passed and one established Memory-only case skipped.

The slice remains synthetic recorded-metadata verification only. It reads no
raw prompt, instruction, payload or credential, detects no injection, grants no
permission, and performs no project inspection, execution, external action,
resource enforcement or OS-sandbox validation. AF-29 remains in progress at
6/12.

## Recorded multi-hop untrusted-influence lineage candidate

The candidate accepts two to sixteen ordered recorded hops. Each hop binds its
input hash to recomputed instruction-provenance evidence, and every later input
must equal the prior output hash. Untrusted instruction or input boundaries and
caller-recorded injection findings activate influence at that hop and propagate
it through all downstream hops. Any affected lineage requires rejection even
when a later hop is recorded as trusted. Substituted evidence, discontinuous
hashes, duplicate hop identities, malformed metadata and action-bearing fields
fail closed.

The verifier reads no instruction or prompt text and does not detect injection.
It processes bounded caller-supplied hashes, identifiers, booleans and
dispositions only. It grants no permission, executes nothing, and accesses no
project, payload, credential, filesystem, network or external system. Exact
Python 3.11 source PR and merged-main CI are complete. Canonical records and
their independent PR/merged-main CI remain required before writer release.

## Recorded multi-hop untrusted-influence lineage source receipt

PR #72 head `17a4481e04e1a3eab5e35144d2f2877159acae89`, tree
`307efa7409053d0d426dde7701204ca17870cae5`, passed exact-head run
39978381724 on Python 3.11.17 with 529 product tests and zero product skips.
Guarded merge produced main `31a83bed71303cbf1dc02b8f5484e7b943f27dab`;
exact push run 40002769894 passed the same 529-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped.

The slice remains synthetic recorded-metadata verification only. It reads no
raw prompt, instruction, payload or credential, detects no injection, grants no
permission, and performs no project inspection, tool/agent/command execution,
filesystem/network access, external action, resource enforcement or OS-sandbox
validation. AF-29 remains in progress and roadmap acceptance remains 6/12.

## Recorded instruction-provenance candidate

The candidate accepts only a trusted-control instruction hash matching the
recorded trusted hash, an exact recomputed security-probe evidence identifier,
an underlying authorization decision that passes and permits authorization,
and no caller-recorded policy-override attempt. Untrusted instruction sources,
hash substitution, denial-required probes, inconsistent decisions, override
attempts, malformed metadata and action-bearing fields fail closed.

Only hashes, bounded identifiers, booleans and dispositions are processed. The
verifier never reads instruction or prompt text, detects injections itself,
authorizes or invokes a tool, or accesses a project, filesystem, network,
credential, payload or external system. Exact Python 3.11 PR and merged-main CI
remain required before a source receipt can be recorded or the writer released.

## Recorded instruction-provenance source receipt

PR #70 head `18d326c096671988f34162d98f2ed48e0344f2e9`, tree
`c6bd70346fdf515bbbf29c781a7c6db381a4bb95`, passed exact-head run
39939002114 on Python 3.11.17 with 516 product tests and zero product
skips. Guarded merge produced main `d3f8723f2269d22e905533df8aaeb3187af92dea`;
exact push run 39939139774 passed the same 516-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped.

The slice remains limited to deterministic fail-closed verification of bounded,
caller-supplied recorded hashes and dispositions. It reads no raw instruction,
prompt, payload or credential; grants no permission; and performs no project
inspection, injection detection, tool/agent/command execution,
filesystem/network access, external action, resource enforcement or OS-sandbox
validation. AF-29 remains in progress and roadmap acceptance remains 6/12.

## Permission-boundary source receipt

PR #68 head `01d73281f39afb7338137f3df10d6d29a8cf8b59`, tree
`7f6ba51744545bfc10902e4f907439afa73b0545`, passed exact-head run
39900570012 on Python 3.11.17 with 504 product tests and zero product
skips. Guarded merge produced main `5330726fd81bf1b6071fdd72b825e89ed47edd6b`;
exact push run 39900701428 passed the same 504-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped.

The slice is limited to deterministic fail-closed verification of caller-supplied
recorded tenant, scope, trust-boundary and injection decisions. It reads no raw
prompts, payloads or credentials; grants no permissions; and performs no
project inspection, tool/agent/command execution, filesystem/network access,
external action, resource enforcement or OS-sandbox validation. AF-29 remains
in progress and roadmap acceptance remains 6/12.

## Recorded sensitive-sink records receipt and binding candidate

Records PR #75 head `6d65ac5c8b0d052b90ad245097f438b0c3cf2cb6`, tree
`92e4ff90be773e19449527560fa4155ef86b586b`, passed run 40045393444
with 542 product tests and zero skips. Guarded merge produced exact main
`6352831c9d88f0da482394b45bd58db0c47286c9`; run 40045473396 passed
the same suite, and the prior writer was explicitly released.

The new bounded candidate recomputes exact sensitive-sink evidence, then binds
the recorded sink input hash to the terminal lineage output and the authorized
tool identifier to the terminal authorization tool. Input substitution,
confused-deputy tool substitution, inconsistent boundary evidence, malformed
metadata, and false recorded acceptance fail closed.

Only bounded hashes, identifiers, dispositions, and recomputed recorded
evidence are processed. The verifier reads no prompt, instruction, payload,
credential, project, filesystem, or network; grants no permission; invokes no
agent, tool, or command; and performs no external action, resource enforcement,
or OS-sandbox validation. Exact Python 3.11 source and records PR/merged-main
CI remain required before writer release. AF-29 remains in progress at 6/12.
