# Transfer of calibrated reactive forecast margins

The calibrated margins screened every archived failure but did not transfer as a completion improvement. They finished 21 of 36 new starts, versus 22 with the fixed reactive margins, and admitted one thermal stop.

## Development calibration

The grid tested 99 pairs of thermal and deadline margins on the 34 archived warm replays. Fifteen pairs admitted all 19 finishes while excluding the 14 thermal stops and the single deadline miss. The prespecified tie-break selected 0.10 °C and 3.0 s, requiring peak forecasts below 69.90 °C and finish forecasts at least three seconds before the physical deadline. The inherited 0.50 °C and 0 s pair admitted 17 of the 19 finishes and the one deadline miss.

The leave-one-course-out check returned the same margins in three folds. Leaving out the crossed split selected 0.50 °C and 5.0 s, then rejected both finishes on that omitted course. The archived replays came from selected routes and fastest nominal probes. Their outcomes support calibration for these cases and leave the deadline margin especially dependent on one failure.

## Held-out evaluation

The six hand-designed courses and calibration were frozen before warm evaluation. The three start conditions and mirrored temperature assignments gave 36 starts per planner. Forty-one of the 42 nominal profiles completed. One branch on the reverse-banked fan failed at full speed and was excluded from all methods. All warm walks used the same simulated reactive controller, thermal derating and 70 °C stop.

| Forecast and margins | Completed | No admitted route | Thermal stop |
| --- | ---: | ---: | ---: |
| Stitched, 0.50 °C and 0 s | 22/36 | 14 | 0 |
| Reactive, 0.50 °C and 0 s | 22/36 | 14 | 0 |
| Reactive, 0.10 °C and 3 s | 21/36 | 14 | 1 |

All 108 planning decisions were within the two-second budget. The calibrated planner lost one finish relative to the fixed reactive planner, a change of −2.8 percentage points. The descriptive course-resampled interval was −8.3 to 0.0 points. The result fell short of the 10-point gain target with no additional thermal stops.

The calibrated margins changed five decisions. On the reverse-banked fan, the 3-second buffer made the planner pick a faster schedule on three starts. All six walks across those paired decisions finished. On a fourth start there, the buffer rejected the fixed planner's schedule. The forecast was 214.59 s and the walk finished in 214.66 s. The buffer moved the planning cutoff to 213 s on that 216 s course. On unequal banks, the narrower temperature margin admitted a schedule forecast to peak at 69.82 °C. The replay hit the 70 °C stop at 315.92 s. Its finish-time forecast would have passed either deadline margin.

Across the 55 shared replays, the fixed reactive margins admitted 34 of the 36 completed walks and screened all 19 thermal stops. The calibrated margins admitted 30 completed walks and one thermal stop. These screening counts cover planner-selected routes and fastest nominal probes. The paired mission counts above measure the actual choices the planners made.

The archived data supported 15 tied margin pairs and contained one deadline miss. The held-out results show that a pair selected from this archive can both admit an overheating schedule and reject a finishable one. The forecast-accuracy result from the earlier study remains separate from this transfer test.

[Protocol](reactive_margin_protocol.md) · [Frozen calibration](../results/reactive_margin_transfer/calibration.json) · [Held-out configuration](../experiments/reactive_margin_transfer.json) · [Summary](../results/reactive_margin_transfer/summary.json) · [Paired plans](../results/reactive_margin_transfer/plans.json) · [Replay outcomes](../results/reactive_margin_transfer/executions.json)
