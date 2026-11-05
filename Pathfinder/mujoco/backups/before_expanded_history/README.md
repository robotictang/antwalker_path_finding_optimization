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
| Fastest / lowest energy | 71.5 m | 73.1 s | 25.9% |

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
