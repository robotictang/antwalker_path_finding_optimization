# Per-motor forecasts for a junction pause

The [time-only fallback](junction_pause_transfer.md) recovered finishes but attempted schedules that still overheated. This experiment estimates the effect of crawling in place on the entire per-motor temperature vector and uses the estimate to screen paused schedules.

## Thermal model

Identify an equivalent constant squared torque for each motor during the 12-second pause. For each [development pause](junction_pause.md), invert the existing heating and cooling equation using the measured motor temperatures at pause entry and exit. Average the inferred loads within each first-stage approach and then weight the two approaches equally. The test predictor carries every motor temperature to the first junction, integrates the inferred loads over the pause, and then resumes the position-dependent branch forecast. The same planned-speed ramp and reactive slowdown state continue during the pause. The forecast holds position fixed and represents stance and rolling foot contacts through constant per-motor loads. It reuses the thermal model of the simulated controller.

Apply the fixed hold model to the 22 archived transfer schedules to compare thermal and time screening. Report peak and finish-time errors for completed walks. Where the robot reached the pause, compare the complete forecast of the hottest pause-exit temperature with the estimate obtained by starting the hold model at the measured per-motor entry temperatures. The second check measures the local pause model independently of error carried from the first stage.

## New course comparison

The [configuration](../experiments/pause_forecast.json) defines four new two-stage courses and fixes a 12-second pause, a 0.50 °C forecast margin, the existing thermal conditions, the simulated controller and a two-second online planning budget. This experiment evaluates three methods over all 24 starts. Each first tries the same reactive no-pause planner. That planner admits schedules only if their predicted peak is below 69.50 °C and their predicted elapsed time is within the deadline. The baseline rejects the start if no schedule qualifies.

On an initial planning rejection, the time-only fallback adds 12 s to the no-pause travel-time forecast and chooses the lowest nominal forecast peak among the schedules within the deadline. The per-motor fallback recomputes the complete paused forecast and tests both peak and elapsed time with the inherited margin. Both methods choose only from the original route and planned-speed options. Each selected schedule is executed once for a given start and pause duration, with identical selections sharing the trace. Compare completions, rejected plans, and failures across the three methods. Report the prespecified 10-percentage-point completion target with no additional thermal stops alongside the change in stops relative to the time-only fallback.

## Archived prediction check

The eight development pauses supplied four observations for each of the two first-stage approach speeds. On the separate archive of 22 selected schedules, the per-motor forecast with the 0.50 °C margin screened all 15 observed thermal stops and admitted four of the seven finishable schedules. Time screening alone admitted all 22. The three finishable schedules that the thermal screen rejected had peak forecasts of 69.60–69.87 °C.

On the seven completed walks, mean absolute error was 0.092 °C for the mission peak and 1.56 s for finish time. Adding 12 s to the original travel-time forecast gave 1.75 s of mean absolute finish-time error. On the 16 replays that reached the junction, mean absolute error in the predicted hottest temperature at the end of the pause was 0.195 °C. With observed entry temperatures supplied, the hold model's average absolute error across all 18 motors at the end of the pause was 0.030 °C.

## Results on the new courses

All 32 nominal branch profiles completed. All 72 decisions were within the two-second budget. Twenty-four distinct schedules were executed under the original simulated protection.

| Method | Completed | Planning rejection | Thermal stop |
| --- | ---: | ---: | ---: |
| Fixed reactive planner | 5/24 | 19 | 0 |
| Time-only pause fallback | 8/24 | 1 | 15 |
| Per-motor pause forecast fallback | 7/24 | 17 | 0 |

The per-motor forecast added two finishes over the fixed baseline, both on staggered banks and both under the near-boundary thermal setting with opposite warm sides. The gain was 8.3 percentage points, below the 10-point target. The descriptive map-resampled interval was 0 to 25 points. Relative to the time-only fallback, the forecast lost one finish and avoided all 15 observed thermal stops.

The missed finish occurred on deep second bank. The time-only method selected a paused walk that finished in 354.82 s under a 363 s deadline at 69.79 °C. Its paused forecast gave 69.62 °C, above the 69.50 °C planning cutoff. These results show the completion and thermal-stop trade-off from enforcing the existing margin with a pause model. The four maps are constructed scenarios, and the model was identified from one simulated junction.

[Configuration](../experiments/pause_forecast.json) · [Inferred motor loads](../results/pause_forecast/pause_model.json) · [Archived forecast check](../results/pause_forecast/archived_evaluation.json) · [New-course summary](../results/pause_forecast/summary.json) · [Plans](../results/pause_forecast/plans.json) · [Replays](../results/pause_forecast/executions.json)
