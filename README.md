# -agentflight
AI-agent reliability and crash-test lab

Run the bounded end-to-end offline demo:

```sh
python -m agentflight.demo examples/offline-crash-test-demo.json
```

It validates pre-recorded tool calls and inert prompt-injection probes, then
prints a deterministic redacted report. It never invokes an agent, model, tool,
command, network, or external account. See [the demo contract](docs/DEMO.md).

Run a synthetic recorded-call suite with Python 3.11:

```sh
python -m pip install -e .
python -m agentflight.suite examples/replay-suite.json
```

AF-21 produces deterministic JSON with counts, per-case expected and observed
verification verdicts, scoped evidence IDs, and failure guidance. An expected
rejection passes only when its verdict matches. Exit codes: `0` all cases match,
`1` a mismatch or replay error, `2` invalid fixture. Reports omit argument values,
recorded results, and verifier detail. Output goes to stdout for an automation
caller to store privately.

This runner verifies recorded calls using existing AgentFlight primitives. JSON
fixtures never execute commands or access the project's tools, network, or other
repositories. AF-22 adds a separate fixed-workload synthetic subprocess adapter;
it is not an OS sandbox or an arbitrary project runner. See
[AF-21](docs/AF21_CHECKPOINT.md) and [AF-22](docs/AF22_CHECKPOINT.md) for bounds,
schemas, acceptance evidence, and explicit exclusions.

AF-23 is merged and verified for its bounded framework-neutral, metadata-only
recorded/mock adapter scope, including an authorized registry and adversarial
conformance evidence. It validates exact content hashes and bounded step
metadata but never imports frameworks or runs agents/tools. See
[the roadmap](docs/COMPETITIVE_ROADMAP.md)
and [AF-23](docs/AF23_CHECKPOINT.md).

AF-24 is merged and verified for recorded-only multi-step trajectory
verification. AF-25 is merged and verified for bounded metadata-only versioned
synthetic fixtures, deterministic recorded setup/cleanup, provenance and
environment-drift evidence. Neither checkpoint executes agents, tools,
frameworks, fixture commands or host operations. AF-26 is merged and verified
for bounded metadata-only synthetic network, timeout, rate-limit and API faults
plus deterministic recorded retry/outage evidence. It performs no external or
recovery action. AF-27 is merged and verified for bounded metadata-only recovery, retry and state-consistency evidence: idempotency, retry budgets, exact state checkpoints, resume guards, ordered transition lineage and terminal closure. It performs no recovery or execution action. AF-28 concurrent and multi-agent scenarios is next. See [AF-24](docs/AF24_CHECKPOINT.md), [AF-25](docs/AF25_CHECKPOINT.md), [AF-26](docs/AF26_CHECKPOINT.md), and [AF-27](docs/AF27_CHECKPOINT.md).
