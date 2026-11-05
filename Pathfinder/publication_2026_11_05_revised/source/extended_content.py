"""Post-hoc descriptive analyses of unchanged archived primary records."""
import csv,json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
METHODS=['proposed_v4','pso_polished','aco_polished','continuous_pso','proposed_v4_no_landmarks','proposed_v4_no_polish']
NAMES=dict(zip(METHODS,['V4','PSO-P','ACO-P','PSO-C','V4 noL','V4 noP']))
FAMILIES=['open','clutter','rough','corridor']

def expand(B,texts,tables,figures):
    primary=json.loads((B/'raw_study/primary.json').read_text());cases={c['id']:c for c in primary['cases']};records=primary['records']
    effects=list(csv.DictReader((B/'results/world_effects.csv').open()))
    family=[];computation=[];sensitivity=[]
    for method in METHODS:
        rows=[r for r in records if r['method']==method]
        for f in FAMILIES:
            group=[r for r in rows if cases[r['case_id']]['world']['family']==f]
            assert len(group)==24
            family.append(dict(method=method,family=f,attempts=len(group),admitted=sum(bool(r['plan']['admissible']) for r in group)))
        times=[r['plan']['planning_seconds'] for r in rows];evaluations=[r['plan']['optimizer']['fitness_evaluations'] for r in rows]
        checks=[r['plan']['optimizer']['visibility_checks'] for r in rows]
        computation.append(dict(method=method,median_seconds=float(np.median(times)),p90_seconds=float(np.quantile(times,.9)),maximum_seconds=max(times),median_evaluations=float(np.median(evaluations)),maximum_evaluations=max(evaluations),at_ceiling=sum(e==240 for e in evaluations),median_visibility_checks=float(np.median(checks))))
    for method in METHODS[1:]:
        rows=[r for r in effects if r['baseline']==method];v=np.array([float(r['relative_percent']) for r in rows]);omissions=(v.sum()-v)/(len(v)-1)
        sensitivity.append(dict(method=method,n=len(v),mean_percent=float(v.mean()),median_percent=float(np.median(v)),max_world=rows[int(np.argmax(v))]['world'],maximum_percent=float(v.max()),minimum_omission_mean_percent=float(omissions.min()),maximum_omission_mean_percent=float(omissions.max())))
    preparation=np.array([c['total_preparation_seconds'] for c in cases.values()])
    original=json.loads((B/'results/realism_probe.json').read_text())
    correction=json.loads((B/'results/corrected_gravity_probe.json').read_text());assert correction['state']=='complete'
    realized=[r for r in original['records'] if r['gravity_compensation']]+correction['records'];assert len(realized)==16
    for r in correction['records']:
        assert r['realized_settings']['enabled_before']==18 and r['realized_settings']['enabled_after']==0
        assert all(v==0 for v in r['realized_settings']['values_after'])
    conditions=[]
    for scale,gc,label in [(1.,True,'Full + GC'),(.5,True,'Blend + GC'),(0.,True,'Zero + GC'),(0.,False,'Zero, no GC')]:
        rows=[r for r in realized if r['assistance']==scale and r['gravity_compensation']==gc];assert len(rows)==4
        ex=[r['execution'] for r in rows]
        conditions.append(dict(label=label,rows=rows,arrived=sum(r['outcome']=='arrived' for r in ex),timeouts=sum(r['outcome']=='timeout' for r in ex),distance_range=[min(r['distance_m'] for r in ex),max(r['distance_m'] for r in ex)],elapsed_range=[min(r['elapsed_s'] for r in ex),max(r['elapsed_s'] for r in ex)],mean_contact_range=[min(r['mean_contact_feet'] for r in ex),max(r['mean_contact_feet'] for r in ex)],no_contact_range=[min(r['no_foot_contact_fraction'] for r in ex),max(r['no_foot_contact_fraction'] for r in ex)],tilt_range=[min(r['max_tilt_deg'] for r in ex),max(r['max_tilt_deg'] for r in ex)]))
    assert all(c['arrived']==4 for c in conditions[:2]);assert all(c['timeouts']==4 for c in conditions[2:])
    assert all(r['execution']['no_foot_contact_fraction']==1 and r['execution']['mean_contact_feet']==0 for c in conditions[:2] for r in c['rows'])
    report=dict(scope='Post-hoc descriptive extensions of frozen records, plus corrected gravity diagnostic',primary_sha256=hashlib.sha256((B/'raw_study/primary.json').read_bytes()).hexdigest(),family=family,computation=computation,sensitivity=sensitivity,preparation=dict(median_seconds=float(np.median(preparation)),maximum_seconds=float(preparation.max())),diagnostic_conditions=[{k:v for k,v in c.items() if k!='rows'} for c in conditions],excluded_records='Four originally requested GC-off runs: initialization restored 18 compensated limb bodies; superseded only for no-GC comparison',corrected_executions=4,original_executions_retained=16)
    (B/'results/expanded_analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    tables['TABLE_PROBE']=('Table 7. Outcomes under realized replay conditions.',[['Condition','Arrived / 4','Timeout / 4']]+[[c['label'],str(c['arrived']),str(c['timeouts'])] for c in conditions])
    tables['TABLE_FAMILY']=('Table 4. Admissions per family, out of 24 attempts.',[['Method','Open','Clutter','Rough','Corridor']]+[[NAMES[m]]+[str(next(x['admitted'] for x in family if x['method']==m and x['family']==f)) for f in FAMILIES] for m in METHODS])
    tables['TABLE_COMPUTE']=('Table 5. Search work across 96 attempts per method.',[['Method','Median s','Max s','Median evals','At 240']]+[[NAMES[r['method']],f"{r['median_seconds']:.3f}",f"{r['maximum_seconds']:.3f}",f"{r['median_evaluations']:g}",str(r['at_ceiling'])] for r in computation])
    tables['TABLE_SENSITIVITY']=('Table 6. Mean effects after omitting one paired world.',[['Control','n','Smallest (%)','Largest (%)']]+[[NAMES[r['method']],str(r['n']),f"{r['minimum_omission_mean_percent']:.3f}",f"{r['maximum_omission_mean_percent']:.3f}"] for r in sensitivity])
    def rng(values,digits=3):
        return f'{values[0]:.{digits}f}' if abs(values[0]-values[1])<10**(-digits-1) else f'{values[0]:.{digits}f}–{values[1]:.{digits}f}'
    tables['TABLE_CONTACT']=('Table 8. Contact telemetry ranges across four missions.',[['Condition','Mean feet','No-contact (%)']]+[[c['label'],rng(c['mean_contact_range']),rng([100*x for x in c['no_contact_range']],2)] for c in conditions])
    texts['FAMILY_RESULTS']='All primary resource rejections occur in the corridor family (Table 4). Open, clutter and rough each contribute 24/24 admissions for every configuration. Corridor admission is 21/24 for V4, PSO-P, ACO-P and V4 noL, 22/24 for PSO-C and 18/24 for V4 noP. The single additional PSO-C admission and the three admissions lost after polishing removal are therefore localized to corridor requests in this campaign.'
    texts['COMPUTE_RESULTS']=(f"Table 5 separates elapsed search time from evaluated-route counts. PSO-C reaches the 240-route ceiling on 84/96 attempts; none of the other five configurations reaches it. Median route evaluations are 33 for V4, 46 for PSO-P, 32.5 for ACO-P, 240 for PSO-C, 21 for V4 noL and 5 for V4 noP. Recorded maximum search times range from {min(r['maximum_seconds'] for r in computation):.3f} to {max(r['maximum_seconds'] for r in computation):.3f} s, all below the nominal allowance. Median visibility-check counts are 1,033 for V4 and 2,142.5 for PSO-C, compared with 146.5 after landmark removal. Shared preparation has median {np.median(preparation):.3f} s and maximum {preparation.max():.3f} s per primary case.")
    texts['SENSITIVITY_RESULTS']=('Figure 4 displays every jointly admitted world effect against PSO-C, ordered by the frozen case identifier. World ij3ctest_24 has a 23.202% positive effect, the largest in that comparison. Omitting it changes the remaining-world mean from 0.690% to −0.060%; omitting each other world in turn yields the range summarized in Table 6. The corresponding largest-world omissions leave mean effects of 0.187% against PSO-P, 0.178% against ACO-P and 0.182% against V4 noL. For polishing removal, the omission mean remains positive throughout its range of 0.682–0.822%. These calculations describe concentration of the observed effects and introduce no exclusion into the primary analysis.')
    no_gc=conditions[3]
    texts['REPLAY_DETAIL']=(f"Full-assistance missions cover {rng(conditions[0]['distance_range'],2)} m with elapsed times {rng(conditions[0]['elapsed_range'],2)} s. Reduced-assistance missions cover {rng(conditions[1]['distance_range'],2)} m in {rng(conditions[1]['elapsed_range'],2)} s. Each completed elapsed time includes 8 s of modeled service. Zero assistance with compensation covers {rng(conditions[2]['distance_range'],3)} m before the 180 s timeout; corrected zero assistance without compensation covers {rng(no_gc['distance_range'],3)} m. Figure 5 shows individual mission distances, preserving all four cases in each realized condition.\n\n"+
    'The full and reduced assistance runs log zero detected foot contacts at every sampled physics step: mean contact feet is zero and the no-foot-contact fraction is 100% in all eight runs. Table 8 reports the contact ranges for every condition. The recorded absence of foot contacts applies to the defined six-foot detector; it supplies no evidence of a load-bearing walking gait. Maximum body tilt is below 0.410 degrees in the assisted runs, where roll/pitch rates are directly corrected. That value is a controller-dependent simulation observation, rather than a physical stability margin.')
    texts['PROBE_RESULTS']='Full assistance and 0.5 assistance each complete 4/4 missions. Zero assistance with compensation and the corrected zero-assistance/no-compensation condition each time out on all four missions at 180 s. GC in Table 7 denotes limb gravity compensation. A timeout records failure to complete the saved destination-and-return mission within the configured duration; it does not classify a fall. The four original mislabeled no-compensation requests are excluded from this comparison and preserved in the supplement with the correction record.'
    # Fix table references before generating the document.
    texts['ABSTRACT']=texts['ABSTRACT'].replace('with or without limb gravity compensation.','both with compensation and after verified removal of limb gravity compensation.')
    fig,ax=plt.subplots(figsize=(3.1,3.05));rows=sorted([r for r in effects if r['baseline']=='continuous_pso'],key=lambda r:r['world']);x=[int(r['world'].split('_')[-1]) for r in rows];y=[float(r['relative_percent']) for r in rows]
    ax.scatter(x,y,s=18,color='#17686f');ax.axhline(0,color='grey',lw=.8);ax.set(xlabel='Primary world index',ylabel='V4 score improvement (%)',xticks=[1,8,16,24,32]);ax.grid(alpha=.15);fig.tight_layout();fig.savefig(B/'figures/world_distribution.png',dpi=400);fig.savefig(B/'figures/world_distribution.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(3.1,3.1));colors=['#17686f','#4f7e99','#a96b35','#6e6262']
    for i,c in enumerate(conditions):
        distances=[r['execution']['distance_m'] for r in c['rows']];ax.scatter(np.arange(4)*.045+i-.0675,distances,s=24,color=colors[i],zorder=3)
    ax.set(xticks=range(4),xticklabels=['Full\n+ GC','Blend\n+ GC','Zero\n+ GC','Zero\nno GC'],ylabel='Mission distance (m)',ylim=(-2,47));ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(B/'figures/replay_distance.png',dpi=400);fig.savefig(B/'figures/replay_distance.pdf');plt.close(fig)
    figures['FIG_DISTRIBUTION']=('world_distribution.png','Figure 4. PSO-C paired world effects. Each point averages jointly admitted repetitions within one world; positive values favor V4. World 24 remains in the primary analysis.')
    figures['FIG_REPLAY']=('replay_distance.png','Figure 5. Whole-mission distance in the four realized conditions. Each point is one archived route; GC-off uses the corrected replays. Points overlap where distances are similar.')
