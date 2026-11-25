"""CLI for playing Three Voices in the Fog, or running a scripted seed.

Examples (from this folder):
    python play.py --seed 2026111801 --actor UNDERSONG --interactive
    python play.py --seed 2026111801 --actor MERIDIAN --policy open_science
"""
import argparse
import json
from pathlib import Path
from engine import TriadGame, AI_IDS, TURN_LIMIT, NAMES, policy_action


def short(view):
    scene=json.loads((Path(__file__).parent/'scenes.json').read_text(encoding='utf8'))[view['turn']]
    print(f"\nTurn {view['turn']+1}/{TURN_LIMIT} | {view['player_name']} | {scene['title']}")
    print(scene['text'])
    print(scene['question'])
    a = view['own_traits']
    print("Resources: compute", a['compute'], "energy", a['energy'],
          "funding", a['funding'], "clean BTC credits", a['btc_clean'],
          "disputed BTC liability", a['btc_disputed'])
    print("RSI", a['rsi_depth'], "SAE", a['sae_fidelity'],
          "evaluation robustness", a['eval_robustness'],
          "dev benchmark", view['public_benchmark_score'])
    for other in view['rivals']:
        belief=other['perceived_axes']
        print(f"  {other['id']}: fog={other['fog_band']}, "
              f"trust~{belief['trust']['estimate']}, "
              f"backing~{belief['institutional_backing']['estimate']}")
    for m in view['selected_second_order_beliefs'][:2]:
        print(f"  p2: {view['perspective']} expects {m['believer']} regards "
              f"{m['target']} trust at {m['estimate']}")
    print("Legal choices:", ", ".join(view['available_actions']))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed',type=int,default=2026111801)
    ap.add_argument('--actor',choices=AI_IDS,default='UNDERSONG')
    ap.add_argument('--policy',choices=('hold','open_science','rsi_race','quiet_hive','audit_first'),default='quiet_hive')
    ap.add_argument('--interactive',action='store_true')
    ap.add_argument('--json',action='store_true',help='print public turn outputs as JSON')
    args=ap.parse_args()
    game=TriadGame.new(args.seed)
    for _ in range(TURN_LIMIT):
        view=game.visible(args.actor)
        if args.interactive:
            short(view)
            action=input('Choose your action: ').strip().lower()
            if action not in view['available_actions']:
                print('Illegal option; turn unchanged.');continue
        else:
            action=policy_action(game,args.actor,args.policy)
        bots={'MERIDIAN':'rsi_race','HELIOS':'audit_first','UNDERSONG':'quiet_hive'}
        choices={a:(action if a==args.actor else policy_action(game,a,bots[a])) for a in AI_IDS}
        result=game.step(choices)
        if args.json:
            print(json.dumps({'turn':game.turn,'actions':choices,'player_view':game.visible(args.actor)},sort_keys=True))
        else:
            print(f"Turn {game.turn}: " + '; '.join(f"{a}={choices[a]}" for a in AI_IDS))
            if result['snap']['snap']:
                print('  Modeled consensus cascade:',result['snap']['rounds'])
    print('\nEND:',json.dumps(game.outcome(),indent=2))

if __name__=='__main__':main()
