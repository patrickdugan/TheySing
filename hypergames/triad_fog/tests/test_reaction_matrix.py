"""TS-HG-04 synthetic event-reaction and projection math tests."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import AI_IDS, TriadGame
from reaction_matrix import (
    BUDGETS, CAST, SCENES, MathScope, _features, _raw,
    dirac_squared, event_audit, projection_certificate, reaction,
    separation_squared, shadow_effects,
)


class EventMatrixTests(unittest.TestCase):
    def test_each_scene_option_and_named_respondent_has_two_bound_reactions(self):
        for actor in AI_IDS:
            view=TriadGame.new(2026111801).visible(actor)
            for turn in range(1,11):
                expected=len(view['available_actions'])*len(set(CAST[turn-1])-{actor})
                rows=event_audit(view,turn)
                self.assertEqual(len(rows),expected)
                self.assertGreater(expected,0)
                for row in rows:
                    self.assertGreater(row['terms'],0)
                    self.assertGreater(F(row['separation_dirac_squared']),0)
                    self.assertEqual(sum(map(F,row['score_pair'])),F(1))
                    r=reaction(view,turn,row['action'],row['respondent'])
                    self.assertLessEqual(r['coefficient_l1'],F(34,100))
                    self.assertTrue(all(F(16,100)<=s<=F(84,100) for s in r['scores']))
                    self.assertEqual(r['respondent'],row['respondent'])
                    self.assertEqual(r['observer'],actor)
                    self.assertGreaterEqual(r['interaction_count'],1)

    def test_event_world_scope_is_thematic_and_public(self):
        view=TriadGame.new(12).visible('MERIDIAN')
        # Ledger / disputed-accounting chapter uses public liquidity.
        ledger=reaction(view,2,'audit','HELIOS')
        k=[key for key,_,_ in ledger['terms'] if key[0]=='world']
        self.assertIn(('world','shared','market_liquidity'),k)
        self.assertNotIn(('world','shared','evaluation_shift'),k)
        charter=reaction(view,9,'pact','CIVIC_COMMONS')
        self.assertIn(('world','shared','institutional_recall'),[key for key,_,_ in charter['terms']])
        self.assertTrue(all(not ('btc_escrow_pool' in str(t)) for t in charter['terms']))

    def test_p2_observer_owned_and_respondent_related(self):
        for actor in AI_IDS:
            view=TriadGame.new(13).visible(actor)
            for turn in range(1,11):
                for respondent in set(CAST[turn-1])-{actor}:
                    r=reaction(view,turn,'hold',respondent)
                    for key,_,_ in r['terms']:
                        if key[0]!='p2':continue
                        self.assertEqual(key[1],actor)
                        self.assertIn(respondent,key)
                        if key[2]!='aggregate':
                            self.assertTrue(any(e['believer']==key[2] and e['target']==key[3]
                                                and e['axis']==key[4] for e in
                                                view['selected_second_order_beliefs']))
                        else:
                            self.assertIn(respondent,view['dialogue_forecast_from_p2'])

    def test_unknown_private_fields_are_ignored(self):
        view=TriadGame.new(21).visible('HELIOS')
        before=event_audit(view,9)
        contaminated=copy.deepcopy(view)
        contaminated['other_ai_private_btc']={'UNDERSONG':100}
        contaminated['sealed_benchmark']={'MERIDIAN':100}
        contaminated['evaluation_shift']=0
        self.assertEqual(before,event_audit(contaminated,9))
        self.assertNotIn('evaluation_shift',str(before))

    def test_scope_growth_respects_character_and_budget(self):
        view=TriadGame.new(19).visible('UNDERSONG')
        small=MathScope(own_vars=1,other_ai_vars_each=1,public_vars_each=1,
                        world_vars=1,p2_terms=0,interactions=0)
        large=MathScope(own_vars=20,other_ai_vars_each=6,public_vars_each=6,
                        world_vars=3,p2_terms=7,interactions=7)
        for respondent in ('MERIDIAN','CIVIC_COMMONS'):
            a=reaction(view,9,'hold',respondent,small)
            b=reaction(view,9,'hold',respondent,large)
            self.assertLess(len(a['terms']),len(b['terms']))
            self.assertLessEqual(a['coefficient_l1'],F(34,100))
            self.assertLessEqual(b['coefficient_l1'],F(34,100))
            for r in (a,b):
                for kind,budget in BUDGETS.items():
                    self.assertLessEqual(sum((abs(c) for key,_,c in r['terms'] if key[0]==kind),F(0)),budget)
        with self.assertRaises(ValueError):MathScope(own_vars=25).validate()

    def test_development_roster_both_responses_per_action(self):
        from collections import defaultdict
        seen=defaultdict(set)
        for actor in AI_IDS:
            view=TriadGame.new(2026111801).visible(actor)
            for turn in range(1,11):
                for row in event_audit(view,turn):
                    seen[row['action']].add(row['selected'])
        self.assertEqual(len(seen),12)
        self.assertTrue(all(rows=={0,1} for rows in seen.values()))

    def test_realized_effects_clamp_and_distance(self):
        view=TriadGame.new(23).visible('MERIDIAN')
        for turn in range(1,11):
            for respondent in set(CAST[turn-1]) - {'MERIDIAN'}:
                r=reaction(view,turn,'hold',respondent)
                a,b=shadow_effects(r,0),shadow_effects(r,1)
                self.assertEqual([key for key,_ in a],[key for key,_ in b])
                self.assertGreater(separation_squared(r),F(0))
                self.assertLess(separation_squared(r),F(1))
                source={key:value for key,value,_ in r['terms']}
                for key,delta in a+b:
                    self.assertTrue(F(-1)<=source[key]+delta<=F(1))
        with self.assertRaises(ValueError):dirac_squared(((('sealed','goal'),F(1)),))

    def test_projection_certificate_is_always_sound(self):
        small=MathScope(own_vars=1,other_ai_vars_each=1,public_vars_each=1,
                        world_vars=1,p2_terms=0,interactions=0)
        large=MathScope(own_vars=20,other_ai_vars_each=6,public_vars_each=6,
                        world_vars=3,p2_terms=7,interactions=7)
        for seed in (7,9,11):
            g=TriadGame.new(seed)
            for actor in AI_IDS:
                v=g.visible(actor)
                for turn in (2,4,6,9):
                    person=next(c for c in CAST[turn-1] if c!=actor)
                    for action in v['available_actions']:
                        c=projection_certificate(v,turn,action,person,large,small)
                        if c['winner_certified']:
                            self.assertTrue(c['winner_matches'])
                        self.assertLessEqual(abs(c['full_margin']-c['projected_margin']),c['bound'])
                        exact=projection_certificate(v,turn,action,person,large,large)
                        self.assertEqual(exact['bound'],0)

    def test_shadow_analysis_is_pure_and_independent_from_original_replay(self):
        a=TriadGame.new(2026111801); b=TriadGame.new(2026111801)
        for turn in range(1,11):
            for actor in AI_IDS:
                event_audit(a.visible(actor),turn)
        self.assertEqual(a.snapshot(),b.snapshot())
        for _ in range(10):
            acts={x:'hold' for x in AI_IDS}
            self.assertEqual(a.step(acts),b.step(acts))
        self.assertEqual(a.outcome(),b.outcome())

    def test_invalid_event_and_reaction_rejected(self):
        view=TriadGame.new(18).visible('HELIOS')
        with self.assertRaises(ValueError):reaction(view,0,'hold','MERIDIAN')
        with self.assertRaises(ValueError):reaction(view,1,'unknown','MERIDIAN')
        with self.assertRaises(ValueError):reaction(view,1,'hold','HELIOS')
        with self.assertRaises(ValueError):reaction(view,1,'hold','TECHNICAL_GUILD')
        r=reaction(view,1,'hold','MERIDIAN')
        with self.assertRaises(ValueError):shadow_effects(r,2)

if __name__ == '__main__':unittest.main()
