"""Read-only provenance and geometry audit of the prospective V5 extension."""
import json,math,hashlib
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from research.run import ROOT,OUT,atomic_json,summarize
from research.worlds import identity,world_model,terrain_context
from research.planning import SceneGraph
from research.reliability import selection_key

def audit(directory=OUT/'validation_extension_v5'):
    d=Path(directory);mf=json.loads((d/'manifest.json').read_text());lock=json.loads((d/'source_lock.json').read_text());selected=json.loads((d/'locked_parameters.json').read_text())
    errors=[];warnings=[];counts={};unique=set();graphs={};checked=0;metrics=0;runs={};physics_executions=0
    def check(condition,label):
        if not condition:errors.append(label)
    names=['v5_development_default','v5_development_alternative','v5_fresh_planning','v5_feature_ablations','v5_budget_0p5','v5_budget_1p0','v5_candidate_cap80','v5_physics_assistance_1p0','v5_physics_assistance_0p5']
    check(identity(selected['parameters'])==selected['sha256'],'Selected parameter hash')
    check(len({c['world_sha256'] for c in mf['cases']})==56,'56 unique development/test worlds')
    old=json.loads((OUT/'advanced_study_v4/manifest.json').read_text())
    check(not ({c['world_sha256'] for c in old['cases']}&{c['world_sha256'] for c in mf['cases']}),'V4/V5 world disjointness')
    for name in names:
        p=d/(name+'.json')
        if not p.exists():errors.append('Missing phase '+name);continue
        r=json.loads(p.read_text());runs[name]=r;counts[name]=len(r['records']);check(r['state']=='complete',name+' complete')
        check(r['study']['manifest_sha256']==identity(mf),name+' manifest hash')
        check(identity(r['study']['parameters'])==r['study']['parameter_sha256'],name+' parameter hash')
        if not name.startswith('v5_development'):check(r['study']['parameters']==selected['parameters'],name+' frozen parameters')
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
            check(opt.get('fitness_evaluations',0)<=r['study']['candidate_cap'],tag+' candidate ceiling')
            check(p.get('expanded',0)<=40000,tag+' expansion ceiling')
            if p.get('planning_seconds',0)>r['planning_budget_s']+.15:warnings.append(tag+' wall overshoot')
            if m:
                score=m['distance_m']/50+m['estimated_seconds']/90+m['energy_percent']/30+.25*m['terrain_exposure']/20
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
            if x.get('execution'):
                physics_executions+=1;ex=x['execution'];check(ex['assistance_scale']==r['assistance_scale'],tag+' assistance logging')
                success=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=c['deadline_s'] and ex['minimum_battery_percent']>=2)
                check(success==x['success'],tag+' execution success')
                if ex['task_time_s'] is not None:check(math.isclose(x['prediction_validation']['task_time_error_s'],ex['task_time_s']-m['estimated_seconds'],abs_tol=1e-8),tag+' prediction residual')
        print('Audited '+name,flush=True)
    if all('v5_development_'+n in runs for n in mf['profiles']):
        for m in mf['methods']:
            actual=min(mf['profiles'],key=lambda n:(selection_key(runs['v5_development_'+n],m),n!='default'))
            check(selected['chosen'][m]==actual,'Independent development selection '+m)
    check(sum(counts.values())==800,'800 scheduled attempts');check(len(counts)==9,'Nine phases')
    for source,sha in lock.items():check(hashlib.sha256((ROOT/source).read_bytes()).hexdigest()==sha,'Live code remained frozen '+source)
    report=dict(state='passed' if not errors else 'failed',attempts=sum(counts.values()),phase_counts=counts,unique_routes_collision_checked=checked,recomputed_metrics=metrics,physics_executions=physics_executions,errors=errors,warnings=warnings,
      scope='Internal protocol, archived provenance, geometry, resource and numerical validation; no hardware or electrical validation')
    atomic_json(d/'audit.json',report);return report

if __name__=='__main__':
    r=audit();print(json.dumps(r,indent=2));raise SystemExit(r['state']!='passed')
