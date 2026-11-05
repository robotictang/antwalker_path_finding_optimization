"""Source-backed version 4 comparison figures, tables and a concise results readout."""
import argparse,collections,csv,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BASE=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--project-root',type=Path,default=BASE.parents[1]);args=parser.parse_args()
ROOT=args.project_root;S=ROOT/'mujoco/outputs/research/advanced_study_v4';FIG=BASE/'figures';FIG.mkdir(exist_ok=True)
def load(name):return json.loads((S/(name+'.json')).read_text())
primary=load('v4_heldout_planning');report=load('comparison');assert primary['state']=='complete'
N={'b1_distance':'Distance A*','b2_terrain':'Terrain A*','b3_energy':'Energy A*','b4_weighted':'Weighted A*','b7_greedy':'Greedy','pso':'PSO','aco':'ACO','proposed_v1':'Old grid proposal','proposed':'Proposal v3','pso_polished':'PSO + polishing','aco_polished':'ACO + polishing','proposed_v4':'Proposed v4'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
def save(fig,name):fig.savefig(FIG/(name+'.png'),dpi=200,bbox_inches='tight');plt.close(fig)
# Primary paired comparison preserves ties and non-admission outcomes.
rows=report['comparisons'];fig,ax=plt.subplots(figsize=(10,6));y=np.arange(len(rows));left=np.zeros(len(rows))
for key,label,color in [('wins','V4 lower score','#355d80'),('ties','Tie','#d1d6d9'),('losses','Baseline lower score','#bd8a45'),('proposed_only_admitted','Only V4 admitted','#7c9f91'),('baseline_only_admitted','Only baseline admitted','#d8b37e'),('both_rejected','Both rejected','#66717c')]:
 vals=np.array([r[key] for r in rows]);ax.barh(y,vals,left=left,color=color,label=label)
 for j,v in enumerate(vals):
  if v>=2:ax.text(left[j]+v/2,j,str(v),ha='center',va='center',fontsize=9,color='white' if key in ['wins','both_rejected'] else '#1e252c')
 left+=vals
ax.set_yticks(y,[N[r['baseline']] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Matched experiments per baseline   24 fresh worlds × 3 seeds');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.12),ncol=3,frameon=False,fontsize=9);fig.tight_layout();save(fig,'V4_Paired_Comparison')
# One table/heatmap cell per actual world repetition, not a fabricated best seed.
verdicts=report['case_verdicts'];classes=['V4 best score','V4 tied best','Another method scored lower','V4 rejected','All rejected'];counts=collections.Counter(r['verdict'] for r in verdicts)
fig,ax=plt.subplots(figsize=(10,3.2));labels=[v for v in classes if counts[v]];values=[counts[v] for v in labels]
ax.barh(np.arange(len(labels)),values,color=['#355d80' if v=='V4 best score' else '#8797a3' if v=='V4 tied best' else '#bd8a45' for v in labels]);ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis();ax.set_xlabel('World and paired repetition experiments out of 72');ax.set_xlim(0,max(values)*1.18)
for i,v in enumerate(values):ax.text(v+.4,i,str(v),va='center')
fig.tight_layout();save(fig,'V4_Each_Experiment')
# Score and runtime are separate objectives with complete denominator labels.
fig,axs=plt.subplots(1,2,figsize=(11,6));summary=primary['summary'];colors=['#355d80' if r['method']=='proposed_v4' else '#a8b2ba' for r in summary]
for ax,field,label in [(axs[0],'mean_quality_score','Mean score of admitted routes   lower is better'),(axs[1],'mean_planning_seconds','Mean planner wall seconds   lower is better')]:
 vals=[r[field] or 0 for r in summary];ax.barh(range(len(summary)),vals,color=colors);ax.set_yticks(range(len(summary)),[N[r['method']]+f" (n={r['admissible'] if field=='mean_quality_score' else r['attempts']})" for r in summary]);ax.invert_yaxis();ax.set_xlabel(label);ax.set_xlim(0,max(vals)*1.25)
 for i,(v,r) in enumerate(zip(vals,summary)):ax.text(v+max(vals)*.015,i,f'{v:.4f}' if field=='mean_quality_score' else f'{v:.3f}',va='center',fontsize=8)
fig.tight_layout();save(fig,'V4_Score_and_Runtime')
# Exact paired relative advantages with descriptive world intervals.
fig,ax=plt.subplots(figsize=(10,5))
for j,r in enumerate(rows):
 mean=r['mean_relative_score_improvement_percent'];ci=r['relative_improvement_95_percent']
 if mean is not None and ci:ax.errorbar(mean,j,xerr=[[max(0,mean-ci[0])],[max(0,ci[1]-mean)]],fmt='o',color='#355d80',capsize=4)
ax.set_yticks(range(len(rows)),[N[r['baseline']] for r in rows]);ax.invert_yaxis();ax.axvline(0,color='#69747c',ls='--',lw=1);ax.set_xlabel('Mean per-world paired balanced-score improvement %   positive favors V4');ax.set_title('Descriptive 95% intervals resample whole worlds; jointly admitted routes only',fontsize=10);fig.tight_layout();save(fig,'V4_Relative_Improvements')
with (BASE/'Every_Experiment.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=verdicts[0]);w.writeheader();w.writerows(verdicts)
with (BASE/'Paired_Comparison.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
lines=['# Hexapod version 4 measured comparison','29 October 2026','The new method adds obstacle/terrain landmarks and continuous waypoint movement to an initial safe route whose search cost counts toward the total budget. The common balanced score and resource checks are unchanged. Parameter tuning used 8 development worlds and two profiles per tuned optimizer. Test results use 24 fresh worlds and three paired seeds; the scientific code and manifest were frozen before testing.',
 'PSO and ACO with the same continuous polishing operator are included as stronger representation controls. Their baseline parameters come from development selection. No result from another method is used by the V4 planner. This is parameter tuning, not training a neural network.',
 '## Results in each experiment','\n'.join(f'- {k}: {v} of 72' for k,v in counts.items()),'A best-score verdict compares admitted balanced routes in one world/repetition. It does not mean best in every physical metric, fastest search, or universal superiority.',
 '## Complete paired comparisons','| Baseline | V4 wins | Ties | V4 losses | Only V4 admitted | Only baseline admitted | Both rejected | Mean world score improvement % |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:lines.append(f"| {N[r['baseline']]} | {r['wins']} | {r['ties']} | {r['losses']} | {r['proposed_only_admitted']} | {r['baseline_only_admitted']} | {r['both_rejected']} | {r['mean_relative_score_improvement_percent']:.4f} |")
lines+=['## Admission and computation','| Method | Admitted out of 72 | Mean admitted score | Mean planner seconds |','|---|---:|---:|---:|']
for r in summary:lines.append(f"| {N[r['method']]} | {r['admissible']} | {r['mean_quality_score']:.6f} | {r['mean_planning_seconds']:.4f} |")
lines+=['The balanced-score improvement over polished ACO is small and its descriptive relative-improvement interval crosses zero. This does not establish a decisive advantage over that stronger control. V4 also takes longer on average than several simpler methods. Conditional mean scores can cover different admitted worlds; the paired table is the direct comparison. Repeated seeds are clustered by world, not 72 independent maps. Relative score differences are not electrical-energy savings. Wall times include each method search but exclude common graph and return preparation. More complex methods may use more of the same time allowance.']
# Secondary analyses keep their own denominators and never enter tuning.
abl=S/'ablation_comparison.json'
if abl.exists():
 a=load('ablation_comparison');lines+=['## Feature removal tests','Eight preselected held-out worlds, three paired repetitions, 72 attempts. These tests measure the contribution of landmarks and polishing; settings were not revised from these results.','| V4 compared with | Wins | Ties | Losses | V4 only admitted | Both rejected |','|---|---:|---:|---:|---:|---:|']
 for r in a['comparisons']:lines.append(f"| {r['baseline']} | {r['wins']} | {r['ties']} | {r['losses']} | {r['proposed_only_admitted']} | {r['both_rejected']} |")
lines+=['The polishing ablation favors the full method, but landmark removal has mixed outcomes and an interval spanning zero on this eight-world subset. These data do not establish that every added component consistently helps.','## Shorter budget sensitivity','Four preselected held-out worlds per budget; 12 methods and one repetition. These small subsets are descriptive, not a replacement for the main test.','| Budget s | Baseline | V4 wins | Ties | V4 losses | Only V4 admitted | Only baseline admitted | Both rejected |','|---|---|---:|---:|---:|---:|---:|---:|']
def budget_counts(run):
 pairs={(r['case_id'],r['repeat'],r['method']):r['plan'] for r in run['records']}
 keys=sorted({(r['case_id'],r['repeat']) for r in run['records']});result=[]
 for method in run['methods']:
  if method=='proposed_v4':continue
  row=dict(baseline=method,wins=0,ties=0,losses=0,proposed_only_admitted=0,baseline_only_admitted=0,both_rejected=0)
  for case,repeat in keys:
   x=pairs[(case,repeat,'proposed_v4')];y=pairs[(case,repeat,method)]
   if x['admissible'] and y['admissible']:
    d=y['quality_score']-x['quality_score'];k='wins' if d>1e-8 else 'losses' if d< -1e-8 else 'ties'
   else:k='proposed_only_admitted' if x['admissible'] else 'baseline_only_admitted' if y['admissible'] else 'both_rejected'
   row[k]+=1
  result.append(row)
 return result
for budget in ['0p5','1p0']:
 path=S/('v4_budget_'+budget+'.json')
 if path.exists():
  b=load('v4_budget_'+budget)
  for r in budget_counts(b):
   lines.append(f"| {b['planning_budget_s']} | {N[r['baseline']]} | {r['wins']} | {r['ties']} | {r['losses']} | {r['proposed_only_admitted']} | {r['baseline_only_admitted']} | {r['both_rejected']} |")

physical=S/'v4_heldout_physics.json';audit=S/'audit.json';summ=S/'study_summary.json'
if physical.exists():
 ph=load('v4_heldout_physics')
 fig,axs=plt.subplots(1,3,figsize=(15,6),sharey=True);ps=ph['summary'];cs=['#355d80' if r['method']=='proposed_v4' else '#a8b2ba' for r in ps]
 for ax,field,label in [(axs[0],'success_rate','Successful / scheduled attempts'),(axs[1],'mean_task_time_s','Destination seconds, successful only'),(axs[2],'mean_positive_work_j','Mission mechanical joules, successful only')]:
  vals=[r[field] or 0 for r in ps];ax.barh(range(len(ps)),vals,color=cs);ax.set_xlabel(label);ax.set_yticks(range(len(ps)),[N[r['method']] for r in ps]);ax.set_ylim(len(ps)-.5,-.5);ax.set_xlim(0,max(vals)*1.3)
  for i,(v,r) in enumerate(zip(vals,ps)):ax.text(v+max(vals)*.02,i,f"{r['successes']}/{r['attempts']}" if field=='success_rate' else f'{v:.2f}',va='center',fontsize=8)
 fig.suptitle('Separate assisted physics: six preselected worlds; rejected plans remain in scheduled counts',fontsize=11);fig.tight_layout();save(fig,'V4_Physics_Comparison')
 lines+=['## Separate assisted physics','| Method | Scheduled | Executed | Succeeded | Mean destination s, successful only | Mean mission mechanical work J, successful only |','|---|---:|---:|---:|---:|---:|']
 for r in ph['summary']:lines.append(f"| {N[r['method']]} | {r['attempts']} | {r['executed']} | {r['successes']} | {r['mean_task_time_s']} | {r['mean_positive_work_j']} |")
 lines+=['Physical means include successful missions only. Scheduled, executed and successful counts must be read together. Mechanical work excludes unmodeled body assistance and is not electrical battery energy. The controller still assists body velocity/posture and gravity compensation. Rejected plans and execution failures remain in scheduled denominators.']
else:lines+=['## Separate assisted physics','Physics checks are still running. The planning figures do not establish measured mission success.']
if audit.exists():lines+=['## Audit','```json\n'+json.dumps(load('audit'),indent=2)+'\n```']
lines+=['## Reproduce','From mujoco: python3 -m research.advanced_study','To recreate figures from the delivered source folder: python make_results.py --project-root /path/to/hexapod_asset. This reads saved records and needs numpy and matplotlib; it does not rerun the experiment.','Source records: mujoco/outputs/research/advanced_study_v4. Every_Experiment.csv shows all 72 paired world/repetition verdicts. Paired_Comparison.csv retains complete counts and descriptive world intervals.',
 '## Publication scope','Version 3 Word documents describe the earlier frozen study. These version 4 results are a separate update and must be incorporated and reviewed before manuscript submission. The proposed representation and polishing use established motion-planning ideas; no universal novelty or dominance theorem is claimed. Electrical calibration and physical robot validation remain outstanding.',
 'Method references: [OMPL path simplification](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1PathSimplifier.html) and [OMPL anytime path shortening](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1AnytimePathShortening.html). These references provide background; V4 is a project-specific implementation, not an exact reproduction.']
text=''
for i,line in enumerate(lines):
 text+=('\n' if i and line.startswith('|') and lines[i-1].startswith('|') else '\n\n' if i else '')+line
(BASE/'V4_Results_Summary.md').write_text(text+'\n')
(BASE/'source/analysis_provenance.json').write_text(json.dumps(dict(primary_run=primary['run_id'],manifest_sha256=primary['study']['manifest_sha256'],case_verdict_counts=dict(counts),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in S.glob('*.json')},physics_complete=physical.exists(),audit_available=audit.exists()),indent=2))
print(json.dumps(dict(primary_run=primary['run_id'],verdicts=dict(counts),attempts=len(primary['records'])),indent=2))
