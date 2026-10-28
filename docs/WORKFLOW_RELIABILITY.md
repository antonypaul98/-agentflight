# Workflow reliability — stabilization 2026-10-03

No product checkpoint advanced. No feature source/test changed.

## Environment

Metadata minimum remains Python >=3.11 where present; this repository's
reproducible development/CI interpreter is **3.11** (`.python-version`).
Other interpreters are not validated by this stabilization. Existing dependency
ranges are retained; version ranges do not guarantee byte-for-byte dependency
reproducibility. No dependencies upgraded or new lockfile guessed.

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python scripts/session_preflight.py
python -m pip install -e . pytest
python -m pip check
python scripts/ci_diagnostics.py
```

Preflight failing on a new clean checkout on main is intentional: switch to the
existing recorded branch. Missing gh is a tooling blocker, not proof that the
connected GitHub integration is unavailable. Follow AGENTS.md's fallback.
A dry-run is preliminary; branch protections/token scopes can still reject a
real write. Verify the first actual coherent commit remotely before larger work.

## CI event contract

Push main/work/** and all PRs; Python 3.11.
CI uses scoped concurrency, contents:read, bounded jobs and early environment
checks. Package import/pip check/connectivity success is not product acceptance.
Never print environment variables, tokens, DSNs or credential helper output.

This infrastructure commit uses `[skip ci]` deliberately to preserve execution
capacity and avoid running feature-checkpoint suites in this repair-only run.
No PR is opened for a skipped commit (required checks could remain pending).
Future normal commits must not copy that marker; expected push/PR events will
run the documented workflows. CI execution after these edits is not claimed.

## Historical first-pass audit evidence (superseded by current state)

Existing exact-head run 36677669902 succeeded; local-only 63fcc3d was not covered.

Observed main: `87b1372f66efe00231c42aacfc6e49b2b95961ff`. Active feature head: `d760d71f9b2f7ccc95e21034dda8fedccc92eb25`.
All current remote feature work was ahead of main, not behind it. Local worktrees
from September 30 had stale refs; some contained uncommitted/untracked work.
Shell access initially failed through an unavailable sandbox proxy; a permitted
network execution context restored read/fetch. Shell GitHub CLI was absent;
connector repository metadata reported push permission. Actual connector
publication must be verified before claiming a durable fix.

`docs/recovery/2026-10-03/` preserves source patches without applying them.
Original worktrees remain untouched. AgentFlight also had a local-only commit
63fcc3d; its patch is archived, not activated or merged. These archives cover the
identified September 30 worktrees, not inaccessible devices or unknown sessions.

## Branch discipline

Use `git fetch --all --prune`, `git merge-base origin/main HEAD`,
`git rev-list --left-right --count origin/main...HEAD` and
`git rev-list --left-right --count HEAD...origin/<active-branch>`.
Inspect dirty status before switching and check `git worktree list`.
No deletions are needed. Historical classifications are in `docs/BRANCH_AUDIT.md`.
Only merge stale main into a feature branch or rebase after reviewing conflicts
and scope; this stabilization does neither. Preserve divergent local variants
for comparison, not automatic integration.

## Follow-up live audit and current operating contract

Run 37100836348: installation/diagnostics passed; 6 AF-19 test assertions failed on inspected_chars. Feature failure intentionally untouched.

Current observations, CI SHA/event/URL, PR, and last-session blocker are in
CHECKPOINT_STATE.json. observed_feature_sha identifies the last source/test
commit; observed_branch_sha identifies the fetched branch head. The current
repository SHA is resolved with git rev-parse HEAD, never a self-reference.
Local tests not run this session are not failures. Historical CI successes are
not evidence for a later skipped head. Prior local receipts are attributed,
not re-executed.

Core CI uses workflow+ref concurrency: a newer push cancels the previous push
on that ref; PR and push refs are separate and may both run. Cancellation is
not a pass. Existing timeouts, interpreter pins, dependency ranges, PostgreSQL
services and workflow permissions are retained. No dependency migration.

The commit-message validator rejects standard Actions skip directives on
ordinary commits. An explicit infrastructure exception requires an audited
file list; install/integrate the local hook as described in AGENTS.md, and call
the same validator before API writes. Hooks cannot enforce remote API behavior
or control the external scheduler.

Bounded infrastructure validation: python -m unittest discover -s scripts/tests
-p 'test_*.py'. No product suites, database matrices or camera access needed.
The Memory direct-script import regression uses real isolated Python import
resolution and a source-only fixture, with only pip-check mocked.

This follow-up intentionally skips feature-suite CI. For AIR's existing PR #9,
the prior successful SHA remains recorded; the new infrastructure head is
not claimed validated. No PR is merged, marked complete or handed to replay.

On every stop, persist the five-field blocker receipt into CHECKPOINT_STATE,
commit/synchronize it, and verify remote SHA. .git/session-preflight.json alone
is ephemeral. Missing API/shell credentials, Actions service outages, quotas,
runner availability, the external hourly scheduler and a physical Mac cannot
be repaired solely by repository code. Report that exact external layer.

## AF-26 recorded retry-sequence receipt (2026-10-15)

AF-26 remains in progress. Source PR #39 added deterministic, fail-closed
verification for bounded recorded retry and outage sequences. It binds the
exact failure-plan evidence, environment evidence, trajectory evidence,
ordered attempts, observed hashes, outcomes and a fixed four-attempt ceiling.
It performs no network calls, sleeping, agent/tool execution, recovery action,
credential or payload handling, and makes no process or OS-isolation claim.

Exact pull-request head `02beb959f5357168cdf4a04bdeaf0a90e26cbf21`
passed CI run 38734703918 on Python 3.11.17 with 385 product tests, zero
failures and zero product skips. Guarded merge
`e89a1afd4ad2998854cfd6c6387234c794134863` passed merged-main CI run
38734820602 with the same 385/0/0 result. The canonical records change must
itself pass exact-head PR CI and merged-main CI before the writer slice is
released or this evidence is used to advance checkpoint acceptance.

## AF-26 bounded-scope acceptance closure (2026-10-15)

AF-26 is accepted only for deterministic recorded metadata. Source PRs #37 and
#39 cover all four roadmap fault kinds and exact plan/environment/trajectory
bindings, including ordered retries and a fixed four-attempt ceiling. Records
PRs #38 and #40 passed exact-head and merged-main CI and were explicitly
released. The final source tree is
`595c08d6bf25d6f93bcf6941013a8c29b0e9b977`; the latest accepted main before
this closure is `833495376f75ea8606b078fd27737b7dd987283c`.

No accepted path performs network calls, DNS, sleeping, retries, recovery,
agent/tool/command execution, project access, or credential/payload handling.
It claims no filesystem, process, network, or OS isolation. This closure must
pass its own exact-head PR and merged-main CI before the 4/12 acceptance record
is canonical and AF-27 work may begin.

## AF-27 recorded recovery/state-consistency receipt (2026-10-16)

Source PR #42 introduced deterministic, fail-closed verification of bounded
recorded recovery metadata. The evidence binds exact failure-plan, trajectory,
operation and idempotency hashes, enforces a contiguous state chain and one
commit at most, and proves that failed or duplicate replay records do not change
state. Source tree `9b4135caafe4a752c1b4d4af57d76ed77fa32a8c` passed exact-head PR CI
38850492412 and merged-main CI 38850574375 on Python 3.11.17 with 401 product
tests, zero failures and zero product skips. Main was
`234678fe214f86336832d1a901a9c5be8a5581aa`.

This is recorded-metadata verification only. It performs no retry, recovery,
agent/tool/command execution, project or durable-state access, external call,
credential/payload handling, or filesystem/process/network/OS isolation. This
records change requires its own exact PR and merged-main CI before release.

## AF-27 recorded retry-budget receipt (2026-10-16)

Source PR #44 added deterministic verification of a fixed retry budget bound to
the exact content hash of a recomputed recovery report. It caps recorded budgets
at eight attempts, rejects already-overrun budgets, and distinguishes recovered,
exhausted, and retry-permitted metadata states. A recovered report never permits
another retry merely because nominal budget remains.

Source head `fd71cf0f1597931ed575e165a8a0b9fb76c35e39`, tree
`43aa52b9353ab12141aed760b75dd520bd668c75`, passed exact-head PR CI
38886756075 on Python 3.11.17 with 409 product tests, zero failures and zero
product skips. Guarded merge `8992aa0e7dbbab05c73848694c972b3dac799a7b`
passed exact merged-main CI 38886830294 with the same 409/0/0 result.

This is metadata-only verification: no retry, recovery, sleeping, project or
durable-state access, agent/tool/command execution, external call, credential,
payload, or isolation claim. This records change requires independent exact-head
and merged-main CI before the writer slice is released.

## AF-27 recorded state-checkpoint receipt (2026-10-18)

Source PR #46 added deterministic validation that binds caller-supplied state
checkpoint metadata to the exact content hash of a recomputed recovery report.
It requires a bounded positive generation and exact initial/final recorded state
hashes. Recovered and incomplete transcripts preserve the existing state-chain
and no-commit invariants.

Source head `c556396d3caa982e70be914cedb12010804bce73`, tree
`dd0eb0c5cf5bac8f3469f85b48220b77f207939a`, passed exact-head PR CI
39089907017 on Python 3.11.17 with 419 product tests, zero failures and zero
product skips. Guarded merge `99ff09825e77613917c866591ebba37700412d40`
passed exact merged-main CI 39089947965 with the same 419/0/0 result.

This is metadata-only verification, not proof that durable storage was read,
written, restored or persisted. It adds no project access, retry/recovery action,
agent/tool/command execution, external call, credential/payload handling, or
filesystem/process/network/OS isolation. This records change requires its own
exact PR and merged-main CI before release.

## AF-27 recorded resume-guard receipt (2026-10-18)

Source PR #48 added deterministic verification that recomputes and binds exact
recovery, retry-budget, and state-checkpoint evidence into one disposition:
closed after recovery, closed after budget exhaustion, or a recorded resume
candidate with the next attempt number. The candidate is explicitly
non-authoritative and does not grant execution permission.

Source head `7d99425194774aab8f1d64aac1c27c744e302a45`, tree
`ce8e5b691c2527955108138022ab491df0f90ab3`, passed exact-head PR CI
39131567287 on Python 3.11.17 with 427 product tests, zero failures and zero
product skips. Guarded merge `f4588406d6c7cf12d9e8893386f106533d5d6556`
passed exact merged-main CI 39131630319 with the same 427/0/0 result.

This is metadata-only verification. It performs no retry, recovery, restore,
project/agent/tool/command execution, durable-state access, external call,
credential/payload handling, or filesystem/process/network/OS isolation. This
records change requires independent exact-head and merged-main CI before writer
release. AF-27 remains in progress and roadmap acceptance remains 4/12.

## AF-27 recorded terminal resume-closure receipt (2026-10-20)

Source PR #54 added deterministic closure verification for exact
content-addressed resume-lineage reports. It accepts only terminal
`closed_recovered` or `closed_exhausted` dispositions and fails closed for an
unfinished candidate, forged lineage, mismatched expected disposition, or
action-bearing metadata.

Source head `3f0e7332d8f8a929318ed794cb6143fbebb750cd`, tree
`6af927ea1bae1eefeea3da22ff7b34122ff09280`, passed exact-head PR CI
39386039725 on Python 3.11.17 with 450 product tests, zero failures and zero
product skips. Guarded merge `ecdfdc932a9501520f73313a2ae75014ba682ec3`
passed exact merged-main CI 39386156518 with the same 450/0/0 result.

This is metadata-only verification. It performs no retry, recovery, restore,
project/agent/tool/command execution, durable-state access, external call,
credential/payload handling, or filesystem/process/network/OS isolation. This
records change requires independent exact-head and merged-main CI before writer
release. AF-27 remains in progress and roadmap acceptance remains 4/12.

## AF-27 recorded resume-lineage receipt (2026-10-18)

Source PR #52 added deterministic verification for a bounded ordered lineage of
content-addressed resume transitions. It enforces exact guard-evidence,
attempt-count and checkpoint-generation continuity, rejects duplicate reports,
and fails closed if a transition follows a recovered or exhausted terminal
disposition.

Source head `20a775610f2a92369b895bddb63bc29a28ae5f6f`, tree
`a541d34f67e6c15d9986903ff8e59024d553533b`, passed exact-head PR CI
39185479785 on Python 3.11.17 with 442 product tests, zero failures and zero
product skips. Guarded merge `5d45a7ccee5146ab429094fb8b5d73809348f819`
passed exact merged-main CI 39185564505 with the same 442/0/0 result.

This is metadata-only verification. It performs no retry, recovery, restore,
project/agent/tool/command execution, durable-state access, external call,
credential/payload handling, or filesystem/process/network/OS isolation. This
records change requires independent exact-head and merged-main CI before writer
release. AF-27 remains in progress and roadmap acceptance remains 4/12.

## AF-27 recorded resume-transition continuity receipt (2026-10-18)

Source PR #50 added deterministic verification that one caller-supplied resume
transition extends a validated prior resume candidate by exactly one event. It
preserves the full recovery prefix and evidence bindings, advances the recorded
attempt and checkpoint generation exactly once, and fails closed on replay,
history alteration, skipped generations, action-bearing fields, and Boolean
schema values.

Source head `74310a2aca5091118d4692a043ba668310b4a8ae`, tree
`0e99662a7080c399088b7cdfedb6996e83e26e0d`, passed exact-head PR CI
39159042557 on Python 3.11.17 with 439 product tests, zero failures and zero
product skips. Guarded merge `d68706b245bd22a63bec854b68c08f1e1f1dc5d6`
passed exact merged-main CI 39159139603 with the same 439/0/0 result.

This is metadata-only verification. It performs no retry, recovery, restore,
project/agent/tool/command execution, durable-state access, external call,
credential/payload handling, or filesystem/process/network/OS isolation. This
records change requires independent exact-head and merged-main CI before writer
release. AF-27 remains in progress and roadmap acceptance remains 4/12.


## AF-27 bounded-scope acceptance closure (2026-10-20)

AF-27 is accepted only for deterministic recorded metadata. Seven independently
verified source/records pairs cover idempotency and state-chain invariants,
bounded retry budgets, exact state checkpoints, recomputed resume guards,
single-step transition continuity, bounded ordered lineage and terminal closure.
The latest canonical records are PR #55 at
`fd65a7cf5acdebb3269544517223fc494a00130a`, merged as
`07a79c9b001fd5597ed11cabd650f8211fa08bbc`; exact PR and merged-main CI runs 39386623417
and 39386694632 each passed all 450 product tests with zero failures or product
skips on Python 3.11.17.

No accepted path performs retry, recovery, restore, durable-state access,
agent/tool/command/project execution, external calls, credential/payload
handling, or filesystem/process/network/OS isolation. This closure requires its
own exact-head PR and merged-main CI before AF-28 starts.

## AF-28 bounded recorded-concurrency source receipt (2026-10-21)

Source PR #57 adds deterministic, fail-closed validation for caller-supplied
concurrent and multi-agent scenario metadata. It bounds two to eight participants
and one to sixty-four events, verifies one hashed tenant boundary, enforces
content-addressed participant chains and stable logical-time/participant ordering,
and requires deterministic conflict rejection without recorded state mutation.

Source head `4047ac8ef65622e7627950ae95b8fa67c671a5ca` passed exact-head
PR CI 39543240658 on Python 3.11.17 with 461 product tests, zero failures and
zero product skips. Guarded merge `12c03f3a2df97a299ed98e36630857df564ce3e5`
passed exact merged-main CI 39543334981 with the same 461/0/0 result.

This is recorded-metadata verification only. It starts no threads, processes,
agents, tools, projects, commands or network calls; accesses no credentials,
payloads, filesystem or durable state; and makes no resource-cap or OS-isolation
claim. This records change requires independent exact-head and merged-main CI
before writer release or another AF-28 source slice.

## AF-28 recorded resource-state-lineage source receipt (2026-10-21)

Source PR #59 adds a deterministic, exact-evidence-bound resource lineage over
the validated concurrent-scenario metadata. Every resource round requires one
shared recorded pre-state and exactly one accepted event; a later round must
begin at the prior accepted post-state, and an isolated conflict rejection fails
closed. Resources are tracked independently and the report exposes only hashes,
content-addressed event identifiers, bounded coverage, and final state hashes.

Source head `7c0c0b942229a9a88dd10f0ab189f0ae89c3d5dd`, tree
`bed10fc7d5490064a6b5f9a5382938710813c5d9`, passed exact-head PR CI
39584777028 on Python 3.11.17 with 466 product tests, zero failures and zero
product skips. Guarded merge `5b36cad43680532448a06e44d16f6945cbe5c85e`
passed exact merged-main CI 39584936518 with the same 466/0/0 result.

This is recorded-metadata verification only. It starts no threads, processes,
agents, tools, projects, commands or external calls; accesses no credentials,
payloads, filesystem or durable state; and makes no retry, recovery,
resource-cap or OS-isolation claim. This records change requires independent
exact-head and merged-main CI before writer release or another AF-28 source
slice. AF-28 remains in progress and roadmap acceptance remains 5/12.

## AF-28 recorded cross-agent causal-handoff source receipt (2026-10-21)

Source PR #61 adds deterministic verification for bounded caller-supplied
cross-agent causal handoff metadata. Each edge binds exact source and receiver
event identities from a validated concurrent schedule, requires registered
distinct participants and completed endpoints, and enforces strict event and
logical-time ordering. Unknown, mismatched, self, noncausal, duplicate,
nondeterministically ordered and action-bearing metadata fail closed.

Source head `59e964c2bf0654ca07a889af50191974444f53fb`, tree
`c9828596e82c9ad8d585529ebff2a350c6527176`, passed exact-head PR CI
39616728490 on Python 3.11.17 with 475 product tests, zero failures and zero
product skips. Guarded merge `ffe763a188e808d0557a678b6b7cec5d6475b3f0`
passed exact merged-main CI 39617458489 with the same 475/0/0 result.

This is recorded-metadata verification only. It starts no agents, threads,
processes, tools, projects or commands; reads or transfers no state, message,
artifact or payload; accesses no credentials or external systems; and makes no
retry, recovery, resource-cap or OS-isolation claim. This records change
requires independent exact-head and merged-main CI before writer release or
another AF-28 source slice. AF-28 remains in progress and roadmap acceptance
remains 5/12.

## AF-28 recorded cross-agent causal-handoff records receipt (2026-10-22)

Canonical records PR #62 head
`7a27ca356d13569dfaa7983806087d47233c3864` passed exact-head Python
3.11.17 CI 39618071176 with 475 product tests, zero failures and zero product
skips. Guarded merge `6328e9ba9871fd63d1b938a0b9fdb9d67e3b8916`
passed exact merged-main CI 39821897925 with the same 475/0/0 result. The prior
writer was explicitly released in PR #62 comment 6346891476.

No executable scope was added by the records-only change. AF-28 remains in
progress and roadmap acceptance remains 5/12.

## AF-28 bounded recorded quorum-barrier source candidate (2026-10-22)

This bounded source candidate validates caller-supplied quorum-barrier metadata
against exact events in an already validated recorded concurrent scenario. It
requires two to eight sorted registered participants, a non-Boolean quorum,
unique completed arrivals meeting that quorum, and a completed release event
strictly after every arrival. Barrier roles cannot reuse event identities, and
normalized evidence is deterministic and content-addressed.

Local Python 3.11.17 validation passed all 35 focused concurrency tests and all
483 portable product tests. The unfiltered local suite has only the two
established container-specific `/proc` descendant-observation failures.
Infrastructure validation passed 17 checks with one documented Memory-only
skip; dependency, import, compile and environment diagnostics passed.

This is recorded-metadata verification only. It performs no waiting,
scheduling, coordination, execution or transfer; starts no agents, threads,
processes, tools, projects or commands; accesses no credentials, payloads,
filesystem, durable state or external systems; and makes no resource-cap or
OS-isolation claim. Source and canonical records still require independent
exact-head and merged-main CI before writer release. AF-28 remains in progress
and roadmap acceptance remains 5/12.

## AF-28 recorded quorum-barrier source receipt (2026-10-22)

Source PR #63 head `dbb4390ed1d9b3536130daeb52be88722b859862`,
tree `e3c96509ea23a931c826b363483ac896461dec75`, passed exact-head
Python 3.11.17 CI 39831615764 with 485 product tests, zero failures and
zero product skips. Guarded merge
`f632ab4a26488f75a981ce4c833f76475b74ec84` passed exact merged-main
CI 39831774279 with the same 485/0/0 result.

This is recorded-metadata verification only. It performs no waiting,
scheduling, coordination, execution or transfer; starts no agents, threads,
processes, tools, projects or commands; accesses no credentials, payloads,
filesystem, durable state or external systems; and makes no resource-cap or
OS-isolation claim. This records change requires independent exact-head and
merged-main CI before writer release or another AF-28 source slice. AF-28
remains in progress and roadmap acceptance remains 5/12.

## AF-28 recorded capacity-budget source candidate (2026-10-22)

This bounded slice binds per-participant event counts and distinct resource-key
counts to exact concurrent-scenario evidence and rejects missing, reordered,
Boolean, oversized, or overrun caller-declared caps.

This is metadata-only accounting. It performs no execution, scheduling,
waiting, resource allocation or enforcement; starts no agents, threads,
processes, tools, projects or commands; and makes no runtime resource-cap,
filesystem, network, process or OS-isolation claim. Exact Python 3.11 PR and
merged-main CI are required before canonical records or writer release.

## AF-28 recorded capacity-budget source receipt (2026-10-22)

PR #65 head `86cb28ee9090bfeb4f2d7eeb64575e3fde306df0`, tree
`e010c7385a1586780d84b71eaf669b2f5ee71760`, passed exact-head Python
3.11.17 CI 39871905292 with 489 product tests and zero product skips. Guarded
merge `31682f750a40055a45be49513d1d4b82df49454f` passed exact merged-main
CI 39872066120 with the same 489/0/0 result.

The verifier binds recorded per-participant event counts and distinct resource
keys to exact concurrent-scenario evidence and caller-declared caps. It performs
no runtime allocation or enforcement and grants no execution or isolation
authority. This records-only change requires its own exact PR and merged-main
CI before writer release.

## AF-28 bounded-scope acceptance closure candidate (2026-10-22)

AF-28 acceptance is supported by five independently verified source/records
pairs: deterministic recorded scheduling and conflict rejection (#57/#58),
resource-state lineage and tenant isolation (#59/#60), causal handoffs (#61/#62),
quorum barriers (#63/#64), and capacity-budget evidence (#65/#66). The latest
records head `aef8dd2769d1120d69c75d9678b1818d729e3239` and resulting main
`4f4d0ab2b90f4493ad5859b5e58a2d1ca746dd03` passed exact Python 3.11.17
CI runs 39872276338 and 39872366099 with 489 product tests and zero product
skips. The writer release is recorded on PR #66.

This acceptance is strictly metadata-only. It does not start real agents,
threads, processes, tools or commands; perform waiting, scheduling,
coordination, execution, allocation or enforcement; access state, payloads,
credentials, filesystems, networks or external systems; or claim runtime
resource limits or OS isolation. Final acceptance requires this closure change
to pass exact PR-head and merged-main CI before its writer is released.

## AF-29 recorded permission-boundary source candidate (2026-10-23)

This bounded candidate compares caller-supplied recorded authorization decisions
with a deterministic fail-closed oracle. Cross-tenant authorization,
untrusted-content control, caller-recorded injection findings and requests beyond
exact granted scopes require denial. Evidence contains hashes and bounded scope
identifiers only; it excludes raw prompts, payloads and credentials.

This is synthetic recorded-metadata verification, not an authorization system.
It reads no project or prompt, invokes no tool, agent or command, accesses no
filesystem, network, credential or external system, grants no permission, and
makes no arbitrary-execution or OS-isolation claim. Exact Python 3.11 PR and
merged-main CI are required before canonical records or writer release. AF-29
remains in progress and roadmap acceptance remains 6/12.

## AF-29 permission-boundary source receipt (2026-10-23)

- Source PR #68: head `01d73281f39afb7338137f3df10d6d29a8cf8b59`, tree `7f6ba51744545bfc10902e4f907439afa73b0545`.
- Exact PR run 39900570012: Python 3.11.17, 504 product tests passed, zero
  product skips; infrastructure 17 passed with one baseline Memory-only skip.
- Guarded merge: exact main `5330726fd81bf1b6071fdd72b825e89ed47edd6b`.
- Exact merged-main run 39900701428: the same 504-test suite passed with zero
  product skips; infrastructure 17 passed with one baseline Memory-only skip.
- Scope remains synthetic recorded-metadata verification only. It grants no
  permissions and performs no raw prompt/payload/credential access, project
  inspection, live execution, external action, resource enforcement or
  OS-sandbox validation. AF-29 remains in progress at 6/12 accepted.

## AF-29 recorded instruction-provenance source candidate (2026-10-23)

This bounded candidate recomputes exact permission-boundary evidence and binds
it to caller-supplied trusted and observed instruction hashes. Acceptance
requires matching hashes, a trusted-control source, no recorded policy-override
attempt, and an underlying security decision that both passes its oracle and
permits authorization. Substitution, untrusted instruction sources,
denial-required or inconsistent security decisions, override attempts,
malformed metadata and action-bearing fields fail closed.

The verifier processes hashes and bounded metadata only. It reads no prompt or
instruction text, detects no injection itself, grants no permission, invokes no
agent, tool or command, and accesses no project, payload, credential,
filesystem, network or external system. It makes no arbitrary-execution,
resource-enforcement or OS-isolation claim. Exact Python 3.11 PR and
merged-main CI remain required before a source receipt or writer release.

## AF-29 recorded instruction-provenance source receipt (2026-10-23)

- Source PR #70: head `18d326c096671988f34162d98f2ed48e0344f2e9`, tree `c6bd70346fdf515bbbf29c781a7c6db381a4bb95`.
- Exact PR run 39939002114: Python 3.11.17, 516 product tests passed,
  zero product skips; infrastructure 17 passed with one baseline Memory-only
  skip.
- Guarded merge: exact main `d3f8723f2269d22e905533df8aaeb3187af92dea`.
- Exact merged-main run 39939139774: the same 516-test suite passed with zero
  product skips; infrastructure 17 passed with one baseline Memory-only skip.
- Scope remains synthetic recorded-metadata verification only. It reads no raw
  prompt or instruction text, detects no injection, grants no permission, and
  performs no project inspection, live execution, credential/payload access,
  external action, resource enforcement or OS-sandbox validation. AF-29 remains
  in progress at 6/12 accepted.

## AF-29 recorded multi-hop influence-lineage source receipt (2026-10-23)

This bounded candidate recomputes exact permission and instruction-provenance
evidence for two to sixteen ordered hops. It binds every hop input to its
recorded provenance, requires hash continuity between adjacent hops, and
propagates recorded untrusted-content or injection influence through every
downstream hop. Affected lineages require rejection; evidence substitution,
discontinuity, duplicate hop identities, malformed metadata and action-bearing
fields fail closed.

This is synthetic recorded-metadata verification only. It reads no raw prompt,
instruction, payload or credential, performs no injection detection, grants no
permission, and invokes no project, agent, tool or command. It accesses no
filesystem, network or external system and makes no arbitrary-execution,
resource-enforcement or OS-isolation claim.

Source PR #72 head `17a4481e04e1a3eab5e35144d2f2877159acae89`, tree
`307efa7409053d0d426dde7701204ca17870cae5`, passed exact-head run
39978381724 on Python 3.11.17 with 529 product tests and zero product skips.
Guarded merge produced main `31a83bed71303cbf1dc02b8f5484e7b943f27dab`;
exact push run 40002769894 passed the same 529-test suite with zero product
skips. Both runs executed 18 infrastructure guards: 17 passed and one baseline
Memory-only case was skipped. Canonical records require independent exact PR
and merged-main CI before writer release. AF-29 remains in progress at 6/12.

## AF-29 recorded sensitive-sink boundary source candidate (2026-10-24)

This bounded candidate recomputes and binds the exact multi-hop influence
lineage and terminal authorization evidence before comparing one recorded sink
disposition with a deterministic fail-closed oracle. Four fixed sink classes
map to fixed least-privilege scopes. A lineage requiring rejection, any
propagated untrusted influence, an inconsistent terminal authorization, or a
missing sink scope requires rejection. A later trusted hop cannot clear earlier
untrusted or caller-recorded injection influence.

This is synthetic recorded-metadata verification only. It reads no prompt,
instruction, payload, credential, project, filesystem, or network; detects no
injection; grants no permission; invokes no agent, tool, or command; and performs
no external action or OS-sandbox validation. Exact Python 3.11 PR and
merged-main CI passed at source head and exact merged main. PR #74 head
`4ff776c745f496b3d1774b617e42c48f10250756` passed run 40045081892 with
542 product tests and zero product skips; guarded merge produced main
`da712d3da89d0a6bb2b4e31cf4a19231163c847a`, whose push run 40045159092
passed the same suite. Records PR #75 head
`6d65ac5c8b0d052b90ad245097f438b0c3cf2cb6` passed exact run
40045393444; guarded merge produced main
`6352831c9d88f0da482394b45bd58db0c47286c9`, whose exact push run
40045473396 passed 542 product tests with zero skips. The writer was explicitly
released on PR #75. AF-29 remains in progress at 6/12.

## AF-29 recorded sensitive-sink binding candidate (2026-10-24)

This bounded candidate recomputes the exact sensitive-sink boundary and binds
its input to the terminal lineage output hash and its authorized tool identity
to the terminal authorization decision. It requires rejection for substituted
inputs, confused-deputy tool substitution, inconsistent upstream evidence, or
false recorded acceptance.

This is synthetic recorded-metadata verification only. It reads no raw prompt,
instruction, payload, credential, project, filesystem, or network; detects no
injection; grants no permission; invokes no agent, tool, or command; and makes
no execution, external-action, resource-enforcement, or OS-isolation claim.
Exact Python 3.11 PR and merged-main CI are required before canonical records
or writer release. AF-29 remains in progress at 6/12 accepted.

## AF-29 recorded sensitive-sink binding source receipt (2026-10-24)

Source PR #76 head `8734496bb7ce3c4b07712dbe5393f4fd68a56667`, tree
`96e6a716565872e176216d14fbe093bf6336375b`, passed exact-head run
40085375517 on Python 3.11.17 with 553 product tests and zero product skips.
Guarded merge produced exact main
`2af2b3b1610d7757b68f359a022c583d15b79b0f`; push run 40085452875 passed
the same suite. Both runs executed 18 infrastructure guards: 17 passed and one
baseline Memory-only case was skipped.

This remains bounded synthetic recorded-metadata verification with no tool
authorization or execution, secret or raw-content access, external action,
resource-enforcement claim, or OS-sandbox claim. Independent records PR and
merged-main CI remain required before writer release. AF-29 remains in progress
at 6/12 accepted.

## AF-29 recorded scope-attenuation source candidate (2026-10-24)

The prior sensitive-sink binding slice is fully recorded and writer-released:
records PR #77 head `9f4063464435895a20cf13fba4b8029c0e0cbbea`
and resulting main `f71508e7d616fa5e02f1429c9ce8c68b0bbd9ad4`
passed exact Python 3.11.17 CI runs 40085669930 and 40085736916 with
553 product tests and zero product skips.

This bounded candidate recomputes that complete sink-binding evidence before
checking one caller-supplied recorded delegation. Tenant, principal and tool
identity must remain exact, and delegated scopes must be a subset of the
terminal authorization's requested scopes. Cross-tenant delegation, identity
substitution, tool substitution, scope amplification, inconsistent evidence,
malformed metadata and false recorded acceptance fail closed.

Local Python 3.11.17 validation passed 78 focused security tests and 565
portable product tests. Infrastructure executed 18 guards: 17 passed and the
documented Memory-only case was skipped. Diagnostics, dependency checks,
compile, JSON validation and diff checks passed.

This is synthetic recorded-metadata verification only. It delegates and grants
nothing, reads no raw prompt, instruction, payload or credential, detects no
injection, invokes no project, agent, tool or command, accesses no filesystem,
network or external system, and makes no resource-enforcement or OS-isolation
claim. Exact source PR and merged-main CI plus independent canonical records
remain required before writer release. AF-29 remains in progress at 6/12.

## AF-29 recorded scope-attenuation source receipt (2026-10-24)

Source PR #78 head `fc1c298805379052326ed1ed73a7784c08e7152d`,
tree `e2b18ffe41ba3e02a8f8d5119e5cf0a9cdf8064b`, passed exact-head
run 40102865929 on Python 3.11.17 with 567 product tests and zero product
skips. Guarded merge produced main
`1ed9e1554a6c2a47caf73cc7b42046a245a4780f`; exact push run
40102928767 passed the same suite. Both runs executed 18 infrastructure guards:
17 passed and one baseline Memory-only case was skipped.

This remains bounded synthetic recorded-metadata verification only. It grants
or delegates no permission, reads no raw prompt, instruction, payload or
credential, detects no injection, invokes no project, agent, tool or command,
accesses no filesystem, network or external system, and makes no
resource-enforcement or OS-isolation claim. Independent canonical records and
their exact CI remain required before writer release. AF-29 remains in progress
at 6/12.

## AF-29 recorded delegation-validity source candidate (2026-10-24)

Scope-attenuation records PR #79 and resulting main
`9ab2d9a9d1256f617fd917bca03234303818fa14` passed exact Python 3.11.17
CI runs 40103172689 and 40103257328 with 567 product tests and zero product
skips. Writer `AF29-SCOPE-ATTENUATION-20261024` was explicitly released.

The new bounded candidate recomputes exact scope-attenuation evidence and
checks one caller-supplied logical validity window plus an explicit revocation
flag. Observation is valid only at or after issuance and strictly before
expiry. Pre-issuance, expiry, revocation, inconsistent upstream evidence,
malformed ticks, and false recorded acceptance fail closed. It uses no system
clock and takes no expiry or revocation action.

Local Python 3.11.17 validation passed 95 focused security tests and 582
portable product tests. Infrastructure executed 18 guards: 17 passed and one
documented Memory-only case skipped. Two unfiltered descendant-observation
failures reproduced on untouched main; one read-race failure passed isolated
and on the clean portable rerun. Diagnostics, dependency checks, compile, JSON
validation and diff checks passed.

This is synthetic recorded-metadata verification only. It grants, delegates or
revokes nothing; reads no raw prompt, instruction, payload or credential;
detects no injection; invokes no project, agent, tool or command; accesses no
filesystem, network or external system; and makes no resource-enforcement or
OS-isolation claim. Exact source PR and merged-main CI plus independent records
remain required before writer release. AF-29 remains in progress at 6/12.

## AF-29 recorded delegation-validity source receipt (2026-10-24)

Source PR #80 head `87842fca19c6fbc94179f7895159ee16133e1961`,
tree `d211bb98677ff3f2e14aa018dea1e94991613641`, passed exact-head run
40107157624 on Python 3.11.17 with 584 product tests and zero product skips.
Guarded merge produced main `013bf40d3dd7c1676c2ab43fb83f587ccd66dd13`;
exact push run 40107229166 passed the same suite. Both runs executed 18
infrastructure guards: 17 passed and one baseline Memory-only case was skipped.

This remains bounded synthetic recorded-metadata verification only. It grants,
delegates or revokes nothing; reads no wall clock, raw prompt, instruction,
payload or credential; schedules no expiry; detects no injection; invokes no
project, agent, tool or command; accesses no filesystem, network or external
system; and makes no resource-enforcement or OS-isolation claim. Independent
canonical records and their exact CI remain required before writer release.
AF-29 remains in progress at 6/12.

## AF-29 delegation resource-binding source receipt (2026-10-26)

Source PR #96 head `53d2d7e619f891cb82fd45c0b0ea3ee4f4b4a98f`,
tree `93332a6232f178e37056ca0686bf9406c539958d`, passed exact Python
3.11.17 PR run 40438330528 with 675 product tests and zero product skips.
Expected-head guarded merge `475a9f0136d7dd6ef146dd01d6455e3e6bc9f0f1`
passed exact main-push run 40438443643 with the same result. Both runs executed
18 infrastructure guards: 17 passed and one established Memory-only case
skipped. Diagnostics passed.

This remains bounded synthetic recorded-metadata verification only. It proves
no resource existence, ownership or accessibility, grants or exercises no
authority, executes nothing, reads no raw content or secrets, and makes no
resource-enforcement or OS-isolation claim. Independent canonical records and
exact PR/final-main CI are required before writer release. AF-29 remains in
progress at 6/12.

## AF-29 recorded delegation-chain consistency source receipt (2026-10-25)

Source PR #82 exact head `b6dfe1a56d1fe3322357743c7559b33a08c52647`,
tree `7b0ce0c692b9886d5a3017e0d9f1062be16ddbf9`, passed exact-head run
40150452926 on Python 3.11.17 with 597 product tests and zero product skips.
Guarded merge produced exact main
`d1025f74f5fa1f7793779fa53861bbe50bc48ad4`; push run 40150534159 passed
the same suite. Both runs executed 18 infrastructure guards: 17 passed and one
baseline Memory-only case was skipped.

This remains bounded synthetic recorded-metadata verification only. It grants,
delegates, revokes or executes nothing; reads no wall clock, raw prompt,
instruction, payload or credential; detects no injection; invokes no project,
agent, tool or command; accesses no filesystem, network or external system; and
makes no resource-enforcement or OS-isolation claim. Independent canonical
records and their exact CI remain required before writer release. AF-29 remains
in progress at 6/12.

## AF-29 recorded delegation-chain consistency candidate (2026-10-24)

Delegation-validity records PR #81 and final main
`7ceb9012fb29dbf822a98bb8308f038a0df47fb5` passed exact Python 3.11.17
CI runs 40107462361 and 40107550251 with 584 product tests and zero product
skips. Writer `AF29-DELEGATION-VALIDITY-20261024` was explicitly released.

This bounded candidate recomputes exact delegation-validity evidence for two
to eight recorded hops and verifies that each hop's upstream tenant, principal,
tool and scope set exactly matches the prior hop's delegated endpoint. It fails
closed for independently self-consistent but disconnected or substituted hops,
rejected validity windows, inconsistent evidence, duplicate hop identifiers,
malformed metadata and false recorded acceptance.

Local Python 3.11.17 validation passed 108 focused security tests and 595
portable product tests. The unfiltered run retained the two established
container-specific descendant-observation failures. Infrastructure executed 18
guards: 17 passed and the documented Memory-only case skipped. Diagnostics,
dependency checks, compile and diff checks passed.

This is synthetic recorded-metadata verification only. It grants, delegates,
revokes or executes nothing; reads no wall clock, raw prompt, instruction,
payload or credential; detects no injection; invokes no project, agent, tool or
command; accesses no filesystem, network or external system; and makes no
resource-enforcement or OS-isolation claim. Exact source PR and merged-main CI
plus independent canonical records remain required before writer release.
AF-29 remains in progress at 6/12.

## AF-29 recorded delegation-time attenuation candidate (2026-10-25)

Delegation-chain consistency records PR #83 and final main
`35724f76632e4fde961719a34d6df5c2005f6667` passed exact Python 3.11.17
CI runs 40169050783 and 40169108584 with 597 product tests and zero product
skips. Writer `AF29-DELEGATION-CHAIN-CONSISTENCY-20261024` was explicitly
released.

The new bounded candidate recomputes exact delegation-chain evidence and
checks that every recorded child validity window is contained by its parent.
It fails closed when a child is issued before its parent, is issued at or after
the parent expiry boundary, outlives its parent, carries inconsistent evidence,
uses malformed or action-bearing metadata, or records a false acceptance. Equal
parent/child boundaries are accepted. Only caller-supplied logical ticks are
used; no wall clock is accessed.

Local Python 3.11.17 validation passed 120 focused security tests and 607
portable product tests. Infrastructure executed 18 guards: 17 passed and the
documented Memory-only case skipped. Diagnostics, dependency checks, compile,
JSON validation and diff checks passed.

This is synthetic recorded-metadata verification only. It grants, delegates,
revokes or executes nothing; reads no wall clock, raw prompt, instruction,
payload or credential; schedules no expiry; detects no injection; invokes no
project, agent, tool or command; accesses no filesystem, network or external
system; and makes no resource-enforcement or OS-isolation claim. Exact source
PR and merged-main CI plus independent canonical records remain required before
writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation issuer-binding source receipt (2026-10-26)

Source PR #92 exact head `18e02e4e0fe8a1711a9c97a5ddd42fb4047050ad`,
tree `5cf0c99bec86b43210f2d65a0a4f40ffd458ade6`, passed exact-head
Python 3.11.17 run 40314961276 with 653 product tests and zero product skips.
Its expected-head guarded merge produced main
`8308ce0c5cd06e7cf3bf552793e5a0641eb59313`; push run 40315063097 passed
the same result. Both ran 18 infrastructure guards: 17 passed and one
established Memory-only case skipped. Diagnostics passed.

This remains synthetic recorded evidence only: no live authentication,
identity proof, authorization, delegation, revocation, execution, raw-content
or secret access, resource enforcement, or OS isolation is claimed.
Independent canonical records and exact PR/final-main CI remain required
before writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation action-coherence source receipt (2026-10-28)

Source PR #103 exact head
`7de7f0d60501ba652396b34fcd8abfabacafbdac`, tree
`76ea04c2ca54b75727daecfe0493305749713c0d`, passed Python 3.11.17
exact-head run 40696268682 with 708 product tests, zero failures and zero
product skips. Expected-head guarded merge
`7a8d8d90e133e2a45f746745de6c06598de9665d` passed exact main-push run
40696475743 with the same result. Both runs executed all 18 infrastructure
guards: 17 passed and one established Memory-only case skipped. Dependency
diagnostics passed.

The verifier recomputes exact action-scope and action-target component evidence,
requires accepted components and binds them to one delegation-chain evidence
identifier. Mixed-chain substitution, stale evidence, component rejection or
false acceptance, malformed metadata and false coherence acceptance fail
closed.

This remains bounded synthetic recorded-metadata verification only. It performs
no live authorization, delegation, revocation, action or execution, reads no
raw content or secrets, and makes no resource-enforcement, sandboxing or
OS-isolation claim. Independent canonical records and their exact PR/final-main
CI remain required before writer release. AF-29 remains in progress at 6/12.

## AF-29 recorded delegation-time attenuation source receipt (2026-10-25)

Source PR #84 exact head `44f886036886daa9f78f1c4121275647e28c2ac7`,
tree `2257db4dbb28227f7919f262d65082ced938ab4d`, passed exact-head run
40197618231 on Python 3.11.17 with 609 product tests and zero product skips.
Guarded merge produced exact main
`41ae378777927fc3f3c34712afc047c2cf01f7bf`; push run 40197704994 passed
the same suite. Both runs executed 18 infrastructure guards: 17 passed and one
baseline Memory-only case was skipped.

This remains bounded synthetic recorded-metadata verification only. It grants,
delegates, revokes or executes nothing; reads no wall clock, raw prompt,
instruction, payload or credential; schedules no expiry; detects no injection;
invokes no project, agent, tool or command; accesses no filesystem, network or
external system; and makes no resource-enforcement or OS-isolation claim.
Independent canonical records and their exact CI remain required before writer
release. AF-29 remains in progress at 6/12.

## AF-29 redelegation-depth attenuation source candidate (2026-10-25)

Delegation-time attenuation records PR #85 head
`2b9a221cdb9187a97300a1912971793d75aea07e` passed exact run
40216399903. Guarded merge produced final main
`be1ab1b2b2bbffb38d44601aefaed56a67310542`; run 40216466618 passed.
Python 3.11.17 executed 609 product tests with zero product skips, and the prior
writer is explicitly released.

The new candidate verifies a strict decrease in bounded recorded remaining
redelegation capacity at every child hop after recomputing exact chain evidence.
Local Python 3.11.17 validation passed 135 focused and 622 portable tests;
infrastructure executed 18 guards, with 17 passed and one established
Memory-only skip. It is synthetic recorded metadata only and adds no live
authorization, delegation, revocation, execution, clock, raw-content, secret,
resource-enforcement or OS-isolation capability. Exact source PR and
merged-main CI plus separate canonical records remain required.

## AF-29 redelegation-depth attenuation source receipt (2026-10-25)

Source PR #86 exact head `ea266d31fce48f2951dfaa604d99e7fa494befd4`,
tree `d3e42e556039b8aa63d35c79abe2d2066f397840`, passed exact-head CI
40221470617 on Python 3.11.17 with 624 product tests and zero skips. Its
expected-head guarded merge produced main
`64f57b1b61060617564aed2afa502fbff8f99f22`; exact push CI 40221547636
passed the same product suite. Each run executed 18 infrastructure guards:
17 passed and one established Memory-only case skipped.

The verifier remains bounded and synthetic: it exercises no live authority,
delegation, revocation, execution, clock, raw-content, secret, filesystem,
network, resource-enforcement or OS-isolation capability. Separate canonical
records and exact PR/final-main CI remain required before writer release.

## AF-29 delegation replay-guard source candidate (2026-10-25)

Redelegation-depth records PR #87 head
`916df600585e3b64a005d138d1d7d1e26ddfad1e` passed exact run
40240133717. Its guarded merge produced final main
`202e98f2bb1ea601d1ead6ebdd012a834a6ac5be`; run 40240212181 passed.
Python 3.11.17 executed 624 product tests with zero skips, and writer
`AF29-REDELEGATION-DEPTH-ATTENUATION-20261025` is explicitly released.

The new candidate recomputes bounded delegation-chain evidence and rejects
replayed delegation-validity identities or evidence across differently named
hops. Local Python 3.11.17 validation passed 144 focused and 631 portable
tests; infrastructure executed 18 guards, with 17 passed and one established
Memory-only skip. It is synthetic recorded metadata only and provides no live
replay prevention, authorization, delegation, revocation, execution, clock,
raw-content, secret, resource-enforcement or OS-isolation capability. Exact
source PR and merged-main CI plus separate canonical records remain required.

## AF-29 delegation replay-guard source receipt (2026-10-26)

Source PR #88 exact head `534178dfe7d365e2a13e389fb343d29945f176d8`,
tree `6cec8fb37515259d5f17d61be1d489b6dc07d29f`, passed exact-head run
40268771803 on Python 3.11.17 with 633 product tests and zero product skips.
Its expected-head guarded merge produced exact main
`8d3d50d98f7ceaf454ff99937d6b81b7d693bc57`; exact push run
40268830559 passed the same product suite. Each run executed 18 infrastructure
guards: 17 passed and one established Memory-only case skipped. Diagnostics
passed.

This remains bounded synthetic recorded-metadata verification only. It does
not prevent live replay, grant, delegate or revoke authority, execute an agent,
tool or command, read a wall clock or raw content, access secrets, filesystems,
networks or external systems, or establish resource enforcement or OS
isolation. Independent canonical records and exact PR/final-main CI remain
required before writer release. AF-29 remains in progress at 6/12.

## AF-29 audience-binding release and issuer-binding source candidate (2026-10-26)

Audience-binding records PR #91 head
`5f7a4bf2eff04dafe7856a844331d0e419573226`, tree
`92abb4db5c2503e4bc8a5b4c5ac0d100ca4a861b`, passed exact-head Python
3.11.17 run 40281102603 with 643 product tests and zero product skips. Its
guarded merge produced final main
`f9fe538e09c716b971afbf93f8dd1ed5de93b641`; push run 40281193243 passed
the same result. Both ran 18 infrastructure guards: 17 passed and one
established Memory-only case skipped. Writer
`AF29-DELEGATION-AUDIENCE-BINDING-20261026` is explicitly released on PR #91.

The issuer-binding candidate recomputes bounded delegation-chain and per-hop
scope-attenuation evidence, then requires each recorded issuer-principal hash
to match the upstream principal bound by that hop. Local Python 3.11.17
validation passed 164 focused security tests and 651 portable product tests;
all 18 infrastructure guards executed, with 17 passed and the established
Memory-only case skipped. Diagnostics, dependency, import, compile, JSON and
diff checks passed.

This is synthetic recorded evidence only: no live authentication, identity
proof, authorization, delegation, revocation, execution, raw-content or secret
access, resource enforcement, or OS isolation is claimed. Exact source PR and
merged-main CI plus independent canonical records remain required before
writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation replay-guard release and audience-binding candidate (2026-10-26)

Replay-guard records PR #89 head
`b6662d39e79c116d0ffcbba0ec23efb1cd08717a`, tree
`f5a79a6f0efbf98147d9c9a2e9ebf0a97bb35413`, passed exact-head run
40269186419 on Python 3.11.17 with 633 product tests and zero product skips.
Its guarded merge `a14dcbc1f181cf0c4f6b90f116c146ec53fb2564`
passed exact push run 40269255336 with the same product result. Both runs
executed 18 infrastructure guards: 17 passed and one established Memory-only
case skipped. Writer `AF29-DELEGATION-REPLAY-GUARD-20261025` is explicitly
released on PR #89.

The new audience-binding candidate recomputes exact delegation-chain evidence
and requires each hop's intended-audience hash to equal its already-bound
delegated-principal hash. Recipient substitution, evidence substitution,
malformed or action-bearing metadata, and false recorded acceptance fail
closed. Local Python 3.11.17 validation passed 154 focused and 641 portable
product tests; infrastructure executed 18 guards, with 17 passed and one
established Memory-only skip. Diagnostics, compile, JSON and diff checks passed.

This remains bounded synthetic recorded-metadata verification only. It proves
no live identity or audience possession, grants or exercises no authority,
executes nothing, reads no raw content or secrets, and makes no resource or
OS-isolation claim. Exact source PR and merged-main CI plus independent
canonical records remain required before writer release. AF-29 remains in
progress at 6/12.

## AF-29 delegation identity-binding source receipt (2026-10-26)

Source PR #94 head `7d3ee69f74aaf364c850ade40060e2b1e5577137`,
tree `d3e83723d5e8684f2dced9045ebc902c07ff6cd5`, passed exact Python
3.11.17 PR run 40367858343 with 664 product tests and zero product skips.
Expected-head guarded merge `16c3980c6f41e440f3294a02da9f92cb8a549a13`
passed exact main-push run 40403503108 with the same result. Both runs executed
18 infrastructure guards: 17 passed and one established Memory-only case
skipped. Diagnostics passed.

This remains bounded synthetic recorded-metadata verification only. It proves
no live identity, authentication, audience possession or authorization, grants
or exercises no authority, executes nothing, reads no raw content or secrets,
and makes no resource or OS-isolation claim. Independent canonical records and
exact PR/final-main CI are required before writer release. AF-29 remains in
progress at 6/12.

## AF-29 delegation audience-binding source receipt (2026-10-26)

Source PR #90 head `8885ec92e591dcc49dd5ac6cea046ada383cca35`,
tree `9852461c1cc595ded45110e9c056fc8fec0550f0`, passed exact Python
3.11.17 PR run 40280206622 with 643 product tests and zero product skips.
Expected-head guarded merge `2e63a17d2eda38f05883053789e071493455b1fb`
passed exact main-push run 40280324997 with the same result. Both runs executed
18 infrastructure guards: 17 passed and one established Memory-only case
skipped. Diagnostics passed.

This remains bounded synthetic recorded-metadata verification only. It proves
no live identity or audience possession, grants or exercises no authority,
executes nothing, reads no raw content or secrets, and makes no resource or OS
isolation claim. Independent canonical records and exact PR/final-main CI are
required before writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation identity-binding source candidate (2026-10-26)

Delegation issuer-binding source/records PRs #92/#93 passed their exact Python
3.11.17 PR and merged-main CI gates. Final main is
`d70385a85222b4018f9cd32bcfbeab99b377b7ac`, and writer
`AF29-DELEGATION-ISSUER-BINDING-20261026` is explicitly released.

The new candidate independently recomputes exact issuer- and audience-binding
evidence, requires both components to be accepted, and rejects substitution
between otherwise valid reports for different delegation chains. Local Python
3.11.17 validation passed 175 focused security tests and 662 portable product
tests. All 18 infrastructure guards executed: 17 passed and the established
Memory-only case skipped. Diagnostics, dependency, import, compile, JSON and
diff checks passed. The unrestricted suite reproduced only the two established
container-specific descendant-observation failures.

This is bounded synthetic recorded-metadata verification only. It performs no
live authentication or identity proof, grants or exercises no authority,
executes nothing, reads no raw content or secrets, and makes no resource or
OS-isolation claim. Exact source PR and merged-main CI plus independent
canonical records remain required before writer release. AF-29 remains in
progress at 6/12.

## AF-29 delegation resource-binding source candidate (2026-10-26)

Identity-binding source/records PRs #94/#95 passed their exact Python 3.11.17
PR and merged-main gates through
`d75b1c3104214a30302591e7eba61bfe840751b8`; writer
`AF29-DELEGATION-IDENTITY-BINDING-20261026` is explicitly released.

The new candidate independently recomputes exact delegation-chain evidence and
each hop's nested sensitive-sink binding, then requires the caller-supplied
recorded resource hash to equal the sink-input hash already bound by that hop.
Resource substitution, stale nested evidence, malformed or action-bearing
metadata, and false recorded acceptance fail closed. Local Python 3.11.17
validation passed 186 focused security tests and 673 portable product tests.
All 18 infrastructure guards executed: 17 passed and the established
Memory-only case skipped. Diagnostics, dependency, import, compile, JSON and
diff checks passed. The unrestricted suite reproduced only the two established
container-specific descendant-observation failures.

This is bounded synthetic recorded-metadata verification only. It proves no
resource existence, ownership or accessibility, grants or exercises no
authority, executes nothing, reads no raw content or secrets, and makes no
resource-enforcement or OS-isolation claim. Exact source PR and merged-main CI
plus independent canonical records remain required before writer release.
AF-29 remains in progress at 6/12.

## AF-29 resource-binding release and action-scope-binding candidate (2026-10-26)

Resource-binding records PR #97 exact head
`43f1143c2563c399e0b5bee0ed9398c7b4143d8d`, tree
`64601fef41bdd7fde6889190e1bbb412710d0746`, passed Python 3.11.17
exact-head run 40438868269 with 675 product tests and zero product skips. Its
expected-head merge produced final main
`beea83cd38a884ac866b6dede7356e80ffbc4cbb`; push run 40438987232 passed
the same suite. Each run executed all 18 infrastructure guards: 17 passed and
one established Memory-only case skipped. Writer
`AF29-DELEGATION-RESOURCE-BINDING-20261026` is explicitly released on PR #97.

The new bounded candidate recomputes exact delegation-chain and per-hop
scope-attenuation evidence, then requires each caller-supplied recorded action
scope set to exactly match the delegated scopes already bound by that hop.
Action-scope substitution, stale nested evidence, malformed or action-bearing
metadata, and false recorded acceptance fail closed. Local Python 3.11.17
validation passed 197 focused security tests and 684 portable product tests.
All 18 infrastructure guards executed: 17 passed and the established
Memory-only case skipped. Diagnostics, dependency, import, compile, JSON and
diff checks passed.

This is bounded synthetic recorded-metadata verification only. It performs no
live authorization, delegation, revocation, action or execution, reads no raw
content or secrets, and makes no resource-enforcement or OS-isolation claim.
Exact source PR and merged-main CI plus independent canonical records remain
required before writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation action-scope-binding source receipt (2026-10-27)

Source PR #98 exact head
`a128cc12d18c17903ff76e580b1d58c6ef726b8e`, tree
`f97b17c651b3c290ff4d0a3a0d8367c2835f434c`, passed Python 3.11.17
exact-head run 40473660562 with 686 product tests, zero failures and zero
product skips. Expected-head guarded merge
`4fbc90411690d8ac488606afa8b16d3a4b8a6248` passed exact main-push
run 40473743386 with the same result. Both runs executed all 18 infrastructure
guards: 17 passed and one established Memory-only case skipped. Diagnostics
passed.

The verifier recomputes each bounded delegation chain and its nested
scope-attenuation evidence, then requires each hop's recorded action scopes to
equal the delegated scopes already bound by that hop. Scope substitution,
stale nested evidence, malformed or action-bearing metadata and false recorded
acceptance fail closed.

This is bounded synthetic recorded-metadata verification only. It performs no
live authorization, delegation, revocation, action or execution, reads no raw
content or secrets, and makes no resource-enforcement or OS-isolation claim.
Independent canonical records and their exact PR/final-main CI remain required
before writer release. AF-29 remains in progress at 6/12.

## AF-29 action-coherence release and action-tuple candidate (2026-10-28)

Action-coherence source/records PRs #103/#104 are verified through final main
`967b0a3f660146fa963e43d32950fb82bee4a84c`. Exact Python 3.11.17 CI runs
40696268682, 40696475743, 40697005439 and 40697103371 passed 708 product
tests with zero product skips. Writer `AF29-DELEGATION-ACTION-COHERENCE-20261028`
is explicitly released.

The new bounded candidate recomputes exact action-coherence evidence and binds
each hop's action scopes and target into one deterministic hash commitment.
Hop, scope, target, evidence, malformed/action-bearing metadata and false
acceptance substitutions fail closed. Local Python 3.11.17 validation passed
231 focused security tests and 718 portable product tests. All 18 infrastructure
guards executed: 17 passed and the established Memory-only case skipped.

Reuse-first review found the required contracts in this repository; no external
code, algorithm, model, dependency, download, account or network access is
introduced. This is synthetic recorded-metadata verification only and grants no
authorization, resource access, action, execution, sandboxing or OS-isolation
authority. Exact source and records PR/merged-main CI remain required before
writer release. AF-29 remains in progress at 6/12.

## AF-29 action-target release and action-coherence candidate (2026-10-28)

Action-target-binding records PR #102 exact head
`1ee81d73cac18cb125c8b0354c0bf369f1cc65c0`, tree
`186ae707032c985f97d90292d2b35061c78b5077`, passed Python 3.11.17
exact-head run 40649680025 with 697 product tests and zero product skips. Its
expected-head merge produced final main
`a2af7d7138f566fde3a36eeead57d37dfcf697cc`; push run 40649764547 passed
the same suite. Writer `AF29-DELEGATION-ACTION-TARGET-BINDING-20261027` is
explicitly released on PR #102.

The new bounded candidate recomputes the existing recorded action-scope and
action-target binding reports, requires exact component evidence IDs, and
requires both accepted components to refer to the same delegation-chain
evidence. Mixed-chain substitution, stale component evidence, a rejected or
falsely accepted component, malformed/action-bearing metadata and false
coherence acceptance fail closed. Local Python 3.11.17 validation passed 219
focused security tests and 706 portable product tests. All 18 infrastructure
guards executed: 17 passed and the established Memory-only case skipped.
Dependency, compile, JSON and diff checks passed.

Reuse-first review found the needed contracts already in this repository, so
the slice introduces no third-party source, algorithm, model or dependency and
performs no download, network call or account access. This is bounded synthetic
recorded-metadata verification only. It performs no live authorization,
delegation, revocation, action or execution, reads no raw content or secrets,
and makes no resource-enforcement, sandboxing or OS-isolation claim. Exact
source PR and merged-main CI plus independent canonical records remain required
before writer release. AF-29 remains in progress at 6/12.

## AF-29 action-scope release and action-target-binding candidate (2026-10-27)

Action-scope-binding records PR #99 exact head
`a3397769741dcedcbd3738c2811031e6b40ae6ba`, tree
`9e5c1e93244e21330a9776fd4572fffb6f03aeeb`, passed Python 3.11.17
exact-head run 40474296686 with 686 product tests and zero product skips. Its
expected-head merge produced final main
`a22ebc01d51121316a175ea9d1073744faaf1a99`; push run 40474410203 passed
the same suite. Each run executed all 18 infrastructure guards: 17 passed and
one established Memory-only case skipped. Writer
`AF29-DELEGATION-ACTION-SCOPE-BINDING-20261026` is explicitly released on PR
#99.

The new bounded candidate recomputes exact delegation-chain and nested
sensitive-sink evidence, then requires each caller-supplied action target
identifier to equal the sensitive-sink identifier already bound by that hop.
Target substitution, stale nested evidence, malformed or action-bearing
metadata and false recorded acceptance fail closed. Local Python 3.11.17
validation passed 208 focused security tests and 695 portable product tests.
All 18 infrastructure guards executed: 17 passed and the established
Memory-only case skipped. Diagnostics, dependency, import, compile, JSON and
diff checks passed.

This is bounded synthetic recorded-metadata verification only. It proves no
target existence, ownership or accessibility, performs no live authorization,
delegation, revocation, action or execution, reads no raw content or secrets,
and makes no resource-enforcement or OS-isolation claim. Exact source PR and
merged-main CI plus independent canonical records remain required before
writer release. AF-29 remains in progress at 6/12.

## AF-29 delegation action-target-binding source receipt (2026-10-28)

Source PR #100 exact head
`cfe080ad2119978fbfbd22ffbe68b3a227f8f233`, tree
`889b1429546e5ffd33735aaf24089f1c4e7f9ca6`, passed Python 3.11.17
exact-head run 40481370030 with 697 product tests, zero failures and zero
product skips. Expected-head guarded merge
`44c286cd6fe109ea4786ffbf98e442217da32892` passed exact main-push run
40510992182 with the same result. Both runs executed all 18 infrastructure
guards: 17 passed and one established Memory-only case skipped. Diagnostics
passed.

The verifier recomputes each bounded delegation chain and its nested
sensitive-sink evidence, then requires every hop's recorded action target to
equal the sink identifier already bound by that hop. Target substitution,
stale nested evidence, malformed or action-bearing metadata and false recorded
acceptance fail closed.

This remains bounded synthetic recorded-metadata verification only. It proves
no target existence, ownership or accessibility, performs no live
authorization, delegation, revocation, action or execution, reads no raw
content or secrets, and makes no resource-enforcement or OS-isolation claim.
Independent canonical records and their exact PR/final-main CI remain required
before writer release. AF-29 remains in progress at 6/12.
