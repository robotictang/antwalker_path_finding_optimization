# Joint planning of route and speed

The same 16 matched starts from the [route-network study](network_study.md) were evaluated with two additional methods. Each could schedule an edge at 100%, 80%, or 65% of the nominal crawl speed. Both used per-motor temperature forecasts and the original 440 s deadline and 70 °C limit. One method stayed on the fastest nominal route. The other searched all branch and speed combinations. The experiment used 36 nominal edge profiles and seven new continuous physics replays. It reused verified baseline executions when the route and speed were identical.

| Method | Completed / 16 | Thermal stop | No route |
| --- | ---: | ---: | ---: |
| Fastest nominal route, fixed speed | 8 | 8 | 0 |
| Fastest nominal route, reactive slowing | 8 | 8 | 0 |
| Per-motor route, fixed speed | 11 | 0 | 5 |
| Per-motor route, reactive slowing | 11 | 0 | 5 |
| Fastest nominal route, planned speeds | 9 | 1 | 6 |
| Joint per-motor route and speed | 12 | 0 | 4 |

All methods completed four of four starts under both the low and middle thermal settings. Under slower cooling, joint planning completed four of four, compared with three for fixed-speed per-motor routing and one for planned speeds on the fastest route. No method completed a high-heating start. Both new methods rejected all four high-heating starts under their modeled deadline and heat constraints.

The additional completion was the left-warm start on the staggered-banks course with slower cooling. Both proactive speed planners recovered that start. Joint planning chose the all-right route at 100%, 65%, and 100%, reaching the goal in 376.2 s at 68.96 °C. The fastest nominal route with those speeds also completed in 374.7 s and peaked at 69.83 °C. For the other three slower-cooling starts, the joint method completed and the speed planner restricted to the fastest route either rejected the mission or hit the modeled heat limit. All four successful joint plans in this setting reduced the middle-edge speed to 65%. On the three starts already completed by fixed-speed per-motor routing, the joint method added 46.9–49.7 s and reduced peak temperature by 0.47–0.79 °C.

The planned-speed method restricted to the fastest route admitted one mission predicted to peak at 69.70 °C that instead reached the 70 °C stop in continuous physics. The prediction used standalone nominal-torque profiles and omitted the effects of speed transitions, carried gait state, and derating on actual torque. The test establishes what these policies did on the two existing courses with uncalibrated thermal parameters. A larger evaluation can use the prediction error to set a margin on separate development maps before testing it on new networks.

[Manifest](../results/route_speed_study/manifest.json) · [Decisions](../results/route_speed_study/decisions.json) · [New mission traces](../results/route_speed_study/executions.json) · [Audit](../results/route_speed_study/audit.json)
