# Methods, interpretation and scientific writing audit

Reviewed 7 November 2026. Target: `paper/Pathfinder-Robot-CLRP-IJ3C-V2.odt`. Paragraph identifiers below refer to `paper/review_2026-11-07/qa/manuscript_paragraphs.txt`; equations refer to the embedded MathML extracted into `equations.xml`. The ODT was not edited.

## Evidence provenance

The main planning campaign is run `20261104T014755850676Z`, archived in `publication_2026_11_04/raw_study/primary.json`. Its frozen source snapshot is `workbench/mujoco/outputs/research/source_snapshots/20261104T014755850676Z/`. I checked SHA-256 hashes of the 14 relevant planning, physics, terrain, telemetry and model files against the hashes in that run; all match. The corresponding files in `workbench/mujoco/` also match. The detailed check is saved as `paper/review_2026-11-07/qa/methods_source_check.txt`. For readable file references below, `W/` means `workbench/mujoco/`; the same line numbers apply to its matching frozen source snapshot. `T/` means `publication_2026_11_04_ten_page/`, whose derived analysis and corrected gravity diagnostic are used by the later manuscript iterations. Numerical raw-data recomputation was delegated separately; this audit concerns implementation and interpretation.

## Required corrections

### M1 — Critical: relative-effect sign is reversed in the prose

**Where:** §5.3, P102. The paragraph says, “If the difference is positive, then CLRP is the worse. If the difference is negative, then the comparative method is the worse.”

**Evidence:** Embedded equation (5) is `δ = 100 (Qc − Qv) / Qc`, where the same paragraph defines `Qc` as control and `Qv` as CLRP. Scores are minimized (`W/research/swarm.py:25–27`). Accordingly, a positive value means CLRP has the lower score. The actual analysis counts a positive `Qc−Qv` as a CLRP win and calculates the same relative effect (`T/source/analyze_study.py:83–89`). Figure 2 and Table 3 use this correct orientation.

**Correction:** “For each jointly accepted repetition, δ = 100(Qc − Qv)/Qc, where Qc and Qv denote the control and CLRP scores. Positive values favor CLRP; negative values favor the control. A tie is an absolute score difference of at most 10⁻⁸.” This fixes prose, not the equation or numerical results.

### M2 — Critical: the incumbent-ranking description is corrupted and partly false

**Where:** §3.3, P043, especially “4. Total normalised violation rank”, “5. Total violations” and “of the sanctioned pathways, the inferior Q pathway is favoured.”

**Evidence:** The implementation returns a three-element lexicographic key: `(any_violation, sum_of_normalized_positive_excesses, Q)`. Excess is counted only when its raw value is greater than `10⁻⁸`. The thresholds are deadline, available battery and exposure budget. It does **not** rank by the count of violated constraints, and it does **not** favor a higher/inferior Q. See `W/research/swarm.py:29–35`. The incumbent changes only on a strictly smaller rank key (`W/research/advanced.py:37–39`).

**Replacement:** “Candidates are ranked lexicographically. Routes satisfying all three resource constraints rank ahead of routes violating any constraint. Raw excesses of at most 10⁻⁸ are treated as zero; larger positive excesses are divided by their corresponding constraint thresholds and summed. Among rejected routes, the lower total normalized violation ranks first, with lower Q breaking ties. Among accepted routes, lower Q ranks first. A rejected route cannot replace an accepted incumbent.”

### M3 — High: Map 24 metric attribution contradicts itself

**Where:** §6.4, P212: “For PSO-C, the expected time, normal battery cost and exposure are 32.959 seconds, 15.446 percentage points and 1.012 for CLRP, respectively.”

**Evidence:** These three numbers are the CLRP metrics in every repetition, alongside CLRP distance `20.802835… m` and Q `1.309807…`. See `T/results/all_640_attempts.csv:482`, `:495` and `:496`. A PSO-C example at `:487` has time `42.562741… s`, nominal battery `20.052892… pp`, and exposure `1.669186…`.

**Correction:** Replace the sentence with “For CLRP, predicted time, nominal battery consumption and terrain exposure are 32.959 s, 15.446 percentage points and 1.012, respectively.” Add PSO-C values only if explicitly labeled as individual-repetition or across-repetition averages. The independent numerical audit can supply the latter.

### M4 — High: seed ranges contain missing digits

**Where:** §5.1/P092 says main-test seeds “2140 to 2140031”; §5.4/P108 says diagnostic seeds “1670–1670003”.

**Evidence:** The prospective study samples primary cases beginning at `2140000` (`W/research/publication_study.py:32–34`); cases increment seeds by one (`W/research/worlds.py:115–118`). The diagnostic input starts with seed `1670000` (`T/results/realism_probe_input_v6.json:23`).

**Correction:** `2140000–2140031` and `1670000–1670003`, respectively. Development range `2130000–2130007` is correct.

### M5 — High: several sentences confuse acceptance with permission to attempt

**Where:** P138: “PSO-C only permits one try. CLRP only permits zero tries, both reject two.” P244: “PSO-C permits one more trial”; P248: “PSO-C allows one additional attempt.”

**Evidence:** Every method has the same 96 scheduled primary attempts. These sentences concern outcome categories, not the number of attempts allowed. The derived paired table records 93 joint admissions, one control-only admission, zero CLRP-only admissions and two joint rejections for the PSO-C comparison (`T/results/paired_comparisons.csv:4`). The analysis explicitly creates those categories (`T/source/analyze_study.py:83–87`).

**Correction:** P138: “Both methods accept 93 paired attempts. PSO-C alone accepts one additional attempt, CLRP alone accepts none, and both reject two.” Elsewhere: “PSO-C accepts one additional scheduled attempt.” Preserve 96 as the denominator for each method.

### M6 — High: Discussion identifies a comparison that was not performed

**Where:** §7/P244: “The PSO-P versus ACO-P comparisons show positive mean relative improvements …”

**Evidence:** Table 3 and the analysis compare CLRP separately to PSO-P and to ACO-P. They do not give a PSO-P versus ACO-P effect (`T/source/analyze_study.py:78–90`; `T/results/paired_comparisons.csv:2–3`).

**Correction:** “The CLRP comparisons with PSO-P and ACO-P have positive mean relative effects and zero medians.” Do not infer a PSO-P/ACO-P ordering from these two separately normalized effects.

### M7 — Moderate: “static gait controller” misdescribes the implemented controller

**Where:** Related Literature/P016.

**Evidence:** The same gait configuration is held fixed across route methods, but the controller itself is dynamic: it advances gait phase, alternates stance and swing, predicts future body pose, and generates a smooth swing trajectory (`W/tripod_gait.py:33–75`). `HybridLocomotion.tick` invokes those targets in walking mode (`W/hybrid_locomotion.py:126–128`). “Static gait” can instead imply a specific quasi-static locomotion class, which is not established by this experiment.

**Correction:** “The current study holds the gait controller fixed, supplies terrain information directly, and evaluates removal of body-route planning stages.”

### M8 — Moderate: initial heading has been replaced with “title”

**Where:** §3.3/P036: “The title is in radians (π/2).” Also P049 uses “different titles”.

**Evidence:** The evaluator starts with `yaw=π/2` (`W/research/planning.py:124`, `:211`); execution initializes the same yaw (`W/research/execution.py:32–34`). Graph states include incoming headings, not titles (`W/research/planning.py:173–198`; `W/research/advanced.py:83–97`).

**Correction:** “The initial heading is π/2 radians for every trial.” Replace “titles” with “incoming headings” in P049. This is essential terminology for interpreting turn costs.

### M9 — Moderate: terrain grades are presented as physical inclines, and patches as squares

**Where:** P031 “pedestrian speed limits”; P034 “terrain inclines of 0, 1 and 2”; P036 “flat, gentle and steep terrain”; P093 “squares of shallow terrain”.

**Evidence:** The terrain grade is a categorical semantic value; `f` is mapped from grade 0/1/2 to 0/0.25/0.60 (`W/research/planning.py:59–72`). It is distinct from `s`, the estimated slope derived from sampled heights. Map patches are rectangles with independently drawn half-extents, contain shallow raised tiles, and the MuJoCo physical geometries are horizontal boxes (`W/research/worlds.py:33–41`, `:106–108`). Walking speed is capped by grade at 0.75/0.65/0.38 m/s (`W/research/worlds.py:62–64`). No physical 0°, 1° and 2° incline protocol is present.

**Correction:** Use “configured walking-speed limits”, “terrain grades 0, 1 and 2”, “grade-0, grade-1 and grade-2 regions”, and “rectangular patches with shallow terrain tiles”. The equation's slope term can still be described as a geometric slope proxy; do not conflate it with semantic grade.

### M10 — Moderate: “preserves velocities” at assistance zero is too strong

**Where:** §3.1/P026: “The support operation at scale 0 preserves these body velocities.”

**Evidence:** At assistance zero, the blend performs no direct change; physics integration can still change velocity through gravity, contacts and actuation (`W/research/execution.py:89–95`). The current wording can be read as clamping the velocity throughout execution.

**Correction:** “At scale 0, these direct velocity corrections are disabled.” For scale 0.5, retain that the horizontal/yaw blend occurs four times per controller frame; it is not a physical 50% support-force condition. A clearer condition label is “0.5 velocity blend + GC”.

### M11 — Moderate: completion time is described as eight seconds of service

**Where:** §5.4/P109: “Mission completion times are simulated station operations of eight seconds.”

**Evidence:** Successful elapsed mission time is all simulated motion time **plus** 8 s of modeled station service (`W/research/execution.py:113–123`). Outbound predicted time T is a different quantity. The later Results/P240 describes this correctly.

**Correction:** “Reported completion times include motion to the destination and back to the station, plus 8 s of modeled station service.”

### M12 — Moderate: “moves … on its own” claims a propulsion mechanism not measured

**Where:** §6.5/P241: “The model can move a short distance on its own …”

**Evidence:** The diagnostic logs small horizontal displacement under zero direct body assistance. It does not identify whether that displacement comes from productive gait propulsion, settling, falling, contact transients or a mixture. With GC present it also retains ideal leg-body gravity compensation. The execution simply accumulates planar position displacement (`W/research/execution.py:100`), and “timeout” is failure to complete a saved mission, not a gait/fall classification (`T/source/extended_content.py:54–56`).

**Correction:** “Small planar displacements occur under zero direct assistance, but no mission is completed within 180 s in either gravity-compensation condition.” Keep the existing statement that there is no evidence of foot-ground propulsion in the assisted runs.

### M13 — Moderate: repetitions are described as diversity in maps

**Where:** §7/P245: “The three repetitions are a measure of diversity in maps by algorithm …”

**Evidence:** Geometry and resource constraints are unchanged within each map. The run changes only the trial seed, using `case_seed + repeat × 100003`, and pairs that seed across methods (`W/research/run.py:207–213`). The manuscript P100 already explains this correctly.

**Correction:** “The three repetitions characterize algorithmic variation within each map; the number of independent generated primary maps remains 32.” Do not imply every method is substantively stochastic: CLRP's core graph/local stages are deterministic except for timing-dependent stopping and any inherited stochastic operations.

### M14 — Minor but exact: contact criterion is ≤0.002 m, not <0.002 m

**Where:** §5.4/P111.

**Evidence:** Telemetry skips only contacts whose distance is **greater** than 0.002 m, so equality is accepted (`W/research/telemetry.py:31–37`).

**Correction:** “A foot is counted as contacting external geometry when an available contact record has distance at most 0.002 m.” This is a geometry/contact-distance detector, not a force or load-bearing-foot measurement.

### M15 — Verify with numerical audit: 0.715 s is labeled as an average

**Where:** §6.2/P168: “The time to prepare shared maps is on average 0.715 seconds …”

**Evidence:** The text generator that produced the 0.715 s value explicitly uses `np.median(preparation)` (`T/source/extended_content.py:27`, `:51`). The numerical audit should check the actual mean separately.

**Correction if retaining 0.715:** “Median shared preparation time is 0.715 s (maximum 0.895 s).”

## Findings that are supported by the implementation

These are useful parts of the manuscript and should be preserved while repairing the wording.

1. **Model mass and actuator count:** Source mass 97.52 kg, source base 35 kg, compiled robot subtree approximately 113.32 kg, compiled base 46 kg and 23 actuators are consistent with the saved model audit (`T/results/model_audit.json:5–14`). The source effort/velocity declarations are 60 Nm and 20 rad/s (`workbench/hexapod.urdf:54`, repeated for the leg joints); the manuscript correctly treats them as declarations rather than measured motor characteristics. The difference in source and compiled mass models is real and should remain explicit.

2. **Gravity and assistance mechanisms:** 0.004 s physics steps, four substeps per 0.016 s control frame, gravity −9.81 m/s² and 18 compensated limb bodies match the code/model (`W/hybrid_hexapod_multi_place.xml:3`; `W/hybrid_locomotion.py:32–35`; `W/research/execution.py:15`, `:89–95`). Direct body-velocity blending and body gravity compensation are different mechanisms. At assistance 0.5 the horizontal/yaw blending happens at every substep, so this condition is still strong active correction and should not be treated as a halfway physical support-force experiment.

3. **Terrain formula:** Equations (1)–(2), nine height samples, population standard deviation, gradient-based slope, clipping range and route exposure integration agree with `W/research/planning.py:61–72`, `:139–146`. The measured `s` is a slope of the footprint-averaged height field, rather than a directly measured local contact-surface slope. Calling R an exposure proxy rather than slip probability is correct. To avoid variable ambiguity, consider using `g_terrain` for the intermediate difficulty and a different symbol for gravity.

4. **Resource acceptance:** Equations (3)–(4) match the fixed quality weights and battery policy (`W/research/swarm.py:16`, `:25–35`; `W/research/planning.py:204–209`). Time, battery and exposure are hard constraints; a lower Q cannot compensate for a violation. The nominal battery coefficients are fixed modeling choices (`W/energy_model.py:8–15`, `:22–25`), and E depends on distance/time/turning. The manuscript correctly says these are not independent physical outcomes or electrical measurements.

5. **Footprint and known-map scope:** Radius 1.82 m, margin 0.12 m and continuous clearance tolerance 0.005 m match `W/safe_navigation.py:19–22`, `:76–101`. The grid additionally inflates occupancy by half a cell diagonal (`:60–63`), so the initial grid is more conservative than the final continuous query. That is compatible with the current description, but include it if claiming an exact reproduction specification. No explicit 3D foothold plan or sensing experiment is performed.

6. **Budget accounting:** The 2 s nominal time limit, 240 counted eligible whole-route evaluations and 40,000 expansion limit describe the implementation. The incumbent is retained, direct candidates and final polishing are charged, and rejected/cached proposals differ from new whole-route evaluations (`W/research/advanced.py:18–39`, `:127–147`; `W/research/swarm.py:71–79`, `:280–287`). Graph edge metric computations and geometric queries can occur without incrementing the counted complete-route evaluations (`W/research/advanced.py:73–78`; `W/research/swarm.py:216–219`). A 240-candidate ceiling therefore does not imply equal computation. The manuscript already makes this limitation and the recorded wall-time asymmetry clear.

7. **Preparation and timer scope:** Scene/model construction, graph construction, return route selection and destination lower-bound preparation happen once before method calls (`W/research/run.py:195–206`). The per-method timer starts after `graph.bounds` (`W/research/planning.py:211–215`). P089's “computation of standard search trajectories” should be “precomputation of shared lower bounds”; the initialization routes themselves are inside method budgets. Recorded search time is not full task latency.

8. **PSO-C definition:** Fixed endpoints, subdivision to at least six internal vertices, 2 m Gaussian perturbations, 2 m per-coordinate velocity clipping, map bounds, retained seed and common polishing match `W/research/continuous_pso.py:16–56`. The number of vertices is fixed during swarm search; polishing may delete vertices, as the manuscript correctly limits its fixed-count statement to the swarm phase. This is a specific coordinate-PSO implementation, not an exhaustive benchmark of continuous planning or of all PSO algorithms.

9. **Stage-removal scope:** `noL` skips landmark diversification; `noP` skips final polishing while retaining the initial refiner (`W/research/advanced.py:130–147`). Both inherit the selected CLRP profile (`W/research/publication_study.py:91–94`). The paper correctly notes that independent ablation runs can have different timing/search histories and that equal nominal caps are not a fully budget-matched causal comparison. The local incumbent-ranking property is monotonic within a run; it does not by itself prove a universal across-run quality guarantee for an ablation.

10. **Sampling and statistics:** Eight development maps, 32 primary maps, two profiles for four base methods, six test configurations and three paired repeats are consistent with the frozen design (`W/research/publication_study.py:32–48`, `:90–102`). Map-level averaging of jointly accepted repeats and 5,000 map-level percentile-bootstrap samples with seed 41104 match the analysis (`T/source/analyze_study.py:78–94`). The zero median, acceptance-conditioned estimand, unadjusted comparisons and lack of external preregistration are legitimate limitations already acknowledged. A bootstrap interval covering zero does not prove equality; the manuscript's caution on this point is correct.

11. **Corrected gravity diagnostic:** The first requested GC-off runs were invalid because the locomotion constructor restores all 18 compensated bodies. The correction wrapper disables compensation after that constructor and records before/after counts (`T/source/corrected_gravity_probe.py:14–25`, `:26–33`). The final comparison retains 12 original GC-on records and adds four corrected GC-off records (`T/source/extended_content.py:28–40`), yielding 16 valid comparison executions. The 16 are descriptive replays on four already observed tasks, not independent new held-out locomotion trials. The manuscript now handles that distinction correctly.

12. **Mechanical work and foot-contact interpretation:** Positive actuator work sums positive actuator force × velocity at each physics sample (`W/research/telemetry.py:21–27`). It excludes the direct body-velocity corrections. Foot counts use the six specified feet against nonrobot geometries, not all possible robot contacts (`:31–37`). Zero assisted foot contacts and low controlled tilt do not establish a load-bearing walking gait. The main scientific interpretation of the diagnostic is appropriately narrow.

## Scope and interpretation to keep

The manuscript can support conclusions about the **specified body-route configurations under a common geometric/resource evaluator**, including their observed acceptance, conditional score differences and recorded computational effort. It can also support a descriptive dependence on direct chassis assistance for the four replayed missions. It cannot establish hardware walking capability, electrical energy savings, robust physical battery reserves, a general failure rate, or superiority of an algorithm family. Those are limitations of the experimental evidence, not reasons to discard the internally documented planning results.

The comparison to PSO-C should continue to say that mean-score superiority is **not demonstrated** by this campaign. The positive mean is concentrated in one retrospectively selected map, the paired median is zero, the descriptive 95% interval covers zero, and PSO-C accepts one more scheduled attempt. The current restraint in the Abstract, Discussion and Conclusions is useful once the sign and acceptance terminology are corrected.

## Further wording corrections that protect meaning

These phrases are scientifically confusing even where the intended claim can be recovered:

- P004: “comprehensive planner” → “full planner”; “partial support” → “0.5 velocity blending”; “six foot contact assessment” → “six-foot contact detector”.
- P007: the last sentence is a fragment; use “The evaluator includes these costs and checks each task constraint independently.”
- P009: replace the opening with “We report acceptance, score differences conditional on joint acceptance, and search computation.”
- P012: “demographic updates” → “population updates”.
- P034: “The figure is from the topographical map” → “The difficulty field is derived from the terrain model”.
- P036/P041: consistently use “nominal battery consumption”, rather than “normal battery usage”.
- P041: “The route score cannot be substituted for the others” is not interpretable; use “A difference in Q is not a measured electrical-energy saving.”
- P042: “external route” and “your trip” → “outbound route” and “the mission”.
- P048: “temporal divisions”, “remarkable cap” and “dimensions of local movements” → “time allocations”, “landmark cap” and “local step sizes”.
- P065: “re-calibrated” → “retuned”; the procedure selects search parameters, not physically calibrated measurements.
- P088: “The collective threshold is supported by route assessments…” → “Initialization route evaluations count toward the shared cap.”
- P097: replace the broken end with “Exact ties retain the default profile. The default is selected for all four base methods; both CLRP variants inherit its choice.”
- P100/P102/P165: “mutually agreed”, “jointly recognised”, “mutually confirmed” → “jointly accepted”; “identified” is insufficient because it could include a resource-rejected route.
- P104: “Reported mean and median are the average map values” → “We compute the mean and median of the map-level mean relative effects.”
- P106: “The desktop can do things simultaneously” → “Runs occurred on a shared desktop with concurrent workloads.”
- P108: “Tentative nominal battery percentages” → “Initial nominal battery allowances”.
- P167: remove the opening quotation mark; “Every denial of resources” → “All resource rejections”.
- P205: “Conventional constraints do not suggest uniform search exertion” → “Shared nominal caps do not imply equal computational effort.”
- P210: “equal number of pairs with lower and higher scores” means **attempt-level** jointly accepted pairs (33 each), whereas the neighboring discussion concerns map effects. State the unit explicitly.
- P218: “None of the zero-assistance conditions meets any requirement” → “Neither zero-assistance condition completes a mission within 180 s.” Failure to complete a mission does not mean every individual requirement was failed.
- P244: “subordination” → “inferiority”.
- P245: “The operation of the actuator does not involve body-assisted work” → “The reported actuator-work calculation excludes work associated with direct body-velocity corrections.”
- P246: “a range of source and combined mass” → “distinct source and compiled mass models”.
- P249: “independent diagnosis” → “separate diagnostic”; “approval of unassisted movement” → “validation of unassisted locomotion”.

Terminology should be stable throughout: **route**, **planner**, **candidate**, **accepted/rejected route**, **heading**, **terrain grade**, **nominal battery consumption**, and **conditional map-level relative effect**. Synonyms such as applicant, sanctioned pathway, title, pedestrian, endeavor and permission distort the mathematical meaning.
