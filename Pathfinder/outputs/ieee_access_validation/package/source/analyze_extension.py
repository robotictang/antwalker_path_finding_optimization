"""Independent paired calculations and scientific figures from frozen trials."""
from pathlib import Path
from collections import Counter
import json,csv,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
B=Path(__file__).resolve().parents[1];ROOT=B.parents[1]
S=B/'evidence/validation_extension_v5' if (B/'evidence/validation_extension_v5').exists() else ROOT/'mujoco/outputs/research/validation_extension_v5'
N={'proposed_v4':'V4 (retuned)','pso_polished':'PSO + polish','aco_polished':'ACO + polish','proposed_v5':'V5 candidate','proposed_v5_fixed':'Fixed allocation','proposed_v5_no_polish':'No polishing','proposed_v5_no_landmarks':'No landmarks'}
COL={'proposed_v4':'#576b73','pso_polished':'#af771e','aco_polished':'#8b6191','proposed_v5':'#27678e'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})

def load(name):return json.loads((S/(name+'.json')).read_text())
def ci(values):
    if len(values)<2:return None
    a=np.asarray(values);rng=np.random.default_rng(6104)
    return np.quantile(rng.choice(a,(5000,len(a)),replace=True).mean(1),[.025,.975]).tolist()
def mean(v):return float(np.mean(v)) if len(v) else None
def permutation(values):
    a=np.asarray(values);a=a[abs(a)>1e-8]
    if not len(a):return 1.
    observed=abs(a.mean());rng=np.random.default_rng(7421);extreme=0;n=100000
    for _ in range(100):
        sim=(rng.integers(0,2,(1000,len(a)))*2-1)@a/len(a)
        extreme+=int(np.sum(abs(sim)>=observed-1e-12))
    return (extreme+1)/(n+1)
def pairs(run,baseline,focal='proposed_v5',cases=None):
    idx={(r['case_id'],r['repeat'],r['method']):r for r in run['records']};counts=Counter(dict(wins=0,ties=0,losses=0,proposed_only_admitted=0,baseline_only_admitted=0,both_rejected=0));worlds=[];trialrows=[];admissions=[]
    for c in run['cases']:
        if cases and c['id'] not in cases:continue
        relative=[];absolute=[];local_admission=[]
        for j in range(run['repeats']):
            p=idx[c['id'],j,focal]['plan'];q=idx[c['id'],j,baseline]['plan'];pa=p.get('admissible',False);qa=q.get('admissible',False);local_admission.append(int(pa)-int(qa))
            if pa and qa:
                # Recompute Q directly from the four saved components.
                score=lambda v:v['metrics']['distance_m']/50+v['metrics']['estimated_seconds']/90+v['metrics']['energy_percent']/30+.25*v['metrics']['terrain_exposure']/20
                ps,qs=score(p),score(q);delta=qs-ps;r=100*delta/qs
                outcome='ties' if abs(delta)<=1e-8 else 'wins' if delta>0 else 'losses';counts[outcome]+=1;relative.append(r);absolute.append(delta)
                trialrows.append(dict(case=c['id'],family=c['world']['family'],repeat=j,baseline=baseline,relative_percent=r,score_difference=delta,outcome=outcome))
            else:counts['proposed_only_admitted' if pa else 'baseline_only_admitted' if qa else 'both_rejected']+=1
        admissions.append(mean(local_admission))
        if relative:worlds.append(dict(case=c['id'],family=c['world']['family'],relative_percent=mean(relative),score_difference=mean(absolute)))
    values=[w['relative_percent'] for w in worlds];deltas=[w['score_difference'] for w in worlds]
    return dict(baseline=baseline,**dict(counts),paired_worlds=len(worlds),mean_relative_percent=mean(values),relative_ci95=ci(values),mean_score_difference=mean(deltas),
      admission_advantage_pp=100*mean(admissions),permutation_p=permutation(deltas),worlds=worlds,trials=trialrows)

def write_csv(name,rows):
    if not rows:return
    with (B/'tables'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(fig,name):
    fig.savefig(B/'figures'/(name+'.png'),dpi=400,bbox_inches='tight',facecolor='white');fig.savefig(B/'figures'/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def clean(ax):ax.grid(axis='x',color='.9',zorder=0);ax.set_axisbelow(True)

def main():
    primary=load('v5_fresh_planning');ablation=load('v5_feature_ablations')
    baselines=[m for m in primary['methods'] if m!='proposed_v5'];reports=[pairs(primary,b) for b in baselines]
    order=sorted(range(len(reports)),key=lambda i:reports[i]['permutation_p']);previous=0.
    for rank,i in enumerate(order):previous=max(previous,min(1.,(len(reports)-rank)*reports[i]['permutation_p']));reports[i]['holm_p']=previous
    # Independent reconciliation to the archived comparison is a cross-check,
    # not the source of any number above.
    archived=load('comparison')
    for p in reports:
        a=next(x for x in archived['comparisons'] if x['baseline']==p['baseline'])
        for key in ['wins','ties','losses','proposed_only_admitted','baseline_only_admitted','both_rejected']:assert p[key]==a[key]
        assert math.isclose(p['mean_relative_percent'],a['mean_relative_score_improvement_percent'],abs_tol=1e-10)
    summary=[]
    for m in primary['methods']:
        rows=[r for r in primary['records'] if r['method']==m];admit=[r for r in rows if r['plan'].get('admissible')]
        summary.append(dict(method=m,attempts=len(rows),admitted=len(admit),mean_q=mean([r['plan']['quality_score'] for r in admit]),
          mean_planning_s=mean([r['plan'].get('planning_seconds') for r in rows if r['plan'].get('planning_seconds') is not None]),
          mean_metric_calls=mean([r['plan'].get('continuous_metric_calls',0) for r in rows]),
          mean_fitness=mean([r['plan'].get('optimizer',{}).get('fitness_evaluations',0) for r in rows]),
          bound_exits=sum(r['plan'].get('optimizer',{}).get('direct_bound_exit',False) for r in rows)))
    abr=[pairs(ablation,m) for m in ablation['methods'] if m!='proposed_v5']
    sensitivity=[];first8={c['id'] for c in primary['cases'][:8]}
    for name in ['v5_budget_0p5','v5_budget_1p0','v5_fresh_planning','v5_candidate_cap80']:
        run=load(name)
        for baseline in baselines:
            p=pairs(run,baseline,cases=first8 if name=='v5_fresh_planning' else None)
            sensitivity.append(dict(phase=name,budget_s=run['planning_budget_s'],cap=run['study']['candidate_cap'],**{k:v for k,v in p.items() if k not in ['trials','worlds']}))
    physical=[];physics_detail=[];diagnostics=[]
    for name in ['v5_physics_assistance_1p0','v5_physics_assistance_0p5']:
        run=load(name)
        for m in primary['methods']:
            rows=[r for r in run['records'] if r['method']==m];executed=[r for r in rows if r.get('execution')];good=[r for r in executed if r['success']]
            residual=[r['execution']['task_time_s']-r['plan']['metrics']['estimated_seconds'] for r in executed if r['execution']['task_time_s'] is not None]
            physical.append(dict(assistance=run['assistance_scale'],method=m,scheduled=len(rows),admitted=sum(r['plan'].get('admissible',False) for r in rows),executed=len(executed),successful=len(good),
              mean_task_s=mean([r['execution']['task_time_s'] for r in good]),mean_work_j=mean([r['execution']['positive_actuator_work_j'] for r in good]),
              prediction_bias_s=mean(residual),prediction_mae_s=mean([abs(x) for x in residual]),outcomes=dict(Counter(r['status'] for r in rows))))
            for r in rows:
                physics_detail.append(dict(phase=name,case=r['case_id'],method=m,status=r['status'],success=r['success'],executed=bool(r.get('execution'))))
                if r.get('execution') and not r['success']:
                    ex=r['execution'];diagnostics.append(dict(phase=name,case=r['case_id'],method=m,status=r['status'],destination_reached=ex['destination_reached'],
                      motion_s=ex['motion_seconds'],distance_m=ex['distance_m'],safety_stops=ex['safety_stops'],penetration_substeps=ex['penetration_substeps'],solver_warnings=ex['solver_warnings'],
                      predicted_destination_s=r['plan']['metrics']['estimated_seconds']))
    allrows=[];phasecounts={}
    for p in sorted(S.glob('v5_*.json')):
        run=json.loads(p.read_text())
        if 'records' not in run:continue
        phasecounts[p.stem]=len(run['records'])
        for r in run['records']:
            plan=r.get('plan',{});mt=plan.get('metrics') or {};ex=r.get('execution') or {}
            allrows.append(dict(phase=p.stem,case=r['case_id'],method=r['method'],repeat=r['repeat'],seed=r['seed'],status=r['status'],admitted=plan.get('admissible',False),success=r['success'] if run['execute'] else None,
             q=plan.get('quality_score'),planning_s=plan.get('planning_seconds'),metric_calls=plan.get('continuous_metric_calls'),fitness=plan.get('optimizer',{}).get('fitness_evaluations'),
             distance_m=mt.get('distance_m'),predicted_s=mt.get('estimated_seconds'),nominal_energy_pp=mt.get('energy_percent'),exposure=mt.get('terrain_exposure'),
             assistance=run['assistance_scale'] if run['execute'] else None,measured_task_s=ex.get('task_time_s'),positive_work_j=ex.get('positive_actuator_work_j')))
    assert len(allrows)==800
    index={(r['case_id'],r['repeat'],r['method']):r for r in primary['records']}
    exact_routes=sum(index[c['id'],j,'proposed_v4']['plan'].get('points')==index[c['id'],j,'proposed_v5']['plan'].get('points') for c in primary['cases'] for j in range(2))
    result=dict(phase_counts=phasecounts,total_attempts=len(allrows),primary=summary,comparisons=reports,ablations=abr,sensitivity=sensitivity,physics=physical,physics_failures=diagnostics,v4_v5_exact_coordinate_pairs=exact_routes,
      subgroup=[dict(baseline=p['baseline'],family=f,worlds=len(w:=[r['relative_percent'] for r in p['worlds'] if r['family']==f]),mean_relative_percent=mean(w),ci95=ci(w)) for p in reports for f in ['open','clutter','rough','corridor']],
      interpretation='Positive percentages favor V5 on jointly admitted worlds only; intervals are descriptive whole-world bootstrap intervals. Holm-adjusted sign-flip p-values are exploratory, assume world-level sign exchangeability, and do not establish practical importance or hardware performance.')
    (B/'source/extension_analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    write_csv('All_800_Extension_Attempts.csv',allrows);write_csv('Primary_Method_Summary.csv',summary)
    write_csv('Primary_Paired_Comparison.csv',[{k:v for k,v in p.items() if k not in ['worlds','trials']} for p in reports]);write_csv('World_Paired_Effects.csv',[dict(baseline=p['baseline'],**r) for p in reports for r in p['worlds']]);write_csv('Physics_Summary.csv',physical);write_csv('Physics_Every_Attempt.csv',physics_detail);write_csv('Physics_Failure_Diagnostics.csv',diagnostics)
    fig,ax=plt.subplots(figsize=(3.32,2.8));ys=np.arange(3)
    for y,p in zip(ys,reports):
        lo,hi=p['relative_ci95'];x=p['mean_relative_percent'];ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt='o',color=COL[p['baseline']],capsize=4);ax.annotate(f'{x:+.3f}% [{lo:+.3f}, {hi:+.3f}]',(x,y),xytext=(0,12),textcoords='offset points',ha='left' if p['baseline']=='proposed_v4' else 'center',fontsize=8)
    ax.axvline(0,color='.25',lw=.8);ax.set_yticks(ys,[N[p['baseline']] for p in reports]);ax.set_ylim(-.5,2.6);ax.set_xlabel('Paired V5 score improvement (%)',fontsize=8);ax.set_title('48 fresh worlds\nDescriptive 95% world bootstrap intervals',fontsize=8.5);clean(ax);fig.tight_layout();save(fig,'ext1')
    fig,ax=plt.subplots(figsize=(3.32,3.0));left=np.zeros(3)
    for key,label,col in [('wins','V5 wins','#27678e'),('ties','Ties','#cdd3d6'),('losses','V5 losses','#af771e'),('proposed_only_admitted','Only V5 admitted','#8b6191'),('baseline_only_admitted','Only control admitted','#736d50'),('both_rejected','Both rejected','#e6e6e6')]:
        values=[p[key] for p in abr]
        if not any(values):continue
        ax.barh(np.arange(3),values,left=left,label=label,color=col,edgecolor='white')
        for i,v in enumerate(values):
            if v:ax.text(left[i]+v/2,i,str(v),ha='center',va='center',fontsize=8,color='white' if key=='wins' else 'black')
        left+=values
    ax.set_yticks(np.arange(3),[N[p['baseline']] for p in abr]);ax.set_xlabel('32 scheduled pairs per control',fontsize=8);ax.set_xlim(0,32);ax.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.35),fontsize=7.5,frameon=False);fig.tight_layout();save(fig,'ext2')
    fig,axes=plt.subplots(1,2,figsize=(6.7,2.7))
    for ax,key,title in zip(axes,['mean_planning_s','mean_metric_calls'],['Planner wall seconds','All continuous metric calls']):
        ax.barh(np.arange(4),[r[key] for r in summary],color=[COL[r['method']] for r in summary]);ax.set_yticks(np.arange(4),[N[r['method']] for r in summary]);ax.set_xlabel(title);ax.set_xlim(left=0);clean(ax)
    fig.tight_layout();save(fig,'ext3')
    fig,ax=plt.subplots(figsize=(3.32,3.1));x=np.arange(4)
    for offset,scale,hatch in [(-.18,1.,''),(.18,.5,'///')]:
        group=[r for r in physical if r['assistance']==scale];bars=ax.bar(x+offset,[r['successful'] for r in group],width=.34,color=[COL[r['method']] for r in group],hatch=hatch,edgecolor='.25',label=f'Assistance {scale:g}')
        for i,(bar,r) in enumerate(zip(bars,group)):
            if scale==1.:ax.text(i,bar.get_height()+.15,f"{r['successful']}/12",ha='center',fontsize=8)
    ax.set_xticks(x,['V4','PSO +','ACO +','V5']);ax.set_ylim(0,14);ax.set_ylabel('Successful / scheduled missions',fontsize=8);ax.legend(frameon=False,fontsize=8);ax.set_title('Same 12 worlds\nGravity compensation remains enabled',fontsize=8.5);fig.tight_layout();save(fig,'ext4')
    fig,ax=plt.subplots(figsize=(3.32,3.0))
    for baseline in baselines:
        group=[r for r in sensitivity if r['baseline']==baseline and r['cap']==240];group.sort(key=lambda r:r['budget_s']);ax.plot([r['budget_s'] for r in group],[r['mean_relative_percent'] for r in group],'o-',color=COL[baseline],label=N[baseline])
    ax.axhline(0,color='.2',lw=.8);ax.set_xticks([.5,1,2]);ax.set_xlabel('Planner budget (s)');ax.set_ylabel('Paired V5 score improvement (%)',fontsize=8);ax.set_title('First eight fresh worlds\nOne repeat at 0.5/1 s; two at 2 s',fontsize=8.5);ax.legend(frameon=False,fontsize=8);fig.tight_layout();save(fig,'ext5')
    # Mechanically selected extremes are illustrative, not the main evidence.
    paired=next(p for p in reports if p['baseline']=='pso_polished')['trials'];selected=[max(paired,key=lambda r:r['relative_percent']),min(paired,key=lambda r:r['relative_percent'])]
    idx={(r['case_id'],r['repeat'],r['method']):r for r in primary['records']};cases={c['id']:c for c in primary['cases']}
    fig,axes=plt.subplots(2,2,figsize=(6.7,6.0))
    for rr,example in enumerate(selected):
        c=cases[example['case']]
        for cc,m in enumerate(['pso_polished','proposed_v5']):
            ax=axes[rr,cc];p=idx[c['id'],example['repeat'],m]['plan'];world=c['world']
            for o in world['obstacles']:ax.add_patch(Rectangle((o['x']-o['sx'],o['y']-o['sy']),2*o['sx'],2*o['sy'],facecolor='.65'))
            for patch in world['patches']:
                x0,x1,y0,y1=patch['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#af771e',alpha=.15 if patch['grade']==1 else .26))
            pts=np.asarray(p['points']);ax.plot(pts[:,0],pts[:,1],'-o',lw=1.2,ms=2,color=COL[m]);ax.plot(*c['start'],'ko',ms=4);ax.plot(*c['goal'],'ks',ms=4)
            ax.set(xlim=(-24,24),ylim=(-24,24),aspect='equal',xlabel='x (m)',ylabel='y (m)',title=f"{N[m]} · Q={p['quality_score']:.6f}")
            ax.text(.02,.02,f"{c['id']} · repeat {example['repeat']+1}",transform=ax.transAxes,fontsize=7)
    fig.suptitle('Illustrative extremes versus polished PSO\nPost hoc examples; complete-set statistics control conclusions',fontsize=10);fig.tight_layout(rect=(0,0,1,.94));save(fig,'ext6')
    result['illustrative_cases']=selected;(B/'source/extension_analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps({'attempts':800,'summary':summary,'comparisons':[{k:v for k,v in p.items() if k not in ['trials','worlds']} for p in reports],'physics':physical},indent=2))

if __name__=='__main__':main()
