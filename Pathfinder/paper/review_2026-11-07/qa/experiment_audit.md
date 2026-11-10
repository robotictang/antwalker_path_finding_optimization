# Independent experiment and numerical audit — 7 November 2026

Manuscript: `paper/Pathfinder-Robot-CLRP-IJ3C-V2.odt`. Paragraph identifiers refer to `paper/review_2026-11-07/qa/manuscript_paragraphs.txt` (latest ODT extraction). All repository paths below are relative to `/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder`.

The main reported numerical findings reproduce. The main corrections are a reversed explanation of the paired-score sign, a median mislabeled as an average, truncated map-seed endpoints, and a garbled attribution of the map-24 metrics. The acceptance gains are concentrated in particular maps and must be described at that level.

## Evidence and independent checks

I read the records through `publication_2026_11_05_revised/raw_study/`; this resolves to the preserved files in `publication_2026_11_04_robot_figure/raw_study/`. I did not use existing summary CSVs or QA pass/fail results as the source of the recomputed statistics. Diagnostic files likewise resolve into `publication_2026_11_04_robot_figure/results/`.

Reproduction artifacts are `paper/review_2026-11-07/qa/recompute_experiment.py`, `recomputed_experiment.json`, and `recompute_experiment.log`. The script uses the bundled Python runtime at `/home/dewayne/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`. No new simulation was run and the manuscript was not modified.

For all 640 stored planning records, independently checked:

- Complete and unique `(case_id, method, repeat)` keys, matching the scheduled Cartesian products: 32 default-development + 32 alternative-development + 576 primary records.
- Distance from the stored waypoint geometry, with maximum discrepancy below `7.2e-15 m` against reported metrics.
- All four route metrics from stored world specifications and route geometry, independently implementing terrain boundaries, terrain speed integration, initial heading, turn time, acceleration allowance, nominal energy, nine-position ground sampling, grid difficulty and route exposure. Maximum discrepancies were `1.43e-14 s` for predicted time, `3.56e-15` nominal battery percentage points for energy, and zero for exposure.
- All 187 distinct world/route combinations for segment clearance against the stored obstacle rectangles, using the `1.82 + 0.12 + 0.005 m` threshold, with no blocked segment found.
- Score `Q = D/50 + T/90 + E/30 + R/80`, required battery `1.25(E + E_return) + 6`, and acceptance against all three resource limits with the declared `1e-8` tolerance. All match; maximum score discrepancy is `4.45e-16`.
- All 29 primary source-snapshot hashes match their recorded values. Snapshot: `workbench/mujoco/outputs/research/source_snapshots/20261104T014755850676Z/`.

This checks the consistency of stored model outputs, geometry and analysis. It cannot establish physical battery calibration, hardware validity, independent map-source generalization, or external preregistration.

Useful implementation locators: `workbench/mujoco/research/worlds.py:45–72` (terrain and speed), `research/planning.py:124–147` (continuous metrics and exposure), `safe_navigation.py:76–101` (clearance), `safe_navigation.py:125–150` (time and energy), `research/swarm.py:25–35` (score and ranking), and `research/planning.py:204–209` (acceptance). Each has a matching recorded snapshot copy.

## Corrections needed

| Priority | ODT location | Finding | Correction supported by data/code |
|---|---|---|---|
| High | P102, §5.3, p6 | The prose says a positive paired difference means CLRP is worse. This reverses the analysis. | Use `100(Q_control − Q_CLRP)/Q_control`; positive values favor CLRP, negative values favor the control. Comparison also requires **joint acceptance**, not merely that both methods identify a route. See `publication_2026_11_04_robot_figure/source/analyze_study.py:81–89`. |
| Medium | P168, §6.2, p7–8 | Shared preparation of `0.715 s` is called an average. | It is the **median**, `0.7152053944955696 s`. The arithmetic mean is `0.7198659537491494 s` (rounds to `0.720 s`); maximum is `0.8948232539987657 s` (`0.895 s`). JSON locator: primary `cases[*].total_preparation_seconds`. |
| Medium | P092, §5.1, p5 | Primary map seeds are written `2140` to `2140031`. | Correct range is **2140000–2140031**. Development range **2130000–2130007** is correct. See primary/development `cases[*].seed` and `workbench/mujoco/research/publication_study.py:33`. |
| Medium | P108, §5.4, p6–7 | Diagnostic seeds are written `1670–1670003`. | Correct range is **1670000–1670003**, for `v6test_01` through `v6test_04`. See `results/realism_probe_input_v6.json`, first four `cases`. |
| Medium | P212, §6.4, p8 | The final sentence says “For PSO-C” then attributes `32.959 s`, `15.446 pp`, `1.012` “for CLRP”. | These three values all belong to **CLRP**. PSO-C means are **42.584 s**, **20.066 nominal battery percentage points**, and **1.665 exposure units**. Suggested replacement below. |
| Medium | P138 / P244 / P248 | Phrases such as “PSO-C only permits one try” or “allows one additional attempt” can imply a different trial budget. | Both methods have 96 scheduled attempts. **PSO-C alone accepts one paired attempt**; total acceptance is 94 vs 93. |
| Medium | P245, §7, p9–10 | “The three repetitions are a measure of diversity in maps by algorithm” misidentifies their role. | They measure algorithmic variation on the **same geometry and task limits**, not map diversity. There are 32 distinct primary maps. |
| Medium | P218, §6.5, p9 | “None of the zero-assistance conditions meets any requirement” overstates the result. | All eight valid zero-assistance missions **fail to complete and time out at 180 s**. That does not imply that every individual safety or resource criterion fails; e.g. recorded obstacle penetration counts remain zero. |
| Low | P110, §5.4 | “The first four executions” is ambiguous about which data were replaced. | Say “The four original executions requested without gravity compensation were invalidated because controller initialization restored compensation; they were replaced by four verified reruns.” The original archived file still has all 16 original records, four of which are superseded, and the correction file adds four reruns. |
| Low | P111, §5.4 | Contact is described with a strict `<0.002 m` criterion. | The code accepts contacts at **distance ≤0.002 m** (`research/telemetry.py:33`: only distances `>0.002` are skipped). This boundary does not change the reproduced aggregate figures. |

Suggested replacement for P212:

> Map 24 belongs to the corridor family, and both methods accept all three repetitions. CLRP returns the same route in each repetition, with a distance of 20.803 m and a score of 1.310. PSO-C has a mean distance of 27.135 m and a mean score of 1.706. CLRP's predicted travel time, nominal battery cost and exposure are 32.959 s, 15.446 percentage points and 1.012; the corresponding PSO-C means are 42.584 s, 20.066 percentage points and 1.665.

## Confirmed study counts and parameter selection

Development contains 8 maps × 4 base methods × 2 profiles = 64 attempts. All 64 have status `found`; each profile accepts all 8 development maps for every method. All four default profiles are selected by the lower accepted mean score:

| Method | Default mean Q | Alternative mean Q | Selected |
|---|---:|---:|---|
| CLRP | 1.3582670263 | 1.3599361545 | Default |
| PSO-P | 1.3590196066 | 1.3615786314 | Default |
| ACO-P | 1.3588066868 | 1.3602506794 | Default |
| PSO-C | 1.3573371726 | 1.3648263436 | Default |

Primary contains 32 maps × 6 methods × 3 repetitions = 576 attempts, 96 per method. The 576 records consist of 556 `found` and 20 `resource_rejected`; no error-status record occurs in the full 640. All 20 rejected primary attempts violate **only the predicted outbound deadline**. Their battery and terrain flags pass. No primary failure is due to failure to find geometric route points.

The 32 primary maps have 8 maps per family, each repeated 3 times. All methods accept every one of the 24 attempts in each non-corridor family. Corridor acceptance is 21/24 for CLRP, PSO-P, ACO-P and noL; 22/24 for PSO-C; 18/24 for noP.

The three additional CLRP acceptances over noP are **repetitions 0, 1 and 2 of one map**, `ij3ctest_12`, corridor seed **2140011**. The single extra PSO-C acceptance over CLRP is **repetition 0 of one map**, `ij3ctest_32`, corridor seed **2140031**. On map 32, CLRP rejects all three repetitions and PSO-C rejects repetitions 1 and 2. This concentration should accompany claims about an acceptance gain; “three maps improved” would be false.

## Confirmed score statistics

For each control, take only jointly accepted repetitions, compute their relative score improvements, average within each map, then give each paired map equal weight. I reproduced all intervals by resetting NumPy `default_rng(41104)` for each comparison, drawing 5000 bootstrap samples of whole-map effects, and taking the 2.5th and 97.5th percentiles. This is the implementation in `publication_2026_11_04_robot_figure/source/analyze_study.py:78–93`.

| Control | Paired maps | Mean improvement % | Median % | Descriptive 95% percentile interval % | CLRP lower / ties / higher in jointly accepted attempts |
|---|---:|---:|---:|---|---|
| PSO-P | 31 | 0.928734455 | 0 | [0.026682672, 2.523187357] | 29 / 50 / 14 |
| ACO-P | 31 | 0.920771454 | 0 | [0.028890264, 2.506644217] | 30 / 51 / 12 |
| PSO-C | 31 | 0.690064997 | 0 | [−0.254695216, 2.312272166] | 33 / 27 / 33 |
| CLRP noL | 31 | 0.924091115 | 0 | [0.035909069, 2.513406718] | 27 / 57 / 9 |
| CLRP noP | 30 | 0.794148368 | 0.502284160 | [0.442892219, 1.208669549] | 57 / 33 / 0 |

All displayed Table 3 values and the listed paired counts reproduce at the manuscript's precision. The PSO-C interval includes zero. It supports the manuscript's caution that a positive mean alone does not establish superiority. The five intervals are unadjusted and conditional on joint acceptance, as disclosed. They do not replace the full acceptance outcomes.

The CLRP vs PSO-C map effects range from **−1.718261324% to 23.202475798%**, matching P207. The largest positive effect is on `ij3ctest_24`, seed **2140023**, corridor. Removing that map changes the 31-map mean **0.690064997%** to **−0.060348696%** over 30 remaining paired maps. This confirms strong concentration in a single case and is a sensitivity result, not justification for removing that map from primary analysis. The noP leave-one-map-out means range from **0.682158027% to 0.821532794%**, matching the rounded `0.682–0.822%`.

Raw-data locators: primary `records` selected by `case_id`, `repeat`, and `method`; score at `plan.quality_score`, acceptance at `plan.admissible`. Full per-map effects are in this review's `recomputed_experiment.json` under `paired[*].map_effects`.

## Confirmed search effort

| Method | Accepted / 96 | Mean s | Median s | Max s | Median route evaluations | At 240 | Median clearance queries |
|---|---:|---:|---:|---:|---:|---:|---:|
| CLRP | 93 | 0.375966 | 0.367693 | 0.775608 | 33 | 0 | 1033 |
| PSO-P | 93 | 0.222602 | 0.199271 | 0.635471 | 46 | 0 | 137 |
| ACO-P | 93 | 0.334651 | 0.296250 | 0.894838 | 32.5 | 0 | 121.5 |
| PSO-C | 94 | 0.731255 | 0.724085 | 1.203068 | 240 | 84 | 2142.5 |
| CLRP noL | 93 | 0.195813 | 0.166197 | 0.586347 | 21 | 0 | 146.5 |
| CLRP noP | 90 | 0.329247 | 0.337662 | 0.634359 | 5 | 0 | 814 |

Tables 2 and 4 reproduce. The maximum recorded search is **1.203067936 s**, so every recorded search is below the nominal 2 s allowance. Equal ceilings do not mean equal actual effort: PSO-C reaches 240 route evaluations in 84/96 attempts while the others reach it zero times. Clearance queries and full route evaluations measure different operations. Raw locators: `records[*].plan.planning_seconds`, `.optimizer.fitness_evaluations`, and `.optimizer.visibility_checks`.

## Confirmed support diagnostic

The valid set is the 12 GC-enabled original records from `results/realism_probe.json` plus the 4 verified GC-disabled reruns from `results/corrected_gravity_probe.json`. Do not pool all 20 stored executions as though they were 20 valid distinct planned conditions. The rerun records explicitly show 18 enabled compensation bodies before correction and zero afterward; all `values_after` are zero. See `source/corrected_gravity_probe.py:17–34`, especially the subclass that disables compensation **after** controller construction.

The four input routes are separate earlier maps, not four of the primary 32: seeds **1670000–1670003**. Their distances reproduce as **21.36, 22.30, 23.45 and 19.78 m**; initial battery allowances are **45, 85, 45 and 100%**.

| Condition | Complete / 4 | Distance range m | Total elapsed range s | Mean contacted feet range | No-contact percentage range |
|---|---:|---|---|---|---|
| Full support + GC | 4 | 34.710987–42.832814 | 62.848–89.632 | 0–0 | 100–100 |
| Half support + GC | 4 | 34.745573–42.910611 | 62.832–89.664 | 0–0 | 100–100 |
| Zero support + GC | 0 | 0.323718–0.326096 | 180–180 | 0.421267–0.421667 | 83.004444–83.046667 |
| Zero support, verified GC off | 0 | 0.375507–0.381349 | 180–180 | 4.008578–4.017044 | 0.024444–0.024444 |

The reported Table 5 and §6.5 ranges reproduce after rounding. Assisted elapsed times include **8 s of modeled station service**, whereas contact telemetry is sampled during physics motion, not during that added downtime. All eight assisted executions have mean foot-contact count zero and no-contact fraction one in the stored telemetry. Assisted maximum tilt is **0.408867190°**, below the stated `0.410°` bound. All eight zero-support runs record 45000 physics samples at 0.004 s = 180 s, outcome `timeout`, no destination completion, and no mission completion.

Measurement implementation locators: `workbench/mujoco/research/telemetry.py:21–37` (work, tilt, contact selection), `:55–66` (aggregates); `research/execution.py:84–95` (direct assistance and sampling), `:111–121` (completion and added service time). The stored aggregate values and implementation are mutually consistent; per-step contact arrays are not retained, so this review did not independently reconstruct contact histories or rerun locomotion.

A careful conclusion is: **the four tested assisted missions complete with no detected six-foot contact, while none of their zero-assistance counterparts completes within 180 s**. This supports dependence on direct body assistance in these tests. It does not establish a broad unassisted failure rate, calibrate nominal battery costs, or demonstrate foot-propelled locomotion.
