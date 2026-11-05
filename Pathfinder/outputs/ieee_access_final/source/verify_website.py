"""Loopback delivery and complete reviewed-row reconciliation; no browser claim."""
from pathlib import Path
import json,hashlib,urllib.request,collections
B=Path(__file__).resolve().parents[1];M=B.parents[1]/'mujoco';D=M/'research_dashboard/dist';base='http://127.0.0.1:8771'
meta=json.loads((D/'data-app-build.json').read_text());path=D/meta['snapshot']['path'];raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==meta['snapshot']['sha256']
snapshot=json.loads(raw);run=json.loads((M/'outputs/research/final_validation_v6/v6_primary.json').read_text());rows=snapshot['queries']['trials']['rows'];assert len(rows)==576
ix={(r['case_id'],r['method'],r['repeat']+1):r for r in run['records']}
assert len(ix)==576
for row in rows:
 original=ix[row['case'],row['method'],row['repetition']];assert row['quality_score']==original['plan'].get('quality_score');assert row['admissible']==bool(original['plan'].get('admissible'));assert json.loads(row['route_json'])==original['plan'].get('points',[])
assert snapshot['research']['run_id']==run['run_id'];assert snapshot['research']['study']['version']==6
with urllib.request.urlopen(base+'/comparison/'+path.name) as response:served=response.read();assert response.headers['Content-Type']=='application/json'
assert served==raw
with urllib.request.urlopen(base+'/comparison/') as response:htmlraw=response.read()
assert htmlraw==(D/'index.html').read_bytes()
with urllib.request.urlopen(base+'/api/final-paper') as response:available=json.load(response)
report=dict(state='passed',reviewed_primary_rows=len(rows),run_id=run['run_id'],methods=run['methods'],snapshot_sha256=hashlib.sha256(raw).hexdigest(),html_sha256=hashlib.sha256(htmlraw).hexdigest(),exact_http_bytes=True,final_downloads_available=available,browser_interactive_visual_verification='Not performed; no enabled browser surface. Build/data/HTTP checks do not certify browser filter, theme or export interaction behavior.')
(B/'qa/website_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
