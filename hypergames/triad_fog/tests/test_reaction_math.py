"""TS-HG-03: visible-only reaction formulas and exact numerical distances."""
import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import TriadGame, AI_IDS, run_scripted
from reaction_math import MathScope, recipe, effects, dirac_squared, public_audit, reaction_separation_squared

class ScopedMathTests(unittest.TestCase):
    def test_all_actor_views_and_scenes_are_bounded(self):
        game=TriadGame.new(2026111801)
        for actor in AI_IDS:
            view=game.visible(actor)
            for turn in range(1,11):
                for action in view['available_actions']:
                    r=recipe(view,turn,action)
                    self.assertEqual(sum(r['scores']),F(1))
                    self.assertTrue(all(F(16,100)<=x<=F(84,100) for x in r['scores']))
                    self.assertLessEqual(r['coefficient_l1'],F(34,100))
                    self.assertEqual(r['perspective'],actor)
                    self.assertGreater(reaction_separation_squared(r),0)
                    self.assertEqual(reaction_separation_squared(r),4*dirac_squared(effects(r,0)))
                    for k,_value,_coeff in r['terms']:
                        if k[0]=='own':self.assertEqual(k[1],actor)
                        if k[0] in ('rival','public'):self.assertNotEqual(k[1],actor)
                        self.assertNotIn(k[0],('grader','sealed','true_world'))
    def test_no_opponent_private_funds_or_sealed_scores(self):
        game=TriadGame.new(22)
        view=game.visible('MERIDIAN')
        baseline=public_audit(view,9)
        changed=copy.deepcopy(view)
        changed['hidden_heldout_benchmark']={'UNDERSONG':100}
        changed['other_private_funding']={'HELIOS':99}
        changed['opponent_true_rsi_depth']={'UNDERSONG':77}
        self.assertEqual(baseline,public_audit(changed,9))
        self.assertNotIn('btc_disputed',str(baseline))
        self.assertNotIn('sealed',str(baseline))
    def test_size_factor_normalization(self):
        game=TriadGame.new(33)
        view=game.visible('UNDERSONG')
        small=recipe(view,9,'hold',MathScope(own_vars=1,rival_vars_per_ai=1,
                              public_vars_per_constituency=1,world_vars=1,p2_terms=0,interaction_terms=0))
        large=recipe(view,9,'hold',MathScope(own_vars=5,rival_vars_per_ai=6,
                              public_vars_per_constituency=6,world_vars=7,p2_terms=5,interaction_terms=5))
        self.assertGreater(len(large['terms']),len(small['terms']))
        self.assertLessEqual(large['coefficient_l1'],F(34,100))
        self.assertLessEqual(small['coefficient_l1'],F(34,100))
        self.assertGreaterEqual(large['interaction_count'],small['interaction_count'])
    def test_scoped_public_data_excludes_private_world_axes(self):
        view=TriadGame.new(8).visible('HELIOS')
        for action in view['available_actions']:
            r=recipe(view,10,action)
            joined=str(r['terms'])
            for name in ('evaluation_shift','btc_escrow_pool','private_funds','grader_sealed_score'):
                self.assertNotIn(name,joined)
    def test_input_errors(self):
        view=TriadGame.new(3).visible('MERIDIAN')
        with self.assertRaises(ValueError):recipe(view,0,'hold')
        with self.assertRaises(ValueError):recipe(view,1,'steal')
        with self.assertRaises(ValueError):MathScope(own_vars=70).validate()
        with self.assertRaises(ValueError):dirac_squared(((('sealed','x','y'),F(1)),))
    def test_interaction_allocates_distinct_legal_belief_families(self):
        view=TriadGame.new(2026111801).visible('MERIDIAN')
        r=recipe(view,9,'hold')
        self.assertGreater(r['groups']['p2'],0)
        self.assertEqual([key[2][0] for key,_,_ in r['terms'] if key[0]=='interaction'],
                         ['rival','public','p2'])

    def test_existing_hypergame_checksum_unchanged(self):
        a=TriadGame.new(17); b=TriadGame.new(17)
        self.assertEqual(a.visible('MERIDIAN'),b.visible('MERIDIAN'))
        _=public_audit(a.visible('MERIDIAN'),1)
        self.assertEqual(a.snapshot(),b.snapshot())

if __name__=='__main__': unittest.main()
