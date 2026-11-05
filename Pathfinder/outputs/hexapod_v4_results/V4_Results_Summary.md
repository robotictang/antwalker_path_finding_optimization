# Hexapod version 4 measured comparison

29 October 2026

The new method adds obstacle/terrain landmarks and continuous waypoint movement to an initial safe route whose search cost counts toward the total budget. The common balanced score and resource checks are unchanged. Parameter tuning used 8 development worlds and two profiles per tuned optimizer. Test results use 24 fresh worlds and three paired seeds; the scientific code and manifest were frozen before testing.

PSO and ACO with the same continuous polishing operator are included as stronger representation controls. Their baseline parameters come from development selection. No result from another method is used by the V4 planner. This is parameter tuning, not training a neural network.

## Results in each experiment

- V4 tied best: 35 of 72
- Another method scored lower: 14 of 72
- All rejected: 3 of 72
- V4 best score: 20 of 72

A best-score verdict compares admitted balanced routes in one world/repetition. It does not mean best in every physical metric, fastest search, or universal superiority.

## Complete paired comparisons

| Baseline | V4 wins | Ties | V4 losses | Only V4 admitted | Only baseline admitted | Both rejected | Mean world score improvement % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Distance A* | 66 | 0 | 0 | 3 | 0 | 3 | 10.9892 |
| Terrain A* | 66 | 0 | 0 | 3 | 0 | 3 | 10.8413 |
| Energy A* | 66 | 0 | 0 | 3 | 0 | 3 | 7.2522 |
| Weighted A* | 66 | 0 | 0 | 3 | 0 | 3 | 6.7832 |
| Greedy | 51 | 15 | 0 | 3 | 0 | 3 | 2.4564 |
| PSO | 51 | 15 | 0 | 3 | 0 | 3 | 2.0710 |
| ACO | 51 | 15 | 0 | 3 | 0 | 3 | 2.0668 |
| Old grid proposal | 66 | 0 | 0 | 3 | 0 | 3 | 7.3626 |
| Proposal v3 | 51 | 15 | 0 | 3 | 0 | 3 | 2.0163 |
| PSO + polishing | 19 | 37 | 10 | 3 | 0 | 3 | 0.7323 |
| ACO + polishing | 19 | 34 | 13 | 3 | 0 | 3 | 0.6885 |

## Admission and computation

| Method | Admitted out of 72 | Mean admitted score | Mean planner seconds |
|---|---:|---:|---:|
| Distance A* | 66 | 1.428039 | 0.0320 |
| Terrain A* | 66 | 1.421142 | 0.1240 |
| Energy A* | 66 | 1.366258 | 0.0546 |
| Weighted A* | 66 | 1.357381 | 0.4479 |
| Greedy | 66 | 1.300004 | 0.1802 |
| PSO | 66 | 1.295394 | 0.2529 |
| ACO | 66 | 1.295351 | 0.3668 |
| Old grid proposal | 66 | 1.367730 | 1.5794 |
| Proposal v3 | 66 | 1.294836 | 0.1976 |
| PSO + polishing | 66 | 1.275859 | 0.3013 |
| ACO + polishing | 66 | 1.275318 | 0.4041 |
| Proposed v4 | 69 | 1.271323 | 0.4500 |

The balanced-score improvement over polished ACO is small and its descriptive relative-improvement interval crosses zero. This does not establish a decisive advantage over that stronger control. V4 also takes longer on average than several simpler methods. Conditional mean scores can cover different admitted worlds; the paired table is the direct comparison. Repeated seeds are clustered by world, not 72 independent maps. Relative score differences are not electrical-energy savings. Wall times include each method search but exclude common graph and return preparation. More complex methods may use more of the same time allowance.

## Feature removal tests

Eight preselected held-out worlds, three paired repetitions, 72 attempts. These tests measure the contribution of landmarks and polishing; settings were not revised from these results.

| V4 compared with | Wins | Ties | Losses | V4 only admitted | Both rejected |
|---|---:|---:|---:|---:|---:|
| proposed_v4_no_polish | 18 | 3 | 0 | 0 | 3 |
| proposed_v4_no_landmarks | 3 | 12 | 6 | 0 | 3 |

The polishing ablation favors the full method, but landmark removal has mixed outcomes and an interval spanning zero on this eight-world subset. These data do not establish that every added component consistently helps.

## Shorter budget sensitivity

Four preselected held-out worlds per budget; 12 methods and one repetition. These small subsets are descriptive, not a replacement for the main test.

| Budget s | Baseline | V4 wins | Ties | V4 losses | Only V4 admitted | Only baseline admitted | Both rejected |
|---|---|---:|---:|---:|---:|---:|---:|
| 0.5 | Distance A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Terrain A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Energy A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Weighted A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Greedy | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | PSO | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | ACO | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Old grid proposal | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | Proposal v3 | 4 | 0 | 0 | 0 | 0 | 0 |
| 0.5 | PSO + polishing | 1 | 1 | 2 | 0 | 0 | 0 |
| 0.5 | ACO + polishing | 0 | 2 | 2 | 0 | 0 | 0 |
| 1.0 | Distance A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Terrain A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Energy A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Weighted A* | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Greedy | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | PSO | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | ACO | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Old grid proposal | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | Proposal v3 | 4 | 0 | 0 | 0 | 0 | 0 |
| 1.0 | PSO + polishing | 0 | 2 | 2 | 0 | 0 | 0 |
| 1.0 | ACO + polishing | 0 | 2 | 2 | 0 | 0 | 0 |

## Separate assisted physics

| Method | Scheduled | Executed | Succeeded | Mean destination s, successful only | Mean mission mechanical work J, successful only |
|---|---:|---:|---:|---:|---:|
| Distance A* | 6 | 5 | 5 | 28.924800000001966 | 7854.813576026126 |
| Terrain A* | 6 | 5 | 5 | 28.95360000000189 | 7864.260799580705 |
| Energy A* | 6 | 5 | 5 | 28.684800000001577 | 7618.73293182507 |
| Weighted A* | 6 | 5 | 5 | 28.30080000000179 | 7663.111767450448 |
| Greedy | 6 | 5 | 5 | 27.52640000000151 | 7486.658645999935 |
| PSO | 6 | 5 | 5 | 27.267200000001473 | 7428.583191888535 |
| ACO | 6 | 5 | 5 | 27.267200000001473 | 7432.117777796544 |
| Old grid proposal | 6 | 5 | 5 | 28.710400000001584 | 7635.251385584957 |
| Proposal v3 | 6 | 5 | 5 | 27.267200000001473 | 7432.117777796544 |
| PSO + polishing | 6 | 5 | 5 | 26.924800000001476 | 7390.151703259433 |
| ACO + polishing | 6 | 5 | 5 | 26.924800000001476 | 7393.09357508571 |
| Proposed v4 | 6 | 5 | 5 | 26.93120000000148 | 7388.771326912756 |

Physical means include successful missions only. Scheduled, executed and successful counts must be read together. Mechanical work excludes unmodeled body assistance and is not electrical battery energy. The controller still assists body velocity/posture and gravity compensation. Rejected plans and execution failures remain in scheduled denominators.

## Audit

```json
{
  "version": 4,
  "state": "passed",
  "attempts": 1232,
  "phase_counts": {
    "v4_development_default": 64,
    "v4_development_alternative": 64,
    "v4_heldout_planning": 864,
    "v4_heldout_ablations": 72,
    "v4_budget_0p5": 48,
    "v4_budget_1p0": 48,
    "v4_heldout_physics": 72
  },
  "development_worlds": 8,
  "heldout_worlds": 24,
  "unique_routes_collision_checked": 189,
  "recomputed_continuous_metrics": 756,
  "errors": [],
  "warnings": [],
  "scope": "Internal provenance, geometry, score, budget and protocol audit. Not hardware validation, an optimality certificate or proof of universal superiority."
}
```

## Reproduce

From mujoco: python3 -m research.advanced_study

To recreate figures from the delivered source folder: python make_results.py --project-root /path/to/hexapod_asset. This reads saved records and needs numpy and matplotlib; it does not rerun the experiment.

Source records: mujoco/outputs/research/advanced_study_v4. Every_Experiment.csv shows all 72 paired world/repetition verdicts. Paired_Comparison.csv retains complete counts and descriptive world intervals.

## Publication scope

Version 3 Word documents describe the earlier frozen study. These version 4 results are a separate update and must be incorporated and reviewed before manuscript submission. The proposed representation and polishing use established motion-planning ideas; no universal novelty or dominance theorem is claimed. Electrical calibration and physical robot validation remain outstanding.

Method references: [OMPL path simplification](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1PathSimplifier.html) and [OMPL anytime path shortening](https://ompl.kavrakilab.org/classompl_1_1geometric_1_1AnytimePathShortening.html). These references provide background; V4 is a project-specific implementation, not an exact reproduction.
