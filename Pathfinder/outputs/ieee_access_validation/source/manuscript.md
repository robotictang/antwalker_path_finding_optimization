# Resource Constrained Hexapod Path Planning With Visibility Search and Continuous Waypoint Refinement

@ABSTRACT
Hexapod route planning must balance distance, destination time, battery capacity, and terrain difficulty under a finite computational allowance. This article presents a resource constrained planner combining a safe corridor solution, visibility search, and continuous waypoint refinement. A shared evaluator ranks feasibility before a fixed balanced score. An initial frozen campaign contains 1,232 attempts, with eight development worlds and 24 separate primary test worlds. The proposed V4 configuration admits 69 of 72 primary attempts versus 66 for each alternative. Its world averaged balanced-score gains are approximately 2.07% over seeded particle swarm and ant colony optimization, falling below 1% against controls with identical waypoint polishing. A prospective extension adds 800 attempts and 48 untouched test worlds. Each of four competitive configurations receives the same two-profile development opportunity before settings are frozen. On fresh primary tests, V4 and an adaptive V5 candidate each admit 94 of 96 attempts, versus 92 for each polished swarm control. Their paired score advantages over these controls are approximately 1.42% and 1.41%. V5 returns identical saved route coordinates to V4 in all 96 matched attempts and does not improve mean planning time. Feature removal, shorter budgets, candidate ceilings, and reduced-assistance execution retain unfavorable outcomes. The evidence supports conditional simulation gains and the importance of strong representation controls, while rejecting a superiority claim for the adaptive extension. Electrical battery savings, unassisted locomotion, and hardware transfer remain unverified.

@KEYWORDS
Ant colony optimization, hexapod robots, motion planning, multiobjective optimization, particle swarm optimization, reproducible simulation.

## I Introduction
A six legged robot can take a short route that is undesirable for its mission. Turns consume time, rough terrain lowers commanded speed, and reaching a destination with insufficient energy to return to a service station can invalidate an otherwise collision free path. These issues motivate evaluating route geometry together with operational constraints. Physics simulation provides a controlled setting for such comparisons, although simulator validity and controller assistance limit the conclusions that can be transferred to hardware [@mujoco].

The planning problem considered here is a planar body route for a walking hexapod in a known static map. Terrain semantics and geometry are supplied to all methods. A fixed locomotion controller executes admitted routes. The study does not learn a perception system, predict footholds, or optimize gait parameters during the planning comparison. The distinction matters because advances in gait optimization [@smartgait] and terrain based foot placement [@terrain] address different parts of the locomotion pipeline.

Graph search, particle swarm optimization, and ant colony optimization offer different ways to construct or refine routes [@astar], [@pso], [@aco]. However, a method comparison can conflate the search rule with the route representation. If every optimizer can only select a subsequence of the same initial waypoints, multiple methods may return exactly the same path. Such ties can reflect a shared representation boundary rather than an erroneous dataset. Conversely, allowing one method to move waypoints freely while restricting its competitors to a fixed corridor can exaggerate the apparent contribution of its search mechanism.

This article investigates whether adding a bounded geometric diversification stage and continuous waypoint movement improves a resource aware route refiner under a common computational limit. The proposed implementation, referred to as V4 to distinguish archived software generations, starts from a safe corridor solution, explores selected obstacle and terrain landmarks, and polishes internal waypoints. It uses a fixed distance, time, nominal battery, and terrain preference. The score and admission rules remain identical across the methods being compared.

The contributions are threefold. First, the planner integrates heading aware route costs, a shared return energy allowance, incumbent preservation, a small visibility roadmap, and collision checked waypoint refinement within one nominal time allowance. Second, the experimental design separates parameter selection from held-out evaluation and includes polished swarm controls to examine the effect of a more flexible representation. Third, an inspectable evidence pipeline preserves every attempted plan, including rejected plans and ties, and links quantitative comparisons to saved route coordinates and source hashes [@evidence]. These are implementation and evaluation contributions; visibility graphs and path simplification are established ideas, and no new general optimality theorem is asserted.

The primary evaluation contains 864 planning attempts on 24 fresh worlds. It is complemented by development, feature removal, shorter budget, and assisted physics phases. The main outcome is a conditional score advantage over the original swarm baselines, accompanied by substantially smaller gains against polished controls and higher average planning time than several simpler methods. The limited benefit of landmark diversification in one ablation subset is reported alongside the more consistent benefit of polishing. AI assisted drafting, software work, and figure preparation are identified in the Acknowledgment [@codex].

A prospective extension additionally evaluates an adaptive search candidate, V5, against V4 and independently tuned polished swarm controls on 48 untouched worlds. Its 800 scheduled attempts cover primary planning, feature removal, budget and candidate-cap sensitivity, and two controller-assistance settings. This extension tests whether an apparently more elaborate planner adds value; unsuccessful enhancements are retained rather than promoted as improvements [@evidence].

## II Related Work
### A Graph Search and Multiple Resource Criteria
A* uses a path cost and heuristic estimate to guide graph search [@astar]. Its familiar guarantees depend on the graph, cost model, heuristic conditions, and termination rule. A shortest path on a finite occupancy grid is not automatically the best continuous body route, particularly when turning costs and terrain dependent travel times are included. Here, heading is retained in search states, and every returned route is reevaluated with the same geometric and resource model.

Multicriteria shortest path methods retain alternatives that cannot be improved in every objective simultaneously [@martins]. This principle motivates the corridor refiner used to initialize V4. The implementation limits labels and archive size to bound computation. It is therefore an approximation and does not enumerate the complete Pareto set. The final selection is made with a declared weighted score after feasibility checks. No hypervolume, Pareto coverage, or globally optimal trade-off result is claimed.

### B Swarm Optimization and Representation Controls
Particle swarm optimization updates candidate positions using individual and collective search information [@pso]. Ant system methods construct solutions probabilistically and reinforce useful decisions through pheromone updates [@aco]. In this project, both are implemented as safe A* seeded waypoint refiners. Particle positions encode inclusion of existing corridor vertices, while ants select forward visible connections. These implementations provide controlled baselines, rather than exact reproductions of every published robot planner based on the same algorithm families.

For particle swarm optimization, each random key is clipped to [0, 1], and keys of at least 0.5 retain the corresponding internal corridor waypoint. Initial particles include the all-retained and all-omitted choices. Unsafe omissions are repaired with forward visible connections from the original safe corridor. Personal and global bests use the same feasibility-first rank as V4. For ants, candidate successors are forward visible corridor nodes; selection is proportional to pheromone raised to α and a geometric progress heuristic raised to β. The heuristic divides forward index progress by the current connection length plus remaining straight-line distance. Deposits penalize rejected candidates using the same violation rank, and pheromone is clipped to [0.0001, 10].

The original swarm methods share an evaluator, initialization recipe, and geometric repair mechanism. This strengthens comparability but also induces common routes. To isolate part of the representation effect, two additional controls receive the same continuous polishing operator used by V4. They retain their development selected swarm settings and do not receive a separate tuning campaign. Their role is to test whether V4 improves beyond an inexpensive extension of the original baseline, rather than only beyond a restricted subsequence representation.

### C Visibility Search and Path Refinement
Planning through transformed obstacle geometry and visible connections has a long history [@visibility]. Path simplification also includes established operations such as removing vertices and attempting collision free shortcuts. The Open Motion Planning Library provides these operations and broader anytime path shortening facilities [@simplifier], [@anytime]. V4 uses a project specific implementation of related ideas with the present terrain and energy evaluator; it does not reproduce these library planners or establish a new geometric planning principle.

The relevant design question is how to allocate a finite allowance between improving an existing route and exploring alternative connections. A landmark stage can escape an initial waypoint subsequence, but consumes time that could otherwise be spent polishing that subsequence. The comparison with polished swarm methods and the no-landmark ablation therefore form essential parts of the evaluation. Sampling based optimal motion planning provides another important family of alternatives [@rrtstar], but is outside the implemented baseline set. Conclusions are restricted accordingly.

### D Legged Robot Terrain and Energy Studies
Smart Gait optimizes locomotion variables for a hexapod, including trajectory, timing, and gait sequence components [@smartgait]. The present comparison keeps the gait fixed and evaluates body routes. Chen et al. combine multidimensional terrain features with hexapod planning [@terrain]. Their work motivates separating terrain related costs from geometric distance; the present terrain proxy and robot thresholds are project specific rather than a reproduction of their full perception and foothold planning system.

Energy aware delivery planning considers resource use together with service actions and task completion [@delivery]. Only the publisher abstract and introduction of that paper were available for the present review; its complete optimization formulation is not claimed to have been implemented. STATE-NAV estimates stability related traversability for bipedal navigation and includes physical validation [@state]. Our geometric and semantic exposure score is not a learned instability probability, and assisted body tilt is not equivalent to unassisted stability.

### E Experimental Comparability
The COCO benchmarking framework emphasizes explicit initialization, termination, and computational accounting [@coco], [@cocoprocedure]. The present study follows these principles in spirit without using the COCO benchmark suite. Search time, candidate evaluations, and visibility queries are recorded separately because these operations have different meanings. Statistical comparisons across multiple datasets also motivate treating the world, rather than each repeated seed, as the independent unit [@demsar]. The reported intervals are descriptive whole-world bootstrap intervals, not a multiple-comparison corrected test of universal superiority. Preparation assistance for this synthesis is disclosed in [@codex].

## III Problem Formulation and Simulation Framework
### A Route and Task Definition
Let a route be an ordered sequence of planar body waypoints from a fixed start to a destination. The robot starts at the same heading in every paired trial. A known map defines obstacles and terrain patches. For each task, the planner receives a destination deadline, available battery percentage, and terrain exposure limit. These inputs are fixed across methods. The formal description and implementation values below follow the archived research source [@evidence]; preparation assistance is disclosed in [@codex].

[[EQ:route]]

Here, n is the waypoint count, p_s and p_g are the supplied start and goal, and intermediate points may be changed by a method only within its stated representation. The common continuous segment clearance query accounts for the robot footprint and tracking margin against obstacle rectangles. The shared grid has 0.25 m spacing and eight motion directions. Diagonal transitions cannot pass through blocked corners. A planner collision check concerns planar body clearance; it does not certify six-foot support or dynamic balance.

[[TABLE:notation]]

### B Common Route Metrics
For a candidate route, the evaluator computes distance D, predicted destination time T, nominal battery use E, and terrain exposure H. Segment integration is split at known terrain boundaries before travel time is evaluated. The walking speed ceiling is 0.75 m/s, falling to 0.65 m/s on grade-one terrain and 0.38 m/s on grade-two terrain. Initial yaw is π/2 rad. Turning is charged at 1 rad/s, and the single start/stop time allowance is 0.6 s.

[[EQ:distance]]

[[EQ:time]]

In (3), l_j and v_j denote the length and commanded speed of each terrain-split segment, while Θ is the sum of absolute wrapped heading changes, including the change from initial yaw. This is a planning approximation. The execution controller accelerates, turns, and accepts waypoints using a finite tolerance, so measured destination time need not equal T.

[[EQ:energy]]

All battery terms are percentage points of a nominal capacity. The coefficients in (4) are simulation assumptions: 0.70 percentage points/m of walking, 0.015 percentage points/s of hotel load, 0.08 percentage points/rad of turning, and 0.10 percentage points per nonzero route for start/stop. The electrical capacity, motor efficiency map, and battery discharge dynamics are not calibrated. Thus E is a modeled resource ledger, not a measured electrical quantity.

The local terrain difficulty combines footprint-scale slope, height range, height variation, and an assigned softness term. Slope and height statistics come from a three by three footprint sampling stencil. Softness values are semantic assignments, not measured deformability. The implemented difficulty is clipped to [0, 2]. Exposure H numerically integrates this difficulty along the route using samples no farther apart than half a grid cell. Low exposure therefore means low modeled terrain difficulty, not a guaranteed lower fall probability.

[[EQ:difficulty]]

In (5), s(x) is footprint slope in radians, r(x) is footprint height range in meters, u(x) is the standard deviation of sampled heights in meters, and z(x) is the assigned semantic softness. The denominators are fixed normalization scales.

### C Balanced Preference and Admission
Every candidate is scored with the same fixed preference. The denominators normalize the four components; they are chosen scales rather than estimates learned from test outcomes. The terrain contribution has coefficient 0.25. This scalar preference expresses one selected compromise among multiple objectives and does not make the component metrics interchangeable.

[[EQ:score]]

A return route from the destination to a service station is prepared once per case using the common energy reference search. Among available station choices, the reference with the lowest modeled energy is used by every method. Return preparation uses the same reference heading rather than each candidate's final heading, which is a simplification. The reserve and uncertainty factor are fixed across methods.

[[EQ:admission]]

Here, E_ret is the common return allowance, B_0 is available battery percentage, T_max is the destination deadline, and H_max is the terrain exposure budget. Admission requires all conditions in (7), along with a valid route and clearance checks. If no candidate satisfies the limits, the best rejected candidate can still be retained for diagnosis; it is never counted as an accepted or executed mission.

The optimization rank is lexicographic. Feasibility is preferred first, then the sum of normalized positive violations, and then Q. A rejected route with a small Q does not outrank an admitted route. The numerical feasibility tolerance is 10⁻⁸ in the corresponding resource units, and paired score ties use an absolute Q tolerance of 10⁻⁸. These conventions are fixed before held-out testing.

[[EQ:rank]]

In (8), I_invalid is one for a route that violates a resource limit and zero otherwise. For resource k, g_k is the predicted value minus its limit, b_k is that positive resource budget, and ε is the numerical feasibility tolerance. The tuple is minimized lexicographically.

### D Simulation and Evidence Architecture
Each procedural specification supplies obstacles, shallow terrain tiles, semantic terrain patches, friction scaling, and service-station positions. The same specification is used to create the physical scene and planner terrain queries. This prevents a method from being evaluated on an invisible cost map unrelated to the displayed world. The map remains fully known; perception uncertainty and online map construction are not modeled.

MuJoCo 3.9.0 supplies articulated contact simulation [@mujoco], [@mujocodocs]. The controller follows a supplied body route with a fixed tripod gait. Its 0.016 s control interval comprises four 0.004 s physics steps. All admitted physics trials also follow the prepared return route. Station service is modeled as 8 s of downtime with a battery reset; the work does not demonstrate a physical charging or replacement mechanism.

[[FIG:tomat1]]

The execution code directly assists horizontal body velocity, yaw rate, body height, roll, and pitch, and the model uses gravity compensation. These interventions make the environment suitable for controlled route comparison but limit locomotion realism. Positive actuator work is sampled at physics substeps. It excludes the unmodeled energetic cost of prescribed body assistance, so it cannot be identified with total robot energy or electrical battery consumption.

[[EQ:work]]

In (9), f_a and v_a are an actuator's force and actuator velocity, and Δt is the physics timestep. Work is summed over the complete executed outbound-and-return motion. The saved destination time stops at the task waypoint, so its scope differs from mission work. These scopes are retained in all tables and captions.

## IV Proposed Visibility and Continuous Refinement Method
### A Incumbent Initialization
V4 starts with the earlier corridor Pareto refiner using its fixed default configuration. The initial search is allocated at most 40% of the total planning allowance B. Within that stage, a shared adaptive A* recipe supplies one or more safe seed corridors. An unfinished energy search can be resumed rather than restarted, with a distance-search fallback when needed. Search, visibility checking, and route evaluation time remain inside the same allowance [@evidence]. The algorithm descriptions and pseudocode were prepared with the assistance disclosed in [@codex].

The corridor refiner retains alternatives with different heading and resource histories, subject to label and archive caps. V4 receives the best evaluated route from this stage, not another algorithm's saved experimental result. The seed's whole-route evaluation count is carried into the subsequent candidate counter. A valid incumbent is preserved even if the initial stage has used the remaining time or candidate allowance.

### B Feasibility Ranked Candidate Pool
The candidate pool stores route geometry, common metrics, and the lexicographic rank in (8). A cache avoids repeated evaluation of equivalent waypoint sequences using coordinates rounded to seven decimals as a cache key. Saved route coordinates and the final metrics retain their original numerical precision. Each new whole-route evaluation increments the shared count; known incumbent metrics can be registered after time expiration so that an existing route is not lost.

The pool never accepts an improvement solely because a route is shorter. A proposed change must have valid segments and improve the declared rank. Consequently, a change may exchange slightly higher terrain exposure for lower time and energy while improving Q. This is a consequence of the fixed preference, rather than evidence that all four metrics improve together.

### C Geometry Based Landmark Diversification
A direct start-to-goal connection is tried first under the exact common clearance query. Additional nodes are drawn from intermediate seed vertices, inflated obstacle corners, and corners outside known terrain patch boundaries. Obstacle-corner padding includes footprint radius, tracking margin, and a fixed 0.06 m offset. Terrain candidates use a fixed 1.22 m offset from patch bounds. Invalid, duplicate, or out-of-map nodes are discarded.

The endpoints remain fixed. Other landmarks are ranked by the sum of their Euclidean distances to start and goal, and the default configuration retains no more than 44 total nodes. This ranking depends on geometry rather than test outcomes or routes returned by competitors. It is deliberately simple and can discard useful distant alternatives; it offers no global completeness guarantee.

A visibility graph attempts collision free connections between nodes. Pairs incident to endpoints are prioritized, followed by short connections. The roadmap stage receives up to 32% of B after it begins; 60% of that stage's remaining time is used for constructing connections and the remainder for searching. This is a maximum allowance, not a requirement to consume the entire budget. Expiration and other shared limits can stop a stage earlier.

Search states retain the incoming and current node so that turning costs can be added consistently. Single-route start/stop overhead is removed from per-edge costs and applied once by final route evaluation. Three scalar searches emphasize the balanced preference, travel time, and nominal energy. Candidate routes are always ranked with (8), regardless of which internal search produced them. Reverse segment reuse is used only for the walking formulation implemented here.

### D Continuous Waypoint Polishing
The polishing stage operates on the current best route. It first attempts deleting an internal vertex. If deletion does not improve the rank, it tries moving that vertex toward its projection on the neighboring chord, to the neighbors' midpoint, and along eight planar directions. Diagonal directions have unit length, preventing a larger displacement merely because both coordinates change.

The default movement scales are 0.75, 0.25, and 0.08 m, with at most three passes per scale. The start and goal never move. Every proposed route is collision checked and reevaluated using the same time, energy, terrain, and return rules. Search stops when the wall allowance expires, the common candidate cap is reached, or no permitted improvement remains. It is a local refinement and can remain trapped in a suboptimal region.

[[FIG:tomat2]]

[[ALG:v4]]

### E Incumbent Preservation and Computational Scope
The candidate update rule gives a useful implementation invariant. Provided that the initial route is registered and evaluation is deterministic, the rank of the returned candidate cannot be worse than that registered route's rank. The reason is direct: a new candidate replaces the incumbent only if its rank is strictly smaller. Repeating this update preserves the ordering. The invariant concerns the registered seed only; it does not compare V4 with every baseline, establish global optimality, or guarantee a feasible route on every task.

With K landmarks, connection construction considers O(K²) pairs and stores at most O(K²) edges. Its cost also depends on obstacle checks and metric integration. Heading-aware search can visit O(K²) incoming/current states with O(K) potential successors each before the configured expansion limit. Polishing uses whole-route evaluations bounded by the shared cap of 240, including evaluations already used during initialization. Roadmap segment metric calls and visibility tests are separate primitives and are not disguised as identical whole-route fitness evaluations.

All internal stages count toward measured planner wall time. The common graph construction, terrain preparation, return reference search, and heuristic bounds are prepared once per case and excluded from per-method planning time. Their recorded average cost is reported separately. Equal upper limits therefore do not imply equal actual runtime or equal numbers of every low-level operation.

### F Swarm Methods With the Same Polishing Operator
The polished particle swarm and ant colony controls replace the V4 initial refiner with their corresponding development-selected swarm method. They receive the same initial-stage fraction, global candidate cap, polishing scales, and total wall allowance. They skip the new landmark roadmap, leaving more remaining time available for polishing. This is an intentionally competitive representation control, not an additional tuned algorithm search.

[[ALG:controls]]

The no-polishing V4 ablation retains the initialization and landmark stages. The no-landmark ablation retains initialization, the direct route test, and polishing. These variants share the selected V4 settings. Feature removal changes how the remaining allowance can be used, so an ablation is a test of the complete bounded configuration rather than an isolated causal effect under equal primitive operation counts.

## V Experimental Protocol
### A Frozen Development and Test Splits
The campaign manifest fixes eight development worlds and 24 held-out worlds, with disjoint seeds and world hashes. Each split cycles through open, clutter, rough, and corridor families, yielding two development and six test worlds per family. Development seeds span 1,240,000–1,240,007; held-out seeds span 1,350,000–1,350,023. These seeds also differ from the earlier archived study. Cases were generated before optimizer parameter selection [@evidence]. Drafting and experiment-implementation assistance are disclosed in [@codex].

Worlds occupy a 48 m by 48 m square. Obstacle placement, terrain patches, tile heights, and a friction multiplier vary within the prescribed generator. Sampled endpoints are snapped to safe grid locations. The initial candidate endpoint distance is selected within 12–26 m, with a final snapped separation of at least 10 m. Deadlines are drawn from {45, 70, 110, 160} s, available battery from {45, 65, 85, 100}%, and terrain budgets from {10, 20, 40}. These are generator settings, not a claim that the test distribution spans all real operating conditions.

A case-specific execution ledger multiplier is drawn from {0.85, 1.00, 1.20}. It perturbs modeled consumption during physics and is not used to tune a method's planning score. This controlled mismatch supports checking simulation prediction residuals, not validating a physical battery. The generator and every selected value are preserved in the manifest.

[[TABLE:protocol]]

### B Parameter Selection
Particle swarm optimization, ant colony optimization, the corridor Pareto refiner, and V4 each receive the same two-profile development opportunity. Each profile is evaluated on eight development worlds with two repetitions, giving 128 attempts across four tuned methods. Selection first maximizes the number of admitted development plans and then minimizes their mean Q. An exact tie retains the default profile. There is no neural-network training.

The selected particle swarm profile uses 24 particles, inertia 0.55, cognitive coefficient 1.70, social coefficient 1.30, and velocity clipping at 0.25. The default ant profile is selected, with 12 ants, exponents 1 and 2, evaporation 0.20, and unit deposit scale. The corridor refiner retains eight labels per heading state. V4 retains its default 0.40 initial-stage fraction, 0.32 roadmap fraction, 44 landmarks, and three polishing scales. No settings are changed after observing held-out performance.

[[TABLE:parameters]]

The polished controls inherit the corresponding selected swarm parameters and selected V4 polishing settings. They do not receive a third profile or additional development cases. The V4 initial corridor refiner uses the fixed default eight-label configuration. A* baselines and other fixed comparison methods are not independently tuned in this campaign. Equal two-profile opportunities for the tuned subset are not a claim of exhaustive or equal-cost tuning over all possible algorithms.

### C Baselines and Computational Limits
The 12 main configurations include distance A*, terrain A*, energy A*, sampled weighted search, energy-seeded greedy shortcutting, seeded particle swarm optimization, seeded ant colony optimization, an earlier grid Pareto planner, the corridor Pareto refiner, two polished swarm controls, and V4. They are related controlled implementations rather than 12 unrelated state-of-the-art published systems.

The weighted-search baseline tries seven declared distance, time, and energy weight patterns within its shared allowance, then selects using the common admission and Q rules. The terrain A* baseline uses its declared distance-plus-exposure search cost. The earlier grid Pareto method has its own bounded label logic. Every returned route is nevertheless evaluated by the same final route model. Differences therefore concern both search policy and candidate representation, which is why the polished controls are included.

Each primary attempt receives a nominal 2 s planning allowance, at most 40,000 search expansions, and, where applicable, 240 whole-route fitness evaluations. Wall-clock checks occur periodically and a final metric evaluation is completed atomically, so small timing overruns can occur. Swarm iteration caps are 40 per corridor, and lower-level search stops can end an attempt earlier. Methods are executed sequentially in a deterministically shuffled order within each world. All methods use the same trial seed for a given world and repetition, computed as the world seed plus 100,003 times the zero-based repetition index.

The recorded platform is an Intel Core i5-7600 at 3.50 GHz with four visible CPUs, Linux with glibc 2.35, Python 3.10.12, NumPy 2.2.6, SciPy 1.15.3, and MuJoCo 3.9.0. Times are wall-clock measurements on this machine, not portable algorithmic constants. Model loading and shared preparation are not charged to one method alone.

### D Paired Outcomes and Uncertainty
Every method has 72 primary attempts, formed by 24 worlds and three repetitions. Admission counts include all scheduled attempts. Paired score differences use only trials where both methods are admitted, with remaining pairs classified as proposal-only admission, baseline-only admission, or both rejected. A smaller Q is better. No rejected case is silently assigned a zero score or dropped from admission denominators.

[[EQ:relative]]

In (10), W_b is the set of worlds with jointly admitted comparisons against baseline b, and J_wb is the set of jointly admitted repetitions in world w. N_b is the number of worlds in W_b, n_wb is the number of repetitions in J_wb, and Q_bwj and Q_vwj are the corresponding baseline and V4 scores. Equation (10) first averages the percentage score difference across jointly admitted repetitions within a world and then averages those world values. It is not obtained by dividing overall admitted-only means, which can involve different worlds. For all 11 primary comparisons, 22 worlds supply 66 jointly admitted pairs. A further world yields only V4 admissions, and one world is rejected by every method.

Descriptive 95% percentile intervals use 5,000 bootstrap samples of whole-world means with random seed 6104. Repeated algorithm seeds are not treated as independent worlds. Admission intervals resample all 24 world-level admission differences. Intervals are uncorrected for 11 comparisons and are not presented as confirmatory significance tests. Absolute score wins can also be too small to have practical importance despite exceeding the numerical tie tolerance.

### E Secondary Phases and Evidence Checks
Feature removal uses the first eight preselected held-out worlds and three repetitions. Shorter-budget tests use the first four held-out worlds at 0.5 and 1.0 s, one repetition per method. Assisted physics uses the first six held-out worlds and one repetition. These subsets were declared in the manifest. They provide additional checks, not extra independent maps to add to the primary sample size.

The integrity audit checks unique trial keys, paired seeds, phase completeness, frozen parameters, model and source hashes, summary calculations, and resource limits. It reconstructs collision geometry for distinct saved routes and recomputes continuous metrics. The manuscript calculations independently recalculate paired counts, percentage improvements, and whole-world intervals from raw records rather than importing the experiment comparison helper. The website snapshot was checked against its served hash and the saved primary run. Graphical route views are displays of these same records, not independent experimental evidence.

## VI Results
### A Admission and Overall Route Quality
V4 admits 69 of 72 primary attempts, or 95.83%, while every other main configuration admits 66, or 91.67%. The difference is 4.17 percentage points. It arises from one additional world across three repetitions, rather than three independent new worlds. The descriptive admission-advantage interval is [0.00, 12.50] percentage points. All methods reject the same remaining world [@evidence]. Preparation assistance for the results presentation is disclosed in [@codex].

[[TABLE:main]]

The lowest overall admitted mean Q is 1.271323 for V4, compared with 1.295394 for particle swarm optimization and 1.295351 for ant colony optimization. These conditional means summarize different admission sets because V4 admits an additional task. They are included for transparency; the direct comparison uses the matched world-level percentage differences below. A higher admission rate should not be confused with measured mission completion.

[[TABLE:components]]

The component means show why a balanced score must be interpreted jointly. A method can reduce nominal battery use while admitting a more difficult task that raises its conditional mean time. The proposal is not lowest in every component against every control. The fixed preference represents the user's declared compromise, and a different preference could produce a different ranking.

### B Paired Comparison With Every Alternative
Against the original particle swarm and ant colony implementations, V4 has 51 lower scores, 15 ties, and no higher scores among 66 jointly admitted pairs. In addition, three pairs admit only V4, and three reject both methods. Mean world-level percentage improvements are 2.0710% and 2.0668%, with descriptive intervals [0.9071%, 3.5812%] and [0.9028%, 3.5718%], respectively.

[[FIG:tomat3]]

[[TABLE:paired]]

The stronger polished controls substantially narrow the advantage. V4 records 19 wins, 37 ties, and 10 losses against polished particle swarm optimization, with a mean improvement of 0.7323% and interval [0.0459%, 1.7659%]. Against polished ant colony optimization, it records 19 wins, 34 ties, and 13 losses, with mean improvement 0.6885% and interval [-0.0048%, 1.7291%]. The latter interval spans zero. Even the positive lower bound against polished particle swarm optimization is close to zero and unadjusted for multiple comparisons; broad superiority is not established.

[[FIG:tomat4]]

Compared with the fixed weighted-search baseline, the mean paired improvement is 6.7832%. Against the earlier corridor refiner, it is 2.0163%. These comparisons show a benefit of the complete V4 configuration within this suite, while the polished controls demonstrate that part of the gain comes from flexible waypoint refinement rather than the specific landmark stage alone.

### C Results in Individual Worlds
Across all 72 world/repetition experiments, V4 is uniquely best among admitted methods in 20, tied best in 35, and beaten in 14. All methods reject the remaining three. The same counts are retained in the downloadable every-experiment table. These are repeated algorithm outcomes on 24 worlds, not 72 independent maps. The distribution across the four terrain families is shown in Fig. 7.

[[WIDEFIG:tomat5]]

The first route example in Fig. 5 is heldout_24. V4 predicts 42.6216 s and meets the 45 s deadline. The particle swarm baseline predicts 92.3238 s and is rejected. Its modeled required battery is also above the task allowance. V4's new connections allow a route outside that baseline's retained corridor alternatives. This single world accounts for the additional three primary admissions and should not be represented as a general four-percentage-point improvement across arbitrary tasks.

The second example, heldout_02, shows an honest counterexample. Polished particle swarm optimization obtains Q = 1.07017690, while V4 obtains 1.07069249. Both are admitted, and the polished baseline is slightly better. These route examples were selected after evaluation to illustrate a feasibility gain and a loss; all global statistics use the complete frozen test set.

### D Computation and Feature Removal
Mean planning time is 0.4500 s for V4, compared with 0.2529 s for particle swarm optimization, 0.3668 s for ant colony optimization, and 0.1976 s for the corridor refiner. Thus the proposal uses more computation on average despite sharing the same 2 s upper allowance. The longest average belongs to the earlier grid Pareto method, at 1.5794 s. A lower score is not evidence of a faster planner. Across the 864 primary attempts, 39 recorded times exceed the nominal 2 s limit; the largest is 2.02315 s. No overrun exceeds the audit warning tolerance of 0.15 s. These measurements distinguish the nominal stop setting from an exact hard real-time guarantee.

Shared model loading, graph construction, return preparation, and heuristic preparation average 0.7796 s per held-out world. This cost is recorded once per case and amortized across methods and repetitions. Consequently, the per-method planning times should not be interpreted as full end-to-end deployment latency. Online mapping, perception, and communication costs are also absent.

[[TABLE:ablation]]

Removing polishing yields 18 V4 wins, three ties, and no losses among 21 jointly admitted pairs, with three pairs rejected by both. The mean improvement is 0.9322%, with interval [0.4379%, 1.4166%]. This supports the usefulness of polishing on the selected eight-world subset.

Removing landmarks yields three wins, 12 ties, and six losses, with mean improvement 0.0322% and interval [-0.0423%, 0.1525%]. The landmark stage therefore does not show a consistent advantage on this subset. The practical gain on heldout_24 lies outside the preselected ablation subset and cannot be used to rewrite that subset after observing results. A broader independent feature study is needed to establish when its time cost is justified.

### E Shorter Planning Budgets
All 12 methods admit all four selected worlds in each shorter-budget phase. V4's mean admitted Q is 1.072303 at both 0.5 and 1.0 s. At 0.5 s, polished particle swarm optimization obtains 1.072263 and polished ant colony optimization 1.071938; at 1.0 s, their respective means are 1.071897 and 1.071938. These small subsets show that V4 need not dominate the stronger controls when the search allowance changes.

[[TABLE:budgets]]

The unchanged V4 mean across these two phases is compatible with reaching a route or evaluation limit before the larger wall allowance is consumed. It does not prove that planning time is irrelevant in other cases. The study does not report a dense time-to-target curve or an exhaustive budget optimization.

### F Assisted Physics and Forecast Residuals
The six-world physics phase schedules 72 attempts. Each method admits and executes five missions; every executed mission reaches the destination within its deadline and completes the return with the required minimum modeled battery. The sixth world is rejected by all methods. Hence each method has five successful missions out of six scheduled attempts and five out of five executed missions. Mission success is tied, and the data do not support a success-rate advantage.

[[TABLE:physics]]

V4's mean destination time is 26.9312 s, compared with 27.2672 s for both original swarm methods. The polished controls are slightly faster, at 26.9248 s. V4 has the lowest mean positive actuator work, 7,388.7713 J, compared with 7,390.1517 J for polished particle swarm optimization and 7,393.0936 J for polished ant colony optimization. The 1.3804 J difference from polished particle swarm optimization is about 0.019% and should not be described as a substantial energy improvement.

[[FIG:tomat6]]

For V4, the mean destination-time prediction error, measured minus forecast, is -1.2363 s over five executions; mean absolute error is 1.2363 s and root mean squared error is 1.3307 s. These small-sample residuals indicate model mismatch rather than external calibration. Differences arise from the planning turn approximation, controller behavior, waypoint acceptance tolerance, and prescribed terrain speeds. The battery residual compares a nominal forecast with a perturbed simulation ledger and is not an electrical sensor validation.

[[FIG:tomat7]]

### G Audit and Traceability
The campaign audit passes all 1,232 recorded attempts without software errors or budget warnings. It separately collision-checks 189 distinct saved routes and recomputes 756 continuous metric values. The count of distinct routes is lower than the attempt count because multiple methods and repetitions can legitimately return the same path. Thirty automated correctness tests also pass, including incumbent retention, infeasible battery rejection, continuous refinement, and server behavior checks.

The primary run identifier is 20261029T003112961474Z and the physics run identifier is 20261029T004156752175Z. The evidence archive includes phase JSON and CSV records, source snapshots, scene XML, the frozen manifest, parameter choices, and audit results. These checks establish internal traceability. They do not establish simulator realism, an optimality certificate, or independent peer replication.

## VII Prospective Validation and an Adaptive Candidate
### A Frozen Extension Protocol
The extension is a separate prospective campaign, not a replacement for the original test records. Eight fresh development worlds use seeds 1,470,000-1,470,007; 48 fresh test worlds use 1,480,000-1,480,047. Each test family contains 12 worlds. Development, new test, and original V4 world hashes are disjoint. Map-generation and task-limit distributions are retained, so this is within-distribution replication rather than an out-of-distribution claim [@evidence]. Implementation, analysis and drafting assistance are disclosed in [@codex].

V4, polished PSO, polished ACO, and V5 each receive two complete parameter profiles on the same eight development worlds, with one repetition per profile. This gives 64 development attempts. Admission is maximized before admitted mean Q is minimized; exact ties retain the default. All four methods select the default profile. In contrast to the original study's inherited polished controls, each stronger control now selects its own complete swarm and polishing profile. The choices and scientific source hashes are saved before fresh evaluation. No setting is changed in response to fresh test outcomes.

[[TABLE:extprotocol]]

The primary phase has 48 worlds, two paired repetitions, four configurations and 384 attempts. The first 16 predeclared worlds supply feature tests and the 80-candidate sensitivity; the first eight supply 0.5 and 1 s tests; the first 12 supply two assistance conditions. Secondary phases reuse subsets and do not increase the independent test-world count. The campaign completes all 800 scheduled attempts. It is parameter selection and simulation evaluation, not neural-network training.

### B Adaptive Candidate and Feature Controls
V5 tests three changes to V4's bounded search. It evaluates a direct connection before initialization and can stop when a feasible direct route is within a small relative gap of an optimistic score. The bound uses straight-line distance, maximum walking speed, the single start/stop allowance, zero turning, and zero terrain exposure under the same nominal cost model. The default relative tolerance is 0.002. This is a model-specific stopping rule; it is not a theorem about the physical robot or unrestricted terrain models.

The default initial-stage fraction is 0.25 when a direct route is clear and 0.40 otherwise. The corresponding roadmap-stage fractions are 0.20 and 0.45, measured against the total allowance, and the candidate roadmap permits up to 52 valid nodes. A fourth internal search emphasizes terrain exposure. When the incumbent violates a resource constraint, the internal search targeting its largest normalized pressure runs first. Deadline pressure is predicted time divided by deadline; battery pressure is required battery including return reserve divided by available charge; terrain pressure is exposure divided by its limit. Final candidate ranking always uses the unchanged feasibility-first balanced objective.

[[ALG:v5]]

The fixed-allocation control disables direct-bound stopping and resource-prioritized search, restoring the selected V4 stage fractions while retaining the V5 node cap and direct-first ordering. It therefore tests this adaptation bundle, not every isolated decision separately. The other variants remove polishing or landmarks. All inherit the selected V5 settings, preserve endpoints and collision checking, and retain the best registered route at termination. These controls do not receive an extra test-informed tuning opportunity.

### C Fresh Primary Results and Uncertainty
V4 and V5 each admit 94/96 primary attempts; both polished controls admit 92/96. The additional admissions correspond to one world over two repetitions. Another world is rejected by all four configurations. Admitted-only means involve different populations, so the paired effects below remain the comparison basis.

[[TABLE:extmain]]

V5 and V4 return exactly the same saved waypoint coordinates in all 96 matched attempts, including the rejected pair. Their 94 jointly admitted score comparisons are therefore ties, with no evidence of a route-quality advantage for V5. Both methods have identical paired score effects against the polished controls. Relative to polished PSO the world averaged improvement is 1.418% (descriptive 95% interval [0.243, 3.441]%); relative to polished ACO it is 1.413% (descriptive 95% interval [0.232, 3.437]%). Joint admission supplies 46 worlds and 92 paired repetitions for each swarm contrast. The median world-level improvement is zero against both controls. The largest improvement is 41.114% in one world; excluding that largest effect as a post hoc diagnostic reduces the means to approximately 0.536% and 0.531%. The official complete-set effects retain that world. Thus the average gain does not describe a typical improvement on every map.

[[TABLE:extpaired]]

Intervals again use 5,000 whole-world bootstrap resamples after averaging paired repetitions. The analysis plan was saved after primary execution began but before inspection of held-out scores; it was not externally preregistered. It adds exploratory two-sided sign-flip tests of world-mean score differences, using 100,000 Monte Carlo sign assignments, seed 7421, a plus-one correction, and Holm adjustment over the three primary V5 contrasts. Adjusted p-values are 1.0000 against V4, <0.0001 against polished PSO, and 0.0002 against polished ACO. These tests assume sign exchangeability under the null and condition on joint admission. They are exploratory, not a guarantee of practical benefit, and they do not replace effect sizes or execution evidence.

[[FIG:ext1]]

### D Feature Removal and Budget Sensitivity
Against the fixed-allocation control, V5 records 0 wins, 32 ties, and 0 losses on jointly admitted pairs; its world averaged score difference is 0.000%. Against the no-polishing control, V5 records 28 wins, 4 ties, and 0 losses on jointly admitted pairs; its world averaged score difference is 1.073%. Against the no-landmark control, V5 records 16 wins, 14 ties, and 0 losses on jointly admitted pairs; its world averaged score difference is 3.378%. These counts cover the first 16 worlds with two repetitions, and the remaining admission categories stay in the archived records. An apparent component benefit is specific to this bounded implementation and subset; the fixed-allocation control removes several adaptation decisions together.

[[FIG:ext2]]

The shorter-budget comparison uses the same first eight worlds at 0.5 and 1 s with one repetition, alongside their two-repetition 2 s results. Figure 10 therefore compares a consistent map subset while disclosing the repetition difference. The candidate-ceiling phase separately uses 16 worlds, a 2 s allowance and at most 80 whole-route evaluations. Against V4, the 80-candidate phase gives 0.000% mean paired score improvement (0 wins, 16 ties, 0 losses). Against polished PSO, the 80-candidate phase gives 3.540% mean paired score improvement (9 wins, 5 ties, 1 losses). Against polished ACO, the 80-candidate phase gives 3.409% mean paired score improvement (8 wins, 6 ties, 1 losses). Neither sensitivity establishes dominance for every available budget.

[[FIG:ext5]]

### E Computation and Identical-Route Diagnosis
Mean planner time is 0.4704 s for V4 and 0.4932 s for V5, a 4.86% increase for V5 on this machine. Its direct-bound rule triggers 0 times in 96 primary attempts. The proposed enhancement therefore does not demonstrate an efficiency or quality gain over V4 on this fresh set. V4 remains the supported main configuration; V5 is retained as a negative enhancement result.

[[WIDEFIG:ext3]]

The new instrumentation counts all calls to the common continuous metric evaluator within each method's planner invocation, including roadmap edge calculations and final route reevaluation. It excludes shared preparation. Counts are distinct from whole-route fitness evaluations, visibility checks and search expansions; one metric call can itself integrate segments of different lengths. Thus the 80-candidate phase equalizes a ceiling, not actual evaluations or total computational work. Per-trial wall time and operation counts are supplied together.

Identical output geometry is checked directly from saved arrays, not inferred from rounded chart labels. Separate trial keys, timers and source records are retained for V4 and V5. Shared initial corridors and the same local polishing operator can converge to the same route, and the extra V5 exploration fails to change the incumbent here. These observations warrant a tie, not fabricated metric differences or an assertion that V5 is better.

### F Assistance Sensitivity and Physical Scope
At assistance 1, 46 of 48 scheduled attempts execute, with 42 successful missions. At assistance 0.5, 46 of 48 scheduled attempts execute, with 42 successful missions. Every method has 12 scheduled tasks per condition. The success denominator includes rejected plans; executed-only rates are a separate quantity. Table 13 reports each method and condition with conditional time/work means. Unexecuted attempts have unavailable physical metrics, not zero time or energy.

[[TABLE:extphysics]]

Assistance 1 reproduces the original commanded body-velocity and posture overwrite. Assistance 0.5 blends the current and commanded body velocities with equal weights at each relevant update; posture blending occurs at the control interval and horizontal/yaw blending at each physics substep. This is not a 50% reduction in force or external energy, and its repeated application can still impose substantial motion guidance. In both conditions, all four methods time out on v5test_02 before reaching the destination. The standard setting records approximately 0.904 m motion and 10,900 safety stops over 180 s, with zero recorded obstacle penetrations or solver warnings. The reduced setting records approximately 0.913 m and 10,898 safety stops. These records identify persistent safety stopping with minimal progress; they do not independently establish its physical cause. Static route admission therefore does not guarantee executable closed-loop progress. The controller and gravity compensation remain enabled. Even successful reduced-assistance trials do not validate unassisted locomotion. Mechanical actuator work still excludes the cost of body guidance; no electrical coefficient is fitted to these values.

[[FIG:ext4]]

### G Extension Integrity and Interpretation
The extension audit passes 800 unique scheduled records across nine phases, reconstructs 143 distinct saved routes, and recomputes 572 continuous metric values. It checks archived sources, models, world hashes, settings, paired seeds, candidate ceilings, score arithmetic, admission and execution success. Independent manuscript calculations reconcile all primary paired counts and percentages with the archived report. Thirty-seven distinct automated checks passed before the scientific source freeze; a final suite of 40 distinct checks also passes after the service-delivery changes. The original 1,232-attempt campaign remains unchanged.

This extension strengthens within-distribution evidence and baseline tuning fairness. It also rejects the expectation that a more elaborate search policy necessarily improves results. It does not address moving obstacles, uncertain perception, unrestricted continuous swarm representations, additional planner families, real electrical calibration, or hardware operation. Illustrative fresh-route panels and all world-level subgroup effects are supplied in Supplementary Evidence S2; complete-set results, rather than selected panels, control the conclusions.

## VIII Discussion and Limitations
### A What the Evidence Supports
The main result is that the complete V4 configuration finds better modeled balanced routes than the original seeded swarm implementations on the jointly admitted portion of this fixed test suite, while admitting one additional world. The relevant comparison is conditional and paired. A larger number of recorded attempts improves visibility into behavior, but the original primary generalization sample remains 24 generated worlds from a restricted distribution [@evidence]. Discussion drafting assistance is disclosed in [@codex].

The polished controls change the interpretation materially. Their smaller gaps and nonzero numbers of wins show that flexible waypoint movement explains an appreciable part of the improvement. V4 should therefore be presented as a bounded integrated planner with measured trade-offs, rather than as a universally superior replacement for particle swarm or ant colony optimization.

### B Contribution and Baseline Coverage
Visibility search, nondominated resource labels, and path polishing are established techniques. The contribution is their particular integration with heading-aware resource accounting, incumbent preservation, matched representation controls, and a reproducible hexapod comparison workflow. A stronger claim of algorithmic novelty would require a more exhaustive literature comparison and evidence separating the integrated design from existing planning and simplification methods.

The baseline suite covers several useful project implementations but does not include every strong motion planner. In particular, the study does not evaluate a full Open Motion Planning Library benchmark, asymptotically optimal sampling based planners [@rrtstar], a jointly tuned unrestricted continuous swarm planner, or a full multiobjective evolutionary method such as nondominated sorting genetic algorithm II [@nsgaii]. It also reports no Pareto-front quality indicator. Those missing comparisons limit claims about the wider planning literature.

### C Simulation and Energy Validity
Body velocity and posture assistance, gravity compensation, and fixed gait behavior limit physical realism. The planar clearance model does not represent all foot or body collision modes. Terrain stiffness and semantic softness are not calibrated deformable-ground properties. There is no perception error, unknown map, moving obstacle, actuator degradation, or sensor delay model in the primary planning test.

The battery model uses fixed percentage coefficients and a common return estimate. Physical electrical consumption depends on motor and driver efficiency, mechanical losses, payload, voltage, battery condition, and controller behavior, none of which are identified here from hardware measurements. Positive actuator work excludes the cost of body assistance and differs from electrical energy. Accordingly, no real-battery saving or autonomous locomotion stability claim follows from the measured work or exposure values.

### D Statistical and Computational Limits
The original campaign has 24 test worlds and five executed physics worlds per method. The extension adds 48 disjoint test worlds and two assistance conditions on a 12-world subset, but all remain within the same restricted generator. The shorter-budget and ablation subsets are smaller still. Repeated seeds can produce identical outputs on easy or strongly constrained worlds and must not be used to inflate the independent sample size. The original bootstrap intervals are descriptive, conditioned on paired admission for scores, and uncorrected for multiple comparisons. The extension adds exploratory Holm-adjusted tests for three primary contrasts; conditioning and modeling limitations remain.

The fixed balanced score encodes one operational preference. Alternative weights may change the method ranking, and equal normalized distance, time, and energy coefficients do not imply equal physical importance. The two-profile tuning search is modest. It cannot exclude a stronger baseline configuration or a different allocation between initial search, geometry diversification, and polishing.

Wall-clock budgets introduce machine and workload dependence. Common preparation time is outside the method timer, and low-level geometric operations differ across implementations. Runtime rankings therefore need replication under controlled workloads and on deployment hardware. Source and model paths in the evidence archive preserve the original machine's asset references; portability requires documented relocation in a separate copy rather than silently altering archived hashes.

### E Next Validation Priorities
The prospective extension supplies an additional independently planned evaluation and does not establish an advantage for the adaptive allocation candidate over V4. The next scientific priority is to identify a more effective diversification mechanism using new development maps, then freeze it before further test maps are generated. A broader comparison with existing continuous and sampling based planners would assess whether the integrated method adds value beyond generic postprocessing.

The reduced-assistance blending test is a sensitivity check, not an unassisted controller demonstration. For physical relevance, a dynamically actuated controller must be evaluated with direct body-velocity overwrites removed and all assistance energy explicitly accounted for. Electrical voltage/current logging and independent mission splits are needed to identify and validate a battery model. Real robot experiments would then test whether route ranking and resource admission remain useful under localization, contact, and actuation uncertainty. Electrical calibration, genuinely unassisted locomotion, and hardware operation remain future validation steps.

## IX Conclusion
This article presented a resource constrained hexapod planner combining a safe corridor initial route, geometry based visibility search, and continuous waypoint refinement. A frozen campaign separated development from 24-world primary testing and preserved 1,232 attempted plans across all phases. The common evaluator retained deadline, battery-return, and terrain checks before selecting a balanced score. The associated evidence and code are documented in [@evidence]; preparation assistance is disclosed in [@codex].

On jointly admitted routes, V4 improved the world averaged balanced score by approximately 2.07% over the original particle swarm and ant colony baselines. It admitted one additional world across three repetitions. The advantage fell below 1% when the same polishing operator was supplied to the swarm controls, and the relative interval against polished ant colony optimization included zero. Feature removal supported polishing more consistently than landmark diversification on the tested subset.

The original assisted physics phase produced equal completion counts across methods. V4 had a slightly lower mean mechanical work, while polished controls had a slightly lower mean destination time. The results support a limited simulation contribution with explicit trade-offs. The separate 800-attempt extension replicates conditional gains against individually tuned polished controls on 48 fresh worlds. However, its adaptive V5 candidate returns the same 96 routes as V4 with a higher mean planner time. The enhancement is therefore not promoted over V4. Broader baseline coverage, out-of-distribution worlds, unassisted control, and electrical calibration remain necessary before extending the claims to robust hardware operation.

## Data and Code Availability
The frozen V4 records are supplied as Supplementary Evidence S1. The prospective 800-attempt extension, its settings, source snapshots, model XML, audits, independent analysis, world-level effects, and reproduction instructions are supplied as Supplementary Evidence S2, identified in [@evidence]. The comparison dashboard is a visualization of these same records. No persistent public repository identifier has yet been assigned; an accessible archive location must be added before submission. The manuscript analysis script reproduces all tabulated primary comparisons directly from the saved JSON files. The original campaign has not been altered. S2 is a separately frozen parameter-selection and evaluation campaign, not a neural-network training result. Its relocation copy distinguishes path-only XML edits from the unchanged archived model and source hashes.

## Acknowledgment
OpenAI Codex was used to assist implementation and revision of the research software, experiment orchestration, data summarization, mathematical and algorithm descriptions, generation of plotting code, and drafting of the Abstract, Sections I–IX, figure captions, tables, and this manuscript [@codex]. The quantitative observations originate from the archived executable simulation records rather than generated example values. The author remains responsible for verifying the technical content, references, originality, disclosures, and final submission. Author approval and affiliation, funding, and conflict declarations are not inferred from the preparation of this draft.

## References
[[REFERENCES]]

## Author Biography
TOMATO. [Author to provide the full publication name if different, educational background, current affiliation and position, research interests, and any verified professional memberships. No credentials or IEEE membership have been assumed.]
