# Hot-motor-swap simulation data

This snapshot contains the saved outputs supporting *Swapping Initial Motor Temperatures Changes Route Feasibility for a Simulated Hexapod*. The experiments use MuJoCo and a simulated actuator thermal model.

| Manuscript location | Results folder | Start here |
| --- | --- | --- |
| Main study and Appendix A | [hot_motor_swap](results/hot_motor_swap/) | [Summary](results/hot_motor_swap/summary.json), [planner decisions](results/hot_motor_swap/plans.json), [288 execution records](results/hot_motor_swap/executions.json) |
| Matched junction-pause study in Appendix B | [matched_pause](results/matched_pause/) | [Summary](results/matched_pause/summary.json), [audit](results/matched_pause/audit.json) |
| Fixed-schedule diagnostic in Appendix B and comparator results in Appendix C | [pause_forecast_confirmation](results/pause_forecast_confirmation/) | [Screening diagnostic](results/pause_forecast_confirmation/screening_diagnostic.json), [summary](results/pause_forecast_confirmation/summary.json) |
| Adapted thermal speed comparison in Appendix C | [published_speed_baseline](results/published_speed_baseline/) | [Summary](results/published_speed_baseline/summary.json), [execution records](results/published_speed_baseline/executions.json) |

Each execution record identifies a trace relative to its results folder, with a checksum. The main-study snapshot includes 96 nominal branch profiles and 288 warm-walk traces. The other folders contain the saved replays and comparison summaries for the listed appendix results. The archived configuration and source fingerprints are in the manifests and evaluation locks.

For the code and original commands, use the [thermal routing project at commit 46a385b](https://github.com/robotictang/antwalker_path_finding_optimization/tree/46a385b8432d0887319d89abb04efd643e7e6c0e/Pathfinder/IEEE_Journal_ver) and the [hot-motor-swap protocol](https://github.com/robotictang/antwalker_path_finding_optimization/blob/46a385b8432d0887319d89abb04efd643e7e6c0e/Pathfinder/IEEE_Journal_ver/docs/hot_motor_swap_protocol.md). The results paths in this archive are relative to the thermal routing project directory.
