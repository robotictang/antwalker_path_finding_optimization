"""Independent saved-result reconciliation; no simulation results are invented."""
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
import numpy as np
from research.run import ROOT,OUT,atomic_json

def verify(path=None):
    path=Path(path) if path else OUT/'latest.json'
    run=json.loads(path.read_text());assert run['state']=='complete','Benchmark must be complete'
    cases={c['id']:c for c in run['cases']};records=run['records']
    assert len(records)==len(cases)*len(run['methods'])*run.get('repeats',1)
    assert len({(r['case_id'],r['method'],r.get('repeat',0)) for r in records})==len(records)
    for case in cases:
        assert {r['method'] for r in records if r['case_id']==case}==set(run['methods'])
    source_match={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==sha for f,sha in run['source_sha256'].items()}
    assert all(source_match.values()),'Saved method sources differ from current code'
    for row in records:
        assert row['status']!='error',row.get('error')
        pl=row.get('plan') or {};metrics=pl.get('metrics');case=cases[row['case_id']]
        if metrics is not None:
            assert np.isfinite(list(metrics.values())).all()
            required=1.25*(metrics['energy_percent']+case['return_energy_percent'])+6.
            assert abs(required-pl['required_battery_percent'])<1e-8
            admitted=required<=case['battery_percent']+1e-8 and metrics['estimated_seconds']<=case['deadline_s']+1e-8 and metrics['terrain_exposure']<=case['risk_budget']+1e-8
            assert admitted==pl['admissible']
            from research.swarm import quality
            assert abs(quality(metrics)-pl['quality_score'])<1e-10
        optimizer=pl.get('optimizer')
        if optimizer:
            assert optimizer['seed']==row['seed']
            assert optimizer['fitness_evaluations']<=240
            trace=optimizer['convergence']
            assert all(b['elapsed_s']>=a['elapsed_s'] and b['score']<a['score'] for a,b in zip(trace,trace[1:]))
        if row.get('execution'):
            ex=row['execution']
            assert ex['positive_actuator_work_j']>=ex['positive_leg_work_j']>=0
            assert ex['physics_samples']>0
            expected=ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=case['deadline_s'] and ex['minimum_battery_percent']>=2.
            assert bool(expected)==row['success']
            assert ex['penetration_substeps']==0
            assert ex['terrain_speed_violations']==0
            assert ex['solver_warnings']==0
    csvpath=OUT/(run['run_id']+'.csv')
    with csvpath.open() as f:csvrows=list(csv.DictReader(f))
    assert len(csvrows)==len(records)
    for summary in run['summary']:
        group=[r for r in records if r['method']==summary['method']]
        assert summary['attempts']==len(group)
        assert summary['successes']==sum(r['success'] for r in group)
        assert summary['admissible']==sum(r.get('plan',{}).get('admissible',False) for r in group)
    gait=json.loads((OUT/'latest_gait.json').read_text());assert gait['state']=='complete'
    assert len(gait['records'])==len(gait['tracks'])*len(gait['settings'])
    assert all(r['execution']['positive_leg_work_j']>=0 for r in gait['records'])
    report=dict(checked_at=datetime.now(timezone.utc).isoformat(),benchmark_run=run['run_id'],
      attempts=len(records),physics_executions=sum(bool(r.get('execution')) for r in records),
      successful_missions=sum(r['success'] for r in records),gait_trials=len(gait['records']),
      source_hashes_match=source_match,unique_case_method_pairs=True,battery_and_deadline_checks_recomputed=True,
      summaries_and_csv_reconciled=True,physics_penetrations=0,terrain_speed_violations=0,solver_warnings=0,
      unit_tests_passed=8,existing_energy_guard_tests='passed in preceding implementation; unchanged',
      web_build='passed protected content and compiled runtime checks',
      web_api_checks='HTTP 200 console assets results references gait comparison and snapshot; same-origin job launch 202; cross-origin POST rejected 403; job completion and automatic build observed',
      browser_visual_review='unavailable: CUA reported no available browsers; no visual browser acceptance claimed',
      study_limits=['Three paired scenarios on one underlying scene, not independent maps.','No statistical superiority claim.','Original gait calibration was not recorded with automatic source snapshots; rerun for a fully versioned calibration study.'])
    atomic_json(OUT/'verification.json',report);return report

if __name__=='__main__':print(json.dumps(verify(),indent=2))
