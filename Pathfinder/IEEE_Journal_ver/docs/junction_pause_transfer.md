# Transfer of a fixed 12-second junction pause

The [development test](junction_pause.md) found one schedule that finished when it paused at the junction on unequal banks. This experiment fixes the pause at 12 s and tests it across the four other two-stage courses from the earlier [reactive forecast](reactive_forecast.md) and [margin transfer](reactive_margin_transfer.md) experiments. These courses had been simulated without the pause and were outside its development case.

## Schedule selection

Keep the original 0.50 °C-margin reactive planner's route and planned speeds when it admits a schedule. For an original rejection, screen all supported schedules against the course deadline minus 12 s, using the existing reactive forecast without pause dynamics. Among those with enough predicted time, choose the lowest forecast peak, then the earliest forecast finish and the schedule identifier. The fallback has no forecast temperature cutoff and the 70 °C physics stop remains active. Freeze these decisions before any pause walks. The selection rule uses archived planning decisions and nominal profiles.

Replay each selected schedule at zero and 12 s of pause with the same per-motor start, deadline, gait and derating. The pause commands zero forward speed on entering the first junction and leaves foot cycling active. Reuse a no-pause trace when the same schedule already exists in its source experiment. Compare the recorded arrays up to the pause onset for every pair. If no pause triggers, require identical arrays through the end.

The primary comparison is matched schedules, with all outcomes counted. A secondary calculation keeps every original admission and attempts a paused fallback only on original rejections with a selected schedule. It counts rejections, fails and completions across all 24 starts. It can show whether a pause-only fallback added finishes and how many extra stops it required. This is a simulation of a search rule using the original forecast with a time allowance. The simulation does not forecast how the pause changes the individual motors.

## Results

| Course | Matched schedules | Completed without pause | Completed with 12 s pause |
| --- | ---: | ---: | ---: |
| Crossed split | 6 | 0 | 3 |
| Staggered split | 5 | 2 | 2 |
| Crossover banks | 5 | 1 | 1 |
| Long entry split | 6 | 1 | 1 |
| **Total** | **22** | **4** | **7** |

Of 24 starts, two had no schedule with 12 s of predicted time to spare. The 22 pairs used 41 new warm replays and three archived controls. Each pair matched sample by sample before the pause. The six pairs that overheated before arrival matched through the end.

The pause converted three thermal stops into completions on crossed split. The four schedules that finished without a pause also finished with it. All other selected walks overheated, and there were no deadline misses. The 16 pauses that triggered reduced the hottest-motor temperature by 0.85 to 1.28 °C. The three recovered walks finished at 69.67 to 69.83 °C, with 1.18 to 20.16 s to spare.

| Policy across all 24 starts | Completed | Planning rejection | Thermal stop |
| --- | ---: | ---: | ---: |
| Original reactive planner | 3 | 21 | 0 |
| Original planner with paused fallback | 7 | 2 | 15 |

The fallback adds four completions and 15 thermal stops. One of the four added completions was already feasible on the same schedule without pausing. Three completions were recovered by changing only the pause. This comparison establishes that the fixed pause can recover feasibility on another course, with the observed gain concentrated on one of the four transfer courses. A fallback that budgets time alone attempts many schedules that still overheat.

[Configuration](../experiments/junction_pause_transfer.json) · [Frozen schedule manifest](../results/junction_pause_transfer/manifest.json) · [Paired outcomes and traces](../results/junction_pause_transfer/summary.json)
