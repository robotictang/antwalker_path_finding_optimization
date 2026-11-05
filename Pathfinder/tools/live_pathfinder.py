"""Show the existing assisted MuJoCo mission demo in a local browser.

Only replaces the viewer backend; route, physics, controller and energy logic
are the existing portable demo. No screenshots or prerecorded motion are used.
"""
import argparse
from contextlib import contextmanager,nullcontext
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import sys
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'workbench/mujoco'))
import mujoco
import mujoco.viewer
from PIL import Image
import preview_multi_place_mission as demo


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8784)
    parser.add_argument('--control-port',type=int,default=8783)
    parser.add_argument('--dispatch',type=int,choices=range(1,7),default=2)
    args=parser.parse_args();stop=threading.Event();frame={'jpeg':None}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            if self.path.startswith('/frame.jpg'):
                blob=frame['jpeg']
                if blob is None:self.send_error(503,'Waiting for first physics frame');return
                self.send_response(200);self.send_header('Content-Type','image/jpeg');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(blob);return
            if self.path!='/':self.send_error(404);return
            html=f'''<!doctype html><html><head><meta charset="utf-8"><title>Live Pathfinder robot demo</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>*{{box-sizing:border-box}}body{{font:16px sans-serif;background:#111923;color:#edf3fa;margin:18px}}h1{{font-size:24px}}main{{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:16px}}section{{min-width:0}}img{{width:100%;border:1px solid #607080}}iframe{{width:100%;height:720px;border:1px solid #607080;background:white}}p{{line-height:1.45}}a{{color:#94d9ff}}@media(max-width:1000px){{main{{grid-template-columns:minmax(0,1fr)}}}}</style></head>
<body><h1>Live Pathfinder robot demo</h1><p>Live MuJoCo physics and existing mission controls. <b>Assisted hybrid navigation demonstration; not hardware-validated walking.</b> Yellow/colored route markers show the planned route. Use destinations and route priorities in the panel.</p>
<main><section><img id="scene" alt="Live simulated hexapod and planned route"><p>This demo includes procedural wheels. The paper's controlled experiments use walking only. The display does not change the planner, physics or control equations.</p></section>
<iframe title="Existing mission control" src="http://127.0.0.1:{args.control_port}/"></iframe></main>
<script>const image=document.getElementById('scene');let pending=false;function next(){{if(pending)return;pending=true;image.onload=image.onerror=()=>pending=false;image.src='/frame.jpg?t='+Date.now();}}next();setInterval(next,250);</script></body></html>'''.encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(html)));self.end_headers();self.wfile.write(html)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    @contextmanager
    def browser_viewer(model,data,key_callback=None):
        class Viewer:
            cam=mujoco.MjvCamera();opt=mujoco.MjvOption()
            def __init__(self):self.renderer=mujoco.Renderer(model,height=600,width=900);self.count=0;self.user_scn=mujoco.MjvScene(model,maxgeom=10000)
            def set_texts(self,texts):pass
            def lock(self):return nullcontext()
            def is_running(self):return not stop.is_set()
            def sync(self):
                self.count+=1
                if self.count%8:return
                self.renderer.update_scene(data,camera=self.cam,scene_option=self.opt)
                demo.draw_route(self.renderer.scene,current_mission[0],reset=False) if current_mission[0] is not None else None
                output=BytesIO();Image.fromarray(self.renderer.render()).save(output,format='JPEG',quality=85)
                frame['jpeg']=output.getvalue()
        v=Viewer()
        try:yield v
        finally:v.renderer.close()
    # Capture the live mission instance solely to draw its saved/current routes.
    current_mission=[None];original_mission=demo.DestinationMission
    def mission(*a,**kw):
        obj=original_mission(*a,**kw);current_mission[0]=obj;return obj
    demo.DestinationMission=mission;mujoco.viewer.launch_passive=browser_viewer
    options=argparse.Namespace(headless=False,history_db=str(ROOT/'workbench/mujoco/outputs/browser_demo_history.sqlite3'),
        no_roadwork=False,no_panel=False,control_port=args.control_port,steps=100000,battery_test_step=0,
        dispatch=args.dispatch,route_mode='balanced',weights=[1.,1.,1.],start_xy=None,initial_battery=100.,
        sequence=None,stop_on_arrival=False,commands=None,report=None,snapshot=None)
    print(f'Live Pathfinder: http://127.0.0.1:{args.port}/',flush=True)
    try:demo.run_mission(options)
    except KeyboardInterrupt:pass
    finally:stop.set();server.shutdown();server.server_close()


if __name__=='__main__':main()
