# Final V6 study and downloads

V6 means the upgraded experiment and tracking pipeline. The focal route optimizer remains V4. The adaptive V5 candidate is preserved as a negative enhancement result.

1. Open http://127.0.0.1:8771/ and select **Load completed final comparison** after the study finishes.
2. Open **Side by side comparison**. The primary view contains 576 planning records: 48 fresh worlds, two repetitions and six methods.
3. Choose **PSO + polishing**, **ACO + polishing**, or an OMPL control as the baseline. Keep all scenarios for complete-set charts. Select a specific world to inspect its saved routes.
4. Read **admission** before **score**. Admission means a plan meets predicted deadline, battery-return and terrain limits. It does not mean the robot completed a physics mission. Lower scores are better only among admitted routes under the same weight profile.
5. To inspect tracking, choose the saved **v6_physics_safe** phase in the console and select **Use selected run in charts**. The legacy and reduced-assistance controls replay the exact saved proposal routes; they do not run a new planner.
6. Weight and budget phases are separate. Absolute route scores from different weight profiles have different definitions. Repeated seeds and reused subsets are not additional independent maps.
7. Use the final DOCX, PDF, ZIP or CSV download links once packaging finishes. The ZIP also includes **Comparison_Offline.html**, which opens without this local server.

**Missing values:** no returned route means no route score or prediction. Planning-only records have no execution time. Rejected plans are not executed. None of these missing values means zero cost.

**Planner budget:** seconds allowed for the computer to search each route, not a charging interval. Use 2 for the primary setting, or 0.5 and 1 for shorter-budget checks.

The final campaign has 1,200 scheduled records across 12 phases. Half the fresh primary worlds have predeclared obstacle, terrain and friction changes. This is assisted simulation with a nominal battery ledger. Hardware voltage/current measurements and unassisted locomotion remain unvalidated.

---

Hexapod Research Lab — version 3

WHAT CHANGED
The planner can resume unfinished energy A* work and try a distance seed if needed. PSO, ACO, greedy and the proposal receive the same adaptive initialization rule. The proposal searches safe shortcut corridors with bounded resource-aware Pareto labels. It is a heuristic and has no full-map optimality guarantee.

The simulator now creates independent worlds in four families: open, cluttered, rough and corridor. Obstacles, terrain patches, shallow physical tiles and friction vary. The planner and MuJoCo use the same world specification. Recorded preparation time is separate from each method's planner budget.

HOW TO START
1. Open http://127.0.0.1:8771/ on this computer.
2. Choose New worlds — 4 independent terrains.
3. Leave world seed 1050000. This recreates the same four worlds for a fair comparison.
4. Choose the six-method comparison, 1 repetition, planner budget 2 seconds and walking only.
5. Choose Planning only for a quick first test. Click Run comparison.
6. Wait until it finishes. Click Open side by side comparison. Refresh the comparison page if it was already open.
7. Select one scenario and one repetition. Choose the baseline beside the route maps.
8. Next, repeat with MuJoCo physics. Planning admission means the forecast passed its limits; mission success means the simulated robot completed the destination and return within the guards.
9. For a new experiment, change the world seed, for example 1060000. Three repetitions change optimizer random seeds, not the number of independent worlds.

FROZEN STRONGER STUDY
Use Load or finish the frozen study to inspect/resume the saved campaign. It does not silently generate new independent evidence on each click.
- 8 development worlds, two settings per method and two paired repeats: 96 attempts.
- 24 new test worlds, six methods and three paired repeats: 432 attempts.
- First eight test worlds, four proposed variants and three repeats: 96 ablation attempts.
- Two previously inspected timeout cases, four methods and three repeats: 24 development diagnostic attempts.
- First six test worlds, six methods and one repeat: 36 physics attempts. Only admitted routes execute.
- Total: 684 scheduled attempts. Rejections and ties remain in the data.
- Separate software correctness check: exhaustive enumeration on 24 tiny synthetic graphs. These are not additional robot experiments.

WHAT TO LOOK AT
Compare admission first, then route quality on matching admitted cases. A lower common score is preferable under the declared weights. Those weights are a research assumption; do not present the score as a universal best route. Check the win/tie/loss table and its world-level descriptive bootstrap intervals. Positive admission advantage favors the proposal. An interval containing zero does not establish a clear advantage.

Identical routes can produce identical measurements in deterministic simulation. Duplicate trial identifiers would be a data error; equal metric values alone are not. The integrity audit checks complete trial keys, source hashes, frozen parameters, world separation and recomputed scores. Missing route metrics stay unavailable rather than being replaced with zero.

Feature-removal runs test adaptive seed time, seed variety and resource pruning separately. A tie means that the component did not change the output in that tested case. The proposal must also be compared with the simpler greedy method. More complexity is useful only if measured benefits justify its time and implementation cost.

BATTERY CALIBRATION — REAL MEASUREMENTS STILL NEEDED
The software now fits a walking energy model from external electrical measurements and validates it on separate missions AND maps. Simulation battery readings cannot serve as hardware calibration truth.
Template: mujoco/outputs/research/calibration_template/electrical_measurements.csv and metadata.json.
Supply usable battery capacity in Wh and sensor details. CSV columns: mission_id,map_id,split,distance_m,seconds,turn_radians,electrical_energy_wh.
Use at least 12 calibration rows and 6 validation rows, with at least three different missions in each split. Calibration and validation mission IDs and map IDs must not overlap. Vary distance, speed and turning to identify separate coefficients. These are software minimums, not a sufficient research sample-size claim.
From mujoco:
python3 -m research.calibration --csv YOUR.csv --metadata YOUR_metadata.json --out fitted_energy_profile.json
python3 -m research.run --suite procedural4 --methods pso aco proposed --execute --energy-profile fitted_energy_profile.json

Current execution uses assisted body velocity/posture and gravity compensation. Measured actuator work is mechanical energy, not electrical battery energy. Terrain exposure is a difficulty proxy, not a measured probability of falling. A good simulated result therefore does not establish real-robot stability or battery accuracy.

PUBLICATION NEXT STEPS
Inspect the new results, including losses and ties. Do not change the frozen test settings to obtain wins. If the method changes, create a new version and new independent test worlds. Add a separate sensitivity study for score weights and tighter budgets. Obtain real electrical measurements and, ideally, unassisted dynamics or physical robot trials. Explain the precise novelty against the original papers; these PSO/ACO implementations are inspired hybrids, not exact published reproductions. A Q2/Q3 acceptance probability cannot be estimated from this project alone.

The earlier Word manuscript describes version 1. Its results must be revised to the audited version 3 evidence before submission. No manuscript has been submitted or published by this update.
