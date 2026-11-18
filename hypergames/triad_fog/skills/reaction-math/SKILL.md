---
name: three-voices-reaction-math
description: Audit and author bounded, observer-scoped, interaction-aware reactions, gates, effects and exact numerical distances for the 1,060-coordinate fictional TheySing Hypergame.
---

# TS-HG-03: Mathematics mode for Three Voices in the Fog

Read the parent \`hypergames/triad_fog/SKILL.md\` and the GPTStoryworld Hyperworld Builder's \`HGW03_REACTION_MATH.md\` first. The 1,060-coordinate tensor consists of 100 actual variables plus 960 correlated pValue/p2Value estimates. A large named tensor is an address space, not 1,060 causally independent factors.

## Observer-owned scope

Each scene identifies a cast and two possible NPC reactions for a chosen action. Select only action-relevant entries from the **acting player's** \`TriadGame.visible(actor)\` record. Never pass \`TriadGame.snapshot()\`, \`grader_only()\`, the entire \`game.p\`/\`game.p2\` arrays, or another AI's own traits into a scorer. The first-order visible rivals expose selected axes for belief-conditioned formulas; only the top-five disclosed trust p2 entries and published aggregated dialogue forecast are observable second-order information. Hidden rival funding, stolen/contested Bitcoin claims, sealed benchmark grades and evaluation shift remain grader-private.

Use \`reaction_math.MathScope\` with separate configurable budgets. Default: four actual own AI variables; three perceived social variables for each other participating AI; two perceived variables per participating public constituency; two public world variables; two disclosed p2 triples; and three explicit two-way interactions. The scope grows with characters involved and their available relevant variables, never by blindly traversing the full tensor. For asymmetric actors, account for budget limits and cost of discovering evidence.

Each formula stores an ordered feature ledger: feature key, source view, owner/observer, value and signed coefficient. \`(observer,believer,target,axis)\` p2 orientation is material. A p2 entry with target outside the scene cannot influence its gate. Use public-source roots to distinguish correlation from independent evidence.

## Normalized reaction formulas

Normalize actual [0,100] bounded traits to \`x=(raw-50)/50\` and perceived [-100,100] entries to \`x=raw/100\`. Every feature stays in [-1,+1]. Score response alternatives by the signed polynomial

\`F_a = Σ_i c_i x_i + Σ_(i,j) b_ij x_i*x_j\`

and use complementary scores \`I_+=1/2+F_a\` and \`I_-=1/2-F_a\`. The source groups' absolute coefficient budgets sum to at most 0.34, so both responses stay within [0.16,0.84] independent of the number of selected features. Scale within each group by its actual feature count. The reference research scorer has budgets 0.10 own, 0.07 rival, 0.05 public, 0.04 public world, 0.04 disclosed p2 and 0.04 explicit pair interactions. Fix signs and weights in source and register them before comparing model behavior.

Interaction products must connect declared scene participants. Examples: an AI's own eval_robustness paired with its belief about another AI's auditability; own coherence with a public-segment trust estimate; own AI reliance with a disclosed belief-about-belief. The terms are fictional narrative physics, not verified causal mechanisms. To test mechanism specificity, ablate each family and compare matched decision margins and game outcomes.

## Effects, gates and geometry

Design distinct, bounded consequences for both responses and report their relevant participants. The \`reaction_math.effects\` function defines *hypothetical shadow effects* and does not mutate the authoritative Python engine. For a numeric effect vector use the exact HG-01 Clifford identity

\`d_D(x,y)^2 = Σ_i w_i^2 (x_i-y_i)^2.\`

The demo uses positive family weights 1 on own traits, 3/4 on social/public perceptions and 1/2 on public world and p2. Normalize each component before comparing; add repeated keyring effects first. For later live transitions, use post-clamp realized deltas. A large geometry shift is a proposal for a gameplay consequence, not proof that the other AI's behavior or actual consent changed.

Keep policy gates split: visibility by observer, action legality by canonical resources, reaction scoring by legal observations, and ending certification by independent population votes and recall. When public social consensus and legal verdict disagree, record the discrepancy. The TypeScript native bridge can use public-only projections from this module once a verified adapter exists; keep original Broker/Archivist overlays and all private fields isolated.

## Experiment and verification

From the repository root:

\`\`\`sh
python -m unittest discover -s hypergames/triad_fog/tests -p 'test_*.py' -q
python -m unittest discover -s hypergames/triad_fog/tests -p 'test_reaction_math.py' -q
\`\`\`

The new scorer is a pure research instrument receiving \`game.visible(actor)\` for its initial 10-scene × legal-action audit. Calling it must not alter the fixed TS-HG-01/02 480 episode / 4,800 turn replay or its checksum. New tests verify six invariants including score bounds for all three perspectives, exact reaction-pair distances, scope budgets, and exclusion of sealed grades/other actors' private resources.

Before adopting scoring in the live game, register fresh paired seeds and compare effect reachability, action regret, saturation, repeated-root influence, projected winner stability and genuine ending changes. Compare actor-subjective Dirac distances with full-state grader distances only after adjudication; the grader-only comparison is never fed back into the actor.


## TS-HG-04: Scene-specific, respondent-by-respondent reaction matrix

Read \`../../TSHG04_EVENT_REACTION_AUDIT.md\` before changing \`reaction_matrix.py\`. This source-only shadow module extends TS-HG-03 with all ten scene contracts and an independent response pair for **every named participant** affected by a legal player action. The ten-scene audit is evaluated using one initial actor-visible observation per perspective, and must be labeled an authoring test rather than a ten-turn rollout.

For each event, fix the acting observer, legal options and respondent cast. \`MathScope(own_vars, other_ai_vars_each, public_vars_each, world_vars, p2_terms, interactions)\` bounds complexity per participating character. Owned variables may reach all twenty slots; opponent variables come solely from visible perceived social axes. Use declared scene priorities, relevant directed pValues and respondent-linked top-five disclosed p2 entries; a published public dialogue forecast counts as one correlated derived p2 feature. Keep the sealed evaluator, unobserved holdings and other actors' raw beliefs out of all formulas.

The response score combines a family-normalized sparse polynomial with a contrast to another **named** scene participant, using the acting observer's own perceptions. Under the declared coefficient budget, both competing inclinations remain in [0.162,0.838]. Shadow effects use source-normalized, post-clamp deltas so adding coordinates does not amplify total effect mass. Exact rational Clifford/Dirac squared distances are computed from the realized hypothetical effect vectors.

For compactification, compare **full versus projected coefficient vectors**, including their changed normalizations and interaction keys. Use \`reaction_matrix.projection_certificate\` before claiming that the reduced term scope preserves a response. The certificate checks the action-specific signed margin against the menu-relative L1 bound. Treat uncertified choices as open empirical cases.

Reproduce the local public development audit using \`python audit_reaction_matrix.py --check\`, then run the normal tests and frozen replay. The new audit records 854 respondent-option rows, 1,708 reaction alternatives, 20–38 scoped terms per row, 834 rows containing disclosed p2, and separate 480-episode original benchmark preservation. No shadow reaction updates the canonical game, votes, TypeScript bridge or sealed grader. Fresh registered seeds and actual model actions are required for a held-out effectiveness claim.
