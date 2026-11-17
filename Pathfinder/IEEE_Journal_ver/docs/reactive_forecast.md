# Forecasting reactive slowdown on new courses

Modeling slowdown improved forecast accuracy on completed walks. At the shared 0.50 °C margin, it completed 12 of 24 starts versus 13 of 24 with the existing forecast. This is a −4.2 percentage-point change, below the prespecified +10-point target. The descriptive interval from resampling the four maps was −25.0 to +12.5 points.

## Paired results

| Forecast used by the planner | Finished | No admitted route | Thermal stop | Longest online decision |
| --- | ---: | ---: | ---: | ---: |
| Existing stitched profiles | 13/24 | 11 | 0 | 0.007 s |
| Position profiles at planned speed | 13/24 | 10 | 1 | 0.057 s |
| Position profiles with reactive slowdown | 12/24 | 12 | 0 | 0.083 s |

All 72 decisions were under the two-second budget. The planners shared the same 24 starts and executed with the same reactive controller and derating. Of 28 nominal profiles, 26 completed, one hit the chassis-contact or fall condition, and one reached the nominal profiling deadline. The two affected branches were excluded from every planner because they lacked a complete profile at one of the two allowed speeds.

The reactive forecast admitted one additional finish on the steep fan. Its 68.67 °C forecast was close to the observed 68.93 °C, while the existing model forecast 70.03 °C for that schedule. On the crossed split, both schedules the existing planner chose finished, but the reactive forecast rejected them. For the left-warm start it forecast 69.87 °C and observed 69.87 °C, above the 69.50 °C admission ceiling but below the 70 °C stop. For the right-warm start it forecast 69.56 °C and observed 68.99 °C. The stricter decision was driven by the margin in the first case and an overestimate that crossed the margin in the second. Both actual finish times were within the course deadline.

## Forecast accuracy

| Forecast | Mean absolute peak-temperature error | Mean absolute finish-time error | Finished replays rejected | Failed replays admitted |
| --- | ---: | ---: | ---: | ---: |
| Existing stitched profiles | 0.299 °C | 24.08 s | 1 | 0 |
| Position profiles at planned speed | 0.256 °C | 23.69 s | 1 | 1 thermal stop |
| Position profiles with reactive slowdown | 0.088 °C | 1.46 s | 2 | 1 deadline |

The screening comparison uses the same 34 warm physics replays for all three forecasts. It includes selected routes and fastest nominal probes. The error comparison uses the 19 completed replays, which have observed full-route peaks and finish times. The reactive forecast correctly indicated whether slowdown ever activated on all 34 replays in this sample. For the 30 activations, its mean absolute error in first trigger time was 1.83 s.

These results support a forecast-accuracy result in simulation and show how a fixed safety margin can suppress a finish even when the peak forecast is accurate. The margin was inherited from earlier tests of the stitched forecast. The experiment uses four hand-designed maps and assumed motor parameters. The screening numbers describe the sampled schedules, and the completion comparison describes the predeclared operating conditions.

[Protocol](reactive_forecast_protocol.md) · [Configuration](../experiments/reactive_forecast.json) · [Summary](../results/reactive_forecast/summary.json) · [Decisions](../results/reactive_forecast/plans.json) · [Schedule forecasts](../results/reactive_forecast/schedule_forecasts.json) · [Execution outcomes](../results/reactive_forecast/executions.json)
