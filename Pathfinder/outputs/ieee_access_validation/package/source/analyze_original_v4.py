"""Independent paper calculations and plots from the frozen V4 JSON records."""
import collections,csv,hashlib,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
B=Path(__file__).resolve().parents[1];R=B.parents[1];S=B/'evidence/advanced_study_v4' if (B/'evidence/advanced_study_v4').exists() else R/'mujoco/outputs/research/advanced_study_v4';F=B/'figures';F.mkdir(exist_ok=True)
def load(n):return json.loads((S/(n+'.json')).read_text())
P=load('v4_heldout_planning');C=load('comparison');PH=load('v4_heldout_physics');A=load('ablation_comparison');M=load('manifest');LOCK=load('locked_parameters');AUD=load('audit')
assert AUD['state']=='passed' and AUD['attempts']==1232
N={'b1_distance':'Distance A*','b2_terrain':'Terrain A*','b3_energy':'Energy A*','b4_weighted':'Weighted search','b7_greedy':'Greedy shortcut','pso':'PSO','aco':'ACO','proposed_v1':'Grid Pareto','proposed':'Corridor Pareto','pso_polished':'PSO + polish','aco_polished':'ACO + polish','proposed_v4':'V4 proposal','proposed_v4_no_polish':'No polishing','proposed_v4_no_landmarks':'No landmarks'}
idx={(r['case_id'],r['repeat'],r['method']):r for r in P['records']}
def boot(x):
 x=np.array(x,float);return np.quantile(np.random.default_rng(6104).choice(x,(5000,len(x)),replace=True).mean(axis=1),[.025,.975]).tolist()
independent=[]
for old in C['comparisons']:
 m=old['baseline'];cnt=collections.Counter();delta=[];rel=[];ad=[]
 for c in P['cases']:
  ds=[];rs=[];ads=[]
  for j in range(3):
   v=idx[c['id'],j,'proposed_v4']['plan'];b=idx[c['id'],j,m]['plan'];va=v['admissible'];ba=b['admissible'];ads.append(int(va)-int(ba))
   if va and ba:
    d=b['quality_score']-v['quality_score'];cnt['ties' if abs(d)<=1e-8 else 'wins' if d>0 else 'losses']+=1;ds.append(d);rs.append(100*d/b['quality_score'])
   else:cnt['proposed_only_admitted' if va else 'baseline_only_admitted' if ba else 'both_rejected']+=1
  if ds:delta.append(np.mean(ds));rel.append(np.mean(rs))
  ad.append(np.mean(ads))
 for k in ['wins','ties','losses','proposed_only_admitted','baseline_only_admitted','both_rejected']:assert cnt[k]==old[k],(m,k)
 assert np.isclose(np.mean(rel),old['mean_relative_score_improvement_percent'],atol=1e-11)
 assert np.allclose(boot(rel),old['relative_improvement_95_percent'],atol=1e-10)
 assert np.allclose(boot(ad)*np.array([100,100]),old['admission_advantage_95_pp'],atol=1e-10)
 independent.append(dict(baseline=m,**cnt,relative_percent=float(np.mean(rel)),relative_ci=boot(rel)))
phases=['v4_development_default','v4_development_alternative','v4_heldout_planning','v4_heldout_ablations','v4_budget_0p5','v4_budget_1p0','v4_heldout_physics'];total=0
for n in phases:
 d=load(n);total+=len(d['records']);assert d['state']=='complete'
 for r in d['records']:
  assert r['status']!='error';p=r.get('plan') or {};x=p.get('metrics')
  if x:assert math.isclose(x['distance_m']/50+x['estimated_seconds']/90+x['energy_percent']/30+.25*x['terrain_exposure']/20,p['quality_score'],abs_tol=1e-10)
assert total==1232
metrics=[];prediction=[]
for m in P['methods']:
 rows=[r for r in P['records'] if r['method']==m and r['plan']['admissible']]
 row=dict(method=m,label=N[m],admitted=len(rows))
 for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']:row[k]=float(np.mean([r['plan']['metrics'][k] for r in rows]))
 metrics.append(row)
 ex=[r for r in PH['records'] if r['method']==m and r.get('execution')]
 err=np.array([r['execution']['task_time_s']-r['plan']['metrics']['estimated_seconds'] for r in ex]);be=np.array([r['execution']['task_energy_percent']-r['plan']['metrics']['energy_percent'] for r in ex])
 prediction.append(dict(method=m,n=len(ex),time_bias_s=float(err.mean()),time_mae_s=float(np.abs(err).mean()),time_rmse_s=float(np.sqrt((err**2).mean())),battery_ledger_bias_pp=float(be.mean())))
summary=dict(primary_run=P['run_id'],physics_run=PH['run_id'],manifest_sha256=P['study']['manifest_sha256'],parameter_sha256=LOCK['sha256'],independent_comparisons=independent,route_components=metrics,prediction=prediction,case_verdict_counts=dict(collections.Counter(r['verdict'] for r in C['case_verdicts'])),phase_counts={n:len(load(n)['records']) for n in phases},attempts=total,preparation_mean_s=float(np.mean([c['total_preparation_seconds'] for c in P['cases']])),preparation_range_s=[min(c['total_preparation_seconds'] for c in P['cases']),max(c['total_preparation_seconds'] for c in P['cases'])],audit=AUD,source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in S.glob('*.json')})
(B/'source/verified_paper_analysis.json').write_text(json.dumps(summary,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','pdf.fonttype':42,'ps.fonttype':42})
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=600,bbox_inches='tight',pad_inches=.04);fig.savefig(F/(name+'.pdf'),bbox_inches='tight',pad_inches=.04);plt.close(fig)
# Single column system architecture.
fig,ax=plt.subplots(figsize=(3.35,2.6));ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
for y,title,desc in [(8.9,'Shared procedural world','Geometry, terrain, task and station'),(6.6,'Matched planning methods','Same score, limits and time allowance'),(4.3,'Admission and optional physics','Reject unsafe resource plans; log all attempts'),(2.,'Archived evidence and comparison','Source hashes, paired charts and route views')]:
 ax.add_patch(FancyBboxPatch((.2,y-.85),9.6,1.7,boxstyle='round,pad=.05',ec='#333',fc='#f3f5f6'));ax.text(5,y+.23,title,ha='center',weight='bold',fontsize=8);ax.text(5,y-.3,desc,ha='center',fontsize=6.9)
 if y>2:ax.annotate('',xy=(5,y-1.35),xytext=(5,y-.9),arrowprops=dict(arrowstyle='->',lw=1))
fig.tight_layout(pad=.2);save(fig,'tomat1')
# Single column method flow.
fig,ax=plt.subplots(figsize=(3.35,3.4));ax.set(xlim=(0,10),ylim=(0,12));ax.axis('off')
steps=[('Safe initial route','Corridor Pareto refinement within 0.40 B'),('Direct visibility test','Keep if exact collision checks pass'),('Obstacle and terrain landmarks','At most 44 nodes including endpoints'),('Visibility roadmap search','Balanced, time and energy preferences'),('Continuous waypoint polishing','Delete, project or move internal vertices'),('Final resource and score check','Return the best candidate; retain rejections')]
for i,(title,sub) in enumerate(steps):
 y=11-i*1.9;ax.add_patch(FancyBboxPatch((.2,y-.73),9.6,1.46,boxstyle='round,pad=.04',ec='#333',fc='#f3f5f6'));ax.text(5,y+.2,title,ha='center',fontsize=7.8,weight='bold');ax.text(5,y-.28,sub,ha='center',fontsize=6.8)
 if i<5:ax.annotate('',xy=(5,y-1.12),xytext=(5,y-.78),arrowprops=dict(arrowstyle='->',lw=1))
fig.tight_layout(pad=.2);save(fig,'tomat2')
# Complete paired outcomes, one column.
fig,ax=plt.subplots(figsize=(3.35,3.55));rs=C['comparisons'];left=np.zeros(len(rs));y=np.arange(len(rs))
for k,label,col in [('wins','V4 lower','#285676'),('ties','Tie','#d4d9dd'),('losses','Baseline lower','#b67a32'),('proposed_only_admitted','Only V4 admitted','#739b8c'),('both_rejected','Both rejected','#646b71')]:
 v=np.array([r[k] for r in rs]);ax.barh(y,v,left=left,label=label,color=col,height=.78)
 for j,n in enumerate(v):
  if n>=3:ax.text(left[j]+n/2,j,str(n),ha='center',va='center',fontsize=6.5,color='white' if k in ['wins','both_rejected'] else 'black')
 left+=v
ax.set_yticks(y,[N[r['baseline']] for r in rs]);ax.tick_params(axis='y',labelsize=7.2);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xticks([0,24,48,72]);ax.set_xlabel('Matched world and repetition pairs');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.17),ncol=2,frameon=False,fontsize=6.1);fig.tight_layout(pad=.2);save(fig,'tomat3')
# Whole-world relative improvement intervals.
fig,ax=plt.subplots(figsize=(3.35,3.2))
for j,r in enumerate(rs):
 v=r['mean_relative_score_improvement_percent'];ci=r['relative_improvement_95_percent'];ax.errorbar(v,j,xerr=[[v-ci[0]],[ci[1]-v]],fmt='o',color='#285676',capsize=2,ms=3,lw=1)
ax.set_yticks(range(len(rs)),[N[r['baseline']] for r in rs]);ax.tick_params(axis='y',labelsize=7.2);ax.invert_yaxis();ax.axvline(0,color='#777',ls='--',lw=.8);ax.set_xlabel('Paired balanced score improvement (%)');fig.tight_layout(pad=.2);save(fig,'tomat4')
# Actual route coordinates in side by side panels with identical axes within each case.
fig,axs=plt.subplots(2,2,figsize=(6.97,4.95))
for row,(case,base) in enumerate([('heldout_24','pso'),('heldout_02','pso_polished')]):
 c=next(x for x in P['cases'] if x['id']==case);route_arrays=[np.array(idx[case,0,m]['plan']['points']) for m in [base,'proposed_v4']];allp=np.concatenate(route_arrays);lo=np.maximum(allp.min(0)-3,-24);hi=np.minimum(allp.max(0)+3,24);span=max(hi-lo);mid=(lo+hi)/2;lo=mid-span/2;hi=mid+span/2
 for col,m in enumerate([base,'proposed_v4']):
  ax=axs[row,col];r=idx[case,0,m];p=np.array(r['plan']['points']);map=c['map']
  for patch in map['terrain_patches']:
   x0,x1,y0,y1=patch['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='#c4a982',alpha=.25))
  for a,b in map['obstacles']:ax.add_patch(Rectangle(a,b[0]-a[0],b[1]-a[1],color='#5e6264'))
  ax.plot(p[:,0],p[:,1],color='#285676' if m=='proposed_v4' else '#b67a32',lw=1.4,ls='-' if r['plan']['admissible'] else '--')
  ax.plot(*c['start'],'ko',ms=3);ax.plot(*c['goal'],'ks',ms=3);ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_aspect('equal');ax.set_xlabel('x (m)',fontsize=7);ax.set_ylabel('y (m)',fontsize=7);ax.tick_params(labelsize=7)
  ax.set_title(f"{case}: {N[m]}\nQ = {r['plan']['quality_score']:.6f}, {'admitted' if r['plan']['admissible'] else 'rejected'}",fontsize=7.4)
fig.tight_layout(pad=.5,h_pad=1,w_pad=1);save(fig,'tomat5')
# Physics tradeoff among strongest methods, success denominators in paper table.
chosen=['pso','aco','pso_polished','aco_polished','proposed_v4'];pr={r['method']:r for r in PH['summary']};fig,axs=plt.subplots(2,1,figsize=(3.35,3.05),sharex=True)
for ax,key,label in [(axs[0],'mean_task_time_s','Destination time (s)'),(axs[1],'mean_positive_work_j','Mission mechanical work (J)')]:
 vals=[pr[m][key] for m in chosen];ax.bar(np.arange(5),vals,color=['#aeb8c0']*4+['#285676']);ax.set_ylabel(label,fontsize=7.3);ax.set_ylim(0,max(vals)*1.18);ax.tick_params(labelsize=7)
 for i,v in enumerate(vals):ax.text(i,v+max(vals)*.02,f'{v:.2f}',ha='center',fontsize=6.4)
axs[1].set_xticks(range(5),['PSO','ACO','PSO\n+ polish','ACO\n+ polish','V4']);fig.tight_layout(pad=.3);save(fig,'tomat6')
# Verdict counts per family, all three repeats retained.
fig,ax=plt.subplots(figsize=(3.35,2.45));families=['open','clutter','rough','corridor'];bottom=np.zeros(4)
for verdict,label,col in [('V4 best score','V4 best','#285676'),('V4 tied best','Tied best','#aeb8c0'),('Another method scored lower','Other lower','#b67a32'),('All rejected','All rejected','#646b71')]:
 vals=[sum(x['verdict']==verdict and x['world_family']==f for x in C['case_verdicts']) for f in families];ax.bar(range(4),vals,bottom=bottom,label=label,color=col);bottom+=vals
ax.set_xticks(range(4),['Open','Clutter','Rough','Corridor']);ax.set_ylabel('World and repetition pairs');ax.set_ylim(0,18);ax.set_yticks([0,6,12,18]);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=2,frameon=False,fontsize=6.4);fig.tight_layout(pad=.2);save(fig,'tomat7')
print(json.dumps(dict(attempts=total,independent_comparisons=len(independent),preparation_mean_s=summary['preparation_mean_s'],prediction=prediction[-1],figures=7),indent=2))
