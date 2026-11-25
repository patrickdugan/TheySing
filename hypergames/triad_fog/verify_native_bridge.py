"""Verify the source-locked TS-HG-02 public-overlay bridge and frozen TS-HG-01 baseline."""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = Path(__file__).resolve().parent
RECEIPT = LOCAL / "native_bridge_receipt.json"
PATHS = (
    "hypergames/triad_fog/export_native_overlay.py",
    "hypergames/triad_fog/verify_native_bridge.py",
    "hypergames/triad_fog/native_harness_smoke.cjs",
    "hypergames/triad_fog/tests/test_native_overlay.py",
    "hypergames/triad_fog/skills/native-overlay-bridge/SKILL.md",
    "hypergames/triad_fog/TSHG02_NATIVE_BRIDGE.md",
    "playtest/scenarios/three-voices-fog.json",
    "playtest/sample-triad-fog-tournament.json",
    ".github/workflows/triad-fog-native-bridge.yml",
)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def generate() -> dict:
    return {
        "schema":"TS-HG-02/native-public-overlay-receipt-v1",
        "scope":"public projection of fictional 1,060-coordinate game into native five-seat TypeScript scenario; no frontier inference",
        "native_focal_factions":3,
        "native_background_seats":2,
        "private_sidecar_emitted":False,
        "frozen_parent_episode_summary_sha256":"1b2c24e1b73c23d4cbd04f578bfc8ae68b91d9bbff0325f9bd2fbbc698d5fc88",
        "source_sha256":{p:sha(ROOT/p) for p in PATHS},
    }


def verify() -> dict:
    stored=json.loads(RECEIPT.read_text('utf8'))
    current=generate()
    if stored!=current:raise AssertionError('TS-HG-02 frozen receipt changed')
    call=[sys.executable,str(LOCAL/'export_native_overlay.py'),
          '--seed','2026111801',
          '--out',str(ROOT/'playtest/scenarios/three-voices-fog.json'),
          '--harness-config',str(ROOT/'playtest/sample-triad-fog-tournament.json'),
          '--check']
    subprocess.run(call,cwd=str(ROOT),check=True,capture_output=True,text=True)
    old=sha(ROOT/'hypergames/triad_fog/artifacts/summary.json')
    if old!=current['frozen_parent_episode_summary_sha256']:
        raise AssertionError('original TS-HG-01 evidence changed')
    return {'checks':['source_hashes','public_projection_reproduction',
                      'original_480_episode_receipt_unchanged'],
            'all_passed':True,'source_count':len(PATHS)}


def main() -> None:
    print(json.dumps(verify(),sort_keys=True))

if __name__=='__main__': main()
