"""Independent analysis of the frozen reliability study, without rerunning planners."""
import argparse,csv,hashlib,json,statistics
from collections import Counter
from pathlib import Path
import numpy as np

METHODS=['pso','aco','proposed']
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(study,out):
    study=Path(study);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    paths={k:study/(k+'.json') for k in ['development_default','development_alternative','heldout_planning','heldout_physics']}
    runs={k:load(p) for k,p in paths.items()};manifest=load(study/'manifest.json');locked=load(study/'locked_parameters.json')
    results=Path(study).parent
    source_sets=[];checks=[];trial_rows=[]
    for phase,r in runs.items():
        assert r['state']=='complete'
        assert len(r['records'])==len(r['cases'])*len(r['methods'])*r['repeats']
        keys=[(x['case_id'],x['method'],x['repeat']) for x in r['records']];assert len(set(keys))==len(keys)
        source_sets.append(r['source_sha256'])
        for f,h in r['source_sha256'].items():assert sha(results/r['source_snapshot']/f)==h
        counts=Counter(x['status'] for x in r['records'])
        checks.append(dict(phase=phase,run_id=r['run_id'],attempts=len(keys),statuses=dict(counts),file_sha256=sha(paths[phase])))
        cases={c['id']:c for c in r['cases']}
        for x in r['records']:
            assert x['status']!='error',x.get('error')
            c=cases[x['case_id']];p=x.get('plan',{});m=p.get('metrics');e=x.get('execution',{})
            if m:
                q=m['distance_m']/50+m['estimated_seconds']/90+m['energy_percent']/30+m['terrain_exposure']/80
                need=1.25*(m['energy_percent']+c['return_energy_percent'])+6
                assert abs(q-p['quality_score'])<1e-10 and abs(need-p['required_battery_percent'])<1e-8
                admitted=need<=c['battery_percent']+1e-8 and m['estimated_seconds']<=c['deadline_s']+1e-8 and m['terrain_exposure']<=c['risk_budget']+1e-8
                assert admitted==bool(p['admissible'])
            if e:
                success=e['success'] and e['task_time_s'] is not None and e['task_time_s']<=c['deadline_s'] and e['minimum_battery_percent']>=2
                assert bool(success)==x['success']
            trial_rows.append(dict(phase=phase,case=x['case_id'],method=x['method'],repeat=x['repeat'],seed=x['seed'],status=x['status'],
              admissible=bool(p.get('admissible')),score=p.get('quality_score'),planning_s=p.get('planning_seconds'),
              predicted_s=m.get('estimated_seconds') if m else None,required_battery=p.get('required_battery_percent'),
              measured_task_s=e.get('task_time_s'),mission_work_j=e.get('positive_actuator_work_j')))
    assert all(x==source_sets[0] for x in source_sets)
    plan=runs['heldout_planning'];cases={c['id']:c for c in plan['cases']};paired=[];layout_deltas=[];summary=[]
    for method in METHODS:
        group=[x for x in plan['records'] if x['method']==method];good=[x for x in group if x['plan'].get('admissible')]
        reasons=Counter()
        for x in group:
            p=x['plan'];m=p.get('metrics');c=cases[x['case_id']]
            if not m:reasons['no_route_returned']+=1
            elif not p['admissible']:
                if p['required_battery_percent']>c['battery_percent']+1e-8:reasons['battery']+=1
                if m['estimated_seconds']>c['deadline_s']+1e-8:reasons['deadline']+=1
                if m['terrain_exposure']>c['risk_budget']+1e-8:reasons['terrain']+=1
        scores=[x['plan']['quality_score'] for x in good]
        planning=[x['plan']['planning_seconds'] for x in group]
        summary.append(dict(method=method,n=len(group),admitted=len(good),counts=dict(Counter(x['status'] for x in group)),
          mean_score=statistics.mean(scores),mean_planning_s=statistics.mean(planning),median_planning_s=statistics.median(planning),
          max_planning_s=max(planning),rejection_reasons=dict(reasons)))
    index={(x['case_id'],x['repeat'],x['method']):x for x in plan['records']}
    for baseline in ['pso','aco']:
        count=Counter();localmeans=[]
        for case in cases:
            deltas=[]
            for rep in range(plan['repeats']):
                a=index[case,rep,'proposed']['plan'];b=index[case,rep,baseline]['plan']
                fa=bool(a.get('admissible'));fb=bool(b.get('admissible'))
                if fa and fb:
                    d=b['quality_score']-a['quality_score'];deltas.append(d)
                    count['ties' if abs(d)<=1e-8 else 'wins' if d>0 else 'losses']+=1
                else:count['proposed_only' if fa else 'baseline_only' if fb else 'neither_admitted']+=1
            if deltas:
                localmeans.append(statistics.mean(deltas));layout_deltas.append(dict(baseline=baseline,case=case,delta=statistics.mean(deltas),n_seeds=len(deltas)))
        rng=np.random.default_rng(4100);boot=rng.choice(localmeans,(5000,len(localmeans)),replace=True).mean(axis=1)
        paired.append(dict(baseline=baseline,counts=dict(count),n_jointly_admitted=count['wins']+count['ties']+count['losses'],
          n_layouts=len(localmeans),mean_delta=statistics.mean(localmeans),ci95=np.quantile(boot,[.025,.975]).tolist()))
    physical=runs['heldout_physics'];executed=[x for x in physical['records'] if x.get('execution')]
    route_hashes=[hashlib.sha256(json.dumps(x['plan']['points'],sort_keys=True).encode()).hexdigest() for x in executed]
    assert len(set(route_hashes))==1
    output=dict(primary_study=checks,planning_summary=summary,paired=paired,layout_deltas=layout_deltas,
      physics=dict(attempts=len(physical['records']),executed=len(executed),successes=sum(x['success'] for x in physical['records']),
        distinct_executed_cases=len({x['case_id'] for x in executed}),same_route=True,
        example=executed[0]['execution']),
      preparation=dict(mean_s=statistics.mean(c['preparation_seconds'] for c in cases.values()),min_s=min(c['preparation_seconds'] for c in cases.values()),max_s=max(c['preparation_seconds'] for c in cases.values())),
      versions=plan['versions'],frozen_choices=locked['chosen'],manifest_sha256=sha(study/'manifest.json'),
      note='Raw manifest file SHA differs from the study canonical-JSON SHA; both identities are retained. Seeds within a layout are repeated trials, not new worlds.')
    (out/'verified_analysis.json').write_text(json.dumps(output,indent=2))
    with (out/'all_168_trials.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(trial_rows[0]));w.writeheader();w.writerows(trial_rows)
    print(json.dumps({k:output[k] for k in ['planning_summary','paired','preparation','frozen_choices']},indent=2))
    return output
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--study',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.study,a.out)
