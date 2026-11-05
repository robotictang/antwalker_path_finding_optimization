"""Small, reproducible development/held-out study; no neural-network training.

Run from mujoco: python3 -m research.reliability
A study directory is immutable once created; rerunning resumes saved phases.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from contextlib import contextmanager
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from multi_place_config import DEST_BASE,MISSION_TARGETS
from research import swarm
from research.planning import SceneGraph,scalar_search
from research.run import OUT,atomic_json,model_for_case,run_suite
import time

METHODS=['pso','aco','proposed']
DIRECTORY=OUT/'reliability_v1'
PROFILES={'default':copy.deepcopy(swarm.PARAMETERS),'alternative':copy.deepcopy(swarm.PARAMETERS)}
PROFILES['alternative']['pso'].update(particles=24,inertia=.55,cognitive=1.7,social=1.3)
PROFILES['alternative']['aco'].update(ants=18,beta=3.,evaporation=.35)
PROFILES['alternative']['proposed'].update(labels_per_state=12)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

@contextmanager
def parameters(values):
    original=copy.deepcopy(swarm.PARAMETERS)
    try:
        swarm.PARAMETERS.clear();swarm.PARAMETERS.update(copy.deepcopy(values));yield
    finally:
        swarm.PARAMETERS.clear();swarm.PARAMETERS.update(original)

def make_manifest():
    """Generate all tasks before parameter selection; no optimizer used to curate wins.

    A reference distance path only locates a real movable obstruction. Disconnected
    cases are retained. Base terrain, stations and collision geometry stay fixed.
    """
    m=model_for_case();d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    nav=SafeNavigator(m,d,resolution=.25);graph=SceneGraph(nav,True)
    def safe(point):
        node=graph.node(point)
        return graph.point(node).tolist()
    cases=[]
    for split,count,seed_base in [('development',4,71000),('heldout',12,92000)]:
        for i in range(count):
            seed=seed_base+i;rng=np.random.default_rng(seed)
            # Six mission regions, sampled endpoint/start offsets and obstacle positions.
            target=MISSION_TARGETS[i%len(MISSION_TARGETS)]['pos']
            start=safe(np.asarray(DEST_BASE)+rng.uniform(-1.5,1.5,2))
            goal=safe(np.asarray(target)+rng.uniform(-1.5,1.5,2))
            node=graph.node(goal);graph.bounds(node)
            route,_,_=scalar_search(graph,start,goal,[1,0,0,0],math.pi/2,time.perf_counter()+10,200000)
            if route is None:raise RuntimeError('Cannot locate reference corridor for manifest')
            lengths=np.linalg.norm(np.diff(route,axis=0),axis=1);position=float(rng.uniform(.3,.7)*sum(lengths))
            edge=int(np.searchsorted(np.cumsum(lengths),position));before=sum(lengths[:edge])
            xy=np.asarray(route[edge])+(np.asarray(route[edge+1])-route[edge])*(position-before)/lengths[edge]
            xy+=rng.uniform(-1.,1.,2)
            cases.append(dict(id=f'{split}_{i+1:02d}',split=split,layout_id=f'{split}_{seed}',seed=seed,
              variant=0,start=start,goal=goal,hazard_position=[*xy.tolist(),0.],
              deadline_s=float([110,160,210][i%3]),battery_percent=float([70,85,100][i%3]),
              risk_budget=float([15,25,40][i%3]),energy_multiplier=float([.9,1.,1.12][i%3])))
    return dict(version=1,cases=cases,profiles=PROFILES,budget_seconds=2.,development_repeats=2,test_repeats=3,
      physics_case_ids=['heldout_02','heldout_03','heldout_05','heldout_06'],
      selection_rule='Maximize development admission count; then minimize mean admitted common score; exact ties select default. Same two-profile search for every method.',
      scope='Independently seeded task/obstacle-position samples on one fixed terrain scene; not new terrain worlds.',
      benchmark_reference='https://numbbo.github.io/coco-doc/experimental-setup/')

def selection_key(result,method):
    rows=[r for r in result['records'] if r['method']==method]
    admitted=[r['plan']['quality_score'] for r in rows if r.get('plan',{}).get('admissible')]
    return (-len(admitted),float(np.mean(admitted)) if admitted else float('inf'))

def paired_report(result):
    indexed={(r['case_id'],r['method'],r.get('repeat',0)):r for r in result['records']}
    cases=[c['id'] for c in result['cases']];reports=[]
    for baseline in ['pso','aco']:
        wins=ties=losses=both_rejected=proposal_only=baseline_only=0;differences=[];layout_means=[]
        for case in cases:
            local=[]
            for repeat in range(result['repeats']):
                a=indexed[(case,'proposed',repeat)];b=indexed[(case,baseline,repeat)]
                pa=a.get('plan',{});pb=b.get('plan',{});fa=bool(pa.get('admissible'));fb=bool(pb.get('admissible'))
                if fa and fb:
                    delta=pb['quality_score']-pa['quality_score'];local.append(delta);differences.append(delta)
                    if abs(delta)<=1e-8:ties+=1
                    elif delta>0:wins+=1
                    else:losses+=1
                elif fa:proposal_only+=1
                elif fb:baseline_only+=1
                else:both_rejected+=1
            if local:layout_means.append(float(np.mean(local)))
        rng=np.random.default_rng(4100)
        boot=np.mean(rng.choice(layout_means,(5000,len(layout_means)),replace=True),axis=1) if len(layout_means)>1 else []
        reports.append(dict(baseline=baseline,wins=wins,ties=ties,losses=losses,both_rejected=both_rejected,
          proposed_only_admitted=proposal_only,baseline_only_admitted=baseline_only,paired_admitted_trials=len(differences),
          layouts_with_paired_admission=len(layout_means),mean_layout_score_advantage=float(np.mean(layout_means)) if layout_means else None,
          descriptive_layout_bootstrap_95_percent=np.quantile(boot,[.025,.975]).tolist() if len(boot) else None))
    return dict(run_id=result['run_id'],attempts=len(result['records']),layouts=len(cases),repeats=result['repeats'],
      comparisons=reports,summary=result['summary'],
      interpretation='Positive score advantage favors proposed. Paired quality includes only jointly admitted trials; separate counts retain all other outcomes. Bootstrap resamples whole sampled layouts, after averaging paired seeds within each layout. Small conditional interval on a fixed terrain; no broad significance or publication claim.')

def study(directory=DIRECTORY,physics=True):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    manifest_path=directory/'manifest.json'
    if not manifest_path.exists():atomic_json(manifest_path,make_manifest())
    manifest=json.loads(manifest_path.read_text());manifest_hash=digest(manifest)
    development=[c for c in manifest['cases'] if c['split']=='development']
    heldout=[c for c in manifest['cases'] if c['split']=='heldout']
    assert not ({c['seed'] for c in development}&{c['seed'] for c in heldout})
    def phase(label,cases,profiles,repeats,execute=False):
        path=directory/(label+'.json')
        if path.exists():
            previous=json.loads(path.read_text())
            if previous['state']!='complete':raise RuntimeError(f'Incomplete phase {label}; retain it and choose a new study directory')
            if previous['study']['manifest_sha256']!=manifest_hash:raise RuntimeError('Manifest changed after phase execution')
            return previous
        meta=dict(manifest=str(manifest_path),manifest_sha256=manifest_hash,split=cases[0]['split'],
          phase=label,parameters=copy.deepcopy(profiles),parameter_sha256=digest(profiles),selection_rule=manifest['selection_rule'],
          reproduction=f'python3 -m research.reliability --directory {directory}',scope=manifest['scope'])
        with parameters(profiles):
            result=run_suite(suite=label,execute_physics=execute,methods=METHODS,
              planning_seconds=manifest['budget_seconds'],repeats=repeats,cases_override=cases,study=meta)
        atomic_json(path,result);return result
    trials={}
    for profile,config in manifest['profiles'].items():
        trials[profile]=phase('development_'+profile,development,config,manifest['development_repeats'])
    chosen={method:min(trials,key=lambda p:(selection_key(trials[p],method),p!='default')) for method in METHODS}
    locked=copy.deepcopy(manifest['profiles']['default'])
    for method,profile in chosen.items():locked[method]=copy.deepcopy(manifest['profiles'][profile][method])
    lock_path=directory/'locked_parameters.json'
    selection=dict(manifest_sha256=manifest_hash,chosen=chosen,parameters=locked,sha256=digest(locked),
      selection_rule=manifest['selection_rule'],development_runs={p:r['run_id'] for p,r in trials.items()})
    if lock_path.exists() and json.loads(lock_path.read_text())!=selection:raise RuntimeError('Previously frozen parameter selection changed')
    atomic_json(lock_path,selection) # Written BEFORE any held-out evaluation.
    test=phase('heldout_planning',heldout,locked,manifest['test_repeats'])
    report=paired_report(test);atomic_json(directory/'comparison.json',report)
    physical=None
    if physics:
        subset=[c for c in heldout if c['id'] in manifest['physics_case_ids']]
        physical=phase('heldout_physics',subset,locked,1,True)
    atomic_json(directory/'study_summary.json',dict(manifest_sha256=manifest_hash,selection=selection,
      planning_report=report,physics_run_id=physical['run_id'] if physical else None,
      physics_summary=physical['summary'] if physical else None))
    # The planning set contains every held-out layout; make it the first dashboard.
    from research.run import save_result
    save_result(test,OUT/(test['run_id']+'.json'))
    from research.export_dashboard import export
    export(OUT/(test['run_id']+'.json'),build=True)
    print(json.dumps(dict(chosen=chosen,report=report,physics_run_id=physical['run_id'] if physical else None),indent=2))
    return test

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=DIRECTORY)
    p.add_argument('--planning-only',action='store_true');a=p.parse_args();study(a.directory,not a.planning_only)
