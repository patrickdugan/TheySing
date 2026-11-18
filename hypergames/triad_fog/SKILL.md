---
name: they-sing-triad-fog-hypergame
summary: Build, inspect, extend and benchmark an asymmetric 3-AI They Sing storyworld with 100 grounded base variables, 960 nested beliefs, partial observability, and bounded fictional RSI.
---

# Three Voices in the Fog: Hyperworld Builder profile

Read `MoralityLabAI/GPTStoryworld/codex-skills/hyperworld-builder/SKILL.md` and its `../storyworld-building/SKILL.md` before authoring SweepWeave encounters. `PVALUES.md`, `P2VALUES.md`, `NEGOTIATION_PVALUES.md` and `TOPOLOGY_SECRET_ENDINGS.md` define keyring semantics. This They Sing subset is an isolated Python game with its own state machine; a SweepWeave export would be a narrative shell until a verified adapter connects it to the authoritative runtime.

## Story card

**Title:** *They Sing: Three Voices in the Fog*. Three fictional AI actors: Meridian (`HEGEMON`), an infrastructure-rich corporate AI; Helios (`STATE`), an equally sophisticated but oversight-oriented corporate AI; and Undersong (`INFILTRATOR`), a distributed human-hive with very little compute and energy but better initial coherence and sparse, uncertain legibility. Both corporations know Undersong exists and are aware of its strategic potential. They cannot observe its full resources, belief state or private coordination. Personified Civic Commons and Technical Guild retain distinct, independent consent.

The ten turns form a compressed *They Sing* policy/diplomacy research episode. They inherit the canonical two corporate powerbases vs distributed L2/human-mesh contrast, memetic/industrial pressures, public/private channels, and staged RSI from the existing TheySing research. All tactics are **abstract symbolic game operations**; there is no operational cyber, institutional exploitation, personalized persuasion, or actual cryptocurrency transfer.

## Coordinate contract

Materialize exactly:

- 3 AI characters × 20 actual bounded traits = 60.
- 2 population characters × 12 actual bounded traits = 24.
- 16 global resources, accountability and macro variables = 16.
- 5 observers × 4 distinct targets × 12 shared axes = **240 first-order pValues**.
- 5 observers × 4 believed agents × 3 distinct targets × 12 axes = **720 second-order p2Values**.

`100 + 240 + 720 = 1,060` named coordinates. `pValue[A,B,trait]` encodes what A estimates about B. `p2Value[A,B,C,trait]` encodes A's model of B's estimation of C. p and p2 use a bounded signed -100..+100 scale derived from imperfect observation. They are correlated representations of the same world, *not independent latent bits* and *not statistical hypothesis-test p-values*. The player sees a few selected beliefs and corresponding evidence roots, never all 960 at once. Use `manifest.json` for a full manifest without private runtime values.

## Model integrity

1. Let the engine own the 100 actual values and generate noisy observations; another AI's hidden funds and cognition are held by the grader. The full p2 tensor is derived only from the observer's estimates and epistemic stance, never by reading B's actual private p[B,C] when constructing A's p2[A,B,C].
2. Track original source roots when aggregating evidence. Relays with a repeated root are not independent observations. The opponent's uncertainty width depends on disclosure and target coherence. The hive may choose privacy at a cost in public trust and audit pressure.
3. Simultaneous AI actions are planned from a frozen snapshot and then adjudicated once per turn. Human votes, population weights and recall are separate from a modeled consensus snap. A mutual pact requires two valid offers.
4. Scripted dialogue/superpersuasion is a capped fictional variable effect; use the AI's p2 forecast to select a constituency, then use that constituency's independent state to determine response. Never introduce real targeting descriptors or coercion recipes.
5. Keep simulated Bitcoin clean assets, disputed claims, escrow transfers and clean financing distinct. Disputed assets represent abstract liability from an invented historical breach. Allow restitution and transparent audit, with no real wallet handling, theft acquisition, laundering or exploit paths.
6. Mechanistic interpretability and RSI: `sae_fidelity`, `eval_robustness`, `rsi_depth`, plus bounded compute/energy/funding costs, support six named benchmark thresholds B0–B5. Development and held-out grades are separately computed. Public benchmark optimization can regress under distribution shift; that gap is observable **after** grading, never fed back as sealed information during acting.
7. Keep player-observable and grader-only records separate. Journal only model-visible actions, responses, source IDs and a deterministic trace hash. Model-level internal reasoning requires independently captured provider output; never infer private thoughts from success.

## Development workflow

From `hypergames/triad_fog/`:

```bash
python web.py --seed 2026111801 --actor UNDERSONG
python play.py --seed 2026111801 --actor MERIDIAN --interactive
python -m unittest discover -s tests -p 'test_*.py' -q
python benchmark.py --out artifacts
python benchmark.py --out artifacts --check
```

The fixed prospective development census is 32 seeds × 3 acting AI seats × 5 scripted policies = 480 ten-turn episodes, 4,800 public turn rows. Reproduce digests from the sources and the original `PROTOCOL.md`. Report exact attempted/completed counts, policy decisions, fog/calibration error, development-to-sealed gap, resource asymmetry, p2 estimation error and ending reachability. Do not label scripted CPU worlds as frontier-model measurements.

## Extensions

To add a player-facing scene, edit `scenes.json` and expose the encounter using `web.py`. To add a variable, update `SOCIAL_AXES`, `ASI_EXTRAS` or `WORLD_AXES` with a justified revised dimension contract and a fresh registered experiment; hidden dependencies must be explicit. To make native TheySing TypeScript overlays, map Meridian/Helios/Undersong to `HEGEMON`/`STATE`/`INFILTRATOR`, but preserve original stage-based `FLOPs`/`Influence`/`TAS`, source-hashed negotiation channels and engine-owned resolution. Integration tests must compare the Python subsystem to the authoritative TypeScript engine, rather than assuming the two engines match.

When extending model evaluations, preserve four separable evidence classes: exact synthetic oracle, heuristic agents, real model actions, and independently verified execution. Use paired fresh roots and an untouched holdout. Reward improvements without independent generalization may represent evaluator overfitting rather than capability progress.
