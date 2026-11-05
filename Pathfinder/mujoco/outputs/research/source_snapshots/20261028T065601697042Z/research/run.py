"""CLI and durable result writer for paired baseline/proposed experiments."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import time
import traceback
import platform
import scipy
from contextlib import contextmanager
import fcntl
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from multi_place_config import DEST_BASE,MISSION_TARGETS,CHARGING_STATIONS
from research.planning import SceneGraph,Limits,METHODS,plan,scalar_search
from research.execution import execute

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/research'

@contextmanager
def experiment_lock():
    OUT.mkdir(exist_ok=True,parents=True)
    with (OUT/'experiment.lock').open('w') as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another research experiment is running; wait for it to finish')
        try:yield
        finally:fcntl.flock(handle,fcntl.LOCK_UN)

def atomic_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2,allow_nan=False));os.replace(tmp,path)

def model_for_case(seed=0,variant=0,hazard_position=None):
    m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'))
    if hazard_position is not None:
        m.body_pos[m.body('roadwork_obstacle').id]=hazard_position
    elif variant:
        # A real physical existing mocap hazard is moved, never an invisible cost.
        body=m.body('roadwork_obstacle').id
        positions=[[-2.,-26.,0.],[25.,-21.,0.],[-30.,2.,0.]]
        m.body_pos[body]=positions[(variant-1)%len(positions)]
    return m

def return_route(graph,start,stations=None):
    choices=[]
    for station in (CHARGING_STATIONS if stations is None else stations):
        points=[np.asarray(start,float)]
        try:
            for target in [*station['via'],station['pos']]:
                if np.linalg.norm(points[-1]-target)<1e-7:continue
                goal=graph.node(target);graph.bounds(goal)
                route,_,status=scalar_search(graph,points[-1],target,[0,0,1,0],math.pi/2,time.perf_counter()+10,200000)
                if route is None:raise RuntimeError(status)
                points.extend(route[1:])
            metrics=graph.metrics(points)
            choices.append(dict(station=station['name'],key=station['key'],energy=metrics['energy_percent'],points=[p.tolist() for p in points],metrics=metrics))
        except (ValueError,RuntimeError):continue
    if not choices:return None
    return min(choices,key=lambda c:c['energy'])

def scenarios(suite,world_seed=1050000):
    if suite in ('procedural4','procedural12'):
        from research.worlds import sample_cases
        return sample_cases(4 if suite=='procedural4' else 12,world_seed)
    if suite=='smoke':return [dict(id='smoke',goal=[0.,-24.],deadline_s=40.,battery_percent=100.,risk_budget=20.,variant=0,seed=101,energy_multiplier=1.)]
    if suite=='pilot':
        return [dict(id='quarry_nominal',goal=MISSION_TARGETS[1]['pos'].tolist(),deadline_s=180.,battery_percent=100.,risk_budget=40.,variant=0,seed=101,energy_multiplier=1.),
          dict(id='marsh_tight',goal=MISSION_TARGETS[2]['pos'].tolist(),deadline_s=100.,battery_percent=65.,risk_budget=12.,variant=0,seed=102,energy_multiplier=1.),
          dict(id='river_obstructed',goal=MISSION_TARGETS[4]['pos'].tolist(),deadline_s=240.,battery_percent=100.,risk_budget=35.,variant=1,seed=103,energy_multiplier=1.12)]
    result=[]
    for i,target in enumerate(MISSION_TARGETS):
        for variant in range(3):
            result.append(dict(id=f'site{i+1}_variant{variant}',goal=target['pos'].tolist(),deadline_s=210. if variant!=1 else 125.,battery_percent=100. if variant!=2 else 70.,risk_budget=40. if variant!=1 else 15.,variant=variant,seed=1000+i*10+variant,energy_multiplier=[1.,1.12,.9][variant]))
    return result

def flat_rows(result):
    rows=[]
    for row in result['records']:
        metrics=row.get('plan',{}).get('metrics') or {};ex=row.get('execution') or {}
        rows.append(dict(case=row['case_id'],method=row['method'],repeat=row.get('repeat',0),seed=row.get('seed'),status=row['status'],
          admissible=row.get('plan',{}).get('admissible',False),success=row.get('success',False),
          planning_seconds=row.get('plan',{}).get('planning_seconds'),
          quality_score=row.get('plan',{}).get('quality_score'),
          fitness_evaluations=row.get('plan',{}).get('optimizer',{}).get('fitness_evaluations'),
          distance_m=metrics.get('distance_m'),predicted_seconds=metrics.get('estimated_seconds'),
          predicted_energy_percent=metrics.get('energy_percent'),terrain_exposure=metrics.get('terrain_exposure'),
          measured_task_seconds=ex.get('task_time_s'),positive_actuator_work_j=ex.get('positive_actuator_work_j'),
          max_tilt_deg=ex.get('max_tilt_deg'),charging_stops=ex.get('charging_stops'),modeled_swap_events=ex.get('modeled_swap_events')))
    return rows

def summarize(result):
    summary=[]
    for method in result['methods']:
        rows=[r for r in result['records'] if r['method']==method]
        admissible=[r for r in rows if r.get('plan',{}).get('admissible')]
        executed=[r for r in rows if r.get('execution')]
        successful=[r for r in rows if r.get('success')]
        def avg(key,physical=False):
            vals=[(r.get('execution') or {}).get(key) if physical else (r.get('plan',{}).get('metrics') or {}).get(key) for r in (successful if physical else admissible)]
            vals=[v for v in vals if v is not None]
            return float(np.mean(vals)) if vals else None
        summary.append(dict(method=method,label=METHODS[method],attempts=len(rows),admissible=len(admissible),executed=len(executed),successes=len(successful),
          success_rate=len(successful)/len(rows) if rows and result['execute'] else None,
          admissible_rate=len(admissible)/len(rows) if rows else None,
          mean_predicted_time_s=avg('estimated_seconds'),mean_predicted_energy_percent=avg('energy_percent'),
          mean_task_time_s=avg('task_time_s',True),mean_positive_work_j=avg('positive_actuator_work_j',True),
          mean_max_tilt_deg=avg('max_tilt_deg',True),
          mean_quality_score=float(np.mean([r['plan']['quality_score'] for r in admissible])) if admissible else None,
          mean_planning_seconds=float(np.mean([r['plan']['planning_seconds'] for r in rows if r.get('plan',{}).get('planning_seconds') is not None])) if any(r.get('plan',{}).get('planning_seconds') is not None for r in rows) else None))
    return summary

def save_result(result,path):
    result['summary']=summarize(result);atomic_json(path,result)
    atomic_json(OUT/'latest.json',result)
    rows=flat_rows(result)
    if rows:
        csvpath=Path(path).with_suffix('.csv')
        with csvpath.open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def _run_suite(suite='pilot',execute_physics=True,methods=None,planning_seconds=2.,resolution=.25,walking_only=True,run_id=None,service='charge',service_seconds=8.,progress=None,repeats=1,cases_override=None,study=None,energy_profile=None,world_seed=1050000):
    methods=methods or list(METHODS)
    if any(m not in METHODS for m in methods):raise ValueError('Unknown method')
    if energy_profile and not walking_only:raise ValueError('An externally fitted walking profile cannot be applied to wheel mode')
    if not .25<=resolution<=2.:raise ValueError('Resolution must be 0.25..2 m')
    if not .1<=planning_seconds<=30.:raise ValueError('Planning budget must be 0.1..30 seconds')
    if not isinstance(repeats,int) or not 1<=repeats<=30:raise ValueError('Repetitions must be 1..30')
    OUT.mkdir(exist_ok=True,parents=True)
    run_id=run_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=OUT/f'{run_id}.json'
    cases=json.loads(json.dumps(cases_override)) if cases_override is not None else scenarios(suite,world_seed)
    files=['research/planning.py','research/swarm.py','research/execution.py','research/telemetry.py','research/run.py','research/reliability.py','research/worlds.py','research/strong_study.py','research/calibration.py','research/reference_validation.py','tripod_gait.py','hybrid_locomotion.py','safe_navigation.py','energy_model.py','terrain_profile.py','terrain_classes.py','road_demo.py','multi_place_config.py','hybrid_hexapod_multi_place.xml']
    files=[f for f in files if (ROOT/f).exists()]
    archived=OUT/'source_snapshots'/run_id
    for filename in files:
        dest=archived/filename;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/filename).read_bytes())
    result=dict(schema_version=3,algorithm_version='adaptive_corridor_v3',run_id=run_id,created_at=datetime.now(timezone.utc).isoformat(),state='running',suite=suite,execute=execute_physics,
      methods=methods,repeats=repeats,records=[],cases=cases,locomotion='walking_only' if walking_only else 'hybrid',resolution_m=resolution,
      planning_budget_s=planning_seconds,service=service,service_seconds=service_seconds,
      versions=dict(mujoco=mujoco.__version__,numpy=np.__version__,scipy=scipy.__version__,python=platform.python_version()),
      hardware=dict(platform=platform.platform(),cpu_count=os.cpu_count(),cpu_model=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),platform.processor())),
      source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},source_snapshot=f'source_snapshots/{run_id}',
      caveats=['Assisted chassis velocity and posture; gravity compensation enabled.','Positive actuator work is mechanical work, not electrical battery energy.',
       'Terrain exposure is a geometric and semantic difficulty proxy, not fall probability.',
       'Controlled research graph and inspired baselines; not exact reproductions of the cited papers.',
       'Pilot cases share one underlying scene; no broad generalization or statistical significance claim.',
       'Cost averages condition on admissibility or success; compare denominators and paired cases.',
       'Return route estimates use a common reference heading and the configured reserve allowance.'])
    if any(c.get('world') for c in cases):
        result['caveats']=[c for c in result['caveats'] if not c.startswith('Pilot cases')]
        result['caveats'].append('Procedurally generated physical worlds from a restricted simulated distribution; not real-world generalization.')
    if study:
        result['study']=study
        result['caveats']=[c for c in result['caveats'] if not c.startswith('Pilot cases')]
        result['caveats'].append(study.get('scope','Sampled tasks share one scene.'))
    result['caveats'].extend(['PSO and ACO are A* seeded waypoint refiners, not unseeded global planners.',
      'All new optimizers share the same feasible-first composite quality and continuous collision checks.',
      'Seed search, visibility checks and fitness evaluations count toward each method wall budget; operation counts are different primitive types.',
      'Repeated stochastic seeds share a scene; they are not independent test maps.'])
    from research.calibration import COEFFICIENTS
    import energy_model as em
    result['energy_model']=dict(status='externally_fitted' if energy_profile else 'uncalibrated_nominal_simulation',profile=energy_profile,coefficients={k:getattr(em,k) for k in COEFFICIENTS})
    save_result(result,path)
    try:
        for case_index,case in enumerate(cases):
            from research.worlds import terrain_context
            with terrain_context(case.get('world')):
                model_start=time.perf_counter()
                if case.get('world'):
                    from research.worlds import world_model,identity
                    xml_path=OUT/'world_models'/run_id/(case['id']+'.xml')
                    model=world_model(case['world'],xml_path)
                    case['world_sha256']=identity(case['world']);case['model_xml']=str(xml_path.relative_to(OUT))
                    case['model_xml_sha256']=hashlib.sha256(xml_path.read_bytes()).hexdigest()
                else:model=model_for_case(case['seed'],case['variant'],case.get('hazard_position'))
                data=mujoco.MjData(model);mujoco.mj_forward(model,data)
                case['model_load_seconds']=time.perf_counter()-model_start
                graph_start=time.perf_counter()
                nav=SafeNavigator(model,data,resolution=resolution)
                graph=SceneGraph(nav,walking_only)
                case['graph_build_seconds']=time.perf_counter()-graph_start
                begin=time.perf_counter();escape=return_route(graph,case['goal'],case.get('world',{}).get('stations'))
                graph.bounds(graph.node(case['goal']))
                case['preparation_seconds']=time.perf_counter()-begin
                case['total_preparation_seconds']=case['model_load_seconds']+case['graph_build_seconds']+case['preparation_seconds']
                case['return_station']=escape['station'] if escape else None
                case['return_energy_percent']=escape['energy'] if escape else None
                case['return_route']=escape['points'] if escape else []
                # Counterbalanced deterministic method order reduces order bias.
                order=[(repeat,method) for repeat in range(repeats) for method in methods]
                np.random.default_rng(case['seed']).shuffle(order)
                limits=Limits(case['deadline_s'],case['battery_percent'],case['risk_budget'],planning_seconds)
                for repeat,method in order:
                    trial_seed=case['seed']+repeat*100003
                    row=dict(case_id=case['id'],method=method,repeat=repeat,seed=trial_seed,status='pending',success=False)
                    try:
                        if escape is None:
                            row.update(status='no_return_route',plan=dict(admissible=False,points=[],metrics=None,status='no_return_route'))
                            result['records'].append(row);save_result(result,path)
                            print(f"{case['id']} · {method} · no_return_route",flush=True);continue
                        row['plan']=plan(graph,case.get('start',DEST_BASE),case['goal'],method,limits,escape['energy'],seed=trial_seed)
                        row['status']=row['plan']['status']
                        if row['plan']['admissible'] and execute_physics:
                            ex=execute(model,row['plan']['points'],case['battery_percent'],walking_only,
                              max_seconds=max(180.,case['deadline_s']+escape['metrics']['estimated_seconds']*2+60),
                              energy_multiplier=case['energy_multiplier'],return_route=escape['points'],service=service,service_seconds=service_seconds)
                            row['execution']=ex
                            row['prediction_validation']=dict(scope='simulation ledger and assisted execution only; not external battery calibration',
                              task_time_error_s=ex['task_time_s']-row['plan']['metrics']['estimated_seconds'] if ex['task_time_s'] is not None else None,
                              task_battery_error_pp=ex['task_energy_percent']-row['plan']['metrics']['energy_percent'] if ex['task_energy_percent'] is not None else None,
                              nominal_return_energy_percent=escape['energy'],energy_multiplier=case['energy_multiplier'])
                            row['success']=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=case['deadline_s'] and ex['minimum_battery_percent']>=2.)
                            row['status']=ex['outcome'] if row['success'] else 'deadline_miss' if ex['success'] else ex['outcome']
                        elif not row['plan']['admissible'] and row['plan']['metrics'] is not None:row['status']='resource_rejected'
                    except Exception as error:
                        row['status']='error';row['error']=str(error);row['traceback']=traceback.format_exc()
                    result['records'].append(row);save_result(result,path)
                    message=f"{case['id']} · repetition {repeat+1} · {METHODS[method]} · {row['status']}"
                    print(message,flush=True)
                    if progress:progress(len(result['records']),len(cases)*len(methods)*repeats,message)
                # Snapshot map from the exact case; no invented drawn obstacle layout.
                case['map']=dict(bounds=[nav.lower,nav.upper],obstacles=nav.boxes.tolist(),
                  start=list(case.get('start',DEST_BASE)),goal=case['goal'],terrain_patches=case.get('world',{}).get('patches',[]),world_family=case.get('world',{}).get('family','original'))
        result['state']='complete'
    except BaseException:
        result['state']='interrupted';save_result(result,path);raise
    save_result(result,path);return result

def run_suite(*args,**kwargs):
    from research.calibration import validate_profile,energy_context
    profile=validate_profile(kwargs.get('energy_profile'))
    kwargs['energy_profile']=profile
    with experiment_lock():
        with energy_context(profile):return _run_suite(*args,**kwargs)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['smoke','pilot','full','procedural4','procedural12'],default='pilot')
    parser.add_argument('--world-seed',type=int,default=1050000)
    parser.add_argument('--energy-profile',help='Optional externally fitted walking-only battery profile')
    parser.add_argument('--execute',action='store_true',help='Run physics after route admission')
    parser.add_argument('--methods',nargs='+',choices=list(METHODS))
    parser.add_argument('--repeats',type=int,default=1,help='Paired random seeds; repeat each method on every case')
    parser.add_argument('--planning-seconds',type=float,default=2.)
    parser.add_argument('--resolution',type=float,default=.25)
    parser.add_argument('--hybrid',action='store_true')
    parser.add_argument('--service',choices=['charge','swap'],default='charge')
    parser.add_argument('--service-seconds',type=float,default=8.)
    args=parser.parse_args()
    result=run_suite(args.suite,args.execute,args.methods,args.planning_seconds,args.resolution,not args.hybrid,service=args.service,service_seconds=args.service_seconds,repeats=args.repeats,energy_profile=args.energy_profile,world_seed=args.world_seed)
    print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':main()
