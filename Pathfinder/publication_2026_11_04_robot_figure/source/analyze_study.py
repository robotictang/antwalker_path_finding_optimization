"""Independently reconcile, audit and summarize the prospective study."""
from collections import Counter,defaultdict
import csv,hashlib,json,math,statistics,sys
from pathlib import Path
import numpy as np

B=Path(__file__).resolve().parents[1];ROOT=B.parent;M=ROOT/'workbench/mujoco'
sys.path.insert(0,str(M))
import mujoco
from safe_navigation import SafeNavigator
from research.planning import SceneGraph
from research.worlds import terrain_context,world_model,identity
S=M/'outputs/research/publication_ij3c_20261104'


def save_csv(name,rows):
    with (B/'results'/name).open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    mf=json.loads((S/'manifest.json').read_text());locked=json.loads((S/'locked_parameters.json').read_text())
    phases={n:json.loads((S/(n+'.json')).read_text()) for n in mf['expected_phases']}
    errors=[];routes=set();recomputed=0;allrows=[]
    for name,r in phases.items():
        if r['state']!='complete' or len(r['records'])!=mf['expected_phases'][name]:errors.append(name+' completeness')
        if r['study']['manifest_sha256']!=identity(mf):errors.append(name+' manifest')
        keys={(x['case_id'],x['method'],x['repeat']) for x in r['records']}
        expected={(c['id'],m,j) for c in r['cases'] for m in r['methods'] for j in range(r['repeats'])}
        if keys!=expected or len(keys)!=len(r['records']):errors.append(name+' trial keys')
        for source,sha in r['source_sha256'].items():
            if hashlib.sha256((M/'outputs/research'/r['source_snapshot']/source).read_bytes()).hexdigest()!=sha:errors.append(name+' source snapshot '+source)
        for c in r['cases']:
            if identity(c['world'])!=c['world_sha256']:errors.append(name+' world hash')
            p=M/'outputs/research'/c['model_xml']
            if hashlib.sha256(p.read_bytes()).hexdigest()!=c['model_xml_sha256']:errors.append(name+' model hash')
            with terrain_context(c['world']):
                model=world_model(c['world']);data=mujoco.MjData(model);mujoco.mj_forward(model,data)
                graph=SceneGraph(SafeNavigator(model,data,resolution=.25),True)
                for row in [x for x in r['records'] if x['case_id']==c['id']]:
                    p=row['plan'];metrics=p.get('metrics');tag=f"{name}/{c['id']}/{row['method']}/{row['repeat']}"
                    if row['status']=='error':errors.append(tag+' trial error')
                    if metrics:
                        score=sum(w*metrics[k] for w,k in zip([1/50,1/90,1/30,.25/20],['distance_m','estimated_seconds','energy_percent','terrain_exposure']))
                        required=1.25*(metrics['energy_percent']+c['return_energy_percent'])+6
                        admitted=metrics['estimated_seconds']<=c['deadline_s']+1e-8 and metrics['terrain_exposure']<=c['risk_budget']+1e-8 and required<=c['battery_percent']+1e-8
                        if not math.isclose(score,p['quality_score'],abs_tol=1e-8) or admitted!=p['admissible']:errors.append(tag+' score/admission')
                        points=np.asarray(p['points']);key=(c['world_sha256'],tuple(map(tuple,points)))
                        if not np.allclose(points[0],c['start']) or not np.allclose(points[-1],c['goal']):errors.append(tag+' endpoints')
                        if key not in routes:
                            if not all(graph.nav.segment_clear(a,b,margin=graph.nav.tracking_margin) for a,b in zip(points,points[1:])):errors.append(tag+' clearance')
                            again=graph.metrics(points)
                            for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']:
                                if not math.isclose(again[k],metrics[k],abs_tol=1e-7):errors.append(tag+' metric '+k)
                                recomputed+=1
                            routes.add(key)
                    allrows.append(dict(phase=name,world=c['id'],family=c['world']['family'],method=row['method'],repeat=row['repeat'],seed=row['seed'],status=row['status'],
                        admitted=p.get('admissible',False),q=p.get('quality_score'),planning_seconds=p.get('planning_seconds'),**(metrics or {})))
        print('Audited',name,flush=True)
    sources=json.loads((S/'source_lock.json').read_text())
    for name,sha in sources.items():
        if hashlib.sha256((M/name).read_bytes()).hexdigest()!=sha:errors.append('Live source changed '+name)
    development={n:phases['development_'+n] for n in mf['profiles']}
    for method in mf['tuned_methods']:
        def choice(n):
            admitted=[x['plan']['quality_score'] for x in development[n]['records'] if x['method']==method and x['plan'].get('admissible')]
            return (-len(admitted),statistics.mean(admitted) if admitted else math.inf,n!='default')
        if min(development,key=choice)!=locked['choices'][method]:errors.append('Development selection '+method)
    primary=phases['primary'];rows=primary['records'];ix={(x['case_id'],x['repeat'],x['method']):x['plan'] for x in rows}
    summary=[]
    for method in primary['methods']:
        group=[x for x in rows if x['method']==method];admitted=[x for x in group if x['plan'].get('admissible')]
        summary.append(dict(method=method,scheduled=len(group),admitted=len(admitted),
            mean_q_admitted=statistics.mean(x['plan']['quality_score'] for x in admitted) if admitted else None,
            mean_planning_seconds=statistics.mean(x['plan']['planning_seconds'] for x in group),
            max_planning_seconds=max(x['plan']['planning_seconds'] for x in group),statuses=dict(Counter(x['status'] for x in group))))
    paired=[];worldrows=[]
    for baseline in primary['methods']:
        if baseline=='proposed_v4':continue
        counts=Counter();worlds=defaultdict(list)
        for case in primary['cases']:
            for j in range(primary['repeats']):
                a,b=ix[case['id'],j,'proposed_v4'],ix[case['id'],j,baseline]
                if a.get('admissible') and b.get('admissible'):
                    delta=b['quality_score']-a['quality_score'];counts['ties' if abs(delta)<=1e-8 else 'wins' if delta>0 else 'losses']+=1
                    worlds[case['id']].append(100*delta/b['quality_score'])
                else:counts['proposal_only' if a.get('admissible') else 'baseline_only' if b.get('admissible') else 'both_rejected']+=1
        values=[statistics.mean(v) for v in worlds.values()];rng=np.random.default_rng(41104)
        ci=np.percentile(np.mean(rng.choice(values,size=(5000,len(values)),replace=True),axis=1),[2.5,97.5]).tolist() if values else [None,None]
        paired.append(dict(baseline=baseline,paired_worlds=len(values),mean_improvement_percent=statistics.mean(values) if values else None,
            median_improvement_percent=statistics.median(values) if values else None,ci95_low=ci[0],ci95_high=ci[1],
            minimum_world_improvement_percent=min(values) if values else None,maximum_world_improvement_percent=max(values) if values else None,
            worlds_improved_over_0p5_percent=sum(x>.5 for x in values),**{k:counts[k] for k in ['wins','ties','losses','proposal_only','baseline_only','both_rejected']}))
        worldrows.extend(dict(baseline=baseline,world=c,relative_percent=statistics.mean(v)) for c,v in worlds.items())
    save_csv('primary_summary.csv',summary);save_csv('paired_comparisons.csv',paired);save_csv('world_effects.csv',worldrows)
    # A uniform flattened schema preserves no-route records with empty metrics.
    metricnames=['distance_m','estimated_seconds','energy_percent','driving_distance_m','walking_distance_m','transformations','terrain_exposure']
    for row in allrows:
        for k in metricnames:row.setdefault(k,None)
    save_csv('all_640_attempts.csv',allrows)
    report=dict(state='passed' if not errors else 'failed',records=len(allrows),primary_worlds=32,unique_routes_checked=len(routes),metric_values_recomputed=recomputed,
        selected_profiles=locked['choices'],errors=errors,primary_summary=summary,paired_comparisons=paired,
        scope='Internal provenance, geometry, admission and numeric checks. Same procedural generator families, descriptive unadjusted intervals, no execution or physical validation.')
    (B/'results/study_analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return int(bool(errors))


if __name__=='__main__':raise SystemExit(main())
