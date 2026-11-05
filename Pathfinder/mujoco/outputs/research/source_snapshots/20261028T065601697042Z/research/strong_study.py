"""Version 3 study on new, independently seeded procedural terrain worlds.

Frozen manifests, equal tuning opportunity, paired methods, explicit ablations,
small-graph exact checks and separate assisted-physics validation.
"""
import argparse,copy,hashlib,json,statistics,time
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from research.run import ROOT,OUT,atomic_json,run_suite,save_result
from research.worlds import make_world,world_model,terrain_context,identity,FAMILIES,sample_cases
from research.reliability import PROFILES,parameters,selection_key
from research.reference_validation import validate as reference_validation

DIRECTORY=OUT/'strong_study_v3'
MAIN_METHODS=['b1_distance','b3_energy','b7_greedy','pso','aco','proposed']
ABLATIONS=['proposed','proposed_fixed','proposed_single','proposed_unpruned']

def make_manifest():
    cases=sample_cases(8,830000,'development')+sample_cases(24,940000,'heldout')
    return dict(version=3,cases=cases,profiles=copy.deepcopy(PROFILES),budget_seconds=2.,development_repeats=2,test_repeats=3,
      main_methods=MAIN_METHODS,ablation_methods=ABLATIONS,ablation_case_ids=[f'heldout_{i:02d}' for i in range(1,9)],
      physics_case_ids=[f'heldout_{i:02d}' for i in range(1,7)],
      selection_rule='For each of PSO ACO proposed: maximize development admission, then minimize admitted mean common score; exact ties retain default. Two profiles and equal paired trials per method.',
      scope='Independently generated physical obstacle and shallow-terrain worlds from four procedural families; simulated distribution only, not real-world validation.',
      energy_calibration='Nominal simulation coefficients remain uncalibrated. External electrical measurements are required before applying a hardware-fitted profile.',
      protocol='Cases and physics/ablation subsets fixed before tuning. Keep all rejections, timeouts and ties; do not retune on held-out outcomes.')

def comparison(result):
    keys={(r['case_id'],r['repeat'],r['method']):r for r in result['records']};pairs=[]
    for method in result['methods']:
        if method=='proposed':continue
        counts=dict(wins=0,ties=0,losses=0,both_rejected=0,proposed_only_admitted=0,baseline_only_admitted=0)
        score_means=[];admission_deltas=[]
        for case in result['cases']:
            local=[];admissions=[]
            for repeat in range(result['repeats']):
                p=keys[case['id'],repeat,'proposed'].get('plan',{});b=keys[case['id'],repeat,method].get('plan',{})
                pa=bool(p.get('admissible'));ba=bool(b.get('admissible'));admissions.append(int(pa)-int(ba))
                if pa and ba:
                    delta=b['quality_score']-p['quality_score'];local.append(delta)
                    counts['ties' if abs(delta)<=1e-8 else 'wins' if delta>0 else 'losses']+=1
                else:counts['proposed_only_admitted' if pa else 'baseline_only_admitted' if ba else 'both_rejected']+=1
            admission_deltas.append(float(np.mean(admissions)))
            if local:score_means.append(float(np.mean(local)))
        def interval(values):
            if len(values)<2:return None
            rng=np.random.default_rng(4100);values=np.asarray(values)
            return np.quantile(rng.choice(values,(5000,len(values)),replace=True).mean(axis=1),[.025,.975]).tolist()
        pairs.append(dict(baseline=method,**counts,paired_admitted_trials=counts['wins']+counts['ties']+counts['losses'],
          layouts_with_paired_admission=len(score_means),mean_layout_score_advantage=float(np.mean(score_means)) if score_means else None,
          descriptive_layout_bootstrap_95_percent=interval(score_means),admission_advantage_pp=100*float(np.mean(admission_deltas)),
          admission_advantage_95_pp=[100*x for x in interval(admission_deltas)] if len(admission_deltas)>1 else None))
    return dict(run_id=result['run_id'],attempts=len(result['records']),layouts=len(result['cases']),repeats=result['repeats'],comparisons=pairs,summary=result['summary'],
      interpretation='Paired comparison resamples whole independent generated worlds after averaging seeds. Route quality is conditional on joint admission; admission advantage uses all scheduled pairs. Descriptive simulation evidence, not a hardware or universal superiority claim.')

def study(directory=DIRECTORY,planning_only=False):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);path=directory/'manifest.json'
    if not path.exists():atomic_json(path,make_manifest())
    manifest=json.loads(path.read_text());fingerprint=identity(manifest)
    current_sources={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [ROOT/'research'/n for n in ['planning.py','swarm.py','run.py','worlds.py','calibration.py','strong_study.py','reference_validation.py','execution.py','telemetry.py','reliability.py']]}
    source_lock=directory/'source_lock.json'
    if source_lock.exists() and json.loads(source_lock.read_text())!=current_sources:raise RuntimeError('Study code changed after the manifest was frozen; use a new study version, retaining prior evidence')
    atomic_json(source_lock,current_sources)
    dev=[c for c in manifest['cases'] if c['split']=='development'];test=[c for c in manifest['cases'] if c['split']=='heldout']
    assert not ({c['world_sha256'] for c in dev}&{c['world_sha256'] for c in test})
    def phase(label,cases,config,methods,repeats,execute=False):
        saved=directory/(label+'.json')
        if saved.exists():
            result=json.loads(saved.read_text())
            if result['state']!='complete' or result['study']['manifest_sha256']!=fingerprint:raise RuntimeError('An earlier phase is incomplete or belongs to another manifest')
            return result
        meta=dict(version=3,manifest=str(path),manifest_sha256=fingerprint,phase=label,split=cases[0].get('split','diagnostic'),parameters=copy.deepcopy(config),
          parameter_sha256=identity(config),selection_rule=manifest['selection_rule'],scope=manifest['scope'],
          reproduction=f'python3 -m research.strong_study --directory {directory}',energy_calibration=manifest['energy_calibration'])
        with parameters(config):result=run_suite(suite=label,methods=methods,repeats=repeats,planning_seconds=manifest['budget_seconds'],execute_physics=execute,cases_override=cases,study=meta)
        atomic_json(saved,result);return result
    tuning={name:phase('v3_development_'+name,dev,config,['pso','aco','proposed'],manifest['development_repeats']) for name,config in manifest['profiles'].items()}
    chosen={method:min(tuning,key=lambda p:(selection_key(tuning[p],method),p!='default')) for method in ['pso','aco','proposed']}
    locked=copy.deepcopy(manifest['profiles']['default'])
    for method,profile in chosen.items():locked[method]=copy.deepcopy(manifest['profiles'][profile][method])
    selection=dict(chosen=chosen,parameters=locked,sha256=identity(locked),manifest_sha256=fingerprint)
    frozen=directory/'locked_parameters.json'
    if frozen.exists() and json.loads(frozen.read_text())!=selection:raise RuntimeError('Frozen parameter selection changed')
    atomic_json(frozen,selection)
    primary=phase('v3_heldout_planning',test,locked,manifest['main_methods'],manifest['test_repeats'])
    report=comparison(primary);atomic_json(directory/'comparison.json',report)
    ablation=phase('v3_heldout_ablations',[c for c in test if c['id'] in manifest['ablation_case_ids']],locked,manifest['ablation_methods'],manifest['test_repeats'])
    atomic_json(directory/'ablation_comparison.json',comparison(ablation))
    # Already-inspected old cases are explicitly a development diagnostic, never new confirmation evidence.
    old=json.loads((OUT/'reliability_v1/manifest.json').read_text())
    diagnostics=[{**c,'id':'diagnostic_'+c['id'],'split':'diagnostic'} for c in old['cases'] if c['id'] in ['heldout_01','heldout_07']]
    diagnostic=phase('v3_old_case_seed_diagnostic',diagnostics,locked,['pso','aco','proposed','proposed_fixed'],3)
    reference=reference_validation();atomic_json(directory/'exact_reference_validation.json',reference)
    physical=None
    if not planning_only:physical=phase('v3_heldout_physics',[c for c in test if c['id'] in manifest['physics_case_ids']],locked,manifest['main_methods'],1,True)
    summary=dict(version=3,manifest_sha256=fingerprint,selection=selection,planning_report=report,
      development_attempts=sum(len(r['records']) for r in tuning.values()),planning_attempts=len(primary['records']),
      ablation_run_id=ablation['run_id'],ablation_attempts=len(ablation['records']),diagnostic_run_id=diagnostic['run_id'],diagnostic_attempts=len(diagnostic['records']),
      physics_run_id=physical['run_id'] if physical else None,physics_summary=physical['summary'] if physical else None,
      reference_validation=dict(state=reference['state'],cases=reference['cases'],mismatches=len(reference['mismatches'])),
      energy_calibration=manifest['energy_calibration'],scope=manifest['scope'])
    atomic_json(directory/'study_summary.json',summary)
    save_result(primary,OUT/(primary['run_id']+'.json'))
    from research.export_dashboard import export
    export(OUT/(primary['run_id']+'.json'),build=True)
    print(json.dumps(summary,indent=2));return primary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--directory',type=Path,default=DIRECTORY);p.add_argument('--planning-only',action='store_true');a=p.parse_args();study(a.directory,a.planning_only)
