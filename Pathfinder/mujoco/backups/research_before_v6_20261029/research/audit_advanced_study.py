"""Read-only integrity and geometry audit for the frozen version 4 campaign."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from research.run import ROOT,OUT,atomic_json,summarize
from research.worlds import identity,world_model,terrain_context
from research.planning import SceneGraph
from research.swarm import quality
from research.advanced import METHODS as ADVANCED,DEFAULT_INITIAL
from research.advanced_study import FOCAL,comparison
from research.reliability import selection_key

PHASES=['v4_development_default','v4_development_alternative','v4_heldout_planning','v4_heldout_ablations','v4_budget_0p5','v4_budget_1p0','v4_heldout_physics']
def audit(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());chosen=json.loads((directory/'locked_parameters.json').read_text());source_lock=json.loads((directory/'source_lock.json').read_text())
    errors=[];warnings=[];counts={};runs={};graphs={};verified_routes=set();metric_checks=0;geometry_checks=0
    def check(ok,message):
        if not ok:errors.append(message)
    digest=identity(manifest);check(identity(chosen['parameters'])==chosen['sha256'],'Locked parameter digest mismatch')
    dev=[c for c in manifest['cases'] if c['split']=='development'];test=[c for c in manifest['cases'] if c['split']=='heldout']
    check(len({c['world_sha256'] for c in manifest['cases']})==32,'World duplicate or wrong world count')
    check(not ({c['seed'] for c in dev}&{c['seed'] for c in test}),'Development/test seed overlap')
    old=json.loads((OUT/'strong_study_v3/manifest.json').read_text());check(not ({c['seed'] for c in old['cases']}&{c['seed'] for c in manifest['cases']}),'Reused v3 worlds')
    for c in manifest['cases']:check(identity(c['world'])==c['world_sha256'],'Manifest world hash mismatch '+c['id'])
    for phase in PHASES:
        path=directory/(phase+'.json')
        if not path.exists():errors.append('Missing phase '+phase);continue
        r=json.loads(path.read_text());runs[phase]=r;counts[phase]=len(r['records']);check(r['state']=='complete',phase+': incomplete')
        check(r['study']['manifest_sha256']==digest,phase+': wrong manifest')
        check(identity(r['study']['parameters'])==r['study']['parameter_sha256'],phase+': parameter digest mismatch')
        if not phase.startswith('v4_development_'):check(r['study']['parameter_sha256']==chosen['sha256'],phase+': changed frozen settings')
        config=r['study']['parameters'];cases={c['id']:c for c in r['cases']}
        keys=[(x['case_id'],x['method'],x['repeat']) for x in r['records']];expected={(c['id'],m,j) for c in r['cases'] for m in r['methods'] for j in range(r['repeats'])}
        check(len(keys)==len(set(keys)) and set(keys)==expected,phase+': missing or duplicated trials')
        check(summarize(r)==r['summary'],phase+': summary recomputation mismatch')
        for filename,sha in r['source_sha256'].items():
            p=OUT/r['source_snapshot']/filename
            check(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==sha,phase+': source archive mismatch '+filename)
            if filename in source_lock:check(sha==source_lock[filename],phase+': frozen code mismatch '+filename)
        for c in r['cases']:
            check(identity(c['world'])==c['world_sha256'],phase+': world modified')
            model=OUT/c['model_xml'];check(model.exists() and hashlib.sha256(model.read_bytes()).hexdigest()==c['model_xml_sha256'],phase+': physical model hash mismatch')
        for x in r['records']:
            c=cases[x['case_id']];p=x.get('plan') or {};m=p.get('metrics');tag=f"{phase}/{x['case_id']}/{x['method']}/{x['repeat']}"
            check(x['seed']==c['seed']+x['repeat']*100003,tag+': trial seed mismatch');check(x['status']!='error',tag+': software error '+x.get('error',''))
            if m:
                required=1.25*(m['energy_percent']+c['return_energy_percent'])+6
                admitted=m['estimated_seconds']<=c['deadline_s']+1e-8 and required<=c['battery_percent']+1e-8 and m['terrain_exposure']<=c['risk_budget']+1e-8
                check(bool(p['admissible'])==admitted,tag+': admission mismatch');check(math.isclose(required,p['required_battery_percent'],abs_tol=1e-8),tag+': return allowance mismatch')
                check(math.isclose(quality(m),p['quality_score'],abs_tol=1e-8),tag+': quality mismatch')
                points=np.asarray(p['points']);check(np.allclose(points[0],c['start'],rtol=0,atol=1e-8) and np.allclose(points[-1],c['goal'],rtol=0,atol=1e-8),tag+': endpoint change')
                key=(c['world_sha256'],tuple(map(tuple,points)))
                if key not in verified_routes:
                    if c['world_sha256'] not in graphs:
                        with terrain_context(c['world']):
                            model=world_model(c['world']);data=mujoco.MjData(model);mujoco.mj_forward(model,data);nav=SafeNavigator(model,data,resolution=r['resolution_m']);graph=SceneGraph(nav,True)
                        graphs[c['world_sha256']]=graph
                    graph=graphs[c['world_sha256']]
                    check(all(graph.nav.segment_clear(a,b,margin=graph.nav.tracking_margin) for a,b in zip(points,points[1:])),tag+': unsafe segment')
                    with terrain_context(c['world']):again=graph.metrics(points)
                    for field in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']:check(math.isclose(again[field],m[field],abs_tol=1e-7),tag+': continuous metric mismatch '+field)
                    verified_routes.add(key);geometry_checks+=1;metric_checks+=4
            elif p.get('admissible'):errors.append(tag+': admitted with no metrics')
            opt=p.get('optimizer') or {}
            if opt:
                check(opt['fitness_evaluations']<=240,tag+': candidate budget exceeded')
                if x['method'] in ADVANCED:
                    actual=opt['parameters']
                    for k,v in config['advanced'].items():check(actual.get(k)==v,tag+': v4 parameter mismatch '+k)
                    base=actual['initial_refiner'];expected_initial=DEFAULT_INITIAL if base=='proposed' else config['swarm'][base]
                    check(actual['initial_parameters']==expected_initial,tag+': initial refiner parameters mismatch')
                    check(actual['continuous_polish']==(x['method']!='proposed_v4_no_polish'),tag+': polishing flag mismatch')
                    check(actual['landmark_diversification']==(x['method'].startswith('proposed_v4') and x['method']!='proposed_v4_no_landmarks'),tag+': roadmap flag mismatch')
                elif x['method'] in ['pso','aco','proposed']:
                    for k,v in config['swarm'][x['method']].items():
                        if k!='seed_portfolio':check(opt['parameters'].get(k)==v,tag+': baseline parameter mismatch '+k)
            if p.get('expanded',0)>40000:errors.append(tag+': expansion budget exceeded')
            if p.get('planning_seconds',0)>r['planning_budget_s']+.15:warnings.append(tag+': wall-time overshoot '+str(p['planning_seconds']))
            if x.get('execution'):
                ex=x['execution'];success=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=c['deadline_s'] and ex['minimum_battery_percent']>=2)
                check(x['success']==success,tag+': success mismatch')
                if ex['task_time_s'] is not None:check(math.isclose(x['prediction_validation']['task_time_error_s'],ex['task_time_s']-m['estimated_seconds'],abs_tol=1e-8),tag+': time residual mismatch')
            check(r['energy_model']['status']=='uncalibrated_nominal_simulation',phase+': false hardware calibration claim')
    if all('v4_development_'+n in runs for n in ['default','alternative']):
        for method in manifest['tuned_methods']:
            selected=min(['default','alternative'],key=lambda n:(selection_key(runs['v4_development_'+n],method),n!='default'))
            check(selected==chosen['chosen'][method],'Tuning selection rule mismatch '+method)
    if 'v4_heldout_planning' in runs:
        saved=json.loads((directory/'comparison.json').read_text());check(saved==comparison(runs['v4_heldout_planning']),'Paired report mismatch')
    total=sum(counts.values());check(total==manifest['expected_attempts'],'Wrong campaign attempt total')
    result=dict(version=4,state='passed' if not errors else 'failed',attempts=total,phase_counts=counts,development_worlds=len(dev),heldout_worlds=len(test),unique_routes_collision_checked=geometry_checks,recomputed_continuous_metrics=metric_checks,errors=errors,warnings=warnings,
      scope='Internal provenance, geometry, score, budget and protocol audit. Not hardware validation, an optimality certificate or proof of universal superiority.')
    atomic_json(directory/'audit.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=OUT/'advanced_study_v4');a=p.parse_args();r=audit(a.directory);print(json.dumps(r,indent=2));raise SystemExit(r['state']!='passed')
