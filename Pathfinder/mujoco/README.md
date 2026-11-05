# Research lab and method comparison

Run `./run_research_lab.sh` for the separate localhost research console at
**http://127.0.0.1:8771**. It launches paired comparisons of distance, terrain,
energy and sampled-weight baselines against a seeded constrained Pareto method,
plus independent gait calibration. Select a saved run to refresh the comparison
dashboard. All figures come from saved experiment records; failed and rejected
attempts remain visible. This lab defaults to walking-only trials and does not
write to the existing live mission history. Research dependencies add SciPy;
see `research/requirements.txt`.

See [the lab guide](research/README.md), [feature boundaries](research/IMPLEMENTATION.md)
and [the four-paper review](research/research_review.md). The proposed method is
an experimental adaptation; no claim of outperforming the baselines is assumed.

# Terrain grades and named roads

The current terrain policy has three unevenness grades, shared by navigation,
route time/energy estimates, automatic locomotion, and the website:

| Ground | Behaviour | Speed cap |
|---|---|---|
| Mild unevenness | Traversable with legs; shallow gravel/cobbles | 0.75 m/s |
| More uneven | Traversable with a slower leg gait; cobbles up to 10.5 cm | 0.38 m/s |
| Extreme unevenness | No entry; plan a safe detour around the full foot envelope | 0 m/s inside |

Smooth roads retain the 1.65 m/s wheel limit. The approach to extreme terrain
is capped at 0.50 m/s (or the lower applicable terrain cap). The swept-radius
clearance prevents entry before reaching the extreme surface. Extreme regions
remain blocked even with a manual wheel/leg override. A goal in an extreme
region produces an explicit no-safe-route error. These are configured capability
limits for this assisted simulation, not measurements of hardware capability.

Six of the twelve road patches are more uneven; the others and existing biome
zones are mild. Three extreme washed-out road sections contain physical rock
piles, warning boards, and matching no-go regions in the planner. Physical
rough surfaces, gait foot-height lookup and terrain classification agree.
Slower travel increases predicted time and hotel energy; task admission still
budgets destination plus a feasible charger return and safety reserve.

Eight roads are now named **Durian Road, Banana Road, Wan Road, Khem Road,
Potato Road, Tomato Road, Fishy Road, and Tea Road**, with road decals in the
3D scene and matching names in the browser map. The website now shows grass,
road shoulders/centre markings, trees, a river bank, a north arrow and 10 m
scale, plus green mild terrain, amber uneven terrain and red-hatched no-go
terrain. Rounded perimeter hills replace the old cylinder pillars. Existing
robot meshes, URDF and persistent mission history remain intact.

Backup: `backups/before_terrain_grades/`. Run `validate_terrain_grades.py` for
clearance/terrain/road-name checks. `outputs/terrain_grades_mission.json` records
the six-site physics run, terrain-grade maximum speeds, no-go entry count and
speed-limit checks. Earlier release reports and numerical examples below refer
to earlier terrain; use current reports for this scene.

Final validation passed: 144 objective-route checks; all six places reached in
729.2 simulated seconds with three charging stops. No obstacle contacts, blocking
penetrations, route failures, solver warnings, extreme-terrain entries or speed
limit violations occurred. The main optimizer avoided the more uneven sections;
a separate direct traversing test covered 1,100 frames on more uneven ground at
up to 0.38 m/s, with zero speed violations and minimum foot clearance +3.28 mm.
The full mission recorded mild-terrain speed up to 0.75 m/s and minimum foot
clearance +7.17 mm. Two protective braking events replanned and resumed.
See `outputs/terrain_grades_final_validation.json` for exact results and hashes.

---

# Six-site expedition and automatic charging network

The live panel now has six destination buttons: Forest, Quarry, Marsh, Desert,
River camp, and Ridge outpost. Keypad 1–4 retains the original site controls;
use the website buttons for sites 5 and 6. There is one **Charge · best station**
command (also KP0), with no numbered station dispatch buttons.

Three physical stations are available: Central plaza, West service bay and
East service bay. A charging request searches collision-free approaches to all
stations, excludes any route whose predicted consumption plus 25% allowance
and 2% arrival reserve exceeds the battery, and ranks the remaining routes by
the current objective (Balanced uses the selected distance/time/energy weights).
The active route names the selected station and lists the minimum battery
needed for each candidate station. The best station can change after obstacles
or preferences change. A geometrically nearest station need not have the best route.

Task admission and periodic checks budget for the destination plus a return to
the lowest-energy reachable station, with the existing allowance and task reserve.
If that budget is insufficient, charging starts before departure or during the trip.
The robot charges to 100% and replans toward its queued destination. It stops
with an explicit error if no station can be reached safely. Charge completion
and departure work at all three stations, including the central plaza's required
front entrance. Battery and speed coefficients remain demonstration assumptions.

The 96 × 96 m scene contains 72 irregularly scattered blocking road hazards
(replacing the previous 40 ordered outer-road objects), plus the existing inner
road debris. Seeded sampling varies spacing, lateral offset, orientation, size,
and height. Each placement preserves connectivity among the depot, all six
sites and all three stations with the full-leg clearance envelope. Twelve rough
road sections now include 216 physical shallow cobbles, gravel and skewed ruts.
Terrain costs and automatic wheel/leg transformations use these same sections.
These shallow rigid surfaces approximate rough ground; they are not deformable mud.
The supplied robot meshes and URDF have not been edited.

History remains append-only in `outputs/mission_history.sqlite3`, shared by the
canonical and Desktop launch copies. Station selection events include all station
estimates, and trip records identify named origins and destinations. Test runs
use a separate SQLite file. Backup: `backups/before_charging_network/`.

Validation: `python3 validate_charging_network.py` checks the actual scene, safe
station selection, insufficient-energy rejection, and all-station resume logic.
The extended headless mission uses `--sequence 5,6,1,3,2,4` and reports contacts,
transformations, charging, arrival and solver diagnostics.

Latest validation result: all 144 destination/objective path checks passed. The
686.7-second simulated mission reached all six sites and completed three charging
stops (West, West, East), with zero obstacle contacts, zero blocking-obstacle
penetrations, zero route failures, and zero solver warnings. Two protective
brakes replanned and resumed successfully. Minimum battery was 15.48%. The minimum
foot/surface measurement was -2.02 mm (soft-contact compliance on shallow terrain),
so this is not a claim of mathematically rigid, zero-penetration foot contact.
The faster terrain lookup matched the prior calculation exactly at 5,000 points.
See `outputs/charging_network_final_validation.json` for the verification manifest.

The following sections document previous releases. Their numerical route examples
and four-place/one-station counts predate this scene; use the current panel and
latest `outputs/charging_network_*.json` reports for current results.

---

# Expanded route explorer and permanent history

Open **http://127.0.0.1:8767** after `./run_simulation.sh`.

## What changed in the map

The navigable area is **96 × 96 m**, almost twice the previous 68 × 68 m area.
Twelve new road links include an outer loop, north/south alternatives, and site
connectors. The new roads are **8.4 m wide**. Twenty additional physical rocks and
twenty cones sit on the new roads; the original obstacles and terrain remain.
The original robot meshes and assembly are unchanged. `outputs/expanded_world_overview.png`
shows the actual expanded MuJoCo scene.

The temporary roadwork detector still brakes and replans around a newly blocked lane.
Staging now verifies that all places and the charging station remain connected,
and avoids the station's narrow entrance corridor. Energy feasibility is still checked
separately; obstacle placement never disables charging safeguards.

## Understand the three screenshots

1. **Records and route candidates:** the old strip only displayed four recent events.
   It is replaced by permanent trip/plan/event/comparison history with **From → To**,
   outcome, objective and costs, filtering, more-records paging, and full CSV export.
   The database is `outputs/mission_history.sqlite3`. It survives browser refresh,
   robot reset, and simulator restart. Existing live events were recovered where
   available; missing historical origins/destinations are explicitly marked unavailable.
2. **Weights:** priorities affect **Balanced** only. The former Fastest mode ignores
   balanced weights. The new sliders immediately rescore a frozen comparison; **Use
   these priorities on robot · switch to Balanced** explicitly applies them to the
   actual mission. Merely exploring the sliders does not dispatch or move the robot.
3. **Four objective cards:** these are selection rules, not a promise of four different
   roads. Several rules can pick the same candidate. During a charging diversion the
   interface now shows a single **active charger route**, explains the safety override,
   and retains the requested preference for the resumed task. It no longer highlights
   Fastest next to an energy-only charging comparison.

## An easy multi-objective demonstration

Scroll to **Understand the optimization** and click **Show me an example**.
The start stays at Origin depot and the destination stays Quarry:

| Candidate | Distance | Estimated travel | Estimated battery |
| --- | ---: | ---: | ---: |
| R1 | 47.3 m | 88.4 s | 29.3% |
| R2 | 70.2 m | 72.4 s | 25.5% |

Click **Shorter road**: balanced priorities 90/5/5 select R1.
Click **Arrive sooner**: 5/90/5 select R2. It is 22.9 m longer, but about 16 s
quicker and uses 3.8 percentage points less battery because it avoids slow walking.
**Save battery** also picks R2 for this example, and the page explains why.
The chosen route is highlighted and the score table updates immediately.

You can choose **Forest → Marsh** or any other distinct pair and compare without
teleporting the actual robot. This is a fixed-start, full-battery, automatic-terrain
planning snapshot. Live obstacle/map changes do not silently alter it; compare again
to refresh the snapshot. Every comparison and explicit priority preset is saved.
The normal destination buttons still dispatch from the robot's actual position.

Trip requests and arrivals are stored separately from planning comparisons, so previewing
Forest → Marsh is never reported as a real completed trip. Arrivals contain actual
travel distance/time/energy; selected plans contain estimates. History is append-only
for normal operation; resetting creates a record rather than deleting earlier results.
Headless tests use no live history unless `--history-db PATH` is supplied.

## Added validation

`python3 validate_explorer.py` checks all 80 objective routes across the 20 ordered
base/site pairs, frozen-comparison priority changes, controller reset/database reopen,
incremental history retrieval and CSV origin/destination labels. The four-place physics
run is recorded in `outputs/expanded_mission_validation.json`; its test-only history
is `outputs/expanded_validation_history.sqlite3`, separate from real live history.
Existing algorithm, energy-budget, transformation and collision checks still apply.
Backups of the previous application/model are in `backups/before_expanded_history/`.

---

# Multi-objective hexapod path planning

Run `./run_simulation.sh` and open **http://127.0.0.1:8767**. Choose any of the four
places. **Balanced** is the default objective; automatic terrain transformations,
roadwork detection/avoidance, route previews, and destination arrival remain active.

## Objectives and preference controls

The control panel compares **Balanced**, **Shortest**, **Fastest**, and **Lowest
energy** routes from the same start, with distance, travel time, estimated energy,
walking distance, and transformation count. Three sliders set the distance/time/energy
weights for balanced planning. Apply weights to stop, recheck energy, and replan.
The panel shows the supported non-dominated candidates and their energy feasibility.
Different objectives may legitimately select the same route.

The planner runs heading-state A* scalarizations for each pure objective, the user's
weights, and three mixed preferences, then removes dominated candidates. The selected
route minimizes the chosen normalized score **among energy-feasible candidates**:

`J = wd × distance/50 m + wt × travel_time/90 s + we × energy/30%`

Weights are finite, nonnegative, and normalized to sum to one; the default is equal
weights. Time includes surface speed, turns, transformation and stop/start allowance.
Energy includes driving/walking distance, elapsed time, turns, and transformations.
The heuristic is a nonnegative lower bound. When SciPy is available, cached 2-D
Dijkstra terrain/obstacle distances tighten it; otherwise the geometric lower bound
is used. Continuous shortcuts are checked against
the swept footprint and accepted only when they do not increase the selected score.
The final distance candidate is also compared under the same objective model.

This produces a **sampled supported Pareto set**, not every possible non-dominated
continuous path. A* optimality refers to each declared scalarized grid objective;
the robot and travel-time model remain assisted demonstration approximations.

Quarry baseline, from the depot before roadwork/charging interruptions:

| Objective | Distance | Estimated time | Estimated energy |
| --- | ---: | ---: | ---: |
| Balanced / shortest | 47.3 m | 88.4 s | 29.3% |
| Fastest / lowest energy | 70.2 m | 72.4 s | 25.5% |

The longer bypass uses less walking and fewer transformations. Prefer energy/time
more strongly to select it; equal balanced weights favor the shorter alternative.
The candidates for all four places are saved in
`outputs/multiobjective_algorithm_validation.json`.

## Charging is a hard feasibility constraint

Before following a destination route, the battery must cover:

`1.25 × (energy to destination + minimum-energy destination-to-charger route) + 6% reserve`

The destination-to-charger route respects the station's front entrance. This avoids
finishing a delivery with no way back to charge. Candidate routes that fail this
constraint cannot be selected, even when they have the best objective score.

If no task candidate fits, the robot queues the destination and plans a minimum-energy
route to charge first. The charging route itself must fit
`1.25 × charger_route_energy + 2% reserve`. It charges to 100%, holds green for 2.4 seconds,
then generates a fresh route from the station to the original destination.

The task budget is checked once per simulated second and after replanning, obstacles,
objective changes, or mode overrides. Below 20% remains a fallback charging trigger;
energy feasibility often sends the robot to charge **above 20%**. While idle, it
returns before the charger requirement plus a 1% departure buffer becomes unaffordable.
If even a fully charged departure cannot cover the task and return, it reports an
infeasible task rather than looping through charging forever.

**Physical limitation:** a robot cannot reach a charger if its remaining energy is
already too low, or no safe route exists. Such requests stop with an explicit reason
and require assistance; the controller does not drive toward an unreachable charger.
These checks are conditional on the declared model/map and do not establish a real
hardware energy guarantee.

## One shared energy model

Prediction and actual simulated consumption use the same coefficients, in percentage
points of nominal battery capacity:

| Component | Consumption |
| --- | ---: |
| Driving | 0.25% / m |
| Walking | 0.70% / m |
| Electronics / elapsed operation | 0.015% / s |
| Turning | 0.08% / rad |
| Each transformation | 0.50% |
| Planned start/stop allowance | 0.10% |

The live meter integrates actual displacement, heading change, operating mode, elapsed
time and transformation starts. Energy use/charging are tracked in an auditable ledger.
The former accelerated first-trip and cheaper emergency-return drain rates are removed.
These are explicit simulation coefficients, not measured motor/battery data. Charging
remains accelerated at 22 percentage points/s for demonstration.

Click **Demo: reset & plan Quarry at 45%** to see the robot recognize insufficient
round-trip task energy and charge before beginning the delivery. This is an explicit
initial-state test; normal dispatch starts with the current battery and uses no hidden
first-trip drain multiplier. Reset demonstration returns to the depot at 100%.
Amber indicates an energy-priority charging diversion; below 20% pulses red.

## Controls

Use the browser buttons or **numeric keypad**, leaving regular letters and top-row
numbers to MuJoCo:

| Key | Action |
| --- | --- |
| KP1–KP4 | Choose Forest / Quarry / Marsh / Desert |
| KP0 | Charge |
| KP5 | Cycle balanced / shortest / fastest / energy |
| KP6 | Cycle camera |
| KP7 | Manual transformation override |
| KP8 | Restore automatic terrain selection |
| KP9 | Force 18% battery for testing (can be unreachable from remote positions) |
| KP decimal | Cancel; charging safety takes priority |

Sliders and explicit objective buttons are available in the panel. Keypad controls also
work while it is focused. User input and browser commands are applied on the simulation
thread. The panel binds to localhost; no external service is required.

## Terrain, navigation, and model scope

Four gravel/rut road sections, 12 added rocks and 12 cones, and the marked smooth bypass
remain. A striped roadwork barrier is staged on a planned lane only after a safe detour
is verified. This temporary demonstration work zone clears after 90 simulated
seconds; its removal updates the map and rechecks any paused task. Permanent scene
obstacles remain fixed. Its simulated proximity detection at 8 m updates the map and triggers a
new collision-checked and energy-checked plan. This is not a real LiDAR perception stack.

Driving speed is 1.65 m/s and walking 0.75 m/s. Rough ground triggers a stationary
3.6-second wheel/leg transformation with an automatic close-up camera. Navigation uses
a 0.25 m grid, a 1.82 m full-leg swept radius, 0.12 m tracking margin, continuous segment
checks, and a braking clearance guard. Actual physics includes millimeter-scale support
contact compliance; chassis movement/attitude and transformation joints remain assisted.
Suspension, individual gravel and ruts are visual details; pads are physical supports.
There is no deformable terrain or validated hardware balance/traction model.

Original six STL files and source URDF remain unchanged. Procedural wheel/battery/status
features are retained; the actuator derivative remains the previously authorized copy.
The source-only option remains `source_only_hexapod.xml` / `./view_source_asset.sh`.
Previous code is backed up under `backups/before_multiobjective/`.

## Reproduce validation

```bash
python3 validate_multiobjective.py
python3 validate_energy_guards.py
python3 preview_multi_place_mission.py --headless --steps 50000 --sequence 2,3,4,1 --report outputs/multiobjective_full.json
python3 preview_multi_place_mission.py --headless --steps 24000 --dispatch 2 --initial-battery 45 --stop-on-arrival --report outputs/multiobjective_precharge.json
python3 preview_multi_place_mission.py --headless --steps 200 --dispatch 1 --initial-battery 2 --report outputs/multiobjective_unreachable.json
```

The algorithm validator compares all four scalarizations against independent Dijkstra,
checks actual-map Pareto candidates and continuous clearance, and verifies energy
accounting and invalid-weight rejection. Guard tests cover an infeasible full-pack task
and idle charger reserves. Mission reports include every planning energy budget,
charging reason, route alternatives, consumption ledger, and contact/solver checks.
CLI options include `--route-mode balanced|shortest|fastest|energy`,
`--weights DISTANCE TIME ENERGY`, `--initial-battery`, `--no-roadwork`, and `--no-panel`.
