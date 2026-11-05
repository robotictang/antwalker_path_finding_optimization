# Route Planning and Body Assistance in a Simulated Hexapod

[Author names and affiliations]
[Corresponding author email]

## Abstract

This study compares six route-planning configurations for a simulated six-legged robot. Each route must clear obstacles and meet a deadline, a nominal battery limit and a terrain-exposure limit. Eight development maps select the planner settings, and 32 main-test maps provide three repetitions per method, giving 640 planning attempts in total. The complete planner, V4, accepts 93 of 96 main-test attempts; a coordinate-based particle swarm planner, PSO-C, accepts 94. On routes accepted by both, V4 has a mean paired-map score improvement of 0.690%, a zero median and a descriptive 95% bootstrap interval of [−0.255, 2.312]%. The interval includes zero. Removing final local route adjustment reduces acceptance to 90 attempts. Removing landmark search retains 93 and reduces mean search time from 0.376 to 0.196 s. In four separate motion missions, full and half-scale body assistance each complete all missions; zero assistance completes none within 180 s. The assisted runs detect no foot-ground contact under the six-foot contact test. The results quantify planning differences and dependence on direct body assistance in the specified simulator. All battery costs are model outputs, with no physical or electrical validation.

Keywords: Hexapod; planning; optimization; simulation; reproducibility

## 1 Introduction

A robot route must clear obstacles and meet the limits of its task. The shortest route is not always the route with the lowest predicted travel time or battery use. In this study, terrain changes the allowed walking speed, turns add time and nominal battery use, and the battery limit includes travel to the destination and return to a charging station. These rules make route selection a constrained planning problem.

This study compares six route-planning configurations for a simulated six-legged robot in MuJoCo [1]. The main planner, called V4, builds initial routes, searches extra connections around obstacles and terrain regions, and then adjusts the route's intermediate points. The comparison includes two planners that select points from initial routes, one particle swarm planner that moves point coordinates, and two versions of V4 with a search stage removed. Every configuration uses the same maps, obstacle-clearance test, cost equations and task limits.

The main test measures whether each planned route meets those limits. Routes that meet every limit are called accepted routes. A separate comparison measures route score when both planners accept the same test. This separates acceptance from score: a planner can return a low-scoring route that still fails a deadline or battery requirement. A second experiment tests whether four simulated missions finish when direct control of the robot body's velocity is reduced or removed.

The complete experiment contains eight maps for parameter selection and 32 maps for the main test. V4 accepts 93 of 96 main-test attempts, while the coordinate-based particle swarm planner accepts 94. Their average paired score difference is 0.690% in V4's favor, with a zero median and a 95% bootstrap interval that includes zero. Removing V4's final route adjustment reduces acceptance to 90 attempts. The motion tests complete with body assistance and time out without it. The study therefore measures route-planning differences and the role of body assistance in this simulator.

## 2 Related work

A* searches a graph using the cost already incurred and an estimate of the remaining cost [2]. It provides the starting point for the grid searches used here. Particle swarm optimization updates candidate solutions using their previous motion and the best positions found by individual particles and the swarm [3]. Ant system uses pheromone and heuristic information to guide repeated construction of candidate solutions [4]. The PSO and ant controls in this study apply these ideas to specified route representations and use one common route score.

A visibility graph connects points when the line segment between them is clear of obstacles [5]. V4 uses this idea to test connections through a limited set of extra points. It also accounts for heading changes and applies local adjustments to complete routes. The number of retained alternatives and the search time are limited. The resulting route is the best candidate retained by the search, rather than a proven global optimum.

Route selection and leg-motion control address different parts of hexapod navigation. Yin et al. optimize swing trajectories, gait timing and gait sequence on the LittleStrong robot [6]. Chen et al. use terrain features to plan travel costs, foot placement and gait, and evaluate their method in simulation and physical experiments [7]. The present experiment keeps the gait controller fixed and supplies the terrain map directly. It compares routes for the robot body and separately tests the body-assistance mechanism.

The COCO benchmarking procedure identifies initialization, parameter selection and stopping rules as parts of an algorithm comparison [8]. These details are specified here because they affect the amount and type of search each planner performs. The main test uses the parameter profiles selected on the development maps. Route evaluations and obstacle-clearance checks are counted separately because they perform different operations.

## 3 Robot and planning model

### 3.1 Robot model and body assistance

The robot model has six legs, with three rotating joints per leg. The imported robot description has a total mass of 97.52 kg and a base mass of 35 kg. The assembled MuJoCo model has a total robot mass of 113.32 kg and a base mass of 46 kg. The simulation also includes wheels and a scanner, giving 23 actuators in total. Table 1 reports these model values. All experiments in this paper use walking mode, while the added mechanisms remain part of the simulated mass.

Table 1. Mass and joint settings of the two robot descriptions.

| Parameter | Imported model | MuJoCo model |
| --- | --- | --- |
| Total mass (kg) | 97.52 | 113.32 |
| Base mass (kg) | 35.00 | 46.00 |
| Leg joints | 18 | 18 |
| Added parts | No wheel joints | Wheels and scanner |

The imported robot description assigns leg-joint limits of 60 Nm of effort and 20 rad/s of velocity. These are declared limits in that description. The experiment includes no measurements of a physical motor's torque-speed curve, battery discharge or robot mass. The simulated assembly is the platform evaluated in this paper; the imported mass values are reported to identify the difference between the two descriptions.

MuJoCo advances the physics in steps of 0.004 s. The motion controller runs once every four physics steps, or every 0.016 s. Gravity is 9.81 m/s squared. Gravity compensation is enabled on 18 leg bodies in the standard configuration. This compensation and direct body assistance are separate mechanisms: the former counteracts gravity on the selected bodies, while the latter changes the free body's velocity directly.

Body assistance controls vertical motion and roll/pitch rates once per controller frame. It also changes horizontal velocity and yaw rate at each physics step. At assistance scale 1, the horizontal velocity is set to the requested velocity. At scale 0.5, each correction keeps half of the current velocity and adds half of the requested velocity. This blend is applied four times per frame. At scale 0, the controller leaves these body velocities unchanged by the assistance operation. The scale is a velocity-blending setting, not a specified support force.

The planner receives the robot's position, heading, obstacles and terrain directly from the simulation. It does not estimate these inputs from sensors. The start position, initial heading, destination and charging-station return estimate are identical across methods for each test. The experiment therefore compares decisions made with the same known map. Sensor noise, localization error and map reconstruction are outside the tested input model.

### 3.2 Route geometry

A route P is a sequence of points in the horizontal plane. Its first and last points are the supplied start and destination. Straight segments join consecutive points. The grid used for initial search has 0.25 m spacing and eight possible motion directions. A diagonal move through a blocked grid corner is rejected.

Every returned segment must pass the same clearance test against the planar obstacle shapes. The configured robot radius is 1.82 m, the tracking margin is 0.12 m, and the segment-clearance tolerance is 0.005 m. These values define the planning clearance model. The test checks a route for the robot body; it does not calculate a separate three-dimensional foot trajectory along every segment.

The terrain map contains regions with different walking-speed limits and difficulty values. Terrain difficulty is sampled along each route segment at spacing no greater than 0.125 m. The exposure assigned to a segment is its length multiplied by its mean sampled difficulty. Total exposure R is the sum over all segments. This is a cost defined by the terrain map, not a measured probability of slipping.

### 3.3 Route score and acceptance

The route evaluator calculates four quantities: distance D in metres, predicted destination travel time T in seconds, nominal battery use E in percentage points, and terrain exposure R. The initial heading is π/2 radians. Predicted time includes travel at the terrain-dependent speed limit, heading changes at 1 rad/s, and an acceleration allowance. The speed limits for smooth, mild and higher-grade terrain are 0.75, 0.65 and 0.38 m/s.

Equation (1) combines the four quantities into a score Q. A smaller score is better. The denominators set the relative weight of each quantity and remain fixed throughout the experiment.

$$Q(P)=D/50+T/90+E/30+R/80\qquad (1)$$

Acceptance requires the predicted destination time to meet the deadline, exposure to meet the terrain limit, and the required nominal battery allowance to fit the available battery. Equation (2) gives that allowance. The subscript return identifies the nominal battery use of a route from the destination to a charging station. The factor 1.25 and the additional six percentage points are fixed reserve rules.

$$B_{\mathrm{req}}=1.25(E+E_{\mathrm{return}})+6\qquad (2)$$

The battery cost model assigns 0.70 percentage points per walking metre, 0.015 per second, 0.08 per turning radian and a 0.10 start/stop allowance. These coefficients were not fitted to electrical measurements. Battery use in this paper means the output of this equation-based model. Mechanical joint work and electrical battery consumption are different quantities, and the route score does not convert one into the other.

The charging station and return route are selected once per test before the planners are compared. Each planner then chooses an outward route using the same return allowance. The destination deadline applies to the outward route. The motion experiment follows both the outward and return routes and adds eight seconds of simulated service after arrival at the station. Its mission distance and elapsed time therefore cover more than the outward quantities D and T.

A route with a lower score is still rejected if any hard limit is exceeded. Candidate ranking first separates routes that meet all limits from routes that do not. For rejected routes, the excess over each limit is divided by that limit, and the positive ratios are added. A lower sum ranks first; excesses of at most 0.00000001 are treated as zero. For accepted routes, lower Q ranks first. This rule allows a search stage to improve acceptance as well as score and prevents a later rejected candidate from replacing an accepted route.

Figure 1 shows the routes produced by V4 and the coordinate-based PSO control in the first main-test map. This case is selected by map order, independently of the score difference. The routes overlap because both planners return the same straight connection for this repetition.

![Figure 1. Map 1, repetition 0. Circle: start; star: goal; black: obstacles; amber: terrain. Routes overlap.](figures/primary_world.png)

Figure 1. Map 1, repetition 0. Circle: start; star: goal; black: obstacles; amber: terrain. Routes overlap.

## 4 Planning methods

### 4.1 Complete planner

V4 has three stages. The first stage searches initial corridors while accounting for time, battery and terrain limits. A corridor is an initial route through free space from which later stages construct alternatives. The second stage adds connections through a limited set of points around obstacles and terrain boundaries. The final stage adjusts complete routes by deleting points, projecting points, replacing points by midpoints, and moving point coordinates.

The best-ranked route is kept throughout the search. A proposed route replaces it only when the ranking improves. Every proposed change must pass the common segment-clearance test before its route cost is evaluated. Repeated route geometries reuse their previous evaluations. These rules apply to the shared local-adjustment stage used by the compared planners.

The selected V4 settings allocate 40% of the nominal time allowance to the initial search and up to a further 32% to the extra-point search. At most 44 points are used in that search. Local coordinate moves use step sizes of 0.75, 0.25 and 0.08 m. The initial corridor search uses a beam width of six, up to eight labels per state, and storage for 16 candidate routes. These bounds limit the alternatives considered within a trial.

A graph connection and a complete route evaluation are counted separately. The graph search can reject a line segment before it becomes part of a full route. It also stores alternatives with different headings and resource costs. The local-adjustment stage instead changes a complete sequence of route points. A shared limit on full route evaluations therefore does not imply equal numbers of geometric queries across methods.

### 4.2 PSO and ant controls

PSO-P and ACO-P select subsequences of points from initial corridors and then apply the common local-adjustment stage. PSO-P uses 16 particles, inertia 0.72, cognitive and social coefficients of 1.49, velocity clipping at 0.25, and at most 40 iterations per corridor. ACO-P uses 12 ants, pheromone exponent 1, heuristic exponent 2, evaporation 0.20, deposit 1, and at most 40 iterations per corridor.

PSO-C uses continuous coordinates for the internal route points. It begins with the same configured initial corridor search as V4. The longest segments are subdivided until the route has at least six internal points. Existing corners are preserved during subdivision, and the start and destination remain fixed. The number of internal points is fixed during a trial, while their horizontal coordinates can move within the map bounds.

The selected PSO-C settings are 12 particles, at most 40 iterations, inertia 0.65, and cognitive and social coefficients of 1.4. Initial Gaussian perturbations have a scale of 2 m, and velocity changes are clipped at 2 m. Positions are clipped to the map bounds. Proposals that fail clearance are discarded. The initial best route remains available even if the particle proposals do not improve it. The last 25% of the nominal time allowance is reserved for common local adjustment, subject to the shared evaluation ceiling.

PSO-C and PSO-P differ in their coordinate representation and their initial-route procedure. Their comparison measures the combined effect of these implementation choices. It does not isolate a change in representation alone. All reported results apply to the specified settings and route objective.

### 4.3 Removal of planner stages and search limits

V4 noL removes the search through extra points, called landmarks. V4 noP removes final local adjustment, also called polishing. Both versions inherit the selected V4 settings for the stages they retain. They measure the effect of removing one stage from the tested planner. The reduced versions are not separately retuned on the main-test maps.

Every method has a nominal two-second search allowance and a ceiling of 240 evaluated collision-free routes. Evaluations used by initialization count toward that ceiling. Collision checks on rejected proposals are counted as geometric work rather than complete route evaluations. A method can finish below both limits when it exhausts its prescribed operations. PSO-C can also exhaust the evaluation ceiling before its time allowance is used.

The wall timer includes initialization and refinement for the individual method. Shared map preparation is performed separately before the methods run. This includes loading the scene, building the common graph, preparing the return route and calculating common search guidance. Search time therefore measures one part of the planning process. It excludes preparation that all methods share for a given case.

## 5 Experimental design

### 5.1 Maps and task limits

The experiment uses eight development maps with seeds 2130000-2130007 and 32 main-test maps with seeds 2140000-2140031. Map types cycle through open, clutter, rough and corridor. Each type contributes two development maps and eight main-test maps. Every map extends from −24 to 24 m along each horizontal axis.

The four types have 5, 16, 7 and 4 generated obstacles, respectively. Corridor maps also contain two interrupted barriers. The numbers of terrain patches are 1, 2, 4 and 3. Each map defines the obstacles, shallow terrain tiles and regions that set the walking speed and exposure. All six planners receive exactly the same geometry and terrain for a given case.

Start and destination proposals are sampled within [−17, 17] m on both axes, with an initial separation of 12-26 m. They are moved to free grid locations and retained when their final separation is at least 10 m. Deadlines are drawn from 45, 70, 110 and 160 s. Available nominal battery levels are 45, 65, 85 and 100%, and exposure limits are 10, 20 and 40. The charging-station return estimate is fixed before comparing the methods.

The planning battery coefficients remain fixed for every map. Thus different battery allowances change the available resource limit, rather than the amount of nominal battery use assigned to a metre or a turn. The experiment varies map geometry and task constraints. It does not test a calibrated range of physical battery characteristics.

### 5.2 Parameter selection and repeated tests

Each of the four base methods is tested with two parameter profiles on the development maps. Selection first favors the profile with more accepted attempts. If acceptance is equal, the profile with the lower mean score among accepted attempts is selected. Exact ties retain the default. The default profile is selected for every base method. Both reduced V4 versions inherit that selection.

The alternative PSO-P profile uses 24 particles, inertia 0.55 and cognitive/social coefficients 1.7/1.3. The alternative ACO-P profile uses 18 ants, heuristic exponent 3 and evaporation 0.35. The alternative PSO-C profile uses 20 particles, 60 iterations, inertia 0.75, cognitive/social coefficients 1.6 and a 4 m perturbation and velocity bound. The alternative V4 profile uses initial-search and extra-point fractions of 0.55 and 0.25, 60 points, and local move sizes of 0.50, 0.15 and 0.05 m. Other settings retain the corresponding defaults.

The development phase contains 64 planning attempts: eight maps, four methods and two profiles. The main test contains 576 attempts: 32 maps, six methods and three paired repetitions. Each method therefore has 96 main-test attempts, and the complete experiment has 640. The maps, parameter-selection rule and primary analysis were set before the main-test results. There was no external preregistration. All scheduled main-test attempts are included in the acceptance counts.

The three repetitions within a map share the same task and geometry. They provide repeated algorithm runs, rather than three independent maps. Score differences are averaged within a map before summarizing across maps. This gives equal weight to each paired map, including cases where the number of jointly accepted repetitions differs.

### 5.3 Score comparison and statistical analysis

Score comparisons use only attempts for which both V4 and the comparison method accept a route. Acceptance by only one method and rejection by both methods are counted separately. Equation (3) defines the relative score difference for a paired attempt. Q_c is the comparison method's score and Q_v is V4's score. A positive difference means V4 has the lower score; a negative difference means the comparison method has the lower score. Absolute score differences of at most 0.00000001 are counted as ties.

$$\delta=100(Q_c-Q_v)/Q_c\qquad (3)$$

The reported mean and median use the map averages of these paired differences. Descriptive 95% percentile bootstrap intervals use 5,000 resamples of maps, with random seed 41104, following the resampling principle in [9]. Repetitions stay grouped within their map. The intervals are conditional on acceptance by both methods and are not adjusted for the five comparisons. A 0.5% difference is used only as a descriptive reference for counting larger improvements.

The family breakdown, computation summary, map-by-map display and omission analysis were calculated after the main test. They describe the existing results without changing the selected settings or the main-test sample. In the omission analysis, one paired map is left out at a time and the mean is recalculated. The smallest and largest resulting means show how strongly an individual map affects the average. Every map remains in the primary analysis.

The tests run under Python 3.10.12, MuJoCo 3.9.0, NumPy 2.2.6 and SciPy 1.15.3 on Linux. The processor is an Intel Core i5-7600 at 3.50 GHz with four logical processors. The desktop also runs concurrent workloads. Reported wall times are observations from that environment, rather than measurements of exclusive processor use or real-time deployment latency.

### 5.4 Motion tests and contact measurements

The motion experiment uses four previously evaluated maps, one each of open, clutter, rough and corridor, with seeds 1670000-1670003. It follows the V4 route from the first repetition in each map and then the fixed return route to a charging station. The outward route lengths are 21.36, 22.30, 23.45 and 19.78 m. Initial nominal battery levels are 45, 85, 45 and 100%, respectively. These routes are selected by map order and are separate from the 32 main planning maps.

Each mission is run under four conditions: full body assistance with gravity compensation, half-scale assistance with compensation, zero assistance with compensation, and zero assistance without compensation. The route follower and 180 s maximum simulated duration are the same in every condition. Completion means reaching the destination and returning to the station. An unfinished mission reaches the time limit. Completed mission time includes eight seconds of modeled station service.

Gravity compensation is checked after the locomotion controller is initialized. The compensation-free condition sets all body compensation values to zero at that point. Four preliminary runs in which initialization restored compensation are excluded from that condition and are repeated after verified removal. The final comparison contains four missions under each of four conditions, giving 16 executions. These previously evaluated routes form a diagnostic of the execution model, rather than a new set of unseen locomotion tests.

Foot contact is sampled at every 0.004 s physics step. A foot counts as in contact when one of the six foot geometries touches a geometry outside the robot and their reported distance is at most 0.002 m. Mean contact feet is the average number of detected feet per sample. The no-contact percentage is the fraction of samples with zero detected foot contacts. This detector concerns the six feet; contacts involving other robot parts are not counted as foot contacts.

Body tilt is calculated from the body's orientation. Assisted runs directly correct roll and pitch, so low tilt in those runs measures the assisted controller's behavior. Positive actuator work integrates the positive part of actuator force times actuator velocity. It excludes work associated with the direct body-velocity corrections. These measurements describe simulated motion and joint activity under the specified assistance condition.

## 6 Results

### 6.1 Accepted routes and paired scores

All 640 planning attempts finish without a recorded trial error. The default profile is selected for every base method. In the main test, V4, PSO-P, ACO-P and V4 noL each accept 93/96 attempts. PSO-C accepts 94/96, and V4 noP accepts 90/96. Every rejected main-test attempt fails a resource requirement. Table 2 and Figure 2 report these acceptance counts. Mean search time is 0.376 s for V4 and 0.731 s for PSO-C; the fastest mean is 0.196 s for V4 noL.

Table 2. Accepted main-test routes and mean search time.

| Method | Accepted / 96 | Mean time (s) |
| --- | --- | --- |
| V4 | 93 | 0.376 |
| PSO-P | 93 | 0.223 |
| ACO-P | 93 | 0.335 |
| PSO-C | 94 | 0.731 |
| V4 noL | 93 | 0.196 |
| V4 noP | 90 | 0.329 |

![Figure 2. Accepted main-test attempts out of 96 per method.](figures/fresh_admission.png)

Figure 2. Accepted main-test attempts out of 96 per method.

Against PSO-C, V4 produces a lower score on 33 paired accepted attempts, a tied score on 27 and a higher score on 33. PSO-C alone accepts one attempt, V4 alone accepts none, and both reject two. The mean of the map-level score differences is 0.690%, with a median of zero and a descriptive 95% interval of [−0.255, 2.312]%. Differences across the 31 paired maps range from −1.718% to 23.202%; five maps exceed the descriptive 0.5% improvement reference.

V4 has mean paired score improvements of 0.929% against PSO-P, 0.921% against ACO-P, 0.924% against V4 noL and 0.794% against V4 noP. The first two comparisons both have zero medians. Against V4 noL, V4 has 27 lower-score pairs, 57 ties and nine higher-score pairs. Against V4 noP, it has 57 lower-score pairs, 33 ties and no higher-score pairs, plus three attempts accepted only by complete V4. Table 3 and Figure 3 summarize the paired-map means and intervals.

Table 3. Paired score differences favoring V4; n is the number of paired maps.

| Control | n | Mean (%) | 95% interval (%) |
| --- | --- | --- | --- |
| PSO-P | 31 | 0.929 | [0.027, 2.523] |
| ACO-P | 31 | 0.921 | [0.029, 2.507] |
| PSO-C | 31 | 0.690 | [-0.255, 2.312] |
| V4 noL | 31 | 0.924 | [0.036, 2.513] |
| V4 noP | 30 | 0.794 | [0.443, 1.209] |

![Figure 3. Paired-map mean score differences and descriptive 95% bootstrap intervals. Positive values favor V4.](figures/fresh_effects.png)

Figure 3. Paired-map mean score differences and descriptive 95% bootstrap intervals. Positive values favor V4.

The score comparison against V4 noP uses 30 paired maps. The other four comparisons each use 31. The acceptance counts in Table 2 include all 96 attempts per method, while Table 3 and Figure 3 include only paired accepted routes. This difference in denominator is part of the analysis: a score mean on accepted routes does not replace the result for rejected tasks.

### 6.2 Map types and computation

All resource rejections in the main test occur in corridor maps. Open, clutter and rough maps each give 24/24 accepted attempts for every method. In corridor maps, V4, PSO-P, ACO-P and V4 noL each accept 21/24 attempts; PSO-C accepts 22/24 and V4 noP accepts 18/24. Table 4 locates both PSO-C’s additional acceptance and the three acceptances lost after removing final local adjustment in the corridor group.

Table 4. Accepted attempts out of 24 for each map type.

| Method | Open | Clutter | Rough | Corridor |
| --- | --- | --- | --- | --- |
| V4 | 24 | 24 | 24 | 21 |
| PSO-P | 24 | 24 | 24 | 21 |
| ACO-P | 24 | 24 | 24 | 21 |
| PSO-C | 24 | 24 | 24 | 22 |
| V4 noL | 24 | 24 | 24 | 21 |
| V4 noP | 24 | 24 | 24 | 18 |

Each cell in Table 4 combines eight maps with three repetitions per map. The open, clutter and rough maps all produce accepted routes under the tested limits. The corridor maps contain every resource rejection in the main test. Acceptance in this table describes the planned route and cost equations. It does not count completed motion tests.

PSO-C reaches the 240-route evaluation limit on 84/96 attempts. None of the other methods reaches it. Median evaluation counts are 33 for V4, 46 for PSO-P, 32.5 for ACO-P, 240 for PSO-C, 21 for V4 noL and five for V4 noP. Table 5 gives median and maximum search times together with these counts. Median geometric-clearance checks are 1,033 for V4, 2,142.5 for PSO-C and 146.5 for V4 noL. Shared preparation takes a median of 0.715 s and a maximum of 0.895 s per main-test map, outside the individual search timers.

Table 5. Search time and evaluated routes over 96 attempts.

| Method | Median s | Max s | Median evals | At 240 |
| --- | --- | --- | --- | --- |
| V4 | 0.368 | 0.776 | 33 | 0 |
| PSO-P | 0.199 | 0.635 | 46 | 0 |
| ACO-P | 0.296 | 0.895 | 32.5 | 0 |
| PSO-C | 0.724 | 1.203 | 240 | 84 |
| V4 noL | 0.166 | 0.586 | 21 | 0 |
| V4 noP | 0.338 | 0.634 | 5 | 0 |

The largest recorded search time is 1.203 s for PSO-C. Every search finishes below the nominal two-second allowance. This does not mean that every method performs the same search work: PSO-C reaches the 240-evaluation limit on most attempts, while the other methods finish with lower counts. Table 5 reports both types of evidence so that lower elapsed time is not interpreted as equal computation at a different speed.

### 6.3 Variation across maps

Figure 4 shows every paired-map score difference against PSO-C. Map 24 has the largest positive difference, 23.202%. Leaving this map out changes the mean of the remaining paired maps from 0.690% to −0.060%. Table 6 reports the range of means obtained by leaving out each map in turn. Leaving out the largest positive map gives means of 0.187% against PSO-P, 0.178% against ACO-P and 0.182% against V4 noL. Against V4 noP, all omission means stay positive, ranging from 0.682% to 0.822%.

![Figure 4. Score difference against PSO-C on each paired map, averaged over jointly accepted repetitions. Positive values favor V4. All points remain in the primary mean.](figures/world_distribution.png)

Figure 4. Score difference against PSO-C on each paired map, averaged over jointly accepted repetitions. Positive values favor V4. All points remain in the primary mean.

Table 6. Mean score differences after leaving out one paired map.

| Control | n | Smallest (%) | Largest (%) |
| --- | --- | --- | --- |
| PSO-P | 31 | 0.187 | 0.983 |
| ACO-P | 31 | 0.178 | 0.979 |
| PSO-C | 31 | -0.060 | 0.770 |
| V4 noL | 31 | 0.182 | 0.983 |
| V4 noP | 30 | 0.682 | 0.822 |

The omission means in Table 6 are calculated from the same paired-map differences as Table 3. The positive effect on map 24 remains in the primary mean and bootstrap interval. Its influence explains why a positive average can coexist with a zero median and nearly balanced numbers of lower- and higher-score pairs. The omission calculation measures that influence directly, without removing the case from the principal result.

### 6.4 Route differences on map 24

Map 24 is a corridor map with seed 2140023. The start is (−7.75, 10.75) m and the destination is (−7.50, −8.75) m. The deadline is 110 s, available nominal battery is 85%, and the exposure limit is 20. The return-route battery estimate is 11.682 percentage points. Both methods accept all three repetitions. Table 7 compares the mean returned route metrics.

V4 returns the same route in all three repetitions, with distance 20.803 m and score 1.310. PSO-C’s mean route distance is 27.135 m and mean score is 1.706. V4 has lower distance, predicted time, nominal battery use and terrain exposure in each paired repetition. Because all four weights in equation (1) are positive, these differences all reduce Q. Figure 5 shows the routes from repetition zero: the PSO-C route takes a wider detour to the west. This observed route difference accounts for the lower score in that repetition; it does not identify a unique cause inside the search algorithm.

Table 7. Mean route metrics on map 24 over three repetitions.

| Metric | V4 | PSO-C |
| --- | --- | --- |
| Distance (m) | 20.803 | 27.135 |
| Time (s) | 32.959 | 42.584 |
| Battery (points) | 15.446 | 20.066 |
| Exposure | 1.012 | 1.665 |
| Score Q | 1.310 | 1.706 |

![Figure 5. Routes on corridor map 24, repetition 0. The PSO-C route passes farther west than the V4 route. The circle and star mark start and destination; amber regions mark terrain patches.](figures/map24_routes.png)

Figure 5. Routes on corridor map 24, repetition 0. The PSO-C route passes farther west than the V4 route. The circle and star mark start and destination; amber regions mark terrain patches.

This example is selected after the main test because it has the largest positive paired-map effect against PSO-C. It is used to explain the distribution in Figure 4. The example does not estimate a typical improvement: the median effect across the paired maps is zero. Both the map-specific result and the full distribution are therefore required to describe the observed score difference.

### 6.5 Motion and detected foot contacts

Full and half-scale body assistance each complete four of four missions. Zero assistance completes none of the four missions, both with gravity compensation enabled and with compensation verified as zero. Every unfinished mission reaches the 180 s time limit. Table 8 uses GC for leg-body gravity compensation. Completion covers the destination and return to the station; it is separate from planning acceptance.

Table 8. Completed missions and timeouts under body assistance.

| Condition | Arrived / 4 | Timeout / 4 |
| --- | --- | --- |
| Full + GC | 4 | 0 |
| Half + GC | 4 | 0 |
| Zero + GC | 0 | 4 |
| Zero, no GC | 0 | 4 |

With full assistance, whole-mission distances range from 34.71 to 42.83 m, and elapsed times range from 62.85 to 89.63 s. With half-scale assistance, distances range from 34.75 to 42.91 m and times from 62.83 to 89.66 s. Each completed time includes eight seconds of station service. With zero assistance and compensation enabled, body displacement totals 0.324–0.326 m by the timeout. With zero assistance and compensation disabled, it totals 0.376–0.381 m. Figure 6 shows all four mission distances in each condition.

Every full- and half-scale assisted run has zero detected foot contact at every sampled physics step. Their mean contact count is zero and their no-contact percentage is 100%. Table 9 gives the contact ranges across the four missions in every condition. The largest body tilt in the assisted runs is below 0.410 degrees, while the controller directly corrects roll and pitch. These are observations of the assisted model under the contact and orientation definitions in Section 5.4.

![Figure 6. Whole-mission distance for four missions in each assistance condition. Points overlap when distances are similar. GC means leg-body gravity compensation.](figures/replay_distance.png)

Figure 6. Whole-mission distance for four missions in each assistance condition. Points overlap when distances are similar. GC means leg-body gravity compensation.

Table 9. Contact-measurement ranges across four missions.

| Condition | Mean feet | No-contact (%) |
| --- | --- | --- |
| Full + GC | 0.000 | 100.00 |
| Half + GC | 0.000 | 100.00 |
| Zero + GC | 0.421–0.422 | 83.00–83.05 |
| Zero, no GC | 4.009–4.017 | 0.02 |

The contact counts change the meaning of mission completion. All eight full- and half-scale assisted runs finish while the six-foot detector reports no foot contact. These runs demonstrate route following by the assisted body model. They do not demonstrate that foot-ground forces propel the body along those routes. Zero assistance produces some body displacement but no completed mission within 180 s, both with leg gravity compensation and after its removal.

## 7 Discussion

PSO-C accepts one more main-test attempt than V4. Among attempts accepted by both methods, V4 has a 0.690% mean score improvement, a zero median, and 33 lower-score versus 33 higher-score pairs. Its descriptive interval includes zero. These results do not establish a lower average score for V4 against this coordinate-based PSO implementation. Map 24 accounts for a large share of the positive mean, as shown by the omission analysis and its shorter V4 route.

The comparison with PSO-P and ACO-P gives positive mean effects of 0.929% and 0.921%, respectively, with zero medians. These are results for the implemented planners, their initial corridors and the common cost model. PSO-C changes both initialization and point coordinates relative to PSO-P. The study therefore compares complete configurations, rather than attributing the outcome to representation alone or ranking every possible PSO and ant algorithm.

Removing final local adjustment changes both acceptance and score. V4 noP loses three accepted corridor attempts, and complete V4 never has a higher score on their paired accepted attempts. Removing landmark search preserves acceptance but reduces mean search time from 0.376 to 0.196 s, with a 0.924% mean paired score cost. The tested planner therefore benefits more consistently from final local adjustment, while the extra-point search adds computation for an uneven score improvement.

The motion experiment identifies a separate dependence on direct body assistance. Full and half-scale assistance complete all four missions; both zero-assistance conditions time out on every mission. The assisted runs report zero detected foot contact under the stated detector. Completion in those conditions is therefore evidence about the assisted execution model, not a demonstration of an unassisted walking robot. Small body tilt under direct roll/pitch correction does not provide an independent gait-stability measurement.

All battery figures in the study come from fixed distance, time and turning coefficients. The model's 25% multiplier and six-point reserve determine route acceptance but have no measured battery-discharge confidence level. Joint work excludes the body-assistance contribution, and the experiment contains no electrical measurements. The evidence supports comparisons of nominal route costs, rather than claims of measured electrical savings.

The maps are generated from four specified types with known robot pose and terrain. The timing measurements come from a shared desktop. The imported and simulation masses differ, and no physical mass, motor, contact-material or terrain measurements are included. These facts define the scope of the reported results. The experiment evaluates the stated planning problem and assisted simulator; it supplies no hardware validation.

## 8 Conclusions

In the 32-map main test, V4 accepts 93/96 attempts and PSO-C accepts 94/96. V4’s paired mean score improvement against PSO-C is 0.690%, with a zero median and a descriptive interval that includes zero. The test does not establish a lower average score for V4 against that control. Final local adjustment raises acceptance from 90 to 93 attempts. Landmark search retains the same acceptance count, with higher recorded computation and a 0.924% paired mean score improvement over its removal.

The strongest consistent component result is the contribution of final local adjustment: removing it reduces acceptance and gives no lower-score paired accepted attempt than complete V4. The landmark stage keeps the same acceptance count and adds search time for a small, uneven score difference. The motion experiment establishes that the four tested missions finish only when direct body assistance is applied. Together, the results define the tested planner's trade-offs and distinguish accepted geometric routes from unassisted physical locomotion.

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

