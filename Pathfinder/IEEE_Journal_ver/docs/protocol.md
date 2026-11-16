# Hot-motor routing development protocol

## Question

When two starts have the same average and maximum motor temperatures, does knowing which motors are warm change the route choice and increase completion within modeled thermal limits?

## Connected-map development pilot

- One continuous heightfield contains two mirrored branches around a divider. Both branches begin on the same flat landing and end at the same goal. They have 6 m curved entry and exit sections and a 3 m bank section. The goal is reached when the chassis enters a 0.55 m radius around the goal.
- Both routes use the same joint-actuated crawl controller, which uses simulated body state and terrain height to place feet and distributes a desired chassis wrench through the stance-leg joint torques. The free chassis is integrated by MuJoCo. The route controller and geometry were tuned on this development scene. A shorter 4 m turn caused a fall on the left branch.
- The runner profiles both routes at nominal torque, then replays every route under each of the two mirrored warm starts. The controller and thermal comparison are shared across both temperature conditions. The route scorer uses whole-route torque traces, including entry and exit. The two centerlines are fixed candidates. Prediction uses nominal torque traces while execution feeds back applied torque and derating.
- The connected pilot uses known terrain geometry and a simulated body-state estimate. The foot-contact force allocator uses a regularized least-squares wrench estimate followed by unilateral and friction limits in world coordinates. Foot height is interpolated from the same grid as the MuJoCo collision surface. There is a small approximation on the sloped transition cells.
- The trial records body position, sampled foot-contact count, torque, and temperature from start to termination. Centerlines and the terrain grid are included with the recorded traces.

The initial connected run uses the planar pilot's thermal parameters, which were retained after the four warm executions reached the modeled limit. A separate sensitivity run multiplies the assumed heating coefficient by 0.55. That factor was selected after inspecting the nominal connected torque profiles. Both settings are development evidence.

## Asymmetric-map benchmark

The [benchmark configuration](../experiments/asymmetric_benchmark.json) fixes six new, hand-designed maps before any of their trajectories are run. The maps are variants of the same two-branch topology, with unequal banks, unequal branch offsets, or banks that begin at different positions. They were held out from controller tuning. The model, controller, four decision methods, warm starts, 70 °C stop limit, deadline and goal tolerance come from the connected pilot.

The thermal grid crosses three relative heating rates (0.45, 0.55 and 0.65 of the original setting) with three cooling time constants (80, 100 and 120 s). Heating multipliers scale the temperature rise rate at the reference torque, so the equilibrium temperature rise is scaled by both the heating multiplier and the ratio of time constants. This keeps the heating rate fixed across each cooling sweep. The range brackets the earlier development setting and has no hardware calibration.

- Run one nominal physics profile for each branch on each map. These profiles are shared inputs to the planners.
- Evaluate both branches for each map, thermal setting and starting state, for 216 scheduled branch outcomes. Where integrating the nominal torque trace never activates thermal derating, the deterministic nominal trajectory and its temperature reconstruction give the same outcome as a warm physics replay. Otherwise rerun physics with temperature-dependent torque limits. Record the evaluation route in each outcome.
- Compare the four decision methods on the same 108 starts each. Count a rejected plan as an incomplete start and report it separately from selected routes that fail in execution.
- The unit for paired comparisons is the map. Average completion over the two starts and nine settings on each map before resampling maps for descriptive intervals. The hand-designed maps do not provide a representative terrain sample. Report raw counts by thermal setting and how often the per-motor method chooses opposite branches for the paired warm starts. Those reversals can occur even when both routes would complete.

This benchmark checks the two-route mechanism across controlled map and thermal variations. The route-network study below carries motor temperatures through successive route choices.

## Route network and reactive slowdown

The [network configuration](../experiments/network_study.json) defines two new courses with three successive choices around dividers. Each course is a single MuJoCo heightfield with six directed edges and eight possible complete routes. All edge profiles are measured by nominal joint-actuated walks. The planner predicts each edge from a standalone profile and the incoming motor temperatures, then carries the 18 predicted temperatures, elapsed time and peak temperature into the next junction. It discards a partial route only when another label at that junction is at least as good on time, peak and every terminal temperature. It chooses the lowest predicted mission peak among routes that meet the modeled temperature and time limits.

Four methods cross the fastest nominal route or the per-motor route with the nominal speed or a reactive speed policy. The policy uses the hottest motor, begins ramping to 65% of the nominal command at 67 °C, and resumes the nominal command at 65.5 °C. A full ramp takes two seconds. The gait stays a crawl, and the commanded speed also scales foot placement lookahead. Both slowdown methods keep their planned route. The combination uses the same per-motor route as the fixed-speed method and can only slow down after that route is admitted. It does not plan routes that are feasible only with slowdown.

Every mission replay walks continuously through both intermediate junctions to a common goal. Motor state, gait phase and robot motion all persist through junctions. Standalone edge profiles include a starting settle and terminate inside the goal tolerance, so their concatenated predictions are approximations of the continuous mission. All methods have the same 440 s mission deadline, nominal gait, torque derating and 70 °C stop limit. The four modeled thermal settings and two initial temperature patterns are fixed before execution. Each method is assessed on the same 16 starts. Identical route and speed policies share a deterministic physics replay.

The benchmark reports paired completions, thermal stops, deadline failures, rejected routes, and slowdown activations. Completion requires entering the shared goal region below the modeled limit and within the deadline. The slowdown rule and thermal settings are fixed development choices. The two courses support descriptive comparisons in simulation.

## Joint route and speed planning

The [route-and-speed configuration](../experiments/route_speed_study.json) reuses the 16 matched network starts and their original four baselines. Each directed edge has profiles at 100%, 80% and 65% of the nominal speed command. The 12 nominal profiles come from the verified reference run and 24 lower-speed profiles are newly simulated. Edge durations and heat come from the measured simulated torque traces. The planner may choose a slower speed even if its peak temperature is already below the limit because predicted peak temperature is its primary objective.

Two new methods use the same per-motor thermal search and the same speed options. One plans speeds along the fastest nominal route. The other searches all edge and speed combinations. Both use the same 440 s deadline and 70 °C limit as the original experiment. The selected speeds are scheduled before departure. During continuous replay the controller switches the speed target at each junction, using a slew rate of 0.5 nominal speed fractions per second. Motor state and gait phase persist across the entire mission. Nominal-speed decisions matching a verified original route and controller use the original execution trace.

Edge profiles start from a stationary pose and use one speed. Their thermal forecasts omit transition effects and temperature-dependent changes in realized torque. A full mission replay tests those approximations. All attempted missions, thermal stops and planning rejections enter the denominator. This extension reuses both courses and the four thermal settings, so it is a paired follow-up on the same benchmark.

## Thermal margin calibration and test

Thermal headroom is the difference between the modeled motor limit and the predicted peak for a complete route. A margin is a minimum headroom requirement. For example, a 0.75 °C margin under a 70 °C limit admits forecasts strictly below 69.25 °C. The continuous simulation still stops at 70 °C.

The two previous network courses provide development data. The calibration uses the saved fixed-speed per-motor, fastest-route planned-speed, and joint route-and-speed forecasts and their physics outcomes. Repeated decisions that reuse one execution contribute one record, using the lowest forecast when predictions differ. The calibration rounds the largest observed underprediction up to the next value on the prespecified margin grid. A thermal-stop record contributes the peak observed through the stop. The eventual peak for a full walk on that route is unknown.

Before any new trajectories, the [test configuration](../experiments/thermal_margin_study.json) fixes three new networks, four simulated thermal settings and the margin grid from 0 to 2 °C. The maps vary left and right banking, bank position, branch offsets and stage lengths. The same two warm starts and three planning policies give 72 decisions. The controller, 440 s deadline, and thermal stop criterion are shared. Test outcomes remain separate from the development-selected margin. The courses were constructed for this study.

Each policy minimizes predicted peak temperature first and predicted travel time second within its action space. Tightening the common peak threshold cannot expose a different route with a lower predicted peak, because that route would already have been preferred. The margin therefore filters the zero-margin decisions. Each distinct zero-margin plan is replayed in continuous physics once, and the full sweep reuses that outcome wherever the plan is admitted. A finishable rejection means a plan blocked by the margin that its replay shows could complete. Cases with no zero-margin plan have no observed execution outcome.

## Earlier planar pilot

- The robot walks under gravity and ground contact using 18 joint torque commands. Its free body is initialized before the trial and then integrated by MuJoCo. Each trial includes a two-second settling period.
- Each corridor is a separate straight planar scene with a fixed lateral slope. The two scenes represent alternative branches with a common travel distance. Entry and exit turns, continuous branch geometry, and online replanning are outside the current pilot.
- A nominal-torque walk on each corridor provides a time series of per-joint RMS torque. Each method receives the same two profiles. The pilot scores candidate routes from these traces. It does not search a terrain graph yet.
- Temperature follows a first-order heating and cooling model with squared torque as the heating input. Replay integrates temperatures from the torque actually applied, reduces available torque above the derating threshold, and stops at the first sample at or above the temperature limit. Temperatures and thermal protection settings are hypothetical.
- For each warm-start pattern, execute both candidate routes with the same controller. Every method's selected route is evaluated using the matching execution. The comparisons are deterministic and paired. The two starts are development cases.
- A trial completes when the chassis passes the target distance before the deadline, without exceeding the modeled thermal limit, drifting outside the corridor, falling, or registering chassis-ground contact. Foot contact counts, position and torque are recorded every 20 ms. Chassis contact is checked at the 2 ms physics step. Nominal walk means that no simulated temperature or derating is applied.
- The per-joint method retains the starting temperature of every motor. The maximum-only and mean-only baselines initialize each motor with the corresponding scalar summary and use the same per-joint torque profiles. The time-only baseline uses nominal duration. Thermal-aware methods rank predicted feasibility, peak temperature, and duration in that order. Actual executions always begin with the true per-joint starting temperatures.

## Before confirmatory evaluation

Verify CAD joint frames, limits, and mass properties. Check the route follower on asymmetric terrain and record its failure envelope before freezing the controller. Use documented actuator parameters or sweep plausible values for heating, cooling, and derating. Confirm that joint loading asymmetry is repeatable without tuning to the final terrain set.

Freeze the controller, parameters, methods, outcome rules, and tuning worlds before using held-out terrains. Use a connected route graph with alternative ways to distribute joint loads. A route history must carry the estimated joint temperatures through edges, so different arrivals at the same position can leave different routes feasible. Compare with an energy-only route choice and a controller that reacts to overheating on a fixed route. Report paired goal completion, rejected plans, peak temperature, and added travel or compute time across independent worlds. The claim should be limited to the simulated thermal and locomotion models.

## Related work

- Čížek et al. measured slope-dependent load distribution and servo overheating in HAntR. [IEEE Access paper](https://comrob.fel.cvut.cz/papers/access21hantr.pdf)
- Wan et al. use motor temperatures to adapt quadruped locomotion and identify planning as future work. [Thermal-aware locomotion preprint](https://arxiv.org/html/2605.27046v3)
- US9821461B1 describes predicting overheating and selecting a safe walking trajectory. [Patent](https://patents.google.com/patent/US9821461B1/en)

## Thermal margin transfer

The [transfer configuration](../experiments/thermal_margin_transfer.json) evaluates the development-selected 0.75 °C margin on three fresh, hand-designed courses. Two courses have three stages and the third has four stages, with 16 route combinations. Geometry, thermal settings, and margins of 0, 0.50, and 0.75 °C are fixed before running the new profiles. The calibration still uses the original 19 development traces. Results from the first margin test informed the choice to concentrate the thermal settings near slower cooling. That earlier test is outside this transfer set.

All three courses use a common 550 s deadline to accommodate the longer course and preserve the same limit across methods. The controller, 70 °C physical stop, warm-start vectors, and speed options follow the earlier test. The analysis reports the two shorter courses and the longer course separately, so differences by course length remain visible. Course length and terrain geometry vary together. Thermal parameters are hypothetical, and this is a transfer check on constructed courses.

## Continuous route forecasts

The comparison uses all distinct admitted route and speed schedules from the thermal-margin transfer set. It profiles each schedule at nominal torque limits in one continuous walk, carrying the robot state, gait phase and speed ramps through the junctions. Nominal profiles omit temperature feedback and derating. Each profile is reused across the applicable warm starts and thermal settings. Both forecasting approaches integrate the same thermal model and use the same starting motor temperatures. Their target is the observed hottest-motor peak in the saved thermal replay.

Compare absolute errors on completed replays, where a full-walk peak is available. Include thermal-stop replays in the admission comparison at the three original margins. Count each distinct replay once and retain any failed nominal profile as an unavailable forecast. This is a diagnostic on the existing routes selected by the branch-profile planner. It evaluates a second admission check and leaves alternate-route selection and profiling all graph paths outside the experiment.

## Mission completion with and without motor identities

The [mission completion configuration](../experiments/mission_completion.json) freezes six new networks before profiling. Three offer a single choice between three branches. Three offer successive choices combining a three-way and a two-way split. A center branch is traversable on all six networks. Earlier networks offered only two branches at each choice. All courses remain constructed banked-heightfield scenarios.

The primary outcome is goal completion before the course deadline and below 70 °C. The prespecified practical target is a gain of at least 10 percentage points with a shared two-second online search budget per decision. Offline edge profiling and conversion of torque traces into thermal models are common to both planners and outside that budget. The two allowed edge speed commands are 100% and 65% of nominal. Both methods search the same feasible route and speed combinations and use the same forecast ceiling of 69.5 °C.

The per-motor method receives the true starting temperature vector. The anonymous method receives the same temperatures without the side assignment. It evaluates both mirrored assignments and ranks by their average predicted peak. This baseline knows the two possible warm-side patterns and can choose its route and speeds in advance. Both controllers use the true hottest-motor temperature during the walk to trigger the same reactive slowdown. At each step, the commanded speed is the lower of the scheduled and reactive speeds. That controller can slow a route selected by either planner. Neither controller changes gait or replans the route during execution.

The two starts in each thermal condition permute the same temperature values. Three simulated thermal conditions and two starts per condition give six matched starts per course and 36 overall. Identical schedules for the same start share one continuous physics replay. Planning rejections, timeouts and failed walks remain in the denominator. Mean paired completion difference weights the six courses equally. The descriptive interval resamples courses and describes variability across this small, constructed test set. These thermal models use assumed parameters.
