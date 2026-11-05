from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'
ASSETS=OUT/'word_guide_assets'
ASSETS.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})

def flow(name, labels):
    fig, ax=plt.subplots(figsize=(9,1.5)); ax.set_xlim(0,len(labels));ax.set_ylim(0,1);ax.axis('off')
    for i,label in enumerate(labels):
        ax.add_patch(FancyBboxPatch((i+.03,.27),.83,.51,boxstyle='round,pad=0.02',facecolor='#eaf0f5',edgecolor='#63788c'))
        ax.text(i+.445,.525,label,ha='center',va='center',fontsize=10)
        if i<len(labels)-1: ax.annotate('',xy=(i+1.01,.525),xytext=(i+.9,.525),arrowprops={'arrowstyle':'->','color':'#34495e'})
    fig.savefig(ASSETS/name,dpi=220,bbox_inches='tight');plt.close(fig)

flow('simulation.png',['Robot and\nworld models','Route\nplanner','Movement\ncontroller','MuJoCo\nphysics','Observe and\nreplan'])
flow('proposal.png',['Set time and\nbattery limits','Search several\ntrade offs','Check safety\nand charger','Choose shortest\nfeasible route'])
rows=json.loads((ROOT/'mujoco/outputs/expanded_comparison.json').read_text())['rows'][:2]
fig,axes=plt.subplots(1,3,figsize=(10,3.1))
for ax,key,title,unit in zip(axes,['distance_m','estimated_seconds','energy_percent'],['Distance','Estimated time','Estimated battery used'],['metres','seconds','percentage points']):
    vals=[r[key] for r in rows]
    ax.barh(['R1','R2'],vals,color=['#376a93','#bd742b'],height=.48)
    ax.invert_yaxis();ax.set_xlabel(unit);ax.set_title(title,fontsize=11,pad=13)
    ax.set_xlim(0,max(vals)*1.33)
    for y,v in enumerate(vals):ax.text(v+max(vals)*.025,y,f'{v:.1f}',va='center',fontsize=11)
    ax.spines[['top','right']].set_visible(False);ax.tick_params(axis='y',length=0)
fig.tight_layout(w_pad=2);fig.savefig(ASSETS/'routes.png',dpi=220,bbox_inches='tight');plt.close(fig)

doc=Document();sec=doc.sections[0]
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
sec.top_margin=Inches(.7);sec.bottom_margin=Inches(.65);sec.left_margin=sec.right_margin=Inches(.75)
normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(11)
normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.05
for name,size in [('Title',27),('Subtitle',12),('Heading 1',17),('Heading 2',12)]:
    s=doc.styles[name];s.font.name='Calibri';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(8)
    if name.startswith('Heading'):s.paragraph_format.space_before=Pt(11)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run('Hexapod research guide  |  ');r.font.size=Pt(9)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
doc.core_properties.title='Understanding Your Hexapod Robot and Preparing for Publication'
doc.core_properties.subject='Student guide to simulation multi objective planning and research publication'

def p(t,style=None):return doc.add_paragraph(t,style)
def h(t):doc.add_heading(t,level=1)
def sub(t):doc.add_heading(t,level=2)
def bullet(t):p(t,'List Bullet')
def page(t):doc.add_page_break();h(t)
def pic(name,caption):
    para=doc.add_paragraph();para.paragraph_format.keep_with_next=True
    run=para.add_run();run.add_picture(str(ASSETS/name),width=Inches(7))
    for el in run._r.xpath('.//wp:docPr'):el.set('descr',caption)
    cap=p(caption);cap.paragraph_format.space_after=Pt(9)
    for r in cap.runs:r.font.size=Pt(9)
def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    for c,w in zip(t.columns,widths):c.width=Inches(w)
    for c,txt in zip(t.rows[0].cells,headers):c.text=txt
    pr=t.rows[0]._tr.get_or_add_trPr();pr.append(OxmlElement('w:tblHeader'))
    for row in rows:
        for c,txt in zip(t.add_row().cells,row):c.text=str(txt)
    for i,row in enumerate(t.rows):
        rp=row._tr.get_or_add_trPr();rp.append(OxmlElement('w:cantSplit'))
        for j,c in enumerate(row.cells):
            c.width=Inches(widths[j]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcp=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');b.append(el)
            tcp.append(b);m=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'90');el.set(qn('w:type'),'dxa');m.append(el)
            tcp.append(m)
            if i==0 or i%2==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DEE8F0' if i==0 else 'F5F7F9');tcp.append(sh)
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=1
                for r in para.runs:r.font.size=Pt(10);r.bold=i==0
    p('')

p('Understanding Your Hexapod Robot','Title')
p('A student guide to simulation algorithms and research publication','Subtitle')
p('Prepared 27 October 2026')
p('Your robot must choose a safe route, reach a destination and keep enough battery to reach a charger afterward. This guide explains the project in simple language and shows how to turn it into a stronger research study.')
p('Publication assessment: this could become a publishable project, but the inspected material is not yet a demonstrated new research contribution. A reliable acceptance percentage cannot be calculated from the files. The proposed method below has not been implemented or benchmarked.')
h('1  Understand the robot simulation')
p('A simulation is a computer world for testing a robot. Think of a video game where your program controls the robot and a physics engine calculates movement and contact with the ground. Your project uses MuJoCo [1].')
pic('simulation.png','Figure 1  The planner chooses a route and the controller makes the robot follow it. Observations feed the next decision.')
p('The current project includes a hybrid robot with wheels and six legs, a 96 by 96 metre scene, six destinations and three charging stations. The legs use a tripod gait: groups of three legs take turns moving.')
table(['Ground','Response','Configured speed cap'],[
('Smooth road','Use wheels','1.65 m/s'),('Mild rough ground','Walk','0.75 m/s'),('More uneven ground','Walk slowly','0.38 m/s'),('Extreme ground','Avoid the area','No entry')],[2.2,2.4,2.4])
p('These are simulation settings, not measured hardware abilities. Body movement and attitude are assisted, so successful navigation does not prove real robot balance or traction.')

page('2  Understand the algorithm and objectives')
p('An algorithm is a recipe for solving a problem. Your project uses A star, written A*, to search a map made of small squares about 25 cm wide. It considers the cost already spent and an estimate of the cost still needed. It also tracks heading because turning costs time and energy.')
p('Multi objective optimization means searching for good choices while considering several goals. Here the goals are shorter distance, less travel time and lower battery use. A longer smooth road can be faster and cheaper in energy than a short rough route.')
pic('routes.png','Figure 2  Estimates from an earlier saved Quarry comparison in outputs/expanded_comparison.json. This is not a measurement of the latest terrain scene. Lower is better in each chart.')
p('In that saved example, R2 was about 18 percent faster and used 13 percent less battery, despite being longer. It involved less walking and fewer wheel to leg transformations.')
sub('Weights and Pareto routes')
p('Weights tell the planner what matters most. Balanced mode adds distance divided by 50, time divided by 90 and battery use divided by 30, each multiplied by its priority weight. The divisions put different units on comparable scales. The weights add to one; a smaller total score wins.')
p('A route is dominated when another route is no worse in every objective and better in at least one. The Pareto front is the set of useful trade offs left after removing dominated routes. R1 and R2 are both useful: R1 wins on distance while R2 wins on time and energy.')
p('The existing planner tries up to seven distinct weight combinations and removes dominated routes. It samples the Pareto front; it does not find every possible trade off. Weighted sums can also miss some Pareto choices even with more weights [2].')
sub('Battery safety is a requirement')
p('The task budget includes predicted energy to the destination plus a feasible route to a charger afterward. The project multiplies this total by 1.25, then adds six battery percentage points of reserve. If the predicted total is 40 points, the required starting charge is 56 percent. If no safe task route fits, the controller checks whether charging first can help.')

page('3  Design a proposed method')
p('Start with a measurable weakness: the small set of weighted searches may miss routes that satisfy a particular deadline and battery budget. A new name or a visually impressive robot is not enough to establish a research contribution.')
sub('Proposed research question')
p('Can a planner find feasible routes for more deadline and battery combinations than the existing planner, using the same computation budget and safety rules?')
sub('A practical starting method')
p('Find the shortest safe route that meets a time limit and keeps enough energy for the destination and charger. For example, ask for arrival within 100 seconds while preserving the required battery reserve. This uses an established idea called the epsilon constraint method: optimize one goal while putting limits on the others.')
pic('proposal.png','Figure 3  Proposed planning process. This is a research design, not an implemented or proven improvement.')
for t in [
'Keep the existing terrain, collision rules, energy model and movement controller for the initial comparison.',
'Track distance, time and energy separately while searching. Keep several useful arrivals at the same position, heading and movement mode.',
'Remove a partial route only when another arrival has no worse costs and the same future movement options. A longer arrival might still be worth keeping if it saves energy.',
'Check deadline and battery feasibility, including the safe charger return. Choose the shortest complete route that satisfies the limits.',
'Repeat with selected limits to build a useful set of trade offs. Refine the limits where important feasible choices appear to be missing.'
]:bullet(t)
p('The difficult implementation change is keeping multiple cost records at a search state. Ordinary A* followed by rejection of its final route is not sufficient for this problem.')
sub('Where a contribution could come from')
p('The epsilon constraint idea itself is not new. A possible contribution is an efficient way to select limits and prune the search while preserving important feasible choices for hybrid robots and charger return. A literature review must establish whether that specific adaptation is new.')
p('Expect a trade off: keeping more routes can increase memory and planning time. An optimal A* result cannot be beaten on the identical objective and graph. Target better feasibility coverage, faster replanning or greater robustness, and test the exact claim.')

page('4  Main limitations and improvements')
table(['Current limitation','Why it matters','Useful improvement'],[
('Assisted body motion and attitude','Can hide balance and traction failures','Keep claims about navigation; add unassisted control and hardware tests for physical claims'),
('Assumed battery coefficients','Reported energy may not reflect real motors','Calibrate from electrical measurements or vary costs independently in the simulator'),
('Predictor and consumption share coefficients','Agreement is partly built into the model','Test model mismatch using different actual consumption parameters'),
('Known map and scripted obstacle detection','Does not demonstrate real perception','Add limited sensing, map errors, delayed detection and unexpected obstacles'),
('Small sampled route set','May miss useful feasible trade offs','Test constraint based search against denser weighted sampling'),
('Limited scenario diversity','Success on one scene may not generalize','Use unseen maps, different terrain layouts, start and goal pairs and battery levels'),
('No proposed method comparisons yet','Existing success is not evidence of improvement','Run fair baselines and component removal experiments'),
('Historical outputs span different versions','Old results can be mixed with current behavior','Freeze code, record hashes and rerun all methods on one version')
],[1.65,2.05,3.3])
sub('What the saved results establish')
p('The saved terrain_grades_final_validation.json records 144 objective route checks and a six destination mission taking about 729 simulated seconds with three charging stops and no recorded obstacle contacts. These are existing saved results, not new runs performed for this guide.')
p('They support the claim that the existing demonstration completed those tests. They do not establish superiority over other methods, general reliability across new environments, or hardware performance.')
sub('Improve the research in this order')
p('First make the comparison reproducible. Then implement one clearly defined planning change and test it on unseen scenarios. Add energy mismatch and sensing uncertainty next. Add real robot validation when making claims about physical deployment. A focused study with a clear result is easier to defend than many untested features.')

page('5  Run a fair experiment')
p('A baseline is an existing approach used for comparison. Use the same map information, route costs, safety checks, machine and planning time budget for every method.')
table(['Comparison','Question it answers'],[
('Shortest distance A*','Does considering time and energy help?'),
('Current sampled weighted sum planner','Does the proposal improve the current project?'),
('More weight samples with matched runtime','Is the gain simply caused by searching more?'),
('Fixed limit constraint planner','Does adaptive limit selection actually help?'),
('Exact multi objective search on small maps','How close is the result to the true feasible trade offs?')
],[3.0,4.0])
sub('A manageable pilot study')
p('Start with about 30 independently generated test maps, several start and destination pairs, and a range of battery levels and deadlines. This is a suggested pilot, not a publication minimum or a guarantee of sufficient sample size. Use a separate development set to tune parameters. Expand testing according to observed variation and the strength of the claim.')
bullet('Use paired scenarios: each method receives the same map, start, goal and battery. For randomized methods or disturbances, repeat with several seeds.')
bullet('Measure mission success, deadline success, battery failures, collisions, distance, actual simulated travel time, energy, planning time and peak memory.')
bullet('Show the quality and spread of feasible Pareto choices. More routes alone do not mean better routes; compare against an exact or pooled reference set with common scales.')
bullet('Report uncertainty, such as confidence intervals, and show failures and timeouts. Closely related runs on one map should not be treated as independent maps.')
bullet('Remove one proposed component at a time. For example, use fixed rather than adaptive limits. This reveals which change causes any improvement.')
sub('Figures your eventual paper should contain')
p('Include example routes on the same map, success rate across battery levels, travel time versus energy, planning time across map sizes, and component removal results. Label units and distinguish predictions from measurements. Do not create improvement charts before the experiments exist.')
sub('Keep the claim narrow and testable')
p('A defensible claim might be that the method finds more feasible deadline and battery solutions on unseen simulated maps within a fixed planning budget. Only state this after the data support it. If it takes longer or uses more memory, report that cost alongside the benefit.')

page('6  Publication prospects and submission plan')
sub('Is publication possible and is the chance high')
p('Publication is possible after the work becomes a well supported contribution. My assessment of the inspected project is that it is a useful prototype, but it is not yet ready as a strong research submission. The main gaps are demonstrated novelty, comparative experiments and evidence beyond the configured demonstration.')
p('I cannot responsibly assign an acceptance percentage. No completed manuscript, full novelty review or proposed method benchmark exists here. A venue acceptance rate, even if available, would not be the probability that your particular paper is accepted. A high chance is not established by the current evidence.')
sub('Choose a realistic publication route')
p('A student research event or a robotics workshop with a suitable demonstration or preliminary results track can be a sensible first target; check whether it publishes archival papers. A full robotics conference or journal requires a stronger completed study. Simulation only research can be publishable when the contribution and evidence support the claims; hardware becomes important when claiming real robot capability.')
p('For orientation, the Journal of Intelligent and Robotic Systems lists simulation, control and robot motion planning within its submission categories [3]. IEEE Robotics and Automation Letters seeks innovative robotics ideas and significant results [4]. These are examples to investigate after the results exist, not predictions of acceptance. Check current scope, recent similar papers, format, fees and submission rules before choosing.')
sub('How to publish step by step')
for t in [
'Read closely related papers on multi objective path planning, constrained shortest paths, hybrid locomotion and energy aware charging. Write down exactly what your method adds.',
'Ask a teacher or robotics researcher to review the contribution and experiment plan. Agree on authorship based on actual contributions.',
'Freeze the baseline, implement the proposal, run fair tests and preserve code versions, seeds, raw results and analysis scripts.',
'Write the paper: problem, related work, method, experimental setup, results, limitations and conclusion. Use measured results in the abstract.',
'Select one suitable venue and follow its template and submission instructions. Verify any claimed indexing in the relevant official index and check all charges.',
'Prepare the manuscript, cover letter, figures, required declarations and permitted supplementary code or video. Submit through the official publisher portal.',
'Respond to reviewer comments point by point, revise the paper and explain every change. If rejected, address the reasons before trying another suitable venue.'
]:bullet(t)
p('Submit to one refereed venue at a time and follow its prior publication policy. A preprint is public sharing, not peer reviewed acceptance. Check asset licenses before releasing the robot meshes or code. Follow the chosen venue policy on substantive AI assistance and verify all references and claims; IEEE requires disclosure of AI generated content, with a separate treatment for language editing [5].')

page('Sources and project files')
p('Publisher guidance checked on 27 October 2026. Recheck the selected venue immediately before submission. This guide explains the project and proposes research work; it is not a submission manuscript.')
sources=[
('[1] MuJoCo documentation','https://mujoco.readthedocs.io/en/stable/overview.html'),
('[2] The Power of the Weighted Sum Scalarization for Approximating Multiobjective Optimization Problems','https://link.springer.com/article/10.1007/s00224-021-10066-5'),
('[3] Journal of Intelligent and Robotic Systems submission guidelines','https://link.springer.com/journal/10846/submission-guidelines'),
('[4] IEEE Robotics and Automation Letters information for authors','https://www.ieee-ras.org/publications/ra-l/ra-l-information-for-authors/'),
('[5] IEEE submission and peer review policies','https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/')]
for title,url in sources:
    p(title);para=p(url)
    for r in para.runs:r.font.size=Pt(9)
sub('Files behind the project explanation')
for t in ['mujoco/README.md — current scene policy and historical development notes',
'mujoco/preview_multi_place_mission.py — simulation loop and assisted motion scope',
'mujoco/safe_navigation.py — grid search heading costs and clearance checks',
'mujoco/multiobjective_planner.py — weight sampling and Pareto filtering',
'mujoco/energy_model.py — normalized score and assumed consumption coefficients',
'mujoco/tripod_gait.py — walking pattern and foot positioning',
'mujoco/outputs/expanded_comparison.json — earlier R1 and R2 estimates used in Figure 2',
'mujoco/outputs/terrain_grades_final_validation.json — saved terrain mission results']:
    bullet(t)
p('Suggested research title: Battery Constrained Multi Objective Route Planning for a Hybrid Hexapod Robot. Revise the title once the implemented contribution and measured outcome are clear.')

dest=OUT/'Hexapod_Student_Guide_and_Publication_Plan.docx'
for element in list(doc.styles.element.iter()) + list(doc.element.iter()):
    if element.tag == qn('w:pBdr'):
        element.getparent().remove(element)
doc.save(dest)
print(dest)
