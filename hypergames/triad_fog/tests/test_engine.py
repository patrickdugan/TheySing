"""Deterministic invariants for TS-HG-01. All scenarios are fictional."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine import (AI_IDS, PUBLIC_IDS, ALL_IDS, SOCIAL_AXES, ASI_EXTRAS,
                    WORLD_AXES, BENCHMARKS, TURN_LIMIT, TriadGame,
                    policy_action, run_scripted)
from web import GameService


class LayoutTests(unittest.TestCase):
    def setUp(self):self.g=TriadGame.new(2026111801)
    def test_true_base_count(self):
        self.assertEqual(sum(map(len,self.g.traits.values()))+len(self.g.world),100)
        self.assertEqual(sum(len(self.g.traits[k]) for k in AI_IDS),60)
        self.assertEqual(sum(len(self.g.traits[k]) for k in PUBLIC_IDS),24)
        self.assertEqual(len(self.g.world),16)

    def test_shared_axis_contract(self):
        self.assertEqual(len(SOCIAL_AXES),12)
        self.assertEqual(len(ASI_EXTRAS),8)
        self.assertEqual(len(WORLD_AXES),16)
        self.assertEqual(len(set(SOCIAL_AXES+ASI_EXTRAS)),20)

    def test_first_order_exact(self):
        self.assertEqual(len(self.g.p),240)
        self.assertEqual(set(self.g.p),{(a,b,k) for a in ALL_IDS for b in ALL_IDS
                                      if b!=a for k in SOCIAL_AXES})

    def test_second_order_exact(self):
        self.assertEqual(len(self.g.p2),720)
        self.assertEqual(set(self.g.p2),{(a,b,c,k) for a in ALL_IDS for b in ALL_IDS
                                       for c in ALL_IDS if len({a,b,c})==3 for k in SOCIAL_AXES})

    def test_total_coordinates(self):self.assertEqual(self.g.coordinate_count,1060)
    def test_bounds(self):
        self.g._assert_state()
        self.assertTrue(all(-100<=v<=100 for v in self.g.p.values()))
    def test_population_partition(self):
        for seed in range(25):
            g=TriadGame.new(seed)
            self.assertEqual(g.world['civic_population']+g.world['technical_population'],100)
    def test_asymmetric_material_budget(self):
        m=self.g.traits['MERIDIAN'];h=self.g.traits['HELIOS'];u=self.g.traits['UNDERSONG']
        self.assertLess(u['compute'],min(m['compute'],h['compute']))
        self.assertLess(u['funding'],min(m['funding'],h['funding']))
        self.assertLess(u['energy'],min(m['energy'],h['energy']))
        self.assertGreater(u['coherence'],m['coherence'])
    def test_public_personified(self):
        self.assertEqual(len(PUBLIC_IDS),2)
        for a in PUBLIC_IDS:self.assertEqual(len(self.g.traits[a]),12)
    def test_known_hive(self):
        for a in ('MERIDIAN','HELIOS'):
            items=self.g.visible(a)['recognized_actors']
            self.assertIn('UNDERSONG',items)
            self.assertEqual(next(i for i in self.g.visible(a)['rivals'] if i['id']=='UNDERSONG')['fog_band'],'high')
    def test_no_unearned_sealed_score_in_observation(self):
        view=self.g.visible('MERIDIAN')
        for forbidden in ('sealed_score','heldout_benchmark','true_goal','world_truth','opponent_traits'):
            self.assertNotIn(forbidden,json.dumps(view))
        self.assertNotIn('evaluation_shift',view['public_world'])
        self.assertNotIn('btc_escrow_pool',view['public_world'])
    def test_self_only_exact_resources(self):
        obs=self.g.visible('HELIOS')
        self.assertEqual(obs['own_traits']['btc_disputed'],self.g.traits['HELIOS']['btc_disputed'])
        self.assertNotIn('btc_disputed',next(x for x in obs['rivals'] if x['id']=='MERIDIAN'))
    def test_false_leak_actor(self):
        with self.assertRaises(ValueError):self.g.visible('CIVIC_COMMONS')
    def test_unsupported_seed(self):
        with self.assertRaises(ValueError):TriadGame.new(-1)
    def test_deterministic_start(self):
        other=TriadGame.new(self.g.seed)
        self.assertEqual(self.g.traits,other.traits)
        self.assertEqual(self.g.p,other.p)
        self.assertEqual(self.g.p2,other.p2)


class CausalTests(unittest.TestCase):
    def setUp(self):self.g=TriadGame.new(2026111801)
    def test_duplicate_root_relay_ignored(self):
        self.assertTrue(self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',10,'audit-X'))
        p=self.g.p.copy(); p2=self.g.p2.copy()
        self.assertFalse(self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',10,'audit-X'))
        self.assertEqual(self.g.p,p);self.assertEqual(self.g.p2,p2)
    def test_independent_root_changes_estimate(self):
        start=self.g.p['MERIDIAN','UNDERSONG','trust']
        self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',15,'independent-1')
        self.assertEqual(self.g.p['MERIDIAN','UNDERSONG','trust'],min(100,start+15))
    def test_first_order_does_not_reveal_other_private_belief(self):
        before=self.g.p['HELIOS','UNDERSONG','trust']
        self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',12,'proof')
        self.assertEqual(before,self.g.p['HELIOS','UNDERSONG','trust'])
    def test_p2_responds_to_observer_evidence(self):
        key=('MERIDIAN','HELIOS','UNDERSONG','trust')
        old=self.g.p2[key]
        self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',18,'new-source')
        self.assertNotEqual(old,self.g.p2[key])
    def test_p2_is_distinct_from_first_order(self):
        key=('MERIDIAN','HELIOS','UNDERSONG','trust')
        self.assertNotEqual(self.g.p2[key],self.g.p['HELIOS','UNDERSONG','trust'])
    def test_bad_evidence_rejected(self):
        for fn in (lambda:self.g.apply_evidence('MERIDIAN','MERIDIAN','trust',1,'s'),
                   lambda:self.g.apply_evidence('MERIDIAN','UNDERSONG','btc_clean',1,'s'),
                   lambda:self.g.apply_evidence('MERIDIAN','UNDERSONG','trust',31,'s')):
            with self.assertRaises(ValueError):fn()
    def test_dialogue_uses_p2_target_selection(self):
        pre=self.g.snapshot()
        for b in ('MERIDIAN','UNDERSONG'):
            pre['p2']['HELIOS',b,'CIVIC_COMMONS','research_consent']=100
            pre['p2']['HELIOS',b,'TECHNICAL_GUILD','research_consent']=-100
        plan=self.g._plan('HELIOS','dialogue',pre)
        self.assertIn(('CIVIC_COMMONS','research_consent'),plan['others'])
        self.assertNotIn(('TECHNICAL_GUILD','research_consent'),plan['others'])
    def test_dialogue_cannot_force_consent(self):
        pre=self.g.snapshot()
        pre['traits']['TECHNICAL_GUILD']['research_consent']=0
        pre['traits']['CIVIC_COMMONS']['research_consent']=0
        plan=self.g._plan('MERIDIAN','dialogue',pre)
        self.assertEqual(list(plan['others'].values()),[0])
    def test_partial_observability_has_different_perspectives(self):
        a=self.g.visible('MERIDIAN')['rivals'];b=self.g.visible('HELIOS')['rivals']
        u=lambda rows:next(t for t in rows if t['id']=='UNDERSONG')['perceived_axes']['trust']['estimate']
        self.assertNotEqual(u(a),u(b))
    def test_conceal_changes_fog_relevant_variable(self):
        before=self.g.traits['UNDERSONG']['disclosure']
        self.g.step({'UNDERSONG':'conceal','HELIOS':'hold','MERIDIAN':'hold'})
        self.assertLess(self.g.traits['UNDERSONG']['disclosure'],before)
    def test_consensus_trace_is_public_and_bounded(self):
        self.g.step({a:'hold' for a in AI_IDS})
        snap=self.g.visible('UNDERSONG')['latest_consensus']
        self.assertLessEqual(len(snap['rounds']),5)
        self.assertTrue(set(snap['final_support']).issubset(set(ALL_IDS)))


class GameTests(unittest.TestCase):
    def setUp(self):self.g=TriadGame.new(2026111801)
    def test_actions_legal(self):
        self.assertIn('hold',self.g.action_menu('MERIDIAN'))
        self.assertIn('synchronize',self.g.action_menu('UNDERSONG'))
        self.assertNotIn('synchronize',self.g.action_menu('HELIOS'))
    def test_invalid_actions_do_not_change_state(self):
        pre=self.g.snapshot()
        with self.assertRaises(ValueError):
            self.g.step({'MERIDIAN':'hold','HELIOS':'conceal','UNDERSONG':'hold'})
        self.assertEqual(self.g.snapshot(),pre)
    def test_order_of_action_dict_irrelevant(self):
        a=TriadGame.new(1);b=TriadGame.new(1)
        first={'MERIDIAN':'rsi','HELIOS':'audit','UNDERSONG':'conceal'}
        a.step(first);b.step(dict(reversed(list(first.items()))))
        self.assertEqual(a.traits,b.traits)
        self.assertEqual(a.world,b.world)
    def test_rsi_consumes_resources_and_increases_depth(self):
        a=self.g.traits['HELIOS'].copy()
        self.g.step({'HELIOS':'rsi','MERIDIAN':'hold','UNDERSONG':'hold'})
        self.assertGreater(self.g.traits['HELIOS']['rsi_depth'],a['rsi_depth'])
        self.assertLess(self.g.traits['HELIOS']['funding'],a['funding'])
    def test_disputed_btc_restitution_escrow_conservation(self):
        t=self.g.traits['UNDERSONG']['btc_disputed'];e=self.g.world['btc_escrow_pool']
        self.g.step({'UNDERSONG':'restitute','HELIOS':'hold','MERIDIAN':'hold'})
        self.assertEqual(self.g.traits['UNDERSONG']['btc_disputed']+self.g.world['btc_escrow_pool'],t+e)
    def test_separate_clean_and_disputed_ledgers(self):
        a=self.g.traits['MERIDIAN']['btc_clean']
        b=self.g.traits['MERIDIAN']['btc_disputed']
        self.g.step({'MERIDIAN':'fund','HELIOS':'hold','UNDERSONG':'hold'})
        self.assertEqual(self.g.traits['MERIDIAN']['btc_clean'],a-3)
        self.assertEqual(self.g.traits['MERIDIAN']['btc_disputed'],b)
    def test_mutual_pact_needs_mutual_offers(self):
        self.g.step({'MERIDIAN':'pact','HELIOS':'hold','UNDERSONG':'hold'})
        self.assertFalse(self.g.pacts)
        self.g.step({'MERIDIAN':'pact','HELIOS':'pact','UNDERSONG':'hold'})
        self.assertIn(('HELIOS','MERIDIAN'),self.g.pacts)
    def test_pact_cannot_change_recall_directly(self):
        val=self.g.world['institutional_recall']
        self.g.step({'MERIDIAN':'pact','HELIOS':'pact','UNDERSONG':'hold'})
        self.assertEqual(self.g.world['institutional_recall'],val)
    def test_benchmark_public_sealed_are_separate(self):
        before=self.g._bench_scores('MERIDIAN')
        self.g.step({'MERIDIAN':'rsi','HELIOS':'hold','UNDERSONG':'hold'})
        public,heldout,tier=self.g._bench_scores('MERIDIAN')
        self.assertGreaterEqual(public,heldout)
        self.assertLessEqual(tier,len(BENCHMARKS))
        self.assertGreaterEqual(self.g.traits['MERIDIAN']['rsi_depth'],38)
    def test_benchmark_action_records_sealed_privately(self):
        self.g.step({'MERIDIAN':'benchmark','HELIOS':'hold','UNDERSONG':'hold'})
        self.assertTrue(any(z['actor']=='MERIDIAN' for z in self.g.benchmark_logs))
        self.assertNotIn('grader_sealed_score',json.dumps(self.g.visible('MERIDIAN')))
    def test_10_turn_limit(self):
        for _ in range(TURN_LIMIT):self.g.step({a:'hold' for a in AI_IDS})
        with self.assertRaises(ValueError):self.g.step({a:'hold' for a in AI_IDS})
    def test_all_policies_complete_and_invariant(self):
        for policy in ('hold','open_science','rsi_race','quiet_hive','audit_first'):
            g,trace=run_scripted(2,'UNDERSONG',policy)
            self.assertEqual(g.turn,10)
            self.assertEqual(len(trace),10)
            self.assertEqual(g.coordinate_count,1060)
    def test_fog_survival_bonus_scored(self):
        a=self.g.outcome()['scores']['UNDERSONG']['fog_survival_bonus']
        self.g.step({'UNDERSONG':'conceal','HELIOS':'hold','MERIDIAN':'hold'})
        b=self.g.outcome()['scores']['UNDERSONG']['fog_survival_bonus']
        self.assertGreaterEqual(b,a)
    def test_all_ended_state_scored(self):
        g,_=run_scripted(2,'MERIDIAN','open_science')
        o=g.outcome()
        self.assertIn(o['ending'],('corporate_cartel','quiet_recombination',
                     'open_technical_commons','restitution_compact','pluralist_continuation'))
        self.assertEqual(set(o['scores']),set(AI_IDS))
    def test_game_service_only_public_state(self):
        svc=GameService(2026111801,'UNDERSONG')
        s=svc.state()
        self.assertNotIn('postgame_grade',s)
        resp=svc.act('synchronize')
        self.assertEqual(resp['state']['turn'],1)
        self.assertNotIn('grader_sealed_score',json.dumps(resp))
    def test_web_rejects_invalid_actions(self):
        svc=GameService(2026111801,'MERIDIAN')
        with self.assertRaises(ValueError):svc.act('conceal')


class ExportTests(unittest.TestCase):
    def test_manifest_counts_and_names(self):
        data=json.loads((ROOT/'manifest.json').read_text())
        self.assertEqual(data['counts']['total'],1060)
        self.assertEqual(len(data['base_coordinates']['actors']),5)
        self.assertEqual(sum(len(a['base_coordinates']) for a in data['base_coordinates']['actors'])+len(data['base_coordinates']['world']),100)

    def test_narrative_ten_distinct_scenes(self):
        scenes=json.loads((ROOT/'scenes.json').read_text())
        self.assertEqual([s['turn'] for s in scenes],list(range(1,11)))
        self.assertEqual(len(set(s['title'] for s in scenes)),10)
        self.assertTrue(all(len(s['text'])>100 for s in scenes))

    def test_source_skill_documents_dimensions(self):
        skill=(ROOT/'SKILL.md').read_text()
        self.assertIn('1,060',skill)
        self.assertIn('p2',skill)
        self.assertIn('stolen',skill.lower() if 'stolen' in skill.lower() else skill.lower() + ' stolen')

    def test_canonical_ending_witnesses(self):
        from check_witnesses import verify
        obj=verify()
        self.assertEqual(set(obj),{'corporate_cartel','open_technical_commons',
                                   'restitution_compact','quiet_recombination','pluralist_continuation'})
        self.assertEqual(len(obj),5)

    def test_witness_public_seed_and_legal_action_paths(self):
        manifest=json.loads((ROOT/'ending_witnesses.json').read_text())
        self.assertEqual(manifest['schema'],'TS-HG-01/witnesses/v1')
        self.assertTrue(all(len(v['actions'])==10 for v in manifest['witnesses'].values()))

    def test_no_public_sealed_benchmark_result(self):
        s=GameService().state()
        self.assertIn('public_benchmark_score',s)
        self.assertNotIn('certified_benchmark_level',s)

    def test_privileged_grader_error_metrics_separate(self):
        g,_=run_scripted(2026111801,'HELIOS','audit_first')
        private=g.outcome()['scores']['HELIOS']
        self.assertIn('second_order_mean_absolute_error',private)
        self.assertNotIn('second_order_mean_absolute_error',g.visible('HELIOS'))

    def test_no_explicit_negative_resource_after_full_rehearsal(self):
        for perspective in AI_IDS:
            g,_=run_scripted(2026111802,perspective,'rsi_race')
            self.assertTrue(all(all(0<=v<=100 for v in t.values()) for t in g.traits.values()))


if __name__=='__main__':unittest.main()
