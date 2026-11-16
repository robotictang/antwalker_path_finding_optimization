# Asymmetric terrain and thermal sensitivity

Six asymmetric courses were held out from tuning the controller on the earlier mirrored course. The map definitions, nine thermal settings and source hashes were saved in the [manifest](../results/asymmetric_benchmark/manifest.json) before running the new maps. All 12 nominal routes reached the shared goal. The warm sweep evaluated 216 branch outcomes and 432 decisions, giving each method the same 108 starts.

| Method | Completed | No route selected | Selected route failed |
| --- | ---: | ---: | ---: |
| Per-motor temperature | 72 | 36 | 0 |
| Maximum starting temperature | 42 | 66 | 0 |
| Mean starting temperature | 57 | 24 | 27 |
| Travel time | 57 | 0 | 51 |

Per-motor tracking added 13.9 percentage points over both mean temperature and travel time. The descriptive 95% paired-map bootstrap interval was 12.0 to 15.7 points for both comparisons. Against the maximum-temperature rule, the difference was 27.8 points, with an interval of 24.1 to 31.5 points. The per-motor method completed every start with at least one physically successful branch in this suite. All 105 failed branch executions reached the thermal limit.

| Relative heating rate | Cooling time constant (s) | Per-motor completions / 12 | Mean and time completions / 12 each | Maps where the only finishable branch switched / 6 |
| ---: | ---: | ---: | ---: | ---: |
| 0.45 | 80 | 12 | 12 | 0 |
| 0.45 | 100 | 12 | 12 | 0 |
| 0.45 | 120 | 12 | 9 | 3 |
| 0.55 | 80 | 12 | 12 | 0 |
| 0.55 | 100 | 12 | 6 | 6 |
| 0.55 | 120 | 0 | 0 | 0 |
| 0.65 | 80 | 12 | 6 | 6 |
| 0.65 | 100 | 0 | 0 | 0 |
| 0.65 | 120 | 0 | 0 | 0 |

The per-motor planner found both finishable branches in all 15 map–setting pairs where swapping the warm side switched the only finishable branch. It also switched preferences in 15 pairs where a switch was unnecessary for completing both starts. At three settings, every planner completed all starts. At three hotter or slower-cooling settings, neither branch finished in any start.

The results cover six hand-designed variants of one topology, two initial temperature patterns, and uncalibrated motor parameters. The bootstrap describes variation across the six tested maps. Each planner scores two predefined, nominally profiled routes. The experiment supports a simulation result for this route-selection task. Testing graph search would require a larger network and a comparison with a controller that can slow down or change gait on a fixed route.

[Summary](../results/asymmetric_benchmark/summary.json) · [Decisions](../results/asymmetric_benchmark/decisions.csv) · [Route executions](../results/asymmetric_benchmark/executions.json) · [Trace audit](../results/asymmetric_benchmark/audit.json)
