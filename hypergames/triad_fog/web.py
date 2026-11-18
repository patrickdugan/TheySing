"""Local browser client for TS-HG-01; run `python web.py`.

This demo server binds only to 127.0.0.1 and has no outbound actions.
It exposes only player-visible state and a postgame grader result.
"""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from engine import AI_IDS, TriadGame, TURN_LIMIT, policy_action

ROOT=Path(__file__).parent
SCENES=json.loads((ROOT/'scenes.json').read_text(encoding='utf8'))


class GameService:
    def __init__(self, seed=2026111801, actor='UNDERSONG'):
        self.reset(seed,actor)

    def reset(self,seed,actor):
        if actor not in AI_IDS or type(seed) is not int or seed<0:
            raise ValueError('invalid role or seed')
        self.game=TriadGame.new(seed)
        self.actor=actor
        return self.state()

    def state(self):
        view=self.game.visible(self.actor)
        view['scene']=SCENES[min(self.game.turn, TURN_LIMIT-1)]
        if self.game.turn==TURN_LIMIT:
            view['postgame_grade']=self.game.outcome()
        return view

    def act(self,action):
        if self.game.turn>=TURN_LIMIT:
            raise ValueError('game ended, start a new campaign')
        if action not in self.game.action_menu(self.actor):
            raise ValueError('illegal choice')
        baseline={'MERIDIAN':'rsi_race','HELIOS':'audit_first','UNDERSONG':'quiet_hive'}
        actions={a:(action if a==self.actor else policy_action(self.game,a,baseline[a])) for a in AI_IDS}
        result=self.game.step(actions)
        return {'transition':result, 'state':self.state()}


class Handler(BaseHTTPRequestHandler):
    service=GameService()

    def json_response(self,payload,status=200):
        body=json.dumps(payload,ensure_ascii=False,sort_keys=True).encode('utf8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path=urlparse(self.path).path
        if path in ('/', '/index.html'):
            data=(ROOT/'index.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        elif path=='/state':
            self.json_response(self.service.state())
        else:
            self.json_response({'error':'not found'},404)

    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=4096:
                raise ValueError('payload length exceeds limit')
            body=json.loads(self.rfile.read(length))
            if not isinstance(body,dict):
                raise ValueError('invalid JSON request')
            path=urlparse(self.path).path
            if path=='/new':
                result=self.service.reset(body.get('seed',2026111801),body.get('actor','UNDERSONG'))
            elif path=='/act':
                result=self.service.act(body.get('action'))
            else:
                self.json_response({'error':'not found'},404);return
            self.json_response(result)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as exc:
            self.json_response({'error':str(exc)},400)


def main():
    import argparse
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',type=int,default=8786)
    ap.add_argument('--seed',type=int,default=2026111801)
    ap.add_argument('--actor',choices=AI_IDS,default='UNDERSONG')
    args=ap.parse_args()
    Handler.service=GameService(args.seed,args.actor)
    httpd=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Open http://127.0.0.1:{args.port}/ for the local Three Voices in the Fog demo')
    try:httpd.serve_forever()
    except KeyboardInterrupt:pass
    finally:httpd.server_close()

if __name__=='__main__':main()
