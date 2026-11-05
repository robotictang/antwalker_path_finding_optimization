"""Convert one saved run into a source-backed comparison dashboard snapshot."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import os
import shutil
from research.run import ROOT,OUT,atomic_json

PROJECT=ROOT/'research_dashboard'
_plugins=list((Path.home()/'.codex/plugins/cache/openai-curated-remote/data-analytics').glob('*/scripts/data-app.mjs'))
DATA_PLUGIN=Path(os.environ['HEXAPOD_DATA_PLUGIN']) if os.environ.get('HEXAPOD_DATA_PLUGIN') else max(_plugins,key=lambda p:p.stat().st_mtime).parents[1] if _plugins else Path('unavailable-data-plugin')
_runtime_node=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
NODE=Path(os.environ.get('HEXAPOD_NODE') or (_runtime_node if _runtime_node.exists() else shutil.which('node') or 'node'))

def export(run_path=None,build=False):
    path=Path(run_path) if run_path else OUT/'latest.json'
    result=json.loads(path.read_text());rows=[];convergence=[]
    cases={c['id']:c for c in result['cases']}
    focal=result.get('study',{}).get('focal_method','proposed_v4' if 'proposed_v4' in result['methods'] else 'proposed')
    for r in result['records']:
        pl=r.get('plan') or {};m=pl.get('metrics') or {};ex=r.get('execution') or {};case=cases[r['case_id']]
        optimizer=pl.get('optimizer') or {}
        reasons=[]
        if not pl.get('admissible'):
            if m:
                if (pl.get('required_battery_percent') or 0)>case['battery_percent']+1e-8:reasons.append('Battery + return reserve')
                if m['estimated_seconds']>case['deadline_s']+1e-8:reasons.append('Deadline')
                if m['terrain_exposure']>case['risk_budget']+1e-8:reasons.append('Terrain exposure limit')
            else:reasons.append('No common safe return route was found' if r['status']=='no_return_route' else 'No route returned within search limits')
        elif result['execute'] and not r.get('success'):reasons.append(r['status'])
        rows.append(dict(case=r['case_id'],method=r['method'],methodLabel=pl.get('label',r['method']),
          repetition=r.get('repeat',0)+1,seed=r.get('seed'),world_family=case.get('world',{}).get('family','original'),world_sha256=case.get('world_sha256'),split=case.get('split','exploratory'),
          resumed_seed=optimizer.get('resumed_seed'),distance_fallback=optimizer.get('distance_fallback'),seed_policy=optimizer.get('seed_policy'),
          task_time_error_s=r.get('prediction_validation',{}).get('task_time_error_s'),task_battery_error_pp=r.get('prediction_validation',{}).get('task_battery_error_pp'),
          status=r['status'],reason='; '.join(reasons) or 'Meets planning limits',admissible=bool(pl.get('admissible')),success=bool(r.get('success')) if result['execute'] else None,
          executed=bool(ex),deadline_s=case['deadline_s'],battery_percent=case['battery_percent'],
          required_battery_percent=pl.get('required_battery_percent'),
          predicted_distance_m=m.get('distance_m'),predicted_time_s=m.get('estimated_seconds'),
          predicted_energy_percent=m.get('energy_percent'),terrain_exposure=m.get('terrain_exposure'),
          planning_time_s=pl.get('planning_seconds'),expanded=pl.get('expanded'),
          continuous_moves=optimizer.get('continuous_moves'),roadmap_nodes=optimizer.get('roadmap_nodes'),roadmap_edges=optimizer.get('roadmap_edges'),
          quality_score=pl.get('quality_score'),fitness_evaluations=optimizer.get('fitness_evaluations'),
          task_time_s=ex.get('task_time_s'),mission_work_j=ex.get('positive_actuator_work_j'),
          mission_energy_percent=ex.get('energy_consumed_percent'),max_tilt_deg=ex.get('max_tilt_deg'),
          mean_slip_mps=ex.get('mean_contact_slip_mps'),support_margin_m=ex.get('min_support_margin_m'),
          charging_stops=ex.get('charging_stops'),modeled_swaps=ex.get('modeled_swap_events'),
          route_json=json.dumps(pl.get('points',[])),trace_json=json.dumps(ex.get('trace',[]))))
        for item in optimizer.get('convergence',[]):
            convergence.append(dict(case=r['case_id'],method=r['method'],methodLabel=pl.get('label',r['method']),
              repetition=r.get('repeat',0)+1,seed=r.get('seed'),elapsed_s=item['elapsed_s'],quality_score=item['score']))
    source=dict(label='Executed local MuJoCo research trials' if result['execute'] else 'Local planning-only research trials',files=[path.name],
      evidenceFlow=[dict(title='Reproduce experiment',detail=f"From mujoco run python3 -m research.run --suite {result['suite']} "+('--execute ' if result['execute'] else '')+('--hybrid ' if result['locomotion']=='hybrid' else '')+f"--planning-seconds {result['planning_budget_s']} --resolution {result['resolution_m']} --service {result.get('service','charge')} --service-seconds {result.get('service_seconds',8)} --repeats {result.get('repeats',1)} --methods "+' '.join(result['methods'])),
                    dict(title='Code version',detail=json.dumps(result['source_sha256'],sort_keys=True)),
                    dict(title='Measurement scope',detail=result.get('study',{}).get('scope','Paired cases; one underlying scene; no independent repeated-map uncertainty estimate.')+' Predictions and physics measurements remain separate.')],
      caveats=result['caveats'],metricDefinitions=[
        dict(label='Mission success',definition='Destination reached by deadline and return to a station completed without a battery guard or execution failure. Denominator includes all attempts, including rejected plans.'),
        dict(label='Mechanical work',definition='Integral of positive actuator force times actuator velocity at every physics substep for the destination and return route. Joules; not electrical battery energy.'),
        dict(label='Terrain exposure',definition='Path length integrated against normalized footprint-window geometric features and assumed semantic softness. Difficulty proxy; not fall probability.'),
        dict(label='Planning time',definition='Per-method wall time on this machine, excluding shared graph and lower-bound preprocessing. Methods share the same declared time and expansion budgets.')])
    source['metricDefinitions'].extend([
        dict(label='Common route quality',definition='distance/50 + time/90 + modeled battery percentage points/30 + 0.25*terrain exposure/20. Lower is better among feasible routes. New PSO ACO and proposal use this same preference.'),
        dict(label='Repeated trials',definition='Each method receives the same case and seed in each repetition. Repetitions share an underlying map and are not independent maps.'),
        dict(label='Prediction residuals',definition='Executed destination time or modeled battery use minus its planned prediction. Positive means underprediction. Simulation consistency only; no external electrical calibration.'),
        dict(label='Search progress',definition='Observed best feasible score improvements by elapsed wall time, including charged A* initialization. No interpolation or manufactured intermediate iterations.')])
    if any(c.get('world') for c in result['cases']) and not result.get('study'):
        source['evidenceFlow'][0]['detail']+=' --world-seed '+str(result['cases'][0]['world']['seed'])
        source['evidenceFlow'][2]['detail']='Independently generated procedural worlds from a restricted simulation distribution. Predictions and physics measurements remain separate.'
    if result.get('study'):
        source['evidenceFlow'][0]['detail']=result['study']['reproduction']
        source['evidenceFlow'].append(dict(title='Frozen study parameters',detail=json.dumps(result['study'],sort_keys=True)))
    old={}
    if (PROJECT/'src/data.json').exists():old=json.loads((PROJECT/'src/data.json').read_text())
    snapshot=dict(id=old.get('id','hexapod-research-comparison-2026'),surface='dashboard',title='Hexapod method comparison',
      generatedAt=datetime.now(timezone.utc).isoformat(),buildStatus='complete',status='observed',
      filters=[],exportPreferences=dict(selected=None,destinations=[]),
      queries=dict(trials=dict(rows=rows,payloadColumns=['route_json','trace_json'],source=source),
        cases=dict(rows=[dict(case=c['id'],world_family=c.get('world',{}).get('family','original'),map_json=json.dumps(c.get('map',{}))) for c in result['cases']],payloadColumns=['map_json'],source=source),
        convergence=dict(rows=convergence,source=source)),
      research=dict(run_id=result['run_id'],suite=result['suite'],state=result['state'],execute=result['execute'],
        focal_method=focal,locomotion=result['locomotion'],resolution_m=result['resolution_m'],methods=result['methods'],repeats=result.get('repeats',1),algorithm_version=result.get('algorithm_version'),energy_model=result.get('energy_model'),independent_worlds=len({c['world_sha256'] for c in result['cases'] if c.get('world_sha256')}),caveats=result['caveats']))
    if result.get('study'):
        snapshot['research']['study']=result['study']
        snapshot['research']['layout_count']=len(result['cases'])
        if result['study'].get('version') in (3,4) and focal in result['methods'] and result['state']=='complete':
            if result['study']['version']==4:
                from research.advanced_study import comparison
            else:
                from research.strong_study import comparison
            report=comparison(result)
            if report.get('case_verdicts'):snapshot['queries']['case_verdicts']=dict(rows=report['case_verdicts'],source={**source,'caveats':source['caveats']+['Per repetition verdict compares only admissible balanced scores in this selected run; an admitted-score winner does not imply best runtime or every physical metric.']})
            for row in report['comparisons']:
                interval=row.get('admission_advantage_95_pp')
                row['admission_ci_display']=('['+', '.join(f'{v:.2f}' for v in interval)+']') if interval else 'Unavailable'
                interval=row.get('descriptive_layout_bootstrap_95_percent')
                row['quality_ci_display']=('['+', '.join(f'{v:.6f}' for v in interval)+']') if interval else 'Unavailable'
            snapshot['queries']['paired_comparison']=dict(rows=report['comparisons'],source={**source,'caveats':source['caveats']+[report['interpretation']]})
        elif result['study']['phase']=='heldout_planning':
            from research.reliability import paired_report
            report=paired_report(result)
            snapshot['queries']['paired_comparison']=dict(rows=report['comparisons'],source={**source,'caveats':source['caveats']+[report['interpretation']]})
    if focal in result['methods']:
        index={(r['case'],r['repetition'],r['method']):r for r in rows};paired=[]
        for row in rows:
            if row['method']==focal:continue
            proposed=index.get((row['case'],row['repetition'],focal))
            if proposed and proposed['admissible'] and row['admissible']:
                delta=row['quality_score']-proposed['quality_score']
                paired.append(dict(case=row['case'],world_family=row['world_family'],repetition=row['repetition'],baseline=row['method'],baselineLabel=row['methodLabel'],score_advantage=delta,
                  score_improvement_percent=100*delta/row['quality_score'] if row['quality_score'] else None,
                  outcome='tie' if abs(delta)<=1e-8 else 'proposed win' if delta>0 else 'baseline win'))
        snapshot['queries']['paired_deltas']=dict(rows=paired,source={**source,'caveats':source['caveats']+['Relative score improvement is 100 × (baseline score − proposed score) / baseline score on jointly admitted paired attempts. Score is a declared composite preference, not a measured percentage energy saving.']})
    gait_path=OUT/'latest_gait.json'
    if gait_path.exists():
        gait=json.loads(gait_path.read_text());comparison=[]
        for grade in (0,1,2):
            group=[r for r in gait['records'] if r['grade']==grade]
            default=next((r for r in group if r['is_default']),None)
            valid=[r for r in group if r['eligible'] and r['leg_work_per_m_j'] is not None]
            best=min(valid,key=lambda r:r['leg_work_per_m_j']) if valid else None
            comparison.append(dict(terrain=['Smooth','Mild uneven','More uneven'][grade],
              default_work_j_m=default['leg_work_per_m_j'] if default else None,
              selected_work_j_m=best['leg_work_per_m_j'] if best else None,
              trials=len(group),selected_period_s=best['gait']['period'] if best else None,selected_duty=best['gait']['duty'] if best else None))
        snapshot['queries']['gait_comparison']=dict(rows=comparison,source=dict(label='Matched gait calibration measurements',files=[gait['run_id']+'.json'],
          caveats=gait['caveats'],evidenceFlow=[dict(title='Reproduce',detail='From mujoco run python3 -m research.gait_sweep. Nine timing settings plus original gait on three straight tracks.')],
          metricDefinitions=[dict(label='Leg work per metre',definition='Positive leg actuator mechanical work divided by actual traveled distance in the calibration trial. Best eligible setting is selected on the same calibration tracks; no held-out validation claim.')]))
    path=OUT/'dashboard_snapshot.json';atomic_json(path,snapshot)
    if (PROJECT/'src').exists():atomic_json(PROJECT/'src/data.json',snapshot)
    if build:
        subprocess.run([str(NODE),str(DATA_PLUGIN/'scripts/data-app.mjs'),'build','--project-dir',str(PROJECT),'--separate-data'],check=True)
    return snapshot

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run');p.add_argument('--build',action='store_true');a=p.parse_args();export(a.run,a.build)
