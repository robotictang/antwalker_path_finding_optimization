# Fact check and writing review

Reviewed 7 November 2026, Asia/Kuala_Lumpur

The main numerical results in **Pathfinder-Robot-CLRP-IJ3C-V2.odt** are reproducible from the saved experiment records. The manuscript needs substantive prose corrections before submission: its score interpretation is reversed in one paragraph, some metrics are assigned to the wrong planner, two seed ranges are truncated, and the candidate-ranking explanation is corrupted. The evidence supports a constrained body-route planning study and a diagnostic of dependence on direct body assistance. It does not establish unassisted walking, physical battery savings, or a general advantage over PSO-C.

The named ODT is the version reviewed. The original manuscript and experiment files were left unchanged. Page numbers below refer to a fresh render of that ODT; section numbers and quoted opening phrases are more stable locators. Ready-to-paste revisions are in [Suggested Replacements](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/Suggested_Replacements.md).

## Corrections that affect scientific meaning

| Location | Finding | Required correction |
|---|---|---|
| Abstract, p. 1 | “relative score increase of 0.924%” conflicts with the lower-is-better objective. | Say **conditional mean paired-map relative score improvement of 0.924%**. An increase in Q would be worse. |
| Section 5.3, p. 6, opening paragraph | The prose reverses Equation (5). | With δ = 100(Qc − QCLRP)/Qc, **positive values favor CLRP** and negative values favor the comparison method. Keep the equation and change the prose. |
| Section 3.3, p. 4, “The front-runner differentiates…” | Stray “4.” and “5.” fragments, “total violations,” and “inferior Q” obscure the actual ranking rule. | Replace the paragraph with the implemented rule: accepted routes first; then lower summed normalized constraint excess; then lower Q. The tolerance is applied to raw excesses before normalization. |
| Section 5.1, p. 5 | Primary seeds are written as 2140–2140031. | Use **2140000–2140031**. Development seeds 2130000–2130007 are correct. |
| Section 5.4, p. 6 | Diagnostic seeds are written as 1670–1670003. | Use **1670000–1670003**. These four diagnostic maps are separate from the 32 primary maps. |
| Section 6.2, p. 8 | Shared preparation time 0.715 s is described as an average. | It is the **median**, rounded from 0.715205 s. The arithmetic mean is **0.720 s**, rounded from 0.719866 s. The maximum 0.895 s is correct. |
| Section 6.4, p. 8 | The sentence beginning “For PSO-C…” assigns 32.959 s, 15.446 percentage points, and 1.012 exposure units to the wrong planner, then ends “for CLRP.” | Those are **CLRP** means. The corresponding **PSO-C** means are **42.584 s, 20.066 percentage points, and 1.665 exposure units**. |
| Sections 6.1, 7 and 8, pp. 7, 9–10 | “PSO-C only permits one try,” “permits one more trial,” and “allows one additional attempt” misdescribe acceptance results. | Both methods have 96 attempts. Say **PSO-C accepts one additional route**, or **one attempt is accepted only by PSO-C**. |
| Section 7, p. 9 | “The PSO-P versus ACO-P comparisons” describes a comparison that Table 3 does not report. | Say **the comparisons of CLRP with PSO-P and with ACO-P**. |
| Sections 5.4 and 6.5, pp. 7 and 9 | “Mission completion times are simulated station operations of eight seconds” and “none … meets any requirement” change the meaning of the results. | Completion times **include an 8 s station-service interval**. Both zero-assistance settings **complete none of the four round trips and time out at 180 s**; this does not mean every individual requirement fails. |
| Section 6.5, p. 9 | “The model can move a short distance on its own” can imply demonstrated locomotion. | Say **small displacements occur in the zero-assistance conditions**. Displacement alone does not demonstrate controlled locomotion or foot-driven propulsion. |
| Section 7, p. 10 | “diversity in maps by algorithm” misstates what repetitions measure; “The operation of the actuator does not involve body-assisted work” also misstates an accounting limitation. | Repetitions measure **algorithmic variation on the same map**. The **reported positive actuator work excludes work introduced by direct body-velocity changes**. |
| Sections 3.2–3.3, p. 3 | “terrain inclines of 0, 1 and 2” and “flat, gentle and steep” conflate semantic categories with measured physical slopes. | Use **terrain grades 0, 1 and 2**. Grade determines configured speed and softness; the separate slope proxy comes from sampled heights. The patches are rectangular, not necessarily square. |
| Section 4.3, p. 5 | Shared preparation is said to compute “standard search trajectories,” which could place method initialization outside its budget. | Say **precomputation of shared lower bounds**. Method-specific initial route search is included in its budget. |
| Section 5.4, p. 7 | Foot contact is described as distance strictly less than 0.002 m. | The detector uses **distance at most 0.002 m**. This is a contact-record criterion, not a measurement of a load-bearing foot. |

These are reporting errors. They do not require changing the verified result tables or rerunning the experiment to correct the text.

## Findings confirmed against the records

The numerical audit independently recomputed the scheduled trial counts, acceptance flags, route scores, battery requirements, paired-map statistics and bootstrap intervals. It checked the saved source hashes and distinguished primary tests from the separate assistance diagnostic. The detailed record and executable reanalysis are retained in the review's QA directory.

| Claim | Verified result |
|---|---|
| Development design | 8 maps × 4 base methods × 2 profiles = **64 attempts**. |
| Primary design | 32 maps × 6 methods × 3 repetitions = **576 attempts**; **96 per method**; **640** including development. No recorded trial errors. |
| Accepted primary routes | CLRP **93/96**; PSO-P **93/96**; ACO-P **93/96**; PSO-C **94/96**; CLRP noL **93/96**; CLRP noP **90/96**. |
| Mean search times | Respectively **0.376, 0.223, 0.335, 0.731, 0.196, 0.329 s**, in the same method order. |
| CLRP versus PSO-C | Conditional mean paired-map relative improvement **0.690%**; median **0%**; descriptive 95% bootstrap interval **[−0.255%, 2.312%]**; **31 paired maps**. |
| Other mean improvements and intervals | Versus PSO-P **0.929% [0.027%, 2.523%]**; ACO-P **0.921% [0.029%, 2.507%]**; noL **0.924% [0.036%, 2.513%]**; noP **0.794% [0.443%, 1.209%]**. The first three use 31 maps; noP uses 30. |
| CLRP/PSO-C paired outcomes | **33** mutually accepted attempts with lower CLRP Q, **27** ties, **33** with higher CLRP Q; **1** accepted only by PSO-C; **0** only by CLRP; **2** rejected by both. |
| Rejected primary routes | All **20** rejected method-attempt records are on corridor maps. Each fails the **outward deadline only**; battery and exposure limits pass. “Resource constraint” is defensible but less informative. |
| Search-effort table | Table 4 agrees with the records, including PSO-C reaching 240 evaluations in **84/96** attempts and its maximum search time **1.203 s**. |
| Map 24 | CLRP distance **20.803 m**, Q **1.310**; PSO-C mean distance **27.135 m**, mean Q **1.706**. The map's paired relative effect is **23.202%**. |
| Map influence | The PSO-C comparison spans **−1.718% to 23.202%**. Omitting Map 24 changes the mean to **−0.060%**. The noP leave-one-map-out means remain **0.682%–0.822%**. |
| Assistance diagnostic | **16 valid runs**, four missions in four conditions. Full and half-scale assistance each complete **4/4**; both zero-assistance conditions complete **0/4** and time out at **180 s**. |
| Six-foot contact diagnostic | All eight assisted runs report mean contacting feet **0.000** and no-contact fraction **100%**. Table 5's zero-assistance ranges also agree with the records. |

The bootstrap calculation uses 5,000 map-level resamples, seed 41104, and percentile endpoints. All five intervals reproduce at the displayed precision. The score-tie threshold is an absolute difference of at most 10⁻⁸ in Q, not a difference of 0.01 or a percentage-point tolerance.

## Interpretation that should remain explicit

**The three additional acceptances come from one map.** Removing final refinement loses repetitions 0, 1 and 2 of corridor map `ij3ctest_12`, seed 2140011. This is a three-attempt gain on one of 32 maps, not three independent map successes. PSO-C's additional acceptance occurs on corridor map `ij3ctest_32`, seed 2140031, repetition 0. Describe the acceptance changes as observations in this test set; no general acceptance advantage has been established.

**The score effect is conditional and map weighted.** The analysis first computes paired relative differences for mutually accepted repetitions, averages within each map, then gives each eligible map equal weight. It is not an unconditional average over all 96 attempts, a comparison of overall mean raw scores, or a percentage saving in measured battery energy. Report acceptance alongside the conditional score effects.

**The comparison with PSO-C does not establish a score advantage.** The interval includes zero, the median map effect is zero, the lower/higher attempt counts are equal, and Map 24 strongly influences the positive mean. These observations also do not establish equivalence or prove CLRP inferior. Keeping Map 24 in the primary analysis and identifying its route plot as a post hoc example are appropriate.

**Equal nominal limits do not mean equal work.** Methods share the evaluator and caps, but differ in initialization, representation, geometric-query counts and termination. PSO-C often exhausts the route-evaluation cap while other methods stop earlier. The stage-removal study estimates the effects of the tested configurations; it does not isolate a universal stage benefit under matched effective work. The existing discussion of an initial-route-only control and budget-matched comparisons should remain.

**The diagnostic establishes assistance dependence for four missions.** The body controller directly changes free-body velocities; the half-scale condition is a velocity blend applied repeatedly, not a measurement of half the support force. Gravity compensation is a separate mechanism. No detected contact at the six selected foot geometries supports the conclusion that the assisted runs do not validate foot-ground propulsion. It does not establish the absence of every robot contact or external interaction.

The contact results were checked against the stored summaries and detector implementation. Per-step contact histories are not retained, so they could not be independently reconstructed in this review. Of 20 stored diagnostic executions, four original GC-off attempts are superseded; the valid comparison consists of 12 original GC-on runs and four corrected GC-off reruns, not all 20 pooled together.

**Nominal battery costs remain model outputs.** The score combines correlated route features, and the battery coefficients and reserve rule are not calibrated to electrical measurements. Positive actuator work excludes the work associated with direct body assistance. Claims of physical energy efficiency, battery conservation or hardware performance would require additional measurements.

The source/model checks support the reported imported mass of 97.52 kg, assembled mass of 113.32 kg, 23 actuators, 0.004 s physics step, 0.016 s controller interval, and the stated distinction between gravity compensation and body assistance. Keep these labeled as simulation specifications and audited model values.

## Literature check

All **11 references are identifiable**, and their listed authors, DOIs, publication details and page or article numbers agree with primary sources or publisher-deposited metadata. The substantive summaries of Ma, Guo, Yin and Chen are supported. Guo's **2025 issue year is correct** despite online-first publication in 2024. The COCO access date of **6 November 2026** is valid relative to this review date.

Use “best positions found so far” for PSO rather than “optimal positions,” and replace “demographic updates” with “population updates.” Ma concerns multiple resource constraints and mode-chain constraints. Chen's technical terms are traversal costs, foothold selection and free-gait planning. COCO supports transparent reporting principles; it does not certify that this experiment is a COCO benchmark or that equal caps provide equal computational effort. [Ma publisher record](https://www.sciencedirect.com/science/article/pii/S1877042814000676), [Guo publisher abstract](https://journals.sagepub.com/doi/10.1177/01423312241264860), [Yin full text](https://link.springer.com/article/10.1186/s10033-024-01000-0), [Chen full text](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1605938/full), [COCO procedure](https://numbbo.github.io/coco-doc/experimental-setup/).

Guo's full text was restricted; its description was checked against the publisher abstract. Some IEEE/ACM landing pages blocked extraction, so DOI metadata and original author/university copies were used. These access limitations do not imply invalid references. The full citation-by-citation record is preserved in the QA literature audit.

## IJ3C formatting check

The [current author guide](https://ij3c.ncut.tw/#authors), [official instruction file](https://ij3c.ncut.tw/downloads/IJ3C_template.doc), and [sample file](https://ij3c.ncut.tw/downloads/IJ3C_Sample-file.doc) were retrieved on 7 November 2026. The two downloaded DOC files exactly match the repository's retained official copies by SHA-256. Written instructions take priority over inconsistent examples in the older sample.

| Requirement or check | Latest ODT assessment |
|---|---|
| Generally no more than 10,000 words, about 8–12 two-column pages | Approximately **7,300 visible text words**. Fresh review render has **11 pages**. There is no exact ten-page requirement. |
| Abstract at most 250 words | **250 whitespace-delimited words** in the present abstract, including a separated punctuation token. It is at the limit and needs editing; a shorter replacement is supplied. |
| No more than five keyword words | Five single-word entries comply. Replace the vague “strategising” with “planning.” |
| A4, two columns, single line spacing, Times New Roman at least 10 pt | A4, two-column body and single spacing are present. Text styles declare Times New Roman, 10 pt body/tables/captions, 16 pt title, 11 pt author/main headings and 10.5 pt subheadings. |
| Actual PDF font compliance | **Unverified for the latest ODT's final export.** The review runtime substituted Liberation Serif for Times New Roman. Check font embedding in the actual submission PDF. The prior revision's font audit does not certify this ODT. |
| Numbered pages and headings | Page numbers and Arabic section/subsection numbering are present. Arabic numbering follows the written instructions even though the older sample uses Roman main headings. |
| Serial equations with right-side numbers | Five editable formula objects, numbered (1)–(5), render legibly. Remove stray prose numbering such as “5. In equation”. Define symbols in complete sentences. |
| Figures and tables in numerical order | Three figures and five tables are present and cited in order. Repeated caption text in the XML extraction includes image alternative text; it is not a duplicate visible caption. |
| Author affiliations follow title | Name and email are present; **institutional affiliation is missing**. Add the correct affiliation or appropriate independent-researcher identification. |
| References and pagination | All 11 references are numbered and cited. The review render strands reference [11] on page 11 and splits it between columns. Reflow the ending and keep the reference together. |
| Submission file | The working ODT is editable, but the journal requests a **single PDF for initial submission**, and source DOC files after acceptance. Check the final PDF after text revisions. |

All 11 rendered pages were visually inspected. The tables repeat their headers when split and the equations are readable. The main layout defect is the orphaned final reference. Pagination and exact line breaks may differ with Times New Roman available; the page count and final-page defect above describe this review render, not a verified font-compliant submission export. Do not shrink text below 10 pt to solve the last-page problem.

The existing paper README and earlier QA files describe a previous nine-page manuscript with three equations. They should not be used as the formatting certificate for this ODT, which now has five equations and different pagination.

## Writing revisions across the manuscript

Use stable terms throughout: **full CLRP**, **landmark search**, **final local refinement**, **accepted route**, **outbound route**, **nominal battery cost**, **terrain exposure**, **heading**, and the map families **open, cluttered, rough, corridor**. Alternating among “comprehensive,” “front-runner,” “approved,” “sanctioned,” “permits,” “expenses,” “title,” “disorganized” and “rugged” obscures otherwise precise definitions.

Several complete sentences need rebuilding, not just grammar correction. Examples include the final fragment in the first introduction paragraph; the symbol definitions after Equations (1)–(2); the candidate-ranking paragraph; the parameter-selection tie-break; and the first paragraph of Section 5.3. Avoid describing the heuristic's retained route as “optimal,” and use “fixed gait controller” rather than “static gait controller” unless static stability is actually established.

The supplied replacements cover the abstract, the major technical errors, the principal methods explanations, and the interpretation paragraphs. They preserve the verified numerical results and distinguish observed findings from unsupported generalizations.

## Review provenance

Reviewed source SHA-256: `53b0c0d45f841779763e0309580a591282badf44af99958e724b00e26f8c96f4`.

The review used the saved raw development and primary study records, frozen source snapshots, model audit, corrected 16-run gravity/assistance diagnostic, original equations, fresh ODT rendering, current official IJ3C files, and primary literature. Independent reanalysis and reviewer notes are saved under `paper/review_2026-11-07/qa`. No new planning simulation, physical measurement, sensitivity study or preregistration verification was performed. Statements about what was decided before the main experiment remain statements supported by the saved protocol/source lock, rather than independent proof of a public preregistration.

Detailed evidence with code/data locators: [numerical audit](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/qa/experiment_audit.md), [methods audit](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/qa/methods_audit.md), [literature audit](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/qa/literature_audit.md), and [independent reanalysis script](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/qa/recompute_experiment.py).
