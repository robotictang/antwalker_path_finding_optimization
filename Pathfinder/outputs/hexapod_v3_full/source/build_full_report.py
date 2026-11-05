"""Complete v3 research report using the original manuscript typography and audited data."""
import ast,json,math,hashlib
from pathlib import Path
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];FIG=BASE/'figures';log=[]
A=json.loads((BASE/'source/verified_analysis.json').read_text());S=ROOT/'mujoco/outputs/research/strong_study_v3'
P=json.loads((S/'v3_heldout_planning.json').read_text());PH=json.loads((S/'v3_heldout_physics.json').read_text());M=json.loads((S/'manifest.json').read_text())
# Reuse only formatting helpers from the original full manuscript, without its authoring calls.
original=ROOT/'outputs/hexapod_journal/source/build_documents.py';tree=ast.parse(original.read_text())
allowed={'setup','para','heading','hyperlink','table','algorithm','mr','fraction','sub','equation','reference'}
helpers=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or isinstance(n,ast.FunctionDef) and n.name in allowed],type_ignores=[])
exec(compile(helpers,str(original),'exec'),globals());BASE=Path(__file__).resolve().parents[1];FIG=BASE/'figures';log=[]
D=setup('Resource constrained planning for simulated hexapod navigation')
D.styles['Subtitle'].font.color.rgb=RGBColor(0,0,0);D.styles['Subtitle'].font.name='Arial';D.styles['Subtitle'].font.size=Pt(11)
D.core_properties.subject='Complete version 3 research report with methods results and student guidance'
def p(t,style=None):return para(D,t,style)
heading_ids={}
def h(t,level=1):
    par=heading(D,t,level)
    if level==1:
        key='sec_'+hashlib.sha256(t.encode()).hexdigest()[:12];identifier=str(100+len(heading_ids));heading_ids[t]=key
        start=OxmlElement('w:bookmarkStart');start.set(qn('w:id'),identifier);start.set(qn('w:name'),key)
        end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),identifier);par._p.insert(0,start);par._p.append(end)
    return par
def page(title):
    par=h(title)
    if title.startswith(('1 Research question','References','Appendix')):par.paragraph_format.page_break_before=True
def tab(caption,headers,rows,widths):return table(D,caption,headers,rows,widths)
def fig(name,caption,width=6.65):
    par=D.add_paragraph();par.alignment=WD_ALIGN_PARAGRAPH.CENTER;par.paragraph_format.keep_with_next=True
    shape=par.add_run().add_picture(str(FIG/(name+'.png')),width=Inches(width));shape._inline.docPr.set('descr',caption)
    p(caption,'Caption');log.append('[Figure '+name+']')
def eq(text,n):equation(D,[text],str(n));log.append(text)
def alg(title,lines):algorithm(D,title,lines)
def number(x,d=3):return f'{x:.{d}f}'
N={'b1_distance':'Distance A*','b3_energy':'Energy A*','b7_greedy':'Greedy shortcuts','pso':'PSO hybrid','aco':'ACO hybrid','proposed':'Proposed v3','proposed_fixed':'Fixed seed time','proposed_single':'One seed family','proposed_unpruned':'No resource pruning'}
# Page 1
p('Resource constrained planning for simulated hexapod navigation','Title')
p('Complete version 3 research report with methods results and practical guidance','Subtitle')
p('28 October 2026   Author names and affiliations to be completed','Caption')
h('Abstract')
p('A hexapod route planner must balance distance, travel time, battery limits and terrain difficulty. This report describes a MuJoCo research framework comparing distance A*, energy A*, greedy shortcuts, A* seeded particle swarm optimization, ant colony optimization and a bounded Pareto resource-label refiner. The upgraded initialization can resume an unfinished energy search and use a distance-search fallback within the same planning budget. A frozen campaign contains 96 development attempts, 432 held-out planning attempts across 24 independently generated worlds, 96 component-removal attempts, 24 old-case diagnostic attempts and 36 separately scheduled assisted-physics attempts. Parameter selection uses separate development worlds. Distance A* admits 63 of 72 held-out attempts; the other five methods admit 66 of 72. Among jointly admitted comparisons, the proposed method has 3 lower scores and 63 ties against PSO, and 9 lower scores and 57 ties against ACO, with no higher scores. All 36 physics attempts succeed on six preselected worlds; the proposed mean destination time is 28.880 s, versus 28.872 s for PSO and 28.880 s for ACO. The results support a reproducible simulation comparison and small conditional planning-score gains, without establishing broad superiority, hardware energy savings or unassisted locomotion stability.')
p('Keywords   Hexapod navigation; multiobjective planning; particle swarm optimization; ant colony optimization; Pareto labels; reproducible simulation','Caption')
h('How to read this report')
p('Sections 1 to 15 describe the research question, simulator, algorithms, protocol and measured results. Sections 16 to 18 explain limitations, publication readiness and how to improve the method responsibly. Appendices A to C provide website instructions, reproducibility commands and a simple glossary. The full report replaces the need to read the earlier four-page supplement alongside the original manuscript.')
p('The software update and frozen study are complete for the scope reported here. The research remains a simulation study: electrical battery calibration and physical robot validation are pending. A complete report is not a journal acceptance guarantee.')
h('Main findings in simple language',2)
p('The robot gets a route, checks whether it has enough resources to complete the task and return, and only then runs the simulation. The proposal often finds the same route as PSO and ACO. Several seed families helped some planning cases; adaptive search recovered routes in old timeout cases, but their battery limits still prevented admission. Equal success rates are legitimate results and do not demonstrate that one method is better.')
# A linked reading index uses page numbers verified against the body render.
index=json.loads((BASE/'source/section_pages.json').read_text())
par=h('Contents');par.paragraph_format.page_break_before=True
p('Select a section in Word or use the heading navigation pane. Page numbers below were checked against the rendered report.')
from docx.enum.text import WD_TAB_ALIGNMENT,WD_TAB_LEADER
for entry in index:
    par=D.add_paragraph();par.paragraph_format.space_after=Pt(3);par.paragraph_format.line_spacing=1.05
    par.paragraph_format.tab_stops.add_tab_stop(Inches(6.65),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
    link=OxmlElement('w:hyperlink');link.set(qn('w:anchor'),'sec_'+hashlib.sha256(entry['title'].encode()).hexdigest()[:12])
    run=OxmlElement('w:r');props=OxmlElement('w:rPr');size=OxmlElement('w:sz');size.set(qn('w:val'),'21');props.append(size);run.append(props)
    tx=OxmlElement('w:t');tx.text=entry['title'];run.append(tx);link.append(run);par._p.append(link)
    r=par.add_run('\t'+str(entry['page']+1));r.font.size=Pt(10.5)
# Page 2
page('1 Research question and contribution')
h('1 1 Why this problem matters',2)
p('A short route can be a poor mission plan. It may cross slow terrain, require large turns or leave too little battery to reach a service station after the destination. A useful hexapod planner must evaluate these consequences together. A fair experiment also needs to distinguish a prediction made before movement from measurements obtained while the simulated robot moves.')
p('The project studies planar body-route planning for a six-legged robot. A candidate route is a sequence of body waypoints. The controller follows this sequence using a fixed tripod gait. Foot placement, perception, gait learning and mission-level scheduling are separate problems; improvements in those areas cannot be credited to this route refiner without separate experiments.')
h('1 2 Questions tested in version 3',2)
p('The primary question is whether bounded Pareto resource-label refinement improves the declared route score relative to common A* seeded PSO and ACO implementations, using matched cases, seeds, limits and computational budgets. A second question asks whether the extra refinement is useful beyond distance A*, energy A* and inexpensive greedy shortcuts. A third asks which individual proposal features change the outcome.')
p('The physics experiment then checks whether an admitted route can be executed by the assisted controller and whether the forecast agrees with simulated movement. It does not test a real battery, unassisted balance or an unknown physical environment. These boundaries determine the claims that the results can support.')
h('1 3 Implemented contributions',2)
p('The framework supplies one continuous route evaluator, explicit destination-and-return resource checks and shared collision geometry. Adaptive initialization preserves the A* frontier rather than repeating completed expansions after a short seed-search timeout. PSO, ACO, greedy and the proposal receive the same adaptive recipe, avoiding an exclusive initialization advantage for the proposal.')
p('A single procedural specification creates physical obstacles and shallow terrain tiles, together with the planner terrain queries. Development and test worlds use disjoint seeds and hashes. The campaign freezes cases before tuning, provides each optimizer the same two-profile tuning opportunity and preserves every rejection and tie. An integrity audit recomputes important quantities from saved records.')
p('The proposed refiner combines established Pareto-label ideas [5] with heading-aware safe shortcut corridors, bounded labels and resource checks. This is an implementation-level research contribution whose novelty must be assessed against the literature. It is not a newly proven general optimization principle, and the experiment does not reproduce unrestricted global PSO, a complete published ACO planner or a learned hexapod navigation system.')
h('1 4 Changes from the earlier study',2)
p('The earlier study used 12 test task/obstacle layouts on one underlying terrain and three main methods. Version 3 uses 24 new generated test worlds, six main methods and explicit feature-removal tests. It also records prediction errors and provides an external calibration workflow. Its larger attempt count strengthens traceability and coverage, but attempts on different task distributions cannot be used to claim a before-and-after percentage performance improvement.')
# Page 3
page('2 Related work and adaptation boundaries')
h('2 1 Foundational optimization methods',2)
p('A* supplies the graph-search basis for collision-checked seed routes [2]. PSO uses particle position, velocity, personal-best and population-best information to search a numerical representation [3]. The implementation here converts numerical keys into selected corridor waypoints. ACO uses pheromone-guided discrete construction and reinforcement [4]; this implementation is an elitist Ant-System-style adaptation, not exact Ant Colony System. Multicriteria shortest-path labeling [5] motivates retaining alternative resource vectors rather than immediately choosing one prefix by a single score.')
h('2 2 Hexapod gait and terrain methods',2)
p('Smart Gait addresses swing trajectories, gait period and duty, and adaptive gait sequences on a hexapod platform [6]. Its published results belong to that controller and robot. The present study freezes the default gait and does not implement its whole-body control or inherit its numerical savings. A separate gait-calibration interface in the software must be evaluated separately from these planner trials.')
p('Chen et al. combine terrain geometry and semantic information for hexapod motion planning [7]. This motivates footprint-scale terrain descriptors here. Version 3 uses known simulator height queries and declared terrain grades; it does not implement semantic camera perception, probabilistic sensor-map fusion or the original foothold search. Its terrain exposure is a cost proxy rather than a calibrated failure probability.')
h('2 3 Energy and stability aware navigation',2)
p('Energy-aware delivery planning for legged robots considers task and battery decisions [8]. Only the publisher abstract and introduction were accessible in the retained review, so the complete method is not reproduced. The present system defines its own battery ledger, destination-and-return reserve and modeled terminal service. It does not implement payload splitting or the paper-specific replacement schedule.')
p('STATE-NAV combines learned bipedal traversability, uncertainty-aware velocity selection and navigation/control components [9]. The retained source is arXiv version 4. The current project neither trains TravFormer nor implements its bipedal MPC. A small tilt angle under body-posture assistance cannot be treated as equivalent evidence of autonomous stability.')
h('2 4 Benchmarking implications',2)
p('COCO emphasizes explicit instances, settings, budgets and termination rules in optimizer evaluation [10, 15]. This project follows those transparency principles but is not a COCO benchmark. Demšar discusses comparisons across independent datasets in a different application domain [11]; the relevant lesson here is to distinguish independent worlds from repeated seeds. The current analysis uses descriptive paired world bootstrap intervals rather than borrowing a classifier significance claim.')
p('The review is targeted, not exhaustive. Before submission, the author should obtain the full energy-delivery paper and compare recent resource-constrained route planners in detail. A larger bibliography alone would not establish novelty; the report must identify precisely which representation, search rule or validated capability differs from prior work.')
# Page 4
page('3 Research system and evidence flow')
fig('system','Figure 1. The console launches trials, one world specification feeds planning and physics, and the comparison interface reads saved records. The integrity audit checks the recorded evidence; it does not create additional robot measurements.')
h('3 1 Hexapod Research Lab',2)
p('Research Lab is the experiment control interface. The user chooses the scenario suite, methods, repetitions, planner budget, locomotion and whether to execute physics. The runner constructs the case, prepares common graph information, runs each method in a shuffled paired order and saves its result. One experiment process holds a file lock to prevent concurrent benchmark runs from sharing this execution path.')
h('3 2 Hexapod Method Comparison',2)
p('Method Comparison is a read-only analytical view of a selected run. It displays admission, conditional route quality, wall time, route geometry and physics diagnostics when available. Scenario, repetition and terrain-family controls filter the recorded trials. The complete held-out paired summary is explicitly labeled when its counts do not follow those filters. The dashboard does not train an optimizer or generate new experimental observations.')
h('3 3 One attempt and its identifiers',2)
p('An attempt is identified by study phase, run identifier, case identifier, method and zero-based repetition. Its trial seed is the case seed plus 100003 times the repetition index. The plan record stores points, predicted metrics, limits, feasibility, diagnostics and actual optimizer parameters. A physics record is added only when execution is enabled and the plan is admitted. The same case and seed are assigned to every compared method.')
p('JSON preserves the detailed evidence, including routes and traces. CSV gives a flat trial table. The frozen manifest, selected-parameter hash, source snapshots and generated-model hashes make the run inspectable. Duplicate trial keys are an error; equal metric values from different valid keys may be a legitimate deterministic result. Unavailable measurements remain null rather than being converted to zero.')
# Page 5
page('4 Procedural worlds and terrain representation')
fig('worlds','Figure 2. Four actual held-out worlds from the frozen manifest. Grey rectangles are physical obstacles; shaded areas are terrain patches; circles mark starts, squares destinations and triangles service stations. These are plan-view maps in metres, not photographs or measured real environments.',6.35)
tab('Table 1  World family construction',['Family','Random boxes','Terrain patches','Additional structure'],[['Open',5,1,'Sparse obstacles'],['Clutter',16,2,'More obstacles'],['Rough',7,4,'Grade 2 terrain patches'],['Corridor',4,3,'Two interrupted barriers']], [1.0,.95,1.05,3.85])
p('Each world occupies a 48 m × 48 m planning region. The 0.25 m grid has 193 × 193 positions. Each terrain patch has 12 shallow physical tiles. Grade 1 tile heights range from 0.025 to 0.045 m; grade 2 heights range from 0.040 to 0.085 m. Terrain pads have 0.020 m tops. The sampled ground-friction coefficient is 1.3 times 0.8, 1.0 or 1.2. These simple worlds do not model deformable mud or granular soil.','Caption')
# Page 6
page('5 Robot simulation and measurement scope')
h('5 1 Shared navigation geometry',2)
p('The robot model is held fixed across methods. Eight-neighbor graph motion forbids diagonal corner cutting. Obstacle clearance uses the navigator footprint radius of 1.82 m, a tracking margin of 0.12 m and its grid allowance. Final waypoint connections receive continuous segment-clearance checks. The corridor refiners may remove intermediate waypoints, but every new chord must pass the same collision query.')
p('The world specification drives both physical MuJoCo geometry and terrain-height, severity and speed queries. Scoped bindings are restored after each case. Terrain-height and collision tests check that the procedural planner interpretation agrees with generated physical geometry. This synchronizes a known model; it is not validation of an external sensor map.')
tab('Table 2  Fixed execution settings',['Quantity','Value','Meaning'],[['MuJoCo / NumPy / SciPy','3.9.0 / 2.2.6 / 1.15.3','Versions saved with runs'],['Physics timestep','0.004 s','Four substeps per controller update'],['Controller update','0.016 s','Route-following commands'],['Tripod gait period / duty','0.689655 s / 0.60','Same default gait for all methods'],['Swing lift / profile','0.13 m / quintic','No planner-specific gait tuning'],['Initial heading','π / 2 radians','Same heading used in prediction'],['Walking speed caps','0.75 / 0.65 / 0.38 m/s','Smooth / mild / higher-grade terrain'],['Waypoint arrival tolerance','0.28 m','Execution advances to next waypoint'],['Minimum battery guard','2 percentage points','Execution stops below guard'],['Terminal service','8 modeled seconds','Restores ledger after station arrival']], [1.6,1.65,3.6])
h('5 2 Assistance and the consequences',2)
p('Horizontal body velocity is imposed during physics substeps. Vertical position and roll/pitch response also receive direct assistance, and gravity compensation is enabled. These interventions help compare route following repeatably, but they contribute support and movement that are not included in actuator-work integration. MuJoCo is a dynamics engine [1, 12]; the scientific validity of a claim still depends on the controller and model used.')
p('Body tilt, foot contact, support margin and slip are diagnostics of this assisted system. They cannot establish torque-feasible autonomous walking or real-world fall risk. The present study holds those assistance choices constant to isolate route-planning differences. A future locomotion study must test stronger dynamics without assuming that the existing results transfer.')
# Page 7
page('6 Multiobjective optimization in simple terms')
p('Multiobjective optimization means considering several goals at once. For this robot, a route can be short but slow, fast but battery-hungry, or easy to walk but longer. No route needs to be best on every goal. A useful planner keeps alternatives long enough to judge which trade-off fits the mission limits.')
tab('Table 3  Illustrative teaching routes only',['Route','Distance m','Time s','Battery points','Exposure'],[['A',14,24,11,3],['B',16,22,12,1],['C',18,26,14,4]], [.75,1.2,1.2,1.55,2.15])
p('These invented teaching values are not experiment results. A is shorter and uses less modeled battery than B. B is faster and has less terrain exposure. Neither dominates the other. C is worse than A on all four quantities, so A dominates C. Dominance lets a Pareto search discard C while retaining the useful A-versus-B trade-off.')
fig('pareto_example','Figure 3. A two-dimensional view of the illustrative teaching routes. Distance and exposure are also considered in Table 3. This sketch explains dominance; it is not an estimated experimental Pareto front.',5.9)
h('6 1 Choosing one route',2)
p('The implementation reports one route using a common score after feasibility is checked. The score converts the four quantities to declared reference scales. For illustrative A, Q = 14/50 + 24/90 + 11/30 + 0.25 × 3/20 = 0.9508. For B, Q = 0.9769. The chosen weights prefer A if both meet the limits; a deadline of 23 s would reject A and leave B admissible.')
p('This distinction matters: keeping Pareto labels during search does not mean the final experiment evaluates a full Pareto front. The report measures a single preference-selected solution. It does not report hypervolume or prove global Pareto optimality. Changing the preference weights would define a different comparison and needs a separate, preplanned sensitivity study.')
# Page 8
page('7 Cost model and mission constraints')
h('7 1 Distance time and modeled battery',2)
p('For route P, D is the sum of segment lengths in metres and Θ is total absolute heading change in radians. Predicted time sums distance divided by the applicable terrain speed, turn time at the reference 1 rad/s rate, and the 0.6 s start/stop allowance. Long segments are split at terrain boundaries before evaluation. For a nonzero walking-only route, the nominal battery ledger is')
eq('E(P) = 0.70 D(P) + 0.015 T(P) + 0.08 Θ(P) + 0.10',1)
p('E is percentage points of usable battery capacity, not joules. The four coefficients are explicit simulation assumptions. Version 3 provides an external fitting workflow, but the reported campaign uses the nominal values. Mechanical actuator work is measured separately during execution.')
h('7 2 Terrain exposure',2)
p('Nine height samples over the footprint window provide mean height, height range and height variation. Slope comes from the gradient of mean height. Difficulty is 0.25 times the sum of slope/0.25 rad, height range/0.12 m, height standard deviation/0.04 m and the assumed softness lookup, clipped to [0, 2]. Softness levels are 0, 0.25, 0.60 and 1. Exposure H integrates this difficulty along the route with approximately 0.125 m or finer sampling. It measures accumulated modeled difficulty, not probability of falling.')
h('7 3 Common preference',2)
eq('Q(P) = D(P)/50 + T(P)/90 + E(P)/30 + 0.25 H(P)/20',2)
p('Smaller Q is preferred among admissible routes. The denominators are reference scales chosen for the experiment, not learned physical constants. A 1% improvement in Q is not a 1% improvement in electrical energy, walking stability or mission success. All six methods receive the same final evaluator even though their search objectives differ.')
h('7 4 Destination and safe return',2)
eq('T(P) ≤ deadline     and     H(P) ≤ exposure limit',3)
eq('Brequired = 1.25 [E(P) + Ereturn] + 6 ≤ Binitial',4)
p('The runner finds a common minimum-modeled-energy reference return route from the destination to available stations. The factor 1.25 adds a 25% round-trip allowance, and 6 adds six reserve points. These are conservative design rules, not statistically calibrated chance constraints. The return forecast uses a common heading and does not jointly optimize intermediate charging decisions.')
p('For example, an outbound prediction of 15 points and a return forecast of 20 points require 1.25 × 35 + 6 = 49.75 points. A 45-point battery would reject the route even if the path is collision-free. Planner budget is different: 2 s means the computer may spend up to about two wall-clock seconds searching; it does not schedule battery charging every two seconds.')
# Page 9
page('8 Adaptive common initialization')
fig('adaptive','Figure 4. The 2 s initialization and refinement budget. Later seed stages run only when needed. Fast initial success may allow time- and distance-oriented seed families before the original 0.6 s seed deadline. Every stage is charged to the method timer.')
p('The first energy A* search receives 30% of total time and a 30,000-expansion cap, which is 75% of the 40,000 nominal total. If it stops without a route because of time or expansion limits, its saved frontier can resume until 70% of total time with the same energy cap. A distance A* fallback can then use the remaining expansion allowance until 90% of total time. The final portion remains available for evaluation and refinement. Resuming an already exhausted expansion cap does not grant extra expansions.')
alg('Algorithm 1 Shared adaptive seed procedure',[
 'Start one total wall timer and the common expansion allowance.',
 'Search energy A* until the initial seed deadline or energy cap.',
 'Retain frontier costs parents and queue when the seed is unfinished.',
 'Resume that frontier to the extended deadline when permitted.',
 'If still unfinished try distance A* with remaining expansions.',
 'If initial work finishes early try other seed families in time.',
 'Remove duplicate seed routes and create safe forward corridors.',
 'Evaluate original routes and common greedy shortcuts.',
 'Use remaining time for the selected refiner; greedy stops here.',
 'Recheck complete-route metrics constraints and diagnostics.' ])
p('A portfolio means several distinct seed corridors, not a guarantee of three returned seeds. Each corridor is a forward waypoint sequence; refiners may choose safe subsequences. The portfolio cannot represent every topologically different route in the map. All unique corridors share the remaining time and candidate allowance.')
p('PSO, ACO, greedy and the full proposal use this adaptive initialization. The fixed-seed-time control deliberately retains the older 30% allocation. Distance A* and energy A* are standalone baselines with their declared search objective and total method budget. Shared graph and return-route preprocessing are recorded separately from all method timers.')
# Page 10
page('9 Baselines and particle swarm refinement')
h('9 1 Simple baselines',2)
p('Distance A* searches the shared grid for a short route. Energy A* uses the nominal energy edge cost including turning. Each returned route receives continuous evaluation and may still be resource-rejected. The greedy baseline uses the common seed portfolio, evaluates the original route and a repaired aggressive shortcut for each unique corridor, and returns its best feasibility-ranked result. It provides an important test of whether expensive search adds value beyond safe simplification.')
h('9 2 PSO representation and updates',2)
p('For a corridor with n waypoints, PSO uses n − 2 internal random keys in [0, 1]. A key at least 0.5 requests that waypoint. If a requested skip crosses an obstacle, decoding inserts safe forward corridor nodes. The initial population includes original-route and aggressive-shortcut key selections. Personal and global bests use the same feasibility-first rank as the proposal.')
eq('v ← clip(wv + c1 r1 ⊙ (pbest − x) + c2 r2 ⊙ (gbest − x))',5)
eq('x ← clip(x + v, 0, 1)',6)
p('The selected version 3 PSO uses 24 particles, inertia w = 0.55, cognitive coefficient c1 = 1.70 and social coefficient c2 = 1.30. Velocity is clipped to ±0.25. Independent random matrices r1 and r2 are generated from the paired trial seed. This is a corridor-refinement adaptation of PSO [3], not an unseeded global planner.')
alg('Algorithm 2 PSO hybrid',[
 'Obtain common safe corridors and the remaining total budget.',
 'Initialize bounded random-key positions and velocities.',
 'Include original-route and aggressive-shortcut particles.',
 'Decode and repair each particle to a safe waypoint subsequence.',
 'Evaluate feasibility violation and then the common route score.',
 'Update personal best and swarm best when the rank improves.',
 'Apply velocity and position updates with the recorded limits.',
 'Continue up to 40 iterations per corridor while caps permit.',
 'Return the best retained whole route and observed diagnostics.' ])
p('The common rank first prefers a feasible route. Among infeasible candidates it minimizes summed positive normalized limit violations, then Q. Routes cannot be labeled successful merely because their score is attractive. Fitness caches avoid recounting identical decoded candidates as new evaluations; repeated particle states can therefore produce no new progress point.')
# Page 11
page('10 Ant colony route refinement')
p('ACO constructs a route through forward-visible corridor waypoints. From current index i, an ant considers every later index j whose chord passes continuous clearance. Its heuristic favors safe forward progress relative to chord length and remaining straight-line distance. Transition probability is proportional to pheromone raised to α and this heuristic raised to β.')
eq('Pr(i → j) = τij^α ηij^β / Σk τik^α ηik^β',7)
p('The selected configuration uses 12 ants per generation, α = 1, β = 2 and evaporation ρ = 0.20. Possible forward edges start with unit pheromone. An ant continues until reaching the final waypoint or failing to construct a complete sequence. Complete paths are evaluated by the same repaired-corridor representation and whole-route constraints used for the other refiners.')
alg('Algorithm 3 ACO hybrid',[
 'Obtain common safe corridors and remaining computation budget.',
 'Initialize pheromones on forward candidate connections.',
 'For each ant start at the corridor first waypoint.',
 'List later waypoints with collision-checked visible chords.',
 'Sample the next waypoint from pheromone and progress weights.',
 'Continue construction to the destination when possible.',
 'Evaluate each complete route with the common feasibility rank.',
 'Evaporate pheromone and reinforce generation routes and incumbent.',
 'Clamp pheromone values to the recorded finite range.',
 'Continue up to 40 generations per corridor while caps permit.',
 'Return the best retained route and actual search diagnostics.' ])
h('10 1 Reinforcement and constraint handling',2)
p('The implementation multiplies pheromone by 1 − ρ after each generation. Generation routes and the retained best route then deposit 1 divided by [1 + Q + 100V + 100I], where V is normalized constraint violation and I is 1 for infeasible routes and 0 otherwise. Pheromones are clipped to [0.0001, 10]. This discourages infeasible construction without deleting those outcomes from the records.')
p('This procedure is an elitist Ant-System-style adaptation of established ACO ideas [4]. It does not implement the ACS q0 policy or its original local pheromone update. The baseline should therefore be named and described by its actual implementation rather than attributed as a faithful reproduction of a particular published robotics system.')
h('10 2 Why ACO and PSO may agree',2)
p('The two methods search the same finite waypoint alternatives, receive the same initial greedy routes and use the same final preference. When the initial shortcut is already the best available candidate, both can return exactly the same result. Different search mechanisms do not require different output routes. Observed best-score traces record improvements that actually occurred; a flat or absent trace is not filled with invented iterations.')
# Page 12
page('11 Proposed bounded Pareto resource labels')
h('11 1 State and dominance',2)
p('A label stores the previous waypoint, current waypoint, cumulative distance, predicted time, modeled battery, terrain exposure and a parent link. Previous and current waypoints together preserve the incoming heading needed for turn accounting. Two labels at the same heading state can be compared component by component. A label dominated by another is discarded; useful trade-offs are retained subject to a memory cap [5].')
p('Segment metrics are cached. The search removes the one-off start/stop allowance from each segment contribution and adds it once for the route, avoiding a stop penalty at every mathematical chord. Incoming turn time and turn-energy terms are then accumulated explicitly. Complete routes are always re-evaluated using the common continuous evaluator before they become the reported result.')
alg('Algorithm 4 Proposed walking mode refiner',[
 'Initialize safe original and greedy whole-route incumbents.',
 'Create the start label with one start and stop allowance.',
 'Prioritize labels using accumulated score plus a remaining bound.',
 'Pop an active label and retain its incoming heading.',
 'For each later waypoint check continuous chord visibility.',
 'Add cached segment metrics and the heading turn cost.',
 'Prune resource-bound violations when that feature is enabled.',
 'Prune score bounds that cannot improve a feasible incumbent.',
 'At the same heading state remove dominated cost labels.',
 'Keep at most eight labels per state in the selected profile.',
 'Record parent links for every retained label.',
 'At the destination reconstruct the complete waypoint route.',
 'Re-evaluate complete metrics and update the feasible-first best.',
 'Stop at wall time expansion or candidate evaluation limits.' ])
h('11 2 Bounds and bounded computation',2)
p('A remaining-distance bound uses the straight-line distance to the destination. The time bound uses the walking ceiling, the battery bound includes nominal walking and hotel costs, and remaining terrain exposure is bounded below by zero. Resource pruning compares these estimates with deadline, task battery after return reserve, and exposure allowances. The label cap and finite corridor representation make the method approximate even when such bounds are useful.')
p('At most 240 whole-route candidate evaluations are available across the method corridors, with nominal 40,000 expansions shared between seed work and labels. Visibility checks, segment-metric calculations and full-route evaluations are different operations; equal high-level caps do not imply equal primitive computational work. For n corridor nodes, up to n(n − 1)/2 forward chords may be considered, while uncapped resource labels can grow combinatorially. The label cap trades completeness for bounded storage.')
p('The current walking search can miss globally better routes outside its seed corridors or discard useful labels at its cap. The separate hybrid-locomotion mode uses a beam fallback and is outside the primary walking-only evidence. No full-map optimality, universal dominance or formal real-time guarantee is claimed.')
# Page 13
page('12 Experimental protocol and fairness')
h('12 1 Frozen cases and splits',2)
p('The manifest fixes 8 development worlds with seeds 830000 to 830007 and 24 held-out worlds with seeds 940000 to 940023. Families cycle through open, clutter, rough and corridor. Start and goal candidates are drawn inside [−17, 17] m on each axis with nominal separation between 12 and 26 m, snapped to free grid locations and retained when snapped separation is at least 10 m. Cases are not filtered according to optimizer wins or resource feasibility.')
p('Deadline is sampled from 45, 70, 110 or 160 s; initial battery from 45, 65, 85 or 100 points; exposure limit from 10, 20 or 40; and execution energy multiplier from 0.85, 1.00 or 1.20. These are independent random choices within the case generator, not a balanced factorial design. Six held-out worlds belong to each terrain family. The small family samples limit any attribution of outcomes to one terrain or resource factor.')
tab('Table 4  Frozen campaign phases',['Phase','Scheduled design','Attempts','Role'],[['Development','8 worlds × 2 profiles × 2 repeats × 3 optimizers',96,'Select settings'],['Held-out planning','24 worlds × 3 repeats × 6 methods',432,'Primary comparison'],['Feature removal','First 8 held-out worlds × 3 repeats × 4 variants',96,'Component effects'],['Old-case diagnosis','2 inspected old cases × 3 repeats × 4 methods',24,'Timeout diagnosis'],['Held-out physics','First 6 held-out worlds × 1 repeat × 6 methods',36,'Assisted execution'],['Total','All scheduled study attempts',684,'No rejected attempts dropped']], [1.05,3.4,.65,1.75])
h('12 2 Pairing and preselection',2)
p('For repetition j starting at zero, the trial seed equals the case seed plus 100003j. Within a case the method/repetition order is deterministically shuffled. Paired seeds reduce avoidable mismatch in stochastic input; they do not make PSO and ACO perform identical random operations. The proposed walking-label search is effectively deterministic apart from wall-time termination, so repeated outcomes may be identical.')
p('The ablation and physics subsets are the first eight and first six held-out case identifiers fixed before tuning. They were not chosen retrospectively for success. Physics is attempted only after planning admission. In this study all 36 scheduled physics plans are admitted and executed. The 24 tiny exhaustive-reference cases are separate synthetic software-validation fixtures and are not added to the 684 experimental attempts.')
p('A manifest hash and scientific source lock prevent a modified method from silently resuming the same campaign. New scientific code needs a new version; fresh confirmatory evidence also needs new world seeds. Old inspected cases remain labeled diagnostic. Tuning, test and diagnostic results must not be pooled into one inflated statistical sample.')
# Page 14
page('13 Parameter selection and analysis')
h('13 1 Equal development opportunity',2)
tab('Table 5  Two tested profiles per optimizer',['Method','Default','Alternative','Chosen'],[['PSO','16 particles; w 0.72; c1/c2 1.49/1.49','24 particles; w 0.55; c1/c2 1.70/1.30','Alternative'],['ACO','12 ants; β 2; evaporation 0.20','18 ants; β 3; evaporation 0.35','Default'],['Proposed','8 labels per state','12 labels per state','Default']], [1.0,2.25,2.55,1.05])
p('Selection first maximizes development admission, then minimizes mean common score among admitted routes; exact ties keep the default. All profiles admit 14 of 16 attempts per method. PSO default mean Q is 1.322402 and alternative mean Q is 1.321889, so the alternative is selected. ACO and the proposal have equal default/alternative means of 1.321376 and retain their defaults. Selected settings are frozen before test execution.')
p('Both swarm methods permit at most 40 iterations per corridor. ACO keeps α = 1 and deposit coefficient 1. The proposal retains an archive capped at 16 entries. The selected profile also records a beam width of 6 for the separate hybrid fallback, which is not an active walking-label parameter. Two profiles per method provide equal tuning opportunity, not an exhaustive search over each optimizer’s best settings.')
h('13 2 Denominators and paired differences',2)
p('Admission rate counts all scheduled planning attempts. Mission success counts all scheduled physics attempts, including any plans that would have been rejected before movement. Route-cost means condition on admission; physics-cost means condition on success. These selected populations can differ between methods, so unconditional means alone are insufficient for a fair quality claim.')
eq('ΔQ = Qbaseline − Qproposed',8)
p('A positive ΔQ favors the proposal. Score wins, ties and losses are counted only when both methods are admitted; differences no larger than 10⁻⁸ in absolute value count as ties. Only-proposed-admitted, only-baseline-admitted and both-rejected outcomes are retained separately. Admission advantage uses every scheduled pair and is reported in percentage points.')
h('13 3 Uncertainty and computation',2)
p('For each baseline, repeated score differences are averaged within each jointly admitted world. A descriptive percentile interval resamples those world means with replacement 5,000 times using analysis seed 4100. The admission interval similarly resamples world-mean paired admission differences over all 24 worlds. This respects clustering by world, but the conditional score analysis excludes jointly rejected worlds and cannot describe their quality.')
p('The intervals are descriptive, with no multiple-comparison correction or precomputed power justification. No p-value or acceptance probability is claimed. The recorded machine has an Intel Core i5-7600 at 3.50 GHz, four logical CPUs and Python 3.10.12. Mean common model/graph/return preparation is 0.776 s per held-out case, maximum 0.943 s; it is excluded from method planning time. Wall-time results are not isolated hardware microbenchmarks.')
# Page 15
page('14 Held out planning outcomes')
fig('admission','Figure 5. Admission and resource rejection for every scheduled primary planning attempt. Every method returns a route in this held-out study; there are no primary no-route outcomes. Admission is a predicted resource decision, not a measured mission-success rate.')
tab('Table 6  Primary planning results',['Method','Admitted / 72','Mean Q','Mean predicted s','Mean planner s'],[[N[x['method']],f"{x['admissible']} ({100*x['admissible']/72:.1f}%)",number(x['mean_quality_score'],6),number(x['mean_predicted_time_s']),number(x['mean_planning_seconds'])] for x in A['planning']], [1.35,1.0,1.15,1.65,1.7])
p('Distance A* admits 63 attempts and rejects 9. Energy A*, greedy, PSO, ACO and the proposal each admit 66 and reject 6. In every method, heldout_12 and heldout_14 fail the battery-plus-return rule in all three repetitions. Distance A* additionally fails the deadline on heldout_24 in all three repetitions. None of the primary routes fails the terrain-exposure limit. The larger proposal admission versus distance A* is therefore specific to the tested deadline case.')
p('The primary proposal admission rate is 91.7%, but the earlier version’s 25% cannot serve as a before/after baseline: its cases, map extent and resource conditions differ. This study supports comparisons between methods on the same version 3 cases. It does not prove that the software update caused a 66.7-point improvement across a common test population.')
p('Means in Table 6 include each method’s admitted routes. Distance A* has one fewer admitted world, so its mean Q should not be compared directly with the proposal’s mean without the paired table. On this machine the proposal’s mean planner time is lower than both tuned swarm implementations, but higher than standalone A*. Such timing depends on corridor length, cache behavior and wall-clock load.')
# Page 16
page('15 Paired route quality and uncertainty')
fig('paired','Figure 6. Complete paired outcomes against each baseline. Wins and ties refer to the declared common score among jointly admitted attempts. No baseline-only admission or baseline-lower-score outcome occurs in this saved primary run.')
tab('Table 7  Paired score advantage by independent world',['Baseline','Paired attempts','Worlds','Mean ΔQ','Descriptive 95 percent interval'],[[N[x['baseline']],x['paired_admitted_trials'],x['layouts_with_paired_admission'],number(x['mean_layout_score_advantage'],6),f"[{x['descriptive_layout_bootstrap_95_percent'][0]:.6f}, {x['descriptive_layout_bootstrap_95_percent'][1]:.6f}]"] for x in A['comparison']['comparisons']], [1.15,1.0,.65,1.15,2.9])
fig('intervals','Figure 7. Saved world-bootstrap intervals for conditional score advantage. The right panel uses an expanded numerical scale to show the small PSO/ACO differences. Positive values favor the proposal; interval magnitudes remain small.',6.55)
p('Against PSO there are 3 wins and 63 ties among 66 admitted pairs; against ACO there are 9 wins and 57 ties. Both have 6 jointly rejected pairs. The PSO interval reaches zero. The ACO lower endpoint is positive but approximately 0.000000730 score units, rounded in Table 7; this should not be described as a substantial practical improvement. Admission advantage over distance A* is 4.167 points with interval [0, 12.5]; the other four baseline admission differences are exactly zero in the tested worlds. These results do not establish a broad or hardware performance advantage.')
# Page 17
page('16 Worked example from a saved test world')
C=A['worked_case']['case'];R=A['worked_case']['records'];aco=R['aco']['plan'];prop=R['proposed']['plan']
p(f"The following example is heldout_22, the first repetition of the clutter family world with seed {C['seed']}. The start is {C['start']} m and the destination is {C['goal']} m. The deadline is {C['deadline_s']:.0f} s, initial battery {C['battery_percent']:.0f} points and exposure allowance {C['risk_budget']:.0f}. The common return forecast is {C['return_energy_percent']:.6f} battery points. These are saved experimental values, not the teaching example in Section 6.")
tab('Table 8  Actual predicted metrics for heldout 22 repetition 1',['Method','Distance m','Time s','Battery pp','Exposure','Q'],[[N[m],number(R[m]['plan']['metrics']['distance_m']),number(R[m]['plan']['metrics']['estimated_seconds']),number(R[m]['plan']['metrics']['energy_percent']),number(R[m]['plan']['metrics']['terrain_exposure']),number(R[m]['plan']['quality_score'],6)] for m in A['methods']], [1.25,1.0,1.0,1.0,1.0,1.6])
fig('case22','Figure 8. Actual planned routes for ACO and the proposal on the same held-out world. Routes may appear almost identical at full-map scale. No measured trail is shown: this world is outside the six-world physics subset.',6.2)
required=prop['required_battery_percent'];percent=100*(aco['quality_score']-prop['quality_score'])/aco['quality_score']
p(f"For the proposed route, the common evaluator gives Q = {prop['metrics']['distance_m']:.6f}/50 + {prop['metrics']['estimated_seconds']:.6f}/90 + {prop['metrics']['energy_percent']:.6f}/30 + 0.25 × {prop['metrics']['terrain_exposure']:.6f}/20 = {prop['quality_score']:.6f}. Required battery is 1.25 × ({prop['metrics']['energy_percent']:.6f} + {C['return_energy_percent']:.6f}) + 6 = {required:.6f} points. It passes the saved limits.")
p(f"The relative score improvement over ACO is 100 × (QACO − Qproposed)/QACO = {percent:.5f}%. This is a very small composite-score change, not a measured electrical-energy saving. The PSO route ties the proposal in this repetition. Repetition 3 has a larger PSO score difference, but choosing only that outcome would hide the full distribution; the complete paired counts must remain the main comparison.")
# Page 18
page('17 Feature removal and timeout diagnosis')
h('17 1 What an ablation tests',2)
p('An ablation disables one feature while retaining the other conditions. Version 3 compares the full proposal with fixed initial seed time, one seed family, and disabled resource-bound pruning. The first eight held-out worlds and three paired repetitions give 24 attempts per variant. This tests whether added complexity changes outcomes in the selected subset; it does not guarantee that all features will prove useful.')
tab('Table 9  Full proposal versus each feature control',['Control','Proposal wins','Ties','Losses','Mean world ΔQ'],[[N[x['baseline']],x['wins'],x['ties'],x['losses'],number(x['mean_layout_score_advantage'],6)] for x in A['ablation']['comparisons']], [2.0,1.0,.75,.75,2.35])
p('The full proposal has 12 lower scores and 12 ties against one seed family. Its mean world score advantage is 0.020317 with descriptive interval [0.004092, 0.041358]. Multiple initial corridors therefore help some cases in this subset. All variants are admitted in all 24 attempts, so the component evidence concerns route quality, not admission.')
p('The fixed-time and unpruned controls each tie the full proposal in all 24 comparisons. There is no demonstrated final-output gain from adaptive time allocation or resource pruning in these eight relatively tractable worlds. The fixed control also changes expansion allocation and removes adaptive fallback, so it tests the recovery policy as a whole, not time extension alone. The unpruned control retains heading labels, score bounds, dominance and final feasibility checks. Broader feature benefits need harder independent tests.')
h('17 2 The two older timeout cases',2)
tab('Table 10  Old-case development diagnostic only',['Method','Attempts','Routes returned','Admitted'],[[N.get(m,m),v['attempts'],v['returned'],v['admitted']] for m,v in A['diagnostics'].items()], [2.85,1.0,1.5,1.5])
p('The fixed allocation returns no routes in six attempts. The adaptive PSO, ACO and proposal each return six routes, all resource-rejected. Reusing the frontier and permitting fallback therefore resolves the previous lack of route metrics on these cases. It does not make their battery-return requirement feasible. Because these cases were already inspected, they are diagnostic evidence rather than fresh confirmation of a general benefit.')
h('17 3 Separate software correctness evidence',2)
p('Exhaustive subset enumeration on 24 tiny synthetic forward-visibility graphs agrees with the resource-label search on admission and admitted score, with zero mismatches. These fixtures check a restricted additive setting with at most nine corridor nodes in the tested construction. They do not certify optimality on the large MuJoCo worlds, and their outcomes must not be counted as robot trials. The campaign integrity audit passes 684 unique attempts with no reported errors or warnings.')
# Page 19
page('18 Assisted physics results')
tab('Table 11  Results on six preselected physics worlds',['Method','Success / 6','Destination s','Mission work J','Mean max tilt deg'],[[N[x['method']],f"{x['successes']}/6",number(x['mean_task_time_s']),number(x['mean_positive_work_j']),number(x['mean_max_tilt_deg'])] for x in A['physics']], [1.4,.9,1.35,1.55,1.65])
fig('physics','Figure 9. Actual assisted-execution means on the same six worlds. Destination time excludes the return leg; mechanical actuator work includes the destination and return. Each bar summarizes six successful missions. These quantities are not electrical battery energy.')
p('All six methods succeed in all six worlds. The success measure is saturated and cannot rank their reliability on this subset. Six successful worlds also provide limited evidence about rare failures, harder terrain or another controller. The physics subset was fixed in advance, but its first-six construction does not guarantee representative resource difficulty.')
p('The proposal averages 28.880 s to the destination and 7564.756 J of positive mission actuator work. PSO averages 28.872 s and 7563.809 J, so the proposal is 0.008 s slower and uses 0.946 J more on average. ACO matches the proposal in both means. These small differences do not support a physical-performance advantage over the swarm baselines.')
p('Relative to greedy shortcuts, the proposal is 0.507 s faster on average but uses 9.690 J more positive actuator work. Relative to energy A*, it is 2.520 s faster and uses 330.270 J less work. These are descriptive comparisons on the same six assisted worlds, without an independent hardware claim. The results illustrate why a lower composite planning score cannot be interpreted as uniformly lower execution cost.')
p('Success requires reaching the destination by its deadline and completing the station return without an execution guard, with minimum battery at least 2 points. Terminal service is modeled after arrival. One service event per completed mission largely follows the experiment design; identical charging counts are not independent evidence of a better charging policy.')
# Page 20
page('19 Forecast validation and data reliability')
fig('prediction','Figure 10. Destination-time forecasts versus simulated execution for all 36 destination-reaching physics trials. The dashed line is exact agreement. Overlapping points may hide identical outcomes from different methods. Every saved destination time is below its corresponding forecast in this subset.')
tab('Table 12  Prediction errors on all 36 executions',['Quantity','Mean absolute error','Signed mean error','Meaning'],[['Destination time','1.808 s','−1.808 s','Forecasts are conservative here'],['Modeled outbound battery','1.908 percentage points','+0.287 percentage points','Simulation ledger comparison']], [1.55,1.5,1.5,2.3])
p('Error is executed value minus forecast. A positive time error would indicate underprediction. Here all time errors are negative. The planned geometry, turn model, execution arrival tolerance and route follower need not produce identical time estimates. Conservative average time is useful for these cases but does not prove that the deadline model is conservative in unseen environments.')
p('The case execution multipliers perturb motion-based battery accounting independently of the nominal prediction. This allows an internal mismatch check, but the prediction and execution ledger still share a designed cost family. Agreement between them cannot validate electrical consumption. The reported battery error must therefore be called a simulation-ledger error, not hardware calibration accuracy.')
h('19 1 Why equal values and unavailable values occur',2)
p('Repeated seeds are paired observations on one world. A deterministic label search or a shared best shortcut can return the same coordinates repeatedly. Fresh simulation states and the same controller may then reproduce the same telemetry. Equal values are legitimate when their route and execution evidence agree. Duplicating a trial identifier or copying a fabricated result would be a different problem; the audit checks unique keys and complete phase counts.')
p('Planning-only attempts have no measured mission time or work. A rejected plan never executes, and a failed execution may not reach the destination. Those values remain unavailable because the relevant observation does not exist. They should not be filled with zero or deleted from success-rate denominators. Version 3 primary planning has complete route metrics, while its physics measurements exist only in the separate physics phase.')
h('19 2 What the audit establishes',2)
p('The audit checks source archives and model hashes, disjoint development/test worlds, frozen parameter selection, unique paired trial keys, recomputed admission, common scores, route lengths, success rules and recorded prediction residuals. These checks support internal consistency and provenance. They do not certify sensor accuracy, physical realism, statistical power or novelty.')
# Page 21
page('20 External electrical calibration workflow')
fig('calibration','Figure 11. Implemented calibration workflow awaiting actual external measurements. No hardware-fitted profile was used in the reported campaign. The diagram describes a supported procedure, not a completed electrical experiment.')
p('A sensor must measure electrical energy supplied by the battery, in watt-hours, and usable battery capacity must be stated in watt-hours. Convert the measured energy to percentage points as 100 × measured Wh / usable Wh. Use real sensor records rather than positive actuator work or the simulator battery ledger. Temperature, payload, contact conditions and battery state can affect whether the fitted model transfers.')
eq('y = aD + bT + cΘ + d     with     a b c d ≥ 0',9)
p('The fitter uses nonnegative least squares for four walking coefficients: distance, time, turning and a mission intercept. Inputs must vary enough to identify all four coefficients. If distance and time are nearly proportional in every observation, their separate effects may be poorly identified even when a numerical fit is possible. The software checks full column rank; the researcher must also inspect practical conditioning and residuals.')
tab('Table 13  Required measurement CSV fields',['Field','What to enter'],[['mission_id','Identifier for an actual measurement mission'],['map_id','Identifier for the physical test environment'],['split','calibration or validation'],['distance_m','Measured travelled distance in metres'],['seconds','Measured mission duration in seconds'],['turn_radians','Accumulated absolute heading change'],['electrical_energy_wh','Externally measured electrical energy']], [2.0,4.85])
p('The software requires at least 12 calibration rows, 6 validation rows and at least three distinct missions in each split. Calibration and validation mission identifiers and map identifiers must be disjoint. Those are software safeguards, not a publication sample-size justification. Metadata must state external hardware origin, usable battery capacity and sensor description; a label cannot prove that a sensor was actually used.')
p('The fitter saves coefficient values, input-file hashes and held-out mean absolute and root-mean-square errors. A fitted walking profile can then be applied to a new walking-only run. It does not automatically calibrate wheel mode, transformations, sensor bias, battery aging or assistance energy. No current evidence justifies labeling the nominal campaign hardware-calibrated.')
# Page 22
page('21 Limitations and publication readiness')
h('21 1 Limits of the algorithmic comparison',2)
p('All three advanced methods search subsequences of common seed corridors. The representation may constrain them so strongly that extra optimization yields mostly ties. The primary evidence does not compare unrestricted global planners, a complete exact constrained solver, NSGA-II or a verified reproduction of every cited paper. The simple greedy baseline is competitive and must remain visible. If extra complexity provides little practical gain, simplification may be a better contribution than adding more components.')
p('Only two parameter profiles per optimizer were tuned. This is a small and equal opportunity, not proof that PSO or ACO was configured optimally. Fixed scalar scales and terrain thresholds may favor particular route trade-offs. A separate sensitivity study must vary these assumptions with a declared protocol rather than changing them after viewing favorable test results.')
h('21 2 Limits of worlds measurements and inference',2)
p('Twenty-four generated test worlds broaden coverage beyond the first fixed scene, but all follow one restricted generator, the same robot and the same controller. Start/goal and resource choices are not a balanced factorial experiment. Physics uses six preselected worlds, and all succeed. There are no physical robot trials, electrical sensor observations, deformable terrain, perception errors, moving obstacles or payload changes in the reported primary evidence.')
p('The composite score is a modeled preference. Its small advantage does not establish a perceptible operational gain. Conditional score intervals omit rejected worlds, and repeated seeds do not increase the number of independent worlds. The uncorrected descriptive intervals should not be converted into broad statistical or causal claims. The simulation controller’s body assistance also limits interpretation of tilt and actuator work.')
tab('Table 14  Current evidence and remaining work',['Area','Current status','Work needed before stronger claims'],[['Traceable experiments','684 attempts audited','Archive and review reproducibility independently'],['Independent simulation cases','8 development and 24 test worlds','New generator distributions and harder tasks'],['PSO and ACO advantage','Mostly ties with small score gains','Larger practical effects on fresh worlds'],['Component evidence','Seed variety helps some cases','Test adaptive time and pruning under stress'],['Electrical battery accuracy','Nominal ledger only','External sensor calibration and validation'],['Autonomous stability','Assisted execution only','Unassisted dynamics or physical robot trials'],['Paper novelty','Implemented combination described','Precise full-paper comparison and defensible novelty']], [1.45,2.0,3.4])
p('The report is now complete for the measured software scope, but the research is not established as submission-ready solely by its length or formatting. A Q2 or Q3 label does not define one universal manuscript standard. Quartiles depend on database, year and subject category; acceptance probability cannot be estimated responsibly from these records.')
# Page 23
page('22 How to develop a stronger proposed method')
h('22 1 Choose a limitation that matters',2)
p('The next method should target a demonstrated weakness. In this campaign, simple seeded methods already solve most admitted cases and success saturates in physics. A useful research target could be recovering a different feasible corridor when the seed family misses one, reducing deadline or battery violations under real prediction uncertainty, or improving route execution under less body assistance. Each target needs a measurable outcome and a fair comparator.')
p('One plausible next direction is a broader route portfolio that changes corridor topology, followed by resource-label refinement using independently calibrated time or electrical-energy uncertainty. This is a proposed research direction, not an implemented or proven version 3 feature. It would need a precisely defined diversification rule, a cost for generating alternatives and a common total budget for all compared methods.')
h('22 2 Test each proposed benefit',2)
p('Keep the version 3 campaign as historical evidence. Create a new development split, tune all methods equally, freeze parameters and declare a smallest useful effect before evaluating fresh worlds. Use stronger simple baselines and original-paper implementations when access permits. Include a no-diversification control, an uncalibrated-cost control and a no-uncertainty-margin control if those components are introduced.')
p('A budget sensitivity study could compare 0.5, 1, 2 and 5 wall seconds on the same new worlds while reporting achieved quality, admission and actual runtime. A preference sensitivity study could vary distance, time, energy and exposure weights across predeclared profiles. These experiments are recommendations and have not been added to the current evidence. Exact constrained solutions on small instances can identify when approximation loses useful routes.')
p('For physical validity, first measure actual electrical energy and validate forecasts on disjoint maps and missions. Then evaluate tracking, contact failures and energy under unassisted dynamics or a physical robot where available. Freeze route and controller separately in gait experiments, and freeze gait/controller in planner experiments. Otherwise a combined improvement cannot be assigned to one feature.')
h('22 3 Define what would count as success',2)
p('A stronger method should show a practical gain with its cost: more admissible missions, a useful paired time or electrical-energy reduction, a better quality-versus-budget curve, or robust performance on new environments. Report losses, failures and intervals alongside wins. If the advanced method ties a simpler baseline, explain the reason and consider reducing complexity. More records improve precision only when they answer a well-defined question with independent variation.')
h('22 4 Conclusion',2)
p('Version 3 provides a more complete and auditable comparison framework, adaptive seed recovery and independent procedural test worlds. The proposal improves modeled score over simple A* and greedy in some cases, while PSO and ACO usually tie it. Its physics evidence does not show an advantage over the swarm baselines. The most defensible present contribution is a transparent constrained simulation benchmark with bounded corridor refinement and clear validation limits. Further novelty and physical validation should precede stronger claims.')
# Page 24
page('23 Preparing a journal submission')
h('23 1 Select a journal by scope',2)
p('Journal of Intelligent and Robotic Systems and Robotica are scope candidates to discuss with the supervisor, not confirmed Q2/Q3 targets or acceptance recommendations. Check the required database and category for the relevant ranking year through the institution. The Springer author instructions cover manuscript structure, references, declarations and research data [13]. Robotica publishes its own preparation instructions [14]. Recheck the selected journal’s current rules, fees and article type immediately before submission.')
h('23 2 Assemble the paper and evidence',2)
p('Prepare a research article with a concise abstract, explicit research question, focused related work, reproducible methods, results with complete denominators, discussion, limitations and conclusion. The technical sections of this report supply that material, while the tutorial appendices are better kept as supplementary guidance if a journal does not need them. Adjust structure, word count and citation style only after choosing the journal.')
p('Complete author names, affiliations, corresponding-author details and contribution statements. Authors should verify the source code, calculations, literature descriptions and AI-assisted drafting. Add actual funding and competing-interest declarations, a truthful data/code availability statement, and any journal-required disclosure of AI use. Do not state that a dataset is public or that ethical approval exists unless those facts have been verified.')
p('The supplementary package should include the manifest, frozen settings, all trial records, analysis scripts, model/source versions, figures and reproduction instructions. Preserve failures and ties. Remove private machine paths from a public package or provide a portable regeneration procedure; generated XML assets currently refer to local project resources. Do not redistribute third-party full-text papers unless their licenses permit it.')
h('23 3 Obtain review before submitting',2)
p('Ask the supervisor to assess novelty, baseline fairness, practical effect size and the gap between assisted simulation and the intended claim. Have another person reproduce at least the analysis and a small experiment. Resolve unexplained discrepancies before polishing the narrative. A complete report can still require more research, especially when the strongest baselines mostly tie the proposal.')
p('Submit through the selected journal’s official portal after all authors approve the final manuscript. Prepare a cover letter that states the concrete contribution and simulation scope. Choose suggested reviewers only under the journal’s rules. If reviews arrive, respond to each comment with a specific change or a supported explanation. No submission or external communication has been made by this report update.')
h('23 4 Declarations to complete',2)
p('Data and code availability: local frozen evidence is retained in the project; the author must choose and verify a public repository or justified access statement before submission. Funding, competing interests and author contributions: to be supplied by the authors. AI assistance: code, plotting and report drafting received AI assistance; the authors remain responsible for verification and journal-specific disclosure. No human or animal participant study is described here.')
# Page 25
page('References')
refs=json.loads((ROOT/'outputs/hexapod_journal/source/reference_list.json').read_text())
refs.extend([
 dict(number=12,text='Google DeepMind. MuJoCo Documentation. Overview and model documentation. Accessed 28 October 2026.',url='https://mujoco.readthedocs.io/en/stable/overview.html'),
 dict(number=13,text='Springer Nature. Journal of Intelligent and Robotic Systems. Submission guidelines. Accessed 28 October 2026.',url='https://link.springer.com/journal/10846/submission-guidelines'),
 dict(number=14,text='Cambridge University Press and Assessment. Robotica. Preparing your materials. Author instructions. Accessed 28 October 2026.',url='https://www.cambridge.org/core/journals/robotica/information/author-instructions/preparing-your-materials'),
 dict(number=15,text='COCO project. The Experimental Procedure. Official benchmarking documentation. Accessed 28 October 2026.',url='https://numbbo.github.io/coco-doc/experimental-setup/')])
for r in refs:reference(D,r['number'],r['text'],r['url'])
p('References identify the literature and author instructions used to explain the study. The CASE source was available only through its abstract/introduction in the retained review. STATE-NAV is pinned to arXiv version 4. Algorithm descriptions and numerical results in this report are tied to the actual project implementation, rather than copied paper performance figures.','Caption')
# Page 26
page('Appendix A Step by step website experiments')
h('A 1 Open and inspect the saved study',2)
p('Open http://127.0.0.1:8771/ on the computer running the project. Research Lab is where you run an experiment; the comparison page at http://127.0.0.1:8771/comparison/ is where you inspect saved evidence. To start with the primary study, use the Stronger research study links, choose the held-out planning run and click Use selected run in charts. Refresh an already-open comparison tab.')
p('In Method Comparison, select heldout_22, repetition 1 and ACO as the paired-score baseline. Read the exact values in Table 8 or the trial table before judging the route drawing. The score advantage is about 0.0763%; a full-map drawing may look almost identical. The PSO comparison ties in this repetition. Use all cases again to return to the complete distribution.')
h('A 2 Run three useful examples',2)
tab('Table A1  Valid settings for practical checks',['Setting','Example 1','Example 2','Example 3'],[['Scenario suite','New worlds 4 terrains','New worlds 4 terrains','New worlds 4 terrains'],['World seed','1050000','1050000','1060000'],['Methods','Six-method comparison','Six-method comparison','Four feature-removal variants'],['Repetitions','1','1','3'],['Planner budget','2.0 s','2.0 s','2.0 s'],['Locomotion','Walking only','Walking only','Walking only'],['Execution','Planning only','Plan and MuJoCo physics','Planning only'],['Station service','Modeled charging','Modeled charging','Modeled charging'],['Scheduled attempts','24','24','48']], [1.25,1.85,1.85,1.9])
p('Example 1 is a quick check of route finding, resource admission and scoring. Four terrain families give more variety than repeating one map. Six methods show whether complicated optimization adds value beyond simple A*. One repetition keeps the run short. The 2.0 s budget is valid for the input’s 0.1 to 30 s range and 0.1 s step. It is a search-time allowance, not the robot’s travel deadline or charging interval.')
p('Example 2 keeps the same world seed and settings to connect predictions to physics. Only admitted routes execute. The number of actual executions may be below 24, and mission success must use all 24 scheduled attempts as its denominator. Inspect both the time and mechanical-work charts. Do not infer electrical savings from mechanical work alone.')
p('Example 3 uses new worlds and three paired repeats to compare the full proposal with its fixed-time, single-family and unpruned controls. Four worlds × four variants × three repeats gives 48 attempts. Repeats change optimizer seeds; changing world seed creates different worlds. These exploratory examples are not automatically added to the frozen 684-attempt paper evidence.')
h('A 3 Wait and inspect',2)
p('Click Run comparison, wait for completion, then refresh the comparison page. Download JSON or CSV to inspect records. The frozen-study button resumes the existing campaign; it does not create new independent evidence.')
# Page 27
page('Appendix B Troubleshooting and reproduction')
tab('Table B1  Common questions and checks',['What you see','What it means and what to check'],[['Same success for every method','The six physics worlds are all successful. Inspect paired cost and time; success is tied.'],['Same route score or measured value','Check case method repetition and route. A shared best shortcut can give a valid tie.'],['Unavailable work or measured time','Planning only rejected plans or unreached destinations have no such observation.'],['No route or timeout','Search stopped without a route. It is not proof that no route exists.'],['Resource rejected','A route exists but its deadline battery-return or exposure rule fails.'],['Blank comparison or local HTTP error','Check that the local service is active then refresh. Use the supplied offline HTML to inspect the saved planning snapshot.'],['Planner budget invalid','Enter a value from 0.1 to 30 with 0.1 increments such as 2.0.'],['Old results after a new run','Select the intended run click Use selected run in charts then refresh the comparison tab.']], [1.85,5.0])
h('B 1 Reproduction commands',2)
p('Run the commands from the mujoco directory using the project Python environment. These commands create or resume local work; they do not submit a manuscript. The frozen study source lock prevents silently resuming changed scientific code. A complete saved run can be inspected without rerunning the campaign.')
for line in [
 'python3 -m research.strong_study',
 'python3 -m research.audit_strong_study',
 'python3 -m research.run --suite procedural4 --world-seed 1050000',
 '  --methods b1_distance b3_energy b7_greedy pso aco proposed',
 '  --repeats 1 --planning-seconds 2.0',
 'python3 -m research.calibration --template outputs/research/calibration_template',
 'python3 -m research.calibration --csv YOUR.csv --metadata YOUR.json',
 '  --out fitted_profile.json',
 'python3 -m research.run --suite procedural4 --methods pso aco proposed',
 '  --execute --energy-profile fitted_profile.json']:
 par=p(line);par.paragraph_format.space_after=Pt(1)
 for run in par.runs:run.font.name='Consolas';run.font.size=Pt(8.5)
p('Indented command lines above continue the preceding command and should be joined with spaces before execution. Add --execute to the procedural experiment for physics. Actual external sensor records are required before fitting an energy profile. No fitted profile is supplied as hardware truth.')
h('B 2 Exact evidence identifiers',2)
p('Primary planning run: '+A['primary_run']+'. Physics run: '+A['physics_run']+'. Evidence directory: mujoco/outputs/research/strong_study_v3. The all_684_trials.csv file retains every scheduled study attempt. The manifest and locked parameter files identify the cases and settings before test results.')
for label,value in [('Manifest SHA256',A['selection']['manifest_sha256']),('Selected parameters SHA256',A['selection']['sha256'])]:
 p(label,'Caption');par=p(value)
 for run in par.runs:run.font.name='Consolas';run.font.size=Pt(8)
p('The offline dashboard is a frozen planning snapshot and cannot launch experiments. It should be kept together with the complete evidence package. Website build and exact HTTP snapshot delivery were checked; browser visual and interaction verification were unavailable during preparation. Document pages were separately rendered and visually reviewed.','Caption')
# Page 28
page('Appendix C Simple explanation for a supervisor')
p('This project compares computer methods that choose a route for a simulated six-legged robot. Each method receives the same task and limits. The planner predicts distance, time, battery use and terrain difficulty. It rejects routes that cannot meet the deadline or keep enough battery for a station return. Admitted plans can then be followed in MuJoCo. The website displays the saved results and does not generate evidence by itself.')
p('The proposal reuses unfinished search work and refines safe route shortcuts using Pareto labels. It sometimes lowers the modeled route score, but usually ties PSO and ACO. On six assisted-physics worlds, all methods succeed; the proposal has no physical-performance advantage over the swarm baselines. The study is traceable, but battery coefficients still need real measurements and the controller still assists the robot body.')
tab('Table C1  Key terms in ordinary language',['Term','Simple meaning'],[['Hexapod','A robot with six legs'],['Simulation','A computer model of the robot and its environment'],['Algorithm','A sequence of rules for solving a problem'],['Baseline','An existing or simple method used for comparison'],['Proposed method','The new implementation being evaluated'],['Multiobjective','Considering several goals such as time and battery together'],['Pareto dominance','One option is no worse on every goal and better on at least one'],['Planner budget','Computer wall time allowed for searching'],['Deadline','Time allowed to reach the task destination'],['Seed route','A starting path that another method refines'],['Random seed','A recorded number that recreates random choices'],['Admission','The forecasted route passes every declared resource rule'],['Mission success','The simulated task and return finish within the execution rules'],['Ablation','A test with one component disabled'],['Held out world','A test environment unused for parameter selection'],['Calibration','Fitting a model to separately measured quantities'],['Mechanical work','Actuator force times motion integrated over simulation time'],['Confidence interval','A range expressing uncertainty under stated sampling assumptions']], [1.5,5.35])
h('C 1 What is finished and what is next',2)
p('The implemented version 3 software, frozen campaign and complete report are finished for the stated simulation scope. The journal paper still requires author and supervisor review, defensible novelty, a selected journal format and appropriate validation for its claims. The next useful work is to measure real battery energy, test harder fresh worlds and assess the controller without relying on body assistance. A guaranteed publication percentage cannot be supplied.')
# Finish and structural checks.
text='\n\n'.join(log)
# Correct section navigation after the full report has been assembled.
for par in D.paragraphs:
 if par.text.startswith('Sections 1 to 15 describe'):
  par.text='Sections 1 to 20 describe the research question, simulator, algorithms, protocol and measured results. Sections 21 to 23 explain limitations, publication readiness and how to improve the method responsibly. Appendices A to C provide website instructions, reproducibility commands and a simple glossary. The full report brings the updated explanation and evidence into one document.'
for par in D.paragraphs:
 if 'same repaired-corridor representation and whole-route constraints' in par.text:par.text=par.text.replace('same repaired-corridor representation and whole-route constraints','same waypoint corridors and whole-route constraints')
# Normalize titles and headings including inherited theme font color.
for name in ['Title','Subtitle','Heading 1','Heading 2','Heading 3']:
 st=D.styles[name];st.font.color.rgb=RGBColor(0,0,0)
 for b in list(st.element.iter(qn('w:pBdr'))):b.getparent().remove(b)
# Keep the original 11 point body type while reducing avoidable layout spill.
D.sections[0].top_margin=Inches(.65);D.sections[0].bottom_margin=Inches(.65)
D.styles['Normal'].paragraph_format.space_after=Pt(5)
D.styles['Normal'].paragraph_format.line_spacing=1.08
for t in D.tables:
 for row in t.rows:
  for cell in row.cells:
   for par in cell.paragraphs:
    par.paragraph_format.space_before=Pt(1);par.paragraph_format.space_after=Pt(1)
    if len(cell.text)>30:par.alignment=WD_ALIGN_PARAGRAPH.LEFT
D.save(BASE/'Hexapod_V3_Upgrade_Report.docx')
# Extract actual final text after navigation and wording corrections.
alltext=[]
for block in D.element.body:
 if block.tag==qn('w:p'):alltext.append(''.join(block.itertext()))
(BASE/'report_text.md').write_text('\n\n'.join(p.text for p in D.paragraphs))
(BASE/'source/reference_list.json').write_text(json.dumps(refs,indent=2))
validation=dict(figures=len(list(D.element.iter(qn('wp:docPr')))),tables=len(D.tables),native_equations=len(list(D.element.iter(qn('m:oMath')))),references=len(refs),paragraphs=len(D.paragraphs),evidence_attempts=A['audit']['attempts'],primary_worlds=len(P['cases']),report_word_count=sum(len(p.text.split()) for p in D.paragraphs)+sum(len(c.text.split()) for t in D.tables for r in t.rows for c in r.cells),purpose='Full version 3 report integrating theory methods results interpretation and practical guidance',previous_short_report='Retained in archive; superseded by full report')
(BASE/'source/document_validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2));print(BASE/'Hexapod_V3_Upgrade_Report.docx')
