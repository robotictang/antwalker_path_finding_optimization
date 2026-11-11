# Suggested manuscript replacements

These passages are proposed revisions for **Pathfinder-Robot-CLRP-IJ3C-V2.odt**. They have not been applied to the original. They correct the verified reporting problems while retaining the existing results, tables, figures, equations and reference numbering. Sections identify the passage to replace; the paragraph IDs are optional locators in the review extraction.

## Abstract

Replace the entire abstract with:

> We evaluate landmark search and final local refinement for constrained body-route planning in a simulated hexapod. Six configurations share obstacle-clearance, deadline, nominal battery, and terrain-exposure constraints. Parameter selection uses 64 attempts on eight development maps; the primary test comprises 576 attempts on 32 maps with three repetitions. Full Constrained Landmark Route Planning (CLRP) accepts 93 of 96 primary attempts, compared with 94 for coordinate-based particle swarm optimization (PSO-C). Removing final refinement reduces acceptance to 90. Removing landmark search retains 93 acceptances and reduces mean search time from 0.376 to 0.196 s; full CLRP provides a conditional mean paired-map relative score improvement of 0.924% over this variant. Against PSO-C, the corresponding mean improvement is 0.690%, with a median of zero and a descriptive 95% bootstrap interval of [−0.255%, 2.312%], which does not establish a score advantage. A separate diagnostic comprises 16 executions of four missions under four assistance conditions. Full and 0.5-scale velocity assistance each complete all four missions; both zero-assistance conditions complete none and time out at 180 s. No foot contact is detected by the six-foot criterion in assisted executions. These results characterize planning trade-offs and assistance dependence under the specified simulation. Nominal battery costs are model outputs without physical or electrical validation.

Suggested keywords: **Hexapod; planning; optimization; simulation; reproducibility**.

## Section 1 first paragraph P007

> A robot route must avoid obstacles and satisfy the task's resource constraints. A short route can still miss an arrival deadline or require more battery capacity than is available for reaching the destination and returning to a charging station. In this model, terrain limits walking speed, turns add travel time and nominal battery cost, and terrain exposure is constrained. The evaluator includes these costs and checks each task constraint independently.

## Section 1 third paragraph P009

> We report route acceptance, score differences conditional on joint acceptance, and search computation. Parameters are selected on eight development maps before evaluation on 32 primary maps with three paired repetitions. Stage-removal comparisons test whether landmark search and final local refinement change acceptance or improve accepted routes. A separate four-map diagnostic examines dependence on direct body assistance, distinguishing route acceptance from validation of locomotion.

## Section 2 technical terminology P012 and P016

Replace the first related-literature paragraph with:

> A* searches a graph using the sum of the cost incurred and an estimate of the remaining cost [2]. Particle swarm optimization updates candidate solutions using particle velocities and the best positions found so far by individual particles and the swarm [3]. Ant System uses pheromone and heuristic information to guide route construction [4]. A visibility graph connects visible nodes with collision-free straight-line segments [5]. These methods inform the initial search, population updates and graph connections used here. The bounded search retains its best candidate but does not guarantee global optimality.

Replace the paragraph beginning “Also the hexapod investigations…” with:

> Hexapod studies also evaluate motion below the body-route level. Yin et al. optimize swing trajectories, gait period, duty factor and gait sequence on LittleStrong [8]. Chen et al. combine geometric and physical terrain features with traversal-cost planning, foothold selection and free-gait planning, with simulation and physical robot validation [9]. The current study holds the gait controller fixed, supplies terrain information directly, and evaluates removal of body-route planning stages. Its assistance diagnostic does not replace the physical locomotion and foothold evaluations in those studies.

In the Ma paragraph, use **“under multiple resource constraints and mode-chain constraints.”** In the Guo paragraph, use **“path planning”** for the cited method. The existing reference list can remain.

## Section 3.1 assistance description P025 and P026

> The physics timestep is 0.004 s. The motion controller updates every four physics steps, giving a control interval of 0.016 s. Gravity has magnitude 9.81 m/s². In the standard configuration, gravity compensation is enabled on 18 leg bodies. Gravity compensation and direct body assistance are separate mechanisms: the former offsets gravity on selected bodies, whereas the latter directly changes free-body velocity.

> Direct body assistance corrects vertical velocity and roll/pitch rates once per controller cycle and blends horizontal velocity and yaw rate at each physics step. At scale 1, the blend sets horizontal velocity to the desired value. At scale 0.5, it retains half the current velocity and adds half the desired velocity at each of the four physics steps per control cycle. At scale 0, these direct velocity corrections are disabled; velocity can still change through physics and actuation. The assistance scale specifies a velocity-correction rule, not a measured support force.

## Section 3.2 terrain definitions P031 and P034

Before the equations:

> Terrain regions have configured walking-speed limits and semantic grades. Equations (1) and (2) define the terrain-difficulty proxy at each grid cell.

After the equations:

> The clip function maps the intermediate difficulty g to the final difficulty d within [0, 2]. Here, s is a slope proxy in radians, h is the sampled height range in metres, u is the population standard deviation of sampled heights in metres, and f is a semantic softness term. Heights are sampled at nine positions with offsets of −1.82, 0 and 1.82 m along each horizontal axis. The slope proxy is the arctangent of the gradient magnitude of the footprint-averaged elevation field on the 0.25 m grid. Terrain grades 0, 1 and 2 have softness values 0, 0.25 and 0.60, respectively. Grade queries include a 1.1 m buffer around patch boundaries. Route difficulty is sampled at intervals no greater than 0.125 m, using the nearest grid cell. Segment exposure equals segment length multiplied by mean sampled difficulty; total exposure R is the sum over segments. This terrain-derived proxy is not a measured probability of slipping.

Consider renaming the intermediate difficulty g if also using g as a gravity symbol; that optional change requires updating its appearances in both Equations (1) and (2) and the definitions together.

## Section 3.3 metrics opening P036

> The evaluator computes outbound distance D in metres, predicted outbound travel time T in seconds, nominal battery cost E in percentage points, and terrain exposure R. The initial heading is π/2 radians in every trial. Predicted travel time includes terrain-dependent translation, turns at 1 rad/s, and an acceleration allowance. The configured walking-speed limits for terrain grades 0, 1 and 2 are 0.75, 0.65 and 0.38 m/s, respectively.

In the battery-model paragraph, retain the verified coefficients and reserve rule. Replace its unclear closing sentences with:

> These coefficients are fixed modeling choices and were not fitted to electrical measurements. Because E depends on distance, time and turning, the four score components are not independent physical outcomes. No sensitivity analysis of score weights or reserves is performed. Differences in Q or nominal battery cost do not demonstrate physical battery savings, and positive actuator work is distinct from electrical battery consumption.

## Section 3.3 outbound and mission timing P042

> Shared preparation establishes the charging station and return route before each method searches for an outbound route. All methods use the same return allowance for a given case. The deadline applies to predicted arrival at the outbound destination. The separate motion diagnostic follows both outbound and return routes, and its successful mission time includes an 8 s modeled station-service interval. D and T describe the planned outbound route, whereas mission distance and elapsed time describe execution of the round trip. Unsuccessful executions may stop before completing either leg.

## Section 3.3 ranking paragraph P043

Replace the entire paragraph beginning “The front-runner differentiates…” with:

> Candidates are ranked lexicographically. Routes satisfying all three resource constraints rank ahead of routes violating any constraint. Raw excesses of at most 10⁻⁸ are treated as zero; larger positive excesses are divided by their corresponding constraint thresholds and summed. Among rejected routes, lower total normalized violation ranks first, with lower Q breaking ties. Among accepted routes, lower Q ranks first. A rejected route cannot replace an accepted incumbent.

This rule does not rank by the number of violated constraints. Keep the raw-excess tolerance separate from the Q-score tie tolerance used in the statistical analysis.

## Section 4.1 planner prose P046 to P049

> CLRP has three stages. The initial resource-aware search generates candidate corridors and uses time, nominal battery and terrain constraints to rank and refine them. Landmark search then adds route options using waypoints around obstacles and terrain boundaries. Final local refinement tests removal of internal points, movement halfway toward the projection on a neighboring segment, midpoint replacement, and coordinate moves.

> The search retains its best route, replacing it only when a candidate improves the ranking rule. Proposed routes must pass the common segment-clearance check before a new whole-route evaluation is counted. Repeated geometry reuses cached evaluations. The same evaluation and ranking rules apply to final refinement where that stage is enabled.

> Table 1 lists the selected time allocations, landmark cap, local step sizes and initial-search settings. These choices define the configurations evaluated in this experiment.

> Graph-edge checks and whole-route evaluations measure different work. Graph search can reject an edge before forming a complete route and retains states with different incoming headings and resource costs. Final refinement instead changes an entire waypoint sequence. Equal whole-route evaluation limits therefore do not imply equal numbers of geometric queries.

Retain Algorithm 1, whose substantive steps are supported. In Section 4.2, replace **“initial optimal path”** with **“best initial route.”**

## Section 4.3 budget and preparation P088 and P089

> Each method has a nominal search-time allowance of 2 s and a cap of 240 counted evaluations of complete collision-free routes. Initialization route evaluations count toward the shared cap. Geometrically rejected proposals and repeated routes with cached evaluations do not count as new whole-route evaluations. A method may terminate before either cap is reached when its search stages finish. PSO-C can exhaust the evaluation cap before the time allowance.

> Reported method search time includes its initial route search and subsequent improvement stages. Shared preparation occurs before method calls and includes scene construction, shared graph construction, return-route selection and precomputation of shared lower bounds. These common preparation costs are excluded from each method's reported search time.

## Section 5.1 map descriptions P092 and P093

> The study uses eight development maps with seeds 2130000–2130007 and 32 primary maps with seeds 2140000–2140031. Map families cycle through open, cluttered, rough and corridor, giving two development maps and eight primary maps per family. Each map spans −24 to 24 m on both horizontal axes.

> Open, cluttered, rough and corridor maps contain 5, 16, 7 and 4 generated obstacles, respectively; corridor maps also have two interrupted barriers. The four families contain 1, 2, 4 and 3 rectangular terrain patches, respectively. Patches use shallow terrain tiles, and their semantic grades affect configured walking speed and exposure. All six planners receive identical geometry and terrain within each case.

## Section 5.2 parameter selection P097

> Each of the four base methods is evaluated with two parameter profiles on the eight development maps. Selection first maximizes the number of accepted attempts, then minimizes mean Q among accepted attempts. Exact ties retain the default profile. The default profile is selected for all four base methods. Both CLRP variants inherit the selected settings for the stages they retain.

In the within-map averaging paragraph, consistently use **“jointly accepted repetitions.”** Repetitions characterize algorithmic variation on a fixed map and do not add independent maps.

## Section 5.3 paired score and bootstrap P102 and P104

Replace the first paragraph, retaining Equation (5):

> Score differences are calculated only for paired repetitions in which both CLRP and the comparison method return accepted routes. Attempts accepted by only one method and attempts rejected by both are counted separately. Equation (5) defines the relative score improvement, where Qc is the comparison-method score and Qv is the CLRP score. Positive values favor CLRP; negative values favor the comparison method. Absolute differences between Qc and Qv of at most 10⁻⁸ are counted as ties.

Replace the bootstrap paragraph with:

> For each comparison, we first average relative effects over jointly accepted repetitions within each map, then compute the mean and median of these map-level values. Using the bootstrap principle [11], we resample paired maps with replacement 5,000 times and report the 2.5th and 97.5th percentiles of the resampled mean. The random seed is reset to 41104 for each comparison. The intervals are descriptive, conditional on joint acceptance, and unadjusted for the five comparisons. A 0.5% relative-improvement threshold is used only as a descriptive guide to larger effects.

In the computing-environment paragraph, replace the final two sentences with:

> Runs occurred on a shared desktop with concurrent workloads. Recorded wall times describe this environment and do not measure deployment latency or dedicated single-core performance.

## Section 5.4 diagnostic setup and contact P108 to P111

> The motion diagnostic uses four previously evaluated maps, one per map family, with seeds 1670000–1670003. It follows the CLRP route from repetition 0 of each map and the saved return route to a charging station. Outbound lengths are 21.36, 22.30, 23.45 and 19.78 m; initial nominal battery allowances are 45%, 85%, 45% and 100%, respectively. These four diagnostic maps are separate from the 32 primary maps.

> Each mission is executed with full assistance and gravity compensation, 0.5-scale assistance and compensation, zero assistance with compensation, and zero assistance without compensation. All conditions use the same path tracker and a simulated execution limit of 180 s. Completion requires reaching the destination and returning to the station. Successful elapsed times include motion plus 8 s of modeled station service. The execution timeout is distinct from the planner's predicted outbound deadline.

> Gravity-compensation values are inspected after locomotion-controller initialization. In the no-compensation condition, all 18 leg-body compensation values are then set to zero. Four original executions requested without compensation were invalidated because initialization restored compensation; they were replaced by four verified reruns. The final comparison contains 16 valid executions, four per condition.

> Contact telemetry is sampled at every 0.004 s physics step. A selected foot geometry is counted as contacting external geometry when an available contact record has distance at most 0.002 m. Mean contacting feet is the average number of selected feet meeting this criterion per sample. The no-contact fraction is the proportion of samples with none of the six selected feet in contact. Other robot geometries are excluded from this detector. This criterion does not measure contact force or load-bearing support.

Keep the positive-actuator-work definition, which correctly applies positivity to force × velocity before integrating. State that the calculation excludes work introduced by direct body-velocity corrections.

## Section 6.1 PSO-C paired outcomes P138

> Among the 93 jointly accepted attempts, CLRP has lower Q in 33, tied Q in 27 and higher Q in 33 compared with PSO-C. One additional attempt is accepted only by PSO-C, none is accepted only by CLRP, and two are rejected by both methods. The conditional mean paired-map relative improvement is 0.690%, the median is zero, and the descriptive 95% bootstrap interval is [−0.255%, 2.312%]. The interval includes zero.

In the opening results paragraph, **“All rejected primary routes fail the predicted outbound deadline; battery and terrain-exposure limits pass”** is more informative than “violates a restriction on resources.”

## Section 6.2 shared preparation P168

Replace the preparation-time sentence with:

> Median shared preparation time is 0.715 s, with a maximum of 0.895 s, and is excluded from individual search times.

If an arithmetic mean is preferred, use **0.720 s** and label it explicitly as the mean. Do not relabel 0.715 s as a mean.

Remove the stray opening quotation mark in Section 6.2. Use **“All resource rejections occur on corridor maps”** and the fixed family names **open, cluttered, rough, corridor**.

## Section 6.4 Map 24 P212

> Map 24 belongs to the corridor family, and both methods accept all three repetitions. CLRP returns the same route in each repetition, with a distance of 20.803 m and a score of 1.310. PSO-C has a mean distance of 27.135 m and a mean score of 1.706. CLRP's predicted travel time, nominal battery cost and terrain exposure are 32.959 s, 15.446 percentage points and 1.012, respectively; the corresponding PSO-C means are 42.584 s, 20.066 percentage points and 1.665.

Keep the explicit statement that this example was selected post hoc for its largest positive map effect. It should not be presented as a typical improvement.

## Section 6.5 diagnostic interpretation P218 and P241

For the opening sentences:

> Full and 0.5-scale assistance each complete all four missions. Neither zero-assistance condition completes a mission within 180 s. Table 5 reports completion and six-foot contact statistics for the 16 valid executions. GC denotes leg-body gravity compensation.

For the closing paragraph:

> No contact at the six selected foot geometries is detected in any physics sample of the eight assisted executions. These results demonstrate route following with direct body assistance and do not validate propulsion through foot-ground interaction. Small planar displacements occur under zero direct assistance, but no mission is completed within 180 s with gravity compensation either enabled or verified disabled. The results characterize these four missions and do not estimate a general hardware failure rate.

## Section 7 acceptance and statistical interpretation P243 and P244

For the opening discussion paragraph:

> Under the tested settings, final local refinement increases acceptance from 90 to 93 of 96 attempts. The three additional acceptances are the three repetitions of one corridor map, seed 2140011. Removing landmark search retains 93 acceptances while reducing recorded computation. Compared with noP, full CLRP has lower Q in 57 jointly accepted attempts, 33 ties and no higher-Q attempts; compared with noL, the counts are 27, 57 and 9. These observations describe different effects on acceptance, score and search work. Incumbent retention prevents a worse-ranked route from replacing the retained route within a run, but independently executed stage-removal variants need not share identical search histories. An initial-route-only control and comparisons with matched effective search work would help separate initialization quality from later-stage effects.

For the second paragraph:

> The study does not establish a conditional mean paired-map score advantage for CLRP over PSO-C. The mean relative improvement is 0.690%, the median is zero, and the descriptive 95% bootstrap interval includes zero. This does not establish equivalence or inferiority. PSO-C accepts one additional scheduled attempt, and Map 24 strongly influences the positive mean. CLRP's separate comparisons with PSO-P and ACO-P have positive mean relative effects and zero medians. These findings concern the tested configurations; differences in initialization and representation prevent attributing all effects to representation alone. The five intervals are unadjusted for multiple comparisons and should be interpreted descriptively.

Elsewhere in the discussion, use these exact distinctions:

- **“The three repetitions characterize algorithmic variation within each map; the number of independent generated primary maps remains 32.”**
- **“The reported positive actuator-work calculation excludes work associated with direct body-velocity corrections.”**
- **“The study evaluates body-route planning and assisted execution with known map and pose inputs; it does not validate unassisted locomotion or sensor-based navigation.”**

## Section 8 conclusion

> In this 32-map primary test, final local refinement increases acceptance from 90 to 93 of 96 attempts; the additional acceptances are three repetitions of one corridor map. Landmark search retains the same acceptance count as its removal variant and provides a conditional mean paired-map relative score improvement of 0.924%, while mean search time increases from 0.196 to 0.376 s. These configurations therefore show different trade-offs among acceptance, score and computation. Against PSO-C, CLRP's mean paired-map relative improvement is 0.690%, its median is zero, and the descriptive 95% bootstrap interval includes zero. The study does not establish a score advantage over PSO-C, which accepts one additional scheduled attempt.

> A separate 16-run diagnostic completes all four missions with both full and 0.5-scale direct body assistance. Both zero-assistance conditions complete none and time out at 180 s, with gravity compensation enabled or verified disabled. No foot contact is detected by the six-foot criterion in any assisted execution. These observations distinguish constrained body-route acceptance from validation of unassisted locomotion. The reported nominal costs and planning effects apply to the specified simulation model and objective, without physical or electrical validation.

## Final editing checks

After applying the passages, add the correct affiliation below the author name, standardize punctuation and units, remove leftover numbered fragments, and re-export the whole paper to PDF. Keep text at or above 10 pt and verify Times New Roman embedding. Reflow the references so [11] stays together and does not occupy a nearly empty final page. Do not infer that the earlier nine-page manuscript's formatting audit also applies to the latest ODT.
