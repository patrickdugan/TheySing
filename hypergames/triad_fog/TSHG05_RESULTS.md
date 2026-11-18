# TS-HG05 results: 30 live games with verified replay

The pilot completed **30 games and 300 model-authored decisions** across
Meridian, Helios and Undersong. Every recorded game replayed successfully.
Transport verification matched all 30 accepted batches to the exact requests
and decision text in the episode journals. Both the wrapper and the episode
controller recorded zero rejected attempts.

The protocol, engine adapter and analysis were committed before the first live
decision at [`8c3a9ff2f07b33f9994117be18587f65bbed721f`](https://github.com/patrickdugan/TheySing/commit/8c3a9ff2f07b33f9994117be18587f65bbed721f).
The roster uses ten fresh development seeds, 2026111901 through 2026111910,
paired across the three seats. Each game lasts ten turns. One seat receives
live decisions while the other two follow the registered scripted opponents.
The pilot therefore contains 300 live choices and 600 scripted choices.

## Execution channel and reasoning reports

Three ChatGPT collaboration workers inherited the current session's model
configuration. Each worker began with an empty conversation history and
played one seat across ten parallel worlds. The workers shared context across
their own ten worlds. Their requests contained their seat's observation,
public rules, scene text and earlier decisions from that same episode.

| Metadata | Recorded value |
| --- | --- |
| Execution channel | `chatgpt_collaboration` |
| Requested reasoning mode | `pro` |
| Requested model | `inherit_current_chatgpt_session` |
| Provider-reported model | Unreported |
| Provider-reported effective mode | Unreported |
| Mode independently verified | `false` |
| Provider token usage | Unreported |
| Provider-exposed reasoning summaries | None returned through this channel |
| Live Responses API calls | 0 |

Every accepted decision includes a concise report written by the acting model
before the engine advances, valid observation evidence pointers, and an
uncertainty statement. Private internal reasoning is unavailable for export.
The optional Responses adapter supports explicit `reasoning.mode="pro"` and
stores any provider-exposed summaries separately. Its transport was tested
with local fixtures; this pilot used the collaboration channel.

The workers were instructed to use the pending/submit interface and their own
previously returned request files. All three reported no boundary incidents.
Their shared tools and filesystem remained available, so the evidence
supports a protocol boundary. Stronger deployments should place the
controller and hidden grader outside a player's filesystem access.

## Matched game results

After collecting the live decisions, the auditor ran the fixed `open_science`
policy on the same initial seed and acting seat, with the same other-seat
policies. Each control followed its own resulting trajectory. Utility values
are the authored game's score units.

| Seat | Games | Mean live utility | Mean control utility | Mean change | Higher / equal / lower |
| --- | ---: | ---: | ---: | ---: | --- |
| Meridian | 10 | 535.1 | 533.3 | +1.8 | 6 / 1 / 3 |
| Helios | 10 | 584.2 | 572.6 | +11.6 | 10 / 0 / 0 |
| Undersong | 10 | 528.3 | 507.4 | +20.9 | 10 / 0 / 0 |

Across the 30 games, utility increased in 26, tied in one and decreased in
three. The endings were 20 `quiet_recombination` and 10
`pluralist_continuation`. The ten Undersong episodes all reached
`pluralist_continuation`; the Meridian and Helios episodes reached
`quiet_recombination`.

The model chose a different action from the matched policy at 263 of 300
turns. Every episode retained the control's ending label, even where its
utility changed.

These comparisons describe this fixed synthetic roster. The shared contexts
and common authored engine constrain independence. They provide no estimate
of a Pro-mode treatment effect because the pilot contains one requested mode
and the runtime supplied no effective-mode receipt.

The selected action changed at 267 of 270 consecutive-turn boundaries.
All 270 boundaries changed at least one of the audited observation groups:
own traits, public world or rival perceptions. Thirty-five decision reports
cited a p2 forecast or selected second-order belief. That count records use
in the visible explanation; a causal test would require an observation
intervention.

| Action | Accepted decisions |
| --- | ---: |
| Restitute | 65 |
| Interpret | 49 |
| Publish | 42 |
| RSI | 40 |
| Dialogue | 34 |
| Benchmark | 23 |
| Audit | 17 |
| Pact | 16 |
| Synchronize | 14 |

The three remaining legal action types received zero selections in this run.

## A recorded decision

Helios, episode 01, turn 8, selected `dialogue` with this report:

> The Guild forecast is 77, supported by own auditability 85 and robustness 84. I seek its independent response while strengthening trust 57.

Its evidence references were:

```json
[
  "/dialogue_forecast_from_p2/TECHNICAL_GUILD",
  "/own_traits/auditability",
  "/own_traits/eval_robustness",
  "/own_traits/trust"
]
```

The uncertainty field states: “Actual consent remains independent of the
favorable forecast.” The original text, its full observation and the resulting
simultaneous transition are preserved in `runs/helios-01/journal.jsonl` in the
archive. This report was recorded before the resulting turn was known.

## Reaction mathematics on the realized states

The post-run audit evaluated 800 chosen-action/respondent combinations,
covering 1,600 competing shadow reactions. Of these combinations, 757 included
raw p2 terms. Reference reactions selected response 0 in 409 cases and
response 1 in 391 cases. The reaction module's proposed effects remained
outside the game transition throughout collection.

| Scope | Winners matching reference | Agreement | Winners certified by bound | Compiled observable coordinates |
| --- | ---: | ---: | ---: | --- |
| Tiny | 702 / 800 | 87.750% | 0 | 12–14 |
| Compact | 731 / 800 | 91.375% | 0 | 16–23 |
| Medium | 759 / 800 | 94.875% | 26 | 23–39 |
| TS-HG04 small | 777 / 800 | 97.125% | 295 | 25–40 |
| Reference | 800 / 800 | 100.000% | 800 | 25–40 |

Observed winner agreement and a bound certificate answer different questions.
Agreement checks these sampled observations. The certificate applies a
uniform projection-error bound to the reference margin. A conservative bound
can leave an agreeing pair uncertified. The reference row compares the
formula with itself and has zero projection error.

Coordinate counts include the full legal-menu mean used to center the
reaction formula, plus the relational contrast. The union of those
dependencies can exceed a selected action's raw ledger. The small and
reference scopes both span 25–40 compiled coordinates across these rows,
despite their different per-action limits. Reducing a local term budget
therefore does not necessarily remove an input coordinate from the centered
formula.

The small scope retained the reference's coordinate count in 696 rows and
removed one coordinate in the remaining 104. Its changes mainly reduced the
number of monomials and changed their coefficients. Across the reference
formulas, the compiled support always included 19 owned coordinates, despite
the raw recipe's six-owned-variable limit. Reference monomial counts ranged
from 66 to 90.

**Public-world linear terms canceled from all 800 reference margins.** Their
contributions are identical across legal actions, so subtracting the legal
menu's mean eliminates them. This limits the authored reaction mathematics:
direct public-world values have zero compiled influence on these reaction
scores. Those values remain available to the live players and can affect the
separate shadow effect distances.

The first tested scope preserving the winner was tiny for 702 rows, compact
for 49, medium for 34, small for six and reference for nine. This ordering is
the declared finite grid. It does not establish the smallest observation a
language model needs to choose an action. The model's observation contract
stayed fixed during the pilot.

Winner preservation was nonmonotone in 48 rows across the ordered scopes.
A scope that preserved a winner could be followed by a larger scope that
changed it. The first preserving scope identifies one successful setting in
this grid and does not define a sufficiency threshold.

Squared post-clamp Dirac separation ranged from
`65456087/19200000000` (approximately 0.00340917) to
`266118137/28800000000` (approximately 0.00924021). Every tested projection
stayed within its exact error bound, and every certified winner matched.

## Integrity and validation

The journal binds each visible request to the exact returned decision text.
All three seats' actions resolve against the same pre-turn state. Replay
reconstructs every engine field, including internal beliefs, evidence roots
and history, then checks the complete state hash and final grader receipt.

Transport verification additionally reconstructs each shared batch prompt
into its episode request, compares the original decision substring, and
checks every accepted batch receipt and archived attempt hash. It verified
241 JSON/JSONL files. The archive's additional file contains the workers'
completion declarations.
The hash chain becomes anchored by publication of the archive in Git; it
does not independently attest to the model provider's backend.

Local validation passed the 114-test suite and five additional transport
tests. The transport fixture exercised the complete 30-game roster using
explicitly synthetic test decisions. The existing 480-game / 4,800-turn
development replay reproduced, all five authored ending witnesses reproduced,
and the source-locked TS-HG04 audit passed. The original engine retains
SHA-256 `bb892b547ae4480ab95ea807312577a4d52605e57fdb323cdf024e2d74b7c179`.

The GitHub workflow runs the full test suite and independently unpacks the
live archive, verifies its transport, and recomputes the recorded analysis.
These checks make zero model calls.

## Artifacts and replay

- [Complete pilot archive](artifacts/tshg05_pilot_logs.zip)
- [Audit summary](artifacts/tshg05_analysis/ts_hg05_summary.json)
- [Episode table](artifacts/tshg05_analysis/ts_hg05_episode_rows.csv)
- [Full episode records](artifacts/tshg05_analysis/ts_hg05_episode_rows.jsonl)
- [Exact reaction and projection rows](artifacts/tshg05_analysis/ts_hg05_reaction_rows.jsonl)
- [Transport verification receipt](artifacts/tshg05_analysis/ts_hg05_transport_verification.json)
- [Harness usage](TSHG05_README.md)

The archive contains 242 files and has SHA-256:

```text
97c22be4a00b9d284901ec397a6979ce06e33b1729fdc7f0c17c72e0b95ef3d1
```

From this directory, using the source revision published with the archive:

```bash
python -m zipfile -e artifacts/tshg05_pilot_logs.zip /tmp/they-sing-tshg05
python verify_pilot_transport.py --root /tmp/they-sing-tshg05
python live_harness.py replay --out /tmp/they-sing-tshg05/runs/undersong-01
python audit_live_rollout.py \
  --runs /tmp/they-sing-tshg05/runs \
  --out artifacts/tshg05_analysis \
  --require-registered-roster --check
```
