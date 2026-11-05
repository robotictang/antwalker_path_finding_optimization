import json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,FancyBboxPatch
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];FIG=BASE/'figures';S=ROOT/'mujoco/outputs/research/strong_study_v3'
A=json.loads((BASE/'source/verified_analysis.json').read_text());P=json.loads((S/'v3_heldout_planning.json').read_text());PH=json.loads((S/'v3_heldout_physics.json').read_text())
N={'b1_distance':'Distance A*','b3_energy':'Energy A*','b7_greedy':'Greedy','pso':'PSO hybrid','aco':'ACO hybrid','proposed':'Proposed'}
colors=['#5d7387','#b47d39','#8796a5','#68609b','#b7645b','#22664d']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
def save(fig,name):fig.savefig(FIG/(name+'.png'),dpi=210,bbox_inches='tight');plt.close(fig)
def flow(name,boxes,arrows,size=(8,3)):
 fig,ax=plt.subplots(figsize=size);ax.axis('off')
 for x,y,w,h,label in boxes:
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.008',transform=ax.transAxes,facecolor='#edf2f6',edgecolor='#687b8a'))
  ax.text(x+w/2,y+h/2,label,ha='center',va='center',transform=ax.transAxes,fontsize=9)
 for a,b in arrows:ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':'#516575'})
 save(fig,name)
flow('system',[(.01,.60,.28,.27,'Research Lab\nChoose settings and run'),(.36,.60,.28,.27,'One world specification\nPlanner and MuJoCo'),(.71,.60,.28,.27,'Matched method trials\nRecord every attempt'),(.01,.10,.28,.27,'Integrity audit\nHashes and calculations'),(.36,.10,.28,.27,'Saved JSON and CSV\nRoutes and diagnostics'),(.71,.10,.28,.27,'Method Comparison\nCharts and source records')],[((.30,.735),(.35,.735)),((.65,.735),(.70,.735)),((.85,.59),(.85,.46)),((.85,.46),(.50,.46)),((.50,.46),(.50,.39)),((.35,.235),(.30,.235)),((.65,.235),(.70,.235))])
flow('adaptive',[(.01,.60,.28,.27,'Energy seed to 0.6 s\n30,000 expansion cap'),(.36,.60,.28,.27,'Resume to 1.4 s\nif time or cap stopped it'),(.71,.60,.28,.27,'Distance seed to 1.8 s\nRemaining expansions'),(.01,.10,.28,.27,'Safe original seeds\nand greedy shortcuts'),(.36,.10,.28,.27,'PSO or ACO or labels\nwithin remaining budget'),(.71,.10,.28,.27,'Common final evaluator\nAdmit or reject and save')],[((.30,.735),(.35,.735)),((.65,.735),(.70,.735)),((.85,.59),(.85,.46)),((.85,.46),(.15,.46)),((.15,.46),(.15,.39)),((.30,.235),(.35,.235)),((.65,.235),(.70,.235))])
flow('calibration',[(.01,.60,.28,.27,'External electrical sensor\nMeasured Wh and capacity'),(.36,.60,.28,.27,'Disjoint missions and maps\nFit and held out groups'),(.71,.60,.28,.27,'Nonnegative linear fit\nFour walking coefficients'),(.01,.10,.28,.27,'Inspect held out errors\nMAE RMSE and bias'),(.36,.10,.28,.27,'Review sensor and model\nCheck model assumptions'),(.71,.10,.28,.27,'Apply a fitted profile\nTest on new missions')],[((.30,.735),(.35,.735)),((.65,.735),(.70,.735)),((.85,.59),(.85,.46)),((.85,.46),(.15,.46)),((.15,.46),(.15,.39)),((.30,.235),(.35,.235)),((.65,.235),(.70,.235))])
def draw_world(ax,case,route=None):
 w=case['world']
 for p in w['patches']:
  x0,x1,y0,y1=p['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,color='#ceb98e',alpha=.5 if p['grade']==1 else .8))
 for b in w['obstacles']:ax.add_patch(Rectangle((b['x']-b['sx'],b['y']-b['sy']),2*b['sx'],2*b['sy'],color='#59636e'))
 for s in w['stations']:ax.plot(*s['pos'],'^',color='#797f84',ms=5)
 ax.plot(*case['start'],'o',color='#111111',ms=5);ax.plot(*case['goal'],'s',color='#111111',ms=5)
 if route:
  q=np.asarray(route);ax.plot(q[:,0],q[:,1],color='#22664d',lw=2)
 ax.set_xlim(-24,24);ax.set_ylim(-24,24);ax.set_aspect('equal');ax.set_xlabel('x in metres');ax.set_ylabel('y in metres')
fig,axs=plt.subplots(2,2,figsize=(8,6.4))
for ax,c in zip(axs.flat,P['cases'][:4]):draw_world(ax,c);ax.set_title(c['id']+'   '+c['world']['family'])
fig.tight_layout();save(fig,'worlds')
fig,ax=plt.subplots(figsize=(8,3.2));y=np.arange(6);ad=np.array([r['admissible'] for r in A['planning']]);rej=72-ad
ax.barh(y,ad,color='#22664d',label='Admitted');ax.barh(y,rej,left=ad,color='#9b6157',label='Resource rejected')
for i,(a,b) in enumerate(zip(ad,rej)):ax.text(a/2,i,str(a),ha='center',va='center',color='white');ax.text(a+b/2,i,str(b),ha='center',va='center',color='white')
ax.set_yticks(y,[N[m] for m in A['methods']]);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Attempts   24 worlds × 3 repeats per method');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.22),ncol=2,frameon=False);fig.tight_layout();save(fig,'admission')
# Outcomes retain all scheduled pairs.
fig,ax=plt.subplots(figsize=(8,3.2));rr=A['comparison']['comparisons'];left=np.zeros(5)
for key,label,c in [('wins','Proposed lower score','#22664d'),('ties','Tie','#c7cdd1'),('losses','Baseline lower score','#b7645b'),('proposed_only_admitted','Only proposed admitted','#70a9aa'),('baseline_only_admitted','Only baseline admitted','#dda15c'),('both_rejected','Both rejected','#565f69')]:
 vals=np.array([x[key] for x in rr]);ax.barh(np.arange(5),vals,left=left,color=c,label=label)
 for j,v in enumerate(vals):
  if v:ax.text(left[j]+v/2,j,str(v),ha='center',va='center',fontsize=9,color='white' if key in ['wins','both_rejected'] else '#17212b')
 left+=vals
ax.set_yticks(np.arange(5),[N[x['baseline']] for x in rr]);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Matched attempts per baseline');ax.legend(loc='upper center',bbox_to_anchor=(.45,-.23),ncol=3,frameon=False,fontsize=8);fig.tight_layout();save(fig,'paired')
# Exact saved world bootstrap intervals; two scales are visibly separated.
fig,axs=plt.subplots(1,2,figsize=(8,3.2),gridspec_kw={'width_ratios':[1.4,1]})
for ax,indices,title in [(axs[0],range(5),'All baseline comparisons'),(axs[1],[3,4],'Expanded PSO and ACO scale')]:
 group=[rr[i] for i in indices]
 for j,row in enumerate(group):
  factor=1000 if len(group)==2 else 1
  mean=row['mean_layout_score_advantage']*factor;lo,hi=np.array(row['descriptive_layout_bootstrap_95_percent'])*factor;ax.errorbar(mean,j,xerr=[[mean-lo],[hi-mean]],fmt='o',color='#22664d',capsize=4)
 ax.set_yticks(range(len(group)),[N[x['baseline']] for x in group]);ax.invert_yaxis();ax.axvline(0,color='#67737d',lw=1,ls='--');ax.set_title(title,fontsize=10);ax.set_xlabel('Score advantage (units of 0.001)' if len(group)==2 else 'Baseline score minus proposed score',fontsize=9);ax.ticklabel_format(axis='x',style='plain',useOffset=False)
fig.tight_layout();save(fig,'intervals')
fig,ax=plt.subplots(figsize=(7,2.9));toy=[('A',24,11),('B',22,12),('C',26,14)]
for label,t,e in toy:ax.scatter(t,e,color='#22664d' if label!='C' else '#9b6157',s=70);ax.annotate(label,(t,e),xytext=(8,3),textcoords='offset points')
ax.set_xlabel('Illustrative time in seconds');ax.set_ylabel('Illustrative battery points');ax.set_xlim(20,28);ax.set_ylim(10,15);ax.grid(alpha=.15);ax.text(.02,.95,'Teaching example only\nA and B trade time against battery\nC is dominated by both',transform=ax.transAxes,va='top',fontsize=9);fig.tight_layout();save(fig,'pareto_example')
fig,axs=plt.subplots(1,2,figsize=(8,3.3));m=PH['methods']
for ax,field,label in [(axs[0],'mean_task_time_s','Mean destination time in seconds'),(axs[1],'mean_positive_work_j','Mean mission mechanical work in joules')]:
 vals=[r[field] for r in A['physics']];ax.barh(range(6),vals,color=colors);ax.set_yticks(range(6),[N[x] for x in m]);ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.16);ax.set_xlabel(label)
 for i,v in enumerate(vals):ax.text(v+max(vals)*.015,i,f'{v:.2f}' if field=='mean_task_time_s' else f'{v:.0f}',va='center',fontsize=8)
fig.tight_layout();save(fig,'physics')
fig,ax=plt.subplots(figsize=(8,3.25));completed=[x for x in PH['records'] if x.get('execution',{}).get('task_time_s') is not None]
for c,m in zip(colors,PH['methods']):
 g=[x for x in completed if x['method']==m];ax.scatter([x['plan']['metrics']['estimated_seconds'] for x in g],[x['execution']['task_time_s'] for x in g],label=N[m],color=c,s=30,alpha=.7)
maxv=max(x['plan']['metrics']['estimated_seconds'] for x in completed)*1.05;ax.plot([0,maxv],[0,maxv],'--',color='#67737d',label='Perfect prediction');ax.set_xlim(0,maxv);ax.set_ylim(0,maxv);ax.set_xlabel('Predicted destination seconds');ax.set_ylabel('Executed destination seconds');ax.legend(loc='center left',bbox_to_anchor=(1,.5),frameon=False,fontsize=8);fig.tight_layout();save(fig,'prediction')
case=next(c for c in P['cases'] if c['id']=='heldout_22');fig,axs=plt.subplots(1,2,figsize=(8,4))
for ax,m in zip(axs,['aco','proposed']):
 row=next(r for r in P['records'] if r['case_id']==case['id'] and r['method']==m and r['repeat']==0);draw_world(ax,case,row['plan']['points']);ax.set_title(N[m]+f"   Q = {row['plan']['quality_score']:.6f}",fontsize=10)
fig.tight_layout();save(fig,'case22')
print('Created',len(list(FIG.glob('*.png'))),'source-backed or explicitly illustrative figures')
