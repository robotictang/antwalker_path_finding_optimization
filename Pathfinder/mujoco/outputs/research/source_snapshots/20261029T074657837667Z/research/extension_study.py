"""Predeclared V5 validation extension: 800 attempts, 48 fresh test worlds.

Development and evaluation are separated. Failed attempts and losing methods
are retained. Run from mujoco: python3 -m research.extension_study
"""
import argparse,copy,hashlib,json
from contextlib import contextmanager
from pathlib import Path
from research import adaptive,advanced,swarm,run
from research.advanced_study import comparison
from research.reliability import PROFILES,selection_key
from research.worlds import sample_cases,identity

DIRECTORY=run.OUT/'validation_extension_v5'
MAIN=['proposed_v4','pso_polished','aco_polished','proposed_v5']
ABLATIONS=['proposed_v5','proposed_v5_fixed','proposed_v5_no_polish','proposed_v5_no_landmarks']

def profiles():
    out={n:dict(swarm=copy.deepcopy(v),advanced=copy.deepcopy(advanced.PARAMETERS),adaptive=copy.deepcopy(adaptive.PARAMETERS)) for n,v in PROFILES.items()}
    out['alternative']['advanced'].update(seed_fraction=.55,roadmap_fraction=.25,max_landmarks=60,polish_steps=[.5,.15,.05])
    out['alternative']['adaptive'].update(seed_clear=.20,seed_blocked=.35,roadmap_clear=.25,roadmap_blocked=.50,max_landmarks=64,direct_gap=.001)
    return out

@contextmanager
def configuration(cfg,cap=240):
    old=(copy.deepcopy(swarm.PARAMETERS),copy.deepcopy(advanced.PARAMETERS),copy.deepcopy(adaptive.PARAMETERS),swarm.FITNESS_CAP)
    try:
        for target,source in [(swarm.PARAMETERS,cfg['swarm']),(advanced.PARAMETERS,cfg['advanced']),(adaptive.PARAMETERS,cfg['adaptive'])]:
            target.clear();target.update(copy.deepcopy(source))
        advanced.PARAMETERS['max_evaluations']=cap;swarm.FITNESS_CAP=cap
        yield
    finally:
        for target,source in zip((swarm.PARAMETERS,advanced.PARAMETERS,adaptive.PARAMETERS),old[:3]):target.clear();target.update(source)
        swarm.FITNESS_CAP=old[3]

@contextmanager
def method_configurations(configs,cap):
    original=run.plan
    def configured(graph,start,goal,method,*args,**kwargs):
        key='proposed_v5' if method.startswith('proposed_v5') else method
        with configuration(configs[key],cap):return original(graph,start,goal,method,*args,**kwargs)
    try:run.plan=configured;yield
    finally:run.plan=original

def make_manifest():
    cases=sample_cases(8,1470000,'v5dev')+sample_cases(48,1480000,'v5test')
    old=json.loads((run.OUT/'advanced_study_v4/manifest.json').read_text())['cases']
    assert not ({c['world_sha256'] for c in cases}&{c['world_sha256'] for c in old})
    return dict(version=5,cases=cases,profiles=profiles(),methods=MAIN,ablation_methods=ABLATIONS,
      development_repeats=1,test_repeats=2,budget_seconds=2.,candidate_cap=240,
      ablation_case_ids=[f'v5test_{i:02}' for i in range(1,17)],
      short_budget_case_ids=[f'v5test_{i:02}' for i in range(1,9)],short_budgets=[.5,1.],
      cap_case_ids=[f'v5test_{i:02}' for i in range(1,17)],sensitivity_candidate_cap=80,
      physics_case_ids=[f'v5test_{i:02}' for i in range(1,13)],assistance_scales=[1.,.5],
      selection_rule='Every core method receives two profiles on the same 8 fresh development worlds; maximize admission then minimize admitted mean common score; exact ties retain default. Each method uses its own selected complete profile. No test-world tuning.',
      objective='Unchanged feasible-first D/50+T/90+E/30+0.25H/20. No method-specific objective coefficients.',
      fairness='Same time, expansion, final-route-candidate cap and common evaluator. The 80-cap phase is an equal ceiling, not equal actual evaluations or equal total compute. All metric calls, including roadmap edges and final evaluation, are recorded separately.',
      scope='48 untouched test worlds from four existing procedural families, 12 per family; independent of earlier V3/V4 campaigns. Assisted simulation only; reduced assistance is velocity blending, not unassisted validation. Gravity compensation remains enabled. No electrical calibration.',
      expected_attempts=800,expected_phases=9,
      stopping_rule='Complete every predeclared phase and retain all outcomes; no early stopping on favorable results. Fixing a scientific defect after freeze requires a new campaign directory and new test seeds.')

def study(directory=DIRECTORY):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/'manifest.json'
    if not path.exists():run.atomic_json(path,make_manifest())
    manifest=json.loads(path.read_text());digest=identity(manifest)
    source_names=sorted(set(json.loads((run.OUT/'advanced_study_v4/source_lock.json').read_text()))|{'research/adaptive.py','research/extension_study.py'})
    sources={n:hashlib.sha256((run.ROOT/n).read_bytes()).hexdigest() for n in source_names}
    lock=directory/'source_lock.json'
    if lock.exists() and json.loads(lock.read_text())!=sources:raise RuntimeError('Frozen scientific code changed; use new campaign and seeds')
    run.atomic_json(lock,sources)
    dev=[c for c in manifest['cases'] if c['split']=='v5dev'];test=[c for c in manifest['cases'] if c['split']=='v5test']
    assert len({c['world_sha256'] for c in manifest['cases']})==56
    def phase(name,cases,configs,methods,repeats,budget=2.,cap=240,execute=False,assistance=1.):
        dest=directory/(name+'.json')
        meta=dict(version=5,focal_method='proposed_v5',phase=name,manifest_sha256=digest,parameters=copy.deepcopy(configs),
          parameter_sha256=identity(configs),candidate_cap=cap,assistance_scale=assistance,scope=manifest['scope'],
          selection_rule=manifest['selection_rule'],fairness=manifest['fairness'],
          reproduction=f'python3 -m research.extension_study --directory {directory}')
        if dest.exists():
            r=json.loads(dest.read_text())
            if r['state']!='complete' or r['study']!=meta:raise RuntimeError('Incomplete or mismatched phase; preserve it and investigate')
            return r
        with method_configurations(configs,cap):
            r=run.run_suite(suite=name,cases_override=cases,study=meta,methods=methods,repeats=repeats,
              planning_seconds=budget,execute_physics=execute,assistance_scale=assistance)
        run.atomic_json(dest,r)
        return r
    development={n:phase('v5_development_'+n,dev,{m:cfg for m in MAIN},MAIN,1) for n,cfg in manifest['profiles'].items()}
    chosen={m:min(development,key=lambda n:(selection_key(development[n],m),n!='default')) for m in MAIN}
    configs={m:copy.deepcopy(manifest['profiles'][chosen[m]]) for m in MAIN}
    selection=dict(chosen=chosen,parameters=configs,sha256=identity(configs),manifest_sha256=digest)
    frozen=directory/'locked_parameters.json'
    if frozen.exists() and json.loads(frozen.read_text())!=selection:raise RuntimeError('Frozen development selection changed')
    run.atomic_json(frozen,selection)
    primary=phase('v5_fresh_planning',test,configs,MAIN,2)
    phases={'v5_fresh_planning':primary}
    subset=lambda key:[c for c in test if c['id'] in manifest[key]]
    phases['v5_feature_ablations']=phase('v5_feature_ablations',subset('ablation_case_ids'),configs,ABLATIONS,2)
    for budget in manifest['short_budgets']:
        name='v5_budget_'+str(budget).replace('.','p');phases[name]=phase(name,subset('short_budget_case_ids'),configs,MAIN,1,budget)
    phases['v5_candidate_cap80']=phase('v5_candidate_cap80',subset('cap_case_ids'),configs,MAIN,1,cap=80)
    for scale in manifest['assistance_scales']:
        name='v5_physics_assistance_'+str(scale).replace('.','p')
        phases[name]=phase(name,subset('physics_case_ids'),configs,MAIN,1,execute=True,assistance=scale)
    report=comparison(primary)
    # The reused mathematical comparison routine's old verdict wording is
    # replaced without changing any numeric calculation.
    for row in report['case_verdicts']:row['verdict']=row['verdict'].replace('V4','V5')
    run.atomic_json(directory/'comparison.json',report)
    run.atomic_json(directory/'study_summary.json',dict(version=5,selection=selection,
      attempts=sum(len(r['records']) for r in [*development.values(),*phases.values()]),
      phase_counts={n:len(r['records']) for n,r in {**{'v5_development_'+n:r for n,r in development.items()},**phases}.items()},
      planning_report=report,scope=manifest['scope']))
    run.save_result(primary,run.OUT/(primary['run_id']+'.json'))
    print(json.dumps({'complete':True,'selection':chosen,'primary_run':primary['run_id']},indent=2))
    return primary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=DIRECTORY);a=p.parse_args();study(a.directory)
