"""Read-only integrity checks for the version 3 frozen research campaign."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from research.run import ROOT,OUT,atomic_json
from research.worlds import identity
from research.swarm import quality
from research.reliability import selection_key

PHASES=['v3_development_default','v3_development_alternative','v3_heldout_planning','v3_heldout_ablations','v3_old_case_seed_diagnostic','v3_heldout_physics']
def audit(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());locked=json.loads((directory/'locked_parameters.json').read_text());errors=[];warnings=[];counts={};runs={}
    def check(ok,message):
        if not ok:errors.append(message)
    fingerprint=identity(manifest);source_lock=json.loads((directory/'source_lock.json').read_text())
    dev=[c for c in manifest['cases'] if c['split']=='development'];test=[c for c in manifest['cases'] if c['split']=='heldout']
    check(len({c['world_sha256'] for c in manifest['cases']})==len(manifest['cases']),'World identity duplicated')
    check(not ({c['seed'] for c in dev}&{c['seed'] for c in test}),'Development/test seed leakage')
    check(not ({c['world_sha256'] for c in dev}&{c['world_sha256'] for c in test}),'Development/test world leakage')
    for c in manifest['cases']:check(identity(c['world'])==c['world_sha256'],f"World specification hash mismatch: {c['id']}")
    for phase in PHASES:
        path=directory/(phase+'.json')
        if not path.exists():errors.append('Missing phase '+phase);continue
        r=json.loads(path.read_text());runs[phase]=r;counts[phase]=len(r['records'])
        check(r['state']=='complete',phase+': incomplete')
        check(r['study']['manifest_sha256']==fingerprint,phase+': wrong manifest')
        check(r['study']['parameter_sha256']==identity(r['study']['parameters']),phase+': parameter digest mismatch')
        if not phase.startswith('v3_development_'):check(r['study']['parameter_sha256']==locked['sha256'],phase+': changed locked parameters')
        keys=[(x['case_id'],x['method'],x['repeat']) for x in r['records']]
        expected={(c['id'],m,j) for c in r['cases'] for m in r['methods'] for j in range(r['repeats'])}
        check(len(keys)==len(set(keys)) and set(keys)==expected,phase+': duplicate or missing trial keys')
        cases={c['id']:c for c in r['cases']}
        for filename,digest in r['source_sha256'].items():
            archive=OUT/r['source_snapshot']/filename
            check(archive.exists() and hashlib.sha256(archive.read_bytes()).hexdigest()==digest,phase+': source archive mismatch '+filename)
            if filename in source_lock:check(digest==source_lock[filename],phase+': frozen source changed '+filename)
        for c in r['cases']:
            if c.get('world'):
                check(c['world_sha256']==identity(c['world']),phase+': modified world')
                xml=OUT/c['model_xml'];check(xml.exists() and hashlib.sha256(xml.read_bytes()).hexdigest()==c['model_xml_sha256'],phase+': physical model hash mismatch')
        for x in r['records']:
            c=cases[x['case_id']];p=x.get('plan') or {};m=p.get('metrics');tag=f"{phase}/{x['case_id']}/{x['method']}/{x['repeat']}"
            check(x['seed']==c['seed']+x['repeat']*100003,tag+': unpaired seed')
            check(x['status']!='error',tag+': software error '+x.get('error',''))
            if m:
                required=1.25*(m['energy_percent']+c['return_energy_percent'])+6
                admitted=(m['estimated_seconds']<=c['deadline_s']+1e-8 and required<=c['battery_percent']+1e-8 and m['terrain_exposure']<=c['risk_budget']+1e-8)
                check(bool(p['admissible'])==admitted,tag+': admission mismatch')
                check(math.isclose(required,p['required_battery_percent'],abs_tol=1e-8),tag+': return reserve mismatch')
                check(math.isclose(quality(m),p['quality_score'],abs_tol=1e-8),tag+': common score mismatch')
                length=float(np.linalg.norm(np.diff(np.asarray(p['points']),axis=0),axis=1).sum())
                check(math.isclose(length,m['distance_m'],abs_tol=1e-7),tag+': route length mismatch')
            elif p.get('admissible'):errors.append(tag+': admission without route metrics')
            if p.get('planning_seconds',0)>r['planning_budget_s']+.15:warnings.append(tag+': wall budget overshoot '+str(p['planning_seconds']))
            opt=p.get('optimizer') or {}
            if opt:
                method=x['method'];base='proposed' if method.startswith('proposed') else method
                declared=r['study']['parameters'].get(base,{})
                actual=opt['parameters']
                # Operational flags intentionally override the historical profile fields.
                for k,v in declared.items():
                    if k!='seed_portfolio':check(actual.get(k)==v,tag+': parameter mismatch '+k)
                check(actual['adaptive_seed_time']==(method!='proposed_fixed'),tag+': adaptive ablation flag')
                check(actual['seed_portfolio']==(method!='proposed_single'),tag+': portfolio ablation flag')
                check(actual['resource_bound_pruning']==(method!='proposed_unpruned'),tag+': pruning ablation flag')
                check(opt['fitness_evaluations']<=240,tag+': fitness evaluation limit exceeded')
            if x.get('execution'):
                ex=x['execution'];expected_success=bool(ex['success'] and ex['task_time_s'] is not None and ex['task_time_s']<=c['deadline_s'] and ex['minimum_battery_percent']>=2)
                check(x['success']==expected_success,tag+': mission success mismatch')
                residual=x['prediction_validation']
                if ex['task_time_s'] is not None:check(math.isclose(residual['task_time_error_s'],ex['task_time_s']-m['estimated_seconds'],abs_tol=1e-8),tag+': time error mismatch')
        check(r['energy_model']['status']=='uncalibrated_nominal_simulation',phase+': unexpected calibration claim')
    if all('v3_development_'+n in runs for n in manifest['profiles']):
        for method in ['pso','aco','proposed']:
            chosen=min(manifest['profiles'],key=lambda n:(selection_key(runs['v3_development_'+n],method),n!='default'))
            check(chosen==locked['chosen'][method],'Parameter choice does not follow predeclared rule: '+method)
    total=sum(counts.values());check(total==684,'Unexpected total scheduled trial count')
    result=dict(version=3,state='passed' if not errors else 'failed',attempts=total,phase_counts=counts,independent_development_worlds=len(dev),independent_heldout_worlds=len(test),errors=errors,warnings=warnings,
      checks=['Complete and unique paired trial keys','Development/held-out world and seed separation','Archived scientific source hashes and physical model hashes','Frozen parameter selection and ablation switches','Recomputed resource admission, common scores and geometric lengths','Mission success and simulation prediction residuals','Honest uncalibrated energy status'],
      limits='Integrity audit only; not external hardware validation, proof of novelty, or a publication guarantee.')
    atomic_json(directory/'audit.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=OUT/'strong_study_v3');a=p.parse_args();r=audit(a.directory);print(json.dumps(r,indent=2));raise SystemExit(0 if r['state']=='passed' else 1)
