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
repositories. Project subprocess adapters and isolation are future checkpoints.
See [AF-21](docs/AF21_CHECKPOINT.md) for bounds, schema, and acceptance evidence.
