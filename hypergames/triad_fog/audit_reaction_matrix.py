"""Reproduce the public, purely authoring-stage TS-HG-04 scene audit.

Runs ten templates at the SAME initial player observation per perspective.
This is not a 10-turn history or an independent model benchmark.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from engine import AI_IDS,TriadGame
from reaction_matrix import MathScope,event_audit,projection_certificate

HERE=Path(__file__).resolve().parent
SEED=2026111801
SMALL=MathScope(own_vars=5,other_ai_vars_each=5,public_vars_each=4,
                world_vars=3,p2_terms=3,interactions=5)


def collect():
    source={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest()
            for p in ("reaction_matrix.py","engine.py")}
    all_rows=[]; certificates=[]
    for actor in AI_IDS:
        observation=TriadGame.new(SEED).visible(actor)
        for turn in range(1,11):
            for row in event_audit(observation,turn):
                row={"actor":actor,"turn":turn,**row}
                all_rows.append(row)
                c=projection_certificate(observation,turn,row["action"],row["respondent"],
                                         MathScope(),SMALL)
                certificates.append(c)
    counts=defaultdict(Counter)
    for row in all_rows:counts[row['action']][str(row['selected'])]+=1
    canon=json.dumps(all_rows,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    distances=[F(row['separation_dirac_squared']) for row in all_rows]
    results={"schema":"TS-HG-04/public-development-authoring-audit-v1",
             "seed":SEED,"observation_policy":"same-initial-observation-all-ten-templates",
             "perspectives":list(AI_IDS),"scenes":10,
             "respondent_option_rows":len(all_rows),"competing_reactions":2*len(all_rows),
             "formula_term_min":min(r['terms'] for r in all_rows),
             "formula_term_max":max(r['terms'] for r in all_rows),
             "mean_terms":round(sum(x['terms'] for x in all_rows)/len(all_rows),4),
             "p2_rows":sum(row['p2_terms']>0 for row in all_rows),
             "interaction_rows":sum(row['interactions']>0 for row in all_rows),
             "response_selections":dict(Counter(str(row['selected']) for row in all_rows)),
             "action_balance":{k:dict(v) for k,v in sorted(counts.items())},
             "min_reaction_distance_squared":str(min(distances)),
             "max_reaction_distance_squared":str(max(distances)),
             "small_projection":SMALL.__dict__,
             "small_scope_winner_matches":sum(c['winner_matches'] for c in certificates),
             "small_scope_winner_certified":sum(c['winner_certified'] for c in certificates),
             "rows_sha256":hashlib.sha256(canon.encode('utf8')).hexdigest(),
             "source_sha256":source,
             "evidence_class":"synthetic source-only descriptive development"}
    return results


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out',type=Path,default=HERE/'artifacts/reaction_matrix_dev_summary.json')
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    data=json.dumps(collect(),sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    if args.check:
        if args.out.read_text(encoding='utf8')!=data:raise SystemExit('FAIL: source-locked audit drift')
        print('PASS: source-locked TS-HG-04 public authoring audit')
    else:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(data,encoding='utf8')
        print('wrote',args.out)

if __name__=='__main__':main()
