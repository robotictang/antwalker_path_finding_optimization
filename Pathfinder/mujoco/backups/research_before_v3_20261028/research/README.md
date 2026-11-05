# Hexapod research lab

PSO, ACO, the upgraded proposal and the previous proposal are now available.
See [the swarm comparison guide](SWARM_COMPARISON.md) for exact algorithms,
shared budgets, parameters, repeated-seed tests and limitations.

This is an isolated local experiment system. The existing mission demo, meshes,
URDF and history database remain in place. The lab defaults to **walking only**;
hybrid routing is an explicit alternative. Neither experiment mode proves real
robot balance or electrical battery performance.

## Run

From `mujoco/`, use the same Python environment as the existing simulation:

```bash
python3 -m research.run --suite pilot --execute
python3 -m research.run --suite full --execute
python3 -m research.gait_sweep
python3 -m research.server
```

The server prints its localhost URL. The experiment console can launch runs,
show progress and compare completed records. Raw JSON/CSV and route traces are
stored in `outputs/research/`, independently of the existing mission history.
Only one job runs at a time. Interrupted runs keep completed records and mark the
run incomplete. No results are generated from invented observations.

On Linux, `python3 -m research.install_service` installs the console as a user
login service. Stop it with `systemctl --user stop hexapod-research-lab.service`;
disable automatic startup with `systemctl --user disable hexapod-research-lab.service`.
It binds only to 127.0.0.1 and never starts experiments automatically.

## Comparison design

All methods share the same conservative scene-derived graph, robot footprint,
terrain speed caps, turn costs, energy assumptions, time budget and case. This
controlled research graph defaults to the production 0.25 m resolution. Coarser
optional grids can disconnect narrow passages and are reported as such. Every returned segment receives continuous clearance
checks before execution. Search time is wall time on this machine, not simulated
time; case/environment preparation and return-route preprocessing are separate.

* B1 distance A star minimizes distance.
* B2 terrain A star adds geometric and semantic terrain exposure to distance.
* B3 energy A star minimizes the declared energy model.
* B4 sampled weighted sum uses the current project's seven weight pattern on
  the shared research graph. It is an adaptation, not the production controller.
* PSO and ACO optimize forward collision-checked waypoint corridors using the
  same charged energy/time/distance seed portfolio as the upgraded proposal.
* The upgraded proposal searches resource-constrained visibility labels in
  walking mode, with a Pareto beam fallback for hybrid mode. It retains safe
  incumbents, checks time/energy/terrain budgets, and reserves charger energy.
* Previous proposed grid search and greedy shortcut baselines remain available
  as ablations. All nine approaches are available through the method selector.

The previous grid search uses resource bins; the new label search caps labels
per state to bound memory. Both are
approximate and may time out or discard useful labels. It makes no global
optimality claim. Pure baselines return their preferred route even if it violates
a case resource budget, so route finding and mission admissibility are reported
separately. All methods use identical feasibility checks before physics execution.
Execution uses the same fixed gait by default; gait optimization is a separate
experiment, preventing a planner gain from being confused with a gait change.
The energy-aware incumbent and subsequent refinement share one total budget.
This may match the energy baseline without improving it; no superiority is
assumed. Completed and interrupted datasets remain available in run history.

The terrain exposure objective is a **difficulty proxy**, not a probability of
falling. Geometric features use a footprint-sized sample window; semantic
softness is an assumed grade lookup, not measured soil or ERFNet output. The
speed map uses existing configured terrain caps, not a trained TravFormer.

## Measurement limits

Positive actuator work integrates `max(force * velocity, 0)` for all actuators
at every physics substep. Leg-only work is also recorded. This is mechanical
work in joules, not battery energy. Nominal battery use is a separate percentage
point model. Tilt, stance contact counts, support margin and slip are diagnostics
of this assisted model, not independent proof of stability. Gravity compensation,
direct base velocity assistance and posture control remain disclosed.

Charging restores the battery using a declared simulated service duration.
Optional battery replacement is a modeled stationary service event, not a
physical swap mechanism. Failed and incomplete trials remain in denominators.
Successful-only cost averages are labeled and must be read alongside success.

See `research_review.md` for the primary-source paper review and adaptation
boundaries. See `IMPLEMENTATION.md` for the feature checklist and verification.
