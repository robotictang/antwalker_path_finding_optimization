# Larger benchmark of the per-motor junction-pause planner

The [earlier four-course study](pause_forecast.md) recovered two finishes on one course with no observed thermal stops. This benchmark tests the same planner on 12 different courses, with six paired starts per course. The simulator, controller, thermal conditions, candidate speeds, learned hold loads, 12 s pause and 0.50 °C admission margin are frozen to that study.

## Design and decision rule

The [configuration](../experiments/pause_forecast_confirmation.json) fixes all course geometries and deadlines before simulation. Four courses reverse the bank sign on each branch between stages. Four retain it. Four have both branches leaning in the same direction on at least one stage. The course family labels describe bank geometry. They do not specify which motor will run hottest. Every map has two branching stages and a flat intermediate junction. The starts combine the two warm-side assignments with the three existing simulated thermal settings. The outcomes apply to these synthetic courses, thermal parameters and fixed graph topology.

Every planner first attempts the same per-motor reactive schedule with no pause. The fixed planner stops at a planning rejection. The time-only fallback tries a 12 s pause when a schedule's no-pause finish estimate leaves time for it. Its forecast peak ranks the candidates but has no admission ceiling. The per-motor fallback tries a pause only when its complete forecast fits the deadline and stays below 69.50 °C. All three have a two-second online budget and execute under the same 70 °C thermal stop. Candidate branches must finish nominal profiling at both speeds to enter the shared search space.

The primary estimate is the paired completion difference between the per-motor pause planner and the fixed reactive planner on all 72 starts. The practical target is at least a 10-percentage-point increase with no additional observed thermal stops. Eight net added finishes are required. The time-only fallback is the secondary comparison. Report outcomes by course, terrain family and thermal setting, plus a descriptive interval from resampling whole courses. Track whether gains are spread across courses. Separate planning rejection, thermal stop, deadline and other failures.

The reproducibility lock checks the inherited source hashes, model inputs and software versions. The frozen configuration and lock are saved before any new warm replay. The audit independently rechecks coverage of all paired decisions, the exact inherited model, and the saved physics traces.

## Results

All 96 nominal profiles completed, preserving the full route-and-speed set on each course. All 216 decisions stayed below the two-second budget. The longest took 0.169 s. Seventy-two distinct schedules were replayed and independently checked against the saved traces.

| Planner | Completed | Planning rejection | Thermal stop | Deadline miss |
| --- | ---: | ---: | ---: | ---: |
| Fixed reactive | 18/72 | 50 | 0 | 4 |
| Time-only pause fallback | 28/72 | 2 | 38 | 4 |
| Per-motor pause forecast | 20/72 | 48 | 0 | 4 |

Compared with the fixed reactive planner, the per-motor pause planner added two finishes and kept all 18 original finishes. The gain was **2.8 percentage points**. The descriptive 95% interval from resampling courses was 0.0 to 8.3 points. The result missed the 10-point target. Compared with the time-only fallback, it finished eight fewer starts and had 38 fewer thermal stops.

| Course | Fixed reactive | Time-only fallback | Per-motor forecast |
| --- | ---: | ---: | ---: |
| Switch shallow | 0 | 2 | 2 |
| Switch early | 1 | 2 | 1 |
| Switch long second | 1 | 2 | 1 |
| Switch long first | 0 | 2 | 0 |
| Persistent shallow | 4 | 4 | 4 |
| Persistent offset | 0 | 0 | 0 |
| Persistent long second | 4 | 5 | 4 |
| Persistent long first | 0 | 1 | 0 |
| Shared bank first | 2 | 3 | 2 |
| Shared bank second | 1 | 1 | 1 |
| Shared bank reversal | 2 | 2 | 2 |
| Shared bank late long | 3 | 4 | 3 |

Each course has six starts per planner. Both added finishes were on switch shallow, with opposite sides warm under the near-boundary thermal condition. The left-warm walk finished at 340.02 s and 68.96 °C. The right-warm walk finished at 341.44 s and 69.21 °C. The deadline was 342 s. Each used 65% planned speed on the first stage and full planned speed on the second, with opposite branch orders. The fixed planner rejected both starts. The comparison measures the effect of adding a paused fallback to the planner.

| Course family | Fixed reactive | Time-only fallback | Per-motor forecast |
| --- | ---: | ---: | ---: |
| Alternating | 2/24 | 8/24 | 4/24 |
| Persistent | 8/24 | 10/24 | 8/24 |
| Same bank sign on at least one stage | 8/24 | 10/24 | 8/24 |

The per-motor pause planner completed 13 of 24 near-boundary starts versus 11 of 24 for the fixed planner. Under the other thermal settings, completion was identical. The larger benchmark repeated the earlier pattern of gains on a single alternating-bank course. It supports a conditional result in simulation and provides an observed completion-versus-overheating trade-off with the time-only fallback.

[Configuration](../experiments/pause_forecast_confirmation.json) · [Frozen comparison](../results/pause_forecast_confirmation/confirmation_lock.json) · [Course, family, and thermal breakdowns](../results/pause_forecast_confirmation/confirmation_audit.json) · [Plans](../results/pause_forecast_confirmation/plans.json) · [Replays](../results/pause_forecast_confirmation/executions.json)
