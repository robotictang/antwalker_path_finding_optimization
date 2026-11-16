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
