# Implementation and research boundaries

## Available now

- PSO random-key waypoint refinement with personal/swarm best updates.
- ACO probabilistic route construction with pheromone evaporation and deposits.
- An upgraded seed-portfolio constrained visibility-label refiner, with a hybrid
  beam fallback and previous-method and greedy
  shortcut ablations preserved. See `SWARM_COMPARISON.md` for exact boundaries.
- Paired repetitions and optimizer seed, parameter, evaluation and convergence
  logs; repetition filtering and observed search-progress charts.

- Three independent scalar baselines: distance A*, terrain-aware A*, energy A*.
- A fourth sampled weighted-sum baseline following the existing weight pattern.
- A seeded, resource-constrained multi-label proposed search with bounded memory.
- The same scene-derived footprint map, 0.25 m graph, hard terrain exclusions,
  continuous returned-segment checks, speed limits and case budgets for all methods.
- Legs-only default and optional hybrid physics execution, isolated from live history.
- Paired smoke, pilot and extended scenario suites; fixed seed/order recording.
- Per-attempt wall time and expansions, source hashes and source snapshots for new runs.
- Deadline, task-plus-charger battery, terrain exposure and execution safety checks.
- Actual physics-substep positive and absolute actuator work, leg work, peak power,
  body tilt, foot contacts, contact slip and projected-COM support margin.
- Independent modeled battery consumption perturbation for robustness scenarios.
- Charging stop and explicitly modeled replacement service accounting, separately named.
- Configurable gait period, duty, lift and cubic/quintic swing interpolation.
- Nine timing combinations plus the original controller, tested on smooth/mild/high
  terrain where a valid track is available. Calibration selection is separate from
  planner comparisons and does not silently change the baseline controller.
- A local experiment-launch console with jobs, progress/logs, durable history and
  JSON/CSV download; source-backed charts with per-scenario filters, measured versus
  predicted values, failures, and side-by-side maps and executed trails.
- Four-reference manifest and review: three accessible full texts, one partial review.

## Explicitly not established or reproduced

The experiment algorithms are inspired adaptations, not exact implementations of
Smart Gait, the terrain paper, CASE2025 or STATE-NAV. This work does not contain
Smart Gait's full dynamics optimization, centroid-support QP or online gait adapter;
ERFNet image segmentation; TravFormer training, TravRRT* or biped LIPM MPC;
deformable soil; calibrated electrical energy; payload splitting; a physical battery
swap mechanism; or a hardware-validated controller. The uploaded document describes
these research systems but does not supply their complete models or datasets.

The geometric terrain score is a difficulty objective, not measured instability or
fall probability. Body assistance and gravity compensation remain present. No
publication acceptance probability, statistical significance or universal improvement
is claimed. A default pilot has only three paired scenarios on one underlying scene.

## How to extend the study

1. Use the extended suite and add independent new map generators and held-out maps.
2. Compare a fixed-cap and an adaptive-cap ablation of the proposed label search.
3. Collect a speed/terrain response dataset with an independently controlled robot,
   then fit and validate a capability predictor before using learned safe speeds.
4. Calibrate electrical power from motor/battery measurements rather than equating
   actuator mechanical work with battery drain.
5. Validate gait settings on new tracks before enabling them in mission controllers.
6. For physical stability claims, reduce assistance and add torque, friction and
   contact-model checks, then validate on hardware.

See `outputs/research/verification.json` for the actual checks and completed runs.
