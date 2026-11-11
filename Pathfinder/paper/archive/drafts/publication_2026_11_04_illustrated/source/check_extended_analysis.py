"""Independent reconciliation of the new descriptive displays with raw records."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,statistics
import numpy as np
B=Path(__file__).resolve().parents[1]
p=json.loads((B/'raw_study/primary.json').read_text());a=json.loads((B/'results/expanded_analysis.json').read_text());cases={c['id']:c for c in p['cases']}
lookup={(r['case_id'],r['repeat'],r['method']):r['plan'] for r in p['records']}
for row in a['family']:
 raw=[r for r in p['records'] if r['method']==row['method'] and cases[r['case_id']]['world']['family']==row['family']]
 assert len(raw)==row['attempts']==24
 assert sum(r['plan']['admissible'] for r in raw)==row['admitted']
for row in a['computation']:
 raw=[r['plan'] for r in p['records'] if r['method']==row['method']]
 assert row['median_seconds']==statistics.median(r['planning_seconds'] for r in raw)
 assert row['maximum_seconds']==max(r['planning_seconds'] for r in raw)
 assert row['median_evaluations']==statistics.median(r['optimizer']['fitness_evaluations'] for r in raw)
 assert row['at_ceiling']==sum(r['optimizer']['fitness_evaluations']==240 for r in raw)
for row in a['sensitivity']:
 means=[]
 for c in p['cases']:
  effects=[]
  for j in range(3):
   v=lookup[(c['id'],j,'proposed_v4')];r=lookup[(c['id'],j,row['method'])]
   if v['admissible'] and r['admissible']:effects.append(100*(r['quality_score']-v['quality_score'])/r['quality_score'])
  if effects:means.append(statistics.mean(effects))
 omitted=[statistics.mean(means[:i]+means[i+1:]) for i in range(len(means))]
 assert len(means)==row['n']
 assert abs(statistics.mean(means)-row['mean_percent'])<1e-10
 assert abs(min(omitted)-row['minimum_omission_mean_percent'])<1e-10
 assert abs(max(omitted)-row['maximum_omission_mean_percent'])<1e-10
c=json.loads((B/'results/corrected_gravity_probe.json').read_text())
for key,name in [('frozen_execution_sha256','research/execution.py'),('frozen_locomotion_sha256','hybrid_locomotion.py')]:
 assert c['protocol'][key]==hashlib.sha256((B.parent/'workbench/mujoco'/name).read_bytes()).hexdigest()
assert all(x['execution']['physics_samples']==45000 for x in c['records'])
assert all(x['realized_settings']['enabled_before']==18 and not any(x['realized_settings']['values_after']) for x in c['records'])
report=dict(state='passed',family_cells=len(a['family']),computation_groups=len(a['computation']),omission_groups=len(a['sensitivity']),corrected_replays=len(c['records']),primary_records_unchanged=True,scope='Raw-record reconciliation of added tables, omission effects and realized compensation settings; not physical validation')
(B/'qa/extended_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
