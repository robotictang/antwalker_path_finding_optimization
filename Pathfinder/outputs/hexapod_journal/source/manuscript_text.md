Resource constrained route refinement for simulated hexapod navigation using swarm and bounded Pareto search

[Author names]

[Department and institution]

[Corresponding author email and ORCID identifiers]


# Abstract

Route planners for legged robots must balance travel cost, resource limits and computational effort. This study presents a reproducible MuJoCo framework for comparing A* seeded particle swarm optimization, ant colony optimization and a proposed bounded Pareto label refiner for assisted hexapod navigation. All methods use common collision checks, a fixed composite route score, a nominal two-second planning budget and explicit destination-and-return battery constraints. Parameters are selected using four development layouts and frozen before evaluation on 12 unused task and obstacle layouts with three paired seeds. The study records 48 development attempts, 108 held-out planning attempts and 12 physics attempts. Each method admits nine of 36 held-out planning attempts. Among nine jointly admitted comparisons, the proposed method achieves four lower scores and five ties against particle swarm optimization, and three lower scores and six ties against ant colony optimization. Mean score differences are small, and descriptive layout bootstrap intervals include zero. Only three physics attempts execute, one per method on the same accepted case; all complete with identical measurements. The results identify shared initialization timeouts and battery-return constraints as important bottlenecks. They support a transparent simulation benchmark, but do not establish general algorithmic superiority, electrical energy savings or unassisted robot stability.

Keywords  Hexapod navigation; resource constrained planning; particle swarm optimization; ant colony optimization; Pareto labels; reproducible simulation


# 1 Introduction

A navigation experiment can appear convincing when its charts show different numbers, yet meaningful comparison requires more than numerical separation. The methods must solve the same task, receive comparable resources and retain unsuccessful attempts in the reported denominators. For a battery-limited hexapod, a short outbound path may still be unsuitable if the robot cannot return to a service station. Equally, a smaller predicted route score does not necessarily imply less actuator work during execution.

MuJoCo provides a physics environment for evaluating model-based control and robot interaction [1]. In this study it supports a controlled simulation experiment, while explicit body assistance makes the scope narrower than autonomous dynamic locomotion. The research question is whether bounded resource-label refinement provides a useful improvement over two stochastic refiners when their representation, initialization recipe and final evaluator are held as consistent as practical.

A* offers a graph-search basis for generating collision-checked routes [2]. Particle swarm optimization (PSO) updates a population using personal and collective best solutions [3]. Ant colony optimization (ACO) constructs solutions through pheromone-guided choices; the implementation here follows an elitist Ant-System-style adaptation [4]. Multicriteria label methods retain alternatives with different cost vectors rather than immediately collapsing every prefix to one scalar value [5]. These are established ideas. Combining them in this implementation does not by itself demonstrate a new general optimization principle.

The work makes three practical contributions. First, it provides a common route representation and a continuous evaluator with explicit task, return-energy and terrain-exposure limits. Second, it compares an implementation of bounded Pareto resource labels with two A* seeded stochastic refiners under recorded budgets and parameters. Third, it links an experiment console to a source-backed comparison interface, preserving routes, seeds, failures and source snapshots. The evidence is presented as a preliminary simulation benchmark rather than a demonstrated replacement for state-of-the-art hexapod planning.


# 2 Related work


## 2.1 Gait and terrain reasoning

Smart Gait addresses swing trajectories, gait timing and adaptive leg-lifting decisions using robot dynamics [6]. Its contribution concerns locomotion control rather than waypoint-subsequence search. The present planner experiment freezes a default tripod gait and does not reproduce Smart Gait or inherit its reported savings. A separate gait-calibration dashboard exists in the software, but those calibration records are not pooled with the planner results in this manuscript.

Chen et al. combine geometric and semantic terrain features for hexapod motion planning [7]. This motivates footprint-scale height and terrain descriptors here. However, the present system uses a known terrain function and assumed semantic softness; it does not perform the paper’s perception pipeline or foothold planning. Its terrain score is therefore a declared geometric cost, not a measured probability of falling.


## 2.2 Energy and stability aware navigation

Energy-aware delivery planning for legged robots considers battery-related task decisions [8]. The accessible material for that reference is limited to the publisher abstract and introduction; its complete method is not reproduced. This study instead states its own nominal battery ledger and destination-plus-return requirement. Modeled terminal service is distinct from an implemented physical battery-swap mechanism.

STATE-NAV learns stability-aware traversability for bipedal navigation and combines it with planning and control [9]. The cited version is arXiv v4. Its learned instability model and bipedal controller are not implemented here. In particular, small body tilt under imposed posture assistance cannot be treated as evidence equivalent to stability-aware autonomous locomotion.


## 2.3 Benchmarking and the remaining question

The COCO framework emphasizes explicit problem instances, parameter settings and computational budgets in optimizer assessment [10]. This project is not a COCO benchmark, but uses these principles to separate development from evaluation and preserve unsuccessful results. Statistical comparison across datasets also distinguishes independent problems from repeated observations on the same problem [11]. Repeating three random seeds on one layout does not create three independent terrain worlds.

The remaining question is deliberately narrow: when safe corridors are initialized with the same recipe and scored by the same constrained preference, what differences remain between PSO, ACO and bounded resource-label refinement? The experiment cannot determine whether these corridor-restricted adaptations outperform unrestricted global planners, exact constrained solvers or recent learned hexapod controllers. Those comparisons require additional evidence.


# 3 Research framework

The software separates experiment execution from result inspection. Hexapod Research Lab selects a suite, methods, repetitions, planning time and optional physics execution. Hexapod Method Comparison reads a saved result and displays outcomes, route scores, wall time, routes and measured telemetry. The comparison website does not train a model or produce new measurements. Figure 1 shows the information flow.

Figure 1  Experiment and visualization workflow. Resource-rejected and empty outcomes are saved alongside accepted plans. The websites are interfaces to the same recorded experiment, not separate sources of evidence. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_1_system]

Each record has a scenario identifier, method, repetition and seed. Its plan stores the returned route, predicted costs, feasibility decision, search diagnostics and parameter values. An execution record is added only when physics is enabled and the plan is admitted. JSON retains the detailed evidence; CSV provides a flat attempt table. Missing measured values in planning-only or rejected attempts are structurally unavailable and are not imputed as zero.


## 3.1 Simulation and route representation

The recorded primary experiment uses MuJoCo 3.9.0 and NumPy 2.2.6. A 96 m by 96 m scene is discretized at 0.25 m, giving 385 by 385 grid nodes. Eight-neighbor motion forbids diagonal corner cutting. Collision queries use obstacle geometry and excluded terrain from the simulated scene. The navigator uses a 1.82 m radius, a 0.12 m tracking margin and an additional cell-size allowance. Final segments undergo continuous clearance checks, so removing waypoints cannot silently cross an obstacle.

A candidate is an ordered sequence of planar body waypoints from the start to the destination. This is body-route planning, not a foothold planner. Grid paths retain heading-dependent turn costs and are compressed by removing collinear vertices. Refinement can connect visible forward waypoints of an initialized corridor; it cannot invent an arbitrary new homotopy class outside the seed portfolio. This representation is shared by the three main methods.


## 3.2 Assisted execution and measurement scope

The default tripod gait has period 0.689655 s, duty factor 0.60, swing lift 0.13 m and a quintic swing profile. The physics timestep is 0.004 s, with four substeps per 0.016 s controller update. All physics trials start with the same reference heading of pi/2 radians. A fresh simulation state is constructed for each method, and the destination route is followed by a common return route.

The controller directly assists horizontal body velocity, vertical position and roll/pitch response, and gravity compensation is enabled. These choices support repeatable route execution, but provide external assistance not accounted for as actuator work. Tilt, contact and work measurements describe this assisted simulator. They do not validate torque-feasible autonomous walking, real electrical consumption or hardware stability.


# 4 Cost model and constraints


## 4.1 Four route quantities

For route P, the evaluator records distance D in metres, predicted destination time T in seconds, nominal outbound battery use E in percentage points of capacity, and integrated terrain exposure H. Distance is the sum of segment lengths. Terrain boundaries are used to split long segments before time and energy evaluation. Turn time assumes a reference angular rate of 1 rad/s, and a start/stop allowance is included. The nominal walking-speed ceiling is 0.75 m/s; terrain policies can reduce it.

[Equation 1]

Equation (1) is the walking-only prediction for a nonzero route, where Θ is accumulated absolute heading change in radians. Its coefficients are simulation assumptions. Battery percentage is a bookkeeping model, not an estimate obtained from motor-current measurements. During execution, the declared case multiplier perturbs the motion-based battery ledger; this does not change the independently integrated mechanical-work measurement.

Terrain difficulty is computed from nine height samples over the footprint window. The components are slope from the gradient of mean sampled height, height range, height standard deviation and assumed semantic softness. Their normalized sum is multiplied by 0.25 and clipped to [0, 2]. The normalizers are 0.25 rad, 0.12 m and 0.04 m; softness is chosen from 0, 0.25, 0.60 and 1. Exposure H integrates this difficulty along the route using samples no farther apart than approximately 0.125 m. It is an exposure cost, not a calibrated safety probability.


## 4.2 Common preference and resource feasibility

[Equation 2]

All three methods use the same fixed composite preference Q in Equation (2). Smaller values are preferred among admitted routes. The denominators express chosen reference scales rather than learned importance weights. Although the implementation retains a bounded nondominated archive and uses multicriteria prefix labels, the reported solution is one preference-selected route. This is not an evaluation of an entire Pareto front, and no hypervolume or global Pareto-optimality claim is made.

[Equation 3]

[Equation 4]

A route is admitted only if it passes both limits in Equation (3) and the battery requirement in Equation (4). The return estimate uses a common minimum-modeled-energy reference route from the destination to the available stations, including required station waypoints. The multiplier 1.25 adds a 25% allowance to the nominal round trip, and 6 adds six percentage points of reserve. This is a conservative simulation rule, not a statistically calibrated chance constraint.

The return calculation does not jointly optimize charging stops during the outbound task. An infeasible trip remains rejected even if a different mission-level schedule could make it possible. Return estimates use a common reference heading rather than the method-specific arrival heading. The reserve does not establish a formal bound on this approximation.


## 4.3 Predicted and measured quantities

Positive mechanical actuator work is integrated at each physics substep by summing positive actuator force times actuator velocity over time. It is reported in joules for the simulated actuator model. It excludes electrical inefficiency, auxiliary power and unmodeled body assistance. A gait or route with lower modeled battery use need not have lower measured positive actuator work.

Destination time ends when the target waypoint is reached. Successful mission execution additionally requires return to a station, satisfaction of the destination deadline and minimum remaining battery of at least 2%. Terminal service adds eight modeled seconds and restores the ledger to 100%; it is not a charge-rate simulation. One charging event per completed mission is largely fixed by this design and is not an informative optimization outcome.


# 5 Compared planning algorithms

Figure 2 summarizes the three refiners. Their common initialization attempts energy-, time- and distance-oriented A* searches within 30% of the nominal total planning time. Duplicate seed routes are removed. Each unique corridor initializes an incumbent using its original route and safe greedy shortcuts. All seed search and refinement time is charged to the method; shared graph and return-route preparation are outside that timer. The common recipe does not guarantee identical initialization work on every machine because it has wall-time cutoffs.

Figure 2  Common initialization and distinct refinement mechanisms. Every returned route passes the same evaluator. The proposed method uses heading-aware resource labels in walking-only mode; its separate hybrid-mode beam fallback is outside the primary experiment. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_2_algorithms]


## 5.1 Particle swarm route refinement

PSO uses a vector of random keys in [0, 1] for internal corridor waypoints. Keys at least 0.5 request retention. Unsafe omissions are repaired by inserting safe forward nodes from the original corridor. Position and velocity updates use inertia, a personal-best term and a swarm-best term [3]. The initial population includes the original and aggressively shortened selections. Feasibility is ranked before normalized constraint violation and the common score; infeasible routes cannot be reported as successful merely because they are short.


## Algorithm 1 PSO hybrid

01 Input common corridors, paired seed, limits and remaining wall time.

02 For each corridor, create random-key particles and bounded velocities.

03 Include original-route and aggressive-shortcut key vectors.

04 Decode each particle into a collision-checked waypoint subsequence.

05 Repair unsafe skips with forward corridor nodes.

06 Evaluate the route; update personal and global best ranks.

07 Update velocity from inertia, personal best and global best.

08 Clip velocity to ±0.25 and position keys to [0, 1].

09 Repeat up to 40 iterations per corridor, subject to time and caps.

10 Return the best feasibility-ranked candidate and observed diagnostics.


## 5.2 Ant colony route refinement

ACO constructs routes on a forward visibility graph of corridor waypoints. Transition probabilities are proportional to pheromone raised to alpha and a progress heuristic raised to beta. The heuristic divides forward index progress by the visible chord length plus remaining straight-line distance. Pheromones evaporate after each generation, and generation routes plus the retained incumbent deposit reinforcement. Constraint violation penalizes deposits. This is an implementation-specific elitist Ant-System-style adaptation [4], not an exact reproduction of the original Ant Colony System variant.


## Algorithm 2 ACO hybrid

01 Input common corridors, paired seed, limits and remaining wall time.

02 Initialize pheromones on possible forward edges.

03 For each ant, begin at the start waypoint.

04 List forward nodes with collision-checked visible connections.

05 Sample the next node using pheromone and progress heuristic.

06 Continue until the destination or construction termination.

07 Evaluate complete routes with the common feasibility-first rank.

08 Evaporate pheromones and reinforce generation plus incumbent paths.

09 Clamp pheromones to [0.0001, 10].

10 Repeat up to 40 generations per corridor, subject to time and caps.

11 Return the best feasibility-ranked candidate and observed diagnostics.


## 5.3 Proposed bounded Pareto label refinement

The proposed walking-mode refiner searches the same forward visibility corridors using labels for partial routes. A label records the previous and current waypoint, accumulated distance, time, battery cost and exposure, and a parent link. The previous waypoint preserves incoming heading for turn accounting. Segment costs are cached, and a single global start/stop allowance is retained rather than added at every chord.

A prefix is pruned when resource lower bounds already exceed the available task budget. A label dominated in all four accumulated quantities at the same heading state is also discarded. Remaining labels are prioritized using a lower bound on the common score. At most eight labels are retained per state in the selected configuration; labels with larger scalar scores are discarded when the cap is reached. Complete candidates are re-evaluated by the common whole-route evaluator before updating the incumbent.

This combines established multicriteria labeling ideas [5] with bounded corridor refinement. The cap, finite seed portfolio, heuristic pruning and wall-time termination make it approximate. There is no proof that its restricted solution is globally optimal or that it dominates PSO or ACO. In particular, advantages on accepted routes must be considered alongside the rejected and empty outcomes.


## Algorithm 3 Proposed walking-mode refiner

01 Input common corridors, limits, return energy and remaining wall time.

02 Initialize a label at the corridor start with one start/stop allowance.

03 Pop the active label with the smallest bound on common score.

04 For each forward waypoint, check continuous chord visibility.

05 Get cached segment costs and add incoming-heading turn costs.

06 Prune when resource lower bounds exceed the task limits.

07 Prune when the score bound cannot improve the feasible incumbent.

08 At the same heading state, remove dominated cost labels.

09 Keep at most eight labels per state; record parent links.

10 When the destination is reached, reconstruct and evaluate the route.

11 Update the feasibility-ranked incumbent and bounded archive.

12 Stop at time, expansion or candidate-evaluation limits.

13 Return the best candidate, limits and observed search diagnostics.


## 5.4 Parameter and computation controls

Table 1  Selected method parameters and development alternatives

Table 1  Selected method parameters and development alternatives
Method | Selected default | Alternative tested
PSO | 16 particles; inertia 0.72; cognitive/social 1.49/1.49 | 24 particles; inertia 0.55; cognitive/social 1.70/1.30
ACO | 12 ants; alpha 1; beta 2; evaporation 0.20 | 18 ants; alpha 1; beta 3; evaporation 0.35
Proposed | 8 labels per state; archive cap 16 | 12 labels per state; archive cap 16



PSO and ACO allow at most 40 iterations per corridor. The experiment limits whole-route fitness evaluations to 240 across a method’s corridors and uses a nominal expansion limit of 40,000 shared between seed search and resource labels. The A* seed-search timer is set to 0.6 s of the two-second nominal budget. Seed evaluation and initial greedy shortcuts also count toward the total method time. These are recorded controls rather than hard real-time guarantees. Segment-cost evaluations, visibility checks and full-route evaluations are different computational primitives; the 240-candidate cap does not imply equal primitive work for all methods.


# 6 Experimental protocol


## 6.1 Development and held-out construction

The experiment manifest fixes four development cases with seeds 71000–71003 and 12 held-out cases with seeds 92000–92011. Every case samples start and destination offsets within ±1.5 m around the base task endpoints and snaps them to free grid locations. A reference distance route locates a real movable roadwork obstacle between 30% and 70% of route length, with an additional ±1 m planar offset. Cases are retained after obstacle placement even when the declared search fails. There is no filtering for proposed-method wins.

The six existing destination regions are cycled. Deadline values of 110, 160 and 210 s, initial batteries of 70, 85 and 100%, exposure budgets of 15, 25 and 40, and execution battery multipliers of 0.90, 1.00 and 1.12 are assigned by fixed index cycles. These settings are coupled by construction rather than varied factorially. The experiment cannot isolate the causal effect of battery, deadline, region or multiplier. All cases share the original underlying terrain, robot, station network and most geometry; different obstacle positions do not create independent terrain worlds.

Table 2  Primary study phases and their denominators

Table 2  Primary study phases and their denominators
Phase | Design | Attempts | What is observed
Development | 4 cases × 2 profiles × 2 seeds × 3 methods | 48 | Planning and parameter selection
Held-out planning | 12 cases × 3 seeds × 3 methods | 108 | Route predictions and admission
Held-out physics | 4 preselected cases × 1 seed × 3 methods | 12 | 3 executions; 9 rejected plans



Both parameter profiles are evaluated for every method on the development cases. Selection first maximizes admission count, then minimizes the mean score of admitted routes; exact ties retain the default. All three methods retain their defaults. The selected settings and a parameter hash are written before held-out execution. This is parameter tuning, not neural-network training. Only one development layout produces accepted routes, so the search provides limited information for tuning.


## 6.2 Paired seeds and execution rules

Each method receives the same case and trial seed within a repetition. The trial seed is the case seed plus 100003 times the zero-based repetition index. A deterministic shuffle counterbalances method/repetition order within each case. Three repetitions primarily assess stochastic sensitivity; the proposed walking-mode label search does not use a stochastic population, and its repeated outcomes need not differ. Machine scheduling can still affect wall-time-limited search.

Physics cases are fixed in the manifest as heldout_02, heldout_03, heldout_05 and heldout_06, before inspecting evaluation outcomes. They are not selected retrospectively for success. The runner executes admitted plans only. Mechanical work covers the destination and return motion, while reported task time covers travel to the destination. Older pilot, smoke and gait-calibration records are excluded from the primary 168-attempt study rather than pooled into its sample sizes.


## 6.3 Analysis and uncertainty

Admission rate uses all planning attempts, including empty and rejected results. Mission success uses all physics attempts, including plans rejected before execution. Route-score averages condition on admission and are presented with their denominator. Paired score differences are computed only when both methods are admitted; the remaining outcomes are counted separately. A score tie has absolute difference no larger than 10 to the power of minus eight.

For each baseline, the difference is baseline score minus proposed score, so positive values favor the proposal. Repeated differences are first averaged within a layout. A descriptive percentile interval resamples these layout means with replacement 5,000 times using analysis seed 4100. Only three layouts contribute paired accepted scores. Such a small conditional bootstrap is not evidence of a general population effect, and no significance test or acceptance probability is reported. Statistical principles from comparisons across independent datasets [11] do not justify treating the nine paired trials here as nine independent terrain samples.

An independent analysis script recomputes the common score, resource decisions, summary denominators and paired comparisons directly from saved JSON. It verifies unique case-method-repetition keys and archived source hashes. Separate HTTP regression checks concern delivery of chart data, not scientific validity. Correct data delivery and an internally consistent record are necessary but do not establish a valid physical model.


# 7 Results


## 7.1 Acceptance and failure categories

All three methods admit nine of 36 held-out planning attempts, an admission rate of 25%. Each also returns 21 resource-rejected routes and six empty outcomes. Figure 3 shows the complete denominators. The identical admission rates are a measured tie. They should not be altered or hidden to create a visually stronger result.

Figure 3  Held-out planning outcomes for all attempts. The three categories are disjoint. Admission refers to predicted resource feasibility, not measured mission success; every method contributes 36 attempts. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_3_outcomes]

For each method, all 21 resource-rejected attempts exceed the battery-plus-return requirement; six of these also exceed the deadline. These overlapping limit counts must not be added as disjoint failures. No returned route is rejected solely for the terrain-exposure limit in this study. The six empty outcomes occur on two layouts and have timeout diagnostics during common seed initialization. They are not certificates that a collision-free or resource-feasible path does not exist.

Table 3  Held-out planning outcomes and conditional costs

Table 3  Held-out planning outcomes and conditional costs
Method | Accepted / 36 | Resource rejected | No route | Mean Q on 9 accepted | Mean planning s on 36
PSO | 9 (25%) | 21 | 6 | 2.798264 | 0.585
ACO | 9 (25%) | 21 | 6 | 2.796809 | 0.737
Proposed | 9 (25%) | 21 | 6 | 2.796744 | 0.517




## 7.2 Paired route quality

Against PSO, the proposed method has four lower common scores, five ties and no higher score among nine jointly admitted paired trials. Against ACO, it has three lower scores, six ties and no higher score. For both comparisons, neither method is admitted in the other 27 paired attempts. These counts show a small conditional score advantage, not a gain in task coverage.

Table 4  Paired common-score outcomes across 36 matched attempts

Table 4  Paired common-score outcomes across 36 matched attempts
Baseline | Proposed lower | Tie | Proposed higher | Neither admitted
PSO | 4 | 5 | 0 | 27
ACO | 3 | 6 | 0 | 27



Figure 4  Mean paired score differences on the three jointly accepted layouts. Both panels use the same horizontal scale, expressed in thousandths of a score unit. Layout 03 is an exact tie; improvements are small and concentrated in limited cases. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_4_paired_scores]

The mean layout-averaged score advantage is 0.00152021 against PSO and 0.00006509 against ACO. The descriptive 95% intervals are [0, 0.00384741] and [0, 0.00019528], respectively. Both include zero. Relative to the respective accepted-route mean scores, the differences are approximately 0.054% and 0.0023%. These percentages describe the chosen composite score only; they are not reductions in measured battery consumption, travel time or electrical energy.


## 7.3 Planning time and initialization bottlenecks

Mean method wall times are 0.585 s for PSO, 0.737 s for ACO and 0.517 s for the proposed method. These observations favor the proposal on this machine and implementation, but exclude shared preparation. Recorded return-route and lower-bound preparation averages 1.638 s per held-out case, ranging from 1.048 to 2.758 s. Model loading and graph construction precede that preparation timer and are also excluded. The method means therefore cannot support an end-to-end real-time claim.

Figure 5  Recorded planning wall time. Each dot averages three repetitions within a layout; black bars mark the overall means. The two-second line is a nominal method allowance. Shared preprocessing and model construction are excluded. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_5_runtime]

On the two empty-result layouts, the initial search consumes approximately its 0.6 s allocation and reports timeout; no corridor is available for any refiner. The remaining nominal time does not create an alternative route because the current design stops without successful initialization. Reallocating unused refinement time to seed generation is a plausible shared improvement to test on development cases. It is a future experiment, not an improvement demonstrated by the current data.


## 7.4 Route geometry and physics checks

Figure 6 shows the first two admitted layouts. The physics phase contains four preselected cases per method. Three cases per method are rejected before execution. Only heldout_03 executes, once for each method, and all three missions complete. Thus success is 1/4 per method when all scheduled physics attempts are counted, while conditional execution completion is 1/1 per method. Reporting only the latter would conceal the limited task coverage.

Figure 6  Recorded first-repetition destination routes for the first two admitted layouts. Gray regions are obstacle bounding boxes in plan view, not a complete rendered terrain map. The paths coincide on Layout 03 and nearly coincide on Layout 04; no artificial offsets are added. AI-assisted plotting code used the archived data or documented implementation.

[Figure: figure_6_routes]

Table 5  Measured quantities on the single executed held-out case

Table 5  Measured quantities on the single executed held-out case
Quantity | PSO | ACO | Proposed
Time to destination s | 72.848 | 72.848 | 72.848
Mission time including service s | 132.864 | 132.864 | 132.864
Positive actuator work including return J | 16385.631 | 16385.631 | 16385.631
Modeled mission battery use percentage points | 65.093 | 65.093 | 65.093
Maximum assisted tilt degrees | 0.157 | 0.157 | 0.157
Completed / scheduled attempts | 1 / 4 | 1 / 4 | 1 / 4



The three executed plans select identical waypoint sequences. Fresh deterministic physics executions therefore produce the same measured quantities, including destination time of 72.848 s and total positive actuator work of 16385.631 J. This is consistent with a shared route and controller, and gives no physical-performance advantage to the proposal. Recorded executions have no obstacle penetration, terrain-speed violation or solver-warning events; three assisted executions are insufficient to establish general safety.


# 8 Discussion


## 8.1 What the comparison establishes

The results establish that the software can preserve matched attempts, distinguish structural missing values from zeros, and expose ties rather than manufacture separation. They also show that a bounded label refiner can obtain slightly smaller common scores on some admitted corridors. The strongest negative result is that changing the refiner does not improve admission in the tested setting: the common seed stage and destination-plus-return resource model dominate much of the outcome.

The proposed method is better described as a resource-aware implementation under a restricted representation than as a universally superior optimizer. PSO and ACO explore subsequences of seeded corridors, not arbitrary collision-free paths. Requiring a safe initializer benefits all methods but can reduce population diversity and hide differences that would appear in broader search spaces. A fair extension must give every method the same available movement and service actions.


## 8.2 Threats to validity

Internal validity is limited by heuristic coefficient choices, capped labels and the allocation of only 30% of time to seed generation. A common final evaluator reduces scoring inconsistencies, but does not validate its physical assumptions. Candidate counts also represent different work across algorithms because segment evaluations and population constructions differ. Source hashes support traceability, not correctness of every modeling assumption.

External validity is limited by one fixed terrain, sampled endpoint and obstacle changes, a small development set and only three layouts with paired accepted routes. Deadline, battery and goal region are coupled by index. In addition, the chosen physics subset yields one executed case. The study does not assess novel terrain families, localization error, perception noise, dynamic obstacles, payload changes, actuator degradation or unassisted hardware locomotion.

Construct validity is limited by the distance/time battery ledger, externally assisted motion and geometric exposure proxy. Positive actuator work omits external assistance and electrical losses. Small assisted tilt is not a fall-risk estimate. Terminal charge counts are mostly predetermined. These boundaries prevent interpreting a lower common score as a validated safety or electrical-efficiency gain.

The descriptive uncertainty interval is especially weak because it conditions on jointly admitted routes and resamples only three layout means. It does not quantify uncertainty in admission across independent terrain worlds. Further method development informed by these results also means these inspected cases should no longer be treated as pristine confirmation data for the revised algorithm.


## 8.3 Evidence needed for a stronger study

A stronger evaluation should first state a specific methodological advance beyond known labeling and swarm ideas. Development experiments should address seed timeouts and calibrate battery/return assumptions. New experiments should include distance and energy A*, greedy shortcutting, denser weighted sampling, and an exact constrained reference on small graphs. Component-removal comparisons should isolate portfolio seeding, heading labels, resource pruning and label caps.

Next, independently generated terrain families should be split before tuning, with enough feasible and challenging cases to support both conditional cost and all-attempt outcome analysis. A larger predeclared sample should be justified by a meaningful effect and pilot variability rather than an arbitrary record count. Execution validation should use calibrated energy accounting and reduced assistance or hardware trials when making locomotion claims. None of these additions is represented as already completed in the present results.


# 9 Conclusion

This study presents a traceable simulation framework for comparing PSO, ACO and bounded Pareto resource-label refinement on hexapod body routes. The primary evidence comprises 48 development attempts, 108 held-out planning attempts and 12 physics attempts. All methods admit 25% of held-out planning attempts. Conditional common-score improvements for the proposal are small, and the single executed case per method produces identical measurements. Shared initialization timeouts and return-energy requirements are more prominent limitations than the choice of refiner. The study supports transparent preliminary benchmarking, while broader novelty, independent terrain evaluation and stronger physical validation remain necessary for general performance claims.


# Statements and declarations

Funding  [Authors must provide the actual funding statement.]

Competing interests  [Authors must disclose actual competing interests or confirm their absence.]

Author contributions  [Complete actual contributions and author agreement using the selected journal’s requirements.]

Ethics  The reported experiments concern a simulated robot; no human-participant or live-animal experiment is reported.

Data and code availability  The study retains raw JSON, flat CSV, scenario manifests, selected parameters, source hashes and source snapshots. The accompanying local evidence package supports inspection and reanalysis. A public repository identifier and redistribution licenses for all model assets have not yet been established.

AI assistance  OpenAI Codex assisted software development, evidence analysis, manuscript preparation and code-generated figures on 28 October 2026. The named human authors must verify the methods, results, references and final text, confirm responsibility, and complete the target journal’s disclosure before submission. No AI system is listed as an author.


# References

[1] E. Todorov, T. Erez and Y. Tassa. MuJoCo: A physics engine for model-based control. Proceedings of the IEEE/RSJ International Conference on Intelligent Robots and Systems, 5026–5033 (2012).

[2] P. E. Hart, N. J. Nilsson and B. Raphael. A formal basis for the heuristic determination of minimum cost paths. IEEE Transactions on Systems Science and Cybernetics 4(2), 100–107 (1968).

[3] J. Kennedy and R. Eberhart. Particle swarm optimization. Proceedings of ICNN 1995, volume 4, 1942–1948 (1995).

[4] M. Dorigo, V. Maniezzo and A. Colorni. Ant system: Optimization by a colony of cooperating agents. IEEE Transactions on Systems, Man, and Cybernetics, Part B 26(1), 29–41 (1996).

[5] E. Q. V. Martins. On a multicriteria shortest path problem. European Journal of Operational Research 16(2), 236–245 (1984).

[6] Y. Yin, F. Gao, Q. Sun, Y. Zhao and Y. Xiao. Smart Gait: A gait optimization framework for hexapod robots. Chinese Journal of Mechanical Engineering 37, article 15 (2024).

[7] C. Chen, J. Lin, B. You, J. Li and B. Gao. Hexapod robot motion planning investigation under the influence of multi-dimensional terrain features. Frontiers in Neurorobotics 19, article 1605938 (2025).

[8] S. Chen, Y. Chen, Z. Wei, Q. Nguyen and S. K. Gupta. Energy-Aware Planning for Delivery Tasks Executed by Legged Robots. Proceedings of IEEE CASE, 1617–1624 (2025). Publisher abstract and introduction consulted.

[9] Z. Yoon, L. Y. Zhu, J. Lu, L. Gan and Y. Zhao. STATE-NAV: Stability-Aware Traversability Estimation for Bipedal Navigation on Rough Terrain. arXiv 2506.01046v4, 5 December 2025.

[10] N. Hansen, A. Auger, R. Ros, O. Mersmann, T. Tušar and D. Brockhoff. COCO: A platform for comparing continuous optimizers in a black-box setting. Optimization Methods and Software 36(1), 114–144 (2021).

[11] J. Demšar. Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research 7, 1–30 (2006).


# Appendix A Reproduction and evidence scope

The primary evidence is in mujoco/outputs/research/reliability_v1. Development run identifiers are 20261028T013044676067Z and 20261028T013126915853Z; planning and physics identifiers are 20261028T013210063968Z and 20261028T013448551391Z. The manifest and parameter selection precede evaluation.

From the project’s mujoco directory, python3 -m research.reliability resumes saved phases. Completed phases are reused. A new execution can differ under machine-dependent wall-time cutoffs; archived source snapshots identify the original implementation.

Reanalyze with source/analyze_evidence.py --study evidence/reliability_v1 --out analysis. Python and NumPy are required; plots also need Matplotlib. The evidence package includes the original records, manifests and source snapshots. Simulation reruns additionally require the project meshes and dependencies, with redistribution permissions reviewed.

Table A1  Held-out cases and fixed resource profiles

Table A1  Held-out cases and fixed resource profiles
Case suffix | Seed | Start x y m | Goal x y m | Deadline s | Battery %
01 | 92000 | -1, -21.25 | -18.5, 17.5 | 110 | 70
02 | 92001 | -1.25, -20.25 | 18.5, 16.5 | 160 | 85
03 | 92002 | -0.75, -20 | -18.5, -10.5 | 210 | 100
04 | 92003 | 0.5, -20 | 17, -8.75 | 110 | 70
05 | 92004 | -1, -21.5 | -34.5, -20.75 | 160 | 85
06 | 92005 | 1, -21 | 35.25, 20.5 | 210 | 100
07 | 92006 | 0.5, -19.25 | -17.5, 15 | 110 | 70
08 | 92007 | 0.75, -19.25 | 18.25, 16.5 | 160 | 85
09 | 92008 | 0, -18.75 | -17.25, -8.75 | 210 | 100
10 | 92009 | -1.5, -19.25 | 19, -10.75 | 110 | 70
11 | 92010 | 1.25, -20.75 | -34.75, -19.5 | 160 | 85
12 | 92011 | 1.25, -20.25 | 36.25, 20.75 | 210 | 100



The manifest retains exposure limits, execution multipliers, obstacle positions, return routes and all 108 planning records. These represent 12 layouts, three methods and three seeds, not 108 independent maps.