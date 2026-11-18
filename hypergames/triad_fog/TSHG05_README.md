# TS-HG05 harness: model decisions, journal and replay

`live_harness.py` connects an external model to one playable seat in the
authoritative Python game. It records each visible request and returned
decision before advancing the simultaneous turn. `model_adapter.py` supplies
a Responses API client with an explicit Pro setting. `pilot_batch.py` carries
the registered ChatGPT-session pilot through isolated seat prompts.

The run design and its interpretation limits are in [TSHG05_PROTOCOL.md](TSHG05_PROTOCOL.md).

## Inspect or replay a recorded episode

Run these commands from `hypergames/triad_fog` after extracting the pilot log
archive into a new directory. Replay makes zero model calls.

```bash
python -m zipfile -e artifacts/tshg05_pilot_logs.zip /tmp/they-sing-tshg05
python live_harness.py replay --out /tmp/they-sing-tshg05/runs/undersong-01
python verify_pilot_transport.py --root /tmp/they-sing-tshg05
python audit_live_rollout.py \
  --runs /tmp/they-sing-tshg05/runs \
  --out artifacts/tshg05_analysis \
  --require-registered-roster --check
```

Use the Git revision that published the archive. The manifest checks the
SHA-256 of the engine, scenes and harness source. Edited sources cause replay
to fail so an experiment cannot silently switch implementations.

## Drive one seat interactively

```bash
python live_harness.py init --out /tmp/my-hypergame \
  --seed 2026112001 --actor UNDERSONG
python live_harness.py pending --out /tmp/my-hypergame
```

Only the JSON from `pending` goes to the player model. The controller's run
directory holds the seed and grader. Keep that directory outside a player's
tool access when deploying this interface with stronger isolation.

A response has this form:

```json
{
  "action": "interpret",
  "decision_summary": "The visible fidelity score leaves room for a useful improvement at a manageable compute cost.",
  "evidence": ["/own_traits/sae_fidelity", "/own_traits/compute"],
  "uncertainty": "The other seats' current choices and the independent grade remain unknown."
}
```

Save the exact response as a UTF-8 file, then submit it with the request ID
returned by `pending` and the actor identifier:

```bash
python live_harness.py submit --out /tmp/my-hypergame \
  --response /tmp/decision.json \
  --provenance '{"request_id":"COPY_PENDING_REQUEST_ID","actor":"UNDERSONG"}'
```

Repeat `pending` after each accepted response. Invalid actions, absent
evidence pointers and stale request IDs produce rejection receipts. A valid
response is durable before the state transition. If the controller stops
between those writes, its next invocation completes that accepted decision
once. The controller requires POSIX advisory file locks.

## Request explicit Pro execution through the API

Provide `OPENAI_API_KEY` through the execution environment's credential
mechanism. The adapter sends a request only when this variable is present.
It does not convert a ChatGPT session into an API credential.

```bash
python model_adapter.py --out /tmp/pro-hypergame \
  --seed 2026112002 --actor UNDERSONG \
  --model gpt-6.2-astra --mode pro --effort medium \
  --max-decisions 10 --max-output-tokens 8192
```

To resume a partially completed API episode, use the same model settings and
`--resume`, omitting `--seed` and `--actor`. Failed or ambiguous network
attempts require review; the adapter never retries them automatically.
If a successful provider response reached disk before a controller crash,
the adapter reuses that recorded response.

Each API request contains only the current player request, has an empty tool
list and uses `store=false`. The supplied request already includes the seat's
earlier chosen actions and concise reports. Credentials are excluded from
receipts, redirects are rejected, and returned bytes reach disk before
decoding. API responses retain the provider's returned model, effective mode,
usage and exposed reasoning summaries when those fields exist. Missing
fields remain null or empty. A returned mode that differs from the requested
mode stops the attempt.

Current interface references, checked 18 November 2026:

- [Reasoning modes and summaries](https://developers.openai.com/api/docs/guides/reasoning)
- [Responses API request and output schema](https://developers.openai.com/api/reference/resources/responses/methods/create)

The shipped adapter was validated with local transport fixtures. The
registered pilot uses the ChatGPT collaboration channel. Its manifest
retains the requested Pro setting with unreported backend model/mode.

## What the logs contain

| File | Contents |
| --- | --- |
| `pilot_manifest.json` | Registered seed/seat roster, source commit and execution metadata |
| `runs/<seat>-<index>/manifest.json` | Per-episode source hashes and controller configuration |
| `runs/<seat>-<index>/journal.jsonl` | Hash-chained requests, original decision text and simultaneous transitions |
| `runs/<seat>-<index>/grader.json` | Outcome computed after the final turn |
| `transport/<seat>/turn-*-request.json` | Exact batch sent to a player worker |
| `transport/<seat>/turn-*-response.jsonl` | Exact accepted batch returned by that worker |
| `transport/<seat>/attempts/` | Every submission attempt, including rejected batches |
| `artifacts/tshg05_analysis/` | Reproducible episode comparisons and reaction-scope audit |

`decision_summary` is a concise model-authored report captured at decision
time. Provider-exposed summaries have separate provenance. Private chain of
thought is unavailable for export. Full-state hashes establish reproducible
game transitions; they do not certify a provider's backend configuration.

## Validation

```bash
python -m unittest discover -s tests -p 'test_*.py' -q
python audit_reaction_matrix.py --check
python benchmark.py --out artifacts --check-compatible
python check_witnesses.py
```

The TS-HG04 math module is evaluated after play on each realized observation.
Its effects remain a shadow model. The audit names the first scope in a
finite grid that preserves each authored reaction winner and counts the
whole formula's observable dependencies, including menu-centering terms.
These measurements concern the authored formula; the pilot keeps the model's
observation contract fixed throughout play.
