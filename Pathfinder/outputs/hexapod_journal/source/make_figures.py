"""Source-backed manuscript figures. No values or routes are synthesized."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,Rectangle
from matplotlib.ticker import MaxNLocator
ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).resolve().parents[1];FIG=BASE/'figures'
STUDY=(BASE/'evidence/reliability_v1') if (BASE/'evidence/reliability_v1').exists() else ROOT/'mujoco/outputs/research/reliability_v1'
P=json.loads((STUDY/'heldout_planning.json').read_text());A=json.loads((BASE/'source/verified_analysis.json').read_text())
COLORS={'pso':'#0072B2','aco':'#D55E00','proposed':'#009E73'}
NAMES={'pso':'PSO hybrid','aco':'ACO hybrid','proposed':'Proposed'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
FIG.mkdir(parents=True,exist_ok=True)
def save(fig,name):
 for suffix in ['png','svg','pdf']:fig.savefig(FIG/(name+'.'+suffix),dpi=300,bbox_inches='tight',facecolor='white')
 plt.close(fig)
def box(ax,xy,w,h,text,color='#EEF4F8',fontsize=10):
 ax.add_patch(FancyBboxPatch(xy,w,h,boxstyle='round,pad=0.015,rounding_size=.025',facecolor=color,edgecolor='#607080',linewidth=.9))
 ax.text(xy[0]+w/2,xy[1]+h/2,text,ha='center',va='center',fontsize=fontsize)
def arrow(ax,a,b):ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#43515D','lw':1.2})
# Figure 1: architecture, with interfaces separated from scientific components.
f,ax=plt.subplots(figsize=(7,3.9));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,(.02,.74),.26,.19,'Research Lab\nSet experiment\nparameters')
box(ax,(.37,.74),.26,.19,'Common model\nTerrain and\ncollision checks')
box(ax,(.72,.74),.26,.19,'Route search\nPSO, ACO and\nproposed method')
arrow(ax,(.28,.835),(.37,.835));arrow(ax,(.63,.835),(.72,.835))
box(ax,(.72,.39),.26,.2,'Resource checks\nTime, battery\nand terrain')
arrow(ax,(.85,.74),(.85,.59))
box(ax,(.37,.39),.26,.2,'Accepted plan\nOptional assisted\nphysics')
arrow(ax,(.72,.49),(.63,.49))
box(ax,(.02,.39),.26,.2,'Saved records\nAll outcomes\nand route data')
arrow(ax,(.37,.49),(.28,.49));arrow(ax,(.85,.39),(.85,.27));arrow(ax,(.85,.27),(.06,.27));arrow(ax,(.06,.27),(.06,.39))
ax.text(.58,.29,'Rejected plans are also saved',ha='center',fontsize=9)
box(ax,(.37,.015),.30,.13,'Comparison website\nCharts and trial records',fontsize=9)
arrow(ax,(.25,.39),(.25,.08));arrow(ax,(.25,.08),(.37,.08));ax.text(.835,.065,'Assisted motion\nNo validation of\nunassisted balance',ha='center',fontsize=8.5)
save(f,'figure_1_system')
# Figure 2: algorithm flow. Labels describe actual implementation.
f,ax=plt.subplots(figsize=(7,3.7));ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
box(ax,(.24,.83),.52,.13,'Common initialization\nEnergy, time and distance A* seeds')
for x in [.16,.5,.84]:arrow(ax,(.5,.83),(x,.70))
box(ax,(.02,.46),.28,.24,'PSO hybrid\nWaypoint keys\nPersonal and global best\nRepair unsafe skips','#EAF3FA',9.5)
box(ax,(.36,.46),.28,.24,'ACO hybrid\nVisible forward nodes\nPheromone reinforcement\nEvaporation','#FFF1E8',9.5)
box(ax,(.70,.46),.28,.24,'Proposed method\nResource labels\nDominance pruning\nLabels capped per state','#E7F5EF',9.5)
for x in [.16,.5,.84]:arrow(ax,(x,.46),(x,.31))
box(ax,(.02,.18),.96,.13,'Common continuous evaluation and feasibility-first ranking\nRetain the best accepted route; report all rejected or empty outcomes',fontsize=10)
ax.text(.5,.045,'A* seed searches receive 30% of the nominal 2 s allowance.\nThe search is restricted to safe seed corridors and forward shortcuts.',ha='center',fontsize=9)
save(f,'figure_2_algorithms')
# Figure 3: categories are disjoint and denominator is explicit.
f,ax=plt.subplots(figsize=(7,3.2));bottom=np.zeros(3);cats=[('found','Accepted','#009E73'),('resource_rejected','Resource rejected','#E69F00'),('no_route','No route returned','#8B969D')]
for key,label,color in cats:
 values=[s['counts'].get(key,0) for s in A['planning_summary']]
 ax.barh(range(3),values,left=bottom,color=color,label=label,height=.52)
 for i,v in enumerate(values):
  if v:ax.text(bottom[i]+v/2,i,str(v),ha='center',va='center',color='white' if key!='resource_rejected' else '#151515',fontweight='bold')
 bottom+=values
ax.set(yticks=range(3),yticklabels=[NAMES[m] for m in COLORS],xlabel='Planning attempts per method (36 total)',xlim=(0,36));ax.invert_yaxis();ax.xaxis.set_major_locator(MaxNLocator(integer=True));ax.legend(ncols=3,loc='upper center',bbox_to_anchor=(.5,1.2),frameon=False,fontsize=9)
ax.text(1,-.25,'12 sampled task/obstacle layouts × 3 seeds; one fixed base terrain',transform=ax.transAxes,ha='right',fontsize=9)
save(f,'figure_3_outcomes')
# Figure 4: show absolute paired differences on jointly accepted layouts.
f,axes=plt.subplots(1,2,figsize=(7,3.3),sharey=True)
for ax,b in zip(axes,['pso','aco']):
 rows=[x for x in A['layout_deltas'] if x['baseline']==b]
 y=np.arange(len(rows));ax.scatter([1000*x['delta'] for x in rows],y,s=55,color=COLORS[b],zorder=3)
 for i,x in enumerate(rows):ax.plot([0,1000*x['delta']],[i,i],color=COLORS[b],lw=2)
 ax.axvline(0,color='#666',lw=1,ls='--');ax.set(yticks=y,yticklabels=[x['case'].replace('heldout_','Layout ') for x in rows],title='Versus '+NAMES[b],xlabel='Score advantage (×10⁻³)');ax.set_xlim(-.3,4.3);ax.margins(y=.3);ax.grid(axis='x',alpha=.2)
f.text(.5,-.03,'Positive differences favor proposed; each point averages 3 paired seeds. Only 3 layouts qualify.',ha='center',fontsize=9)
f.tight_layout();save(f,'figure_4_paired_scores')
# Figure 5: measured wall time, averaged within each sampled layout.
f,ax=plt.subplots(figsize=(7,3.6))
for i,m in enumerate(COLORS):
 vals=[]
 for c in P['cases']:
  r=[x['plan']['planning_seconds'] for x in P['records'] if x['case_id']==c['id'] and x['method']==m]
  vals.append(float(np.mean(r)))
 offsets=np.linspace(-.13,.13,len(vals));ax.scatter(np.full(len(vals),i)+offsets,vals,color=COLORS[m],s=30,alpha=.85)
 ax.plot([i-.22,i+.22],[np.mean(vals)]*2,color='black',lw=2)
ax.axhline(2.,ls='--',color='#777',lw=1);ax.text(2.38,2.02,'Nominal budget',ha='right',va='bottom',fontsize=9)
ax.set(xticks=range(3),xticklabels=[NAMES[m] for m in COLORS],ylabel='Planning wall time (seconds)',ylim=(0,2.18),xlim=(-.45,2.45));ax.grid(axis='y',alpha=.2)
f.text(.5,-.02,'Dots: 12 layout means per method. Black bars: overall means. Shared preparation is excluded.',ha='center',fontsize=9)
save(f,'figure_5_runtime')
# Figure 6: first two accepted layouts; no offsets applied to make routes differ.
f,axes=plt.subplots(1,2,figsize=(7,4.0))
for ax,case_id in zip(axes,['heldout_03','heldout_04']):
 c=next(c for c in P['cases'] if c['id']==case_id);mp=c['map']
 routes={m:next(x['plan']['points'] for x in P['records'] if x['case_id']==case_id and x['repeat']==0 and x['method']==m) for m in COLORS}
 allpoints=np.array([p for points in routes.values() for p in points]);lo=allpoints.min(0)-3;hi=allpoints.max(0)+3
 for a,b in mp['obstacles']:
  if b[0]>=lo[0] and a[0]<=hi[0] and b[1]>=lo[1] and a[1]<=hi[1]:ax.add_patch(Rectangle(a,b[0]-a[0],b[1]-a[1],fc='#D8DDE0',ec='#8A949B',lw=.3))
 for m,style,width in [('pso','-',2.7),('aco','--',1.8),('proposed',':',1.5)]:
  points=np.array(routes[m]);ax.plot(points[:,0],points[:,1],style,lw=width,color=COLORS[m],label=NAMES[m])
 ax.scatter(*mp['start'],marker='o',c='black',s=25,zorder=4);ax.scatter(*mp['goal'],marker='*',c='black',s=55,zorder=4)
 ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),xlabel='x (m)',ylabel='y (m)',title=case_id.replace('heldout_','Layout ')+' · seed repetition 1');ax.set_aspect('equal');ax.grid(alpha=.15)
axes[1].legend(frameon=False,loc='upper left',fontsize=8)
f.text(.5,.005,'Circle: start. Star: destination. Gray: obstacle boxes. Coincident paths are drawn without offsets.',ha='center',fontsize=8.5)
f.tight_layout(rect=(0,.04,1,1));save(f,'figure_6_routes')
print('Created',len(list(FIG.glob('*.png'))),'figures with PNG, SVG and PDF copies')
