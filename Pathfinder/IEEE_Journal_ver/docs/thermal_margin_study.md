# Thermal margins for branch-profile predictions

**A 0.50 °C margin was the smallest tested value that screened out all four observed thermal stops across the three test planners.** It rejected one decision whose route completed. The 0.75 °C margin selected from development data also screened out all four stops and rejected three finishable decisions.

## Development selection

The previous two network courses provided 19 distinct mission traces for calibration. The largest observed underprediction was 0.694 °C. Rounding up to the nearest value on the prespecified grid selected 0.75 °C before the new courses were run. Under the modeled 70 °C motor limit, this admits predictions strictly below 69.25 °C. Thermal-stop traces contribute their observed peak through the stop.

## Test on new courses

The test used three new asymmetric networks, four thermal settings, two warm starts, and three planning policies. All 54 branch profiles completed. The 72 zero-margin decisions yielded 23 distinct continuous mission replays. Nineteen replays completed and four stopped at the modeled thermal limit. Multiple policies used some of the same replays, so the table counts decisions across policies. The 72 decisions are paired across 24 starts.

| Margin (°C) | Admitted | Completed | Thermal stops | Finishable decisions rejected |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 32 | 28 | 4 | 0 |
| 0.25 | 30 | 28 | 2 | 0 |
| 0.50 | 27 | 27 | 0 | 1 |
| 0.75 | 25 | 25 | 0 | 3 |
| 1.00 | 22 | 22 | 0 | 6 |
| 1.25 | 19 | 19 | 0 | 9 |
| 1.50 | 18 | 18 | 0 | 10 |
| 2.00 | 18 | 18 | 0 | 10 |

Fixed-speed per-motor routing needed 0.50 °C on the tested grid to screen its two thermal stops. The planner that scheduled speeds on the fastest route needed 0.25 °C to screen its two stops. Joint route-and-speed planning completed 12 of 24 starts at every margin from 0 to 0.75 °C. Its 12 remaining starts were rejected at zero margin. Its lowest predicted headroom among executed plans was about 0.91 °C. At 1.00 °C, it rejected two more finishable decisions.

The largest observed test underprediction was 0.508 °C on a mission that still completed. The four failed forecasts had headroom between 0.075 and 0.356 °C. One successful fixed-speed mission had 0.298 °C of predicted headroom and peaked at 69.997 °C in simulation. A single headroom threshold cannot retain that mission while screening the failure with 0.356 °C headroom.

The 0.50 °C result is specific to the observed test set. The 0.75 °C margin is the independently selected value assessed on that test set. Both values depend on the simulated motor model, controller, and route profiles. The test filters each planner's lowest-peak plan. The study did not execute alternative routes for cases with no plan at zero margin or estimate an uncensored peak past a thermal stop.

[Configuration](../experiments/thermal_margin_study.json) · [Frozen manifest](../results/thermal_margin_study/manifest.json) · [Summary and errors](../results/thermal_margin_study/summary.json) · [Decisions](../results/thermal_margin_study/plans.json) · [Executions](../results/thermal_margin_study/executions.json)
