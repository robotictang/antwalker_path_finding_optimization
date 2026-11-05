# Hexapod research lab

Version 3 adds resumable seed search, independent procedural terrain worlds, stronger baselines, explicit component-removal controls and an external electrical-calibration workflow. The earlier studies remain available as historical evidence.
See [the swarm comparison guide](SWARM_COMPARISON.md) for exact algorithms,
shared budgets, parameters, repeated-seed tests and limitations.

This is an isolated local experiment system. The existing mission demo, meshes,
URDF and history database remain in place. The lab defaults to **walking only**;
hybrid routing is an explicit alternative. Neither experiment mode proves real
robot balance or electrical battery performance.

## Run

From `mujoco/`, use the same Python environment as the existing simulation:

```bash
python3 -m research.run --suite procedural4 --world-seed 1050000 --methods b1_distance b3_energy b7_greedy pso aco proposed
python3 -m research.strong_study
python3 -m research.audit_strong_study
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
  as ablations. All twelve approaches are available through the method selector.

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

## Version 3 evidence and calibration

Read [the simple experiment guide](web/research-guide.md) for the website steps,
exact phase counts and interpretation. The frozen campaign lives in
`outputs/research/strong_study_v3/`: 96 development attempts, 432 held-out
planning attempts on 24 new worlds, 96 ablation attempts, 24 old-case diagnostic
attempts and 36 separately scheduled physics attempts. A scheduled physics
attempt executes only if admitted. Twenty-four tiny exact-reference graphs are
separate synthetic software checks, not robot experiment data.

The main six methods are distance A*, energy A*, greedy shortcuts, PSO, ACO and
proposed. Ablations disable adaptive seed timing, seed-family variety or
resource-bound pruning one at a time. Initial adaptive seed recovery is shared
with PSO, ACO and greedy to avoid giving the proposal an exclusive initialization
advantage. The study locks its manifest and scientific source hashes, tunes all
three optimizers with the same two-profile opportunity, and freezes selections
before held-out execution. Rerunning resumes the frozen campaign; it does not
create independent new evidence. Use a new version directory AND new world
seeds when changing the scientific method or conducting a new confirmatory test.

The four procedural world families are open, clutter, rough and corridor. A
single world specification supplies physical obstacles/tiles and planning
terrain queries. Bindings are scoped to the isolated research run and restored
after each case. Development and held-out worlds use disjoint seeds and hashes.
These are still samples from a restricted simulated distribution.

Prediction errors for destination time and modeled battery use are saved on
physics records. Neither the simulated battery ledger nor mechanical actuator
work is accepted as external electrical calibration truth. Start with:

```bash
python3 -m research.calibration --template outputs/research/calibration_template
python3 -m research.calibration --csv YOUR.csv --metadata YOUR_metadata.json --out fitted_profile.json
python3 -m research.run --suite procedural4 --methods pso aco proposed --execute --energy-profile fitted_profile.json
```

Fill the template with real electrical measurements and usable battery capacity.
Calibration and validation maps AND missions must be disjoint. The fitter is
walking-only; coefficient validation does not verify a sensor or certify a
physical battery model. The software minimum observation count is not a
publication sample-size justification. The existing Word manuscript describes
version 1 and needs revision before citing version 3 results.

## Version 4 development and comparison

The new `proposed_v4` method adds a geometry visibility roadmap and free movement
of internal waypoints to a safe Pareto-refined incumbent. Roadmap landmarks come
from the known obstacle and terrain geometry. Continuous polishing uses the
unchanged evaluator, feasibility-first ranking and exact segment clearance.
The old safe incumbent survives even when the remaining search budget expires.
This uses established roadmap/shortcutting ideas; it has no global optimality
or universal superiority guarantee.

`pso_polished` and `aco_polished` are stronger controls with the same polishing
operator and total wall/fitness limits. They inherit tuned baseline parameters
and the same selected polishing settings, with no separate tuning search.
The V4 seed label refiner keeps its fixed default v3 settings. The distinct
candidate representation is explicitly disclosed in the results.

Run `python3 -m research.advanced_study` from `mujoco/`. The frozen campaign
contains 128 development attempts on 8 worlds, 864 primary planning attempts on
24 new worlds and 12 methods, 72 feature-removal attempts, 96 shorter-budget
attempts and 72 separately scheduled assisted-physics attempts: 1,232 total.
Development seeds begin at 1240000 and test seeds at 1350000. The manifest fixes
all subsets before tuning. Balanced score, battery coefficients and resource
rules are identical between methods. Parameter selection is tuning, not neural
network training. No test outcome is used to choose parameters or remove cases.

Use `python3 -m research.audit_advanced_study` after completion. It checks source
and physical-model hashes, trial keys, tuning selection, frozen parameters,
resource decisions, scores, collision clearance and continuous metric
recomputation. Ties, losses, resource rejection and physics failure remain in
records. A best balanced score need not have the lowest runtime, distance,
battery use or terrain exposure separately.

Version 4 methods currently support walking only. The console rejects incompatible
hybrid selections before running. The comparison dashboard dynamically identifies
the focal method from the selected run; old v3 records retain their original
meaning. `Every_Experiment.csv` in the result delivery lists each paired world
and repetition's score verdict against all methods. Older Word documents describe
version 3 and require explicit revision before citing version 4 evidence.
