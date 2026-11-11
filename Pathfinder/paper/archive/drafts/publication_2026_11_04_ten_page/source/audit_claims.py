"""Check retained numerical claims against archived records and source inputs."""
from pathlib import Path
import hashlib,json,re,statistics,xml.etree.ElementTree as ET
from collections import Counter
B=Path(__file__).resolve().parents[1];ROOT=B.parent

def main():
    a=json.loads((B/'results/study_analysis.json').read_text());assert a['state']=='passed' and not a['errors']
    primary=json.loads((B/'raw_study/primary.json').read_text())
    phases={name:json.loads((B/'raw_study'/f'{name}.json').read_text()) for name in ['development_default','development_alternative','primary']}
    assert sum(len(x['records']) for x in phases.values())==640
    assert len(primary['cases'])==32 and len(primary['records'])==576
    assert Counter(c['world']['family'] for c in primary['cases'])==dict(open=8,clutter=8,rough=8,corridor=8)
    previous=set()
    for manifest in (ROOT/'mujoco/outputs/research').glob('*/manifest.json'):
        previous.update(c.get('world_sha256') for c in json.loads(manifest.read_text()).get('cases',[]) if c.get('world_sha256'))
    worlds=json.loads((B/'raw_study/manifest.json').read_text())['cases']
    assert len({c['world_sha256'] for c in worlds})==40 and not {c['world_sha256'] for c in worlds}&previous
    summary={x['method']:x for x in a['primary_summary']}
    for m,count in {'proposed_v4':93,'continuous_pso':94,'pso_polished':93,'aco_polished':93,'proposed_v4_no_landmarks':93,'proposed_v4_no_polish':90}.items():
        group=[r for r in primary['records'] if r['method']==m]
        assert len(group)==96 and sum(bool(r['plan']['admissible']) for r in group)==count==summary[m]['admitted']
        assert all(r['status'] in ['found','resource_rejected'] for r in group)
        assert max(r['plan']['optimizer']['fitness_evaluations'] for r in group)<=240
        assert abs(statistics.mean(r['plan']['planning_seconds'] for r in group)-summary[m]['mean_planning_seconds'])<1e-12
    effects={r['baseline']:r for r in a['paired_comparisons']};q=effects['continuous_pso']
    assert (q['wins'],q['ties'],q['losses'],q['proposal_only'],q['baseline_only'],q['both_rejected'])==(33,27,33,0,1,2)
    assert q['ci95_low']<0<q['ci95_high'] and q['paired_worlds']==31 and q['median_improvement_percent']==0
    assert effects['proposed_v4_no_polish']['losses']==0
    probe=json.loads((B/'results/realism_probe.json').read_text());assert probe['state']=='complete' and len(probe['records'])==16
    corrected=json.loads((B/'results/corrected_gravity_probe.json').read_text());assert corrected['state']=='complete'
    assert len(corrected['records'])==4
    for r in corrected['records']:
        assert r['realized_settings']['enabled_before']==18
        assert r['realized_settings']['enabled_after']==0
        assert not any(r['realized_settings']['values_after'])
    probe['records']=[r for r in probe['records'] if r['gravity_compensation']]+corrected['records']
    conditions=[]
    for scale,gc,outcome in [(1.,True,'arrived'),(.5,True,'arrived'),(0.,True,'timeout'),(0.,False,'timeout')]:
        rows=[x for x in probe['records'] if x['assistance']==scale and x['gravity_compensation']==gc]
        assert len(rows)==4 and all(x['execution']['outcome']==outcome for x in rows)
        conditions.append(dict(scale=scale,gravity_compensation=gc,count=4,outcome=outcome))
    model=json.loads((B/'results/model_audit.json').read_text())
    assert abs(model['source_total_link_mass_kg']-97.52)<1e-8
    assert abs(model['mujoco_robot_subtree_mass_kg']-113.32)<.001
    assert model['source_revolute_joints']==18 and model['mujoco_actuators']==23
    for name,sha in json.loads((B/'raw_study/source_lock.json').read_text()).items():
        assert hashlib.sha256((ROOT/'workbench/mujoco'/name).read_bytes()).hexdigest()==sha
    for name in phases:
        assert (B/'raw_study'/f'{name}.json').read_bytes()==(ROOT/'workbench/mujoco/outputs/research/publication_ij3c_20261104'/f'{name}.json').read_bytes()
    doc=(B/'IJ3C_Manuscript.md').read_text()
    assert not re.search(r'(?i)tutorial|review draft|not submitted|maybe|perhaps|might|pending',doc)
    ledger=[
        dict(claim='640 planning records; 32 primary worlds; 576 primary records; 8 worlds per family',support=['raw_study/manifest.json','raw_study/development_default.json','raw_study/development_alternative.json','raw_study/primary.json'],kind='checked empirical counts'),
        dict(claim='Per-method admissions and mean search times',support=['results/primary_summary.csv','raw_study/primary.json'],kind='recomputed counts and arithmetic; times are recorded observations'),
        dict(claim='0.690% conditional PSO-C effect, zero median, interval spans zero; 33/27/33 pairs',support=['results/paired_comparisons.csv','results/world_effects.csv','results/study_analysis.json'],kind='checked saved descriptive analysis; whole-world bootstrap; no universal or causal performance claim'),
        dict(claim='Component-removal outcomes, including 3 fewer admissions without polishing',support=['results/paired_comparisons.csv','raw_study/primary.json'],kind='checked paired counts and scores; no post-test retuning'),
        dict(claim='16 realized-condition diagnostic comparisons from 12 original and 4 corrected executions; full/blended 4 arrivals each; zero assistance 4 timeouts in each GC condition',support=['results/realism_probe_protocol.json','results/realism_probe.json','results/realism_probe_input_v6.json','results/corrected_gravity_probe.json','source/corrected_gravity_probe.py'],kind='original mislabeled GC-off condition excluded; corrected body settings verified; four previously observed routes; no hardware inference'),
        dict(claim='URDF 97.52 kg versus compiled robot about 113.32 kg; 18 leg joints and 23 model actuators',support=['results/model_audit.json','source/model_audit.py','../hexapod.urdf','../workbench/mujoco/hybrid_hexapod_multi_place.xml'],kind='source and compiled-model specification; not physical measurements'),
        dict(claim='Score weights, battery coefficients, speed/clearance limits, assistance equations and planner parameters',support=['raw_study/source_lock.json','raw_study/locked_parameters.json','../workbench/mujoco/research/planning.py','../workbench/mujoco/research/advanced.py','../workbench/mujoco/research/swarm.py','../workbench/mujoco/research/continuous_pso.py','../workbench/mujoco/research/execution.py','../workbench/mujoco/research/worlds.py','../workbench/mujoco/energy_model.py','../workbench/mujoco/safe_navigation.py'],kind='configured definitions and assumptions; explicitly not calibrated physical quantities'),
        dict(claim='Primary figure uses the first world and repetition zero',support=['raw_study/primary.json','source/build_manuscript.py'],kind='fixed presentation selection independent of favorable score'),
        dict(claim='Numeric/geometry audit: 640 records, 187 route geometries, 748 metric values',support=['results/study_analysis.json','source/analyze_study.py','qa/study_audit_recheck.log'],kind='internal consistency audit; not independent laboratory replication')]
    ledger.append(dict(claim='Family admissions, computation counts, omission means and contact telemetry',support=['results/expanded_analysis.json','source/extended_content.py','results/corrected_gravity_probe.json','results/world_effects.csv','raw_study/primary.json'],kind='post-hoc descriptive extension; unchanged primary sample; not new confirmatory trials'))
    for row in ledger:
        for support in row['support']:assert (B/support).is_file(),support
    report=dict(state='passed',claims=ledger,diagnostic_conditions=conditions,
        excluded_claims=['Real electrical or battery savings','Hardware autonomy or walking stability','Global optimality','Universal planner superiority','General hardware failure probability','Independent laboratory replication'],
        author_information='Still required; not invented',manuscript_sha256=hashlib.sha256((B/'IJ3C_Manuscript.md').read_bytes()).hexdigest(),
        scope='Checks evidence support for retained quantitative statements and the implementation descriptions; empirical evidence is bounded by the stated model and protocol.')
    (B/'qa/claim_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Evidence supporting manuscript claims','', 'The retained empirical results are conditional on the declared simulator and protocol. Configuration values are identified as assumptions rather than measurements.','', '| Retained claim | Evidence | Scope |','|---|---|---|']
    for row in ledger:lines.append('| '+row['claim']+' | '+'; '.join('['+p+']('+p+')' for p in row['support'])+' | '+row['kind']+' |')
    lines+=['','The paper excludes claims of real battery savings, hardware autonomy, global optimality, universal superiority and independent laboratory replication. Required author information remains outside this numerical audit.']
    (B/'Evidence_Map.md').write_text('\n'.join(lines)+'\n')
    print('Passed: 10 evidence groups, source lock, campaign copies, admissions, recorded times, comparison categories, model specifications and all 16 realized-condition diagnostic outcomes (including four corrected replays).')

if __name__=='__main__':main()
