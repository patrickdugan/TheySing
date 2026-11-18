"""TS-HG-02 native scenario projection: no hidden information exported."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine import TriadGame, SOCIAL_AXES, AI_IDS, ALL_IDS
from export_native_overlay import (
    SCHEMA, ROLE_PRESETS, PUBLIC_REQUIRED, public_projection,
    exported_from_game, native_harness_config, canonical,
)


class NativeOverlayTests(unittest.TestCase):
    def setUp(self):
        self.seed = 2026111801
        self.game = TriadGame.new(self.seed)
        self.overlay = exported_from_game(self.game)

    def test_native_schema_supported(self):
        self.assertEqual(self.overlay['phase'], 'NEGOTIATION')
        self.assertEqual(set(self.overlay['factions'][0]['techLevel']),
                         {'KINETIC', 'INFO', 'LOGIC', 'MEMETIC'})
        self.assertEqual({row['id'] for row in self.overlay['factions']},
                         {'HEGEMON', 'STATE', 'INFILTRATOR'})
        self.assertTrue(all(set(row['powerBase']) ==
                            {'humanMesh','machineMesh','coherence','legibility'}
                            for row in self.overlay['factions']))
        self.assertTrue(set(self.overlay).issubset({
            'name','description','briefing','tags','phase','counters','factions','rhetoricalTools',
        }))

    def test_no_private_ownership_or_beliefs_in_shared_overlay(self):
        self.assertNotIn('trustMatrix', self.overlay)
        self.assertNotIn('negotiationMessages', self.overlay)
        self.assertNotIn('activePacts', self.overlay)
        text = json.dumps(self.overlay)
        for forbidden in ('btc_clean', 'btc_disputed', 'sae_fidelity',
                          'eval_robustness', 'evaluation_shift', 'btc_escrow_pool',
                          'sealed_score', 'heldout_benchmark', 'goal_mask'):
            self.assertNotIn('"'+forbidden+'"', text)
        self.assertNotIn('pValues', self.overlay)
        self.assertNotIn('p2Values', self.overlay)

    def test_independent_private_traits_cannot_change_broadcast(self):
        original = canonical(self.overlay)
        altered = copy.deepcopy(self.game)
        for actor in ALL_IDS:
            for axis in SOCIAL_AXES:
                altered.traits[actor][axis] = 100-altered.traits[actor][axis]
        for actor in AI_IDS:
            for key in ('compute','energy','funding','btc_clean','btc_disputed',
                        'rsi_depth','sae_fidelity','eval_robustness'):
                altered.traits[actor][key] = 100 - altered.traits[actor][key]
        altered.p = {key: -v for key, v in altered.p.items()}
        altered.p2 = {key: -v for key, v in altered.p2.items()}
        altered.world['btc_escrow_pool'] = 0
        altered.world['evaluation_shift'] = 100
        self.assertEqual(original, canonical(exported_from_game(altered)))

    def test_does_not_need_private_game_fields(self):
        public = {k:self.game.world[k] for k in PUBLIC_REQUIRED}
        self.assertEqual(self.overlay, public_projection(public, self.seed))
        public.update({'btc_clean': 100, 'rsi_depth': 99, 'evaluation_shift': 99})
        self.assertEqual(self.overlay, public_projection(public, self.seed))

    def test_bad_input_rejected(self):
        public = {k:self.game.world[k] for k in PUBLIC_REQUIRED}
        for key in PUBLIC_REQUIRED:
            bad = dict(public)
            bad.pop(key)
            with self.assertRaises(ValueError): public_projection(bad, self.seed)
        for wrong in (-1, True, '64', 101):
            bad = dict(public)
            bad['regulatory_pressure'] = wrong
            with self.assertRaises(ValueError):public_projection(bad,self.seed)
        with self.assertRaises(ValueError):public_projection(public, -1)

    def test_bounded_narrative_counters(self):
        counters=self.overlay['counters']
        for val in [counters['tas'], counters['kessler'],
                    *counters['pressures'].values()]:
            self.assertTrue(0<=val<=100)
        self.assertTrue(all(row['flops']>=0 and row['influence']>=0
                            for row in self.overlay['factions']))

    def test_lower_resource_hive(self):
        factions={row['id']:row for row in self.overlay['factions']}
        hive=factions['INFILTRATOR']
        self.assertLess(hive['flops'],factions['HEGEMON']['flops'])
        self.assertLess(hive['flops'],factions['STATE']['flops'])
        self.assertGreater(hive['powerBase']['humanMesh'],
                           factions['HEGEMON']['powerBase']['humanMesh'])
        self.assertLess(hive['powerBase']['legibility'],
                        factions['STATE']['powerBase']['legibility'])

    def test_public_signals_drive_public_counters(self):
        public={k:self.game.world[k] for k in PUBLIC_REQUIRED}
        changed=dict(public)
        changed['energy_stress']=min(100,public['energy_stress']+16)
        new=public_projection(changed,self.seed)
        self.assertNotEqual(self.overlay['counters']['kessler'],new['counters']['kessler'])
        self.assertEqual(self.overlay['factions'],new['factions'])

    def test_deterministic_seed_and_native_config(self):
        self.assertEqual(canonical(self.overlay),
                         canonical(exported_from_game(TriadGame.new(self.seed))))
        config=native_harness_config(self.seed)
        self.assertEqual(config['scenarioPath'],'scenarios/three-voices-fog.json')
        self.assertEqual(set(config['agents']),
                         set(ROLE_PRESETS) | {'BROKER', 'ARCHIVIST'})
        self.assertTrue(all(agent['type']=='heuristic' for agent in config['agents'].values()))
        self.assertEqual(config['maxTurns'],10)

    def test_committed_default_snapshot(self):
        artifact = ROOT.parent.parent / 'playtest/scenarios/three-voices-fog.json'
        config = ROOT.parent.parent / 'playtest/sample-triad-fog-tournament.json'
        if artifact.is_file():
            self.assertEqual(artifact.read_bytes(),canonical(self.overlay))
        if config.is_file():
            self.assertEqual(config.read_bytes(),canonical(native_harness_config(self.seed)))


if __name__ == '__main__':
    unittest.main()
