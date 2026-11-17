# Published thermal speed controller comparison

This additional comparison adapts the footfall-level decision rule in Section III-D, Eq. (8) of Trujillo and Cutkosky's ICRA 2009 paper. They estimate a motor's available heat budget and invert an empirically measured speed-to-heating curve to choose the fastest permissible command. The published robot is a four-legged configuration of RiSE climbing a vertical surface. Its case thermal network, motor data and climbing gait belong to that platform. [Published paper](https://doi.org/10.1109/ROBOT.2009.5152870) · [Author manuscript](https://bdml.stanford.edu/twiki/pub/Rise/RisePublications/ICRA09_Trujillo.pdf)

## Reimplementation on the hexapod

The decision rule is evaluated in the existing MuJoCo hexapod using its shared first-order actuator model, the same branch profiles, the same 69.50 °C planning ceiling and the same 70 °C execution stop. It uses the current simulated temperature of all 18 motors. At each scheduled footfall, every 0.50 s, the controller computes a squared-torque budget for a 3 s gait period. It solves the shared thermal update for the largest allowable constant mean squared torque. The thermal model yields the following per-motor budget, where $T_i$ is the current temperature, $T_a$ is ambient, $T_\mathrm{cap}$ is the forecast ceiling and $g$ is the gait period.

$$
B_i = \frac{q_\mathrm{ref}^2}{R}
\left[T_i - T_a +
\frac{T_\mathrm{cap}-T_i}{1-\exp(-g/\tau)}\right].
$$

For the current position bin, interpolate the per-motor mean squared torques between the same 65% and 100% nominal speed profiles used in the original experiment. Choose the fastest interpolated command that fits every motor budget. Both increases and decreases in predicted motor load with speed are allowed. When the supported speed range contains no feasible command, the adaptation records that event and issues the slowest supported command. Physics retains the common torque derating and thermal stop. This controller operates continuously along the walk without adding a scheduled pause.

A route-selection wrapper forecasts that controller on the same four geometric routes that were available to the original methods. The wrapper selects the earliest predicted finish among routes that pass the shared peak and deadline gates and ranks tied arrival times by predicted peak and route identifier. It has the same 2 s online budget. The wrapper and single-node motor budgets are hexapod adaptations. The published element is the fastest-feasible speed rule at each footfall, with an empirical map from speed to heating. The benchmark evaluates that rule on our simulated robot.

## Protocol

The comparison uses all 72 starts and 12 courses from the frozen benchmark. It checks source and input hashes, preserves the archived three-method comparison, and reports the new controller as an additional comparison on the same instances. This controller was added after the original benchmark and its comparison is supplementary. The no-pause comparator itself may choose a continuous intermediate speed between the shared endpoints.

Run from the project directory after reproducing the frozen benchmark:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.published_speed_baseline --workers 14
```

## Results

| Method | Finished | Planning rejection | Thermal stop | Deadline miss |
| --- | ---: | ---: | ---: | ---: |
| Fixed reactive | 18/72 | 50 | 0 | 4 |
| Time-only pause fallback | 28/72 | 2 | 38 | 4 |
| Per-motor pause forecast | 20/72 | 48 | 0 | 4 |
| Published speed rule (hexapod adaptation) | 30/72 | 39 | 3 | 0 |

The adapted speed rule completed 14 starts that the pause planner missed. The pause planner completed four that the speed rule missed. The pause planner's net completion difference was −13.9 percentage points. The descriptive 95% interval from resampling courses was −25.0 to −2.8 points. Its thermal-stop count was three lower. Both original pause gains on the shallow alternating-bank course ended in thermal stops under the adapted speed rule. The third stop under the adapted rule occurred before the junction on the switch-early course.

All 72 decisions stayed within the shared planning budget. The longest selection took 0.065 s. All 33 new thermal physics replays were audited against their traces. The comparison is between two complete strategies under the shared simulator conditions. Their route ranking, speed selection and availability of a pause differ.

[Paired summary](../results/published_speed_baseline/summary.json) · [Frozen comparison manifest](../results/published_speed_baseline/manifest.json) · [Planning decisions](../results/published_speed_baseline/plans.json) · [Replay outcomes](../results/published_speed_baseline/executions.json)
