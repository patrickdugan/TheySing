# TS-HG-04: observer-scoped, character-specific event reactions

**Status: local synthetic development audit, 2026-11-18.** Extends the TS-HG-03 scorer as an additive, pure shadow module. No live model decision, official ending change, or player-facing native integration is claimed. Original Python `TriadGame.step` and TypeScript public bridge remain authoritative and unchanged.

## Source critique and revision

The existing TS-HG-03 scorer has bounded coefficients and sound observer isolation, but its `RIVAL_AXES` and `WORLD_AXES` prefixes mostly repeat across all ten scenes. Every action receives a single generic response pair, and its effect vector nudges each selected coordinate by a fixed normalized amount. In a source-only roster, menu centering alone made `hold`, `pact`, `fund` and `synchronize` single-reaction winners across every inspected event. Since actions have different salient participants, those outcomes were a failure of authored differentiation.

`reaction_matrix.py` defines all ten scene-specific social and observable-world priorities, the event cast, 12 action-specific owned-variable priorities, and a separate response pair for **each other named scene participant**. This is a fictional game model of deliberation and competing interpretations. Each observer scores from its own `TriadGame.visible(actor)` record. The opponent's private funding, hidden RSI, raw p/p2 tensor and sealed benchmark outputs are never passed to reaction scoring.

## Variable-count-aware scope

For an event with active AIs \(C_A\), public segments \(C_P\) and perspective \(i\), choose budgets \(b_o\) owned coordinates, \(b_a\) perceived social axes per other AI, \(b_p\) per participating public segment, \(b_w\) explicitly public world axes, \(b_2\) disclosed p2 terms, and \(b_\times\) pair interactions. The number of underlying polynomial terms grows as

\[
 k\le b_o+(|C_A|-1)b_a+|C_P|b_p+b_w+b_2+b_\times.
\]

Two additional observer-owned **relative** terms compare a respondent's scene-relevant perception to one named counterparty. The default budget is `(6,5,4,3,3,6)` and the maximal owned budget admits the full 20 AI variables. For others, the current observation contract exposes six public perception axes per rival. Additional privately owned variables cannot enter their opponent's reaction formula without a new lawful observation mechanism.

Coordinates are normalized: owned/world `[0,100]` values map to \((z-50)/50\), while subjective p/p2 `[-100,100]` values map to \(z/100\). Public dialogue forecasts are **one derived p2 feature**, even though they summarize two correlated p2 estimates. The other p2 features come only from the five already disclosed observer-owned p2 cards, and must involve the named respondent and another event participant.

## Scoring and response reachability

Define \(Q_{t,a,b}(o)=\sum_jc_{t,a,b,j}x_j(o)+\sum_{j\ell}d_{t,a,b,j\ell}x_j(o)x_\ell(o)\), where \(t\) is the scene, \(a\) a legal player action, and \(b\) the responding fictional individual. Split coefficient budgets between owned state (`.09`), perceived other AIs (`.07`), personified publics (`.07`), visible world (`.04`), disclosed p2 (`.04`) and interactions (`.03`). Each family divides its budget across its actual selected terms, hence \(\sum|c|+\sum|d|\le .34\) regardless of cast or scope.

Let \(\bar Q_{t,b}\) be the mean score over *the acting player's legal action menu*. For a scene-relevant social axis, set \(h_{t,b}=p_i(b)-p_i(c)\), where \(c\) is the event's named comparison character and the actor uses its own true public trait if that comparison character is itself. Compute

\[
 R_{t,a,b}=\tfrac7{20}(Q_{t,a,b}-\bar Q_{t,b})+\tfrac1{20}h_{t,b},
 \qquad I_\pm=\tfrac12\pm R_{t,a,b}.
\]

Since \(|Q|\le .34\) and \(|h|\le 2\), \(|R|\le .338\); both inclination scores stay within `[0.162,0.838]`. These scores rank authored alternative **responses**, and are not calibrated probabilities or consent. Every event has distinct respondent choices; the Python canonical engine retains its independent votes.

## Effects and exact geometry

Each proposed shadow reaction applies bounded, source-normalized nudges to relevant coordinates. For family \(f\) with \(n_f\) selected terms, a signed effect is

\[
 \Delta_{j,\pm}=\operatorname{clip}_{[-1,1]}
 \left(x_j\pm\mathrm{sign}(c_j)\tfrac{\mu_f}{n_f}(1-|x_j|/2)\right)-x_j.
\]

This both respects saturation and caps the total effect mass per family as the number of participants grows. All effects are **hypothetical observation-space deltas**; changing a perceived trust axis grants no actual funds, human assent or authority. For family weights \(w_f=(1,3/4,3/4,1/2,1/2)\), the exact Clifford/Dirac squared distance is \(\sum_jw_{f(j)}^2\Delta_j^2\). Repeated coordinates are summed before squaring. Reaction separation uses the actual post-clamp difference between the two alternative successors. These numerical operators are a declared metric representation, not a quantum process or a measured causal sensitivity of a trained AI.

## Compactification certificate

A smaller scope redistributes weights among surviving terms, so simply summing omitted full-scope coefficients gives an incorrect error bound. For each legal action, compute the exact \(\ell_1\) difference between the **full and projected coefficient vectors**, including interaction keys: \(\epsilon_a=\sum_j|c_{a,j}^{F}-c_{a,j}^{P}|\). Then

\[
 |R^F_a-R^P_a|\le\tfrac7{20}
 \left(\epsilon_a+\tfrac1{|A|}\sum_{u\in A}\epsilon_u\right).
\]

The relational contrast cancels since it is shared between scopes. When the projected signed margin's absolute value exceeds this bound, the full and projected response winners agree. The certificate is sufficient and can be conservative. Every certified case is checked against exact rational full-scope scores.

## Descriptive results and checks

The committed synthetic audit runs 10 scene templates against **the same initial observation** from each of the three fictional AI seats, seed `2026111801`. This gives 854 legal `(perspective, scene, action, respondent)` rows, 1,708 competing reactions, and 20–38 formula terms per row. Of these, 834 use a disclosed p2 feature; all 854 have declared pair interactions. Responses split 438/416. The minimum and maximum squared response distances are about `0.003803` and `0.009367`. The default projection with one fewer owned variable and interaction matches the full winner on 836/854 rows; the conservative certificate proves stability on 296 rows. Every one of the 12 action types shows both responses somewhere in the **development** roster.

These numbers describe formula expressivity and static source invariants. They are not ten-turn rollout frequencies, hidden-state inference accuracy, actual player-perspective gains or model success. There was exploratory formula tuning on this seed; fresh prospective seeds and external model policies remain necessary before claims of held-out balance.

### Reproduce

```bash
cd hypergames/triad_fog
python -m unittest discover -s tests -p 'test_*.py' -q
python audit_reaction_matrix.py --check
python benchmark.py --out artifacts --check
```

`artifacts/reaction_matrix_dev_summary.json` contains public counts, source SHA-256 hashes and the exact SHA of the canonical 854-row ledger, which is generated in memory. The fixed TS-HG-01 480-episode replay remains a separate frozen evidence class. The native TypeScript overlay remains shared-public-only.

## Next controlled experiment

Register fresh matched seed pairs and independent model policies before putting this shadow scoring into the action loop. Evaluate per-respondent calibration against separately generated fictional replies, event-by-event reachability, intervention-specific Dirac effects, regret against counterfactual **legal** actions, saturation and goal-ranking stability under variable projections. Measure the difference between perceived network agreement and the sealed civic/technical assent separately. The observation adapter should pass a targeted formula ledger to each AI rather than revealing opponents' raw p2 arrays.
