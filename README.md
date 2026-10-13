# -agentflight
AI-agent reliability and crash-test lab

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

AF-23 begins the separately authorized competitive roadmap with a
framework-neutral, metadata-only recorded-run adapter. It validates exact
content hashes and bounded step metadata but never imports frameworks or runs
agents/tools. See [the roadmap](docs/COMPETITIVE_ROADMAP.md) and
[AF-23](docs/AF23_CHECKPOINT.md).
