# Does bank order change the value of motor identities?

Three new course templates each used the same two physical stages and deadline in both orders. Reversing the stages also reversed the nominal loading order on both branches in all three templates. In the standalone profiles, the negative bank stage consistently required more squared femur-joint torque on the right. The positive bank stage consistently required more on the left. All 48 nominal branch-and-speed profiles completed.

The [original matched run](../results/matched_load_order/summary.json) produced no admitted routes for either planner across 24 starts each at the initial two thermal settings. The [supplemental run](../results/matched_load_order_boundary/summary.json) used two lower simulated heating multipliers, 0.43 and 0.44, with 120 s cooling. Both values were chosen from nominal forecasts after the original matched run produced no admissions, before any continuous warm replay at the new settings. Geometry, starting temperatures within each new warm-side pair, deadlines, margin, and controller were shared across planners. The follow-up reused the nominal profiles.

## Supplemental outcomes

| Outcome | Anonymous baseline | Per-motor |
| --- | ---: | ---: |
| Completed | 7/24 | 13/24 |
| No admitted route | 8 | 2 |
| Deadline | 9 | 9 |
| Thermal stop | 0 | 0 |

All 48 decisions were under the original 2 s online search budget. The 32 distinct continuous warm replays produced 16 completions and 16 deadline misses. The per-motor method finished six starts the baseline missed. The baseline finished zero starts that the per-motor method missed. The gain was 25 percentage points. Its descriptive interval, from resampling the three templates, was +12.5 to +37.5 points. This interval describes the selected test conditions.

| Course template | Right-loaded stage first, baseline / per-motor | Left-loaded stage first, baseline / per-motor |
| --- | --- | --- |
| Shallow banks | 2 / 3 | 3 / 4 |
| Long banks | 0 / 0 | 0 / 1 |
| Wide banks | 1 / 2 | 1 / 3 |

Each order has four matched starts per template. Reversing the stages changed completion for each planner in three of the 12 template–setting–start comparisons. All three per-motor changes were gains for right-warm starts when the left-loaded stage came first. The baseline's changes went in both directions. The per-motor advantage changed in six of the 12 comparisons. The two planners could choose a different branch and planned speed after the order changed. The experiment establishes the effect of reversing the course order under each planner, with the initial temperatures held fixed.

## Paper scope

Keep the [original 36-start benchmark](mission_completion.md) as the primary test of an overall gain. Its 2.8-point gain fell short of the 10-point criterion. The selected supplemental operating range exceeded that target and supports a conditional finding about completion near the admission boundary. In this range the gain combined fewer rejected routes with different deadline outcomes across starts. Those conditions differ from a broad mix of terrains and actuator settings.

The [seven-case replay analysis](discordant_replays.md) explains why the planner can reject finishable walks and admit plans that overheat. Include it as a mechanism and limitation. Treat the continuous temperature-forecast result as supporting evidence. Scope the claims to the simulated controller, assumed motor parameters, and constructed bank-order templates.

[Protocol](matched_load_order_protocol.md) · [Supplemental configuration](../experiments/matched_load_order_boundary.json) · [Paired decisions](../results/matched_load_order_boundary/plans.json) · [Trace and outcome summary](../results/matched_load_order_boundary/summary.json)
