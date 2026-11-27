# Hot-motor-swap thermal routing

*Swapping Initial Motor Temperatures Changes Route Feasibility for a Simulated Hexapod* compares route choices made with individual motor temperatures against choices made with their mean and maximum.

- [Array manuscript (Word)](Elsevier%E2%80%99s%20journal%20Array.docx)
- [Browse the versioned simulation data](https://github.com/robotictang/antwalker_path_finding_optimization/tree/hot-motor-swap-data-v1.0.0) or [download the data snapshot (ZIP)](https://github.com/robotictang/antwalker_path_finding_optimization/archive/refs/tags/hot-motor-swap-data-v1.0.0.zip)
- [Study protocol](../docs/hot_motor_swap_protocol.md), [frozen configuration](../experiments/hot_motor_swap.json), and [reproduction commands](../README.md#run-the-exhaustive-hot-motor-swap-test)

## Study data

| Manuscript location | Saved output |
| --- | --- |
| Main results and Appendix A | [Route and planner outcomes](https://github.com/robotictang/antwalker_path_finding_optimization/blob/hot-motor-swap-data-v1.0.0/results/hot_motor_swap/summary.json) for 288 warm walks and 96 nominal branch profiles |
| Appendix B | [Matched junction-pause results](https://github.com/robotictang/antwalker_path_finding_optimization/blob/hot-motor-swap-data-v1.0.0/results/matched_pause/summary.json) and [fixed-schedule screening diagnostic](https://github.com/robotictang/antwalker_path_finding_optimization/blob/hot-motor-swap-data-v1.0.0/results/pause_forecast_confirmation/screening_diagnostic.json) |
| Appendix C | [Earlier pause and adapted speed comparisons](https://github.com/robotictang/antwalker_path_finding_optimization/blob/hot-motor-swap-data-v1.0.0/results/published_speed_baseline/summary.json) |

The versioned snapshot includes the trace files, execution indexes, summaries, and study manifests for these comparisons. The code and configuration are in [the thermal routing project](../README.md).

[Springer-formatted copy](../Springer%2CComplex-Intelligent-system-Submission/) · [Earlier IEEE draft](../manuscript/ieee-access-v3-hot-motor-swap/README.md)
