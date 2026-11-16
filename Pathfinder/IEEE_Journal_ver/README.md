# Pathfinder thermal routing

A simulation-only study of whether knowing which hexapod motors start warm changes the route the robot should take. This project is independent of the earlier IJ3C experiment. The current development pilot has two banked routes in one MuJoCo scene with a shared start and goal.

## Run the pilot

From this directory, with Python 3.12 and `uv` installed:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m thermal_pathfinder.connected_pilot
```

The default configuration is [experiments/connected_pilot.json](experiments/connected_pilot.json). Use `--config` and `--output` for alternate runs. The runner saves the scene, planning decisions, execution outcomes, and traces in [results/connected_pilot](results/connected_pilot). Inspect the scene with `.venv/bin/python -m mujoco.viewer --mjcf=results/connected_pilot/scene.xml`.

## Run the mission-completion benchmark

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_completion --workers 12
.venv/bin/python -m thermal_pathfinder.mission_analysis
```

The [configuration](experiments/mission_completion.json) freezes six new courses, two-second online search budgets, and a minimum worthwhile gain of 10 percentage points. Both planners choose routes and speeds and can slow down during execution. They differ in whether the initial temperatures identify the individual motors. The per-motor planner completed 32/36 starts and the baseline completed 31/36, below the 10-point target. See the [results report](docs/mission_completion.md) and [protocol](docs/protocol.md#mission-completion-with-and-without-motor-identities).

## Run the continuous-profile forecast comparison

Run the thermal-margin transfer experiment first. The forecast comparison profiles each distinct route and speed schedule from that run as one nominal walk, then applies the same motor model and warm-start temperatures used by the stitched branch forecasts.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.continuous_forecast --workers 12
```

The analysis compares peak-temperature errors on completed thermal replays and admission at 0, 0.50, and 0.75 °C of headroom. Continuous profiles reduced mean absolute peak error from 0.140 °C to 0.028 °C across 22 completed replays. See the [results report](docs/continuous_forecast.md) and [protocol](docs/protocol.md#continuous-route-forecasts).

## Reproduce the thermal-margin transfer test

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.margin_profiles --config experiments/thermal_margin_transfer.json --output results/thermal_margin_transfer --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.margin_study --config experiments/thermal_margin_transfer.json --output results/thermal_margin_transfer --workers 12
.venv/bin/python -m thermal_pathfinder.margin_transfer
```

The [transfer configuration](experiments/thermal_margin_transfer.json) fixes the 0, 0.50 and 0.75 °C margins and three fresh courses. The four-stage course has 16 possible routes. Both nonzero margins screened all four observed thermal stops, and 0.50 °C retained four more completions than 0.75 °C. See the [results](docs/thermal_margin_transfer.md) and [protocol](docs/protocol.md#thermal-margin-transfer).

## Run the thermal-margin study

Run the route-and-speed study first to reproduce the development data. The margin study uses a separate set of three courses.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.margin_profiles --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.margin_study --workers 12
.venv/bin/python -m thermal_pathfinder.margin_analysis
```

The [configuration](experiments/thermal_margin_study.json) fixes the test courses, thermal settings, and admission thresholds. A 0.50 °C margin was the smallest tested value that screened all four observed thermal stops. The development-selected 0.75 °C margin preserved all 12 joint-planner completions. See the [results](docs/thermal_margin_study.md) and [protocol](docs/protocol.md#thermal-margin-calibration-and-test).

## Run the joint route-and-speed study

Run this after the reference route-network study. The commands use the saved network outcomes as paired controls.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.route_speed_profiles --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.route_speed_study --workers 12
.venv/bin/python -m thermal_pathfinder.audit_route_speed
```

The [configuration](experiments/route_speed_study.json) adds two speed levels to each edge. Joint planning completed 12/16 starts, compared with 11/16 for fixed-speed per-motor routing and 9/16 for planning speeds on the fastest route. See the [results report](docs/route_speed_study.md) and [protocol](docs/protocol.md#joint-route-and-speed-planning). To reproduce the exact prior network audit with its original source, run the audit from [its frozen source snapshot](results/network_study/frozen_source) and pass the original output directory.

## Run the route-network study

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.network_study --workers 12
.venv/bin/python -m thermal_pathfinder.audit_network
```

The [network configuration](experiments/network_study.json) defines two courses, each with three successive branch choices and eight possible routes. It compares four combinations of fixed or thermal route choice and fixed or temperature-triggered speed. Per-motor routing completed 11/16 starts and the fastest route with reactive slowing completed 8/16. See the [results report](docs/network_study.md), [protocol](docs/protocol.md#route-network-and-reactive-slowdown), and [run artifacts](results/network_study). Use an unused `--output` directory for a repeat run.

## Run the asymmetric-map benchmark

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.benchmark --workers 12
.venv/bin/python -m thermal_pathfinder.audit_benchmark
```

Use an unused `--output` directory for repeat runs. The [benchmark configuration](experiments/asymmetric_benchmark.json) fixes six test maps and a nine-setting thermal sweep. The runner saves a source-hashed manifest, all method decisions, route outcomes, raw traces, and the six scenes in [results/asymmetric_benchmark](results/asymmetric_benchmark). The earlier saved run has a matching [source snapshot](results/asymmetric_benchmark/frozen_source). See the [results report](docs/asymmetric_benchmark.md) and [protocol](docs/protocol.md#asymmetric-map-benchmark). The per-motor planner completed 72/108 starts across the six maps, compared with 57/108 for both mean temperature and travel time.

## Connected-map pilot

The branches split around a divider, cross banks of opposite orientation, then turn back toward a common goal 16 m from the start. The route follower commands only joint torques. It allocates a desired body force and moment across stance feet and uses joint position tracking during swing. Each trial starts in the same pose and walks continuously to the goal.

Both nominal-torque runs reached the goal in about 106 s. With the planar pilot's thermal parameters, all four warm-start walks hit the 70 °C modeled limit before completing. See the [reference run](results/connected_pilot/summary.json) for all four thermal stops.

Reproduce the development sensitivity run with:

```bash
.venv/bin/python -m thermal_pathfinder.connected_pilot --heating-multiplier 0.55 --output results/connected_pilot_heat055
```

The multiplier scales the assumed temperature rise at the reference torque. It was selected after inspecting the development traces. It has no measured calibration for the new hexapod. In that run, the per-motor planner completed both starts by switching branches. The mean-only and time-only planners each completed one start. The maximum-only planner rejected both branches in both starts. The [sensitivity results](results/connected_pilot_heat055/summary.json) are development evidence from one scene and two paired starts.

## Earlier two-metre pilot

Run `.venv/bin/python -m thermal_pathfinder.pilot` to reproduce the earlier pilot on separate planes.

The hexapod completed 2 m on flat ground and on each 8° cross-slope with joint actuation. Both warm-start cases had a mean of 55.5 °C and a maximum of 66 °C. The per-joint planner switched routes when the warm side switched.

| Warm motors | Per-joint choice | Peak on chosen route | Peak on the other route |
| --- | --- | ---: | ---: |
| Left side | Ground rises to the right | 66.0 °C | 68.9 °C |
| Right side | Ground rises to the left | 67.0 °C | 68.1 °C |

All four executions finished below the modeled 70 °C limit. Every baseline chose the right-rising route in both starts and completed both. The pilot observed a change in route preference and peak temperature. A completion advantage is an open question for the larger study.

## Project layout

| Path | Contents |
| --- | --- |
| [Hexapod_Model/](Hexapod_Model/) | Local source assembly, provenance, and reproducible CAD audit |
| [thermal_pathfinder/](thermal_pathfinder/) | Parametric MJCF, crawl gait, thermal dynamics, route scoring, and experiment runner |
| [experiments/](experiments/) | Versioned experiment settings |
| [tests/](tests/) | Thermal dynamics and planner regression checks |
| [docs/protocol.md](docs/protocol.md) | Pilot design, limitations, and confirmatory study requirements |
| [results/](results/) | Generated evidence |

The pilot uses a simplified, CAD-informed model with provisional joint frames, inertial properties, and thermal parameters. The planner scores two predefined centerlines from nominal torque traces. See the protocol for the study design and the criteria for evaluating a completion advantage.
