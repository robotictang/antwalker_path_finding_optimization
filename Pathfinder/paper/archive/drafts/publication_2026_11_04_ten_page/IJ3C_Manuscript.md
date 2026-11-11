# Waypoint Representation and Chassis Assistance in Simulated Hexapod Route Planning

[Author names and affiliations]
[Corresponding author email]

## Abstract

This study evaluates waypoint representation and component removal in resource-constrained route planning for a simulated hexapod. Six configurations share geometric clearance checks, mission limits and a distance, time, nominal battery and terrain score. A locally frozen campaign comprises eight development worlds and 32 primary worlds, yielding 640 planning records. The complete geometric refiner, V4, admits 93/96 primary attempts; a continuous-coordinate particle swarm control admits 94/96. On joint admissions, V4 has a mean world-level score improvement of 0.690%, a median of 0.000% and a descriptive 95% bootstrap interval of [-0.255, 2.312]%. The interval spans zero. Removing landmarks retains 93 admissions; removing polishing reduces admissions to 90. A separate diagnostic replays four archived missions under four assistance conditions. Full and reduced chassis assistance each complete all four missions; zero assistance times out on all four, both with compensation and after verified removal of limb gravity compensation. The findings quantify configuration-specific planning trade-offs and assistance dependence in the declared simulator. No physical robot performance or electrical energy saving is established.

Keywords: Hexapod; planning; optimization; simulation; reproducibility

## 1 Introduction

Resource-constrained navigation requires a route to satisfy operational limits as well as geometric clearance. In the model studied here, travel time depends on terrain-dependent walking speeds and heading changes, while route admission also requires a nominal battery allowance for travel to the destination and return to a charging station. Route length alone therefore does not determine admission or the configured route score.

This study evaluates an integrated geometric route refiner for a simulated hexapod in MuJoCo [1]. The refiner combines a resource-aware corridor incumbent, a bounded visibility search and continuous waypoint polishing. The comparison addresses two implementation questions: performance against a specified continuous-coordinate particle swarm control, and the effects of removing landmark search or polishing from the integrated refiner. All methods use a common map, cost evaluator, clearance query and mission limits.

The contribution is a controlled comparison of these configurations on a locally frozen development and primary-test protocol, together with a diagnostic of chassis assistance in the execution model. The primary outcome is route admission; route-score differences are evaluated on joint admissions. The diagnostic evaluates dependence of simulated completion on direct chassis control. The article reports planning and assisted-simulation outcomes; it does not report hardware measurements.

The experimental questions distinguish route feasibility, score quality and execution. First, does complete V4 admit more of the scheduled requests than the coordinate control under the same declared limits? Second, among mutually admitted requests, how large and consistent are the score differences across worlds? Third, which outcomes change when landmarks or polishing are removed? Finally, do the archived missions still complete when chassis velocity corrections are removed? Each question has a different denominator: scheduled planning attempts, jointly admitted worlds or the four replayed missions. Keeping these denominators explicit prevents a feasible geometric path from being interpreted as a demonstrated physical mission.

## 2 Related work

The initialization uses heuristic graph search in the tradition of A* [2]. Particle swarm optimization [3] and ant system [4] provide the search mechanisms underlying the swarm controls. The compared implementations differ in route representation: the existing controls select safe subsequences of seeded corridors, whereas the coordinate control moves internal vertices in the plane. Final collision checks and scalar evaluation are shared. Consequently, the comparison concerns the specified implementations and their representations, rather than an ordering of entire algorithm families.

Visibility-graph planning connects mutually visible points around modeled obstacles [5]. The integrated refiner uses this geometric construction with bounded landmarks, heading-dependent costs and local polishing. Its finite search budget and retained-label limits make it approximate; no global-optimality or complete Pareto-front claim is made.

Hexapod locomotion studies address additional variables. Yin et al. optimize swing trajectories, gait timing and gait sequence on the LittleStrong platform [6]. Chen et al. combine multidimensional terrain features with traversal costs, foothold costs and gait planning, with simulation and physical experiments [7]. The present study holds locomotion behavior fixed and supplies the terrain map. It evaluates body-route selection and assistance dependence, without reproducing those studies' gait adaptation or hardware validation. Explicit initialization, tuning and termination accounting follow the benchmarking concerns described by the COCO project [8].

## 3 Robot and route model

### 3.1 Robot assembly and execution assumptions

The source asset is named hexapod and is identified in its files as a Fusion 360 export. It has six legs and 18 revolute leg joints. The files do not identify a commercial product model. Source URDF comments identify RS04 actuators, and the joint limits specify 60 Nm effort and 20 rad/s velocity. These values are configuration inputs, rather than measured torque-speed characteristics.

Table 1 compares the source description with the compiled MuJoCo robot subtree. The source totals 97.52 kg with a 35 kg base; the simulation totals approximately 113.32 kg with a 46 kg base. The simulation includes procedural wheels and a scanner, with 23 actuators overall. Both the planning comparison and diagnostic replays use walking mode. The source and simulated assemblies are therefore distinct mass models.

Table 1. Declared source and simulation parameters.

| Parameter | Source URDF | MuJoCo assembly |
| --- | --- | --- |
| Total mass (kg) | 97.52 | 113.32 |
| Base mass (kg) | 35.00 | 46.00 |
| Leg joints | 18 | 18 |
| Added mechanisms | No wheel joints | Wheels and scanner |

The physics timestep is 0.004 s; the execution controller uses four substeps per 0.016 s frame. Gravity is 9.81 m/s squared, and 18 limb bodies have gravity compensation enabled. The controller directly blends chassis vertical velocity and roll/pitch rates once per frame, and horizontal velocity and yaw rate at each physics substep. At assistance 1, the horizontal velocity is replaced by the commanded velocity. At assistance 0.5, repeated blending is applied; this value does not specify a physical support force. Assistance 0 removes those direct velocity corrections, while limb gravity compensation remains active unless separately disabled.

The simulation supplies the robot pose and an obstacle/terrain description directly. There is no sensor reconstruction, localization estimate or map-learning stage in the primary planning comparison. The same supplied start, heading, goal and return estimate are used by each method. Route admission therefore evaluates decision making with the declared map and resource model; it does not measure navigation performance under perceptual error. Wheel and scanner mechanisms remain part of the compiled mass even though walking mode is selected.

### 3.2 Geometry and cost evaluation

A route P is an ordered sequence of planar chassis waypoints from the supplied start to the destination. The grid spacing is 0.25 m with eight motion directions and blocked-corner rejection. Every returned segment is checked against the common planar obstacle geometry using a configured 1.82 m clearance radius, 0.12 m tracking margin and 0.005 m segment-clearance tolerance. These parameters define the planning envelope; they are not a measured three-dimensional foot or body envelope.

The common evaluator returns distance D in metres, destination travel time T in seconds, nominal battery consumption E in percentage points and terrain exposure R. Travel time includes segment distance divided by the configured local walking speed, heading changes at 1 rad/s and an acceleration allowance. Smooth, mild and higher-grade speed caps are 0.75, 0.65 and 0.38 m/s. Terrain exposure sums segment length times mean grid difficulty sampled at spacing no greater than 0.125 m. The initial heading is π/2 radians for all trials. The balanced score is equation (1), where w = (1/50, 1/90, 1/30, 0.25/20).

$$Q(P)=D/50+T/90+E/30+R/80\qquad (1)$$

A route is admitted only if it meets its deadline, terrain-exposure budget and nominal battery constraint. Equation (2) defines the required battery allowance, where subscript return denotes the common destination-to-station estimate and the constant 6 is a reserve in percentage points.

$$B_{\mathrm{req}}=1.25(E+E_{\mathrm{return}})+6\qquad (2)$$

The consumption model assigns 0.70 percentage points per walking metre, 0.015 per second, 0.08 per turning radian and a 0.10 start/stop allowance. These coefficients define the benchmark cost model and were not calibrated against electrical measurements. Neither Q nor a difference in Q is a measured energy saving. Figure 1 shows the first frozen primary case and the compared routes; it is an example of the evaluated geometry, rather than evidence of physical traversal.

![Figure 1. First primary world, seed 2140000, repetition 0. Circles and stars mark start and goal; black blocks are obstacles and amber regions are terrain patches. Coincident route segments overlap.](figures/primary_world.png)

Figure 1. First primary world, seed 2140000, repetition 0. Circles and stars mark start and goal; black blocks are obstacles and amber regions are terrain patches. Coincident route segments overlap.

### 3.3 Meaning of the resource constraints

Distance, time, nominal battery use and terrain exposure have different roles in the evaluator. The score assigns a trade-off within the feasible set, while deadline, battery and exposure limits determine whether a route enters that set. A lower Q cannot compensate for violating a hard limit. Conversely, a longer route can be admitted when its terrain avoidance or heading sequence meets the configured constraints. This distinction is required when interpreting the component-removal comparison: an improved incumbent can change an admission outcome even when its average score effect on already admitted routes is small.

The destination-to-station allowance in equation (2) is prepared from the case's shared return route. It is held constant across configurations within that case. Thus the evaluated planner chooses the outward route under a common return allowance; it does not jointly optimize charging-station choice and outward/return trajectories. The destination travel-time limit applies to the predicted outward journey. The assistance diagnostic instead follows an outward-and-return mission and includes modeled service downtime. Its elapsed times and distances consequently have a different scope from T and D in the planning records.

The factor 1.25 and six-point reserve are declared policy margins. They provide no measured confidence level for battery depletion. Likewise, terrain exposure accumulates the configured difficulty field along a route; it is not a probability of slipping or mechanical failure. The interpretation of these quantities remains fixed across all algorithms. Although the saved cases contain an energy_multiplier metadata field, the planning evaluator uses the fixed coefficients stated above. The campaign therefore supplies no coefficient-robustness experiment or calibration result.

## 4 Compared planning configurations

### 4.1 Integrated geometric refiner

The complete implementation is denoted V4 to match the archived source. A charged resource-aware corridor stage supplies an incumbent. A bounded visibility graph adds candidate connections through route vertices and obstacle/terrain landmarks. The final polishing stage tests vertex deletion, projections, midpoint replacements and coordinate displacements. All accepted candidates pass the shared segment-clearance query.

Candidate ranking first distinguishes feasible routes, then minimizes normalized constraint violation and finally Q. Among feasible routes, Q determines the retained incumbent. An incumbent is preserved when later search stages exhaust their allowance. The selected default profile allocates 40% of the nominal wall allowance to initialization, up to a further 32% to visibility work, at most 44 landmarks and polishing displacement scales of 0.75, 0.25 and 0.08 m. The corridor refiner uses beam width 6, eight labels per state and an archive of 16 routes.

The search retains a finite set of alternatives rather than exhaustively enumerating paths. A candidate can first improve feasibility and subsequently improve Q. Reusing an incumbent prevents a later unsuccessful search stage from replacing an admitted route with a rejected one. This is an implementation property of the candidate ranking and archive; it does not imply that every route returned before a limit is feasible. Final admission is recalculated from the retained route and common mission constraints.

The graph and continuous stages perform different work. Graph expansion queries geometric connectivity and stores heading/resource labels. Continuous polishing proposes modified vertices and evaluates surviving route geometries. A visibility query can reject a connection without producing a complete route evaluation. Consequently, a common ceiling on evaluated routes is a shared accounting rule, rather than an assertion that every method performs the same number of collision operations or floating-point operations.

### 4.2 Swarm and component controls

PSO-P and ACO-P are the existing corridor-subsequence swarm implementations followed by the common polishing operator. PSO-P uses 16 particles, inertia 0.72, cognitive/social coefficients 1.49, velocity clipping at 0.25 and at most 40 iterations per corridor. ACO-P uses 12 ants, pheromone and heuristic exponents 1 and 2, evaporation 0.20, deposit 1 and at most 40 iterations per corridor. Both receive the seeded-corridor portfolio and the shared total planning allowance.

The continuous-coordinate control, PSO-C, starts from the same configured corridor refiner used for V4 initialization. It subdivides the longest segments until there are at least six internal vertices, preserving existing corners. Endpoints remain fixed, and internal xy coordinates form the particle state. Vertex count is fixed during each trial. The selected profile uses 12 particles, at most 40 iterations, inertia 0.65, cognitive/social coefficients 1.4, Gaussian perturbations of scale 2 m and velocity clipping at 2 m. Positions are clipped to map bounds. Colliding particle proposals are discarded, and the shared incumbent remains available. Final polishing reserves the last 25% of the nominal allowance.

V4 noL removes landmark search; V4 noP removes final polishing. These controls inherit the selected V4 profile. They isolate removal of the configured stage, without independent retuning. The six configurations share a nominal 2 s allowance and a ceiling of 240 evaluated collision-free routes, including charged initialization evaluations. Visibility checks and rejected particle proposals are recorded separately and are not equivalent to route evaluations.

### 4.3 Candidate flow and termination

For each trial, the map and mission limits are supplied to the selected configuration, an initialization portfolio is generated within its charged allowance, and the best retained route is updated according to feasibility and Q. V4 can extend this portfolio through bounded landmark connections before polishing. The corridor-subsequence controls search combinations drawn from their supplied corridors. PSO-C perturbs coordinates around an initialized route, retaining that route as an incumbent while proposals are tested. Component removals bypass the named V4 stage and preserve the remaining ranking and evaluator.

The route-evaluation counter advances on eligible complete candidates; cached evaluations are reused. Segment-clearance checks also screen partial or proposed geometry. For PSO-C, raw particles, collision-free particles and metric evaluations are therefore distinct counts. A fixed 240-evaluation ceiling does not prescribe 240 successful coordinate updates. Likewise, an algorithm can terminate below both nominal limits when its configured search operations are exhausted. The observed evaluation counts and wall-time distributions are reported with this distinction in Section 6.

The controls are executable parameterizations of the cited search ideas. Their common evaluator improves comparability of the configured objective, but it also restricts the question to that objective and initializer portfolio. The development phase compares two profiles for each base configuration rather than an exhaustive tuning space. Component removals answer whether deleting a stage changes the selected configuration; they do not estimate the best achievable performance of a separately retuned reduced algorithm.

## 5 Experimental protocol

### 5.1 Worlds and development selection

The protocol contains eight development worlds with seeds 2130000-2130007 and 32 primary worlds with seeds 2140000-2140031. Families cycle through open, clutter, rough and corridor; each contributes eight primary worlds. All maps have a 24 m half-extent. The same world specification supplies obstacles, shallow terrain tiles and semantic speed regions. Obstacle counts for the four families are 5, 16, 7 and 4, with the corridor family additionally containing two interrupted barriers. Terrain-patch counts are 1, 2, 4 and 3. Generated map specifications and their hashes are retained in the manifest.

Start and goal proposals are sampled within [-17, 17] m with initial separation 12-26 m, mapped to free grid locations and retained with separation at least 10 m. Per-case deadlines are sampled from 45, 70, 110 and 160 s; nominal battery allowances from 45, 65, 85 and 100%; and exposure limits from 10, 20 and 40. All compared methods receive the identical case. Return-to-station routes and costs are prepared once for that case. Saved world hashes are disjoint from the earlier campaign manifests, but the generator families are shared with the earlier work.

Each of four base configurations receives two complete development profiles. Selection first maximizes admitted attempts, then minimizes mean Q among admissions; exact ties retain the default. The alternative changes PSO-P to 24 particles, inertia 0.55 and cognitive/social coefficients 1.7/1.3; ACO-P to 18 ants, heuristic exponent 3 and evaporation 0.35; and PSO-C to 20 particles, 60 iterations, inertia 0.75, cognitive/social coefficients 1.6 and a 4 m perturbation/velocity bound. The geometric alternative uses initialization/visibility fractions 0.55/0.25, 60 landmarks and polishing scales 0.50, 0.15 and 0.05 m. Complete profiles, including inherited values, are archived. The default was selected for every base configuration before the primary test. Component controls inherit V4's choice.

Development contributes 64 planning records. Primary evaluation uses six configurations, 32 worlds and three paired repetitions, giving 576 records and 96 attempts per configuration. The complete campaign therefore contains 640 planning records. The manifest, source lock and selection rules were frozen locally before primary outcomes; there was no external preregistration. No primary case or unfavorable outcome was removed.

### 5.2 Runtime and outcome accounting

The scientific environment was Python 3.10.12, MuJoCo 3.9.0, NumPy 2.2.6 and SciPy 1.15.3 on Linux with an Intel Core i5-7600 CPU at 3.50 GHz and four logical processors. Scene loading, graph construction, return-route preparation and common heuristic preparation are recorded outside the per-method timer. The 2 s allowance is a search stop condition, rather than a hard real-time deadline. Runs occurred on a shared desktop with concurrent workloads; the recorded wall times characterize that execution environment.

Admission includes all scheduled primary attempts. A planning admission does not assert simulated mission completion. Paired Q comparisons include only case/repetition pairs admitted by both configurations. V4-only, control-only and mutual rejections remain separate outcome categories. For each jointly admitted pair, the relative score effect is equation (3), where subscripts c and v denote the control and V4 scores. Positive effects favor V4. Repetitions are averaged within each world before calculating across-world summaries.

$$\delta=100(Q_c-Q_v)/Q_c\qquad (3)$$

Descriptive 95% percentile intervals use 5,000 bootstrap resamples of the paired world means, with random seed 41104 [9]. The world is the resampling unit; repetitions within a world are not counted as independent maps. Intervals are unadjusted for the five control comparisons and conditional on joint admission. The locally frozen analysis also reports medians, effect ranges and counts above a descriptive 0.5% reference. This reference is not a validated operational benefit threshold.

The supplementary analysis added for the expanded report stratifies admissions by map family, summarizes observed computation, displays individual world effects and calculates leave-one-world-out means. These are post-hoc descriptions of the frozen primary records. No new primary trials, profile changes or case exclusions enter these analyses. The omission calculation deletes each paired world in turn, recomputes the mean of the remaining worlds and retains the smallest and largest values. It is a sensitivity description, not a replacement estimator or a rule for excluding an unfavorable world.

### 5.3 Assistance diagnostic

A separate post-hoc diagnostic uses V4 repetition-zero routes from the first four worlds of the archived final-pipeline campaign, identified as v6test_01-v6test_04 in the supplied input. Each replay includes the saved destination route and return to a service station. The four realized conditions are full assistance with gravity compensation, 0.5 assistance with compensation, zero assistance with compensation, and zero assistance without compensation. Each condition uses the same safe follower and a maximum duration of 180 simulated seconds. The initial script requested compensation removal before locomotion initialization; the constructor restored compensation on the 18 limb bodies. Those four mislabeled records are retained but excluded from the no-compensation comparison. Four corrected replays set compensation to zero after initialization and record all realized body values. The reported four-condition comparison uses 12 original executions and these four corrected executions. The selected routes were already observed, so this diagnostic is not an additional held-out locomotion test.

Telemetry is sampled at each 0.004 s physics step. Positive actuator work integrates the positive part of actuator force multiplied by actuator velocity; absolute work integrates its absolute value. The reported joint work excludes the externally imposed chassis velocity corrections. Foot contact counts use the six named foot geometries against geometries outside the robot subtree, accepting contact distances at most 0.002 m. The no-foot-contact fraction is the fraction of samples with no such detected contact. These definitions concern the logged contact detector and do not establish that other robot geometries never touch the scene.

A support margin is evaluated only when at least three detected feet form a valid planar convex hull. It measures the signed distance of the projected subtree centre of mass from the hull edges. Missing margins are retained as unavailable values, rather than converted to zero. Body tilt is derived from the robot quaternion. Because the assisted controller directly corrects body roll and pitch, small recorded tilt under assistance is not an independent demonstration of gait stability.

## 6 Results

### 6.1 Planning admission and paired scores

All 640 scheduled records completed. Development selected the default profile for every base configuration. V4, PSO-P, ACO-P and V4 noL each admit 93/96 primary attempts; PSO-C admits 94/96 and V4 noP admits 90/96. Table 2 reports admission and mean planner wall time; Figure 2 shows the admission counts. V4 records a mean search time of 0.376 s, compared with 0.731 s for PSO-C. All non-admitted primary outcomes are resource rejections; no primary trial has an error status.

Table 2. Primary admission and mean planner wall time.

| Method | Admitted / 96 | Mean time (s) |
| --- | --- | --- |
| V4 | 93 | 0.376 |
| PSO-P | 93 | 0.223 |
| ACO-P | 93 | 0.335 |
| PSO-C | 94 | 0.731 |
| V4 noL | 93 | 0.196 |
| V4 noP | 90 | 0.329 |

![Figure 2. Primary admission counts across all scheduled attempts.](figures/fresh_admission.png)

Figure 2. Primary admission counts across all scheduled attempts.

Against PSO-C, V4 has 33 lower-score pairs, 27 ties and 33 higher-score pairs among joint admissions. There are 0 V4-only admissions, 1 PSO-C-only admission and 2 mutual rejections. The world-averaged score effect is 0.690% with a descriptive 95% interval [-0.255, 2.312]%, based on 31 worlds. The median is 0.000%; world effects range from -1.718% to 23.202%, with 5/31 above the declared 0.5% reference. The mean effects against PSO-P and ACO-P are 0.929% and 0.921%, respectively, both with zero median. The component comparisons yield mean effects of 0.924% against V4 noL and 0.794% against V4 noP. Against V4 noL, V4 has 27 lower-score pairs, 57 ties and 9 higher-score pairs. Against V4 noP, it has 57 lower-score pairs, 33 ties and 0 higher-score pairs, plus 3 V4-only admissions. Table 3 and Figure 3 report the corresponding conditional mean effects and intervals.

Table 3. V4 score effects; n is the paired world count.

| Control | n | Mean (%) | 95% interval (%) |
| --- | --- | --- | --- |
| PSO-P | 31 | 0.929 | [0.027, 2.523] |
| ACO-P | 31 | 0.921 | [0.029, 2.507] |
| PSO-C | 31 | 0.690 | [-0.255, 2.312] |
| V4 noL | 31 | 0.924 | [0.036, 2.513] |
| V4 noP | 30 | 0.794 | [0.443, 1.209] |

![Figure 3. Conditional V4 score effects and descriptive 95% intervals. Positive values favor V4.](figures/fresh_effects.png)

Figure 3. Conditional V4 score effects and descriptive 95% intervals. Positive values favor V4.

The admission denominators in Table 2 include all primary attempts. The score summaries in Table 3 and Figure 3 use joint admissions and average repetitions within worlds. V4 noP has 30 paired worlds; the other comparisons have 31. The paired world effects, trial-level admission categories and all scheduled attempts are included in the supplementary records.

### 6.2 Family and computation breakdown

All primary resource rejections occur in the corridor family (Table 4). Open, clutter and rough each contribute 24/24 admissions for every configuration. Corridor admission is 21/24 for V4, PSO-P, ACO-P and V4 noL, 22/24 for PSO-C and 18/24 for V4 noP. The single additional PSO-C admission and the three admissions lost after polishing removal are therefore localized to corridor requests in this campaign.

Table 4. Admissions per family, out of 24 attempts.

| Method | Open | Clutter | Rough | Corridor |
| --- | --- | --- | --- | --- |
| V4 | 24 | 24 | 24 | 21 |
| PSO-P | 24 | 24 | 24 | 21 |
| ACO-P | 24 | 24 | 24 | 21 |
| PSO-C | 24 | 24 | 24 | 22 |
| V4 noL | 24 | 24 | 24 | 21 |
| V4 noP | 24 | 24 | 24 | 18 |

The family breakdown retains 24 scheduled attempts per method and family, combining eight worlds with three repetitions each. These attempts share a world within each three-repetition group. The counts therefore describe where resource rejection occurred; 24 is not a count of independently generated maps. Full admission in open, clutter and rough maps does not rank methods by score within those families or validate traversal of their physical terrain.

Table 5 separates elapsed search time from evaluated-route counts. PSO-C reaches the 240-route ceiling on 84/96 attempts; none of the other five configurations reaches it. Median route evaluations are 33 for V4, 46 for PSO-P, 32.5 for ACO-P, 240 for PSO-C, 21 for V4 noL and 5 for V4 noP. Recorded maximum search times range from 0.586 to 1.203 s, all below the nominal allowance. Median visibility-check counts are 1,033 for V4 and 2,142.5 for PSO-C, compared with 146.5 after landmark removal. Shared preparation has median 0.715 s and maximum 0.895 s per primary case.

Table 5. Search work across 96 attempts per method.

| Method | Median s | Max s | Median evals | At 240 |
| --- | --- | --- | --- | --- |
| V4 | 0.368 | 0.776 | 33 | 0 |
| PSO-P | 0.199 | 0.635 | 46 | 0 |
| ACO-P | 0.296 | 0.895 | 32.5 | 0 |
| PSO-C | 0.724 | 1.203 | 240 | 84 |
| V4 noL | 0.166 | 0.586 | 21 | 0 |
| V4 noP | 0.338 | 0.634 | 5 | 0 |

Preparation is shared within each case and excluded from method wall times. It includes loading the model, constructing the common graph and preparing the return route and heuristic. Adding it to each method independently would count shared work repeatedly in a paired experiment. Conversely, quoting search time alone as application startup latency would omit that work. The archived preparation and per-method timings permit either scope to be reconstructed explicitly.

### 6.3 Distribution and omission sensitivity

Figure 4 displays every jointly admitted world effect against PSO-C, ordered by the frozen case identifier. World ij3ctest_24 has a 23.202% positive effect, the largest in that comparison. Omitting it changes the remaining-world mean from 0.690% to −0.060%; omitting each other world in turn yields the range summarized in Table 6. The corresponding largest-world omissions leave mean effects of 0.187% against PSO-P, 0.178% against ACO-P and 0.182% against V4 noL. For polishing removal, the omission mean remains positive throughout its range of 0.682–0.822%. These calculations describe concentration of the observed effects and introduce no exclusion into the primary analysis.

![Figure 4. PSO-C paired world effects. Each point averages jointly admitted repetitions within one world; positive values favor V4. World 24 remains in the primary analysis.](figures/world_distribution.png)

Figure 4. PSO-C paired world effects. Each point averages jointly admitted repetitions within one world; positive values favor V4. World 24 remains in the primary analysis.

Table 6. Mean effects after omitting one paired world.

| Control | n | Smallest (%) | Largest (%) |
| --- | --- | --- | --- |
| PSO-P | 31 | 0.187 | 0.983 |
| ACO-P | 31 | 0.178 | 0.979 |
| PSO-C | 31 | -0.060 | 0.770 |
| V4 noL | 31 | 0.182 | 0.983 |
| V4 noP | 30 | 0.682 | 0.822 |

The sensitivity calculations retain the original conditional-admission rule. Deleting a paired world changes the descriptive population as well as its size. The results show how concentrated the measured advantage is in this sample; they do not identify a world as invalid. In particular, the largest positive effect remains part of every reported primary mean and bootstrap interval. No case is removed from the principal comparison as a consequence of the post-hoc display.

### 6.4 Diagnostic outcomes and record integrity

Table 7 reports completion under each realized assistance condition.

Table 7. Outcomes under realized replay conditions.

| Condition | Arrived / 4 | Timeout / 4 |
| --- | --- | --- |
| Full + GC | 4 | 0 |
| Blend + GC | 4 | 0 |
| Zero + GC | 0 | 4 |
| Zero, no GC | 0 | 4 |

Full assistance and 0.5 assistance each complete 4/4 missions. Zero assistance with compensation and the corrected zero-assistance/no-compensation condition each time out on all four missions at 180 s. GC in Table 7 denotes limb gravity compensation. A timeout records failure to complete the saved destination-and-return mission within the configured duration; it does not classify a fall. The four original mislabeled no-compensation requests are excluded from this comparison and preserved in the supplement with the correction record.

Full-assistance missions cover 34.71–42.83 m with elapsed times 62.85–89.63 s. Reduced-assistance missions cover 34.75–42.91 m in 62.83–89.66 s. Each completed elapsed time includes 8 s of modeled service. Zero assistance with compensation covers 0.324–0.326 m before the 180 s timeout; corrected zero assistance without compensation covers 0.376–0.381 m. Figure 5 shows individual mission distances, preserving all four cases in each realized condition.

The full and reduced assistance runs log zero detected foot contacts at every sampled physics step: mean contact feet is zero and the no-foot-contact fraction is 100% in all eight runs. Table 8 reports the contact ranges for every condition. The recorded absence of foot contacts applies to the defined six-foot detector; it supplies no evidence of a load-bearing walking gait. Maximum body tilt is below 0.410 degrees in the assisted runs, where roll/pitch rates are directly corrected. That value is a controller-dependent simulation observation, rather than a physical stability margin.

![Figure 5. Whole-mission distance in the four realized conditions. Each point is one archived route; GC-off uses the corrected replays. Points overlap where distances are similar.](figures/replay_distance.png)

Figure 5. Whole-mission distance in the four realized conditions. Each point is one archived route; GC-off uses the corrected replays. Points overlap where distances are similar.

Table 8. Contact telemetry ranges across four missions.

| Condition | Mean feet | No-contact (%) |
| --- | --- | --- |
| Full + GC | 0.000 | 100.00 |
| Blend + GC | 0.000 | 100.00 |
| Zero + GC | 0.421–0.422 | 83.00–83.05 |
| Zero, no GC | 4.009–4.017 | 0.02 |

An internal record audit reconciles all 640 records, checks 187 distinct route geometries and recomputes 748 metric values without an error. It verifies trial keys, development selection, source/model hashes, endpoints, clearance and score/admission arithmetic. These checks establish consistency with the declared evaluator, not independent physical validation.

The audit separates data integrity from simulator validity. Recomputing a route's score from the same cost definitions tests arithmetic and implementation consistency. Verifying frozen file hashes identifies which implementation produced a record. Neither procedure measures the error of the nominal cost model relative to physical energy consumption. The corrected compensation replay similarly checks the realized model setting and outcome; it does not add a physical reference trajectory.

## 7 Discussion

The coordinate representation control changes the interpretation of the complete planner's performance. PSO-C admits one more attempt than V4, and the descriptive interval for their paired mean score effect spans zero. The comparison therefore does not establish a mean score advantage for V4 against PSO-C. Against the corridor-subsequence controls, the positive mean effects coexist with zero medians and losses. The observed benefits are conditional on the configured representations, resource limits and sampled maps.

The component comparisons identify distinct trade-offs. Removing landmarks retains the admission count and lowers recorded mean search time, while its paired mean Q is higher. Removing polishing reduces admissions by three and has no lower-score joint admission than complete V4. These results support retaining polishing for this tested configuration, while landmark search trades additional recorded computation for a small, uneven score effect. The shared-desktop timing conditions prevent a controlled deployment-latency conclusion.

The assistance diagnostic establishes dependence of completion on direct chassis corrections for the four replayed missions. Removing those corrections produces timeouts under both gravity-compensation settings. This is an execution-model result, not an estimate of hardware failure probability. Mechanical joint work excludes the assistance contribution and cannot represent total electrical consumption. The differing source/simulation masses and uncalibrated consumption coefficients further restrict the findings to the declared simulator.

The primary maps come from four related procedural families; they do not establish performance on independently measured terrain or unseen map sources. PSO-C changes both internal-waypoint representation and the corridor-initialization procedure relative to PSO-P. Its comparison therefore evaluates a combined implementation change, rather than isolating representation alone. It uses a fixed vertex count and one selected update profile. The comparison does not cover adaptive vertex-count swarms, alternative native objectives or every possible parameterization. No physical robot measurements, electrical calibration or unassisted hardware experiment forms part of this study.

The distribution and computation results further constrain the practical interpretation. Near-zero medians and an influential positive world mean that an average score improvement does not describe a typical uniform reduction across maps. Admission is therefore reported before conditional score effects. Separately, the coordinate control reaches the evaluated-route ceiling far more often than the other configurations, while all recorded searches finish below the nominal 2 s allowance. This observation concerns the implemented stopping rules and workload; it does not show that 2 s of exclusive computation was supplied to every method.

The contact telemetry also changes the interpretation of successful assisted replay. Completion with no detected foot contact in the full and reduced assistance conditions cannot demonstrate propulsion through a load-bearing walking gait. The logged result establishes that the commanded route was followed by the assisted model under the specified detector and stopping criteria. Chassis correction and limb gravity compensation are separate mechanisms: the corrected zero-compensation comparison removes the latter only after initialization, while the zero-assistance condition removes the direct velocity blends. Mechanical joint work, nominal battery decrements and imposed base motion must therefore remain distinct quantities.

The available evidence supports a simulation planning study with an explicit execution diagnostic. It leaves actuator torque-speed behavior, electrical conversion losses, contact-material calibration, terrain-measurement error and the source-to-simulator mass difference unvalidated against hardware. No assertion about those quantities is inferred from geometric admission or the software consistency audit. A hardware autonomy claim would require a separately specified physical platform and measurements; those observations are absent from this dataset.

## 8 Conclusions

Under the frozen 32-world primary protocol, V4 admits 93/96 attempts and PSO-C admits 94/96. The V4 paired mean score effect against PSO-C is 0.690% with a zero median and an interval spanning zero; the campaign does not demonstrate a mean score advantage over that control. Polishing removal reduces admissions from 93 to 90, while landmark removal retains admission and lowers recorded search time at a small conditional score cost. All four archived diagnostic missions complete with full or reduced chassis assistance and time out after assistance removal.

The supported contribution is a traceable comparison of waypoint representations and component removals under common modeled constraints, together with an assistance-removal diagnostic. The results establish the observed admission, paired-score and replay outcomes. They do not establish universal planner superiority, measured battery savings or autonomous physical locomotion.

## 9 Data and code availability

The supplementary material contains the manifest, frozen profiles, full development and primary records, source snapshots, generated-model hashes, per-attempt and per-world summaries, the diagnostic input and outcomes, and the analysis scripts. Raw records retain all scheduled attempts. Source and model checksums identify the evaluated implementation. Analysis reconstructs geometry from saved world specifications; archived generated XML is retained unchanged for hash verification. Wall-clock-limited reruns can differ in completed search steps, routes and timing.

## References

[1] E. Todorov, T. Erez, and Y. Tassa, "MuJoCo: A physics engine for model-based control," in Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst., 2012, pp. 5026–5033, doi: 10.1109/IROS.2012.6386109.

[2] P. E. Hart, N. J. Nilsson, and B. Raphael, "A formal basis for the heuristic determination of minimum cost paths," IEEE Trans. Syst. Sci. Cybern., vol. 4, no. 2, pp. 100–107, 1968, doi: 10.1109/TSSC.1968.300136.

[3] J. Kennedy and R. Eberhart, "Particle swarm optimization," in Proc. ICNN Int. Conf. Neural Netw., vol. 4, 1995, pp. 1942–1948, doi: 10.1109/ICNN.1995.488968.

[4] M. Dorigo, V. Maniezzo, and A. Colorni, "Ant system: Optimization by a colony of cooperating agents," IEEE Trans. Syst., Man, Cybern. B, vol. 26, no. 1, pp. 29–41, 1996, doi: 10.1109/3477.484436.

[5] T. Lozano-Pérez and M. A. Wesley, "An algorithm for planning collision-free paths among polyhedral obstacles," Commun. ACM, vol. 22, no. 10, pp. 560–570, 1979, doi: 10.1145/359156.359164.

[6] Y. Yin, F. Gao, Q. Sun, Y. Zhao, and Y. Xiao, "Smart Gait: A gait optimization framework for hexapod robots," Chin. J. Mech. Eng., vol. 37, Art. no. 15, 2024, doi: 10.1186/s10033-024-01000-0.

[7] C. Chen, J. Lin, B. You, J. Li, and B. Gao, "Hexapod robot motion planning investigation under the influence of multi-dimensional terrain features," Front. Neurorobot., vol. 19, Art. no. 1605938, 2025, doi: 10.3389/fnbot.2025.1605938.

[8] COCO Project, "COCO: The experimental procedure," 2016. [Online]. Available: https://numbbo.github.io/coco-doc/experimental-setup/. Accessed: Nov. 4, 2026.

[9] B. Efron, "Bootstrap methods: Another look at the jackknife," Ann. Statist., vol. 7, no. 1, pp. 1-26, 1979, doi: 10.1214/aos/1176344552.

