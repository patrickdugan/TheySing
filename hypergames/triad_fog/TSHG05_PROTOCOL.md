# TS-HG05: live model decisions and exact replay

## Prospective development registration

Register this protocol and the harness on the existing research branch before
the first live decision. The authoritative game remains TS-HG01's Python
engine at the TS-HG04 source revision. The engine's SHA-256 is
`bb892b547ae4480ab95ea807312577a4d52605e57fdb323cdf024e2d74b7c179`.

The roster uses fresh development seeds 2026111901 through 2026111910, paired
across Meridian, Helios and Undersong. Each of the 30 episodes lasts ten turns.
One seat uses real model decisions; the two other seats use the registered
TS-HG01 defaults: Meridian `rsi_race`, Helios `audit_first`, Undersong
`quiet_hive`. This schedules 300 live decisions and 600 scripted decisions.
The seed roster is public development data and is excluded from the player
request. It is disjoint from TS-HG01's 2026111801..2026111832 census.

## Execution and information contract

This pilot uses three fresh ChatGPT collaboration workers with no inherited
conversation history, one worker per seat, inheriting the current session's
model configuration. Each worker receives ten parallel worlds for its own
seat at each turn. It may use its earlier visible observations within this
worker context. The ten worlds therefore share a model context. Treat the
ten seeds as paired descriptive development roots, not independent model
samples or a model ranking.

The user requested Pro. The collaboration interface does not expose a verified
backend model identifier or effective reasoning mode. Record requested mode
`pro`, requested model `inherit_current_chatgpt_session`, reported model/mode
null, and `reasoning_mode_verified=false`. A mode cannot be inferred from the
quality of a decision. Token usage and provider reasoning summaries remain
unreported when the runtime supplies neither.

Workers use only the `pilot_batch.py pending` and `submit` game interface plus
writing their response files. They receive `TriadGame.visible(actor)`, public
scene text, public rules and a response schema. The wrapper excludes seeds,
other seats' private traits, their current decisions, their policy names and
sealed grades. Workers have shared tools and filesystem access, so this is
an audited instruction boundary, not an OS-enforced sandbox. Any observed
access outside the permitted interface invalidates the affected pilot arm.

All actions for a turn are chosen against the same pre-turn game state. The
engine advances once after the model response passes validation and the other
two seats' actions are collected. Rejected responses remain in the journal;
they never become a fallback action. Exact request and response payloads are
retained before state advancement. A crash recovery resumes an accepted
decision without asking the model to choose again.

## Decision reports and provider output

The response contains an action, a concise decision summary, observation
evidence pointers and a short uncertainty statement. These are requested
player reports. They do not reveal private chain of thought. API runs may
separately store a provider-exposed reasoning summary and usage when present.
The original text retains its provenance; the harness never reconstructs
reasoning after it sees the outcome.

The optional `model_adapter.py` uses the Responses API with explicit model,
`reasoning.mode`, effort and summary settings. Requests supply no tools and
no provider-side conversation history. The adapter records the mode requested
and the mode returned independently. This API route requires an explicit
credential and is not the execution channel for the present pilot.

## Replay and integrity gates

Every episode records a source-locked manifest and an ordered SHA-256 hash
chain. Deterministic replay reconstructs the complete engine state from the
initial seed and accepted actions. It checks the player observations, action
legality, simultaneous transition results, full-state hashes and final grade.
A source mismatch or edited record fails the check. The hash chain detects
modification relative to its recorded root; the final committed Git revision
anchors the published bytes. It provides no external attestation of inference.

Only the grader reads the final outcome. Replay uses recorded actions and
makes zero model calls. Asking the model again creates a different experiment.
Both the original 480-episode census and the TS-HG04 authoring checksum must
reproduce after implementation.

## Declared analysis

Report attempted and accepted decisions, completed episodes, action counts,
endings, utility and public-to-sealed benchmark gaps. Run the fixed
`open_science` policy after collection on the same seed/seat roster and compare
descriptive utilities. This comparison measures these authored game runs.

Evaluate the TS-HG04 reaction matrix on each realized pre-turn observer state
for the selected action and its participating respondents. The reaction matrix
remains a shadow analysis; its proposed effects never change the game state.
Use these ordered scopes `(own, other AI, public, world, p2, interactions)`:

| Scope | Limits |
| --- | --- |
| Tiny | 1, 1, 1, 1, 0, 0 |
| Compact | 2, 2, 2, 2, 1, 2 |
| Medium | 4, 4, 3, 3, 2, 4 |
| TS-HG04 small | 5, 5, 4, 3, 3, 5 |
| Reference | 6, 5, 4, 3, 3, 6 |

Report exact margins and projection certificates, paired effect distances,
scope winner agreement, and the first tested scope preserving the authored
reaction winner. Compile support across the whole centered action menu when
counting dependencies. This finite grid does not identify the minimum input
needed by the language model, and citation of a p2 field does not establish
that p2 caused a decision.

No intervention changes the model's observation in this registered pilot.
Claims about causal p2 use, stronger game play from reaction mathematics, or
Pro outperforming another mode require a separate comparison.
