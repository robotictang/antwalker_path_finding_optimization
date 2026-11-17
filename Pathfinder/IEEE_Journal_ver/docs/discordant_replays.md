# Why seven paired mission outcomes differed

The [original benchmark](mission_completion.md) had seven starts where exactly one planner finished. This follow-up includes all seven starts. It compares 12 distinct case-and-schedule combinations under the original adaptive controller and under the same scheduled speeds with only the reactive speed override disabled. Temperature-dependent torque derating, the 70 °C stop, planner forecasts, and deadlines are shared. Nine adaptive executions came from the original audited traces. Fifteen new replays cover scheduled speed alone and three previously unexecuted lowest-forecast plans.

## What the forecast margin did

All five thermal planning rejections among these seven starts had a candidate below the modeled 70 °C limit. The 0.50 °C margin, which required forecasts below 69.50 °C, blocked each planner's lowest forecast. Replaying those lowest-forecast schedules with the adaptive controller yielded two finishes and three thermal stops. Removing the margin alone would have recovered two of the five rejected starts and admitted three stops in this selected sample.

| Rejected planner and start | Best forecast used by that planner | Adaptive replay of best schedule |
| --- | ---: | --- |
| Per-motor, left ridge with left warm | 69.714 °C | Completed |
| Per-motor, right ridge with right warm | 69.919 °C | Thermal stop |
| Per-motor, staggered fan with left warm | 69.721 °C | Thermal stop |
| Anonymous, split then fan with left warm | 69.600 °C | Completed |
| Anonymous, split then fan with right warm | 69.600 °C | Thermal stop |

The three single-fan cases use the slower-cooling setting. The last two use the warmer-start setting. The anonymous planner reports the mean of the two possible assignments. For the right-warm rejection on split then fan, the forecast for the true assignment alone was 71.200 °C on that schedule.

## What the reactive controller changed

| Course and branch | Stitched forecast for true start | Scheduled speed alone | With reactive override |
| --- | ---: | --- | --- |
| Right ridge, center | 70.118 °C | Thermal stop at 95.5 s | Finished at 217.0 s, peak 69.472 °C |
| Staggered fan, center | 70.197 °C | Thermal stop at 93.9 s | Finished at 218.8 s, peak 69.490 °C |
| Right ridge, outer | 69.919 °C | Finished at 162.6 s, peak 69.926 °C | Thermal stop at 152.9 s |
| Staggered fan, outer | 69.721 °C | Finished at 165.6 s, peak 69.712 °C | Thermal stop at 160.4 s |

On the two rescued center branches, the override triggered at 17.4 and 21.9 s. On the two outer branches it triggered at 131.4 and 136.6 s. Five schedules finished under both policies and three stopped under both. The four remaining schedules changed outcome when the override was toggled. These are disagreement cases selected from the original benchmark, so the counts describe the audited cases.

The matched replays establish that reactive execution can change the feasibility of a route in either direction. The forecast margin alone cannot account for the original losses. A possible planner improvement is to forecast the behavior of its reactive controller on each shortlisted schedule and test that forecast on untouched courses.

[Reference hashes](../results/discordant_replays/manifest.json) · [All seven cases and traces](../results/discordant_replays/summary.json)
