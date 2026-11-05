"""V4 balanced-score development and fresh held-out experiment campaign.

No neural network is trained: two predeclared parameter profiles are tuned on
8 development worlds, then frozen before 24 untouched evaluation worlds.
"""
import argparse,copy,hashlib,json
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from research import advanced
from research.run import ROOT,OUT,run_suite,atomic_json,save_result
from research.worlds import sample_cases,identity
from research.reliability import PROFILES,parameters,selection_key

DIRECTORY=OUT/'advanced_study_v4';FOCAL='proposed_v4'
MAIN=['b1_distance','b2_terrain','b3_energy','b4_weighted','b7_greedy','pso','aco','proposed_v1','proposed','pso_polished','aco_polished',FOCAL]
TUNED=['pso','aco','proposed',FOCAL]
ABLATIONS=[FOCAL,'proposed_v4_no_polish','proposed_v4_no_landmarks']

def profiles():
    result={name:dict(swarm=copy.deepcopy(cfg),advanced=copy.deepcopy(advanced.PARAMETERS)) for name,cfg in PROFILES.items()}
    result['alternative']['advanced'].update(seed_fraction=.55,roadmap_fraction=.25,max_landmarks=60,polish_steps=[.5,.15,.05])
    return result

@contextmanager
def configuration(config):
    old=copy.deepcopy(advanced.PARAMETERS)
    try:
        advanced.PARAMETERS.clear();advanced.PARAMETERS.update(copy.deepcopy(config['advanced']))
        with parameters(config['swarm']):yield
    finally:advanced.PARAMETERS.clear();advanced.PARAMETERS.update(old)

def comparison(result):
    focal=result.get('study',{}).get('focal_method',FOCAL)
    indexed={(r['case_id'],r['repeat'],r['method']):r for r in result['records']};comparisons=[]
    def interval(values):
        if len(values)<2:return None
        arr=np.asarray(values);rng=np.random.default_rng(6104)
        return np.quantile(rng.choice(arr,(5000,len(arr)),replace=True).mean(axis=1),[.025,.975]).tolist()
    for method in result['methods']:
        if method==focal:continue
        counts=dict(wins=0,ties=0,losses=0,both_rejected=0,proposed_only_admitted=0,baseline_only_admitted=0)
        scores=[];relative=[];admissions=[]
        for case in result['cases']:
            local=[];rel=[];adm=[]
            for j in range(result['repeats']):
                p=indexed[case['id'],j,focal].get('plan',{});b=indexed[case['id'],j,method].get('plan',{})
                pa=bool(p.get('admissible'));ba=bool(b.get('admissible'));adm.append(int(pa)-int(ba))
                if pa and ba:
                    delta=b['quality_score']-p['quality_score'];local.append(delta);rel.append(100*delta/b['quality_score'])
                    counts['ties' if abs(delta)<=1e-8 else 'wins' if delta>0 else 'losses']+=1
                else:counts['proposed_only_admitted' if pa else 'baseline_only_admitted' if ba else 'both_rejected']+=1
            admissions.append(float(np.mean(adm)))
            if local:scores.append(float(np.mean(local)));relative.append(float(np.mean(rel)))
        ci=interval(admissions)
        comparisons.append(dict(baseline=method,**counts,paired_admitted_trials=counts['wins']+counts['ties']+counts['losses'],layouts_with_paired_admission=len(scores),
          mean_layout_score_advantage=float(np.mean(scores)) if scores else None,descriptive_layout_bootstrap_95_percent=interval(scores),
          mean_relative_score_improvement_percent=float(np.mean(relative)) if relative else None,relative_improvement_95_percent=interval(relative),
          admission_advantage_pp=100*float(np.mean(admissions)),admission_advantage_95_pp=[100*x for x in ci] if ci else None))
    verdicts=[]
    for c in result['cases']:
        for j in range(result['repeats']):
            rows=[indexed[c['id'],j,m] for m in result['methods']];valid=[r for r in rows if r.get('plan',{}).get('admissible')]
            p=indexed[c['id'],j,focal];pm=p.get('plan',{});others=[r for r in valid if r['method']!=focal]
            if not valid:verdict='All rejected';best=None;winners=[]
            else:
                best=min(r['plan']['quality_score'] for r in valid);winners=[r['method'] for r in valid if abs(r['plan']['quality_score']-best)<=1e-8]
                verdict='V4 rejected' if not pm.get('admissible') else 'V4 best score' if winners==[focal] else 'V4 tied best' if focal in winners else 'Another method scored lower'
            verdicts.append(dict(case=c['id'],repetition=j+1,world_family=c.get('world',{}).get('family','original'),verdict=verdict,
              proposed_score=pm.get('quality_score') if pm.get('admissible') else None,best_admitted_score=best,best_methods=', '.join(winners),
              admitted_methods=len(valid),total_methods=len(rows)))
    return dict(run_id=result['run_id'],focal_method=focal,attempts=len(result['records']),layouts=len(result['cases']),repeats=result['repeats'],comparisons=comparisons,
      summary=result['summary'],case_verdicts=verdicts,
      interpretation='Paired modeled balanced scores on jointly admitted trials. All admission differences include scheduled pairs. Descriptive 95% bootstrap intervals resample worlds after averaging paired seeds (5000 resamples, seed 6104). Uncorrected multiple comparisons; no hardware or universal superiority claim.')

def make_manifest():
    cases=sample_cases(8,1240000,'development')+sample_cases(24,1350000,'heldout')
    return dict(version=4,cases=cases,profiles=profiles(),methods=MAIN,tuned_methods=TUNED,ablation_methods=ABLATIONS,
      budget_seconds=2.,development_repeats=2,test_repeats=3,ablation_case_ids=[f'heldout_{i:02d}' for i in range(1,9)],physics_case_ids=[f'heldout_{i:02d}' for i in range(1,7)],
      sensitivity_case_ids=[f'heldout_{i:02d}' for i in range(1,5)],sensitivity_budgets=[.5,1.],
      selection_rule='Each of PSO ACO v3 proposal and v4: maximize development admission then minimize admitted mean common score; exact ties retain default. Two profiles per tuned method.',
      controls='Polished PSO/ACO inherit their selected baseline parameters and the same selected v4 polishing settings; they are representation controls without an additional tuning search. V4 seed label refiner retains fixed default v3 settings.',
      objective='Unchanged balanced score: D/50 + T/90 + E/30 + 0.25 H/20; feasibility first. No per-method coefficients or outcome-dependent weights.',
      scope='Fresh independent procedural simulation worlds from four families; assisted dynamics and uncalibrated electrical battery model.',
      training='Parameter tuning only, not neural-network or hardware training. Never tune on held-out outcomes.',
      expected_attempts=1232)

def study(directory=DIRECTORY,planning_only=False):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);path=directory/'manifest.json'
    if not path.exists():atomic_json(path,make_manifest())
    manifest=json.loads(path.read_text());fingerprint=identity(manifest)
    names=['research/advanced.py','research/advanced_study.py','research/planning.py','research/swarm.py','research/run.py','research/worlds.py','research/reliability.py','research/execution.py','research/telemetry.py','research/calibration.py','safe_navigation.py','energy_model.py','terrain_profile.py','terrain_classes.py','road_demo.py','multi_place_config.py','tripod_gait.py','hybrid_locomotion.py','hybrid_hexapod_multi_place.xml']
    sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names};lock=directory/'source_lock.json'
    if lock.exists() and json.loads(lock.read_text())!=sources:raise RuntimeError('Scientific sources changed after freeze. Preserve this campaign and use a new directory AND fresh held-out seeds.')
    atomic_json(lock,sources)
    dev=[c for c in manifest['cases'] if c['split']=='development'];test=[c for c in manifest['cases'] if c['split']=='heldout']
    assert not ({c['world_sha256'] for c in dev}&{c['world_sha256'] for c in test})
    old=json.loads((OUT/'strong_study_v3/manifest.json').read_text());assert not ({c['seed'] for c in old['cases']}&{c['seed'] for c in manifest['cases']})
    def phase(name,cases,config,methods,repeats,budget=2.,execute=False):
        dest=directory/(name+'.json')
        if dest.exists():
            r=json.loads(dest.read_text())
            if r['state']!='complete' or r['study']['manifest_sha256']!=fingerprint:raise RuntimeError('Incomplete or mismatched saved phase; preserve records and investigate')
            return r
        meta=dict(version=4,focal_method=FOCAL,phase=name,manifest_sha256=fingerprint,parameter_sha256=identity(config),parameters=copy.deepcopy(config),
          split=cases[0]['split'],scope=manifest['scope'],selection_rule=manifest['selection_rule'],controls=manifest['controls'],
          reproduction=f'python3 -m research.advanced_study --directory {directory}')
        with configuration(config):r=run_suite(suite=name,cases_override=cases,study=meta,methods=methods,repeats=repeats,planning_seconds=budget,execute_physics=execute)
        atomic_json(dest,r);return r
    development={n:phase('v4_development_'+n,dev,cfg,TUNED,2) for n,cfg in manifest['profiles'].items()}
    chosen={m:min(development,key=lambda n:(selection_key(development[n],m),n!='default')) for m in TUNED}
    config=copy.deepcopy(manifest['profiles']['default'])
    for m in ['pso','aco','proposed']:config['swarm'][m]=copy.deepcopy(manifest['profiles'][chosen[m]]['swarm'][m])
    config['advanced']=copy.deepcopy(manifest['profiles'][chosen[FOCAL]]['advanced'])
    selected=dict(chosen=chosen,parameters=config,sha256=identity(config),manifest_sha256=fingerprint)
    frozen=directory/'locked_parameters.json'
    if frozen.exists() and json.loads(frozen.read_text())!=selected:raise RuntimeError('Frozen parameter choice changed')
    atomic_json(frozen,selected)
    primary=phase('v4_heldout_planning',test,config,MAIN,3);report=comparison(primary);atomic_json(directory/'comparison.json',report)
    ablation=phase('v4_heldout_ablations',[c for c in test if c['id'] in manifest['ablation_case_ids']],config,ABLATIONS,3);atomic_json(directory/'ablation_comparison.json',comparison(ablation))
    sensitivity=[]
    for budget in manifest['sensitivity_budgets']:
        r=phase('v4_budget_'+str(budget).replace('.','p'),[c for c in test if c['id'] in manifest['sensitivity_case_ids']],config,MAIN,1,budget)
        sensitivity.append(dict(budget_seconds=budget,run_id=r['run_id'],attempts=len(r['records']),summary=r['summary']))
    physical=None
    if not planning_only:physical=phase('v4_heldout_physics',[c for c in test if c['id'] in manifest['physics_case_ids']],config,MAIN,1,2.,True)
    summary=dict(version=4,focal_method=FOCAL,manifest_sha256=fingerprint,selection=selected,planning_report=report,
      development_attempts=sum(len(r['records']) for r in development.values()),planning_attempts=len(primary['records']),
      ablation_run_id=ablation['run_id'],ablation_attempts=len(ablation['records']),budget_sensitivity=sensitivity,
      physics_run_id=physical['run_id'] if physical else None,physics_summary=physical['summary'] if physical else None,
      scope=manifest['scope'],training=manifest['training'],controls=manifest['controls'])
    atomic_json(directory/'study_summary.json',summary)
    save_result(primary,OUT/(primary['run_id']+'.json'))
    from research.export_dashboard import export
    export(OUT/(primary['run_id']+'.json'),build=True)
    print(json.dumps(summary,indent=2));return primary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=DIRECTORY);p.add_argument('--planning-only',action='store_true');a=p.parse_args();study(a.directory,a.planning_only)
