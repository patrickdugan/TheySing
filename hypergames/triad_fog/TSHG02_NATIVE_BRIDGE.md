# TS-HG-02: Public native ScenarioOverlay bridge

**Implementation status:** built and tested as an isolated extension to the TS-HG-01 standalone Python Hypergame. This is not a full TypeScript port of its 1,060-coordinate runtime.

`export_native_overlay.py` produces `playtest/scenarios/three-voices-fog.json` and a native harness session configuration `playtest/sample-triad-fog-tournament.json`. Use `npm run build:harness` to compile the TypeScript harness; run its existing scenario-driven tournament using the generated session config.

## Mapping

| Python fictional actor | Native faction | Shared starting identity |
|---|---|---|
| Meridian Systems | HEGEMON | Infrastructure-rich corporate ASI |
| Helios Consortium | STATE | Corporate ASI with high legibility and audit institutions |
| Undersong | INFILTRATOR | Underfunded but coherent distributed hive |

The native scenario uses **public** market, energy, consent and oversight indicators plus static faction-role presets to initialize the existing map game. The canonical TypeScript harness has **five** playable seats, so Broker and Archivist remain active background factions in its native match. The independent Python Hypergame is the three-AI benchmark; native scenario match results must be labelled as five-faction demonstration data. Starting FLOPs are fictional tabletop allowances, not underlying private `compute` coordinates; a scalar public `trustMatrix` would leak first-order beliefs and is intentionally omitted.

## Important limitation

The native game has a different state machine and technology tree. This projection places recognizable factions, public pressures and narrative rhetorical tools into an already supported `ScenarioOverlay`; it does not synchronize hidden p2, resource ownership, genuine public votes, evidence source trees or sealed RSI benchmark grades with TypeScript. The Python engine continues to resolve the three-agent Hypergame, and its browser UI remains the complete player-facing version.

A future bridge may carry **per-player private sidecars** with signed observation schemas and a separate grader oracle. Such sidecars must be emitted to that player's inference process rather than the shared scenario file.

## Verification

Run `python hypergames/triad_fog/export_native_overlay.py --check` from the repository root, then `python -m unittest discover -s hypergames/triad_fog/tests -p 'test_*.py' -q`. The native projection tests enforce strict public-data whitelisting, bounded counters, deterministic output, legal faction roles and resistance to private-state perturbations. The existing TS-HG-01 registered receipt is untouched. The generated native overlay and its harness configuration are tracked by SHA-256 in the separate TS-HG-02 receipt and reproduce without neural inference.
