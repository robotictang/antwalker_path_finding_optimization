# In-place crawl at the junction on unequal banks

The [exhaustive schedule audit](schedule_audit.md) found that all 16 original schedules hit the thermal stop with the left-side motors warm on unequal banks. This follow-up adds one action to those same schedules and asks whether any can finish.

The [configuration](../experiments/junction_pause.json) fixes in-place crawl durations of 6, 12 and 24 s, all multiples of the 3 s gait cycle. At the first crossing of the flat junction, the speed override commands zero forward speed for the specified duration. The robot still cycles its feet and supports its weight. The planned-speed ramp, reactive speed controller, gait phase and thermal state continue during the dwell. The original 352 s deadline and 70 °C thermal stop apply.

Test all 16 route-and-speed schedules at each duration. For eight schedules, the original trace stops before the pause can trigger. Their outcomes carry over because the commanded speed before the junction is identical. The other eight schedules receive continuous warm physics replays at each duration. One extra zero-pause replay checks that the wrapper reproduces the original trace. Record thermal readings and planar displacement during each pause to distinguish cooling from the effect of changing subsequent motion.

A completion in this study would show that a pause can make a tested schedule feasible on this start. Route choice, pause-location optimization, and performance on other starts and courses are outside this diagnostic.

## Results

| Junction pause | Completed | Thermal stop | Deadline |
| --- | ---: | ---: | ---: |
| None, archived | 0/16 | 16 | 0 |
| 6 s | 0/16 | 15 | 1 |
| 12 s | 1/16 | 14 | 1 |
| 24 s | 0/16 | 14 | 2 |

The only completion used the first branch on both stages, with full planned speed on the first stage and 65% on the second. The zero-pause control for that same schedule reproduced the original torque, body position, contact count, and temperature arrays exactly. It hit the thermal stop at 315.92 s.

| Pause on that schedule | Hottest motor at pause end | Mission peak | Outcome |
| --- | ---: | ---: | --- |
| 6 s | 66.29 °C | 70.00 °C | Thermal stop at 325.16 s |
| 12 s | 65.79 °C | 69.91 °C | Finished in 350.32 s |
| 24 s | 64.84 °C | 69.67 °C | Deadline at 352 s |

The hottest motor at pause entry was the left front femur at 66.75 °C. Its temperature fell 0.96 °C during the successful 12 s pause, while the body moved at most 6.83 cm from its pause-entry position. Across all 24 pause replays, the hottest-motor temperature was lower at pause end than at entry. The successful walk finished 1.68 s before the deadline and 0.09 °C below the thermal stop. The other tested pauses on its schedule illustrate the trade-off. The 6 s pause still ended in a thermal stop, while the 24 s pause kept the observed peak below the limit through the deadline.

This run establishes feasibility for one additional schedule on the selected start. The pause also changes the robot's contact and controller history, and the study does not isolate how much of the subsequent outcome comes from each change.

[Configuration](../experiments/junction_pause.json) · [Manifest and archive references](../results/junction_pause/manifest.json) · [Schedule outcomes and traces](../results/junction_pause/summary.json)
