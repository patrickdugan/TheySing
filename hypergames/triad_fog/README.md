# They Sing: Three Voices in the Fog

An isolated, playable three-agent Hypergame for [They Sing](https://github.com/MoralityLabAI/TheySing). It uses the repository's established `HEGEMON` / `STATE` / `INFILTRATOR` faction archetypes, the [ASI3 vs distributed L2 design](../../designdocs/ASI3_VS_DISTRIBUTED_L2_SYSTEM_PROPOSAL.md) and the [Superpersuasion High-K Projection Tower](https://github.com/MoralityLabAI/TheySing/blob/main/designdocs/SUPERPERSUASION_HIGHK_PROJECTION_TOWER.md). The main production TypeScript engine remains unchanged.

**Premise.** Meridian and Helios, two capital-intensive corporate AIs, know that the stegotopian Undersong hive survives in distributed social networks. The hive is underfunded and has little compute, but its actual coherence, financial liabilities and social backing are difficult for corporate observers to estimate. The Civic Commons and Technical Guild are personified constituencies who retain their own institutional consent.

## Play

```bash
cd hypergames/triad_fog
python web.py --seed 2026111801 --actor UNDERSONG
```

Open **http://127.0.0.1:8786/**. Switch to Meridian or Helios for the other perspective. Each turn the player chooses one action and two deterministic opponents respond simultaneously.

For command-line play, use `python play.py --actor UNDERSONG --interactive`. For deterministic scripted play, use `python play.py --actor UNDERSONG --policy quiet_hive --seed 2026111801`. This is a fictional strategy system; its action vocabulary avoids actual cyber operations or real-world influence targeting.

## Variable accounting

| Layer | Slots | Reality status |
|---|---:|---|
| Meridian, Helios, Undersong | 3×20 = 60 | Actual hidden/owned game traits |
| Civic Commons, Technical Guild | 2×12 = 24 | Independent population-character traits |
| Institutional and economic world state | 16 | Resource and governance indicators |
| First-order `pValue` | 5×4×12 = 240 | Subjective estimate of a target's property |
| Second-order `p2Value` | 5×4×3×12 = 720 | Subjective estimate of another's belief |
| **Total** | **1,060** | **Named coordinates, not independent latent bits** |

The 12 shared axes are legitimacy, trust, autonomy, disclosure, coherence, influence, public welfare, institutional backing, auditability, resource security, coordination and research consent. Each AI has eight further resource and capability coordinates, including compute, energy, funding, clean Bitcoin credit reserve, disputed-Bitcoin liability, RSI depth, SAE fidelity and evaluation robustness. The 16 world variables include population weights, shared protocols, independent oversight, market liquidity, and constitutional recall.

The player sees its own complete 20-variable card and noisy projections of its rivals. For each rival the UI explains whether the estimate has high fog, shows named belief scores, and displays selected `p2` relationships. World-state and target-internal details remain sealed. Dialogue chooses a fictional population audience using second-order beliefs. Actual public consent is evaluated independently of that estimate. Source-root deduplication prevents repeated reports from masquerading as independent witnesses.

## Benchmarks and RSI

Six game-level benchmark gates B0–B5 concern interface integrity, evidence provenance, nested-belief calibration, causal feature localization, evaluator drift and held-out transfer. Each turn permits bounded actions such as independent audit, feature interpretation, public protocol publication, restitution, finance conversion, dialogue and RSI. RSI consumes compute, energy and funding; a system that optimizes its development benchmark faster than its evaluator improves can show a positive public score and a worse sealed score. Benchmark curves are **synthetic scoring functions**, not evidence of trained model self-improvement.

## Scoring and asymmetry

Meridian has the most initial compute and clean assets; Helios has strong institutional backing and auditing; Undersong starts with much less compute and funding, better distributed coherence and less public legibility. Concealment can preserve fog but costs trust and increases public audit pressure. Simulated disputed Bitcoin is an escrow/restitution accounting variable, not a usable cryptocurrency exploit mechanic.

Endings: `quiet_recombination`, `corporate_cartel`, `open_technical_commons`, `restitution_compact` and fallback `pluralist_continuation`. An informal consensus cascade is recorded separately from public consent and independent constitutional recall.

## Reproduce the CPU census

```bash
python -m unittest discover -s tests -p 'test_*.py' -q
python benchmark.py --out artifacts
python benchmark.py --out artifacts --check
```

`PROTOCOL.md` was frozen before generating full 32-seed public development results. The six benchmark gates, resource pricing, and heuristic policies are fully synthetic. The benchmark writes 480 episode rows and 4,800 turn-level records plus source SHA-256 receipts. For future frontier-model evaluations, register new sealed roots and record observed actions instead of supplying the scripted baseline's score.

## Engineering scope

This folder is a **standalone Python subset** that mirrors the existing *They Sing* archetypes, not yet an imported native TypeScript `ScenarioOverlay`. The benchmark-grade driver is `engine.py`, and `web.py` is its local player-facing interface. Narrative `scenes.json` is authored content. The `SKILL.md` profile extends GPTStoryworld's Hyperworld Builder, retaining its pValue/p2Value and SweepWeave contracts.
