"""Prospective representation and component study for the IJ3C revision.

Eight development worlds, 32 fresh primary worlds, 640 planning records.
This is a new test of related procedural worlds, not hardware validation.
"""
import copy
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from research import advanced,continuous_pso,run,swarm
from research.reliability import PROFILES,selection_key
from research.worlds import sample_cases,identity

DIRECTORY=run.OUT/'publication_ij3c_20261104'
TUNED=['proposed_v4','pso_polished','aco_polished','continuous_pso']
METHODS=TUNED+['proposed_v4_no_landmarks','proposed_v4_no_polish']


def profiles():
    result={n:dict(swarm=copy.deepcopy(v),advanced=copy.deepcopy(advanced.PARAMETERS),continuous=copy.deepcopy(continuous_pso.PARAMETERS)) for n,v in PROFILES.items()}
    result['alternative']['advanced'].update(seed_fraction=.55,roadmap_fraction=.25,max_landmarks=60,polish_steps=[.5,.15,.05])
    result['alternative']['continuous'].update(particles=20,iterations=60,inertia=.75,cognitive=1.6,social=1.6,jitter_m=4.)
    return result


def source_lock():
    files=[*run.ROOT.glob('*.py'),*run.ROOT.glob('research/*.py'),run.ROOT/'hybrid_hexapod_multi_place.xml']
    return {str(p.relative_to(run.ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def make_manifest():
    dev=sample_cases(8,2130000,'ij3cdev');test=sample_cases(32,2140000,'ij3ctest')
    oldroot=run.ROOT.parents[1]/'mujoco/outputs/research';previous=set()
    for p in oldroot.glob('*/manifest.json'):
        data=json.loads(p.read_text())
        previous.update(c.get('world_sha256') for c in data.get('cases',[]) if c.get('world_sha256'))
    fresh={c['world_sha256'] for c in dev+test}
    assert len(fresh)==40 and not fresh&previous
    return dict(version='ij3c-20261104',cases=dev+test,methods=METHODS,tuned_methods=TUNED,profiles=profiles(),
        planning_seconds=2.,candidate_cap=240,primary_repeats=3,development_repeats=1,expected_records=640,
        expected_phases={'development_default':32,'development_alternative':32,'primary':576},
        primary_question='Does V4 retain useful benefit against a continuous-coordinate PSO control, and which components contribute on a new 32-world sample?',
        representation_scope='Coordinate PSO freely moves a fixed number of internal xy vertices within the map; not an exhaustive unrestricted path-space swarm algorithm.',
        fairness='Same common evaluator, footprint, resources, nominal 2 s wall limit and 240 evaluated-route ceiling. Common preparation excluded and logged. Each base method receives the same two complete development profiles; component removals inherit selected V4 settings.',
        selection_rule='Maximize development admission, then minimize admitted mean balanced Q; exact ties retain default. Select before primary test. Never select by primary outcomes.',
        analysis_plan='Retain all scheduled records. Compare Q only on joint admission; report remaining admission categories. Average relative effects within worlds then 5000 whole-world bootstrap draws, seed 41104. Descriptive unadjusted intervals. Report median, range, and fraction of worlds exceeding a declared descriptive 0.5 percent practical-effect reference, not a significance threshold.',
        caveats=['Same four procedural world families as earlier studies; new seeds do not create independent map sources.','Planning only. No hardware, electrical energy or unassisted-locomotion claim.','Protocol frozen locally before runs; not externally preregistered.','Wall-clock timing is machine/load dependent.'])


@contextmanager
def configuration(config):
    targets=[swarm.PARAMETERS,advanced.PARAMETERS,continuous_pso.PARAMETERS]
    before=[copy.deepcopy(x) for x in targets]
    try:
        for target,key in zip(targets,['swarm','advanced','continuous']):target.clear();target.update(copy.deepcopy(config[key]))
        yield
    finally:
        for target,old in zip(targets,before):target.clear();target.update(old)


@contextmanager
def per_method(configs):
    original=run.plan
    def configured(graph,start,goal,method,*args,**kwargs):
        with configuration(configs[method]):return original(graph,start,goal,method,*args,**kwargs)
    try:run.plan=configured;yield
    finally:run.plan=original


def study():
    DIRECTORY.mkdir(parents=True,exist_ok=True);mp=DIRECTORY/'manifest.json'
    if not mp.exists():run.atomic_json(mp,make_manifest())
    manifest=json.loads(mp.read_text());sources=source_lock();lp=DIRECTORY/'source_lock.json'
    if lp.exists() and json.loads(lp.read_text())!=sources:raise RuntimeError('Frozen study source changed; use a new protocol version')
    run.atomic_json(lp,sources)
    dev=[c for c in manifest['cases'] if c['split']=='ij3cdev'];test=[c for c in manifest['cases'] if c['split']=='ij3ctest']
    def phase(name,cases,methods,configs,repeats):
        dest=DIRECTORY/(name+'.json')
        if dest.exists():
            saved=json.loads(dest.read_text())
            if saved['state']!='complete':raise RuntimeError('Incomplete phase requires explicit review: '+name)
            return saved
        meta=dict(version=manifest['version'],phase=name,focal_method='proposed_v4',manifest_sha256=identity(manifest),
                  parameters=copy.deepcopy(configs),parameter_sha256=identity(configs),protocol_frozen=True,
                  score_weights=swarm.QUALITY_WEIGHTS.tolist(),scope='Prospective related-procedural-world planning comparison, no physical validation.')
        with per_method(configs):result=run.run_suite(suite='ij3c_'+name,cases_override=cases,study=meta,methods=methods,
              repeats=repeats,planning_seconds=2.,execute_physics=False)
        run.atomic_json(dest,result);return result
    development={n:phase('development_'+n,dev,TUNED,{m:cfg for m in TUNED},1) for n,cfg in manifest['profiles'].items()}
    choices={m:min(development,key=lambda n:(selection_key(development[n],m),n!='default')) for m in TUNED}
    configs={m:copy.deepcopy(manifest['profiles'][choices[m]]) for m in TUNED}
    for m in METHODS:
        if m not in configs:configs[m]=copy.deepcopy(configs['proposed_v4'])
    selected=dict(choices=choices,configs=configs,sha256=identity(configs),manifest_sha256=identity(manifest))
    sl=DIRECTORY/'locked_parameters.json'
    if sl.exists() and json.loads(sl.read_text())!=selected:raise RuntimeError('Development selection changed')
    run.atomic_json(sl,selected)
    primary=phase('primary',test,METHODS,configs,3)
    assert source_lock()==sources
    run.atomic_json(DIRECTORY/'study_summary.json',dict(state='complete',records=640,primary_records=len(primary['records']),
        primary_worlds=32,choices=choices,primary_run=primary['run_id'],scope=manifest['caveats']))
    print('Completed 640-record IJ3C study',flush=True)


if __name__=='__main__':study()
