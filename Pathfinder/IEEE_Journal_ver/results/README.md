# Generated pilot outputs

Running the development pilot writes `results/pilot/summary.json` (configuration, tool versions, decisions and execution outcomes), `traces.npz` (joint torque, joint temperature, chassis position and foot contact counts), and the generated MJCF for each terrain. Pass `--output results/<name>` for a separate run. The generated files are ignored by Git. The pilot configuration and evidence interpretation live in the project source.

The connected-map runner writes `results/connected_pilot/summary.json`, `traces.npz`, and a shared `scene.xml`. The trace archive includes each branch centerline and the terrain grid alongside the simulated trajectories.

The asymmetric benchmark writes a frozen `manifest.json`, a per-method `decisions.csv`, per-route `executions.json`, aggregate `summary.json`, six MJCF scenes and one NumPy archive per trace. Nominal traces have no temperature records. Each warm trace includes its starting temperature vector followed by one vector per 20 ms torque sample.

Run `.venv/bin/python -m thermal_pathfinder.audit_benchmark` to verify the manifest, trace contents, decision counts, and branch-switch outcomes and write `audit.json`.

The network study writes a frozen `manifest.json`, nominal `edge_profiles.json`, `plans.json`, `decisions.json`, `executions.json`, `summary.json`, two MJCF scenes and one NumPy archive per trace. Run `.venv/bin/python -m thermal_pathfinder.audit_network` to produce `audit.json` with paired completion differences and slowdown statistics.

The route-and-speed study writes `profile_manifest.json`, `manifest.json`, `edge_profiles.json`, `plans.json`, `executions.json`, `decisions.json`, `summary.json`, and profile and mission trace archives in separate subfolders. Decisions using a previous execution identify their reference run. Run `.venv/bin/python -m thermal_pathfinder.audit_route_speed` to verify the pairing and write `audit.json`.

The thermal-margin experiment writes `manifest.json` with the source hashes and development calibration, `edge_profiles.json`, `plans.json`, `executions.json`, and `summary.json`. The summary contains per-method sweeps and observed-minus-predicted peaks for distinct test replays. Profile and mission trace archives are in separate subfolders.

The thermal-margin transfer run uses the same artifacts under `results/thermal_margin_transfer`. Run `.venv/bin/python -m thermal_pathfinder.margin_transfer` to verify all branch profiles and continuous traces and save decision counts by course and thermal setting.

The continuous-profile comparison stores a source and input checksum manifest, nominal route profiles and their traces, `forecasts.json` with paired forecasts and observed outcomes, and `summary.json` with peak errors and admission counts. It uses the saved transfer outcomes as the evaluation reference.

The mission-completion benchmark writes its frozen `manifest.json`, generated scenes, `edge_profiles.json`, `plans.json`, `executions.json`, and `summary.json` under `results/mission_completion`. Nominal and warm traces are stored separately. The summary includes map-level paired effects and planning-time measurements.

The disagreement study keeps a reference manifest and writes `summary.json` plus new traces in `results/discordant_replays`. The matched bank-order study reuses the mission-completion artifact layout in `results/matched_load_order`. Its summary includes course-order pairs and the nominal femur loading check.

The reactive-forecast comparison uses `results/reactive_forecast`. Its `forecast_manifest.json` hashes the forecast source and all nominal profiles, including excluded branches. In addition to the paired `plans.json` and warm `executions.json`, `schedule_forecasts.json` records each method's predicted peak and elapsed time for the same set of selected schedules and fastest probes.

The reactive-margin transfer experiment uses `results/reactive_margin_transfer`. Its `calibration.json` freezes the development inputs, grid, selected margins, and leave-one-course-out diagnostics. The separate `evaluation_manifest.json`, `plans.json`, `schedule_forecasts.json`, `executions.json`, and `summary.json` record the held-out comparison and its nominal and warm traces.

The exhaustive schedule audit uses `results/schedule_audit`. Its manifest records the source and archive hashes and lists the new replays. The summary lists every schedule's forecast, screening reasons, simulation outcome, and trace hash, plus the fastest and coolest observed finishes for each adverse start.

The junction-pause study uses `results/junction_pause`. The manifest identifies the original trace for every baseline schedule and the warm replay traces record temperatures, joint torque and body position. The summary includes thermal change and body displacement during the pause and an exact zero-pause trace check.

The junction-pause transfer study uses `results/junction_pause_transfer`. Its manifest freezes the schedule for each start and records the archived inputs and reused trace hashes. The summary gives paired outcomes, per-run pause telemetry, and the result of applying a pause only as a fallback on original rejections.

The pause forecast study writes its inferred motor loads and hashes in `results/pause_forecast/pause_model.json`. Its `archived_evaluation.json` checks prediction errors and screening on the previous transfer schedules. The new-course `plans.json`, `executions.json`, and `summary.json` give the decisions, trace references and paired outcomes.

The larger fixed-planner benchmark uses `results/pause_forecast_confirmation`. Its `confirmation_lock.json` ties the model, comparison rules and 12 course definitions to the previous implementation. The standard pause-forecast outputs are supplemented by `confirmation_audit.json`, with independent paired-trace checks and breakdowns by course, family and thermal setting.

The published speed controller comparison writes to results/published_speed_baseline. Its manifest links the original benchmark by checksum. The archive adds 72 decisions, 33 replay traces and a paired comparison with the pause planner.

The matched governor comparison uses `results/matched_pause`. The evaluation lock records the protocol, sources and archived hold estimate. Profile and mission checksum records track all raw traces. The paired plans retain every candidate forecast and both selected outcomes. The summary records the overall, course, family and setting comparisons and the diagnostic replays on selected paused routes with the pause removed. Run `.venv/bin/python -m thermal_pathfinder.matched_pause_audit` to recompute the candidate forecasts, thermal histories, outcome pairing, and unchanged trajectory prefixes and write `audit.json`.
