# Mission completion with and without motor identities

The per-motor planner completed **32 of 36** starts. The baseline without motor identities completed **31 of 36**. The difference of **2.8 percentage points** fell below the prespecified 10-point target. A descriptive 95% interval from resampling the six maps was −13.9 to +22.2 points. Four starts finished only with the per-motor planner and three only with the baseline.

## Design

The [frozen configuration](../experiments/mission_completion.json) specified six new courses, three thermal settings, two mirrored temperature starts per setting, a two-second online search budget, and a 10-point minimum worthwhile completion gain. It used three single three-way splits and three successive-split networks. All courses were constructed banked heightfields. The offline profiles and search spaces were shared.

Both planners selected a route and scheduled speeds at 100% or 65% of nominal. Both could react to the hottest motor during the walk using the same slowdown controller. For planning, one method received the motor identities associated with the starting temperatures. The baseline received the same temperature values and averaged its forecast over the two possible side assignments. Both admitted forecasts strictly below 69.50 °C and used a simulated 70 °C stop. The forecast used nominal edge profiles, with adaptive slowing applied in the execution replay.

## Results

| Outcome | Baseline | Per-motor |
| --- | ---: | ---: |
| Completed | 31 | 32 |
| No admitted route | 2 | 3 |
| Thermal stop | 2 | 0 |
| Deadline | 1 | 0 |
| Fall or chassis contact | 0 | 1 |
| Planning timeout | 0 | 0 |
| Median online selection | 5.68 ms | 2.55 ms |
| Maximum online selection | 14.80 ms | 8.71 ms |

The baseline evaluated two possible temperature assignments per candidate and the per-motor planner evaluated one. Online timing covers candidate selection after the common edge profiling and thermal model preparation.

| Course | Baseline completed / 6 | Per-motor completed / 6 |
| --- | ---: | ---: |
| Fan with left ridge | 6 | 5 |
| Fan with right ridge | 6 | 5 |
| Staggered fan | 5 | 4 |
| Fan then split | 6 | 6 |
| Split then fan | 3 | 6 |
| Fan with merge detour | 5 | 6 |

The baseline completed three single-fan starts that the per-motor planner rejected. In each case the baseline selected the center branch. On the successive-split courses, per-motor routing recovered two starts the baseline rejected and two that ended in thermal stops. These course groups each contain three maps. Their differences identify cases for further investigation, and the experiment does not isolate topology as the cause.

The audit checked all 48 branch-and-speed profiles, 72 decisions, and 55 distinct continuous mission traces. The 41 completed nominal profiles were available to both planners. Five fell or had chassis contact and two timed out during profiling. The result applies to the tested route and speed choices, controller, and uncalibrated thermal parameters.

[Manifest](../results/mission_completion/manifest.json) · [Summary](../results/mission_completion/summary.json) · [Decisions](../results/mission_completion/plans.json) · [Executions](../results/mission_completion/executions.json)
