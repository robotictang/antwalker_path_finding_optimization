"""V6 final validation: 1,200 predeclared records, external OMPL and tracking.

Run from mujoco: python3 -m research.final_study. This never overwrites V4/V5.
No neural model is trained. All six methods receive the same two-profile
development search. New test outcomes never choose parameters or weights.
"""
import argparse,copy,hashlib,json,time
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from research import advanced,swarm,run,external_planners
from research.reliability import PROFILES,selection_key
from research.worlds import sample_cases,identity,world_model,terrain_context
from research.advanced_study import comparison

DIRECTORY=run.OUT/'final_validation_v6'
MAIN=['proposed_v4','pso_polished','aco_polished','ompl_rrtstar','ompl_seeded_rrtstar','ompl_rrtconnect']
BASE=np.array([1/50,1/90,1/30,.25/20])
WEIGHTS=dict(balanced=[1.,1.,1.,1.],distance=[2.,1.,1.,1.],time=[1.,2.,1.,1.],energy=[1.,1.,2.,1.],terrain=[1.,1.,1.,4.])

def profiles():
    out={n:dict(swarm=copy.deepcopy(v),advanced=copy.deepcopy(advanced.PARAMETERS),external=copy.deepcopy(external_planners.PARAMETERS)) for n,v in PROFILES.items()}
    out['alternative']['advanced'].update(seed_fraction=.55,roadmap_fraction=.25,max_landmarks=60,polish_steps=[.5,.15,.05])
    out['alternative']['external'].update(range_m=7.,goal_bias=.25,seed_fraction=.55,polish_fraction=.45,simplify_steps=45)
    return out

@contextmanager
def objective(profile='balanced'):
    previous=swarm.QUALITY_WEIGHTS.copy()
    try:swarm.QUALITY_WEIGHTS[:]=BASE*np.asarray(WEIGHTS[profile]);yield
    finally:swarm.QUALITY_WEIGHTS[:]=previous

@contextmanager
def configuration(cfg):
    targets=(swarm.PARAMETERS,advanced.PARAMETERS,external_planners.PARAMETERS);before=[copy.deepcopy(x) for x in targets]
    cap=swarm.FITNESS_CAP
    try:
        for target,key in zip(targets,['swarm','advanced','external']):target.clear();target.update(copy.deepcopy(cfg[key]))
        swarm.FITNESS_CAP=240;yield
    finally:
        for target,value in zip(targets,before):target.clear();target.update(value)
        swarm.FITNESS_CAP=cap

@contextmanager
def method_configurations(configs):
    original=run.plan
    def configured(graph,start,goal,method,*args,**kwargs):
        with configuration(configs[method]):return original(graph,start,goal,method,*args,**kwargs)
    try:run.plan=configured;yield
    finally:run.plan=original

def shifted_cases():
    cases=sample_cases(24,1680000,'v6shift')
    for c in cases:
        spec=c['world'];spec['friction_scale']*=.7;spec['regime']='shifted'
        for b in spec['obstacles']:
            b['sx']*=1.15
            if b['sy']<1.:b['sy']*=1.15
        for patch in spec['patches']:patch['grade']=2
        for tile in spec['tiles']:tile['height']=min(.105,1.25*tile['height'])
        with terrain_context(spec):
            model=world_model(spec);data=mujoco.MjData(model);mujoco.mj_forward(model,data);nav=SafeNavigator(model,data,resolution=.25)
            c['start']=nav.point(nav.nearest_free(c['start'])).tolist();c['goal']=nav.point(nav.nearest_free(c['goal'])).tolist()
        c['world_sha256']=identity(spec);c['regime']='shifted'
    return cases

def make_manifest():
    dev=sample_cases(8,1660000,'v6dev');test=sample_cases(24,1670000,'v6test')+shifted_cases()
    for c in dev+test:c.setdefault('regime','standard')
    prior=[]
    for directory in ['advanced_study_v4','validation_extension_v5']:
        prior+=json.loads((run.OUT/directory/'manifest.json').read_text())['cases']
    assert not ({c['world_sha256'] for c in dev+test}&{c['world_sha256'] for c in prior})
    selected=[f'v6test_{i:02}' for i in range(1,9)]+[f'v6shift_{i:02}' for i in range(1,5)]
    short=[f'v6test_{i:02}' for i in range(1,5)]+[f'v6shift_{i:02}' for i in range(1,9)]
    return dict(version=6,cases=dev+test,profiles=profiles(),methods=MAIN,development_repeats=1,test_repeats=2,
      budget_seconds=2.,candidate_cap=240,weights=WEIGHTS,weight_case_ids=selected,physics_case_ids=selected,short_budget_case_ids=short,short_budgets=[.5,1.],
      physics_plan_rule='Replay repetition zero of the frozen primary run. Safe V6 tracking for all six methods at assistance 1. Legacy and reduced-assistance controls replay V4 only on the same 12 worlds. These are repeated measurements of existing worlds, not extra independent maps.',
      selection_rule='Two complete profiles per method on the same 8 fresh standard development worlds. Maximize admission then minimize admitted mean balanced Q; exact ties retain default. Freeze before any test phase.',
      objective_rule='Feasibility first; same four normalized weights for every method within a profile. Weight profiles predeclared, never tuned on test outcomes. Alternative-profile absolute scores cannot be compared across different profiles.',
      native_scope='Actual OMPL 2.0.1 RRT*, common-seeded RRT*, and RRTConnect. Native RRT* uses additive translation/terrain edge-cost relaxation without turn history. Final evaluation and polishing use the exact common heading-aware score. Seeded RRT* receives the same fixed initial corridor refiner as V4 within its wall allowance.',
      fairness='Same 2 s nominal primary planner allowance, 240 whole-route candidate ceiling, 40000 declared expansion/state-check ceiling, exact common footprint geometry, common final ranking and polishing. OMPL import is outside the timer; fork, native search, simplification, polishing and IPC are inside. Different counter primitives are reported separately.',
      scope='48 fresh primary worlds: 24 standard and 24 predeclared shifted geometry/terrain/friction worlds. Assisted walking simulation with gravity compensation; no real electrical or hardware validation.',
      tracking_policy='safe_v6',expected_attempts=1200,expected_phases=12,
      analysis_plan='All scheduled attempts retained. Paired Q only on jointly admitted cases; all admission categories reported. Average repeated seeds within worlds; 5000 whole-world bootstrap resamples, seed 6104. Descriptive intervals. Report means, medians, maxima, per-regime outcomes and leave-largest-effect sensitivity as a labeled diagnostic. Weight and budget phases are secondary; controller comparison uses exact saved routes. No favorable-result stopping or test-informed retuning.')

def dependency():
    import importlib.metadata
    root=external_planners.VENDOR
    return dict(library='OMPL',version=importlib.metadata.version('ompl'),binary_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*.so'))})

def replay(primary,cases,methods,name,meta,directory,policy='safe_v6',assistance=1.):
    dest=directory/(name+'.json')
    if dest.exists():
        r=json.loads(dest.read_text())
        if r['state']!='complete' or r['study']!=meta:raise RuntimeError('Incomplete or mismatched replay')
        return r
    r=copy.deepcopy(primary);r.update(run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'),created_at=datetime.now(timezone.utc).isoformat(),suite=name,execute=True,repeats=1,records=[],cases=copy.deepcopy(cases),methods=methods,state='running',study=meta,tracking_policy=policy,assistance_scale=assistance)
    index={(x['case_id'],x['method']):x for x in primary['records'] if x['repeat']==0}
    path=run.OUT/(r['run_id']+'.json');run.save_result(r,path)
    with run.experiment_lock():
        try:
            for c in r['cases']:
                with terrain_context(c['world']):
                    model=world_model(c['world'])
                    for method in methods:
                        row=copy.deepcopy(index[c['id'],method]);row.pop('execution',None);row.pop('prediction_validation',None);row['success']=False;row['plan_origin_run']=primary['run_id']
                        p=row['plan']
                        if p.get('admissible'):
                            ex=run.execute(model,p['points'],c['battery_percent'],walking_only=True,max_seconds=max(180.,c['deadline_s']+120),energy_multiplier=c['energy_multiplier'],return_route=c['return_route'],assistance_scale=assistance,tracking_policy=policy)
                            row['execution']=ex;row['success']=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=c['deadline_s'] and ex['minimum_battery_percent']>=2.)
                            row['status']=ex['outcome'] if row['success'] else 'deadline_miss' if ex['success'] else ex['outcome']
                            row['prediction_validation']=dict(scope='Simulated nominal ledger and assisted execution; not external battery calibration',task_time_error_s=ex['task_time_s']-p['metrics']['estimated_seconds'] if ex['task_time_s'] is not None else None,task_battery_error_pp=ex['task_energy_percent']-p['metrics']['energy_percent'] if ex['task_energy_percent'] is not None else None)
                        r['records'].append(row);run.save_result(r,path);print(f"{name} · {c['id']} · {method} · {row['status']}",flush=True)
            r['state']='complete'
        except BaseException:r['state']='interrupted';run.save_result(r,path);raise
    run.save_result(r,path);run.atomic_json(dest,r);return r

def study(directory=DIRECTORY):
    directory=Path(directory);directory.mkdir(exist_ok=True,parents=True);mp=directory/'manifest.json'
    if not mp.exists():run.atomic_json(mp,make_manifest())
    mf=json.loads(mp.read_text());digest=identity(mf)
    source_names=set(json.loads((run.OUT/'validation_extension_v5/source_lock.json').read_text()))|{'research/tracking.py','research/external_planners.py','research/final_study.py','research/electrical_logging.py'}
    sources={n:hashlib.sha256((run.ROOT/n).read_bytes()).hexdigest() for n in sorted(source_names)}
    frozen=directory/'source_lock.json'
    if frozen.exists() and json.loads(frozen.read_text())!=sources:raise RuntimeError('Scientific sources changed after freeze; use new study and test seeds')
    run.atomic_json(frozen,sources);dep=dependency();dp=directory/'native_dependency.json'
    if dp.exists() and json.loads(dp.read_text())!=dep:raise RuntimeError('Native library changed after freeze')
    run.atomic_json(dp,dep)
    dev=[c for c in mf['cases'] if c['split']=='v6dev'];test=[c for c in mf['cases'] if c['split']!='v6dev']
    def metadata(name,configs,weight='balanced',policy='safe_v6',assistance=1.):
        return dict(version=6,focal_method='proposed_v4',phase=name,manifest_sha256=digest,parameters=copy.deepcopy(configs),parameter_sha256=identity(configs),weight_profile=weight,score_weights=(BASE*np.asarray(mf['weights'][weight])).tolist(),tracking_policy=policy,assistance_scale=assistance,native_dependency_sha256=identity(dep),scope=mf['scope'],selection_rule=mf['selection_rule'],fairness=mf['fairness'],reproduction=f'python3 -m research.final_study --directory {directory}')
    def phase(name,cases,configs,repeats=1,budget=2.,weight='balanced'):
        dest=directory/(name+'.json');meta=metadata(name,configs,weight)
        if dest.exists():
            r=json.loads(dest.read_text())
            if r['state']!='complete' or r['study']!=meta:raise RuntimeError('Incomplete or changed phase '+name)
            return r
        with objective(weight),method_configurations(configs):r=run.run_suite(suite=name,cases_override=cases,study=meta,methods=MAIN,repeats=repeats,planning_seconds=budget,execute_physics=False,tracking_policy='safe_v6')
        run.atomic_json(dest,r);return r
    development={n:phase('v6_development_'+n,dev,{m:cfg for m in MAIN}) for n,cfg in mf['profiles'].items()}
    choices={m:min(development,key=lambda n:(selection_key(development[n],m),n!='default')) for m in MAIN}
    configs={m:copy.deepcopy(mf['profiles'][choices[m]]) for m in MAIN}
    selected=dict(chosen=choices,parameters=configs,sha256=identity(configs),manifest_sha256=digest)
    lock=directory/'locked_parameters.json'
    if lock.exists() and json.loads(lock.read_text())!=selected:raise RuntimeError('Selected settings changed')
    run.atomic_json(lock,selected)
    primary=phase('v6_primary',test,configs,repeats=2);phases={'v6_primary':primary}
    subset=lambda key:[c for c in test if c['id'] in mf[key]]
    for weight in ['distance','time','energy','terrain']:
        name='v6_weight_'+weight;phases[name]=phase(name,subset('weight_case_ids'),configs,weight=weight)
    for budget in mf['short_budgets']:
        name='v6_budget_'+str(budget).replace('.','p');phases[name]=phase(name,subset('short_budget_case_ids'),configs,budget=budget)
    selected_cases=[c for c in primary['cases'] if c['id'] in mf['physics_case_ids']]
    for name,methods,policy,assistance in [('v6_physics_safe',MAIN,'safe_v6',1.),('v6_physics_legacy',['proposed_v4'],'legacy',1.),('v6_physics_reduced',['proposed_v4'],'safe_v6',.5)]:
        phases[name]=replay(primary,selected_cases,methods,name,metadata(name,configs,policy=policy,assistance=assistance),directory,policy,assistance)
    report=comparison(primary)
    for row in report['case_verdicts']:row['verdict']=row['verdict'].replace('V4','Proposed')
    run.atomic_json(directory/'comparison.json',report)
    allphases={**{'v6_development_'+n:r for n,r in development.items()},**phases}
    total=sum(len(r['records']) for r in allphases.values());assert total==1200
    run.atomic_json(directory/'study_summary.json',dict(version=6,selection=selected,attempts=total,phase_counts={n:len(r['records']) for n,r in allphases.items()},planning_report=report,scope=mf['scope'],hardware_calibration='awaiting_external_measurements'))
    run.save_result(primary,run.OUT/(primary['run_id']+'.json'))
    print(json.dumps(dict(complete=True,attempts=total,primary_run=primary['run_id'],selection=choices),indent=2));return primary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=DIRECTORY);a=p.parse_args();study(a.directory)
