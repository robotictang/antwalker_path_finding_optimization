"""Independent V6 summary and scientific plots; all outcomes retained."""
from pathlib import Path
import json,csv,math
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Rectangle
B=Path(__file__).resolve().parents[1];R=B.parents[1]
S=B/'evidence/final_validation_v6' if (B/'evidence/final_validation_v6').exists() else R/'mujoco/outputs/research/final_validation_v6'
METHODS=['proposed_v4','pso_polished','aco_polished','ompl_rrtstar','ompl_seeded_rrtstar','ompl_rrtconnect']
N=dict(zip(METHODS,['Proposal','PSO + polish','ACO + polish','OMPL RRT* + polish','RRT* + incumbent + polish','RRTConnect + polish']))
COL=dict(zip(METHODS,['#17686f','#81508c','#b97821','#315f97','#a64848','#63753a']))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':9,'axes.labelsize':8.5,'xtick.labelsize':8,'ytick.labelsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
def load(name):return json.loads((S/(name+'.json')).read_text())
def mean(v):return float(np.mean(v)) if len(v) else None
def ci(v):
    if len(v)<2:return None
    a=np.asarray(v);rng=np.random.default_rng(6104)
    return np.quantile(rng.choice(a,(5000,len(a)),replace=True).mean(1),[.025,.975]).tolist()
def q(plan,weights):return sum(a*b for a,b in zip(weights,[plan['metrics'][k] for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']]))
def pairs(run,baseline,case_ids=None):
    ix={(r['case_id'],r['repeat'],r['method']):r for r in run['records']};counts=Counter(dict(wins=0,ties=0,losses=0,proposed_only_admitted=0,baseline_only_admitted=0,both_rejected=0));worlds=[];trials=[];admission=[]
    for c in run['cases']:
        if case_ids is not None and c['id'] not in case_ids:continue
        effects=[];absolute=[];adm=[]
        for j in range(run['repeats']):
            p=ix[c['id'],j,'proposed_v4']['plan'];b=ix[c['id'],j,baseline]['plan'];pa=p.get('admissible',False);ba=b.get('admissible',False);adm.append(int(pa)-int(ba))
            if pa and ba:
                ps,bs=q(p,run['study']['score_weights']),q(b,run['study']['score_weights']);delta=bs-ps;effect=100*delta/bs
                outcome='ties' if abs(delta)<=1e-8 else 'wins' if delta>0 else 'losses';counts[outcome]+=1;effects.append(effect);absolute.append(delta)
                trials.append(dict(case=c['id'],regime=c.get('regime','standard'),family=c['world']['family'],repeat=j,relative_percent=effect,score_difference=delta,outcome=outcome))
            else:counts['proposed_only_admitted' if pa else 'baseline_only_admitted' if ba else 'both_rejected']+=1
        admission.append(mean(adm))
        if effects:worlds.append(dict(case=c['id'],regime=c.get('regime','standard'),family=c['world']['family'],relative_percent=mean(effects),score_difference=mean(absolute)))
    values=[x['relative_percent'] for x in worlds];largest=max(worlds,key=lambda x:x['relative_percent']) if worlds else None
    return dict(baseline=baseline,**dict(counts),paired_worlds=len(worlds),mean_relative_percent=mean(values),median_relative_percent=float(np.median(values)) if values else None,minimum_relative_percent=min(values) if values else None,maximum_relative_percent=max(values) if values else None,relative_ci95=ci(values),admission_advantage_pp=100*mean(admission),leave_largest_world_diagnostic=mean([w['relative_percent'] for w in worlds if w!=largest]),worlds=worlds,trials=trials)
def csvout(name,rows):
    if not rows:return
    with (B/'tables'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save(fig,name):
    fig.savefig(B/'figures'/(name+'.png'),dpi=400,bbox_inches='tight',facecolor='white');fig.savefig(B/'figures'/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
def plot_primary(summary,comparisons):
    fig,axes=plt.subplots(1,2,figsize=(6.7,3.1),gridspec_kw={'width_ratios':[1,1.35]})
    ax=axes[0];bars=ax.barh(np.arange(6),[r['admitted'] for r in summary],color=[COL[m] for m in METHODS]);ax.set_yticks(np.arange(6),[N[m] for m in METHODS]);ax.set_xlim(0,108);ax.set_xlabel('Admitted / 96 scheduled');ax.invert_yaxis()
    for bar,r in zip(bars,summary):ax.text(bar.get_width()+1,bar.get_y()+bar.get_height()/2,str(r['admitted']),va='center',fontsize=8)
    ax=axes[1]
    for y,p in enumerate(comparisons):
        x=p['mean_relative_percent'];interval=p['relative_ci95']
        if interval:ax.errorbar(x,y,xerr=[[x-interval[0]],[interval[1]-x]],fmt='o',color=COL[p['baseline']],capsize=3)
        ax.annotate(f'{x:+.2f}%',(x,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=8)
    ax.axvline(0,color='.4',lw=.8);ax.set_yticks(range(5),[N[m] for m in METHODS[1:]]);ax.invert_yaxis();ax.set_ylim(4.6,-.6);ax.set_xlabel('Paired proposal score improvement (%)');ax.set_title('48 worlds; descriptive 95% world intervals')
    fig.tight_layout();save(fig,'final1')

def plot_sensitivity(weights,budgets):
    fig,axes=plt.subplots(1,2,figsize=(6.7,3.0),gridspec_kw={'width_ratios':[1.3,1.]})
    matrix=np.array([[next(r['mean_relative_percent'] for r in weights if r['baseline']==m and r['profile']==p) for p in ['balanced','distance','time','energy','terrain']] for m in METHODS[1:]])
    limit=max(1,abs(matrix).max());im=axes[0].imshow(matrix,cmap='RdBu',vmin=-limit,vmax=limit,aspect='auto')
    for i in range(5):
        for j in range(5):axes[0].text(j,i,f'{matrix[i,j]:+.2f}',ha='center',va='center',fontsize=7,color='white' if abs(matrix[i,j])>.6*limit else 'black')
    axes[0].set_xticks(range(5),['Bal.','Dist.','Time','Energy','Terrain']);axes[0].set_yticks(range(5),[N[m] for m in METHODS[1:]]);axes[0].set_title('Same 12 worlds; within-profile paired %');fig.colorbar(im,ax=axes[0],fraction=.045,pad=.03)
    for m in METHODS[1:]:
        group=sorted([r for r in budgets if r['baseline']==m],key=lambda r:r['budget_s']);axes[1].plot([r['budget_s'] for r in group],[r['mean_relative_percent'] for r in group],'o-',label=N[m],color=COL[m],ms=3)
    axes[1].axhline(0,color='.4',lw=.8);axes[1].set_xticks([.5,1,2]);axes[1].set_xlabel('Planner allowance (s)');axes[1].set_ylabel('Paired improvement (%)');axes[1].legend(fontsize=6.5,frameon=False);axes[1].set_title('Separate fixed 12-world budget subset');fig.tight_layout();save(fig,'final2')

def plot_workflow():
    # Diagram is a workflow, never a measured robot trajectory.
    fig,ax=plt.subplots(figsize=(6.7,2.7));ax.set(xlim=(0,10),ylim=(0,4));ax.axis('off')
    boxes=[(.1,2.4,2.2,1.2,'Frozen test worlds\n24 standard\n24 shifted'),(2.7,2.4,2.2,1.2,'Six route planners\nSame declared limits'),(5.3,2.4,2.2,1.2,'Common evaluator\nGeometry and resources\nFeasible first then Q'),(7.9,2.4,2.,1.2,'Save every attempt\nAdmitted or rejected\nor no route'),(5.3,.2,2.2,1.25,'Replay saved routes\nShared safe follower'),(2.7,.2,2.2,1.25,'Align then translate\nSafe connector checks\nBounded recovery\nStop if still blocked'),(.1,.2,2.2,1.25,'Simulated telemetry\nBattery data workflow\nHardware pending')]
    for x,y,w,h,t in boxes:ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.04',facecolor='#eef5f5',edgecolor='#17686f',lw=.8));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=8)
    for a,b in [((2.35,3),(2.65,3)),((4.95,3),(5.25,3)),((7.55,3),(7.85,3)),((6.4,2.35),(6.4,1.5)),((5.25,.82),(4.95,.82)),((2.65,.82),(2.35,.82))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=10,color='#49535b',lw=.9))
    fig.tight_layout();save(fig,'final4')

def plot_original_route_panels():
    old=B/'evidence/advanced_study_v4' if (B/'evidence/advanced_study_v4').exists() else R/'mujoco/outputs/research/advanced_study_v4'
    run=json.loads((old/'v4_heldout_planning.json').read_text());ix={(r['case_id'],r['repeat'],r['method']):r for r in run['records']};cases={c['id']:c for c in run['cases']}
    fig,axes=plt.subplots(1,2,figsize=(6.7,3.0))
    for ax,(cid,baseline,label) in zip(axes,[('heldout_24','pso','PSO'),('heldout_02','pso_polished','PSO + polish')]):
        c=cases[cid];a=ix[cid,0,baseline]['plan'];b=ix[cid,0,'proposed_v4']['plan'];mapping=c['map']
        for patch in mapping.get('terrain_patches',[]):
            x0,x1,y0,y1=patch['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='#c4a982',alpha=.25))
        for lo,hi in mapping['obstacles']:ax.add_patch(Rectangle(lo,hi[0]-lo[0],hi[1]-lo[1],color='#5e6264'))
        pts=np.concatenate([np.asarray(a['points']),np.asarray(b['points'])]);lo=pts.min(axis=0)-3;hi=pts.max(axis=0)+3;center=.5*(lo+hi);span=max(hi-lo);lo=center-span/2;hi=center+span/2
        for plan,tone,style,name in [(a,'#b97821','--',label),(b,'#17686f','-','V4 proposal')]:
            xy=np.asarray(plan['points']);ax.plot(xy[:,0],xy[:,1],style,color=tone,lw=1.4,label=f"{name}: Q={plan['quality_score']:.6f}"+(' (rejected)' if not plan['admissible'] else ''))
        ax.plot(*c['start'],'ko',ms=3);ax.plot(*c['goal'],'ks',ms=3);ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),aspect='equal',xlabel='x (m)',ylabel='y (m)',title=cid)
        ax.legend(fontsize=7.5,loc='upper center',bbox_to_anchor=(.5,-.22),frameon=False)
    fig.tight_layout(rect=(0,.08,1,1));save(fig,'tomat5')

def plot_original_forest():
    old=B/'evidence/advanced_study_v4' if (B/'evidence/advanced_study_v4').exists() else R/'mujoco/outputs/research/advanced_study_v4'
    comp=json.loads((old/'comparison.json').read_text())['comparisons']
    names={'b1_distance':'Distance A*','b2_terrain':'Terrain A*','b3_energy':'Energy A*','b4_weighted':'Weighted search','b7_greedy':'Greedy shortcut','pso':'PSO','aco':'ACO','proposed_v1':'Grid Pareto','proposed':'Corridor Pareto','pso_polished':'PSO + polish','aco_polished':'ACO + polish'}
    fig,ax=plt.subplots(figsize=(6.7,2.6))
    for y,r in enumerate(comp):
        x=r['mean_relative_score_improvement_percent'];lo,hi=r['relative_improvement_95_percent'];ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt='o',color='#285676',capsize=2,ms=3,lw=1)
    ax.set_yticks(range(len(comp)),[names[r['baseline']] for r in comp]);ax.invert_yaxis();ax.axvline(0,color='#777',ls='--',lw=.8);ax.set_xlabel('Paired V4 balanced-score improvement (%)');fig.tight_layout(pad=.3);save(fig,'tomat4')

def main():
    primary=load('v6_primary');manifest=load('manifest');comparisons=[pairs(primary,m) for m in METHODS[1:]];summary=[]
    archived=load('comparison')
    for p in comparisons:
        original=next(x for x in archived['comparisons'] if x['baseline']==p['baseline'])
        for key in ['wins','ties','losses','proposed_only_admitted','baseline_only_admitted','both_rejected']:assert p[key]==original[key]
        assert math.isclose(p['mean_relative_percent'],original['mean_relative_score_improvement_percent'],abs_tol=1e-10)
        assert np.allclose(p['relative_ci95'],original['relative_improvement_95_percent'],rtol=0,atol=1e-9)

    for m in METHODS:
        rows=[r for r in primary['records'] if r['method']==m];ok=[r for r in rows if r['plan'].get('admissible')]
        summary.append(dict(method=m,attempts=len(rows),admitted=len(ok),mean_q=mean([q(r['plan'],primary['study']['score_weights']) for r in ok]),mean_planning_s=mean([r['plan'].get('planning_seconds',0) for r in rows]),mean_metric_calls=mean([r['plan'].get('continuous_metric_calls',0) for r in rows]),outcomes=dict(Counter(r['status'] for r in rows))))
    regimes=[]
    for regime in ['standard','shifted']:
        ids={c['id'] for c in primary['cases'] if c.get('regime','standard')==regime}
        for m in METHODS[1:]:regimes.append(dict(regime=regime,**{k:v for k,v in pairs(primary,m,ids).items() if k not in ['worlds','trials']}))
    weights=[];weightids=set(manifest['weight_case_ids'])
    for profile in ['balanced','distance','time','energy','terrain']:
        run=primary if profile=='balanced' else load('v6_weight_'+profile)
        for m in METHODS[1:]:weights.append(dict(profile=profile,**{k:v for k,v in pairs(run,m,weightids).items() if k not in ['worlds','trials']}))
    budgets=[];shortids=set(manifest['short_budget_case_ids'])
    for name in ['v6_budget_0p5','v6_budget_1p0','v6_primary']:
        run=load(name)
        for m in METHODS[1:]:budgets.append(dict(budget_s=run['planning_budget_s'],**{k:v for k,v in pairs(run,m,shortids).items() if k not in ['worlds','trials']}))
    physical=[];physics_rows=[];allrows=[];phasecounts={};warnings=[]
    for p in sorted(S.glob('v6_*.json')):
        run=json.loads(p.read_text())
        if 'records' not in run:continue
        phasecounts[p.stem]=len(run['records']);cases={c['id']:c for c in run['cases']}
        for r in run['records']:
            pl=r.get('plan') or {};mt=pl.get('metrics') or {};ex=r.get('execution') or {};opt=pl.get('optimizer') or {};c=cases[r['case_id']]
            row=dict(phase=p.stem,case=r['case_id'],regime=c.get('regime','standard'),family=c['world']['family'],method=r['method'],repeat=r['repeat'],seed=r['seed'],status=r['status'],admitted=bool(pl.get('admissible')),success=r['success'] if run['execute'] else None,weight_profile=run['study']['weight_profile'],q=pl.get('quality_score'),planner_budget_s=run['planning_budget_s'],planning_s=pl.get('planning_seconds'),metric_calls=pl.get('continuous_metric_calls'),fitness_evaluations=opt.get('fitness_evaluations'),distance_m=mt.get('distance_m'),predicted_destination_s=mt.get('estimated_seconds'),nominal_energy_pp=mt.get('energy_percent'),terrain_exposure=mt.get('terrain_exposure'),tracking_policy=run.get('tracking_policy') if run['execute'] else None,assistance=run['assistance_scale'] if run['execute'] else None,destination_s=ex.get('task_time_s'),motion_s=ex.get('motion_seconds'),safety_stops=ex.get('safety_stops'),tracking_recoveries=ex.get('tracking_recoveries'),penetration_substeps=ex.get('penetration_substeps'),solver_warnings=ex.get('solver_warnings'),positive_actuator_work_j=ex.get('positive_actuator_work_j'),native_library=opt.get('library'),native_version=opt.get('library_version'),native_exitcode=opt.get('worker_exitcode'))
            allrows.append(row)
            if run['execute']:physics_rows.append(row)
            if ex and (ex.get('solver_warnings',0) or ex.get('penetration_substeps',0)):warnings.append(dict(phase=p.stem,case=r['case_id'],method=r['method'],solver_warnings=ex.get('solver_warnings'),penetration_substeps=ex.get('penetration_substeps')))
        if run['execute']:
            for m in run['methods']:
                rows=[r for r in run['records'] if r['method']==m];exs=[r for r in rows if r.get('execution')];ok=[r for r in rows if r.get('success')]
                physical.append(dict(phase=p.stem,method=m,tracking_policy=run['tracking_policy'],assistance=run['assistance_scale'],scheduled=len(rows),admitted=sum(bool(r['plan'].get('admissible')) for r in rows),executed=len(exs),successful=len(ok),mean_destination_s_success_only=mean([r['execution']['task_time_s'] for r in ok]),mean_safety_stops_executed=mean([r['execution']['safety_stops'] for r in exs]),outcomes=dict(Counter(r['status'] for r in rows))))
    safe=load('v6_physics_safe');legacy=load('v6_physics_legacy');reduced=load('v6_physics_reduced');sidx={r['case_id']:r for r in safe['records'] if r['method']=='proposed_v4'}
    tracking=[]
    for control in [legacy,reduced]:
        pairsrows=[]
        for r in control['records']:
            a=sidx[r['case_id']];pairsrows.append(dict(case=r['case_id'],safe_success=a['success'],control_success=r['success'],safe_outcome=a['status'],control_outcome=r['status'],destination_delta_s=(r['execution']['task_time_s']-a['execution']['task_time_s']) if a.get('success') and r.get('success') else None))
        tracking.append(dict(control=control['suite'],both_success=sum(x['safe_success'] and x['control_success'] for x in pairsrows),safe_only_success=sum(x['safe_success'] and not x['control_success'] for x in pairsrows),control_only_success=sum(x['control_success'] and not x['safe_success'] for x in pairsrows),both_unsuccessful=sum(not x['safe_success'] and not x['control_success'] for x in pairsrows),paired_mean_destination_improvement_s=mean([x['destination_delta_s'] for x in pairsrows if x['destination_delta_s'] is not None]),rows=pairsrows))
    assert len(allrows)==1200 and len(phasecounts)==12
    result=dict(attempts=1200,phase_counts=phasecounts,primary=summary,comparisons=comparisons,regimes=regimes,weights=weights,budgets=budgets,physics=physical,tracking_pairs=tracking,physics_numerical_warnings=warnings,interpretation='Descriptive 95% intervals resample whole worlds, not individual repeated seeds. Relative scores are conditional on joint admission. The tested pipeline is assisted simulation and has no measured electrical validation. Native and Python methods use different inner counter primitives; all metric calls are reported.')
    (B/'source/final_analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    csvout('All_1200_Final_Attempts.csv',allrows);csvout('Final_Primary_Summary.csv',summary);csvout('Final_Paired_Comparison.csv',[{k:v for k,v in p.items() if k not in ['worlds','trials']} for p in comparisons]);csvout('Final_World_Effects.csv',[dict(baseline=p['baseline'],**w) for p in comparisons for w in p['worlds']]);csvout('Final_Physics_Summary.csv',physical);csvout('Final_Physics_Every_Attempt.csv',physics_rows);csvout('Final_Weight_Sensitivity.csv',weights);csvout('Final_Budget_Sensitivity.csv',budgets)
    plot_primary(summary,comparisons)
    plot_sensitivity(weights,budgets)
    fig,axes=plt.subplots(1,2,figsize=(6.7,3.))
    safe_summary=[next(r for r in physical if r['phase']=='v6_physics_safe' and r['method']==m) for m in METHODS]
    bars=axes[0].bar(range(6),[r['successful'] for r in safe_summary],color=[COL[m] for m in METHODS]);axes[0].set_xticks(range(6),['Prop.','PSO+','ACO+','RRT*','Seed*','Connect'],rotation=25);axes[0].set_ylim(0,14);axes[0].set_ylabel('Successful / 12 scheduled');axes[0].set_title('Common safe follower; assistance 1')
    for bar,r in zip(bars,safe_summary):axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()+.2,str(r['successful']),ha='center',fontsize=8)
    proposal=[next(r for r in physical if r['phase']==p and r['method']=='proposed_v4') for p in ['v6_physics_legacy','v6_physics_safe','v6_physics_reduced']]
    bars=axes[1].bar(range(3),[r['successful'] for r in proposal],color=['#9b9b9b',COL['proposed_v4'],'#7aa9ac']);axes[1].set_xticks(range(3),['Legacy\nassist. 1','Safe V6\nassist. 1','Safe V6\nassist. 0.5']);axes[1].set_ylim(0,14);axes[1].set_ylabel('Successful / 12 scheduled');axes[1].set_title('Exact saved proposal routes; no rerouting')
    for bar,r in zip(bars,proposal):axes[1].text(bar.get_x()+bar.get_width()/2,bar.get_height()+.2,str(r['successful']),ha='center',fontsize=8)
    fig.tight_layout();save(fig,'final3')
    plot_workflow()
    plot_original_route_panels()
    plot_original_forest()
    print(json.dumps({k:v for k,v in result.items() if k not in ['comparisons','weights','budgets','regimes','tracking_pairs']},indent=2))
if __name__=='__main__':main()
