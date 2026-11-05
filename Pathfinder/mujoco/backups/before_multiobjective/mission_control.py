"""Local button controls and live route comparison, independent of viewer shortcuts."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import json,threading

KEYS={'place1':321,'place2':322,'place3':323,'place4':324,'charge':320,
      'route':325,'camera':326,'transform':327,'auto':328,'battery':329,'cancel':330,
      'shortest':400,'fastest':401,'reset':402}
KEY_NAMES={f'KP{i}':320+i for i in range(10)}|{'KP_DECIMAL':330,'SHORTEST':400,'FASTEST':401}


def key_code(value):
    if isinstance(value,int):return value
    value=str(value).upper()
    if value in KEY_NAMES:return KEY_NAMES[value]
    raise ValueError('Use KP0..KP9, KP_DECIMAL, SHORTEST, or FASTEST for scripted commands')


class ControlPanel:
    def __init__(self,commands,port=8767):
        self.state={};self.lock=threading.Lock()
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/state':
                    with outer.lock:payload=json.dumps(outer.state).encode()
                    kind='application/json'
                elif self.path in ('/','/index.html'):
                    payload=(Path(__file__).parent/'mission_control.html').read_bytes();kind='text/html'
                else:self.send_error(404);return
                self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
            def do_POST(self):
                if self.path!='/command':self.send_error(404);return
                try:
                    if int(self.headers.get('Content-Length',0))>1000:raise ValueError()
                    action=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))))['action']
                    commands.put(KEYS[action])
                except (ValueError,KeyError):self.send_error(400);return
                self.send_response(204);self.end_headers()
        self.server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        print(f'MISSION CONTROL: http://127.0.0.1:{port}',flush=True)

    def update(self,state):
        with self.lock:self.state=state

    def close(self):self.server.shutdown();self.server.server_close()
