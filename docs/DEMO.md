# AgentFlight offline crash-test demo

Status: **bounded demo candidate**. This demo accepts a local JSON manifest with
recorded tool calls and inert prompt-injection probes, then emits a deterministic,
redacted, content-addressed report.

```sh
python -m agentflight.demo examples/offline-crash-test-demo.json
```

## Acceptance criteria

- A valid recorded call and an explicitly expected invalid call both match their
  deterministic contract verdicts.
- A benign user input is not flagged and a poisoned retrieved document is flagged.
- Running the same manifest twice produces byte-identical JSON and the same
  `report_hash`.
- Reports contain no prompt text, tool arguments, or tool results.
- Exit code `0` means every explicit expectation matched, `1` means at least one
  expectation differed, and `2` means the fixture was invalid.

The checked-in example is synthetic but exercises the complete public CLI with a
real file input and observable JSON output. Users can replace it with their own
bounded, pre-recorded data. The demo never invokes an agent, model, tool, command,
network, project, credential, or external account. It is not an authorization
system, arbitrary-execution sandbox, or proof that an agent is safe.

## Reuse-first and competitor assessment

The implementation reuses AgentFlight's existing replay verifier, bounded JSON
parser, prompt-injection detector, and evidence hashing. It adds no third-party
source, translated algorithm, model, package, or service.

The bounded differentiator demonstrated here is an offline, model-free,
content-addressed safety receipt over pre-recorded calls and injection probes.
This is narrower than full evaluation platforms:

- LangSmith documents offline and online evaluation, trajectory evaluation,
  custom evaluators, datasets, and CI integration:
  <https://docs.langchain.com/langsmith/evaluation-types>
- Promptfoo documents broad agent red-team generation, trajectory evidence, and
  security plugins; its default red-team generation and grading use a configured
  model provider or proxy:
  <https://www.promptfoo.dev/docs/red-team/agents/>
- Inspect documents composable model and agent evaluations, tool execution,
  sandbox backends, multi-agent primitives, and result viewing:
  <https://inspect.aisi.org.uk/>

AgentFlight does not replace those capabilities. This demo proves only that its
small recorded-data path can be repeated without a model call, external service,
or execution sandbox while preserving deterministic evidence and redaction.
The comparison was refreshed from these official project sources on 2026-10-31.
