"""Build a concise, source-backed v3 supervisor supplement from completed study files."""
import json,math,shutil,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];STUDY=ROOT/'mujoco/outputs/research/strong_study_v3';FIG=BASE/'figures'
def load(name):return json.loads((STUDY/(name+'.json')).read_text())
report=load('comparison');primary=load('v3_heldout_planning');physics=load('v3_heldout_physics');ablation=load('ablation_comparison');diagnostic=load('v3_old_case_seed_diagnostic');audit=load('audit');summary=load('study_summary')
assert physics['state']=='complete' and audit['state']=='passed'
names={'b1_distance':'Distance A*','b3_energy':'Energy A*','b7_greedy':'Greedy shortcuts','pso':'PSO hybrid','aco':'ACO hybrid','proposed':'Proposed v3','proposed_fixed':'Fixed seed time','proposed_single':'One seed family','proposed_unpruned':'No resource pruning'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','savefig.facecolor':'white'})
# Recorded outcomes remain separated from software correctness fixtures.
fig,ax=plt.subplots(figsize=(8,3.25));rows=report['comparisons'];y=np.arange(len(rows));left=np.zeros(len(rows))
for key,label,color in [('wins','Proposed lower score','#22664d'),('ties','Equal score','#c7cdd1'),('losses','Baseline lower score','#ac5a42'),('proposed_only_admitted','Only proposed admitted','#70a9aa'),('baseline_only_admitted','Only baseline admitted','#dda15c'),('both_rejected','Both rejected','#565f69')]:
    values=np.array([r[key] for r in rows]);ax.barh(y,values,left=left,label=label,color=color)
    for j,v in enumerate(values):
        if v:ax.text(left[j]+v/2,j,str(v),ha='center',va='center',color='white' if key in ['wins','both_rejected'] else '#17212b',fontsize=9)
    left+=values
ax.set_yticks(y,[names[r['baseline']] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,72);ax.set_xlabel('Paired attempts per baseline   24 worlds × 3 seeds');ax.legend(loc='upper center',bbox_to_anchor=(.45,-.25),ncol=3,frameon=False,fontsize=8);fig.tight_layout();fig.savefig(FIG/'paired_outcomes.png',dpi=200,bbox_inches='tight');plt.close(fig)
# Actual deterministic flow of the implemented method, not empirical outcomes.
fig,ax=plt.subplots(figsize=(8,2.8));ax.axis('off')
boxes=[(.02,.58,.27,.27,'Energy A* seed\nfirst 30% of budget'),(.365,.58,.27,.27,'Resume saved frontier\nup to 70% if needed'),(.71,.58,.27,.27,'Distance seed fallback\nup to 90% if needed'),(.02,.10,.27,.27,'Keep safe seed routes\nand greedy shortcuts'),(.365,.10,.27,.27,'Bounded Pareto labels\nwith resource pruning'),(.71,.10,.27,.27,'Recheck all limits\nand save every outcome')]
for x,y,w,h,label in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.012',transform=ax.transAxes,facecolor='#edf2f6',edgecolor='#576a7b'))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',transform=ax.transAxes,fontsize=10)
for a,b in [((.30,.715),(.35,.715)),((.645,.715),(.695,.715)),((.30,.235),(.35,.235)),((.645,.235),(.695,.235)),((.845,.56),(.845,.45)),((.845,.45),(.15,.45)),((.15,.45),(.15,.39))]:ax.annotate('',xy=b,xytext=a,xycoords='axes fraction',arrowprops={'arrowstyle':'->','color':'#576a7b'})
fig.savefig(FIG/'planner_flow.png',dpi=200,bbox_inches='tight');plt.close(fig)
# Time forecast check on actually executed destination legs.
executed=[r for r in physics['records'] if r.get('execution')];completed=[r for r in executed if r['execution']['task_time_s'] is not None]
fig,ax=plt.subplots(figsize=(8,3.1));palette=plt.get_cmap('tab10')
for i,m in enumerate(physics['methods']):
    group=[r for r in completed if r['method']==m]
    ax.scatter([r['plan']['metrics']['estimated_seconds'] for r in group],[r['execution']['task_time_s'] for r in group],label=names[m],s=30,alpha=.75,color=palette(i))
maxv=max(max(r['plan']['metrics']['estimated_seconds'],r['execution']['task_time_s']) for r in completed)*1.06
ax.plot([0,maxv],[0,maxv],'--',color='#737c84',lw=1,label='Perfect time prediction');ax.set_xlim(0,maxv);ax.set_ylim(0,maxv);ax.set_xlabel('Predicted destination time in seconds');ax.set_ylabel('Executed destination time in seconds');ax.legend(loc='center left',bbox_to_anchor=(1.01,.5),frameon=False,fontsize=8);fig.tight_layout();fig.savefig(FIG/'time_validation.png',dpi=200,bbox_inches='tight');plt.close(fig)
D=Document();sec=D.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11);sec.top_margin=sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
for n,size in [('Normal',11),('Title',21),('Heading 1',14),('Heading 2',12),('Caption',9)]:
    st=D.styles[n];st.font.name='Arial';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0);st.paragraph_format.space_after=Pt(6)
D.styles['Normal'].paragraph_format.line_spacing=1.1
for st in D.styles:
    for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
for n in ['Title','Heading 1','Heading 2']:D.styles[n].paragraph_format.keep_with_next=True
D.core_properties.title='Hexapod version 3 improvements and evidence';D.core_properties.author='Hexapod research project';D.core_properties.subject='Audited simulation results and practical next steps'
text=[]
def p(t,style=None):text.append(t);return D.add_paragraph(t,style)
def h(t):return p(t,'Heading 1')
def pic(file,caption,width=6.8):
    par=D.add_paragraph();par.paragraph_format.keep_with_next=True;par.alignment=WD_ALIGN_PARAGRAPH.CENTER
    shape=par.add_run().add_picture(str(FIG/file),width=Inches(width));shape._inline.docPr.set('descr',caption);p(caption,'Caption')
def table(headers,rows):
    t=D.add_table(rows=1,cols=len(headers));t.style='Light Shading Accent 1'
    for c,label in zip(t.rows[0].cells,headers):c.text=str(label)
    for row in rows:
        for c,v in zip(t.add_row().cells,row):c.text=str(v)
    for i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if i==0:trpr.append(OxmlElement('w:tblHeader'))
        for c in row.cells:
            for par in c.paragraphs:
                par.paragraph_format.space_after=Pt(4);par.paragraph_format.space_before=Pt(3)
                for r in par.runs:r.font.size=Pt(9);r.bold=i==0
    text.append(' | '.join(headers));text.extend(' | '.join(map(str,row)) for row in rows)
def page():D.add_page_break()
p('Hexapod version 3 improvements and evidence','Title')
p('Supervisor supplement   28 October 2026','Subtitle')
p('The project now has a more robust planner and a stronger comparison protocol. The completed study contains 684 scheduled attempts. The proposal improved the declared route score over simple A* baselines, while PSO and ACO usually found the same score. Real robot and electrical battery validation remain outstanding.')
h('What was improved')
p('An unfinished energy A* search can now resume from its saved work. If necessary, a distance A* search supplies another safe starting route. PSO, ACO, greedy and the proposal share this adaptive initialization rule. The proposal then searches safe shortcuts using bounded Pareto labels, keeping routes that offer useful distance, time, energy and terrain trade-offs.')
pic('planner_flow.png','Figure 1. Implemented planning flow. All stages share the same total planner budget. Seed stages may finish earlier than their limits.',6.8)
p('The new worlds vary obstacles, shallow terrain tiles, terrain severity and friction. The planner and MuJoCo read the same world specification. Each saved result records seeds, parameters, source hashes, model hashes, timing and rejection reasons.')
h('What the study contains')
table(['Phase','Worlds or cases','Attempts'],[['Parameter development','8 new worlds and two settings',96],['Held out planning','24 new worlds and six methods',432],['Feature removal','First 8 held out worlds and four variants',96],['Old timeout diagnosis','2 previously inspected cases',24],['Assisted physics','First 6 held out worlds and six methods',36]])
p('The 24 small synthetic reference graphs are separate software checks. They are not additional robot experiments. Repeated optimizer seeds are not independent worlds.','Caption')
page();h('What the held out planning results show')
p('Each method received the same 24 test worlds, three paired seeds per world and a 2 second maximum planning budget. Settings were selected on separate development worlds and frozen before testing. A route is admitted only if its deadline, modeled battery plus return reserve, and terrain exposure satisfy their limits.')
table(['Method','Admitted out of 72','Mean admitted score','Mean planner seconds'],[[names[r['method']],r['admissible'],f"{r['mean_quality_score']:.6f}",f"{r['mean_planning_seconds']:.3f}"] for r in primary['summary']])
p('Mean scores above can cover different admitted worlds. Use the paired results below for direct comparisons. Lower score is better under the chosen weights. Planning time excludes shared model and graph preparation, which is recorded separately. These wall times are not isolated CPU microbenchmarks.','Caption')
pic('paired_outcomes.png','Figure 2. Every baseline comparison contains 72 paired attempts. Score comparisons require both routes to be admitted. Ties and rejections remain visible.',6.8)
p('Against PSO, the proposal had 3 lower scores, 63 ties and no higher scores among 66 jointly admitted trials. Against ACO, it had 9 lower scores, 57 ties and no higher scores. Both comparisons had 6 jointly rejected attempts. Admission was identical at 66 of 72. These results support small modeled-score gains in some cases, not a broad superiority claim.')
p('The mean world score advantage over PSO was 0.000245, with a descriptive 95% world bootstrap interval from 0 to 0.000734. Against ACO it was 0.000423, with interval 0.000000730 to 0.001038. Intervals resample whole worlds after averaging seeds and condition on joint admission; multiple comparisons and the restricted simulated distribution limit interpretation.')
p('Common score = distance / 50 + predicted seconds / 90 + modeled battery percentage points / 30 + 0.25 × terrain exposure / 20. A percentage score change is not a percentage electrical energy saving.','Caption')
page();h('Which features helped')
table(['Feature removed','Proposed lower score','Ties','Proposed higher score'],[[names[r['baseline']],r['wins'],r['ties'],r['losses']] for r in ablation['comparisons']])
p('Using several seed families helped in 12 of the 24 paired trials in this eight-world subset. Fixed seed time and removing resource pruning produced the same scores as the full proposal in all 24 pairs. Those features therefore have no demonstrated output advantage in this subset. A larger or more difficult independent test is needed before claiming their general benefit.')
control=[r for r in diagnostic['records'] if r['method']=='proposed_fixed'];new=[r for r in diagnostic['records'] if r['method']=='proposed']
p(f"On the two old timeout cases, the fixed-time control returned metrics in {sum(bool(r.get('plan',{}).get('metrics')) for r in control)} of {len(control)} attempts. The adaptive proposal returned metrics in {sum(bool(r.get('plan',{}).get('metrics')) for r in new)} of {len(new)}. The resulting routes still failed the resource limits. Recovering a route fixes lost planning effort; it does not create extra battery capacity. These previously inspected cases are diagnostic evidence only.")
h('What the physics trials show')
table(['Method','Scheduled','Executed','Successful'],[[names[r['method']],r['attempts'],r['executed'],r['successes']] for r in physics['summary']])
pic('time_validation.png','Figure 3. Predicted and executed destination times on trials that reached the destination. Points may overlap when methods use identical routes.',6.4)
errors=[r['prediction_validation']['task_time_error_s'] for r in completed];battery=[r['prediction_validation']['task_battery_error_pp'] for r in completed]
p(f"Across {len(completed)} destination-reaching executions, mean absolute time prediction error was {np.mean(np.abs(errors)):.3f} seconds. Mean absolute modeled battery prediction error was {np.mean(np.abs(battery)):.3f} percentage points. The latter compares two simulation quantities, not an electrical sensor.")
page();h('How to inspect the changes')
for line in ['1. Open http://127.0.0.1:8771/ on this computer. The updated comparison is at http://127.0.0.1:8771/comparison/.','2. Start with the saved v3 held out planning run. Use a single scenario and repetition before reading aggregate charts. The paired score chart makes small differences and exact ties visible.','3. Choose heldout_22, repetition 1 and ACO for an example with different scores. The proposed composite score is about 0.0763% lower. This is a very small modeled-score difference.','4. For feature-removal or physics results, use the study links in the console, select that run, then click Use selected run in charts. Refresh the comparison tab.','5. To run your own check, choose New worlds with 4 terrains, six methods, 1 repetition, a 2 second budget, walking only and Planning only. Keep seed 1050000 to repeat the same four worlds. Change the seed for new worlds.','6. Follow with physics on the same settings. Read rejection and failure reasons. An unavailable measured value means the trial was not executed or never reached the relevant stage.']:
    p(line)
h('What still needs real measurements')
p('The battery model is still nominal. A new fitter accepts externally measured electrical energy, requires separate calibration and validation missions and maps, and reports held-out prediction error. The supplied empty CSV and metadata template explain the inputs. No calibration measurements were invented.')
p('The software minimum is 12 calibration observations and 6 validation observations with at least three distinct missions in each split. Vary speed, distance and turning. These counts are input safeguards, not a justified publication sample size. Choose a larger study using expected variation, the effect size you need to detect and supervisor advice.')
p('The robot still receives assisted body velocity and posture with gravity compensation. Mechanical actuator work is not electrical consumption. Terrain exposure is a difficulty proxy, not a fall probability. New simulations alone cannot establish real robot stability, battery accuracy or universal superiority.')
h('What to do before journal submission')
p('Use this version 3 evidence to revise the earlier version 1 manuscript. Verify the precise novelty against full papers and clearly describe the PSO and ACO implementations as inspired hybrids. Add weight and budget sensitivity tests without retuning on the frozen test worlds. Collect real electrical measurements and physical robot or unassisted dynamics evidence if the paper makes those claims. Retain the simpler greedy baseline and all ties or failures.')
p(f"The integrity audit passed for {audit['attempts']} scheduled attempts. It checks trial identity, world separation, frozen settings, archived sources, physical model hashes and recomputed metrics. The 24 tiny exact-reference cases also passed. Neither check estimates a journal acceptance percentage.")
p('Evidence folder: mujoco/outputs/research/strong_study_v3. The new report supplements the earlier Word manuscript; it does not make that historical manuscript current automatically. No journal submission has been made.','Caption')
D.save(BASE/'Hexapod_V3_Upgrade_Report.docx');(BASE/'report_text.md').write_text('\n\n'.join(text))
# Machine readable source inventory for exact provenance.
(BASE/'report_sources.json').write_text(json.dumps(dict(study=str(STUDY),manifest_sha256=summary['manifest_sha256'],primary_run=primary['run_id'],physics_run=physics['run_id'],audit_state=audit['state'],physical_executions=len(executed),destination_reaching_executions=len(completed),time_mae_s=float(np.mean(np.abs(errors))),simulation_battery_mae_pp=float(np.mean(np.abs(battery)))),indent=2))
print(BASE/'Hexapod_V3_Upgrade_Report.docx')
