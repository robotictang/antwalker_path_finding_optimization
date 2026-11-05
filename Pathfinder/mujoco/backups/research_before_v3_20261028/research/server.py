"""Loopback-only research console with bounded job launch and result downloads."""
import argparse
import csv
import fcntl
import io
import json
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs,urlparse
from research.run import ROOT,OUT
from research.planning import METHODS
from research.export_dashboard import export

WEB=Path(__file__).parent/'web';job_lock=threading.Lock()
JOB=dict(state='idle',completed=0,total=0,message='Ready')

def result_file(identifier=None):
    if not identifier:
        latest=json.loads((OUT/'latest.json').read_text())
        identifier=latest['run_id']
    if not re.fullmatch(r'[A-Za-z0-9_-]+',identifier):raise ValueError('Invalid run identifier')
    path=OUT/(identifier+'.json')
    if not path.is_file():raise ValueError('Run not found')
    return path

def launch(payload):
    global JOB
    if not job_lock.acquire(blocking=False):raise ValueError('Another experiment or dashboard build is running')
    try:
        kind=payload.get('kind','benchmark')
        if kind=='dashboard':
            path=result_file(payload.get('run'))
            command=[sys.executable,'-m','research.export_dashboard','--run',str(path),'--build']
        elif kind=='gait':command=[sys.executable,'-m','research.gait_sweep']+(['--quick'] if payload.get('quick',True) else [])
        elif kind=='benchmark':
            suite=payload.get('suite','pilot')
            if suite not in ('smoke','pilot','full'):raise ValueError('Invalid suite')
            seconds=float(payload.get('planning_seconds',2.))
            if not .1<=seconds<=30:raise ValueError('Planning budget must be 0.1..30 seconds')
            service=payload.get('service','charge')
            if service not in ('charge','swap'):raise ValueError('Invalid service')
            command=[sys.executable,'-m','research.run','--suite',suite,'--planning-seconds',str(seconds),'--service',service]
            methods=payload.get('methods')
            if methods is not None:
                if not isinstance(methods,list) or not methods or len(set(methods))!=len(methods) or any(m not in METHODS for m in methods):raise ValueError('Select valid distinct methods')
                command.extend(['--methods',*methods])
            repeats=payload.get('repeats',1)
            if not isinstance(repeats,int) or not 1<=repeats<=30:raise ValueError('Repetitions must be 1..30')
            command.extend(['--repeats',str(repeats)])
            if payload.get('execute',True):command.append('--execute')
            if payload.get('hybrid',False):command.append('--hybrid')
        else:raise ValueError('Unknown job')
        OUT.mkdir(exist_ok=True,parents=True)
        log_path=OUT/'console_job.log'
        log=log_path.open('w');process=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        JOB=dict(state='running',kind=kind,pid=process.pid,message='Experiment started',started_at=time.time())
        def monitor():
            global JOB
            try:
                code=process.wait();log.close()
                JOB.update(state='complete' if code==0 else 'failed',exit_code=code,message='Finished' if code==0 else 'See job log')
                if code==0 and kind=='benchmark' and (ROOT/'research_dashboard/src').is_dir():
                    JOB.update(state='running',message='Updating comparison dashboard')
                    export(build=True)
                    JOB.update(state='complete',message='Results and comparison dashboard updated')
            except Exception as error:JOB.update(state='failed',message=str(error))
            finally:job_lock.release()
        threading.Thread(target=monitor,daemon=True).start()
    except Exception:
        job_lock.release();raise

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def reply(self,data,code=200,content_type='application/json'):
        # Static JSON snapshots are already encoded bytes. Serialize API objects
        # only; serializing a snapshot again disconnects the chart data request.
        body=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode() if content_type=='application/json' else str(data).encode()
        self.send_response(code);self.send_header('Content-Type',content_type);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        p=urlparse(self.path);query=parse_qs(p.query)
        try:
            if p.path=='/api/status':
                log=OUT/'console_job.log';payload=dict(JOB)
                payload['log']=log.read_text()[-6000:] if log.exists() else ''
                if payload.get('state')!='running':
                    lock_path=OUT/'experiment.lock'
                    if lock_path.exists():
                        with lock_path.open('a') as handle:
                            try:
                                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                            except BlockingIOError:
                                latest=OUT/'latest.json'
                                if latest.exists():
                                    current=json.loads(latest.read_text())
                                    total=len(current.get('cases',[]))*len(current.get('methods',[]))*current.get('repeats',1)
                                    count=len(current.get('records',[]))
                                    payload.update(state='running',kind='external',completed=count,total=total,
                                      message=f"{current.get('suite','Experiment')}: {count} of {total} attempts recorded")
                                    study_log=ROOT/'outputs/reliability_study.log'
                                    if current.get('study') and study_log.exists():payload['log']=study_log.read_text()[-6000:]
                            else:fcntl.flock(handle,fcntl.LOCK_UN)
                if payload.get('state')=='running' and payload.get('kind') in ('benchmark','gait'):
                    latest=OUT/('latest_gait.json' if payload['kind']=='gait' else 'latest.json')
                    if latest.exists() and latest.stat().st_mtime>=payload.get('started_at',0):
                        try:
                            running=json.loads(latest.read_text())
                            total=len(running.get('tracks',[]))*len(running.get('settings',[])) if payload['kind']=='gait' else len(running.get('cases',[]))*len(running.get('methods',[]))*running.get('repeats',1)
                            payload.update(completed=len(running.get('records',[])),total=total,
                              message=f"{len(running.get('records',[]))} of {total} attempts recorded")
                        except (ValueError,OSError):pass
                self.reply(payload);return
            if p.path=='/api/runs':
                rows=[]
                for path in sorted(OUT.glob('*.json'),reverse=True):
                    if path.name in ('latest.json','latest_gait.json','dashboard_snapshot.json'):continue
                    try:
                        data=json.loads(path.read_text())
                        if 'run_id' not in data:continue
                        rows.append({k:data.get(k) for k in ('run_id','created_at','state','suite','kind','execute','methods','repeats')})
                    except (ValueError,OSError):continue
                self.reply(rows);return
            if p.path=='/api/result':self.reply(json.loads(result_file(query.get('run',[None])[0]).read_text()));return
            if p.path=='/api/study':
                path=OUT/'reliability_v1/study_summary.json'
                self.reply(json.loads(path.read_text()) if path.exists() else None);return
            if p.path=='/api/gait':
                path=OUT/'latest_gait.json';self.reply(json.loads(path.read_text()) if path.exists() else None);return
            if p.path=='/api/references':self.reply(json.loads((Path(__file__).parent/'references.json').read_text()));return
            if p.path=='/api/download':
                path=result_file(query.get('run',[None])[0]);format=query.get('format',['json'])[0]
                if format=='csv':path=path.with_suffix('.csv')
                if not path.exists():raise ValueError('Download not available')
                body=path.read_bytes();self.send_response(200);self.send_header('Content-Type','text/csv' if format=='csv' else 'application/json')
                self.send_header('Content-Disposition',f'attachment; filename="{path.name}"');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
            if p.path.startswith('/comparison'):
                suffix=p.path[len('/comparison'):].lstrip('/') or 'index.html'
                base=ROOT/'research_dashboard/dist';path=(base/suffix).resolve()
                if not path.is_relative_to(base.resolve()):raise ValueError('Invalid path')
            else:
                path=(WEB/(p.path.lstrip('/') or 'index.html')).resolve()
                if not path.is_relative_to(WEB.resolve()):raise ValueError('Invalid path')
            if not path.is_file():self.reply({'error':'Not found'},404);return
            import mimetypes
            self.reply(path.read_bytes(),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        except (ValueError,OSError) as error:self.reply({'error':str(error)},404)
    def do_POST(self):
        origin=self.headers.get('Origin')
        allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if origin not in allowed or self.headers.get('Content-Type','').split(';')[0]!='application/json':
            self.reply({'error':'Same-origin JSON requests only'},403);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16384:raise ValueError('Invalid request length')
            payload=json.loads(self.rfile.read(length))
            if self.path!='/api/jobs':raise ValueError('Unknown operation')
            launch(payload);self.reply(JOB,202)
        except (ValueError,TypeError) as error:self.reply({'error':str(error)},400)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8771);a=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler)
    print(f'Research console ready at http://127.0.0.1:{a.port}',flush=True)
    server.serve_forever()

if __name__=='__main__':main()
