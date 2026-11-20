# Hot-motor swaps under adaptive speed control

Across 36 course–thermal-setting pairs, **11 required a different route for the two hot-side assignments to both finish**, spanning 8 of the 12 courses. In 6 pairs each side had exactly one finishable route and those routes differed. A strict thermal crossover occurred in 13 pairs across 10 courses.

## Protocol and outcome definitions

The [protocol](hot_motor_swap_protocol.md) defined 12 new two-stage courses and three thermal settings. All 96 nominal branch profiles completed. The evaluation ran 288 continuous MuJoCo walks across 72 starts, covering all four geometric routes per start. Both planners used the same adapted thermal speed governor during walking. Each pair had the same start-temperature values, mean, and maximum. The swap moved the nine warm temperatures to the opposite side.

A necessary route change means both starts had a finishable route and the sets had no route in common. A strict thermal crossover means one route finished with heat on the left and overheated with heat on the right, while another route showed the opposite outcomes.

| Course family or heating multiplier | Pairs | Neither side had a finishable route | One side did | Shared finishable route | Necessary route change | Strict thermal crossover |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All courses | 36 | 16 | 5 | 4 | 11 | 13 |
| Alternating banks | 12 | 8 | 1 | 1 | 2 | 3 |
| Persistent banks | 12 | 4 | 0 | 1 | 7 | 7 |
| Same-sign stage | 12 | 4 | 4 | 2 | 2 | 3 |
| 0.44 heating multiplier | 12 | 0 | 1 | 4 | 7 | 9 |
| 0.45 heating multiplier | 12 | 8 | 2 | 0 | 2 | 2 |
| 0.46 heating multiplier | 12 | 8 | 2 | 0 | 2 | 2 |

The branch numbers in the routes below are listed in stage order.

| Course | Heating multiplier | Routes that finished left-warm | Routes that finished right-warm | Strict thermal crossover |
| --- | ---: | --- | --- | --- |
| swap_alternating_03 | 0.44 | 2–2 | 1–1 | Yes |
| swap_alternating_04 | 0.44 | 2–1, 2–2 | 1–1, 1–2 | Yes |
| swap_persistent_01 | 0.46 | 1–1 | 2–2 | Yes |
| swap_persistent_01 | 0.45 | 1–1 | 2–2 | Yes |
| swap_persistent_02 | 0.44 | 2–2 | 1–1 | Yes |
| swap_persistent_03 | 0.46 | 1–1 | 2–2 | Yes |
| swap_persistent_03 | 0.44 | 1–1, 2–1 | 1–2, 2–2 | Yes |
| swap_persistent_03 | 0.45 | 1–1 | 2–2 | Yes |
| swap_persistent_04 | 0.44 | 2–2 | 1–1, 1–2 | Yes |
| swap_same_sign_stage_02 | 0.44 | 2–2 | 1–1, 1–2 | Yes |
| swap_same_sign_stage_04 | 0.44 | 2–1 | 1–1, 1–2 | Yes |

For example, on the third persistent-bank course at the 0.46 heating multiplier, each start had nine motors at 67 °C and nine at 45 °C. Route 1–1 finished at 69.64 °C with the left side warm and reached the 70 °C thermal stop with the right side warm. Route 2–2 showed the reverse, finishing at 69.43 °C with the right side warm. The other two routes overheated under both assignments. All 11 pairs that required different routes exhibited this type of thermal crossover.

## Planner comparison

| Information available when choosing the route | Finished | Thermal stop | Other execution failure | No route admitted |
| --- | ---: | ---: | ---: | ---: |
| Mean and maximum | 7 | 5 | 0 | 60 |
| Individual motor temperatures | 26 | 2 | 0 | 44 |

The paired gain was +26.4 percentage points, with 20 starts finished only by the per-motor planner and 1 finished only by the aggregate planner. The descriptive 95% interval from resampling the 12 courses was +15.3 to +40.3 points. The net difference in thermal stops was -3. The result met the prespecified joint criterion of a 10-point gain and zero additional thermal stops.

Given the full replay outcomes, the best assignment-specific route choices could finish 35 of 72 starts. Giving both starts in each pair one common route could finish at most 24. These counts describe what the tested routes allowed with the outcomes known.

The aggregate planner rejected 24 starts for which a route could finish in simulation. The per-motor planner rejected seven such starts. On the 22 starts in pairs requiring different routes, the per-motor planner finished 15 and the aggregate planner finished one. The per-motor planner still missed nine of the 35 finishable starts across the full experiment.

## Verification

All 288 warm traces were checked against the starting temperatures, the deadline, the goal, and the simulator's first crossing of the thermal limit. Recomputing temperatures from the saved torques gave a maximum recurrence residual of 0 °C. The results concern this simulated hexapod, tested geometry, thermal assumptions, and side-level starting patterns.

[Frozen configuration](../experiments/hot_motor_swap.json) · [Full summary](../results/hot_motor_swap/summary.json) · [Pre-execution forecasts and choices](../results/hot_motor_swap/plans.json) · [Replay index and audit records](../results/hot_motor_swap/executions.json)
