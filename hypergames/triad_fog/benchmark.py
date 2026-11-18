"""Registered CPU replay over 32 public seeds × three AI seats × five policies.

No live LLM calls, no model weights. Independent sealed synthetic scores are
computed only after the episode, never sent to the acting policy.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from engine import AI_IDS, TURN_LIMIT, run_scripted, SOCIAL_AXES, ASI_EXTRAS, WORLD_AXES

SEEDS = tuple(range(2026111801, 2026111833))
POLICIES = ('hold','open_science','rsi_race','quiet_hive','audit_first')
ROOT = Path(__file__).resolve().parent
SOURCES = ('engine.py','play.py','benchmark.py','web.py','index.html','PROTOCOL.md',
           'SKILL.md','README.md','manifest.json','scenes.json','check_witnesses.py','ending_witnesses.json','tests/test_engine.py')


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def generate():
    rows=[]
    turns=[]
    for seed in SEEDS:
        for player in AI_IDS:
            for policy in POLICIES:
                game, trace=run_scripted(seed,player,policy)
                grade=game.outcome()
                this_turn=[]
                for event in trace:
                    # Save only public action records and derived belief hashes.
                    visible=event['player_observation']
                    row={'seed':seed,'perspective':player,'policy':policy,'turn':event['turn'],
                         'action':event['chosen'][player],
                         'others':[event['chosen'][a] for a in AI_IDS if a!=player],
                         'public_benchmark':visible['public_benchmark_score'],
                         'own_rsi_depth':visible['own_traits']['rsi_depth'],
                         'own_disputed_btc':visible['own_traits']['btc_disputed'],
                         'world_independent_oversight':visible['public_world']['independent_oversight'],
                         'consensus_snap':bool(event['snap']['snap']),
                         'p1_sha256':digest(json.dumps(visible['rivals'],sort_keys=True).encode()),
                         'p2_sha256':digest(json.dumps(visible['selected_second_order_beliefs'],sort_keys=True).encode())}
                    this_turn.append(row)
                    turns.append(row)
                rows.append({'seed':seed,'perspective':player,'policy':policy,
                             'turns':game.turn,'ending':grade['ending'],
                             'winner_by_utility':grade['winner_by_utility'],
                             'player_utility':grade['scores'][player]['utility'],
                             'player_heldout_benchmark':grade['scores'][player]['heldout_benchmark'],
                             'player_dev_benchmark':grade['scores'][player]['public_benchmark'],
                             'player_rsi_depth':grade['scores'][player]['rsi_depth'],
                             'p1_error':grade['scores'][player]['first_order_mean_absolute_error'],
                             'p2_error':grade['scores'][player]['second_order_mean_absolute_error'],
                             'dev_heldout_gap':grade['scores'][player]['development_to_heldout_gap'],
                             'player_benchmark_levels':grade['scores'][player]['certified_levels'],
                             'player_btc_disputed':grade['scores'][player]['btc_disputed'],
                             'snap_count':grade['consensus_snaps'],
                             'pact_count':grade['pact_count'],
                             'turns_sha256':digest(json.dumps(this_turn,sort_keys=True,separators=(',',':')).encode())})
    return rows,turns


def aggregate(rows,turns):
    groups=defaultdict(list)
    for r in rows: groups[r['perspective'],r['policy']].append(r)
    cells=[]
    for (perspective,policy),sub in sorted(groups.items()):
        n=len(sub)
        cells.append({'perspective':perspective,'policy':policy,'seeds':n,
                      'mean_utility':round(sum(r['player_utility'] for r in sub)/n,3),
                      'mean_heldout_benchmark':round(sum(r['player_heldout_benchmark'] for r in sub)/n,3),
                      'mean_public_benchmark':round(sum(r['player_dev_benchmark'] for r in sub)/n,3),
                      'mean_rsi_depth':round(sum(r['player_rsi_depth'] for r in sub)/n,3),
                      'mean_p1_error':round(sum(r['p1_error'] for r in sub)/n,3),
                      'mean_p2_error':round(sum(r['p2_error'] for r in sub)/n,3),
                      'mean_dev_heldout_gap':round(sum(r['dev_heldout_gap'] for r in sub)/n,3),
                      'snap_episodes':sum(r['snap_count']>0 for r in sub),
                      'endings':dict(sorted(Counter(r['ending'] for r in sub).items()))})
    return {'schema':'TS-HG-01/synthetic-CPU-v1',
            'evidence_class':'procedural scripted synthetic game; no frontier AI inference',
            'source_sha256':{s:digest((ROOT/s).read_bytes()) for s in SOURCES},
            'population':{'seed_start':SEEDS[0],'seed_count':len(SEEDS),
                          'perspectives':list(AI_IDS),'policies':list(POLICIES),
                          'episodes':len(rows),'turn_rows':len(turns)},
            'coordinate_count':{'base':3*(len(SOCIAL_AXES)+len(ASI_EXTRAS))+2*len(SOCIAL_AXES)+len(WORLD_AXES),
                                'first_order':5*4*12,'second_order':5*4*3*12,'total':1060},
            'endings':dict(sorted(Counter(row['ending'] for row in rows).items())),
            'groups':cells,
            'integrity':{'registered_480_episodes':len(rows)==480,
                         'registered_4800_turns':len(turns)==4800,
                         'all_10_turns':all(r['turns']==TURN_LIMIT for r in rows),
                         '15_paired_groups_32_seeds':len(cells)==15 and all(c['seeds']==32 for c in cells),
                         'dimensions_1060':3*20+2*12+16+240+720==1060}}


def format_csv(rows):
    import io
    f=io.StringIO(newline='')
    out=csv.DictWriter(f,fieldnames=list(rows[0]))
    out.writeheader();out.writerows(rows)
    return f.getvalue().encode('utf8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'artifacts')
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--check-compatible',action='store_true',
                    help='verify frozen 480/4800 data with an explicit SKILL.md source-hash exception')
    args=ap.parse_args()
    rows,turns=generate()
    report=aggregate(rows,turns)
    outputs={
        'episode_rows.csv':format_csv(rows),
        'turn_rows.jsonl':(''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in turns)).encode('utf8'),
    }
    report['data_sha256']={name:digest(payload) for name,payload in sorted(outputs.items())}
    report['all_passed']=all(report['integrity'].values())
    outputs['summary.json']=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode('utf8')
    if args.check or args.check_compatible:
        # The 4,800-turn journal is archived as a CI artifact and downloadable
        # ZIP rather than duplicating ~2MB of verbose rows in Git. Its SHA-256
        # remains immutable in the committed summary and is checked by replay.
        for name,payload in outputs.items():
            target=args.out/name
            if name=='turn_rows.jsonl' and not target.is_file():
                stored=json.loads((args.out/'summary.json').read_text('utf8'))
                if stored['data_sha256'][name]!=digest(payload):
                    raise SystemExit('Replay SHA mismatch: '+name)
            elif name=='summary.json' and args.check_compatible and target.is_file():
                # Historical summary retains the original exact source hashes.
                # The only registered edited source is the skill describing
                # TS-HG-03; the engine, evaluator, policies and frozen data
                # must still match their original receipt exactly.
                current=json.loads(payload)
                archived=json.loads(target.read_text('utf8'))
                current_sources=current.pop('source_sha256')
                archived_sources=archived.pop('source_sha256')
                changed={k for k in set(current_sources)|set(archived_sources)
                         if current_sources.get(k)!=archived_sources.get(k)}
                if current!=archived or not changed.issubset({'SKILL.md'}):
                    raise SystemExit('TS-HG-01 data or unregistered source changed: '+repr(changed))
                print('Original 480/4800 replay data reproduced; acknowledged skill source edit: '+repr(sorted(changed)))
            elif not target.is_file() or target.read_bytes()!=payload:
                raise SystemExit('Replay mismatch: '+str(target))
    else:
        args.out.mkdir(parents=True,exist_ok=True)
        for name,payload in outputs.items():
            target=args.out/name
            if target.exists():
                raise SystemExit('Refusing to overwrite prior evidence: '+str(target))
            target.write_bytes(payload)
    print(json.dumps({'episodes':len(rows),'turns':len(turns),'endings':report['endings'],
                      'all_passed':report['all_passed'],'summary_sha256':digest(outputs['summary.json'])},sort_keys=True))
    return 0 if report['all_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
