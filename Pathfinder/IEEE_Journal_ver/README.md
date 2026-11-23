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

## Run the exhaustive hot-motor swap test

The [protocol](docs/hot_motor_swap_protocol.md) fixes 12 new courses and three thermal settings. The test replays every supported route under both mirrored starts using the same thermal speed controller. It compares choices made with individual motor temperatures against choices made with the mean and maximum.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/hot_motor_swap.json --output results/hot_motor_swap --workers 14
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.hot_motor_swap --workers 14
```

See the [verified results](docs/hot_motor_swap.md) for the route reversals and planner comparison.

Use an unused output directory for a new nominal run. Restarting the warm-run command in the same output directory checks the frozen inputs and resumes from the audited replay checkpoint.

## IEEE Access review package

Version 3 covers the exhaustive hot-motor swap study and includes the author biographies. Open the [latest PDF](output/pdf/hexapod-hot-motor-swap-ieee-access-juo-bio-updated.pdf), [editable LaTeX](manuscript/ieee-access-v3-hot-motor-swap/README.md), or [source ZIP](output/hexapod-hot-motor-swap-ieee-access-juo-bio-updated-source.zip).

The [editable LaTeX source](manuscript/ieee-access/README.md) uses the official IEEE Access class. Open the [compiled review PDF](output/pdf/hexapod-junction-pause-ieee-access-review.pdf) or download the [portable LaTeX archive](output/hexapod-junction-pause-ieee-access-source.zip). The byline and corresponding-author details are placeholders in [author-details.tex](manuscript/ieee-access/author-details.tex).

## Manuscript and figures

The [integrated manuscript](docs/manuscript.md) describes the simulation, planner, and benchmark. Regenerate both figures from the audited records after running the benchmark and screening diagnostic:

~~~bash
uv run --python 3.12 --with-requirements requirements.txt --with matplotlib==3.10.3 python -m thermal_pathfinder.manuscript_figures
~~~

The PNG previews and editable SVGs are in [docs/figures](docs/figures/).

## Reproduce the published-controller comparison

After reproducing the frozen 12-course benchmark, run:

~~~bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.published_speed_baseline --workers 14
~~~

The [published speed comparison](docs/published_speed_baseline.md) describes the hexapod adaptation and provides the paired replay results.

## Run the larger fixed-planner pause benchmark

After reproducing the four-course pause forecast study:

```bash
.venv/bin/python -m thermal_pathfinder.pause_confirmation freeze
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/pause_forecast_confirmation.json --output results/pause_forecast_confirmation --workers 14
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.pause_forecast_study --config experiments/pause_forecast_confirmation.json --output results/pause_forecast_confirmation --workers 14
.venv/bin/python -m thermal_pathfinder.pause_confirmation audit
```

The [benchmark report](docs/pause_forecast_confirmation.md) records the design and the 10-point practical completion criterion. The [manuscript draft](docs/manuscript_results_discussion.md) includes a post hoc check of the 48 time-only fallback schedules. Run `.venv/bin/python -m thermal_pathfinder.pause_screening_diagnostic` to reproduce that check from the saved traces.

## Forecast per-motor cooling before selecting a pause

With the junction-pause development and transfer results available:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/pause_forecast.json --output results/pause_forecast --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.pause_forecast_study --workers 12
```

The [forecast study](docs/pause_forecast.md) evaluates the per-motor pause model on archived schedules and compares its fallback planner with the time-only planner on four new courses.

## Test the fixed junction pause on other courses

After reproducing the junction-pause development test and both archived reactive studies:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.junction_pause_transfer --workers 12
```

The [transfer study](docs/junction_pause_transfer.md) compares the same schedule with and without the fixed 12-second pause, using four previously evaluated two-stage courses outside pause development.

## Test an in-place crawl at a junction

After reproducing the exhaustive schedule audit:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.junction_pause --workers 12
```

The [junction-pause study](docs/junction_pause.md) tests three pause durations on the unequal-banks start for which all original schedules overheated.

## Audit adverse reactive planning decisions

After reproducing both reactive forecast and margin transfer comparisons:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.schedule_audit --workers 12
```

The [audit](docs/schedule_audit.md) exhausts the available route-and-speed schedules for each adverse start and compares simulated outcomes with the forecast screens.

## Test whether recalibrated reactive margins transfer

With the archived reactive-forecast outputs in `results/reactive_forecast`:

```bash
.venv/bin/python -m thermal_pathfinder.reactive_margin
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/reactive_margin_transfer.json --output results/reactive_margin_transfer --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.reactive_margin_study --workers 12
```

The [protocol](docs/reactive_margin_protocol.md) freezes the calibration grid and six new courses. The comparison uses two reactive planners with different margins and the earlier stitched planner as a reference. On the six new courses, the calibrated planner finished 21/36 starts and the fixed reactive planner finished 22/36. See the [results](docs/reactive_margin_transfer.md).

## Test forecasts that account for reactive slowdown

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/reactive_forecast.json --output results/reactive_forecast --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.reactive_study --workers 12
```

The [protocol](docs/reactive_forecast_protocol.md) specifies four new courses and three forecasts using the same per-motor starting temperatures, route and speed options, and adaptive execution controller. The runner records selected schedules, comparable forecasts on the replay set, warm trace checks, and paired completion. The reactive forecast improved peak and time accuracy but completed 12/24 starts, compared with 13/24 for the existing forecast. See the [results](docs/reactive_forecast.md).

## Reproduce the disagreement and bank-order follow-ups

Run the original mission-completion benchmark first. Its saved executions provide the adaptive reference for the seven disagreements. The diagnostic replays schedules with the reactive speed override disabled while keeping torque derating in place.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.discordant_replays --workers 4
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/matched_load_order.json --output results/matched_load_order --workers 12
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_completion --config experiments/matched_load_order.json --output results/matched_load_order --workers 12
.venv/bin/python -m thermal_pathfinder.load_order_analysis
```

The [matched-course protocol](docs/matched_load_order_protocol.md) specifies three pairs whose stages appear in opposite orders. The original thermal margin, adaptive controller, planning-time budget, and completion target carry forward.

For the supplemental thermal settings, reuse the audited nominal profiles:

```bash
.venv/bin/python -m thermal_pathfinder.prepare_load_order
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_completion --config experiments/matched_load_order_boundary.json --output results/matched_load_order_boundary --workers 12
.venv/bin/python -m thermal_pathfinder.load_order_analysis --config experiments/matched_load_order_boundary.json --output results/matched_load_order_boundary
```

See the [seven-case replay report](docs/discordant_replays.md) and [matched bank-order results](docs/matched_load_order.md).


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

## Matched test of a junction pause

The adapted published thermal speed controller runs in both arms. One arm can plan a 12 s junction pause in addition to all no-pause options. The [protocol](docs/matched_pause_protocol.md) fixes 72 paired warm starts on 12 fresh courses. The pause-load estimate comes from the existing confirmation archive. Enabling the pause raised completion from 25 to 29 and thermal stops from two to four. The same-route controls confirmed three physical recoveries. [Paired results](results/matched_pause/summary.json) · [Independent audit](results/matched_pause/audit.json)

```bash
.venv/bin/python -m thermal_pathfinder.matched_pause freeze
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.matched_pause profiles --workers 14
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.matched_pause execute --workers 14
.venv/bin/python -m thermal_pathfinder.matched_pause_audit
```

Regenerate the matched-results figure from the saved plans and replays:

```bash
uv run --python 3.12 --with-requirements requirements.txt --with matplotlib==3.10.3 python -m thermal_pathfinder.matched_pause_figure
```

Use the same unused `--output` directory for each step of a repeat. The [results index](results/README.md) describes the saved forecasts and physics traces.

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
