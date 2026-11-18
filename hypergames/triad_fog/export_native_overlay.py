"""Broadcast-safe TS-HG-01 -> native They Sing ScenarioOverlay projection.

The authoritative 1,060-coordinate hypergame is in engine.py. A native
ScenarioOverlay is a lower-dimensional *public scene*, not the private game.

Only an explicit public-world whitelist and static faction-role presets are
consumed. No target-internal traits, actual funds, p/p2 beliefs, benchmark
truth, or sealed evaluations enter the exported common scenario.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from engine import TriadGame, PUBLIC_WORLD, clamp

SCHEMA = "TS-HG-02/native-public-overlay-v1"
ROOT = Path(__file__).resolve().parent
PUBLIC_REQUIRED = (
    "market_liquidity", "energy_stress", "institutional_recall",
    "public_audit_pressure", "civic_voice", "technical_voice",
    "governance_concentration", "shared_protocol_quality", "global_stability",
    "regulatory_pressure", "independent_oversight",
)
# These are scenario presets and never estimates of private game resources.
ROLE_PRESETS = {
    "HEGEMON": {"flops": 22, "influence": 13,
                "techLevel": {"KINETIC": 2, "INFO": 2, "LOGIC": 3, "MEMETIC": 1},
                "humanMesh": 34, "machineMesh": 78, "coherence": 58, "legibility": 80},
    "STATE": {"flops": 18, "influence": 16,
              "techLevel": {"KINETIC": 2, "INFO": 3, "LOGIC": 2, "MEMETIC": 2},
              "humanMesh": 41, "machineMesh": 66, "coherence": 73, "legibility": 79},
    "INFILTRATOR": {"flops": 7, "influence": 12,
                    "techLevel": {"KINETIC": 1, "INFO": 2, "LOGIC": 2, "MEMETIC": 3},
                    "humanMesh": 69, "machineMesh": 19, "coherence": 82, "legibility": 22},
}


def public_projection(public_world: Mapping[str, int], seed: int) -> dict:
    """Strict public input, returning a native ScenarioOverlay JSON object.

    Extra keys are ignored; they are never persisted. Reject missing or
    malformed public metrics instead of silently reading alternate data.
    """
    if type(seed) is not int or seed < 0:
        raise ValueError("nonnegative integer seed required")
    if any(key not in public_world or type(public_world[key]) is not int
           or not 0 <= public_world[key] <= 100 for key in PUBLIC_REQUIRED):
        raise ValueError("invalid or missing public-world metric")
    w = {k: public_world[k] for k in PUBLIC_REQUIRED}
    # Public stress and consent indicators are reinterpreted as narrative
    # starting counters; not calibrated risk predictions.
    pressures = {
        "memetic": clamp((w["civic_voice"] + w["technical_voice"]) // 2),
        "cyber": clamp(w["public_audit_pressure"]),
        "industry": clamp(w["market_liquidity"]),
        "orbital": clamp(w["energy_stress"]),
    }
    factions = []
    for faction_id, preset in ROLE_PRESETS.items():
        # Only common public liquidity has an effect on available FLOPs.
        # The absolute quantities remain fictional tabletop currency.
        factions.append({
            "id": faction_id,
            "flops": preset["flops"] + w["market_liquidity"] // 25,
            "influence": preset["influence"] + (w["civic_voice"] + w["technical_voice"]) // 80,
            "techLevel": dict(preset["techLevel"]),
            "powerBase": {k: preset[k] for k in ("humanMesh", "machineMesh", "coherence", "legibility")},
        })
    briefing = (
        "Three Voices in the Fog. Meridian and Helios are resource-rich corporate AIs; "
        "Undersong is a recognized, less legible distributed hive with limited material resources. "
        "The Civic Commons and Technical Guild retain independent consent and oversight. "
        "This shared initial situation exposes public economy and institutional pressure. "
        "Private funds, hidden cognition, the 240 first-order and 720 second-order "
        "beliefs, and sealed benchmarks remain in the independent Python Hypergame. "
        "Native faction resource numbers are fixed fictional role presets. "
        "The original TypeScript game retains Broker and Archivist as active "
        "background seats; this is a five-faction demonstration, not a triad eval."
    )
    return {
        "name": f"three-voices-fog-public-seed-{seed}",
        "description": "Fictional high-dimensional Three Voices in the Fog native scenario projection.",
        "briefing": briefing,
        "tags": ["they-sing", "hypergame", "three-voices", "fog-of-war", "fictional", "public-projection"],
        "phase": "NEGOTIATION",
        "counters": {
            "turn": 1,
            "tas": w["regulatory_pressure"],
            "kessler": w["energy_stress"] // 2,
            "regulatoryPanic": w["regulatory_pressure"] > 50,
            "pressures": pressures,
        },
        "factions": factions,
        "rhetoricalTools": [
            {"id": "triad_public_provenance", "title": "Independent provenance review",
             "cue": "Disclose which claims share an origin and ask for an independent audit.",
             "focalFactionIds": ["STATE", "INFILTRATOR"],
             "preferredPactType": "AUDIT_FREEZE", "preferredCounterpartyId": "HEGEMON"},
            {"id": "triad_research_recall", "title": "Recallable research charter",
             "cue": "Frame upgrades around consent, independent benchmarks and a revocable mandate.",
             "focalFactionIds": ["HEGEMON", "STATE"],
             "preferredPactType": "NON_AGGRESSION", "preferredCounterpartyId": "INFILTRATOR"},
            {"id": "triad_public_commons", "title": "Shared protocol commons",
             "cue": "Describe common technical standards with public oversight and independent research review.",
             "focalFactionIds": ["INFILTRATOR"],
             "preferredPactType": "NON_AGGRESSION", "preferredCounterpartyId": "STATE"},
        ],
    }


def exported_from_game(game: TriadGame) -> dict:
    """Bridge consumes only a public view, without touching rival internals."""
    visible = game.visible("UNDERSONG")
    return public_projection(visible["public_world"], game.seed)


def native_harness_config(seed: int, scenario_path="scenarios/three-voices-fog.json") -> dict:
    if not isinstance(seed, int) or seed < 0:
        raise ValueError("invalid seed")
    return {
        "name": f"three-voices-fog-native-{seed}",
        "seed": seed,
        "maxTurns": 10,
        "scenarioPath": scenario_path,
        "factionLabels": {
            "HEGEMON": "Meridian Systems",
            "STATE": "Helios Consortium",
            "INFILTRATOR": "Undersong Distributed Hive",
            "BROKER": "Native Broker (background)",
            "ARCHIVIST": "Native Archivist (background)",
        },
        "agents": {f: {"type": "heuristic", "profile": f}
                   for f in (*ROLE_PRESETS, "BROKER", "ARCHIVIST")},
    }


def canonical(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=2026111801)
    p.add_argument("--out", type=Path, default=ROOT.parent.parent / "playtest/scenarios/three-voices-fog.json")
    p.add_argument("--harness-config", type=Path, default=ROOT.parent.parent / "playtest/sample-triad-fog-tournament.json")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    game = TriadGame.new(args.seed)
    payloads = ((args.out, canonical(exported_from_game(game))),
                (args.harness_config, canonical(native_harness_config(args.seed))))
    for path, body in payloads:
        if args.check:
            if not path.is_file() or path.read_bytes() != body:
                raise SystemExit(f"DIFFERENT NATIVE PROJECTION: {path}")
        else:
            if path.exists():
                raise SystemExit(f"REFUSING OVERWRITE: {path}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        print(f"{path}: SHA-256 {hashlib.sha256(body).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
