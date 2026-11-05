Resource constrained planning for simulated hexapod navigation

Complete version 3 research report with methods results and practical guidance

28 October 2026   Author names and affiliations to be completed

Abstract

A hexapod route planner must balance distance, travel time, battery limits and terrain difficulty. This report describes a MuJoCo research framework comparing distance A*, energy A*, greedy shortcuts, A* seeded particle swarm optimization, ant colony optimization and a bounded Pareto resource-label refiner. The upgraded initialization can resume an unfinished energy search and use a distance-search fallback within the same planning budget. A frozen campaign contains 96 development attempts, 432 held-out planning attempts across 24 independently generated worlds, 96 component-removal attempts, 24 old-case diagnostic attempts and 36 separately scheduled assisted-physics attempts. Parameter selection uses separate development worlds. Distance A* admits 63 of 72 held-out attempts; the other five methods admit 66 of 72. Among jointly admitted comparisons, the proposed method has 3 lower scores and 63 ties against PSO, and 9 lower scores and 57 ties against ACO, with no higher scores. All 36 physics attempts succeed on six preselected worlds; the proposed mean destination time is 28.880 s, versus 28.872 s for PSO and 28.880 s for ACO. The results support a reproducible simulation comparison and small conditional planning-score gains, without establishing broad superiority, hardware energy savings or unassisted locomotion stability.

Keywords   Hexapod navigation; multiobjective planning; particle swarm optimization; ant colony optimization; Pareto labels; reproducible simulation

How to read this report

Sections 1 to 20 describe the research question, simulator, algorithms, protocol and measured results. Sections 21 to 23 explain limitations, publication readiness and how to improve the method responsibly. Appendices A to C provide website instructions, reproducibility commands and a simple glossary. The full report brings the updated explanation and evidence into one document.

The software update and frozen study are complete for the scope reported here. The research remains a simulation study: electrical battery calibration and physical robot validation are pending. A complete report is not a journal acceptance guarantee.

Main findings in simple language

The robot gets a route, checks whether it has enough resources to complete the task and return, and only then runs the simulation. The proposal often finds the same route as PSO and ACO. Several seed families helped some planning cases; adaptive search recovered routes in old timeout cases, but their battery limits still prevented admission. Equal success rates are legitimate results and do not demonstrate that one method is better.

Contents

Select a section in Word or use the heading navigation pane. Page numbers below were checked against the rendered report.

1 Research question and contribution	3

2 Related work and adaptation boundaries	4

3 Research system and evidence flow	5

4 Procedural worlds and terrain representation	6

5 Robot simulation and measurement scope	7

6 Multiobjective optimization in simple terms	7

7 Cost model and mission constraints	8

8 Adaptive common initialization	9

9 Baselines and particle swarm refinement	10

10 Ant colony route refinement	11

11 Proposed bounded Pareto resource labels	12

12 Experimental protocol and fairness	12

13 Parameter selection and analysis	13

14 Held out planning outcomes	15

15 Paired route quality and uncertainty	16

16 Worked example from a saved test world	17

17 Feature removal and timeout diagnosis	18

18 Assisted physics results	19

19 Forecast validation and data reliability	20

20 External electrical calibration workflow	21

21 Limitations and publication readiness	22

22 How to develop a stronger proposed method	23

23 Preparing a journal submission	23

References	25

Appendix A Step by step website experiments	26

Appendix B Troubleshooting and reproduction	27

Appendix C Simple explanation for a supervisor	28

1 Research question and contribution

1 1 Why this problem matters

A short route can be a poor mission plan. It may cross slow terrain, require large turns or leave too little battery to reach a service station after the destination. A useful hexapod planner must evaluate these consequences together. A fair experiment also needs to distinguish a prediction made before movement from measurements obtained while the simulated robot moves.

The project studies planar body-route planning for a six-legged robot. A candidate route is a sequence of body waypoints. The controller follows this sequence using a fixed tripod gait. Foot placement, perception, gait learning and mission-level scheduling are separate problems; improvements in those areas cannot be credited to this route refiner without separate experiments.

1 2 Questions tested in version 3

The primary question is whether bounded Pareto resource-label refinement improves the declared route score relative to common A* seeded PSO and ACO implementations, using matched cases, seeds, limits and computational budgets. A second question asks whether the extra refinement is useful beyond distance A*, energy A* and inexpensive greedy shortcuts. A third asks which individual proposal features change the outcome.

The physics experiment then checks whether an admitted route can be executed by the assisted controller and whether the forecast agrees with simulated movement. It does not test a real battery, unassisted balance or an unknown physical environment. These boundaries determine the claims that the results can support.

1 3 Implemented contributions

The framework supplies one continuous route evaluator, explicit destination-and-return resource checks and shared collision geometry. Adaptive initialization preserves the A* frontier rather than repeating completed expansions after a short seed-search timeout. PSO, ACO, greedy and the proposal receive the same adaptive recipe, avoiding an exclusive initialization advantage for the proposal.

A single procedural specification creates physical obstacles and shallow terrain tiles, together with the planner terrain queries. Development and test worlds use disjoint seeds and hashes. The campaign freezes cases before tuning, provides each optimizer the same two-profile tuning opportunity and preserves every rejection and tie. An integrity audit recomputes important quantities from saved records.

The proposed refiner combines established Pareto-label ideas [5] with heading-aware safe shortcut corridors, bounded labels and resource checks. This is an implementation-level research contribution whose novelty must be assessed against the literature. It is not a newly proven general optimization principle, and the experiment does not reproduce unrestricted global PSO, a complete published ACO planner or a learned hexapod navigation system.

1 4 Changes from the earlier study

The earlier study used 12 test task/obstacle layouts on one underlying terrain and three main methods. Version 3 uses 24 new generated test worlds, six main methods and explicit feature-removal tests. It also records prediction errors and provides an external calibration workflow. Its larger attempt count strengthens traceability and coverage, but attempts on different task distributions cannot be used to claim a before-and-after percentage performance improvement.

2 Related work and adaptation boundaries

2 1 Foundational optimization methods

A* supplies the graph-search basis for collision-checked seed routes [2]. PSO uses particle position, velocity, personal-best and population-best information to search a numerical representation [3]. The implementation here converts numerical keys into selected corridor waypoints. ACO uses pheromone-guided discrete construction and reinforcement [4]; this implementation is an elitist Ant-System-style adaptation, not exact Ant Colony System. Multicriteria shortest-path labeling [5] motivates retaining alternative resource vectors rather than immediately choosing one prefix by a single score.

2 2 Hexapod gait and terrain methods

Smart Gait addresses swing trajectories, gait period and duty, and adaptive gait sequences on a hexapod platform [6]. Its published results belong to that controller and robot. The present study freezes the default gait and does not implement its whole-body control or inherit its numerical savings. A separate gait-calibration interface in the software must be evaluated separately from these planner trials.

Chen et al. combine terrain geometry and semantic information for hexapod motion planning [7]. This motivates footprint-scale terrain descriptors here. Version 3 uses known simulator height queries and declared terrain grades; it does not implement semantic camera perception, probabilistic sensor-map fusion or the original foothold search. Its terrain exposure is a cost proxy rather than a calibrated failure probability.

2 3 Energy and stability aware navigation

Energy-aware delivery planning for legged robots considers task and battery decisions [8]. Only the publisher abstract and introduction were accessible in the retained review, so the complete method is not reproduced. The present system defines its own battery ledger, destination-and-return reserve and modeled terminal service. It does not implement payload splitting or the paper-specific replacement schedule.

STATE-NAV combines learned bipedal traversability, uncertainty-aware velocity selection and navigation/control components [9]. The retained source is arXiv version 4. The current project neither trains TravFormer nor implements its bipedal MPC. A small tilt angle under body-posture assistance cannot be treated as equivalent evidence of autonomous stability.

2 4 Benchmarking implications

COCO emphasizes explicit instances, settings, budgets and termination rules in optimizer evaluation [10, 15]. This project follows those transparency principles but is not a COCO benchmark. Demšar discusses comparisons across independent datasets in a different application domain [11]; the relevant lesson here is to distinguish independent worlds from repeated seeds. The current analysis uses descriptive paired world bootstrap intervals rather than borrowing a classifier significance claim.

The review is targeted, not exhaustive. Before submission, the author should obtain the full energy-delivery paper and compare recent resource-constrained route planners in detail. A larger bibliography alone would not establish novelty; the report must identify precisely which representation, search rule or validated capability differs from prior work.

3 Research system and evidence flow



Figure 1. The console launches trials, one world specification feeds planning and physics, and the comparison interface reads saved records. The integrity audit checks the recorded evidence; it does not create additional robot measurements.

3 1 Hexapod Research Lab

Research Lab is the experiment control interface. The user chooses the scenario suite, methods, repetitions, planner budget, locomotion and whether to execute physics. The runner constructs the case, prepares common graph information, runs each method in a shuffled paired order and saves its result. One experiment process holds a file lock to prevent concurrent benchmark runs from sharing this execution path.

3 2 Hexapod Method Comparison

Method Comparison is a read-only analytical view of a selected run. It displays admission, conditional route quality, wall time, route geometry and physics diagnostics when available. Scenario, repetition and terrain-family controls filter the recorded trials. The complete held-out paired summary is explicitly labeled when its counts do not follow those filters. The dashboard does not train an optimizer or generate new experimental observations.

3 3 One attempt and its identifiers

An attempt is identified by study phase, run identifier, case identifier, method and zero-based repetition. Its trial seed is the case seed plus 100003 times the repetition index. The plan record stores points, predicted metrics, limits, feasibility, diagnostics and actual optimizer parameters. A physics record is added only when execution is enabled and the plan is admitted. The same case and seed are assigned to every compared method.

JSON preserves the detailed evidence, including routes and traces. CSV gives a flat trial table. The frozen manifest, selected-parameter hash, source snapshots and generated-model hashes make the run inspectable. Duplicate trial keys are an error; equal metric values from different valid keys may be a legitimate deterministic result. Unavailable measurements remain null rather than being converted to zero.

4 Procedural worlds and terrain representation



Figure 2. Four actual held-out worlds from the frozen manifest. Grey rectangles are physical obstacles; shaded areas are terrain patches; circles mark starts, squares destinations and triangles service stations. These are plan-view maps in metres, not photographs or measured real environments.

Table 1  World family construction



Each world occupies a 48 m × 48 m planning region. The 0.25 m grid has 193 × 193 positions. Each terrain patch has 12 shallow physical tiles. Grade 1 tile heights range from 0.025 to 0.045 m; grade 2 heights range from 0.040 to 0.085 m. Terrain pads have 0.020 m tops. The sampled ground-friction coefficient is 1.3 times 0.8, 1.0 or 1.2. These simple worlds do not model deformable mud or granular soil.

5 Robot simulation and measurement scope

5 1 Shared navigation geometry

The robot model is held fixed across methods. Eight-neighbor graph motion forbids diagonal corner cutting. Obstacle clearance uses the navigator footprint radius of 1.82 m, a tracking margin of 0.12 m and its grid allowance. Final waypoint connections receive continuous segment-clearance checks. The corridor refiners may remove intermediate waypoints, but every new chord must pass the same collision query.

The world specification drives both physical MuJoCo geometry and terrain-height, severity and speed queries. Scoped bindings are restored after each case. Terrain-height and collision tests check that the procedural planner interpretation agrees with generated physical geometry. This synchronizes a known model; it is not validation of an external sensor map.

Table 2  Fixed execution settings



5 2 Assistance and the consequences

Horizontal body velocity is imposed during physics substeps. Vertical position and roll/pitch response also receive direct assistance, and gravity compensation is enabled. These interventions help compare route following repeatably, but they contribute support and movement that are not included in actuator-work integration. MuJoCo is a dynamics engine [1, 12]; the scientific validity of a claim still depends on the controller and model used.

Body tilt, foot contact, support margin and slip are diagnostics of this assisted system. They cannot establish torque-feasible autonomous walking or real-world fall risk. The present study holds those assistance choices constant to isolate route-planning differences. A future locomotion study must test stronger dynamics without assuming that the existing results transfer.

6 Multiobjective optimization in simple terms

Multiobjective optimization means considering several goals at once. For this robot, a route can be short but slow, fast but battery-hungry, or easy to walk but longer. No route needs to be best on every goal. A useful planner keeps alternatives long enough to judge which trade-off fits the mission limits.

Table 3  Illustrative teaching routes only



These invented teaching values are not experiment results. A is shorter and uses less modeled battery than B. B is faster and has less terrain exposure. Neither dominates the other. C is worse than A on all four quantities, so A dominates C. Dominance lets a Pareto search discard C while retaining the useful A-versus-B trade-off.



Figure 3. A two-dimensional view of the illustrative teaching routes. Distance and exposure are also considered in Table 3. This sketch explains dominance; it is not an estimated experimental Pareto front.

6 1 Choosing one route

The implementation reports one route using a common score after feasibility is checked. The score converts the four quantities to declared reference scales. For illustrative A, Q = 14/50 + 24/90 + 11/30 + 0.25 × 3/20 = 0.9508. For B, Q = 0.9769. The chosen weights prefer A if both meet the limits; a deadline of 23 s would reject A and leave B admissible.

This distinction matters: keeping Pareto labels during search does not mean the final experiment evaluates a full Pareto front. The report measures a single preference-selected solution. It does not report hypervolume or prove global Pareto optimality. Changing the preference weights would define a different comparison and needs a separate, preplanned sensitivity study.

7 Cost model and mission constraints

7 1 Distance time and modeled battery

For route P, D is the sum of segment lengths in metres and Θ is total absolute heading change in radians. Predicted time sums distance divided by the applicable terrain speed, turn time at the reference 1 rad/s rate, and the 0.6 s start/stop allowance. Long segments are split at terrain boundaries before evaluation. For a nonzero walking-only route, the nominal battery ledger is

     (1)

E is percentage points of usable battery capacity, not joules. The four coefficients are explicit simulation assumptions. Version 3 provides an external fitting workflow, but the reported campaign uses the nominal values. Mechanical actuator work is measured separately during execution.

7 2 Terrain exposure

Nine height samples over the footprint window provide mean height, height range and height variation. Slope comes from the gradient of mean height. Difficulty is 0.25 times the sum of slope/0.25 rad, height range/0.12 m, height standard deviation/0.04 m and the assumed softness lookup, clipped to [0, 2]. Softness levels are 0, 0.25, 0.60 and 1. Exposure H integrates this difficulty along the route with approximately 0.125 m or finer sampling. It measures accumulated modeled difficulty, not probability of falling.

7 3 Common preference

     (2)

Smaller Q is preferred among admissible routes. The denominators are reference scales chosen for the experiment, not learned physical constants. A 1% improvement in Q is not a 1% improvement in electrical energy, walking stability or mission success. All six methods receive the same final evaluator even though their search objectives differ.

7 4 Destination and safe return

     (3)

     (4)

The runner finds a common minimum-modeled-energy reference return route from the destination to available stations. The factor 1.25 adds a 25% round-trip allowance, and 6 adds six reserve points. These are conservative design rules, not statistically calibrated chance constraints. The return forecast uses a common heading and does not jointly optimize intermediate charging decisions.

For example, an outbound prediction of 15 points and a return forecast of 20 points require 1.25 × 35 + 6 = 49.75 points. A 45-point battery would reject the route even if the path is collision-free. Planner budget is different: 2 s means the computer may spend up to about two wall-clock seconds searching; it does not schedule battery charging every two seconds.

8 Adaptive common initialization



Figure 4. The 2 s initialization and refinement budget. Later seed stages run only when needed. Fast initial success may allow time- and distance-oriented seed families before the original 0.6 s seed deadline. Every stage is charged to the method timer.

The first energy A* search receives 30% of total time and a 30,000-expansion cap, which is 75% of the 40,000 nominal total. If it stops without a route because of time or expansion limits, its saved frontier can resume until 70% of total time with the same energy cap. A distance A* fallback can then use the remaining expansion allowance until 90% of total time. The final portion remains available for evaluation and refinement. Resuming an already exhausted expansion cap does not grant extra expansions.

Algorithm 1 Shared adaptive seed procedure

01  Start one total wall timer and the common expansion allowance.

02  Search energy A* until the initial seed deadline or energy cap.

03  Retain frontier costs parents and queue when the seed is unfinished.

04  Resume that frontier to the extended deadline when permitted.

05  If still unfinished try distance A* with remaining expansions.

06  If initial work finishes early try other seed families in time.

07  Remove duplicate seed routes and create safe forward corridors.

08  Evaluate original routes and common greedy shortcuts.

09  Use remaining time for the selected refiner; greedy stops here.

10  Recheck complete-route metrics constraints and diagnostics.

A portfolio means several distinct seed corridors, not a guarantee of three returned seeds. Each corridor is a forward waypoint sequence; refiners may choose safe subsequences. The portfolio cannot represent every topologically different route in the map. All unique corridors share the remaining time and candidate allowance.

PSO, ACO, greedy and the full proposal use this adaptive initialization. The fixed-seed-time control deliberately retains the older 30% allocation. Distance A* and energy A* are standalone baselines with their declared search objective and total method budget. Shared graph and return-route preprocessing are recorded separately from all method timers.

9 Baselines and particle swarm refinement

9 1 Simple baselines

Distance A* searches the shared grid for a short route. Energy A* uses the nominal energy edge cost including turning. Each returned route receives continuous evaluation and may still be resource-rejected. The greedy baseline uses the common seed portfolio, evaluates the original route and a repaired aggressive shortcut for each unique corridor, and returns its best feasibility-ranked result. It provides an important test of whether expensive search adds value beyond safe simplification.

9 2 PSO representation and updates

For a corridor with n waypoints, PSO uses n − 2 internal random keys in [0, 1]. A key at least 0.5 requests that waypoint. If a requested skip crosses an obstacle, decoding inserts safe forward corridor nodes. The initial population includes original-route and aggressive-shortcut key selections. Personal and global bests use the same feasibility-first rank as the proposal.

     (5)

     (6)

The selected version 3 PSO uses 24 particles, inertia w = 0.55, cognitive coefficient c1 = 1.70 and social coefficient c2 = 1.30. Velocity is clipped to ±0.25. Independent random matrices r1 and r2 are generated from the paired trial seed. This is a corridor-refinement adaptation of PSO [3], not an unseeded global planner.

Algorithm 2 PSO hybrid

01  Obtain common safe corridors and the remaining total budget.

02  Initialize bounded random-key positions and velocities.

03  Include original-route and aggressive-shortcut particles.

04  Decode and repair each particle to a safe waypoint subsequence.

05  Evaluate feasibility violation and then the common route score.

06  Update personal best and swarm best when the rank improves.

07  Apply velocity and position updates with the recorded limits.

08  Continue up to 40 iterations per corridor while caps permit.

09  Return the best retained whole route and observed diagnostics.

The common rank first prefers a feasible route. Among infeasible candidates it minimizes summed positive normalized limit violations, then Q. Routes cannot be labeled successful merely because their score is attractive. Fitness caches avoid recounting identical decoded candidates as new evaluations; repeated particle states can therefore produce no new progress point.

10 Ant colony route refinement

ACO constructs a route through forward-visible corridor waypoints. From current index i, an ant considers every later index j whose chord passes continuous clearance. Its heuristic favors safe forward progress relative to chord length and remaining straight-line distance. Transition probability is proportional to pheromone raised to α and this heuristic raised to β.

     (7)

The selected configuration uses 12 ants per generation, α = 1, β = 2 and evaporation ρ = 0.20. Possible forward edges start with unit pheromone. An ant continues until reaching the final waypoint or failing to construct a complete sequence. Complete paths are evaluated by the same waypoint corridors and whole-route constraints used for the other refiners.

Algorithm 3 ACO hybrid

01  Obtain common safe corridors and remaining computation budget.

02  Initialize pheromones on forward candidate connections.

03  For each ant start at the corridor first waypoint.

04  List later waypoints with collision-checked visible chords.

05  Sample the next waypoint from pheromone and progress weights.

06  Continue construction to the destination when possible.

07  Evaluate each complete route with the common feasibility rank.

08  Evaporate pheromone and reinforce generation routes and incumbent.

09  Clamp pheromone values to the recorded finite range.

10  Continue up to 40 generations per corridor while caps permit.

11  Return the best retained route and actual search diagnostics.

10 1 Reinforcement and constraint handling

The implementation multiplies pheromone by 1 − ρ after each generation. Generation routes and the retained best route then deposit 1 divided by [1 + Q + 100V + 100I], where V is normalized constraint violation and I is 1 for infeasible routes and 0 otherwise. Pheromones are clipped to [0.0001, 10]. This discourages infeasible construction without deleting those outcomes from the records.

This procedure is an elitist Ant-System-style adaptation of established ACO ideas [4]. It does not implement the ACS q0 policy or its original local pheromone update. The baseline should therefore be named and described by its actual implementation rather than attributed as a faithful reproduction of a particular published robotics system.

10 2 Why ACO and PSO may agree

The two methods search the same finite waypoint alternatives, receive the same initial greedy routes and use the same final preference. When the initial shortcut is already the best available candidate, both can return exactly the same result. Different search mechanisms do not require different output routes. Observed best-score traces record improvements that actually occurred; a flat or absent trace is not filled with invented iterations.

11 Proposed bounded Pareto resource labels

11 1 State and dominance

A label stores the previous waypoint, current waypoint, cumulative distance, predicted time, modeled battery, terrain exposure and a parent link. Previous and current waypoints together preserve the incoming heading needed for turn accounting. Two labels at the same heading state can be compared component by component. A label dominated by another is discarded; useful trade-offs are retained subject to a memory cap [5].

Segment metrics are cached. The search removes the one-off start/stop allowance from each segment contribution and adds it once for the route, avoiding a stop penalty at every mathematical chord. Incoming turn time and turn-energy terms are then accumulated explicitly. Complete routes are always re-evaluated using the common continuous evaluator before they become the reported result.

Algorithm 4 Proposed walking mode refiner

01  Initialize safe original and greedy whole-route incumbents.

02  Create the start label with one start and stop allowance.

03  Prioritize labels using accumulated score plus a remaining bound.

04  Pop an active label and retain its incoming heading.

05  For each later waypoint check continuous chord visibility.

06  Add cached segment metrics and the heading turn cost.

07  Prune resource-bound violations when that feature is enabled.

08  Prune score bounds that cannot improve a feasible incumbent.

09  At the same heading state remove dominated cost labels.

10  Keep at most eight labels per state in the selected profile.

11  Record parent links for every retained label.

12  At the destination reconstruct the complete waypoint route.

13  Re-evaluate complete metrics and update the feasible-first best.

14  Stop at wall time expansion or candidate evaluation limits.

11 2 Bounds and bounded computation

A remaining-distance bound uses the straight-line distance to the destination. The time bound uses the walking ceiling, the battery bound includes nominal walking and hotel costs, and remaining terrain exposure is bounded below by zero. Resource pruning compares these estimates with deadline, task battery after return reserve, and exposure allowances. The label cap and finite corridor representation make the method approximate even when such bounds are useful.

At most 240 whole-route candidate evaluations are available across the method corridors, with nominal 40,000 expansions shared between seed work and labels. Visibility checks, segment-metric calculations and full-route evaluations are different operations; equal high-level caps do not imply equal primitive computational work. For n corridor nodes, up to n(n − 1)/2 forward chords may be considered, while uncapped resource labels can grow combinatorially. The label cap trades completeness for bounded storage.

The current walking search can miss globally better routes outside its seed corridors or discard useful labels at its cap. The separate hybrid-locomotion mode uses a beam fallback and is outside the primary walking-only evidence. No full-map optimality, universal dominance or formal real-time guarantee is claimed.

12 Experimental protocol and fairness

12 1 Frozen cases and splits

The manifest fixes 8 development worlds with seeds 830000 to 830007 and 24 held-out worlds with seeds 940000 to 940023. Families cycle through open, clutter, rough and corridor. Start and goal candidates are drawn inside [−17, 17] m on each axis with nominal separation between 12 and 26 m, snapped to free grid locations and retained when snapped separation is at least 10 m. Cases are not filtered according to optimizer wins or resource feasibility.

Deadline is sampled from 45, 70, 110 or 160 s; initial battery from 45, 65, 85 or 100 points; exposure limit from 10, 20 or 40; and execution energy multiplier from 0.85, 1.00 or 1.20. These are independent random choices within the case generator, not a balanced factorial design. Six held-out worlds belong to each terrain family. The small family samples limit any attribution of outcomes to one terrain or resource factor.

Table 4  Frozen campaign phases



12 2 Pairing and preselection

For repetition j starting at zero, the trial seed equals the case seed plus 100003j. Within a case the method/repetition order is deterministically shuffled. Paired seeds reduce avoidable mismatch in stochastic input; they do not make PSO and ACO perform identical random operations. The proposed walking-label search is effectively deterministic apart from wall-time termination, so repeated outcomes may be identical.

The ablation and physics subsets are the first eight and first six held-out case identifiers fixed before tuning. They were not chosen retrospectively for success. Physics is attempted only after planning admission. In this study all 36 scheduled physics plans are admitted and executed. The 24 tiny exhaustive-reference cases are separate synthetic software-validation fixtures and are not added to the 684 experimental attempts.

A manifest hash and scientific source lock prevent a modified method from silently resuming the same campaign. New scientific code needs a new version; fresh confirmatory evidence also needs new world seeds. Old inspected cases remain labeled diagnostic. Tuning, test and diagnostic results must not be pooled into one inflated statistical sample.

13 Parameter selection and analysis

13 1 Equal development opportunity

Table 5  Two tested profiles per optimizer



Selection first maximizes development admission, then minimizes mean common score among admitted routes; exact ties keep the default. All profiles admit 14 of 16 attempts per method. PSO default mean Q is 1.322402 and alternative mean Q is 1.321889, so the alternative is selected. ACO and the proposal have equal default/alternative means of 1.321376 and retain their defaults. Selected settings are frozen before test execution.

Both swarm methods permit at most 40 iterations per corridor. ACO keeps α = 1 and deposit coefficient 1. The proposal retains an archive capped at 16 entries. The selected profile also records a beam width of 6 for the separate hybrid fallback, which is not an active walking-label parameter. Two profiles per method provide equal tuning opportunity, not an exhaustive search over each optimizer’s best settings.

13 2 Denominators and paired differences

Admission rate counts all scheduled planning attempts. Mission success counts all scheduled physics attempts, including any plans that would have been rejected before movement. Route-cost means condition on admission; physics-cost means condition on success. These selected populations can differ between methods, so unconditional means alone are insufficient for a fair quality claim.

     (8)

A positive ΔQ favors the proposal. Score wins, ties and losses are counted only when both methods are admitted; differences no larger than 10⁻⁸ in absolute value count as ties. Only-proposed-admitted, only-baseline-admitted and both-rejected outcomes are retained separately. Admission advantage uses every scheduled pair and is reported in percentage points.

13 3 Uncertainty and computation

For each baseline, repeated score differences are averaged within each jointly admitted world. A descriptive percentile interval resamples those world means with replacement 5,000 times using analysis seed 4100. The admission interval similarly resamples world-mean paired admission differences over all 24 worlds. This respects clustering by world, but the conditional score analysis excludes jointly rejected worlds and cannot describe their quality.

The intervals are descriptive, with no multiple-comparison correction or precomputed power justification. No p-value or acceptance probability is claimed. The recorded machine has an Intel Core i5-7600 at 3.50 GHz, four logical CPUs and Python 3.10.12. Mean common model/graph/return preparation is 0.776 s per held-out case, maximum 0.943 s; it is excluded from method planning time. Wall-time results are not isolated hardware microbenchmarks.

14 Held out planning outcomes



Figure 5. Admission and resource rejection for every scheduled primary planning attempt. Every method returns a route in this held-out study; there are no primary no-route outcomes. Admission is a predicted resource decision, not a measured mission-success rate.

Table 6  Primary planning results



Distance A* admits 63 attempts and rejects 9. Energy A*, greedy, PSO, ACO and the proposal each admit 66 and reject 6. In every method, heldout_12 and heldout_14 fail the battery-plus-return rule in all three repetitions. Distance A* additionally fails the deadline on heldout_24 in all three repetitions. None of the primary routes fails the terrain-exposure limit. The larger proposal admission versus distance A* is therefore specific to the tested deadline case.

The primary proposal admission rate is 91.7%, but the earlier version’s 25% cannot serve as a before/after baseline: its cases, map extent and resource conditions differ. This study supports comparisons between methods on the same version 3 cases. It does not prove that the software update caused a 66.7-point improvement across a common test population.

Means in Table 6 include each method’s admitted routes. Distance A* has one fewer admitted world, so its mean Q should not be compared directly with the proposal’s mean without the paired table. On this machine the proposal’s mean planner time is lower than both tuned swarm implementations, but higher than standalone A*. Such timing depends on corridor length, cache behavior and wall-clock load.

15 Paired route quality and uncertainty



Figure 6. Complete paired outcomes against each baseline. Wins and ties refer to the declared common score among jointly admitted attempts. No baseline-only admission or baseline-lower-score outcome occurs in this saved primary run.

Table 7  Paired score advantage by independent world





Figure 7. Saved world-bootstrap intervals for conditional score advantage. The right panel uses an expanded numerical scale to show the small PSO/ACO differences. Positive values favor the proposal; interval magnitudes remain small.

Against PSO there are 3 wins and 63 ties among 66 admitted pairs; against ACO there are 9 wins and 57 ties. Both have 6 jointly rejected pairs. The PSO interval reaches zero. The ACO lower endpoint is positive but approximately 0.000000730 score units, rounded in Table 7; this should not be described as a substantial practical improvement. Admission advantage over distance A* is 4.167 points with interval [0, 12.5]; the other four baseline admission differences are exactly zero in the tested worlds. These results do not establish a broad or hardware performance advantage.

16 Worked example from a saved test world

The following example is heldout_22, the first repetition of the clutter family world with seed 940021. The start is [-5.0, -6.0] m and the destination is [7.25, -17.0] m. The deadline is 110 s, initial battery 65 points and exposure allowance 10. The common return forecast is 9.389306 battery points. These are saved experimental values, not the teaching example in Section 6.

Table 8  Actual predicted metrics for heldout 22 repetition 1





Figure 8. Actual planned routes for ACO and the proposal on the same held-out world. Routes may appear almost identical at full-map scale. No measured trail is shown: this world is outside the six-world physics subset.

For the proposed route, the common evaluator gives Q = 16.685318/50 + 30.332685/90 + 12.461721/30 + 0.25 × 1.196977/20 = 1.101089. Required battery is 1.25 × (12.461721 + 9.389306) + 6 = 33.313784 points. It passes the saved limits.

The relative score improvement over ACO is 100 × (QACO − Qproposed)/QACO = 0.07630%. This is a very small composite-score change, not a measured electrical-energy saving. The PSO route ties the proposal in this repetition. Repetition 3 has a larger PSO score difference, but choosing only that outcome would hide the full distribution; the complete paired counts must remain the main comparison.

17 Feature removal and timeout diagnosis

17 1 What an ablation tests

An ablation disables one feature while retaining the other conditions. Version 3 compares the full proposal with fixed initial seed time, one seed family, and disabled resource-bound pruning. The first eight held-out worlds and three paired repetitions give 24 attempts per variant. This tests whether added complexity changes outcomes in the selected subset; it does not guarantee that all features will prove useful.

Table 9  Full proposal versus each feature control



The full proposal has 12 lower scores and 12 ties against one seed family. Its mean world score advantage is 0.020317 with descriptive interval [0.004092, 0.041358]. Multiple initial corridors therefore help some cases in this subset. All variants are admitted in all 24 attempts, so the component evidence concerns route quality, not admission.

The fixed-time and unpruned controls each tie the full proposal in all 24 comparisons. There is no demonstrated final-output gain from adaptive time allocation or resource pruning in these eight relatively tractable worlds. The fixed control also changes expansion allocation and removes adaptive fallback, so it tests the recovery policy as a whole, not time extension alone. The unpruned control retains heading labels, score bounds, dominance and final feasibility checks. Broader feature benefits need harder independent tests.

17 2 The two older timeout cases

Table 10  Old-case development diagnostic only



The fixed allocation returns no routes in six attempts. The adaptive PSO, ACO and proposal each return six routes, all resource-rejected. Reusing the frontier and permitting fallback therefore resolves the previous lack of route metrics on these cases. It does not make their battery-return requirement feasible. Because these cases were already inspected, they are diagnostic evidence rather than fresh confirmation of a general benefit.

17 3 Separate software correctness evidence

Exhaustive subset enumeration on 24 tiny synthetic forward-visibility graphs agrees with the resource-label search on admission and admitted score, with zero mismatches. These fixtures check a restricted additive setting with at most nine corridor nodes in the tested construction. They do not certify optimality on the large MuJoCo worlds, and their outcomes must not be counted as robot trials. The campaign integrity audit passes 684 unique attempts with no reported errors or warnings.

18 Assisted physics results

Table 11  Results on six preselected physics worlds





Figure 9. Actual assisted-execution means on the same six worlds. Destination time excludes the return leg; mechanical actuator work includes the destination and return. Each bar summarizes six successful missions. These quantities are not electrical battery energy.

All six methods succeed in all six worlds. The success measure is saturated and cannot rank their reliability on this subset. Six successful worlds also provide limited evidence about rare failures, harder terrain or another controller. The physics subset was fixed in advance, but its first-six construction does not guarantee representative resource difficulty.

The proposal averages 28.880 s to the destination and 7564.756 J of positive mission actuator work. PSO averages 28.872 s and 7563.809 J, so the proposal is 0.008 s slower and uses 0.946 J more on average. ACO matches the proposal in both means. These small differences do not support a physical-performance advantage over the swarm baselines.

Relative to greedy shortcuts, the proposal is 0.507 s faster on average but uses 9.690 J more positive actuator work. Relative to energy A*, it is 2.520 s faster and uses 330.270 J less work. These are descriptive comparisons on the same six assisted worlds, without an independent hardware claim. The results illustrate why a lower composite planning score cannot be interpreted as uniformly lower execution cost.

Success requires reaching the destination by its deadline and completing the station return without an execution guard, with minimum battery at least 2 points. Terminal service is modeled after arrival. One service event per completed mission largely follows the experiment design; identical charging counts are not independent evidence of a better charging policy.

19 Forecast validation and data reliability



Figure 10. Destination-time forecasts versus simulated execution for all 36 destination-reaching physics trials. The dashed line is exact agreement. Overlapping points may hide identical outcomes from different methods. Every saved destination time is below its corresponding forecast in this subset.

Table 12  Prediction errors on all 36 executions



Error is executed value minus forecast. A positive time error would indicate underprediction. Here all time errors are negative. The planned geometry, turn model, execution arrival tolerance and route follower need not produce identical time estimates. Conservative average time is useful for these cases but does not prove that the deadline model is conservative in unseen environments.

The case execution multipliers perturb motion-based battery accounting independently of the nominal prediction. This allows an internal mismatch check, but the prediction and execution ledger still share a designed cost family. Agreement between them cannot validate electrical consumption. The reported battery error must therefore be called a simulation-ledger error, not hardware calibration accuracy.

19 1 Why equal values and unavailable values occur

Repeated seeds are paired observations on one world. A deterministic label search or a shared best shortcut can return the same coordinates repeatedly. Fresh simulation states and the same controller may then reproduce the same telemetry. Equal values are legitimate when their route and execution evidence agree. Duplicating a trial identifier or copying a fabricated result would be a different problem; the audit checks unique keys and complete phase counts.

Planning-only attempts have no measured mission time or work. A rejected plan never executes, and a failed execution may not reach the destination. Those values remain unavailable because the relevant observation does not exist. They should not be filled with zero or deleted from success-rate denominators. Version 3 primary planning has complete route metrics, while its physics measurements exist only in the separate physics phase.

19 2 What the audit establishes

The audit checks source archives and model hashes, disjoint development/test worlds, frozen parameter selection, unique paired trial keys, recomputed admission, common scores, route lengths, success rules and recorded prediction residuals. These checks support internal consistency and provenance. They do not certify sensor accuracy, physical realism, statistical power or novelty.

20 External electrical calibration workflow



Figure 11. Implemented calibration workflow awaiting actual external measurements. No hardware-fitted profile was used in the reported campaign. The diagram describes a supported procedure, not a completed electrical experiment.

A sensor must measure electrical energy supplied by the battery, in watt-hours, and usable battery capacity must be stated in watt-hours. Convert the measured energy to percentage points as 100 × measured Wh / usable Wh. Use real sensor records rather than positive actuator work or the simulator battery ledger. Temperature, payload, contact conditions and battery state can affect whether the fitted model transfers.

     (9)

The fitter uses nonnegative least squares for four walking coefficients: distance, time, turning and a mission intercept. Inputs must vary enough to identify all four coefficients. If distance and time are nearly proportional in every observation, their separate effects may be poorly identified even when a numerical fit is possible. The software checks full column rank; the researcher must also inspect practical conditioning and residuals.

Table 13  Required measurement CSV fields



The software requires at least 12 calibration rows, 6 validation rows and at least three distinct missions in each split. Calibration and validation mission identifiers and map identifiers must be disjoint. Those are software safeguards, not a publication sample-size justification. Metadata must state external hardware origin, usable battery capacity and sensor description; a label cannot prove that a sensor was actually used.

The fitter saves coefficient values, input-file hashes and held-out mean absolute and root-mean-square errors. A fitted walking profile can then be applied to a new walking-only run. It does not automatically calibrate wheel mode, transformations, sensor bias, battery aging or assistance energy. No current evidence justifies labeling the nominal campaign hardware-calibrated.

21 Limitations and publication readiness

21 1 Limits of the algorithmic comparison

All three advanced methods search subsequences of common seed corridors. The representation may constrain them so strongly that extra optimization yields mostly ties. The primary evidence does not compare unrestricted global planners, a complete exact constrained solver, NSGA-II or a verified reproduction of every cited paper. The simple greedy baseline is competitive and must remain visible. If extra complexity provides little practical gain, simplification may be a better contribution than adding more components.

Only two parameter profiles per optimizer were tuned. This is a small and equal opportunity, not proof that PSO or ACO was configured optimally. Fixed scalar scales and terrain thresholds may favor particular route trade-offs. A separate sensitivity study must vary these assumptions with a declared protocol rather than changing them after viewing favorable test results.

21 2 Limits of worlds measurements and inference

Twenty-four generated test worlds broaden coverage beyond the first fixed scene, but all follow one restricted generator, the same robot and the same controller. Start/goal and resource choices are not a balanced factorial experiment. Physics uses six preselected worlds, and all succeed. There are no physical robot trials, electrical sensor observations, deformable terrain, perception errors, moving obstacles or payload changes in the reported primary evidence.

The composite score is a modeled preference. Its small advantage does not establish a perceptible operational gain. Conditional score intervals omit rejected worlds, and repeated seeds do not increase the number of independent worlds. The uncorrected descriptive intervals should not be converted into broad statistical or causal claims. The simulation controller’s body assistance also limits interpretation of tilt and actuator work.

Table 14  Current evidence and remaining work



The report is now complete for the measured software scope, but the research is not established as submission-ready solely by its length or formatting. A Q2 or Q3 label does not define one universal manuscript standard. Quartiles depend on database, year and subject category; acceptance probability cannot be estimated responsibly from these records.

22 How to develop a stronger proposed method

22 1 Choose a limitation that matters

The next method should target a demonstrated weakness. In this campaign, simple seeded methods already solve most admitted cases and success saturates in physics. A useful research target could be recovering a different feasible corridor when the seed family misses one, reducing deadline or battery violations under real prediction uncertainty, or improving route execution under less body assistance. Each target needs a measurable outcome and a fair comparator.

One plausible next direction is a broader route portfolio that changes corridor topology, followed by resource-label refinement using independently calibrated time or electrical-energy uncertainty. This is a proposed research direction, not an implemented or proven version 3 feature. It would need a precisely defined diversification rule, a cost for generating alternatives and a common total budget for all compared methods.

22 2 Test each proposed benefit

Keep the version 3 campaign as historical evidence. Create a new development split, tune all methods equally, freeze parameters and declare a smallest useful effect before evaluating fresh worlds. Use stronger simple baselines and original-paper implementations when access permits. Include a no-diversification control, an uncalibrated-cost control and a no-uncertainty-margin control if those components are introduced.

A budget sensitivity study could compare 0.5, 1, 2 and 5 wall seconds on the same new worlds while reporting achieved quality, admission and actual runtime. A preference sensitivity study could vary distance, time, energy and exposure weights across predeclared profiles. These experiments are recommendations and have not been added to the current evidence. Exact constrained solutions on small instances can identify when approximation loses useful routes.

For physical validity, first measure actual electrical energy and validate forecasts on disjoint maps and missions. Then evaluate tracking, contact failures and energy under unassisted dynamics or a physical robot where available. Freeze route and controller separately in gait experiments, and freeze gait/controller in planner experiments. Otherwise a combined improvement cannot be assigned to one feature.

22 3 Define what would count as success

A stronger method should show a practical gain with its cost: more admissible missions, a useful paired time or electrical-energy reduction, a better quality-versus-budget curve, or robust performance on new environments. Report losses, failures and intervals alongside wins. If the advanced method ties a simpler baseline, explain the reason and consider reducing complexity. More records improve precision only when they answer a well-defined question with independent variation.

22 4 Conclusion

Version 3 provides a more complete and auditable comparison framework, adaptive seed recovery and independent procedural test worlds. The proposal improves modeled score over simple A* and greedy in some cases, while PSO and ACO usually tie it. Its physics evidence does not show an advantage over the swarm baselines. The most defensible present contribution is a transparent constrained simulation benchmark with bounded corridor refinement and clear validation limits. Further novelty and physical validation should precede stronger claims.

23 Preparing a journal submission

23 1 Select a journal by scope

Journal of Intelligent and Robotic Systems and Robotica are scope candidates to discuss with the supervisor, not confirmed Q2/Q3 targets or acceptance recommendations. Check the required database and category for the relevant ranking year through the institution. The Springer author instructions cover manuscript structure, references, declarations and research data [13]. Robotica publishes its own preparation instructions [14]. Recheck the selected journal’s current rules, fees and article type immediately before submission.

23 2 Assemble the paper and evidence

Prepare a research article with a concise abstract, explicit research question, focused related work, reproducible methods, results with complete denominators, discussion, limitations and conclusion. The technical sections of this report supply that material, while the tutorial appendices are better kept as supplementary guidance if a journal does not need them. Adjust structure, word count and citation style only after choosing the journal.

Complete author names, affiliations, corresponding-author details and contribution statements. Authors should verify the source code, calculations, literature descriptions and AI-assisted drafting. Add actual funding and competing-interest declarations, a truthful data/code availability statement, and any journal-required disclosure of AI use. Do not state that a dataset is public or that ethical approval exists unless those facts have been verified.

The supplementary package should include the manifest, frozen settings, all trial records, analysis scripts, model/source versions, figures and reproduction instructions. Preserve failures and ties. Remove private machine paths from a public package or provide a portable regeneration procedure; generated XML assets currently refer to local project resources. Do not redistribute third-party full-text papers unless their licenses permit it.

23 3 Obtain review before submitting

Ask the supervisor to assess novelty, baseline fairness, practical effect size and the gap between assisted simulation and the intended claim. Have another person reproduce at least the analysis and a small experiment. Resolve unexplained discrepancies before polishing the narrative. A complete report can still require more research, especially when the strongest baselines mostly tie the proposal.

Submit through the selected journal’s official portal after all authors approve the final manuscript. Prepare a cover letter that states the concrete contribution and simulation scope. Choose suggested reviewers only under the journal’s rules. If reviews arrive, respond to each comment with a specific change or a supported explanation. No submission or external communication has been made by this report update.

23 4 Declarations to complete

Data and code availability: local frozen evidence is retained in the project; the author must choose and verify a public repository or justified access statement before submission. Funding, competing interests and author contributions: to be supplied by the authors. AI assistance: code, plotting and report drafting received AI assistance; the authors remain responsible for verification and journal-specific disclosure. No human or animal participant study is described here.

References

[1] E. Todorov, T. Erez and Y. Tassa. MuJoCo: A physics engine for model-based control. Proceedings of the IEEE/RSJ International Conference on Intelligent Robots and Systems, 5026–5033 (2012). https://doi.org/10.1109/IROS.2012.6386109

[2] P. E. Hart, N. J. Nilsson and B. Raphael. A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics 4(2), 100–107 (1968). https://doi.org/10.1109/TSSC.1968.300136

[3] J. Kennedy and R. Eberhart. Particle swarm optimization. Proceedings of ICNN 1995, volume 4, 1942–1948 (1995). https://doi.org/10.1109/ICNN.1995.488968

[4] M. Dorigo, V. Maniezzo and A. Colorni. Ant system: Optimization by a colony of cooperating agents. IEEE Transactions on Systems, Man, and Cybernetics, Part B 26(1), 29–41 (1996). https://doi.org/10.1109/3477.484436

[5] E. Q. V. Martins. On a multicriteria shortest path problem. European Journal of Operational Research 16(2), 236–245 (1984). https://doi.org/10.1016/0377-2217(84)90077-8

[6] Y. Yin, F. Gao, Q. Sun, Y. Zhao and Y. Xiao. Smart Gait: A gait optimization framework for hexapod robots. Chinese Journal of Mechanical Engineering 37, article 15 (2024). https://doi.org/10.1186/s10033-024-01000-0

[7] C. Chen, J. Lin, B. You, J. Li and B. Gao. Hexapod robot motion planning investigation under the influence of multi-dimensional terrain features. Frontiers in Neurorobotics 19, article 1605938 (2025). https://doi.org/10.3389/fnbot.2025.1605938

[8] S. Chen, Y. Chen, Z. Wei, Q. Nguyen and S. K. Gupta. Energy-Aware Planning for Delivery Tasks Executed by Legged Robots. Proceedings of IEEE CASE, 1617–1624 (2025). Publisher abstract and introduction consulted. https://doi.org/10.1109/CASE58245.2025.11164088

[9] Z. Yoon, L. Y. Zhu, J. Lu, L. Gan and Y. Zhao. STATE-NAV: Stability-Aware Traversability Estimation for Bipedal Navigation on Rough Terrain. arXiv 2506.01046v4, 5 December 2025. https://arxiv.org/abs/2506.01046v4

[10] N. Hansen, A. Auger, R. Ros, O. Mersmann, T. Tušar and D. Brockhoff. COCO: A platform for comparing continuous optimizers in a black-box setting. Optimization Methods and Software 36(1), 114–144 (2021). https://doi.org/10.1080/10556788.2020.1808977

[11] J. Demšar. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research 7, 1–30 (2006). https://www.jmlr.org/papers/v7/demsar06a.html

[12] Google DeepMind. MuJoCo Documentation. Overview and model documentation. Accessed 28 October 2026. https://mujoco.readthedocs.io/en/stable/overview.html

[13] Springer Nature. Journal of Intelligent and Robotic Systems. Submission guidelines. Accessed 28 October 2026. https://link.springer.com/journal/10846/submission-guidelines

[14] Cambridge University Press and Assessment. Robotica. Preparing your materials. Author instructions. Accessed 28 October 2026. https://www.cambridge.org/core/journals/robotica/information/author-instructions/preparing-your-materials

[15] COCO project. The Experimental Procedure. Official benchmarking documentation. Accessed 28 October 2026. https://numbbo.github.io/coco-doc/experimental-setup/

References identify the literature and author instructions used to explain the study. The CASE source was available only through its abstract/introduction in the retained review. STATE-NAV is pinned to arXiv version 4. Algorithm descriptions and numerical results in this report are tied to the actual project implementation, rather than copied paper performance figures.

Appendix A Step by step website experiments

A 1 Open and inspect the saved study

Open http://127.0.0.1:8771/ on the computer running the project. Research Lab is where you run an experiment; the comparison page at http://127.0.0.1:8771/comparison/ is where you inspect saved evidence. To start with the primary study, use the Stronger research study links, choose the held-out planning run and click Use selected run in charts. Refresh an already-open comparison tab.

In Method Comparison, select heldout_22, repetition 1 and ACO as the paired-score baseline. Read the exact values in Table 8 or the trial table before judging the route drawing. The score advantage is about 0.0763%; a full-map drawing may look almost identical. The PSO comparison ties in this repetition. Use all cases again to return to the complete distribution.

A 2 Run three useful examples

Table A1  Valid settings for practical checks



Example 1 is a quick check of route finding, resource admission and scoring. Four terrain families give more variety than repeating one map. Six methods show whether complicated optimization adds value beyond simple A*. One repetition keeps the run short. The 2.0 s budget is valid for the input’s 0.1 to 30 s range and 0.1 s step. It is a search-time allowance, not the robot’s travel deadline or charging interval.

Example 2 keeps the same world seed and settings to connect predictions to physics. Only admitted routes execute. The number of actual executions may be below 24, and mission success must use all 24 scheduled attempts as its denominator. Inspect both the time and mechanical-work charts. Do not infer electrical savings from mechanical work alone.

Example 3 uses new worlds and three paired repeats to compare the full proposal with its fixed-time, single-family and unpruned controls. Four worlds × four variants × three repeats gives 48 attempts. Repeats change optimizer seeds; changing world seed creates different worlds. These exploratory examples are not automatically added to the frozen 684-attempt paper evidence.

A 3 Wait and inspect

Click Run comparison, wait for completion, then refresh the comparison page. Download JSON or CSV to inspect records. The frozen-study button resumes the existing campaign; it does not create new independent evidence.

Appendix B Troubleshooting and reproduction

Table B1  Common questions and checks



B 1 Reproduction commands

Run the commands from the mujoco directory using the project Python environment. These commands create or resume local work; they do not submit a manuscript. The frozen study source lock prevents silently resuming changed scientific code. A complete saved run can be inspected without rerunning the campaign.

python3 -m research.strong_study

python3 -m research.audit_strong_study

python3 -m research.run --suite procedural4 --world-seed 1050000

  --methods b1_distance b3_energy b7_greedy pso aco proposed

  --repeats 1 --planning-seconds 2.0

python3 -m research.calibration --template outputs/research/calibration_template

python3 -m research.calibration --csv YOUR.csv --metadata YOUR.json

  --out fitted_profile.json

python3 -m research.run --suite procedural4 --methods pso aco proposed

  --execute --energy-profile fitted_profile.json

Indented command lines above continue the preceding command and should be joined with spaces before execution. Add --execute to the procedural experiment for physics. Actual external sensor records are required before fitting an energy profile. No fitted profile is supplied as hardware truth.

B 2 Exact evidence identifiers

Primary planning run: 20261028T065751941702Z. Physics run: 20261028T070120014195Z. Evidence directory: mujoco/outputs/research/strong_study_v3. The all_684_trials.csv file retains every scheduled study attempt. The manifest and locked parameter files identify the cases and settings before test results.

Manifest SHA256

6f6d75052a5bb9210300e4af43af07fcddd5c1d52a26c0cb74191e1a96f47a50

Selected parameters SHA256

3ee0a43a6b219a5f62ea98b857b142f8043817e7ef49e51f1c95293a19090a91

The offline dashboard is a frozen planning snapshot and cannot launch experiments. It should be kept together with the complete evidence package. Website build and exact HTTP snapshot delivery were checked; browser visual and interaction verification were unavailable during preparation. Document pages were separately rendered and visually reviewed.

Appendix C Simple explanation for a supervisor

This project compares computer methods that choose a route for a simulated six-legged robot. Each method receives the same task and limits. The planner predicts distance, time, battery use and terrain difficulty. It rejects routes that cannot meet the deadline or keep enough battery for a station return. Admitted plans can then be followed in MuJoCo. The website displays the saved results and does not generate evidence by itself.

The proposal reuses unfinished search work and refines safe route shortcuts using Pareto labels. It sometimes lowers the modeled route score, but usually ties PSO and ACO. On six assisted-physics worlds, all methods succeed; the proposal has no physical-performance advantage over the swarm baselines. The study is traceable, but battery coefficients still need real measurements and the controller still assists the robot body.

Table C1  Key terms in ordinary language



C 1 What is finished and what is next

The implemented version 3 software, frozen campaign and complete report are finished for the stated simulation scope. The journal paper still requires author and supervisor review, defensible novelty, a selected journal format and appropriate validation for its claims. The next useful work is to measure real battery energy, test harder fresh worlds and assess the controller without relying on body assistance. A guaranteed publication percentage cannot be supplied.