"""Validate every ending against an explicit, playable ten-turn public action path."""
from __future__ import annotations
import json
from pathlib import Path
from engine import AI_IDS, TriadGame

ROOT=Path(__file__).parent


def witness_paths(seed=2026111801):
    hold={a:'hold' for a in AI_IDS}
    return {
        'corporate_cartel':[{'MERIDIAN':'pact','HELIOS':'pact','UNDERSONG':'hold'} for _ in range(10)],
        'open_technical_commons':[{a:'publish' for a in AI_IDS} for _ in range(10)],
        'restitution_compact':[{a:('audit' if n<4 else 'restitute') for a in AI_IDS} for n in range(10)],
        'quiet_recombination':[
           {'MERIDIAN':'hold','HELIOS':'hold','UNDERSONG':act}
           for act in ('synchronize','conceal','synchronize','conceal','synchronize',
                       'conceal','synchronize','conceal','synchronize','conceal')],
        'pluralist_continuation':[hold.copy() for _ in range(10)],
    }


def verify(seed=2026111801):
    out={}
    for ending,path in witness_paths(seed).items():
        game=TriadGame.new(seed)
        for a in path:
            for actor,act in a.items():
                if act not in game.action_menu(actor):
                    raise AssertionError('witness contains illegal action: '+str((ending,actor,act)))
            game.step(a)
        score=game.outcome()
        if score['ending']!=ending:
            raise AssertionError(f'{ending}: reached {score["ending"]}')
        out[ending]={'seed':seed,'actions':path,'winner':score['winner_by_utility'],
                     'snap_count':score['consensus_snaps']}
    return out

if __name__=='__main__':
    report={'schema':'TS-HG-01/witnesses/v1','witnesses':verify()}
    dest=ROOT/'ending_witnesses.json'
    if dest.exists():
        if json.loads(dest.read_text())!=report:raise SystemExit('Witness receipt mismatch')
        print('All five ending witnesses reproduce')
    else:
        dest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print('Wrote five ending witnesses')
