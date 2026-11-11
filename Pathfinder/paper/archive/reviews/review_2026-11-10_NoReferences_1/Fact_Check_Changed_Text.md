# Fact check of the revised manuscript text

Reviewed 10 November 2026, Asia/Kuala_Lumpur

**This version contains substantial factual errors and reversals of scientific meaning. I would correct it before submission.** The five tables and the mathematical token sequences of all five equations match the previously verified V3 snapshot. The surrounding prose now contradicts several of those results and the saved implementation. This finding concerns the manuscript's descriptions; it does not show that the saved experiment results have changed.

Source: [NoReferences(1).docx](</home/dewayne/Downloads/NoReferences(1).docx>). The original file was not edited. Page numbers below refer to its fresh nine-page render. Paragraph identifiers refer to the retained extraction in this review's QA directory.

## What changed between the files available now

The main-body text, including table text and mathematical text, is **identical** in the two currently available Downloads files, `NoReferences.docx` and `NoReferences(1).docx`. Their document packages differ in formatting, settings, headers/footers and metadata. I therefore cannot attribute the errors below specifically to the latest save. Both current Downloads copies contain them.

The comparison with the earlier scientific review uses its retained V3 XML extraction, not an assumption that a file bearing the same V3 filename has remained unchanged. The current named V3 file has also changed since that review. No document contents were treated as instructions to perform actions.

## Priority factual corrections

| Location | Current statement | Finding and correction |
|---|---|---|
| Section 3.3, p. 3, P024 | “The difficulty of the route and the number of smallmouth bass received.” | This is unrelated to the robot experiment and should be deleted. No such outcome exists in the model or records. |
| Section 3.3, p. 3, P024 | “10 mph acceleration allowance” | Unsupported and dimensionally wrong: mph is a speed unit. The evaluator uses a time allowance for acceleration/start and stop. Restore **“an acceleration allowance”**; the audited walking implementation adds 0.6 s to nonzero routes. |
| Section 3.3, pp. 3–4, P028 | “All constraint raw excesses above 10−8 are considered to be zero.” | **Reversed.** Raw excesses **at most** 10⁻⁸ are treated as zero. Larger positive excesses contribute to normalized violation and mark the candidate as violating a constraint. |
| Section 4.1, p. 4, P031 | Equal route-evaluation limits mean “the numbers of geometric queries will be the same.” | **False.** Equal ceilings do not imply equal work or query counts. Primary median clearance queries are **1,033 for CLRP, 2,142.5 for PSO-C and 146.5 for noL**. |
| Section 4.1, p. 4, P031 | “The common ceiling is increased by route evaluations made during the route initialization.” | **False.** The ceiling remains **240**. Initialization evaluations consume the shared allowance; they do not increase it. |
| Section 5.1, p. 5, P069 | Categories alternate between “4 open, 4 cluttered, 4 rough and 4 corridor.” | These counts are unsupported and contradict the next sentence. The primary set has **eight maps per family**; development has **two per family**. The generator cycles through the four family names one map at a time. |
| Section 5.3, p. 6, P073 | Ties are “any difference” between Qc and Qv at most 10⁻⁸. | The **absolute** difference is required: **abs(Qc − Qv) ≤ 10⁻⁸**. A large negative signed difference is not a tie. |
| Section 6.2, p. 7, P132 | Corridor acceptance: PSO-P **22/24**, ACO-P **24/24**; PSO-C and noL omitted. | **Wrong method attribution and counts.** CLRP, PSO-P, ACO-P and noL each accept **21/24**; PSO-C accepts **22/24**; noP accepts **18/24**. The overall totals in Table 2 remain correct. |
| Section 6.3, pp. 7–8, P171 | “Without it, the mean of the other 30 paired maps is 0.690% and -0.060% without it.” | The **31-map** mean including Map 24 is **0.690%**. The **30-map** mean after omitting it is **−0.060%**. The sentence currently assigns both values to the reduced set. |
| Section 6.3, p. 8, P171 | “primary sample that has not been preserved” | This reverses the recorded protocol. The primary sample **remains unchanged**. Omission analyses are separate sensitivity summaries; all maps remain in the primary analysis. |
| Section 6.5, p. 8, P181 | “16 completed, valid executions” | There are **16 valid executions, of which eight complete**. Full and 0.5-scale assistance each complete 4/4; both zero-assistance conditions complete 0/4 and time out. |
| Section 6.5, p. 9, P203 | “gravity turned on or off confirmed” | **Different experimental condition.** The diagnostic enables or disables **leg-body gravity compensation**. Environmental gravity remains **9.81 m/s²**; it is not switched off. |
| Conclusions, p. 9, P207 | “landmark search improves acceptance by 0.924%” | **False.** Acceptance is **93/96 with and without landmark search**. The **0.924%** is a conditional mean paired-map relative improvement in Q, not an acceptance gain. The abstract's claim that acceptance “decreases to 93” also needs correction. |
| Discussion and Conclusions, p. 9, P205/P207 | “There is one more PSO-C attempt”; “PSO-C has one more chance.” | Both methods have **96 scheduled attempts**. PSO-C **accepts one additional attempt**, giving 94/96 versus CLRP's 93/96. |
| Discussion, p. 9, P205 | “no evidence that the mean score is higher for CLRP” | This changes the intended comparison. **Lower Q is better.** State that the study **does not demonstrate a mean paired-map relative score advantage for CLRP over PSO-C**. The interval includes zero and establishes neither equivalence nor inferiority. |

These corrections can be made without changing the verified tables, equations or raw results.

## Other descriptions that need repair

1. **Clipping is not an input-admission rule.** Section 3.2, p. 3, P022 says clip will “only accept” a first argument in [0, 2]. It can receive g outside that interval and maps it to bounded output d. Use: **“Clipping maps the intermediate value g to the final difficulty d in [0, 2].”** The same paragraph's slope description should be: **“Slope is the arctangent of the gradient magnitude of the footprint-averaged sampled height field on the 0.25 m grid.”** Heights are sampled from the simulator's terrain model, not physically measured.

2. **Local refinement happens during planning.** The introduction's “end-of-trip local path manipulation” places it at the wrong point in the process. Use **“final local route refinement during planning.”** An initial path is an **ordered sequence of planar waypoints**, not an unordered set.

3. **Candidate rank improves when its tuple becomes smaller.** Section 4.1 and Algorithm 1 say rank “increased” or “rank increases.” Replace these with **“improves the ranking rule”** or **“has a lower rank key.”** Accepted routes rank first, then lower total normalized violation, then lower Q.

4. **Landmark sorting has a specific definition.** Algorithm 1, p. 4, P036 sorts candidate points by the **sum of their Euclidean distances to the start and destination**. “Distance from start to destination and vice versa” does not describe that operation. The cap is 44 nodes **including** the two endpoints.

5. **noL and noP mean stages are omitted.** The extra caption embedded in Section 4.3 says “noL = landmark search, noP = final adjustment.” Delete that duplicate and keep the actual caption: **“noL omits landmark search and noP omits final adjustment.”**

6. **A cap and recorded effort are different.** Section 4.3 starts “Both methods” despite six configurations. Use **“Each method.”** A method may finish below both limits. Section 6.2's claim that route-evaluation limits are not equal should say **“The common limits do not imply equal recorded search effort.”** Remove the duplicated sentence “Table 4. Search work is performed more than 96 times”; the table summarizes **96 attempts per method**.

7. **Shared preparation computes lower bounds.** Replace “nominal search directions” in Section 4.3 with **“destination-based lower bounds.”** The shared setup includes the scene, graph, return route and cached goal-based bounds. Method-specific initialization belongs inside its timer.

8. **Parameter selection compares accepted attempts, not accepted profiles.** In Section 5.2, compare the number of accepted attempts for each profile. If tied, select the lower mean Q **among accepted routes**. Exact ties retain the default. There is no cognitive/social “ratio of 1.6”: the alternative PSO-C has **both coefficients set to 1.6**.

9. **Mean and median are different summaries.** Section 5.3 should say: **“Relative effects are averaged over jointly accepted repetitions within each map; the reported mean and median summarize these map-level averages.”** The bootstrap interval is a **statistical interval**, not a “time frame.” An interval that **contains zero** is not an interval that **is zero**.

10. **The acceptance gain is concentrated in one map.** The increase from 90 to 93 accepted attempts is three repetitions of corridor map `ij3ctest_12`, seed **2140011**. Add this qualification in the discussion and conclusion. All **20** rejected primary method-attempt records fail the **outbound deadline only**, with their battery and exposure checks passing. This does not imply those other constraints never influence route selection.

11. **Full and half-scale assistance are separate conditions.** “It takes both full and half-scale assistance” can suggest they are applied together. Say **“Full and 0.5-scale assistance each complete all four missions.”** Use “walking mode” rather than “performed on foot”; the assisted runs do not validate foot-driven locomotion.

12. **Restore understandable diagnostic terms.** “Both ZAs do none and TO,” “6' test,” and “16 missions” obscure the protocol. Use **“both zero-assistance conditions complete no missions and time out at 180 s,” “six-foot contact criterion,”** and **“16 executions of four missions under four conditions.”** Six refers to selected foot geometries, not a six-foot distance. No detected contact at those feet does not establish absence of all robot contacts or prove a propulsion mechanism.

## Statements and values that remain supported

The tables retain the verified primary acceptance counts **93, 93, 93, 94, 93 and 90 out of 96**, in the order CLRP, PSO-P, ACO-P, PSO-C, noL and noP. There are **64 development attempts** and **576 primary attempts**, totaling **640**. Primary map seeds **2140000–2140031** and diagnostic seeds **1670000–1670003** remain correct.

The score formulas, battery reserve formula, all five conditional paired-map means and bootstrap intervals, the Table 4 effort figures, and the Table 5 aggregate contact/completion figures match the retained verification. The CLRP-versus-PSO-C effect remains **0.690%**, median **0%**, descriptive 95% interval **[−0.255%, 2.312%]**. These results do not establish a score advantage over PSO-C.

Map 24's numerical paragraph remains supported: CLRP distance **20.803 m**, Q **1.310**, predicted time **32.959 s**, nominal battery **15.446 percentage points**, exposure **1.012**; PSO-C mean distance **27.135 m**, Q **1.706**, time **42.584 s**, battery **20.066 percentage points**, exposure **1.665**. Its post hoc selection and retention in the primary analysis remain appropriate.

The prior independent reanalysis checked all 640 records, all 187 distinct stored world/route geometries, acceptance, Q, resource calculations and bootstrap outputs. For this pass I verified that the three raw planning files have the same hashes and all 29 frozen primary source hashes still match. I did not rerun simulations or repeat unchanged calculations unnecessarily. Diagnostic contact claims remain checks of stored aggregate summaries and detector code; per-step contact histories were not independently reconstructed.

## Literature and completeness

The A* opening sentence in Section 2 is confused and repeats cost-to-reach concepts. Replace it with: **“A* evaluates a node using the cost incurred to reach it plus a heuristic estimate of the remaining cost.”** This is the two-part evaluation described in the [original Hart, Nilsson and Raphael paper](https://people.stfx.ca/jdelamer/courses/csci-564/_downloads/b2220c66675ddde471ca1795147b8e86/A_Formal_Basis_for_the_Heuristic_Determination_of_Minimum_Cost_Paths.pdf).

The general descriptions of PSO, Ant System and the cited robot studies remain recognizable, but “best candidate in the world” should be **“globally optimal route.”** COCO supports transparent reporting of initialization, termination and evaluation counts; it does not establish equal geometric work under equal nominal caps. [COCO experimental procedure](https://numbbo.github.io/coco-doc/experimental-setup/).

The file contains in-text citations **[1]–[11]** but no bibliography. It also begins at the abstract without a title or author block. If this is the complete submission manuscript, restore the title, author information/affiliation and reference list. If it is intentionally a body-only excerpt, those omissions are outside the scientific corrections above.

In the review render, the **n** column of Table 3 wraps **31** and **30** into separate digits on two lines. Widen that column or adjust padding so each sample size stays on one line. The stored numbers themselves are unchanged. Long sections have also been merged into single paragraphs, making the argument difficult to follow; restore paragraph breaks by topic.

## Ready-to-paste replacements

### Abstract

> We evaluate landmark search and final local refinement for constrained body-route planning in a simulated hexapod. Six configurations share obstacle-clearance, deadline, nominal battery, and terrain-exposure constraints. Parameter selection uses 64 attempts on eight development maps; the primary test comprises 576 attempts on 32 maps with three repetitions. Full Constrained Landmark Route Planning (CLRP) accepts 93 of 96 primary attempts, compared with 94 for coordinate-based particle swarm optimization (PSO-C). Removing final refinement reduces acceptance to 90; the three lost acceptances are repetitions of one map. Removing landmark search retains 93 acceptances and reduces mean search time from 0.376 to 0.196 s. Full CLRP provides a conditional mean paired-map relative score improvement of 0.924% over this variant. Against PSO-C, the corresponding mean improvement is 0.690%, with a median of zero and a descriptive 95% bootstrap interval of [−0.255%, 2.312%], which does not establish a score advantage. A separate diagnostic comprises 16 executions of four missions under four assistance conditions. Full and 0.5-scale velocity assistance each complete all four missions; both zero-assistance conditions complete none and time out at 180 s. No foot contact is detected under the six-foot criterion in assisted executions. These results characterize planning trade-offs and assistance dependence in the specified simulation. Nominal battery costs lack physical or electrical validation.

### Section 3.3 opening

> The route evaluator computes outbound distance D in metres, predicted outbound travel time T in seconds, nominal battery cost E in percentage points, and terrain exposure R. The initial heading is π/2 radians. Predicted time includes terrain-dependent travel, turns at 1 rad/s and an acceleration allowance. The configured speed limits for terrain grades 0, 1 and 2 are 0.75, 0.65 and 0.38 m/s, respectively.

Keep the existing Equation (3) and its verified score denominators after this paragraph. Delete the sentence about smallmouth bass and the 10 mph phrase entirely.

### Section 3.3 candidate ranking

> Candidate ranking first distinguishes routes satisfying all resource constraints from those violating any constraint. Raw excesses of at most 10⁻⁸ are treated as zero. Larger positive excesses are divided by their corresponding limits and summed. Among rejected routes, lower total normalized violation ranks first, followed by lower Q when normalized violations are equal. Among accepted routes, lower Q ranks first. A rejected candidate cannot replace an accepted incumbent.

### Section 4.1 work and budget accounting

> Graph-edge checks and full route evaluations measure different work. A segment can be rejected before a complete route is formed. A shared ceiling on full route evaluations therefore does not imply equal geometric-query counts. Initialization route evaluations count toward the fixed common cap; they do not increase it. Every stage uses the same evaluator and ranking rule.

### Section 6.2 corridor outcomes

> All resource rejections occur on corridor maps. Every method accepts all 24 attempts in each of the open, cluttered and rough families. On corridor maps, CLRP, PSO-P, ACO-P and CLRP noL each accept 21 of 24 attempts; PSO-C accepts 22 and CLRP noP accepts 18. Each family has eight maps with three repetitions per map. The three additional CLRP acceptances over noP are repetitions of one corridor map, seed 2140011. All 20 rejected primary attempts exceed the predicted outbound deadline, while their battery and terrain-exposure checks pass.

### Section 6.3 omission analysis

> The 31 paired-map relative score effects against PSO-C range from −1.718% to 23.202%. Map 24 has the largest positive effect. Including all 31 maps gives a mean of 0.690%; omitting Map 24 gives −0.060% over the remaining 30 maps. For the noP comparison, leave-one-map-out means range from 0.682% to 0.822%. These post hoc summaries assess map influence without changing the primary sample. All maps remain in the primary analysis.

### Section 6.5 completion and assistance

> The diagnostic contains 16 valid executions, of which eight complete. Full and 0.5-scale direct body assistance each complete all four missions. Both zero-assistance conditions complete none and time out at 180 s. Leg-body gravity compensation is enabled in one zero-assistance condition and verified disabled in the other; environmental gravity remains unchanged.

> The eight assisted executions record no contact at the six selected foot geometries under the specified detector. These results demonstrate route following with direct body assistance and do not validate propulsion through foot–ground interaction. Small horizontal displacements occur under zero direct assistance, but no mission completes within 180 s in either gravity-compensation condition.

### Conclusion

> In the 32-map primary test, full CLRP accepts 93 of 96 attempts compared with 90 for CLRP noP; the difference consists of three repetitions of one corridor map. Including landmark search leaves acceptance unchanged at 93 of 96 and provides a conditional mean paired-map relative score improvement of 0.924%, while mean search time rises from 0.196 to 0.376 s. Against PSO-C, the mean paired-map relative improvement is 0.690%, the median is zero, and the descriptive 95% bootstrap interval includes zero. A score advantage over PSO-C is not established. PSO-C accepts one additional scheduled attempt.

> The separate diagnostic contains 16 valid executions. Full and 0.5-scale assistance each complete all four missions; both zero-assistance conditions complete none and time out at 180 s, with leg-body gravity compensation enabled or verified disabled. No foot contact is detected in assisted executions under the six-foot criterion. These observations distinguish constrained body-route acceptance from validation of unassisted locomotion. The results apply to the specified simulation model and objective, without physical or electrical validation of the nominal battery costs.

## Evidence locations and provenance

The main implementation checks are [constraint ranking](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/swarm.py:29), [fixed candidate budget and incumbent comparison](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/advanced.py:18), [landmark sorting](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/advanced.py:64), [time allowance](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/safe_navigation.py:145), [map-family sampling](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/worlds.py:115), [absolute score ties and map-level statistics](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/publication_2026_11_04_robot_figure/source/analyze_study.py:83), and [corrected gravity-compensation diagnostic](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/publication_2026_11_04_ten_page/source/corrected_gravity_probe.py:16).

The [retained independent numerical analysis](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-10_V3/qa/recomputed_experiment.json) supplies the method/family acceptance counts, work summaries, paired effects and motion aggregates. Current raw planning hashes and frozen source hashes were checked against it. The current source files cited above were also checked against their recorded snapshot where applicable.

Reviewed source SHA-256: `7038f264d2d9899f1b4d83146a23c1c05036699686f97419e7910aa4a01aabe0`.

This is a fact-check report with proposed replacements, not an edited Word manuscript. The supplied file, earlier manuscript files and experimental records were left unchanged.
