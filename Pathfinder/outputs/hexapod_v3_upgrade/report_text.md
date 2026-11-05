Hexapod version 3 improvements and evidence

Supervisor supplement   28 October 2026

The project now has a more robust planner and a stronger comparison protocol. The completed study contains 684 scheduled attempts. The proposal improved the declared route score over simple A* baselines, while PSO and ACO usually found the same score. Real robot and electrical battery validation remain outstanding.

What was improved

An unfinished energy A* search can now resume from its saved work. If necessary, a distance A* search supplies another safe starting route. PSO, ACO, greedy and the proposal share this adaptive initialization rule. The proposal then searches safe shortcuts using bounded Pareto labels, keeping routes that offer useful distance, time, energy and terrain trade-offs.

Figure 1. Implemented planning flow. All stages share the same total planner budget. Seed stages may finish earlier than their limits.

The new worlds vary obstacles, shallow terrain tiles, terrain severity and friction. The planner and MuJoCo read the same world specification. Each saved result records seeds, parameters, source hashes, model hashes, timing and rejection reasons.

What the study contains

Phase | Worlds or cases | Attempts

Parameter development | 8 new worlds and two settings | 96

Held out planning | 24 new worlds and six methods | 432

Feature removal | First 8 held out worlds and four variants | 96

Old timeout diagnosis | 2 previously inspected cases | 24

Assisted physics | First 6 held out worlds and six methods | 36

The 24 small synthetic reference graphs are separate software checks. They are not additional robot experiments. Repeated optimizer seeds are not independent worlds.

What the held out planning results show

Each method received the same 24 test worlds, three paired seeds per world and a 2 second maximum planning budget. Settings were selected on separate development worlds and frozen before testing. A route is admitted only if its deadline, modeled battery plus return reserve, and terrain exposure satisfy their limits.

Method | Admitted out of 72 | Mean admitted score | Mean planner seconds

Distance A* | 63 | 1.320188 | 0.028

Energy A* | 66 | 1.321896 | 0.045

Greedy shortcuts | 66 | 1.259056 | 0.153

PSO hybrid | 66 | 1.252533 | 0.208

ACO hybrid | 66 | 1.252711 | 0.292

Proposed v3 | 66 | 1.252288 | 0.170

Mean scores above can cover different admitted worlds. Use the paired results below for direct comparisons. Lower score is better under the chosen weights. Planning time excludes shared model and graph preparation, which is recorded separately. These wall times are not isolated CPU microbenchmarks.

Figure 2. Every baseline comparison contains 72 paired attempts. Score comparisons require both routes to be admitted. Ties and rejections remain visible.

Against PSO, the proposal had 3 lower scores, 63 ties and no higher scores among 66 jointly admitted trials. Against ACO, it had 9 lower scores, 57 ties and no higher scores. Both comparisons had 6 jointly rejected attempts. Admission was identical at 66 of 72. These results support small modeled-score gains in some cases, not a broad superiority claim.

The mean world score advantage over PSO was 0.000245, with a descriptive 95% world bootstrap interval from 0 to 0.000734. Against ACO it was 0.000423, with interval 0.000000730 to 0.001038. Intervals resample whole worlds after averaging seeds and condition on joint admission; multiple comparisons and the restricted simulated distribution limit interpretation.

Common score = distance / 50 + predicted seconds / 90 + modeled battery percentage points / 30 + 0.25 × terrain exposure / 20. A percentage score change is not a percentage electrical energy saving.

Which features helped

Feature removed | Proposed lower score | Ties | Proposed higher score

Fixed seed time | 0 | 24 | 0

One seed family | 12 | 12 | 0

No resource pruning | 0 | 24 | 0

Using several seed families helped in 12 of the 24 paired trials in this eight-world subset. Fixed seed time and removing resource pruning produced the same scores as the full proposal in all 24 pairs. Those features therefore have no demonstrated output advantage in this subset. A larger or more difficult independent test is needed before claiming their general benefit.

On the two old timeout cases, the fixed-time control returned metrics in 0 of 6 attempts. The adaptive proposal returned metrics in 6 of 6. The resulting routes still failed the resource limits. Recovering a route fixes lost planning effort; it does not create extra battery capacity. These previously inspected cases are diagnostic evidence only.

What the physics trials show

Method | Scheduled | Executed | Successful

Distance A* | 6 | 6 | 6

Energy A* | 6 | 6 | 6

Greedy shortcuts | 6 | 6 | 6

PSO hybrid | 6 | 6 | 6

ACO hybrid | 6 | 6 | 6

Proposed v3 | 6 | 6 | 6

Figure 3. Predicted and executed destination times on trials that reached the destination. Points may overlap when methods use identical routes.

Across 36 destination-reaching executions, mean absolute time prediction error was 1.808 seconds. Mean absolute modeled battery prediction error was 1.908 percentage points. The latter compares two simulation quantities, not an electrical sensor.

How to inspect the changes

1. Open http://127.0.0.1:8771/ on this computer. The updated comparison is at http://127.0.0.1:8771/comparison/.

2. Start with the saved v3 held out planning run. Use a single scenario and repetition before reading aggregate charts. The paired score chart makes small differences and exact ties visible.

3. Choose heldout_22, repetition 1 and ACO for an example with different scores. The proposed composite score is about 0.0763% lower. This is a very small modeled-score difference.

4. For feature-removal or physics results, use the study links in the console, select that run, then click Use selected run in charts. Refresh the comparison tab.

5. To run your own check, choose New worlds with 4 terrains, six methods, 1 repetition, a 2 second budget, walking only and Planning only. Keep seed 1050000 to repeat the same four worlds. Change the seed for new worlds.

6. Follow with physics on the same settings. Read rejection and failure reasons. An unavailable measured value means the trial was not executed or never reached the relevant stage.

What still needs real measurements

The battery model is still nominal. A new fitter accepts externally measured electrical energy, requires separate calibration and validation missions and maps, and reports held-out prediction error. The supplied empty CSV and metadata template explain the inputs. No calibration measurements were invented.

The software minimum is 12 calibration observations and 6 validation observations with at least three distinct missions in each split. Vary speed, distance and turning. These counts are input safeguards, not a justified publication sample size. Choose a larger study using expected variation, the effect size you need to detect and supervisor advice.

The robot still receives assisted body velocity and posture with gravity compensation. Mechanical actuator work is not electrical consumption. Terrain exposure is a difficulty proxy, not a fall probability. New simulations alone cannot establish real robot stability, battery accuracy or universal superiority.

What to do before journal submission

Use this version 3 evidence to revise the earlier version 1 manuscript. Verify the precise novelty against full papers and clearly describe the PSO and ACO implementations as inspired hybrids. Add weight and budget sensitivity tests without retuning on the frozen test worlds. Collect real electrical measurements and physical robot or unassisted dynamics evidence if the paper makes those claims. Retain the simpler greedy baseline and all ties or failures.

The integrity audit passed for 684 scheduled attempts. It checks trial identity, world separation, frozen settings, archived sources, physical model hashes and recomputed metrics. The 24 tiny exact-reference cases also passed. Neither check estimates a journal acceptance percentage.

Evidence folder: mujoco/outputs/research/strong_study_v3. The new report supplements the earlier Word manuscript; it does not make that historical manuscript current automatically. No journal submission has been made.