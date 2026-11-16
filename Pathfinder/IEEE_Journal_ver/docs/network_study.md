# Per-motor route search and reactive slowing

Two continuous MuJoCo courses had three successive junctions, six directed edges and eight possible routes each. The [frozen manifest](../results/network_study/manifest.json) fixes two warm-start patterns, four thermal settings and the same 440 s deadline for every method. All 12 nominal edge profiles completed. The 64 paired decisions used 42 distinct continuous physics replays.

| Route and speed policy | Completed / 16 | Thermal stop | No route |
| --- | ---: | ---: | ---: |
| Fastest nominal route, fixed speed | 8 | 8 | 0 |
| Fastest nominal route, reactive slowing | 8 | 8 | 0 |
| Per-motor route, fixed speed | 11 | 0 | 5 |
| Per-motor route, reactive slowing | 11 | 0 | 5 |

| Thermal setting | Heating multiplier | Cooling time constant (s) | Each fastest-route method / 4 | Each per-motor method / 4 |
| --- | ---: | ---: | ---: | ---: |
| Low | 0.39 | 100 | 4 | 4 |
| Middle | 0.45 | 100 | 4 | 4 |
| Slow cooling | 0.45 | 120 | 0 | 3 |
| High | 0.55 | 100 | 0 | 0 |

The three additional per-motor completions occurred under slower cooling. The planner changed the second edge for the left-warm start on the alternating course. It selected an all-left route for the right-warm start on both courses. The per-motor methods rejected the remaining slow-cooling start and all four high-heating starts. The rejection means the search found no admissible route under its nominal edge profiles, so the physical feasibility of unexecuted paths remains unknown.

Reactive slowing ramped the speed command to 65% at 67 °C. It activated on nine fastest-route missions. Eight still stopped at the thermal limit. The ninth also finished at fixed speed. On the three per-motor routes where slowing activated, it reduced peak temperature by 0.19–0.46 °C and added 71–80 s, with the same completion outcomes. Those runs isolate the effect of slowing on the same routes.

The search carries all motor temperatures through the graph using nominal profiles collected by walking each edge separately. A mission replay runs the selected path continuously and retains chassis state, gait phase and temperature at junctions. Profile concatenation approximates that continuous mission. The combined method chooses a route with the fixed-speed thermal model and slows during execution, so it leaves routes that would be feasible only at reduced speed unexplored. This comparison covers one threshold-based slowing policy and two constructed courses with uncalibrated motor parameters.

[Raw decisions](../results/network_study/decisions.json) · [Executions](../results/network_study/executions.json) · [Trace audit](../results/network_study/audit.json)
