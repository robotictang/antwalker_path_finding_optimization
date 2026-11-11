# Final manuscript review

Reviewed 10 November 2026 against the live IJ3C author guide and its downloadable instructions. Highlighting was excluded from the assessment. The manuscript was not edited.

**Verdict:** The principal numerical findings and the restored references check out. Before submission, correct the alternative-profile description in Section 5.2, clarify endpoint sampling in Section 5.1, repair the table headings and author-affiliation markers, and complete a short English proofread. These corrections do not require changing the reported results or rerunning the experiment.

Reviewed manuscript: [current Word manuscript](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/NoReferences-Minimal-Factual-Corrections-Highlighted.docx). Page numbers below refer to the current ten-page render.

## Scientific corrections to make

### 1. Section 5.2, pages 5–6 — report the settings actually executed

Two details in the alternative-profile description need correction:

- The declared alternative CLRP configuration contains 12 labels per state, but all eight saved alternative CLRP executions used **eight labels per state**. The frozen implementation restores the default initial-refiner settings. I introduced the 12-label statement in the preceding highlighted edit by reading the declared profile without following that override; that correction was mistaken.
- The alternative initial-search fraction of **0.55** and local-refinement move sizes of **0.50, 0.15 and 0.05 m** apply to **all four base methods**, not only CLRP. Consequently, the statement that all other settings are unchanged is incomplete.

Keep the preceding method-specific particle, ant, inertia, coefficient and iteration settings. Replace the sentences beginning “The alternative CLRP profile consists…” and ending “All other settings…” with:

> In all four alternative profiles, the initial-search time fraction is 0.55 and the local-refinement move sizes are 0.50, 0.15 and 0.05 m. Alternative CLRP additionally uses a landmark-search time fraction of 0.25 and a maximum of 60 landmark points. Its executed initial refiner retains eight labels per state. Apart from these changes and the method-specific settings listed above, other effective settings remain at their respective defaults.

This describes the existing executions; it does not propose changing the experiment. The selected primary-test profiles are still the defaults.

Evidence: the retained [development-alternative records](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/publication_2026_11_05_revised/raw_study/development_alternative.json) record eight labels in `records[*].plan.optimizer.parameters.initial_parameters` for CLRP. The frozen [initial-refiner override](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/outputs/research/source_snapshots/20261104T014733366267Z/research/advanced.py:134) explains the difference between declared and executed settings. The shared alternative time fraction and move sizes also appear in the saved PSO-P and ACO-P records; PSO-C uses the shared values through the frozen [continuous PSO implementation](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/outputs/research/source_snapshots/20261104T014733366267Z/research/continuous_pso.py:28).

### 2. Section 5.1, page 5 — distinguish coordinate bounds from separation

The wording “with a starting distance of 12–26 m) on each axis” can imply that the distance bound applies separately on both axes. The code filters **Euclidean start–goal separation**.

Replace the two endpoint-sampling sentences with:

> Start and destination coordinates are sampled between −17 and 17 m on each axis, with an initial Euclidean separation of 12–26 m. The endpoints are then moved to free grid locations and retained if their final Euclidean separation is at least 10 m.

Evidence: the frozen [case generator](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/outputs/research/source_snapshots/20261104T014733366267Z/research/worlds.py:124).

## Results and fairness checks

No changes to table values or equations are indicated by this review.

| Check | Finding |
|---|---|
| Planning sample | 64 development attempts plus 576 primary-test attempts equals 640; 32 primary-test maps with three repetitions per method gives 96 attempts per method. |
| Acceptance | CLRP, PSO-P, ACO-P and CLRP noL each accept 93/96; PSO-C accepts 94/96; CLRP noP accepts 90/96. |
| Rejections | All 20 rejected primary-test method-attempt records fail the outbound deadline; battery and exposure checks pass. |
| Paired analysis | Map averages, conditional acceptance, tie tolerance, bootstrap intervals and paired-map sample sizes agree with the retained results. |
| CLRP versus PSO-C | Mean relative score effect 0.690%, median zero and interval [−0.255, 2.312]% are correctly reported without establishing a mean advantage. |
| Map 24 | Its influence is disclosed. Omitting it gives −0.060% across the remaining 30 paired maps; it remains in the primary analysis. |
| Stage removal | The three extra acceptances with final refinement are repetitions of one corridor map, not three independent map successes. Landmark removal leaves acceptance unchanged and reduces recorded search time. |
| Computation | Common evaluation ceilings are correctly distinguished from equal evaluation counts, geometric-query work and complete deployment latency. |
| Motion diagnostic | There are 16 valid executions and eight completions. Both assisted conditions complete four missions; both zero-assistance conditions complete none. |
| Physical interpretation | Direct velocity assistance, gravity compensation, six-foot contact detection and nominal battery costs are disclosed. The paper does not establish unassisted walking, physical battery savings or sensor-based navigation. |

For statistical wording, replace “map 24 has **significant impact**” in Section 7 with “Map 24 has a **strong influence**.” No significance test of that map's influence is reported. In Section 6.3, “relative score effects” is clearer than “improvements” for the collection containing negative values.

## IJ3C formatting review

The live [author guide](https://ij3c.ncut.tw/#authors) and [downloadable submission instructions](https://ij3c.ncut.tw/downloads/IJ3C_template.doc) were checked. The freshly downloaded instructions match the retained copy used in the earlier review.

| Requirement | Current finding |
|---|---|
| A4 paper | Pass: A4 dimensions are declared. |
| Two columns | Pass: main text and references use two columns; the title block and Figure 1 span the page width. |
| Times New Roman, at least 10 pt | Pass in Word declarations: Latin text is Times New Roman; ordinary text is 10 pt, with larger headings, author text and title. |
| Single line spacing | Pass for the manuscript's main text. |
| Generally no more than 10,000 words | Pass: approximately 7,365 whitespace-delimited words including tables, formulas and references. |
| Informative title without a subtitle | Pass: “Constrained Route Planning for a Simulated Hexapod” accurately identifies the subject and avoids a physical-validation claim. |
| Abstract no more than 250 words | Pass: 222 words. |
| No more than five keywords | Pass: five single-word keywords. |
| Numbered, left-aligned sections | Pass: sections 1–8 and their subsections are numbered and left aligned. |
| Numbered equations | Pass: equations (1)–(5) have right-side numbering and legible fractions/subscripts. |
| Figure/table references in order | Pass: three figures and five tables are introduced in order. |
| Sequential square-bracket citations | Pass: first appearances follow [1]–[11], and each has a reference entry. |
| Page numbers | Pass: all ten pages are numbered. |
| Initial submission file | IJ3C requests a single PDF containing the figures and tables. Export it after completing the corrections and checking the final PDF. |

The local QA renderer substituted Liberation Serif for Times New Roman. That is a rendering-environment limitation, not evidence that the Word document specifies the wrong font. Check that the actual submission PDF embeds Times New Roman. The internal QA PDF should not be treated as the final submission file.

### Layout corrections before submission

- **Table 1, page 5:** “Method” breaks inside the word, and “Final adjustment” breaks into several fragments. Widen those columns or use the short header “Refinement”; retain a font size of at least 10 pt.
- **Table 4, page 7:** “Median s” breaks as “Media / n s.” Use “Median” with “(s)” on the next line, or adjust the width.
- **Table 5, page 8:** “Done / 4” breaks inside “Done.” Use “Completed” and “/ 4” on separate lines, with enough width.
- **Section 4.3, page 5:** Table 1's caption appears once at the end of the prose and again above the table. Remove the caption embedded in the prose; retain the actual caption above the table.
- **Section 4.1, page 4:** Remove the isolated trailing “Algorithm 1.” after the paragraph. The preceding sentence already introduces the algorithm.

All ten pages were visually inspected. No missing equations, figures, clipped body text or overlapping content was found. The last reference page has uneven column lengths; balancing those columns is optional.

## Title and author block

The title is suitable. The affiliation block needs a small consistency cleanup:

- Six names carry a superscript 1, the first name does not, and the affiliation itself has no matching 1. If all authors share the single listed affiliation, remove the superscripts throughout; otherwise provide a consistent mapping for every author and affiliation.
- Use the institution's published name, **Research Centre for Human-Machine Collaboration (HUMAC)**. Add a comma after “Sunway University,” and remove the comma inside “Selangor Darul Ehsan.” These spellings and the address are supported by the university's [staff profile](https://www.sunwayuniversity.edu.my/research-centre-human-machine-collaboration-humac/staff-profiles/dr-tang-tiong-yew) and [contact page](https://sunwayuniversity.edu.my/contact-us).
- Clearly identifying the corresponding author would improve the block. The guide does not explicitly require a particular marker, so this is an editorial recommendation rather than an identified rule violation.

The review does not independently establish the authors' individual affiliations or intended corresponding-author role.

## English corrections worth making before submission

IJ3C explicitly includes English clarity in its screening instructions. The following are concrete corrections, not reasons to rewrite the scientific content.

| Location | Current wording/problem | Minimal replacement |
|---|---|---|
| Abstract, page 1 | “…is 0.690%, the zero median and the descriptive 95 % bootstrap interval is…” | “…is 0.690%, the median is zero, and the descriptive 95% bootstrap interval is…” |
| Introduction, page 1 | “…refinement during planning affects…” after “landmark search and…” | “…refinement during planning affect…” |
| Related Literature, pages 1–2 | “The ant system bases on…” | “Ant System uses…” |
| Related Literature, page 1 | “the best candidate in the world” | “a global optimum” |
| Related Literature, pages 1–2 | “minimizing the length one route” | “minimizing route length” |
| Related Literature, page 2 | “Does not make use of or test their controller.” | “The present study does not use or test their controller.” |
| Section 3.1, page 2 | “No physical measurements of motor torque-speed characteristics, battery depletion or robot mass.” | “Motor torque–speed characteristics, battery depletion and robot mass were not physically measured.” |
| Section 3.1, page 3 | “Also modifies horizontal velocity…” | “It also modifies horizontal velocity…” |
| Section 3.1, page 3 | “route choice choices” | “route choices” |
| Section 3.1, page 3 | “Not including sensor noise, localization errors and map reconstruction.” | “Sensor noise, localization errors and map reconstruction are not included.” |
| Section 3.3, page 3 | “Acceptance\" means…” | “Acceptance means…” |
| Section 3.3, page 3 | “Both rules are not statistically calibrated probability…” | “Neither rule provides a statistically calibrated probability…” |
| Section 3.3, page 4 | “The candidate ranking process first determines if routes meet all constraints, and then if they do not.” | “Candidates are ranked first by feasibility, then by total normalized violation, and finally by Q.” |
| Section 4.2, page 5 | “Does not only focus on the impact of representation.” | “The comparison does not isolate the effect of representation.” |
| Section 5.2, page 6 | “576 shots” | “576 planning attempts” |
| Section 5.4, page 6 | “Mission times are completed and includes…” | “Completed mission times include…” |
| Section 6.2, page 7 | “Search effort for all 96 search efforts…” | “Search effort across all 96 attempts…” |
| Section 6.3, pages 7–8 | “For the noP comparison, it is leave-one-map-out, remain positive…” | “For the noP comparison, the leave-one-map-out means remain positive…” |
| Section 6.4, page 8 | “This is why you are seeing the scores…” | “The returned routes therefore have different scores, although this does not identify a particular internal cause in the optimizer.” |
| Section 6.4, page 8 | “It is a one instance…” | “It is one instance…” |
| Section 7, page 9 | “final local adjustment is more accepted…” | “Final local adjustment has a larger observed acceptance effect…” |
| Section 7, page 9 | “a loss of recorded computation” | “a reduction in recorded computation” |
| Section 7, page 9 | “non-corridor action” and “corridor actions” | “non-corridor attempt” and “corridor attempts” |
| Conclusions, page 9 | “the description 95% bootstrap interval” | “the descriptive 95% bootstrap interval” |

Two small precision improvements are also useful: describe Table 1's PSO-C final 25% as a **reserved time allowance**, and describe Figure 3's obstacles as **black shapes** rather than only black squares, since the corridor barriers are rectangular.

## Reference review

All 11 references are identifiable and support the associated descriptions at the level used in the manuscript. The ten DOI records match the listed authors, titles, venues, volumes/issues, page ranges or article numbers, and years.

| Reference | Verification source |
|---|---|
| [1] MuJoCo | [DOI](https://doi.org/10.1109/IROS.2012.6386109) |
| [2] A* | [DOI](https://doi.org/10.1109/TSSC.1968.300136) |
| [3] Particle swarm optimization | [DOI](https://doi.org/10.1109/ICNN.1995.488968) |
| [4] Ant System | [DOI](https://doi.org/10.1109/3477.484436) |
| [5] Collision-free paths/visibility | [DOI](https://doi.org/10.1145/359156.359164) |
| [6] Ma's constrained A* label setting | [DOI](https://doi.org/10.1016/j.sbspro.2014.01.066) |
| [7] Guo, Sun and Chen | [Publisher](https://journals.sagepub.com/doi/10.1177/01423312241264860) |
| [8] Smart Gait | [Publisher](https://link.springer.com/article/10.1186/s10033-024-01000-0) |
| [9] Terrain-aware hexapod planning | [Publisher](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1605938/full) |
| [10] COCO procedure | [Official documentation](https://numbbo.github.io/coco-doc/experimental-setup/) |
| [11] Bootstrap foundation | [DOI](https://doi.org/10.1214/aos/1176344552) |

Keep **Guo, Sun, Chen** in that order in reference [7]. Its 2025 issue year is correct; the 2024 online-first date is not a reason to replace it. No missing or uncited reference was found. Full-text access was restricted for some publisher pages; the check used publisher-deposited DOI metadata and accessible primary abstracts/full texts, rather than treating every cited paper as fully reproduced.

No additional simulations are needed for the corrections identified here. The remaining work is to align the methods description with the retained executions, improve readability, and export a final PDF.

