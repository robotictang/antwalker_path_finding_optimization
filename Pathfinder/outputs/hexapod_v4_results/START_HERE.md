# Your upgraded hexapod project

The proposed method is now version 4. It checks extra routes around obstacles and moves waypoints to improve the balanced distance, time, modeled battery and terrain score. It keeps a safe route available if its search allowance runs out. This is algorithm parameter tuning; no neural network was trained.

## See the saved results now

1. Open http://127.0.0.1:8771/comparison/ on this computer. Refresh an already open comparison tab.
2. Keep Terrain family, Scenario and Repetition set to All to see the complete planning comparison.
3. Read “Does the new proposal stand out in each experiment”. The chart counts the 72 world/repetition experiments. The table shows each result.
4. Scroll to “Proposed versus each baseline” for wins, ties, losses and rejected attempts.
5. Scroll to “Side by side routes”. Select a scenario, repetition 1, and a baseline such as PSO. You will see its route beside V4.
6. Change the baseline to PSO + polishing or ACO + polishing for a harder comparison.

If local links fail, double-click Hexapod_V4_Comparison.html in this folder. It includes the saved planning data and charts. It does not need the research server. The console link inside it still needs the local server.

## Three examples to explain to your supervisor

- Clear practical benefit: Scenario heldout_24, repetition 1, baseline PSO. V4 predicts 42.62 seconds and meets the 45-second deadline. PSO predicts 92.32 seconds and is rejected. These are planning predictions, not measured execution times.
- Balanced trade-off: heldout_07, repetition 1. V4 score 1.46858834; PSO score 1.48594058; PSO + polishing score 1.47407052. V4 has a shorter route and lower modeled energy, with slightly higher terrain exposure. The combined score chooses that trade-off.
- Honest limitation: heldout_02, repetition 1, baseline PSO + polishing. V4 score 1.07069249; polished PSO score 1.07017690. Smaller is better. V4 loses slightly here. In heldout_01, it ties the polished controls.

The overall main test has 24 fresh worlds and three paired repetitions, with 12 methods: 864 planning attempts. V4 is sole best in 20 experiments, tied best in 35, and beaten in 14; all methods reject the other three. A repeated seed is another algorithm attempt on the same world, not another independently generated map.

## Inspect physics results separately

Open http://127.0.0.1:8771/ . In “Research studies and saved evidence”, click “Inspect held-out physics”. Click “Use selected run in charts”, wait for the build, then refresh the comparison tab. This changes the chart dataset to the physics run. To return, click “Inspect held-out planning” and repeat the same steps.

Planning-only runs deliberately have no measured mission time, work or success. “Unavailable” does not mean a zero or a successful mission. Rejected routes never execute. The saved physics records explain any execution failure.

## Run a small new example later

Use the experiment console. Choose:

- Scenario suite: New worlds · 4 independent terrains.
- World seed: 1600000 (new exploration, separate from the frozen study).
- Methods: V4 vs PSO vs ACO plus polished controls, 5 methods.
- Repetitions: 3.
- Planner budget: 2 seconds.
- Locomotion: walking.
- Execution: Planning only for a quick comparison; Plan and run MuJoCo physics for a longer simulation.

These exploratory runs use the standard console settings. The frozen study uses separately selected settings recorded in locked_parameters.json. This gives 4 × 5 × 3 = 60 scheduled attempts. The planner budget is the allowed computer search time, not a charging interval. After it finishes, choose the new saved run, click “Use selected run in charts”, then refresh the comparison tab. Do not pool these exploratory results into the frozen held-out test or tune on that test.

## What the files mean

- V4_Results_Summary.md: protocol, measured tables, limitations and evidence audit.
- Every_Experiment.csv: all 72 main world/repetition verdicts, including ties and losses.
- Paired_Comparison.csv: all 11 baseline comparisons.
- All_1232_Attempts.csv: every campaign attempt with its phase and execution status. Success is blank on planning-only rows because no mission was executed; use physics_executed and phase to interpret it.
- figures/: comparison charts and the method flow diagram.
- Hexapod_V4_Evidence.zip: preserved raw records, source snapshots, world XML files, settings and audit. Read its reproduction notes before moving model files.

## What is still missing for a strong paper

The balanced score is a weighted preference, not proof that every individual metric improves. V4 uses more planning time than several simpler methods. The small advantage over polished ACO is uncertain: its descriptive percentage-improvement interval includes zero. Feature tests provide stronger support for polishing than for a uniform landmark benefit.

Physics still assists the robot body and uses nominal battery coefficients. Mechanical actuator work is not electrical battery consumption. Physical measurements and stronger independent validation are still needed. The version 3 Word manuscript describes the earlier study; these new version 4 results must be incorporated and reviewed before submission. A publication decision or journal quartile cannot be guaranteed by these runs.

Verification: 30 automated tests passed. Static figures were visually checked. No browser was available for interactive visual testing; local HTTP, data integrity and build checks were performed.

Final campaign audit: passed, 1,232 attempts, no errors or warnings. The audit separately rechecked 189 distinct saved routes for collision clearance and recomputed 756 continuous metric values. Physics: 72 scheduled, 60 executed and successful; all methods rejected the same sixth world. V4 mean destination time 26.9312 seconds; PSO/ACO 27.2672; polished controls 26.9248. V4 mean mechanical work 7,388.77 J; polished PSO 7,390.15 J. These small differences do not establish electrical battery savings.
