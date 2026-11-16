# Thermal margin transfer to fresh networks

The previously selected **0.75 °C** margin screened all four modeled thermal stops on the three new courses. The prespecified **0.50 °C** comparison also screened all four and retained four more finishable decisions. The 0.50 °C setting was chosen as a comparator from the earlier test, before the new courses ran.

The experiment kept the original development calibration and used three asymmetric networks, three thermal settings, and the same two warm-start patterns. Two networks had three stages. The longer network spanned 65.25 m along the course axis and had four stages and 16 possible routes. All courses shared a 550 s deadline. The geometry and cooling conditions were chosen to check transfer near the earlier operating boundary. The courses were constructed variants of the same route-network family.

All 60 standalone branch profiles completed. The 54 zero-margin decisions across three planners and 18 paired starts led to 26 distinct continuous physics replays. Twenty-two replays finished and four reached the modeled 70 °C stop. Multiple planners shared some replays. Every margin was applied to the same lowest-predicted-peak plans. A finishable rejection is counted when a stricter admission rule blocks a zero-margin plan that completed in its replay.

| Margin (°C) | Admitted decisions / 54 | Completed decisions / 54 | Thermal stops | Finishable decisions rejected |
| ---: | ---: | ---: | ---: | ---: |
| 0.00 | 35 | 31 | 4 | 0 |
| 0.50 | 27 | 27 | 0 | 4 |
| 0.75 | 23 | 23 | 0 | 8 |

| Planner | Completions at 0 °C / 18 | At 0.50 °C / 18 | At 0.75 °C / 18 |
| --- | ---: | ---: | ---: |
| Fixed-speed per-motor routing | 10 | 8 | 6 |
| Planned speeds on fastest nominal route | 7 | 6 | 6 |
| Joint route and speed | 14 | 13 | 11 |

Zero margin admitted two thermal stops each for fixed-speed per-motor routing and joint route-and-speed planning. On the four-stage course, joint planning completed three of six starts and hit one thermal stop at zero margin. Both margins screened that stop and retained two completions. The other two starts already had no plan at zero margin. Course geometry varied with stage count, so the comparison does not isolate the effect of route length.

The worst observed test underprediction was 0.639 °C on a completed mission. That forecast had 0.833 °C of headroom, and the replay peaked at 69.806 °C. All four thermal stops had predicted headroom between 0.191 and 0.356 °C. The observed error therefore exceeded 0.50 °C on one mission even though that threshold screened every stop. The 0.50 °C result supports a completion-versus-rejection trade-off in these simulated courses. The thermal parameters are uncalibrated, and the sample does not establish an error bound for future walks.

[Configuration](../experiments/thermal_margin_transfer.json) · [Frozen manifest](../results/thermal_margin_transfer/manifest.json) · [Results by course and setting](../results/thermal_margin_transfer/summary.json) · [Executions](../results/thermal_margin_transfer/executions.json)
