"""Build an evidence-limited manuscript and a separate supervisor/publication guide."""
import json,re
from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1]
A=json.loads((BASE/'source/verified_analysis.json').read_text())
S=(BASE/'evidence/reliability_v1') if (BASE/'evidence/reliability_v1').exists() else ROOT/'mujoco/outputs/research/reliability_v1'
P=json.loads((S/'heldout_planning.json').read_text());PH=json.loads((S/'heldout_physics.json').read_text())
FIG=BASE/'figures';log=[]

def setup(title):
 d=Document();sec=d.sections[0];sec.page_width=Inches(8.5);sec.page_height=Inches(11)
 sec.top_margin=Inches(.75);sec.bottom_margin=Inches(.75);sec.left_margin=sec.right_margin=Inches(.8)
 normal=d.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(11)
 normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.12
 for name,size in [('Title',19),('Heading 1',13),('Heading 2',11.5),('Heading 3',11)]:
  st=d.styles[name];st.font.name='Times New Roman';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
  st.font.bold=True;st.paragraph_format.space_before=Pt(11);st.paragraph_format.space_after=Pt(5)
  st.paragraph_format.keep_with_next=True
 for name in ['Caption','Table Text']:
  if name not in d.styles:
   from docx.enum.style import WD_STYLE_TYPE
   d.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
  d.styles[name].font.name='Times New Roman';d.styles[name].font.size=Pt(9.5)
  d.styles[name].paragraph_format.space_after=Pt(5);d.styles[name].paragraph_format.line_spacing=1.05
 d.styles['Caption'].font.color.rgb=RGBColor(0,0,0);d.styles['Caption'].font.bold=False
 for st in d.styles:
  for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
 for name in ['Title','Heading 1','Heading 2','Heading 3']:
  fonts=d.styles[name].element.get_or_add_rPr().get_or_add_rFonts()
  for attr in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:
   fonts.attrib.pop(qn('w:'+attr),None)
  fonts.set(qn('w:ascii'),'Arial');fonts.set(qn('w:hAnsi'),'Arial')
 d.core_properties.title=title;d.core_properties.author='Author details to be completed';d.core_properties.subject='Hexapod route planning simulation and publication assessment'
 # Page numbers aid supervision of a long manuscript.
 footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
 r=footer.add_run();r.font.size=Pt(9)
 fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');footer._p.append(fld)
 return d

def para(d,text,style=None):
 p=d.add_paragraph(text,style=style);p.paragraph_format.widow_control=True;log.append(text);return p

def heading(d,text,level=1):
 log.append('\n'+'#'*level+' '+text);return d.add_paragraph(text,style=f'Heading {level}')

def hyperlink(p,label,url):
 rel=p.part.relate_to(url,RT.HYPERLINK,is_external=True);h=OxmlElement('w:hyperlink');h.set(qn('r:id'),rel)
 r=OxmlElement('w:r');pr=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'174D70');pr.append(color)
 under=OxmlElement('w:u');under.set(qn('w:val'),'single');pr.append(under);r.append(pr);t=OxmlElement('w:t');t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=label;r.append(t);h.append(r);p._p.append(h)

def table(d,caption,headers,rows,widths):
 p=para(d,caption,'Caption');p.paragraph_format.keep_with_next=True
 t=d.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for col,w in zip(t.columns,widths):col.width=Inches(w)
 for i,h in enumerate(headers):t.rows[0].cells[i].text=str(h)
 for vals in rows:
  cells=t.add_row().cells
  for i,v in enumerate(vals):cells[i].text=str(v)
 for j,row in enumerate(t.rows):
  trpr=row._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
  if j==0:repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
  for i,c in enumerate(row.cells):
   c.width=Inches(widths[i]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
   for side in ['top','left','bottom','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');b.append(e)
   pr.append(b);m=OxmlElement('w:tcMar')
   for side in ['top','bottom','left','right']:
    e=OxmlElement('w:'+side);e.set(qn('w:w'),'75');e.set(qn('w:type'),'dxa');m.append(e)
   pr.append(m)
   sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E6EEF4' if j==0 else 'F6F8FA' if j%2==0 else 'FFFFFF');pr.append(sh)
   for p in c.paragraphs:
    p.style=d.styles['Table Text'];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
    p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.CENTER
    for r in p.runs:r.bold=j==0
 log.append(caption+'\n'+' | '.join(headers)+'\n'+'\n'.join(' | '.join(map(str,r)) for r in rows))
 para(d,'').paragraph_format.space_after=Pt(1)
 return t

def figure(d,file,caption,width=6.6):
 p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
 pic=p.add_run().add_picture(str(FIG/(file+'.png')),width=Inches(width));pic._inline.docPr.set('descr',caption)
 para(d,caption+' AI-assisted plotting code used the archived data or documented implementation.','Caption')
 log.append('[Figure: '+file+']')

def algorithm(d,title,lines):
 heading(d,title,2)
 for i,text in enumerate(lines,1):
  p=d.add_paragraph();p.paragraph_format.left_indent=Inches(.12);p.paragraph_format.space_after=Pt(1);p.paragraph_format.line_spacing=1.04
  p.paragraph_format.keep_with_next=i<len(lines)
  r=p.add_run(f'{i:02d}  {text}');r.font.name='Consolas';r.font.size=Pt(9)
  log.append(f'{i:02d} {text}')

def mr(text):
 e=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;e.append(t);return e

def fraction(a,b):
 e=OxmlElement('m:f');n=OxmlElement('m:num');n.append(mr(a));de=OxmlElement('m:den');de.append(mr(b));e.extend([n,de]);return e

def sub(base,index):
 e=OxmlElement('m:sSub');a=OxmlElement('m:e');a.append(mr(base));b=OxmlElement('m:sub');b.append(mr(index));e.extend([a,b]);return e

def equation(d,parts,number):
 p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 math=OxmlElement('m:oMath')
 for item in parts:math.append(mr(item) if isinstance(item,str) else item)
 p._p.append(math);p.add_run('     ('+str(number)+')');log.append('[Equation '+str(number)+']')

def reference(d,n,text,url):
 p=para(d,f'[{n}] {text}','Table Text');hyperlink(p,' '+url,url)

TITLE='Resource constrained route refinement for simulated hexapod navigation using swarm and bounded Pareto search'
d=setup(TITLE);para(d,TITLE,'Title')
para(d,'[Author names]');para(d,'[Department and institution]');para(d,'[Corresponding author email and ORCID identifiers]')
heading(d,'Abstract')
abstract=('Route planners for legged robots must balance travel cost, resource limits and computational effort. This study presents a reproducible MuJoCo framework for comparing A* seeded particle swarm optimization, ant colony optimization and a proposed bounded Pareto label refiner for assisted hexapod navigation. All methods use common collision checks, a fixed composite route score, a nominal two-second planning budget and explicit destination-and-return battery constraints. Parameters are selected using four development layouts and frozen before evaluation on 12 unused task and obstacle layouts with three paired seeds. The study records 48 development attempts, 108 held-out planning attempts and 12 physics attempts. Each method admits nine of 36 held-out planning attempts. Among nine jointly admitted comparisons, the proposed method achieves four lower scores and five ties against particle swarm optimization, and three lower scores and six ties against ant colony optimization. Mean score differences are small, and descriptive layout bootstrap intervals include zero. Only three physics attempts execute, one per method on the same accepted case; all complete with identical measurements. The results identify shared initialization timeouts and battery-return constraints as important bottlenecks. They support a transparent simulation benchmark, but do not establish general algorithmic superiority, electrical energy savings or unassisted robot stability.')
assert 150<=len(abstract.split())<=250;para(d,abstract)
para(d,'Keywords  Hexapod navigation; resource constrained planning; particle swarm optimization; ant colony optimization; Pareto labels; reproducible simulation')
heading(d,'1 Introduction')
para(d,'A navigation experiment can appear convincing when its charts show different numbers, yet meaningful comparison requires more than numerical separation. The methods must solve the same task, receive comparable resources and retain unsuccessful attempts in the reported denominators. For a battery-limited hexapod, a short outbound path may still be unsuitable if the robot cannot return to a service station. Equally, a smaller predicted route score does not necessarily imply less actuator work during execution.')
para(d,'MuJoCo provides a physics environment for evaluating model-based control and robot interaction [1]. In this study it supports a controlled simulation experiment, while explicit body assistance makes the scope narrower than autonomous dynamic locomotion. The research question is whether bounded resource-label refinement provides a useful improvement over two stochastic refiners when their representation, initialization recipe and final evaluator are held as consistent as practical.')
para(d,'A* offers a graph-search basis for generating collision-checked routes [2]. Particle swarm optimization (PSO) updates a population using personal and collective best solutions [3]. Ant colony optimization (ACO) constructs solutions through pheromone-guided choices; the implementation here follows an elitist Ant-System-style adaptation [4]. Multicriteria label methods retain alternatives with different cost vectors rather than immediately collapsing every prefix to one scalar value [5]. These are established ideas. Combining them in this implementation does not by itself demonstrate a new general optimization principle.')
para(d,'The work makes three practical contributions. First, it provides a common route representation and a continuous evaluator with explicit task, return-energy and terrain-exposure limits. Second, it compares an implementation of bounded Pareto resource labels with two A* seeded stochastic refiners under recorded budgets and parameters. Third, it links an experiment console to a source-backed comparison interface, preserving routes, seeds, failures and source snapshots. The evidence is presented as a preliminary simulation benchmark rather than a demonstrated replacement for state-of-the-art hexapod planning.')
heading(d,'2 Related work')
heading(d,'2.1 Gait and terrain reasoning',2)
para(d,'Smart Gait addresses swing trajectories, gait timing and adaptive leg-lifting decisions using robot dynamics [6]. Its contribution concerns locomotion control rather than waypoint-subsequence search. The present planner experiment freezes a default tripod gait and does not reproduce Smart Gait or inherit its reported savings. A separate gait-calibration dashboard exists in the software, but those calibration records are not pooled with the planner results in this manuscript.')
para(d,'Chen et al. combine geometric and semantic terrain features for hexapod motion planning [7]. This motivates footprint-scale height and terrain descriptors here. However, the present system uses a known terrain function and assumed semantic softness; it does not perform the paper’s perception pipeline or foothold planning. Its terrain score is therefore a declared geometric cost, not a measured probability of falling.')
heading(d,'2.2 Energy and stability aware navigation',2)
para(d,'Energy-aware delivery planning for legged robots considers battery-related task decisions [8]. The accessible material for that reference is limited to the publisher abstract and introduction; its complete method is not reproduced. This study instead states its own nominal battery ledger and destination-plus-return requirement. Modeled terminal service is distinct from an implemented physical battery-swap mechanism.')
para(d,'STATE-NAV learns stability-aware traversability for bipedal navigation and combines it with planning and control [9]. The cited version is arXiv v4. Its learned instability model and bipedal controller are not implemented here. In particular, small body tilt under imposed posture assistance cannot be treated as evidence equivalent to stability-aware autonomous locomotion.')
heading(d,'2.3 Benchmarking and the remaining question',2)
para(d,'The COCO framework emphasizes explicit problem instances, parameter settings and computational budgets in optimizer assessment [10]. This project is not a COCO benchmark, but uses these principles to separate development from evaluation and preserve unsuccessful results. Statistical comparison across datasets also distinguishes independent problems from repeated observations on the same problem [11]. Repeating three random seeds on one layout does not create three independent terrain worlds.')
para(d,'The remaining question is deliberately narrow: when safe corridors are initialized with the same recipe and scored by the same constrained preference, what differences remain between PSO, ACO and bounded resource-label refinement? The experiment cannot determine whether these corridor-restricted adaptations outperform unrestricted global planners, exact constrained solvers or recent learned hexapod controllers. Those comparisons require additional evidence.')
heading(d,'3 Research framework')
para(d,'The software separates experiment execution from result inspection. Hexapod Research Lab selects a suite, methods, repetitions, planning time and optional physics execution. Hexapod Method Comparison reads a saved result and displays outcomes, route scores, wall time, routes and measured telemetry. The comparison website does not train a model or produce new measurements. Figure 1 shows the information flow.')
figure(d,'figure_1_system','Figure 1  Experiment and visualization workflow. Resource-rejected and empty outcomes are saved alongside accepted plans. The websites are interfaces to the same recorded experiment, not separate sources of evidence.')
para(d,'Each record has a scenario identifier, method, repetition and seed. Its plan stores the returned route, predicted costs, feasibility decision, search diagnostics and parameter values. An execution record is added only when physics is enabled and the plan is admitted. JSON retains the detailed evidence; CSV provides a flat attempt table. Missing measured values in planning-only or rejected attempts are structurally unavailable and are not imputed as zero.')
heading(d,'3.1 Simulation and route representation',2)
para(d,'The recorded primary experiment uses MuJoCo 3.9.0 and NumPy 2.2.6. A 96 m by 96 m scene is discretized at 0.25 m, giving 385 by 385 grid nodes. Eight-neighbor motion forbids diagonal corner cutting. Collision queries use obstacle geometry and excluded terrain from the simulated scene. The navigator uses a 1.82 m radius, a 0.12 m tracking margin and an additional cell-size allowance. Final segments undergo continuous clearance checks, so removing waypoints cannot silently cross an obstacle.')
para(d,'A candidate is an ordered sequence of planar body waypoints from the start to the destination. This is body-route planning, not a foothold planner. Grid paths retain heading-dependent turn costs and are compressed by removing collinear vertices. Refinement can connect visible forward waypoints of an initialized corridor; it cannot invent an arbitrary new homotopy class outside the seed portfolio. This representation is shared by the three main methods.')
heading(d,'3.2 Assisted execution and measurement scope',2)
para(d,'The default tripod gait has period 0.689655 s, duty factor 0.60, swing lift 0.13 m and a quintic swing profile. The physics timestep is 0.004 s, with four substeps per 0.016 s controller update. All physics trials start with the same reference heading of pi/2 radians. A fresh simulation state is constructed for each method, and the destination route is followed by a common return route.')
para(d,'The controller directly assists horizontal body velocity, vertical position and roll/pitch response, and gravity compensation is enabled. These choices support repeatable route execution, but provide external assistance not accounted for as actuator work. Tilt, contact and work measurements describe this assisted simulator. They do not validate torque-feasible autonomous walking, real electrical consumption or hardware stability.')
heading(d,'4 Cost model and constraints')
heading(d,'4.1 Four route quantities',2)
para(d,'For route P, the evaluator records distance D in metres, predicted destination time T in seconds, nominal outbound battery use E in percentage points of capacity, and integrated terrain exposure H. Distance is the sum of segment lengths. Terrain boundaries are used to split long segments before time and energy evaluation. Turn time assumes a reference angular rate of 1 rad/s, and a start/stop allowance is included. The nominal walking-speed ceiling is 0.75 m/s; terrain policies can reduce it.')
equation(d,['E(P) = 0.70 D(P) + 0.015 T(P) + 0.08 Θ(P) + 0.10'],1)
para(d,'Equation (1) is the walking-only prediction for a nonzero route, where Θ is accumulated absolute heading change in radians. Its coefficients are simulation assumptions. Battery percentage is a bookkeeping model, not an estimate obtained from motor-current measurements. During execution, the declared case multiplier perturbs the motion-based battery ledger; this does not change the independently integrated mechanical-work measurement.')
para(d,'Terrain difficulty is computed from nine height samples over the footprint window. The components are slope from the gradient of mean sampled height, height range, height standard deviation and assumed semantic softness. Their normalized sum is multiplied by 0.25 and clipped to [0, 2]. The normalizers are 0.25 rad, 0.12 m and 0.04 m; softness is chosen from 0, 0.25, 0.60 and 1. Exposure H integrates this difficulty along the route using samples no farther apart than approximately 0.125 m. It is an exposure cost, not a calibrated safety probability.')
heading(d,'4.2 Common preference and resource feasibility',2)
equation(d,['Q(P) = ',fraction('D(P)','50'),' + ',fraction('T(P)','90'),' + ',fraction('E(P)','30'),' + ',fraction('H(P)','80')],2)
para(d,'All three methods use the same fixed composite preference Q in Equation (2). Smaller values are preferred among admitted routes. The denominators express chosen reference scales rather than learned importance weights. Although the implementation retains a bounded nondominated archive and uses multicriteria prefix labels, the reported solution is one preference-selected route. This is not an evaluation of an entire Pareto front, and no hypervolume or global Pareto-optimality claim is made.')
equation(d,['T(P) ≤ ',sub('T','max'),';  H(P) ≤ ',sub('H','max')],3)
equation(d,['1.25 [E(P) + ',sub('E','return'),'] + 6 ≤ ',sub('B','initial')],4)
para(d,'A route is admitted only if it passes both limits in Equation (3) and the battery requirement in Equation (4). The return estimate uses a common minimum-modeled-energy reference route from the destination to the available stations, including required station waypoints. The multiplier 1.25 adds a 25% allowance to the nominal round trip, and 6 adds six percentage points of reserve. This is a conservative simulation rule, not a statistically calibrated chance constraint.')
para(d,'The return calculation does not jointly optimize charging stops during the outbound task. An infeasible trip remains rejected even if a different mission-level schedule could make it possible. Return estimates use a common reference heading rather than the method-specific arrival heading. The reserve does not establish a formal bound on this approximation.')
heading(d,'4.3 Predicted and measured quantities',2)
para(d,'Positive mechanical actuator work is integrated at each physics substep by summing positive actuator force times actuator velocity over time. It is reported in joules for the simulated actuator model. It excludes electrical inefficiency, auxiliary power and unmodeled body assistance. A gait or route with lower modeled battery use need not have lower measured positive actuator work.')
para(d,'Destination time ends when the target waypoint is reached. Successful mission execution additionally requires return to a station, satisfaction of the destination deadline and minimum remaining battery of at least 2%. Terminal service adds eight modeled seconds and restores the ledger to 100%; it is not a charge-rate simulation. One charging event per completed mission is largely fixed by this design and is not an informative optimization outcome.')
heading(d,'5 Compared planning algorithms')
para(d,'Figure 2 summarizes the three refiners. Their common initialization attempts energy-, time- and distance-oriented A* searches within 30% of the nominal total planning time. Duplicate seed routes are removed. Each unique corridor initializes an incumbent using its original route and safe greedy shortcuts. All seed search and refinement time is charged to the method; shared graph and return-route preparation are outside that timer. The common recipe does not guarantee identical initialization work on every machine because it has wall-time cutoffs.')
figure(d,'figure_2_algorithms','Figure 2  Common initialization and distinct refinement mechanisms. Every returned route passes the same evaluator. The proposed method uses heading-aware resource labels in walking-only mode; its separate hybrid-mode beam fallback is outside the primary experiment.')
heading(d,'5.1 Particle swarm route refinement',2)
para(d,'PSO uses a vector of random keys in [0, 1] for internal corridor waypoints. Keys at least 0.5 request retention. Unsafe omissions are repaired by inserting safe forward nodes from the original corridor. Position and velocity updates use inertia, a personal-best term and a swarm-best term [3]. The initial population includes the original and aggressively shortened selections. Feasibility is ranked before normalized constraint violation and the common score; infeasible routes cannot be reported as successful merely because they are short.')
algorithm(d,'Algorithm 1 PSO hybrid',['Input common corridors, paired seed, limits and remaining wall time.','For each corridor, create random-key particles and bounded velocities.','Include original-route and aggressive-shortcut key vectors.','Decode each particle into a collision-checked waypoint subsequence.','Repair unsafe skips with forward corridor nodes.','Evaluate the route; update personal and global best ranks.','Update velocity from inertia, personal best and global best.','Clip velocity to ±0.25 and position keys to [0, 1].','Repeat up to 40 iterations per corridor, subject to time and caps.','Return the best feasibility-ranked candidate and observed diagnostics.'])
heading(d,'5.2 Ant colony route refinement',2)
para(d,'ACO constructs routes on a forward visibility graph of corridor waypoints. Transition probabilities are proportional to pheromone raised to alpha and a progress heuristic raised to beta. The heuristic divides forward index progress by the visible chord length plus remaining straight-line distance. Pheromones evaporate after each generation, and generation routes plus the retained incumbent deposit reinforcement. Constraint violation penalizes deposits. This is an implementation-specific elitist Ant-System-style adaptation [4], not an exact reproduction of the original Ant Colony System variant.')
algorithm(d,'Algorithm 2 ACO hybrid',['Input common corridors, paired seed, limits and remaining wall time.','Initialize pheromones on possible forward edges.','For each ant, begin at the start waypoint.','List forward nodes with collision-checked visible connections.','Sample the next node using pheromone and progress heuristic.','Continue until the destination or construction termination.','Evaluate complete routes with the common feasibility-first rank.','Evaporate pheromones and reinforce generation plus incumbent paths.','Clamp pheromones to [0.0001, 10].','Repeat up to 40 generations per corridor, subject to time and caps.','Return the best feasibility-ranked candidate and observed diagnostics.'])
heading(d,'5.3 Proposed bounded Pareto label refinement',2)
para(d,'The proposed walking-mode refiner searches the same forward visibility corridors using labels for partial routes. A label records the previous and current waypoint, accumulated distance, time, battery cost and exposure, and a parent link. The previous waypoint preserves incoming heading for turn accounting. Segment costs are cached, and a single global start/stop allowance is retained rather than added at every chord.')
para(d,'A prefix is pruned when resource lower bounds already exceed the available task budget. A label dominated in all four accumulated quantities at the same heading state is also discarded. Remaining labels are prioritized using a lower bound on the common score. At most eight labels are retained per state in the selected configuration; labels with larger scalar scores are discarded when the cap is reached. Complete candidates are re-evaluated by the common whole-route evaluator before updating the incumbent.')
para(d,'This combines established multicriteria labeling ideas [5] with bounded corridor refinement. The cap, finite seed portfolio, heuristic pruning and wall-time termination make it approximate. There is no proof that its restricted solution is globally optimal or that it dominates PSO or ACO. In particular, advantages on accepted routes must be considered alongside the rejected and empty outcomes.')
algorithm(d,'Algorithm 3 Proposed walking-mode refiner',['Input common corridors, limits, return energy and remaining wall time.','Initialize a label at the corridor start with one start/stop allowance.','Pop the active label with the smallest bound on common score.','For each forward waypoint, check continuous chord visibility.','Get cached segment costs and add incoming-heading turn costs.','Prune when resource lower bounds exceed the task limits.','Prune when the score bound cannot improve the feasible incumbent.','At the same heading state, remove dominated cost labels.','Keep at most eight labels per state; record parent links.','When the destination is reached, reconstruct and evaluate the route.','Update the feasibility-ranked incumbent and bounded archive.','Stop at time, expansion or candidate-evaluation limits.','Return the best candidate, limits and observed search diagnostics.'])
heading(d,'5.4 Parameter and computation controls',2)
table(d,'Table 1  Selected method parameters and development alternatives',['Method','Selected default','Alternative tested'],[
 ['PSO','16 particles; inertia 0.72; cognitive/social 1.49/1.49','24 particles; inertia 0.55; cognitive/social 1.70/1.30'],
 ['ACO','12 ants; alpha 1; beta 2; evaporation 0.20','18 ants; alpha 1; beta 3; evaporation 0.35'],
 ['Proposed','8 labels per state; archive cap 16','12 labels per state; archive cap 16']], [1.0,2.9,2.9])
para(d,'PSO and ACO allow at most 40 iterations per corridor. The experiment limits whole-route fitness evaluations to 240 across a method’s corridors and uses a nominal expansion limit of 40,000 shared between seed search and resource labels. The A* seed-search timer is set to 0.6 s of the two-second nominal budget. Seed evaluation and initial greedy shortcuts also count toward the total method time. These are recorded controls rather than hard real-time guarantees. Segment-cost evaluations, visibility checks and full-route evaluations are different computational primitives; the 240-candidate cap does not imply equal primitive work for all methods.')
heading(d,'6 Experimental protocol')
heading(d,'6.1 Development and held-out construction',2)
para(d,'The experiment manifest fixes four development cases with seeds 71000–71003 and 12 held-out cases with seeds 92000–92011. Every case samples start and destination offsets within ±1.5 m around the base task endpoints and snaps them to free grid locations. A reference distance route locates a real movable roadwork obstacle between 30% and 70% of route length, with an additional ±1 m planar offset. Cases are retained after obstacle placement even when the declared search fails. There is no filtering for proposed-method wins.')
para(d,'The six existing destination regions are cycled. Deadline values of 110, 160 and 210 s, initial batteries of 70, 85 and 100%, exposure budgets of 15, 25 and 40, and execution battery multipliers of 0.90, 1.00 and 1.12 are assigned by fixed index cycles. These settings are coupled by construction rather than varied factorially. The experiment cannot isolate the causal effect of battery, deadline, region or multiplier. All cases share the original underlying terrain, robot, station network and most geometry; different obstacle positions do not create independent terrain worlds.')
table(d,'Table 2  Primary study phases and their denominators',['Phase','Design','Attempts','What is observed'],[
 ['Development','4 cases × 2 profiles × 2 seeds × 3 methods','48','Planning and parameter selection'],
 ['Held-out planning','12 cases × 3 seeds × 3 methods','108','Route predictions and admission'],
 ['Held-out physics','4 preselected cases × 1 seed × 3 methods','12','3 executions; 9 rejected plans']], [1.25,2.45,.65,2.45])
para(d,'Both parameter profiles are evaluated for every method on the development cases. Selection first maximizes admission count, then minimizes the mean score of admitted routes; exact ties retain the default. All three methods retain their defaults. The selected settings and a parameter hash are written before held-out execution. This is parameter tuning, not neural-network training. Only one development layout produces accepted routes, so the search provides limited information for tuning.')
heading(d,'6.2 Paired seeds and execution rules',2)
para(d,'Each method receives the same case and trial seed within a repetition. The trial seed is the case seed plus 100003 times the zero-based repetition index. A deterministic shuffle counterbalances method/repetition order within each case. Three repetitions primarily assess stochastic sensitivity; the proposed walking-mode label search does not use a stochastic population, and its repeated outcomes need not differ. Machine scheduling can still affect wall-time-limited search.')
para(d,'Physics cases are fixed in the manifest as heldout_02, heldout_03, heldout_05 and heldout_06, before inspecting evaluation outcomes. They are not selected retrospectively for success. The runner executes admitted plans only. Mechanical work covers the destination and return motion, while reported task time covers travel to the destination. Older pilot, smoke and gait-calibration records are excluded from the primary 168-attempt study rather than pooled into its sample sizes.')
heading(d,'6.3 Analysis and uncertainty',2)
para(d,'Admission rate uses all planning attempts, including empty and rejected results. Mission success uses all physics attempts, including plans rejected before execution. Route-score averages condition on admission and are presented with their denominator. Paired score differences are computed only when both methods are admitted; the remaining outcomes are counted separately. A score tie has absolute difference no larger than 10 to the power of minus eight.')
para(d,'For each baseline, the difference is baseline score minus proposed score, so positive values favor the proposal. Repeated differences are first averaged within a layout. A descriptive percentile interval resamples these layout means with replacement 5,000 times using analysis seed 4100. Only three layouts contribute paired accepted scores. Such a small conditional bootstrap is not evidence of a general population effect, and no significance test or acceptance probability is reported. Statistical principles from comparisons across independent datasets [11] do not justify treating the nine paired trials here as nine independent terrain samples.')
para(d,'An independent analysis script recomputes the common score, resource decisions, summary denominators and paired comparisons directly from saved JSON. It verifies unique case-method-repetition keys and archived source hashes. Separate HTTP regression checks concern delivery of chart data, not scientific validity. Correct data delivery and an internally consistent record are necessary but do not establish a valid physical model.')
heading(d,'7 Results')
heading(d,'7.1 Acceptance and failure categories',2)
para(d,'All three methods admit nine of 36 held-out planning attempts, an admission rate of 25%. Each also returns 21 resource-rejected routes and six empty outcomes. Figure 3 shows the complete denominators. The identical admission rates are a measured tie. They should not be altered or hidden to create a visually stronger result.')
figure(d,'figure_3_outcomes','Figure 3  Held-out planning outcomes for all attempts. The three categories are disjoint. Admission refers to predicted resource feasibility, not measured mission success; every method contributes 36 attempts.')
para(d,'For each method, all 21 resource-rejected attempts exceed the battery-plus-return requirement; six of these also exceed the deadline. These overlapping limit counts must not be added as disjoint failures. No returned route is rejected solely for the terrain-exposure limit in this study. The six empty outcomes occur on two layouts and have timeout diagnostics during common seed initialization. They are not certificates that a collision-free or resource-feasible path does not exist.')
table(d,'Table 3  Held-out planning outcomes and conditional costs',['Method','Accepted / 36','Resource rejected','No route','Mean Q on 9 accepted','Mean planning s on 36'],[
 [s['method'].upper() if s['method']!='proposed' else 'Proposed',f"{s['admitted']} (25%)",s['counts']['resource_rejected'],s['counts']['no_route'],f"{s['mean_score']:.6f}",f"{s['mean_planning_s']:.3f}"] for s in A['planning_summary']], [1.05,.9,1.0,.8,1.55,1.5])
heading(d,'7.2 Paired route quality',2)
para(d,'Against PSO, the proposed method has four lower common scores, five ties and no higher score among nine jointly admitted paired trials. Against ACO, it has three lower scores, six ties and no higher score. For both comparisons, neither method is admitted in the other 27 paired attempts. These counts show a small conditional score advantage, not a gain in task coverage.')
table(d,'Table 4  Paired common-score outcomes across 36 matched attempts',['Baseline','Proposed lower','Tie','Proposed higher','Neither admitted'],[['PSO',4,5,0,27],['ACO',3,6,0,27]], [1.05,1.4,.65,1.4,2.3])
figure(d,'figure_4_paired_scores','Figure 4  Mean paired score differences on the three jointly accepted layouts. Both panels use the same horizontal scale, expressed in thousandths of a score unit. Layout 03 is an exact tie; improvements are small and concentrated in limited cases.')
para(d,'The mean layout-averaged score advantage is 0.00152021 against PSO and 0.00006509 against ACO. The descriptive 95% intervals are [0, 0.00384741] and [0, 0.00019528], respectively. Both include zero. Relative to the respective accepted-route mean scores, the differences are approximately 0.054% and 0.0023%. These percentages describe the chosen composite score only; they are not reductions in measured battery consumption, travel time or electrical energy.')
heading(d,'7.3 Planning time and initialization bottlenecks',2)
para(d,'Mean method wall times are 0.585 s for PSO, 0.737 s for ACO and 0.517 s for the proposed method. These observations favor the proposal on this machine and implementation, but exclude shared preparation. Recorded return-route and lower-bound preparation averages 1.638 s per held-out case, ranging from 1.048 to 2.758 s. Model loading and graph construction precede that preparation timer and are also excluded. The method means therefore cannot support an end-to-end real-time claim.')
figure(d,'figure_5_runtime','Figure 5  Recorded planning wall time. Each dot averages three repetitions within a layout; black bars mark the overall means. The two-second line is a nominal method allowance. Shared preprocessing and model construction are excluded.')
para(d,'On the two empty-result layouts, the initial search consumes approximately its 0.6 s allocation and reports timeout; no corridor is available for any refiner. The remaining nominal time does not create an alternative route because the current design stops without successful initialization. Reallocating unused refinement time to seed generation is a plausible shared improvement to test on development cases. It is a future experiment, not an improvement demonstrated by the current data.')
heading(d,'7.4 Route geometry and physics checks',2)
para(d,'Figure 6 shows the first two admitted layouts. The physics phase contains four preselected cases per method. Three cases per method are rejected before execution. Only heldout_03 executes, once for each method, and all three missions complete. Thus success is 1/4 per method when all scheduled physics attempts are counted, while conditional execution completion is 1/1 per method. Reporting only the latter would conceal the limited task coverage.')
figure(d,'figure_6_routes','Figure 6  Recorded first-repetition destination routes for the first two admitted layouts. Gray regions are obstacle bounding boxes in plan view, not a complete rendered terrain map. The paths coincide on Layout 03 and nearly coincide on Layout 04; no artificial offsets are added.')
table(d,'Table 5  Measured quantities on the single executed held-out case',['Quantity','PSO','ACO','Proposed'],[
 ['Time to destination s','72.848','72.848','72.848'],
 ['Mission time including service s','132.864','132.864','132.864'],
 ['Positive actuator work including return J','16385.631','16385.631','16385.631'],
 ['Modeled mission battery use percentage points','65.093','65.093','65.093'],
 ['Maximum assisted tilt degrees','0.157','0.157','0.157'],
 ['Completed / scheduled attempts','1 / 4','1 / 4','1 / 4']], [2.95,1.28,1.28,1.29])
para(d,'The three executed plans select identical waypoint sequences. Fresh deterministic physics executions therefore produce the same measured quantities, including destination time of 72.848 s and total positive actuator work of 16385.631 J. This is consistent with a shared route and controller, and gives no physical-performance advantage to the proposal. Recorded executions have no obstacle penetration, terrain-speed violation or solver-warning events; three assisted executions are insufficient to establish general safety.')
heading(d,'8 Discussion')
heading(d,'8.1 What the comparison establishes',2)
para(d,'The results establish that the software can preserve matched attempts, distinguish structural missing values from zeros, and expose ties rather than manufacture separation. They also show that a bounded label refiner can obtain slightly smaller common scores on some admitted corridors. The strongest negative result is that changing the refiner does not improve admission in the tested setting: the common seed stage and destination-plus-return resource model dominate much of the outcome.')
para(d,'The proposed method is better described as a resource-aware implementation under a restricted representation than as a universally superior optimizer. PSO and ACO explore subsequences of seeded corridors, not arbitrary collision-free paths. Requiring a safe initializer benefits all methods but can reduce population diversity and hide differences that would appear in broader search spaces. A fair extension must give every method the same available movement and service actions.')
heading(d,'8.2 Threats to validity',2)
para(d,'Internal validity is limited by heuristic coefficient choices, capped labels and the allocation of only 30% of time to seed generation. A common final evaluator reduces scoring inconsistencies, but does not validate its physical assumptions. Candidate counts also represent different work across algorithms because segment evaluations and population constructions differ. Source hashes support traceability, not correctness of every modeling assumption.')
para(d,'External validity is limited by one fixed terrain, sampled endpoint and obstacle changes, a small development set and only three layouts with paired accepted routes. Deadline, battery and goal region are coupled by index. In addition, the chosen physics subset yields one executed case. The study does not assess novel terrain families, localization error, perception noise, dynamic obstacles, payload changes, actuator degradation or unassisted hardware locomotion.')
para(d,'Construct validity is limited by the distance/time battery ledger, externally assisted motion and geometric exposure proxy. Positive actuator work omits external assistance and electrical losses. Small assisted tilt is not a fall-risk estimate. Terminal charge counts are mostly predetermined. These boundaries prevent interpreting a lower common score as a validated safety or electrical-efficiency gain.')
para(d,'The descriptive uncertainty interval is especially weak because it conditions on jointly admitted routes and resamples only three layout means. It does not quantify uncertainty in admission across independent terrain worlds. Further method development informed by these results also means these inspected cases should no longer be treated as pristine confirmation data for the revised algorithm.')
heading(d,'8.3 Evidence needed for a stronger study',2)
para(d,'A stronger evaluation should first state a specific methodological advance beyond known labeling and swarm ideas. Development experiments should address seed timeouts and calibrate battery/return assumptions. New experiments should include distance and energy A*, greedy shortcutting, denser weighted sampling, and an exact constrained reference on small graphs. Component-removal comparisons should isolate portfolio seeding, heading labels, resource pruning and label caps.')
para(d,'Next, independently generated terrain families should be split before tuning, with enough feasible and challenging cases to support both conditional cost and all-attempt outcome analysis. A larger predeclared sample should be justified by a meaningful effect and pilot variability rather than an arbitrary record count. Execution validation should use calibrated energy accounting and reduced assistance or hardware trials when making locomotion claims. None of these additions is represented as already completed in the present results.')
heading(d,'9 Conclusion')
para(d,'This study presents a traceable simulation framework for comparing PSO, ACO and bounded Pareto resource-label refinement on hexapod body routes. The primary evidence comprises 48 development attempts, 108 held-out planning attempts and 12 physics attempts. All methods admit 25% of held-out planning attempts. Conditional common-score improvements for the proposal are small, and the single executed case per method produces identical measurements. Shared initialization timeouts and return-energy requirements are more prominent limitations than the choice of refiner. The study supports transparent preliminary benchmarking, while broader novelty, independent terrain evaluation and stronger physical validation remain necessary for general performance claims.')
heading(d,'Statements and declarations')
para(d,'Funding  [Authors must provide the actual funding statement.]')
para(d,'Competing interests  [Authors must disclose actual competing interests or confirm their absence.]')
para(d,'Author contributions  [Complete actual contributions and author agreement using the selected journal’s requirements.]')
para(d,'Ethics  The reported experiments concern a simulated robot; no human-participant or live-animal experiment is reported.')
para(d,'Data and code availability  The study retains raw JSON, flat CSV, scenario manifests, selected parameters, source hashes and source snapshots. The accompanying local evidence package supports inspection and reanalysis. A public repository identifier and redistribution licenses for all model assets have not yet been established.')
para(d,'AI assistance  OpenAI Codex assisted software development, evidence analysis, manuscript preparation and code-generated figures on 28 October 2026. The named human authors must verify the methods, results, references and final text, confirm responsibility, and complete the target journal’s disclosure before submission. No AI system is listed as an author.')
heading(d,'References')
refs=[
 ('E. Todorov, T. Erez and Y. Tassa. MuJoCo: A physics engine for model-based control. Proceedings of the IEEE/RSJ International Conference on Intelligent Robots and Systems, 5026–5033 (2012).','https://doi.org/10.1109/IROS.2012.6386109'),
 ('P. E. Hart, N. J. Nilsson and B. Raphael. A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics 4(2), 100–107 (1968).','https://doi.org/10.1109/TSSC.1968.300136'),
 ('J. Kennedy and R. Eberhart. Particle swarm optimization. Proceedings of ICNN 1995, volume 4, 1942–1948 (1995).','https://doi.org/10.1109/ICNN.1995.488968'),
 ('M. Dorigo, V. Maniezzo and A. Colorni. Ant system: Optimization by a colony of cooperating agents. IEEE Transactions on Systems, Man, and Cybernetics, Part B 26(1), 29–41 (1996).','https://doi.org/10.1109/3477.484436'),
 ('E. Q. V. Martins. On a multicriteria shortest path problem. European Journal of Operational Research 16(2), 236–245 (1984).','https://doi.org/10.1016/0377-2217(84)90077-8'),
 ('Y. Yin, F. Gao, Q. Sun, Y. Zhao and Y. Xiao. Smart Gait: A gait optimization framework for hexapod robots. Chinese Journal of Mechanical Engineering 37, article 15 (2024).','https://doi.org/10.1186/s10033-024-01000-0'),
 ('C. Chen, J. Lin, B. You, J. Li and B. Gao. Hexapod robot motion planning investigation under the influence of multi-dimensional terrain features. Frontiers in Neurorobotics 19, article 1605938 (2025).','https://doi.org/10.3389/fnbot.2025.1605938'),
 ('S. Chen, Y. Chen, Z. Wei, Q. Nguyen and S. K. Gupta. Energy-Aware Planning for Delivery Tasks Executed by Legged Robots. Proceedings of IEEE CASE, 1617–1624 (2025). Publisher abstract and introduction consulted.','https://doi.org/10.1109/CASE58245.2025.11164088'),
 ('Z. Yoon, L. Y. Zhu, J. Lu, L. Gan and Y. Zhao. STATE-NAV: Stability-Aware Traversability Estimation for Bipedal Navigation on Rough Terrain. arXiv 2506.01046v4, 5 December 2025.','https://arxiv.org/abs/2506.01046v4'),
 ('N. Hansen, A. Auger, R. Ros, O. Mersmann, T. Tušar and D. Brockhoff. COCO: A platform for comparing continuous optimizers in a black-box setting. Optimization Methods and Software 36(1), 114–144 (2021).','https://doi.org/10.1080/10556788.2020.1808977'),
 ('J. Demšar. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research 7, 1–30 (2006).','https://www.jmlr.org/papers/v7/demsar06a.html')]
for i,(text,url) in enumerate(refs,1):reference(d,i,text,url)
heading(d,'Appendix A Reproduction and evidence scope')
para(d,'The primary evidence is in mujoco/outputs/research/reliability_v1. Development run identifiers are 20261028T013044676067Z and 20261028T013126915853Z; planning and physics identifiers are 20261028T013210063968Z and 20261028T013448551391Z. The manifest and parameter selection precede evaluation.')
para(d,'From the project’s mujoco directory, python3 -m research.reliability resumes saved phases. Completed phases are reused. A new execution can differ under machine-dependent wall-time cutoffs; archived source snapshots identify the original implementation.')
para(d,'Reanalyze with source/analyze_evidence.py --study evidence/reliability_v1 --out analysis. Python and NumPy are required; plots also need Matplotlib. The evidence package includes the original records, manifests and source snapshots. Simulation reruns additionally require the project meshes and dependencies, with redistribution permissions reviewed.')
table(d,'Table A1  Held-out cases and fixed resource profiles',['Case suffix','Seed','Start x y m','Goal x y m','Deadline s','Battery %'],[[c['id'][-2:],c['seed'],f"{c['start'][0]:g}, {c['start'][1]:g}",f"{c['goal'][0]:g}, {c['goal'][1]:g}",int(c['deadline_s']),int(c['battery_percent'])] for c in P['cases']], [.65,.8,1.4,1.65,1.1,1.2])
para(d,'The manifest retains exposure limits, execution multipliers, obstacle positions, return routes and all 108 planning records. These represent 12 layouts, three methods and three seeds, not 108 independent maps.')
main_path=BASE/'Hexapod_Journal_Manuscript.docx';d.save(main_path)
(BASE/'source/manuscript_text.md').write_text('\n\n'.join(log));log=[]

# A separate plain-language guide keeps publication advice out of the research paper.
g=setup('Hexapod study explanation and publication readiness')
para(g,'Hexapod study explanation and publication readiness','Title')
para(g,'Prepared for discussion with your supervisor 28 October 2026')
heading(g,'1 Is the study ready for a journal')
para(g,'There is enough material for a detailed preliminary manuscript and a useful supervisor meeting. The present evidence is not yet strong enough to support a broad claim that the proposed system outperforms existing methods in a Q2 or Q3 research submission. A polished paper cannot replace missing experiments. Acceptance cannot be predicted as a reliable percentage.')
para(g,'The main result is honest but limited. All three methods accepted 25% of the held-out planning attempts. The proposed method obtained a slightly smaller modeled route score in some accepted comparisons. Only one case actually executed per method in the physics check, and those measurements were identical. The manuscript reports these results without inventing an advantage.')
table(g,'What is already available',['Item','Current evidence'],[
 ['Working research software','Experiment console, comparison website, route logs and downloads'],
 ['Recorded primary study','48 tuning attempts + 108 planning tests + 12 physics attempts'],
 ['Separate tuning and test cases','4 development layouts and 12 unused evaluation layouts'],
 ['Measured physics','3 completed executions on the same case; 9 rejected plans'],
 ['Manuscript and figures','A full journal-style draft, six original figures and numbered references']], [2.0,4.8])
para(g,'The Word manuscript follows a conventional research-paper structure. It uses the Journal of Intelligent & Robotic Systems instructions as a formatting reference: a 150–250-word abstract, four to six keywords, decimal headings, numbered citations and declarations. This is a style choice, not a claim that the journal has endorsed the work or that its current quartile has been verified. [G1]')
heading(g,'2 Understand the system in simple words')
para(g,'The hexapod is a six-legged robot. The simulator is its virtual test environment. A planner chooses where its body should travel. The controller makes the simulated robot follow that route. The evaluator checks time, battery and terrain limits.')
para(g,'PSO is a group of candidate routes that learn from good previous candidates. ACO builds routes using reinforced connections. The proposed method keeps useful partial routes and removes ones that are worse in every recorded cost. All three begin with safe A* routes, so they can select the same final path.')
para(g,'Multiobjective means considering several goals together. Here the goals are short distance, short predicted time, low modeled battery use and low terrain exposure. The software combines them into one declared score after checking limits. It does not prove that one route is best for every possible preference.')
figure(g,'figure_1_system','System overview  The Research Lab runs the experiment; the comparison website shows the saved results.',width=6.4)
heading(g,'3 Use the two websites')
para(g,'Open the Research Lab to choose settings, launch an experiment and inspect saved records. Open the Method Comparison website to compare the saved methods. You do not need to run the robot again just to view an existing result.')
p=para(g,'Research Lab  ');hyperlink(p,'http://127.0.0.1:8771/','http://127.0.0.1:8771/')
p=para(g,'Method Comparison  ');hyperlink(p,'http://127.0.0.1:8771/comparison/','http://127.0.0.1:8771/comparison/')
para(g,'These are local addresses. They work on the computer running the project and are not public links for your supervisor. Share the Word documents and evidence files, or arrange an authorized deployment later. Open the website address rather than double-clicking a split-build HTML file.')
para(g,'To view the main study, find Reliability study in the Research Lab and choose held-out planning or held-out physics. Select that saved run, click Use selected run in charts, then open Method Comparison. Use the scenario and repetition filters for a matched comparison. The paired-outcome table is explicitly labeled as the full held-out set and does not change with those filters.')
table(g,'A short demonstration experiment',['Setting','Choose','Reason'],[
 ['Suite','Pilot with 3 scenarios','More informative than the one-task smoke check'],
 ['Methods','PSO versus ACO versus Proposed','Directly compare the three main methods'],
 ['Repetitions','3','Inspect sensitivity to paired random seeds'],
 ['Planner budget','2.0 seconds','Same nominal search allowance for every method'],
 ['Locomotion','Walking only','Keep the movement mode fixed'],
 ['Execution','Plan and run MuJoCo physics','Obtain measurements if the route passes its limits'],
 ['Service','Modeled charging stop','Keep the terminal service rule consistent']], [1.25,2.35,3.2])
para(g,'This demonstration schedules 27 attempts: 3 scenarios × 3 methods × 3 repetitions. It is not part of the manuscript’s frozen primary study unless a later version explicitly analyzes it. A two-second planner budget is time for route search, not robot travel time and not a charging interval. The current mission checks battery for the destination and return; it does not recharge every two seconds.')
heading(g,'4 Read the results correctly')
table(g,'Meaning of common outcomes and missing values',['Display','Simple meaning'],[
 ['found or admitted','A returned route passed the predicted limits'],
 ['resource_rejected','A route was found, but battery, deadline or exposure failed'],
 ['no_route','No route was returned under this search configuration; not proof of impossibility'],
 ['Unavailable predicted value','The algorithm returned no route from which to calculate it'],
 ['Unavailable measured value','Physics did not execute, or this was a planning-only run'],
 ['Equal measured numbers','The same path and deterministic controller can give the same result']], [2.0,4.8])
para(g,'For planning, use admission rate, route score and planning time. For executed missions, use measured destination time, mechanical work and mission completion. Keep their denominators visible. The common score is an estimate. Mechanical work is not electrical battery energy. Small assisted tilt does not prove real-robot balance.')
para(g,'The main study has 36 planning attempts per method. Each method admits nine, rejects 21 for resources and returns no route in six. The 21 resource rejections all exceed battery plus return reserve; six also exceed the deadline. The overlap explains why failure-reason counts do not add up as separate categories.')
para(g,'Among nine paired admitted trials, proposed versus PSO has four lower scores and five ties. Proposed versus ACO has three lower scores and six ties. These nine trials come from only three layouts. The small score advantages do not establish a general winner. On the executed physics case, all three take 72.848 seconds to reach the destination and perform 16385.631 J of positive actuator work for the mission including return.')
heading(g,'5 What is still missing')
table(g,'Priority gaps before a strong submission',['Priority','Gap','Required evidence'],[
 ['1','A clearly new research contribution','Explain what is new beyond combining known A*, PSO, ACO and label-search ideas'],
 ['2','Broader independent environments','Use new terrain families, not only one scene with a moved obstacle'],
 ['3','More informative feasible cases','Balance feasible and challenging tasks without selecting proposed-method wins'],
 ['4','Stronger matched baselines','Include simple A*, greedy shortcuts and an exact small-graph constrained reference'],
 ['5','Component-removal comparisons','Measure the value of portfolio seeds, resource pruning, heading labels and caps'],
 ['6','Physical and energy validity','Calibrate battery assumptions and external assistance; add hardware or stronger dynamics validation for physical claims'],
 ['7','Adequate uncertainty and robustness','Predeclare effects, seeds and disturbances; report layout-level intervals and all failures'],
 ['8','Complete submission package','Resolve authorship, funding, conflicts, licenses, data archive and AI disclosure']], [.6,2.1,4.1])
para(g,'Real-robot hardware is not a universal requirement for every simulation paper. It becomes essential, or needs a persuasive alternative, when the manuscript claims hardware energy savings, autonomous balance or practical physical deployment. A simulation-only paper must make a defensible contribution within its stated scope.')
heading(g,'6 Recommended next experiment')
para(g,'Step 1  Discuss the research claim with your supervisor. Choose one measurable contribution. One candidate is better use of planning time when common A* initialization fails. Another is a calibrated mission-level return or station-stop policy. These are research directions, not demonstrated improvements.')
para(g,'Step 2  Work on development cases only. Investigate the six timeout records and test whether unused refinement time can return to the seed search. Give the same initialization policy to PSO and ACO for a fair refiner comparison. Check whether the battery coefficients describe the intended robot before changing limits.')
para(g,'Step 3  Add matched baselines and component-removal tests. A simple method is a valuable baseline: the proposed system must justify its added complexity. When station actions or terrain information change, all compared methods should receive the same available actions and information.')
para(g,'Step 4  Create a new evaluation set before further tuning. As a planning example, 30 independent terrain maps × 5 paired seeds × 5 methods produces 750 attempts at one fixed planning budget. First estimate runtime with a small development pilot. Thirty maps is an example, not a guarantee of enough statistical power. Select the final sample using the practical effect of interest and variability. Keep a range of terrain difficulty, route lengths and feasible resource profiles.')
para(g,'Step 5  Freeze the final method. Test once on the new evaluation set. Keep rejected plans, timeouts and ties. Report both all-attempt coverage and conditional route costs. Use layout-level paired uncertainty and an appropriate predeclared test if the independent sample supports it. After inspecting a test set to improve the algorithm, treat that set as development evidence.')
para(g,'Step 6  Validate execution on several preselected scenarios per terrain family. Measure disturbances, collision behavior and model mismatch. Calibrate electrical battery claims with an appropriate measurement model or hardware. Evaluate assistance reductions only with clear controls and failure reporting.')
heading(g,'7 Suitable journals and how to choose')
para(g,'Q2 and Q3 are journal-ranking categories, not universal manuscript templates or acceptance percentages. Rankings depend on database, subject category and year. Current authoritative JCR or SCImago category records were not verified in this preparation, so the shortlist below is based on publisher scope rather than a certified Q2/Q3 label. Confirm the required database and year with your supervisor or university library before choosing a target.')
table(g,'Scope-based shortlist for supervisor discussion',['Journal','Why consider it','Current obstacle'],[
 ['Journal of Intelligent & Robotic Systems','Robot planning and intelligent robotic systems fit the topic','Needs stronger novelty and evaluation; use its official author instructions [G1]'],
 ['Robotica','Broad robotics, task planning and realistic applications [G2]','Needs a convincing robotics contribution beyond a small assisted benchmark'],
 ['Industrial Robot','Possible later application-focused option [G3]','Consider only after establishing a realistic industrial task and practical validation']], [1.7,2.45,2.65])
para(g,'For each candidate, check recent papers with similar methods, actual scope, article type, current quartile in the required category, open-access conditions, fees or institutional agreements, word limits and figure requirements. A ranking does not determine whether your manuscript fits the editor’s priorities. Do not pay an intermediary promising acceptance.')
para(g,'The manuscript uses a conventional introduction, related work, method, experiment, results, discussion, conclusion, declarations and references. Journal-specific format must be checked again after a target is selected. Word acceptance, abstract length and citation style were checked in the Journal of Intelligent & Robotic Systems guidance. [G1]')
heading(g,'8 Submission steps')
para(g,'First agree on authorship and the contribution with your supervisor. Complete the missing experiments and update every affected result, chart and claim. Then select one journal and follow its current author instructions. Do not submit the same manuscript to multiple journals at the same time.')
para(g,'Prepare the final manuscript, separate figure files, evidence archive, data-availability statement and cover letter. Confirm that all authors approve the submission and that funding, conflicts and model-asset licenses are accurate. The present placeholders must be completed with real details, not assumed values.')
para(g,'Disclose AI assistance and retain human responsibility. [G4] This work involved AI assistance in implementation, analysis, drafting and figure code, not only grammar editing. The human authors must understand and verify the methods and conclusions. Cambridge’s instructions also address disclosure of AI-assisted visual content. [G2]')
para(g,'Upload through the selected journal’s official portal. Answer editorial questions accurately. If reviewers request changes, respond point by point and identify exactly what changed. No submission, email to editors or public publication has been performed as part of preparing these files.')
heading(g,'9 A short explanation for your supervisor')
para(g,'“I built a simulation lab to compare three route-planning methods for a hexapod: PSO, ACO and a proposed bounded Pareto refiner. They share the same tasks, collision checks and declared planning budget. I separated parameter-tuning cases from test cases and saved every failure and tie. The proposal sometimes has a slightly better predicted score, but all methods have the same admission rate. Physics evidence is still limited, so I need stronger baselines, independent terrains and better validation before claiming a publishable performance improvement.”')
para(g,'If asked why the results are equal, say: “They often choose the same route from the shared initialization, so equal outcomes are expected.” If asked why there are missing values, say: “Some routes were not returned or were rejected, so no physics measurement exists.” If asked whether the method is ready for hardware, say: “The current simulator assists body movement, so that has not been demonstrated.”')
heading(g,'Sources for journal preparation')
for n,text,url in [
 ('G1','Journal of Intelligent & Robotic Systems submission guidelines. Checked 28 October 2026.','https://link.springer.com/journal/10846/submission-guidelines'),
 ('G2','Robotica author instructions and preparing your materials. Checked 28 October 2026.','https://www.cambridge.org/core/journals/robotica/information/author-instructions/preparing-your-materials'),
 ('G3','Industrial Robot publisher journal page. Publisher scope was available in its search record; detailed page access was blocked and current requirements must be checked.','https://www.emeraldgrouppublishing.com/journal/ir'),
 ('G4','Springer Nature policy on AI use in manuscript preparation. Checked 28 October 2026.','https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation')]:reference(g,n,text,url)
para(g,'The scientific references and source-access boundaries appear in the manuscript. The data analysis uses the frozen primary study, not an invented or regenerated dataset. Authorship, the final journal selection and human approval remain for the research team.')
guide_path=BASE/'Hexapod_Supervisor_and_Publication_Guide.docx';g.save(guide_path)
(BASE/'source/supervisor_guide_text.md').write_text('\n\n'.join(log))
(BASE/'source/reference_list.json').write_text(json.dumps([dict(number=i+1,text=t,url=u) for i,(t,u) in enumerate(refs)],indent=2))
print('Saved',main_path,guide_path);print('Abstract words',len(abstract.split()))
