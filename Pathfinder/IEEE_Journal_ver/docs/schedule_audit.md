# Exhaustive replay of adverse route decisions

The earlier forecasts and margins changed some choices even though the MuJoCo controller and course stayed the same. This diagnostic checks whether available schedules could finish on the starts where those changes hurt.

## Selection and execution

The selection includes every lost finish in the existing-versus-reactive forecast comparison and the fixed-versus-calibrated reactive margin comparison. It also includes every thermal stop selected by the newer method in either comparison. This gives four case starts across three courses. These cases were selected using the earlier outcomes.

Enumerate the full Cartesian product of available branch and planned speed options at each junction. Availability follows the original tests, which required a successful nominal profile at both the 100% and 65% speed commands for a branch. The warm replay always starts at the original per-motor temperatures and retains the original reactive slowdown, torque derating, deadline and 70 °C stop. Both valid archived replays and new runs receive the same trace checks. There are 52 distinct case-and-schedule pairs.

For each replay the audit records the actual completion, deadline miss, or thermal or locomotion stop. Forecast screens distinguish planned thermal rejection from deadline rejection. Compare the inherited reactive margin of 0.50 °C and 0 s, the calibrated 0.10 °C and 3 s, and zero extra headroom. For each screen, reproduce the planner's selection rule of lowest forecast peak, then earliest forecast finish, then schedule identifier. The zero-margin screen is retrospective.

Exhaustive replay gives the best achievable result within the tested schedule set, controller, and start state. It provides no estimate of how often the original planners make these errors on new courses.

## Outcomes

| Course and start | Schedules | Finished | Thermal stop | Deadline |
| --- | ---: | ---: | ---: | ---: |
| Crossed split, left warm | 16 | 1 | 15 | 0 |
| Crossed split, right warm | 16 | 2 | 12 | 2 |
| Reverse-banked fan, right warm | 4 | 2 | 2 | 0 |
| Unequal banks, left warm | 16 | 0 | 16 | 0 |
| **Total** | **52** | **5** | **45** | **2** |

Forty-four replays are new and eight were verified from the archives. The three lost finishes had feasible schedules. On the crossed split, the original 0.50 °C margin excluded all three finishable schedules across the two starts. All three used 65% planned speed on the first stage and 100% on the second. The first branch changed with the warm side. The fastest right-warm schedule completed in 323.72 s at 69.96 °C, even though its peak forecast was 70.41 °C. It would have been screened at zero margin. On the reverse-banked fan, the 3-second buffer rejected both feasible schedules. They completed in 214.08 s and 214.66 s under a 216 s deadline.

All 16 schedules overheated on the left-warm unequal-banks case. The lower margin admitted one of them. Under the tested controller and route-and-speed options, rejecting the start was the only way for the planner to avoid a thermal stop.

## Why a shared margin cannot fix both cases

| Schedule | Forecast thermal headroom | Forecast deadline headroom | Observed outcome |
| --- | ---: | ---: | --- |
| Only finishable schedule on the left-warm crossed split | 0.135 °C | 4.69 s | Finished |
| Schedule selected on left-warm unequal banks | 0.185 °C | 13.81 s | Thermal stop |

The unequal-banks schedule had more forecast headroom on both measures. Any shared temperature and deadline margins that admit the only finishable crossed-split schedule also admit that unequal-banks schedule. Since every tested choice there overheats, a common pair of fixed margins cannot recover that crossed-split finish and keep the unequal-banks start from selecting a thermal stop. The finding applies to this forecast, these selected starts, and the tested schedule set.

[Forecast comparison](reactive_forecast.md) · [Margin transfer](reactive_margin_transfer.md) · [Schedule outcomes and trace links](../results/schedule_audit/summary.json) · [Replay manifest](../results/schedule_audit/manifest.json)
