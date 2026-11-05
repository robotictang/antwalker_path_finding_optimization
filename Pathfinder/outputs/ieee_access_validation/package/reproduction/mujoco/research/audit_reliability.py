"""Reconcile a completed reliability study without changing its measurements."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from research.reliability import DIRECTORY,digest,selection_key,paired_report
from research.run import OUT,atomic_json
from research.swarm import quality

def audit(directory=DIRECTORY):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    lock=json.loads((directory/'locked_parameters.json').read_text());sha=digest(manifest)
    assert sha==lock['manifest_sha256']
    dev={c['id'] for c in manifest['cases'] if c['split']=='development'}
    test={c['id'] for c in manifest['cases'] if c['split']=='heldout'}
    assert len(dev)==4 and len(test)==12 and dev.isdisjoint(test)
    seeds=[c['seed'] for c in manifest['cases']];assert len(set(seeds))==16
    hazards={tuple(c['hazard_position']) for c in manifest['cases']};assert len(hazards)==16
    phases={name:json.loads((directory/(name+'.json')).read_text()) for name in ['development_default','development_alternative','heldout_planning','heldout_physics']}
    expected_counts=dict(development_default=24,development_alternative=24,heldout_planning=108,heldout_physics=12)
    reports=[];source_sets=[]
    for name,r in phases.items():
        assert r['state']=='complete'
        assert len(r['records'])==expected_counts[name]
        assert len({(x['case_id'],x['method'],x['repeat']) for x in r['records']})==len(r['records'])
        assert r['study']['manifest_sha256']==sha
        if name.startswith('heldout'):assert r['study']['parameter_sha256']==lock['sha256']
        source_sets.append(r['source_sha256'])
        for f,h in r['source_sha256'].items():
            archived=OUT/r['source_snapshot']/f
            assert hashlib.sha256(archived.read_bytes()).hexdigest()==h
        for x in r['records']:
            assert x['status']!='error',x.get('error')
            case=next(c for c in r['cases'] if c['id']==x['case_id'])
            pl=x.get('plan',{});metrics=pl.get('metrics')
            if metrics is not None:
                required=1.25*(metrics['energy_percent']+case['return_energy_percent'])+6
                assert abs(required-pl['required_battery_percent'])<1e-8
                assert abs(quality(metrics)-pl['quality_score'])<1e-9
                assert pl['admissible']==(required<=case['battery_percent']+1e-8 and metrics['estimated_seconds']<=case['deadline_s']+1e-8 and metrics['terrain_exposure']<=case['risk_budget']+1e-8)
            optimizer=pl.get('optimizer')
            if optimizer:
                assert optimizer['parameters']==r['study']['parameters'][x['method']]
                assert optimizer['seed']==x['seed']
                assert optimizer['fitness_evaluations']<=240
            if x.get('execution'):
                ex=x['execution'];assert ex['physics_samples']>0
                assert ex['positive_actuator_work_j']>=ex['positive_leg_work_j']>=0
                expected=ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=case['deadline_s'] and ex['minimum_battery_percent']>=2.
                assert x['success']==bool(expected)
        with (OUT/(r['run_id']+'.csv')).open() as f:assert len(list(csv.DictReader(f)))==len(r['records'])
        reports.append(dict(phase=name,run_id=r['run_id'],attempts=len(r['records']),executed=sum(bool(x.get('execution')) for x in r['records']),
          statuses=dict(Counter(x['status'] for x in r['records'])),
          repeated_route_signatures_across_attempts=len(r['records'])-len({json.dumps(x.get('plan',{}).get('points')) for x in r['records']})))
    assert all(s==source_sets[0] for s in source_sets),'Algorithms changed between tuning and evaluation'
    chosen={method:min(manifest['profiles'],key=lambda p:(selection_key(phases['development_'+p],method),p!='default')) for method in lock['chosen']}
    assert chosen==lock['chosen']
    planning=phases['heldout_planning'];maps=[digest(c['map']) for c in planning['cases']]
    assert len(set(maps))==12
    comparison=json.loads((directory/'comparison.json').read_text());assert paired_report(planning)==comparison
    result=dict(state='passed',attempts=sum(x['attempts'] for x in reports),phases=reports,unique_manifest_seeds=16,
      distinct_heldout_navigation_maps=12,parameter_selection_recomputed=True,unchanged_algorithm_sources=True,
      archived_source_hashes_verified=True,trial_keys_unique=True,csv_counts_reconciled=True,
      caveat='Different sampled obstacle/task layouts share one terrain. Repeated routes and deterministic ties are retained; duplicate trial keys are forbidden.')
    atomic_json(directory/'audit.json',result);return result

if __name__=='__main__':print(json.dumps(audit(),indent=2))
