"""Recompute document tables from the unchanged frozen v3 evidence."""
import hashlib,json,collections,statistics
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];STUDY=ROOT/'mujoco/outputs/research/strong_study_v3'
def load(n):return json.loads((STUDY/(n+'.json')).read_text())
r=load('v3_heldout_planning');ph=load('v3_heldout_physics');manifest=load('manifest');comparison=load('comparison');audit=load('audit')
assert audit['state']=='passed' and audit['attempts']==684
methods=r['methods'];idx={(x['case_id'],x['method'],x['repeat']):x for x in r['records']};pidx={(x['case_id'],x['method']):x for x in ph['records']}
analysis=dict(methods=methods,primary_run=r['run_id'],physics_run=ph['run_id'],versions=r['versions'],hardware=r['hardware'],selection=load('locked_parameters'),comparison=comparison,ablation=load('ablation_comparison'),audit=audit)
analysis['planning']=[]
for m in methods:
 rows=[x for x in r['records'] if x['method']==m];ad=[x for x in rows if x['plan'].get('admissible')]
 for x in rows:
  p=x['plan'];q=p.get('metrics')
  if q:
   score=q['distance_m']/50+q['estimated_seconds']/90+q['energy_percent']/30+.25*q['terrain_exposure']/20
   assert abs(score-p['quality_score'])<1e-8
 analysis['planning'].append(dict(**next(x for x in r['summary'] if x['method']==m),status_counts=dict(collections.Counter(x['status'] for x in rows)),battery_rejections=sum(not x['plan'].get('battery_ok',True) for x in rows),deadline_rejections=sum(not x['plan'].get('deadline_ok',True) for x in rows),exposure_rejections=sum(not x['plan'].get('terrain_budget_ok',True) for x in rows),admitted_mean_distance_m=float(np.mean([x['plan']['metrics']['distance_m'] for x in ad])),admitted_mean_exposure=float(np.mean([x['plan']['metrics']['terrain_exposure'] for x in ad]))))
analysis['by_world']=[]
for c in r['cases']:
 row=dict(case=c['id'],family=c['world']['family'],deadline=c['deadline_s'],battery=c['battery_percent'],risk=c['risk_budget'],friction=c['world']['friction_scale'],energy_multiplier=c['energy_multiplier'])
 for m in methods:
  vals=[idx[c['id'],m,j]['plan'] for j in range(r['repeats'])];row[m+'_admitted']=sum(bool(x.get('admissible')) for x in vals)
  if m!='proposed':
   paired=[(idx[c['id'],m,j]['plan'],idx[c['id'],'proposed',j]['plan']) for j in range(r['repeats'])];paired=[(a,b) for a,b in paired if a.get('admissible') and b.get('admissible')]
   row[m+'_score_advantage']=float(np.mean([a['quality_score']-b['quality_score'] for a,b in paired])) if paired else None
   row[m+'_score_improvement_percent']=float(np.mean([100*(a['quality_score']-b['quality_score'])/a['quality_score'] for a,b in paired])) if paired else None
 analysis['by_world'].append(row)
analysis['development']={name:load('v3_development_'+name)['summary'] for name in ['default','alternative']}
analysis['physics']=ph['summary'];analysis['physics_pairs']=[]
for m in methods:
 if m=='proposed':continue
 pairs=[(pidx[c['id'],'proposed'],pidx[c['id'],m]) for c in ph['cases']]
 analysis['physics_pairs'].append(dict(baseline=m,worlds=len(pairs),mean_proposed_minus_baseline_task_seconds=float(np.mean([a['execution']['task_time_s']-b['execution']['task_time_s'] for a,b in pairs])),mean_proposed_minus_baseline_work_j=float(np.mean([a['execution']['positive_actuator_work_j']-b['execution']['positive_actuator_work_j'] for a,b in pairs]))))
completed=[x for x in ph['records'] if x.get('execution',{}).get('task_time_s') is not None]
analysis['prediction']=dict(executions=len(completed),time_mae_s=float(np.mean([abs(x['prediction_validation']['task_time_error_s']) for x in completed])),time_bias_s=float(np.mean([x['prediction_validation']['task_time_error_s'] for x in completed])),simulation_battery_mae_pp=float(np.mean([abs(x['prediction_validation']['task_battery_error_pp']) for x in completed])),simulation_battery_bias_pp=float(np.mean([x['prediction_validation']['task_battery_error_pp'] for x in completed])))
case=next(c for c in r['cases'] if c['id']=='heldout_22');analysis['worked_case']=dict(case={k:v for k,v in case.items() if k not in ['world','map','return_route']},records={m:idx['heldout_22',m,0] for m in methods})
analysis['preparation']=dict(mean_total_seconds=float(np.mean([c['total_preparation_seconds'] for c in r['cases']])),max_total_seconds=max(c['total_preparation_seconds'] for c in r['cases']))
analysis['family_summary']=[dict(family=f,worlds=sum(c['world']['family']==f for c in r['cases']),methods={m:sum(row[m+'_admitted'] for row in analysis['by_world'] if row['family']==f) for m in methods}) for f in ['open','clutter','rough','corridor']]
analysis['diagnostics']={}
d=load('v3_old_case_seed_diagnostic')
for m in d['methods']:
 rows=[x for x in d['records'] if x['method']==m];analysis['diagnostics'][m]=dict(attempts=len(rows),returned=sum(bool(x['plan'].get('metrics')) for x in rows),admitted=sum(bool(x['plan'].get('admissible')) for x in rows),outcomes=dict(collections.Counter(x['status'] for x in rows)))
analysis['evidence_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in STUDY.glob('*.json')}
(BASE/'source/verified_analysis.json').write_text(json.dumps(analysis,indent=2,allow_nan=False))
print(json.dumps({k:analysis[k] for k in ['prediction','physics_pairs','preparation','family_summary']},indent=2))
