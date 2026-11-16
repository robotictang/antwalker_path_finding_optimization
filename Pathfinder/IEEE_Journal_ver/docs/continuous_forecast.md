# Continuous route profiles and thermal forecasts

This comparison uses the 26 distinct thermal replays from the [margin transfer experiment](thermal_margin_transfer.md). The original predictor stitched together torque profiles collected from standalone branches. The continuous predictor profiled each of the 19 distinct route and speed schedules in one MuJoCo walk at nominal torque limits, then applied the same motor model and warm starts. Both predictors were scored against the same continuous warm replays. All nominal route profiles completed.

## Forecast accuracy

Peak-temperature errors use the 22 warm replays that reached the goal. Thermal-stop traces end when the simulated temperature reaches the limit, so their full-mission peak is unavailable.

| Metric | Stitched branch profiles | Continuous route profiles |
| --- | ---: | ---: |
| Mean absolute error | 0.140 °C | 0.028 °C |
| Mean observed minus predicted | +0.140 °C | −0.019 °C |
| Largest underprediction | 0.639 °C | 0.093 °C |

The continuous predictor was closer on 12 walks, the stitched predictor on one, and nine tied within numerical tolerance. Mean absolute error decreased on each course. On the four-stage course, it fell from 0.036 °C to 0.003 °C across four completed replays.

## Admission

The following counts are unique replays. The earlier transfer report counts each planner's decisions, which sometimes share a replay.

| Profile | Margin (°C) | Completions retained | Thermal stops admitted | Finishable replays rejected |
| --- | ---: | ---: | ---: | ---: |
| Stitched | 0.00 | 22 | 4 | 0 |
| Stitched | 0.50 | 18 | 0 | 4 |
| Stitched | 0.75 | 14 | 0 | 8 |
| Continuous | 0.00 | 21 | 0 | 1 |
| Continuous | 0.50 | 14 | 0 | 8 |
| Continuous | 0.75 | 13 | 0 | 9 |

With zero extra margin, the continuous forecast screened all four observed thermal stops and retained three more finishable replays than the stitched forecast with a 0.50 °C margin. Its one finishable rejection had a nominal forecast of 70.309 °C and a warm replay peak of 69.977 °C. Temperature-dependent torque derating was active in that replay. The nominal profile omits that feedback, so the comparison cannot isolate its effect from the changes in the robot's motion.

The test covers schedules selected by the original branch-based planner on three constructed courses. It estimates the effect of profiling shortlisted plans and does not measure the outcome of selecting alternative routes after a rejection. A continuous profile requires one full nominal simulation for each distinct candidate schedule. The result supports evaluating it as a second check on shortlisted plans. The four observed stops and the uncalibrated motor parameters limit any claim about future admission errors.

[Input manifest](../results/continuous_forecast_transfer/manifest.json) · [Paired forecasts](../results/continuous_forecast_transfer/forecasts.json) · [Summary by course](../results/continuous_forecast_transfer/summary.json)
