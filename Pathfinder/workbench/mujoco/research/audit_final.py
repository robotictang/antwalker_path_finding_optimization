"""Read-only provenance and geometry audit of the frozen V6 final study."""
import json,math,hashlib
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from research.run import ROOT,OUT,atomic_json,summarize
from research.worlds import identity,world_model,terrain_context
from research.planning import SceneGraph
from research.reliability import selection_key

def audit(directory=OUT/'final_validation_v6',partial=False):
    d=Path(directory);mf=json.loads((d/'manifest.json').read_text());lock=json.loads((d/'source_lock.json').read_text());selected=json.loads((d/'locked_parameters.json').read_text());native=json.loads((d/'native_dependency.json').read_text())
    errors=[];warnings=[];counts={};unique=set();graphs={};checked=0;metrics=0;runs={};physics_executions=0
    def check(condition,label):
        if not condition:errors.append(label)
    names=['v6_development_default','v6_development_alternative','v6_primary','v6_weight_distance','v6_weight_time','v6_weight_energy','v6_weight_terrain','v6_budget_0p5','v6_budget_1p0','v6_physics_safe','v6_physics_legacy','v6_physics_reduced']
    if partial:names=[n for n in names if (d/(n+'.json')).exists()]
    check(identity(selected['parameters'])==selected['sha256'],'Selected parameter hash')
    check(len({c['world_sha256'] for c in mf['cases']})==56,'56 unique development/test worlds')
    old={'cases':sum([json.loads((OUT/d/'manifest.json').read_text())['cases'] for d in ['advanced_study_v4','validation_extension_v5']],[])}
    check(not ({c['world_sha256'] for c in old['cases']}&{c['world_sha256'] for c in mf['cases']}),'V6 versus V4/V5 world disjointness')
    for name in names:
        p=d/(name+'.json')
        if not p.exists():errors.append('Missing phase '+name);continue
        r=json.loads(p.read_text());runs[name]=r;counts[name]=len(r['records']);check(r['state']=='complete',name+' complete')
        check(r['study']['manifest_sha256']==identity(mf),name+' manifest hash')
        check(r['study']['native_dependency_sha256']==identity(native),name+' native dependency hash')
        expected_weights=np.array([1/50,1/90,1/30,.25/20])*np.asarray(mf['weights'][r['study']['weight_profile']])
        check(np.allclose(r['study']['score_weights'],expected_weights,rtol=0,atol=1e-14),name+' predeclared weights')
        check(identity(r['study']['parameters'])==r['study']['parameter_sha256'],name+' parameter hash')
        if not name.startswith('v6_development'):check(r['study']['parameters']==selected['parameters'],name+' frozen parameters')
        keys=[(x['case_id'],x['method'],x['repeat']) for x in r['records']]
        expected={(c['id'],m,j) for c in r['cases'] for m in r['methods'] for j in range(r['repeats'])}
        check(len(keys)==len(set(keys)) and set(keys)==expected,name+' complete unique trial keys')
        check(summarize(r)==r['summary'],name+' summary recomputation')
        for source,sha in lock.items():
            snap=OUT/r['source_snapshot']/source
            check(r['source_sha256'].get(source)==sha and snap.exists() and hashlib.sha256(snap.read_bytes()).hexdigest()==sha,name+' archived source '+source)
        cases={c['id']:c for c in r['cases']}
        for c in r['cases']:
            check(identity(c['world'])==c['world_sha256'],name+' world hash '+c['id'])
            xml=OUT/c['model_xml'];check(xml.exists() and hashlib.sha256(xml.read_bytes()).hexdigest()==c['model_xml_sha256'],name+' model hash '+c['id'])
        for x in r['records']:
            c=cases[x['case_id']];p=x.get('plan',{});m=p.get('metrics');tag=f"{name}/{x['case_id']}/{x['method']}/{x['repeat']}"
            check(x['status']!='error',tag+' error '+x.get('error',''))
            check(x['seed']==c['seed']+x['repeat']*100003,tag+' paired seed')
            opt=p.get('optimizer',{})
            check(opt.get('fitness_evaluations',0)<=mf['candidate_cap'],tag+' candidate ceiling')
            check(p.get('expanded',0)<=40000,tag+' expansion ceiling')
            if p.get('planning_seconds',0)>r['planning_budget_s']+.15:warnings.append(tag+' wall overshoot')
            if m:
                weights=r['study']['score_weights'];score=sum(a*b for a,b in zip(weights,[m['distance_m'],m['estimated_seconds'],m['energy_percent'],m['terrain_exposure']]))
                required=1.25*(m['energy_percent']+c['return_energy_percent'])+6
                admit=m['estimated_seconds']<=c['deadline_s']+1e-8 and m['terrain_exposure']<=c['risk_budget']+1e-8 and required<=c['battery_percent']+1e-8
                check(math.isclose(score,p['quality_score'],abs_tol=1e-9),tag+' independent scalar score')
                check(math.isclose(required,p['required_battery_percent'],abs_tol=1e-8) and bool(p['admissible'])==admit,tag+' admission')
                points=np.asarray(p['points']);check(np.allclose(points[0],c['start'],rtol=0,atol=1e-8) and np.allclose(points[-1],c['goal'],rtol=0,atol=1e-8),tag+' endpoints')
                key=(c['world_sha256'],tuple(map(tuple,points)))
                if key not in unique:
                    with terrain_context(c['world']):
                        if c['world_sha256'] not in graphs:
                            model=world_model(c['world']);data=mujoco.MjData(model);mujoco.mj_forward(model,data);graphs[c['world_sha256']]=SceneGraph(SafeNavigator(model,data,resolution=.25),True)
                        g=graphs[c['world_sha256']]
                        check(all(g.nav.segment_clear(a,b,margin=g.nav.tracking_margin) for a,b in zip(points,points[1:])),tag+' exact collision geometry')
                        again=g.metrics(points)
                    for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']:check(math.isclose(m[k],again[k],abs_tol=1e-7),tag+' metric '+k);metrics+=1
                    unique.add(key);checked+=1
                check(p.get('continuous_metric_calls',0)>=opt.get('fitness_evaluations',0),tag+' full metric-call instrumentation')
            else:check(not p.get('admissible'),tag+' no false admission without metrics')
            if x['method'].startswith('ompl_'):
                check(opt.get('library')=='OMPL' and opt.get('library_version')=='2.0.1',tag+' actual native library')
                check(opt.get('worker_exitcode')==0,tag+' native process exit')
                if m:check(opt.get('native_exact_solution',False) or (x['method']=='ompl_seeded_rrtstar' and 'found' in opt.get('seed_status',[])),tag+' exact path or shared seed')
            if name.startswith('v6_physics'):
                original=next(z for z in runs['v6_primary']['records'] if z['case_id']==x['case_id'] and z['method']==x['method'] and z['repeat']==0)
                check(x['plan']==original['plan'],tag+' exact frozen planning replay')
                check(x['plan_origin_run']==runs['v6_primary']['run_id'],tag+' replay origin')
            if x.get('execution'):
                physics_executions+=1;ex=x['execution'];check(ex['assistance_scale']==r['assistance_scale'],tag+' assistance logging')
                check(ex['tracking_policy']==r['tracking_policy'],tag+' tracking policy logging')
                success=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=c['deadline_s'] and ex['minimum_battery_percent']>=2)
                check(success==x['success'],tag+' execution success')
                if ex['task_time_s'] is not None:check(math.isclose(x['prediction_validation']['task_time_error_s'],ex['task_time_s']-m['estimated_seconds'],abs_tol=1e-8),tag+' prediction residual')
        print('Audited '+name,flush=True)
    if all('v6_development_'+n in runs for n in mf['profiles']):
        for m in mf['methods']:
            actual=min(mf['profiles'],key=lambda n:(selection_key(runs['v6_development_'+n],m),n!='default'))
            check(selected['chosen'][m]==actual,'Independent development selection '+m)
    if not partial:
        check(sum(counts.values())==1200,'1200 scheduled attempts');check(len(counts)==12,'Twelve phases')
    for source,sha in lock.items():check(hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha,'Live code remained frozen '+source)
    native=json.loads((d/'native_dependency.json').read_text())
    for name,sha in native['binary_sha256'].items():check(hashlib.sha256((ROOT/'research_vendor'/name).read_bytes()).hexdigest()==sha,'Native binary '+name)
    check(sum(c.get('regime')=='shifted' for c in mf['cases'])==24,'24 shifted worlds')
    report=dict(state=('partial validated' if partial else 'passed') if not errors else 'failed',attempts=sum(counts.values()),phase_counts=counts,unique_routes_collision_checked=checked,recomputed_metrics=metrics,physics_executions=physics_executions,errors=errors,warnings=warnings,
      scope='Internal protocol, archived provenance, geometry, resource and numerical validation; no hardware or electrical validation')
    atomic_json(d/('audit_partial.json' if partial else 'audit.json'),report);return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--partial',action='store_true');p.add_argument('--directory',type=Path,default=OUT/'final_validation_v6');a=p.parse_args()
    r=audit(directory=a.directory,partial=a.partial);print(json.dumps(r,indent=2));raise SystemExit(r['state']=='failed')
