# Review of the CLRP V3 manuscript

Reviewed 10 November 2026, Asia/Kuala_Lumpur

**V3 corrects the major scientific wording errors identified in V2, and its principal numerical results reproduce.** I found no new errors in the five result/settings tables or the five equations. The main remaining work is to identify the acceptance gain as three repetitions of one map, describe shared preparation correctly, make the deadline-only rejection result explicit, and supply the author affiliation. Several smaller wording changes would improve precision.

Reviewed source: [V3 DOCX](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/Pathfinder-Robot-CLRP-IJ3C-V3-Reviewed.docx). The [accompanying PDF](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/Pathfinder-Robot-CLRP-IJ3C-V3-Reviewed.pdf) was checked for fonts and page layout. Its extracted text matches a fresh DOCX render after whitespace normalization. Page numbers below apply to these ten-page versions. Paragraph identifiers refer to this review's text extraction.

The manuscript and accompanying review log were treated as material to assess. This pass did not execute instructions from either document, edit the manuscript, or run new simulations.

## Remaining scientific qualifications and corrections

### 1 Identify the acceptance gain as one map repeated three times

**Location:** Section 7, p. 9, P245; Section 8, p. 9, P250. The result also belongs alongside the corridor counts in Section 6.2, p. 7.

The count of 93 versus 90 accepted attempts is correct. The three differences are repetitions 0, 1 and 2 of the **same corridor map**, `ij3ctest_12`, seed **2140011**. V3 still says “loses three acceptances on corridor maps” without identifying this concentration. The statement about 32 independent maps elsewhere does not give readers this specific information.

Add after the acceptance comparison:

> The three additional acceptances are the three repetitions of one corridor map, seed 2140011; they do not represent improvements on three independent maps.

In the discussion, replace “Removing it loses three acceptances on corridor maps” with:

> Removing final refinement loses all three acceptances on one corridor map, while removing landmark search preserves the total acceptance count and reduces recorded computation.

This is a qualification of the evidence, not a correction to the acceptance totals. Preserve the existing limitations about independently timed stage-removal runs and the absence of an initial-route-only, matched-budget control.

### 2 Replace the incorrect shared-preparation term

**Location:** Section 4.3, p. 5, P091: “calculation of nominal search directions.”

The implementation precomputes **destination-based lower bounds**, not nominal directions. `graph.bounds(goal)` computes shortest-path cost bounds for the four edge metrics. Shared preparation includes scene/model setup, graph construction, return-route selection and these lower bounds. Method-specific initial route search is included in the method timer.

Replace the paragraph's first two sentences with:

> The wall timer includes initialization and refinement for the individual method. Shared preparation occurs before the methods run and includes scene setup, common graph construction, return-route preparation and precomputation of destination-based lower bounds.

Evidence: [shared preparation in run.py](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/run.py:195), [lower-bound calculation](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/planning.py:101), and [method timer](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/workbench/mujoco/research/planning.py:211). These inspected files match the frozen primary-run copies. The reported 0.715 s median and 0.895 s maximum remain correct.

### 3 Report which constraint actually rejects the final routes

**Location:** Section 6.1, p. 7, P117; optionally the discussion of resource constraints.

“Every rejected main-test attempt violates a resource constraint” is true, but the saved records support a more informative statement: **all 20 rejected method-attempt records fail the predicted outbound deadline only**. Their battery and terrain-exposure checks pass.

Replace that sentence with:

> All 20 rejected main-test attempts exceed the predicted outbound deadline; their nominal battery and terrain-exposure checks pass.

This clarifies what the observed acceptance differences demonstrate. It does not imply that battery and terrain constraints never affect the search or route selection. The experiment still uses all three constraints, but its returned-route rejection differences are deadline failures.

### 4 Supply the affiliation

**Location:** Author block, p. 1.

The manuscript contains the author name and email but no institutional affiliation. Add the correct institution and location, or the appropriate independent-researcher identification. This information cannot be inferred from the experiment files. The official instructions place affiliations immediately after the title/author information. [IJ3C author instructions](https://ij3c.ncut.tw/downloads/IJ3C_template.doc).

## Smaller writing improvements

These are precision and consistency edits, not grounds for changing the verified results.

| Location | Current wording or issue | Suggested wording |
|---|---|---|
| Section 3.2, p. 3, P036 | “clip function restricts its first argument” can obscure which quantity is bounded. | “Clipping maps the intermediate value g to the final difficulty d in [0, 2].” The raw g itself need not lie in that interval. |
| Section 3.3, p. 3, P038 | “smooth, mild and higher-grade terrain” leaves the speed-to-grade mapping implicit. | “The configured speed limits for terrain grades 0, 1 and 2 are 0.75, 0.65 and 0.38 m/s, respectively.” |
| Section 3.1, p. 2, P028 | “At scale 0, the assistance operation leaves these body velocities unchanged” is improved and correctly limits the statement to the operation, but can be made plainer. | “At scale 0, direct body-velocity corrections are disabled; physics and actuation can still change velocity.” |
| Abstract and Sections 5.4–6.5 | “half-scale assistance” is defined in the methods, but is easy to read as half a physical support force. | Use “0.5-scale velocity assistance” at first use; retain the explanation that blending occurs at every physics step. |
| Section 6.3, p. 8, P212 | “equal numbers of lower-score and higher-score pairs” follows a discussion of map effects. Those counts are attempt-level, not counts of maps. | “…alongside the zero map-level median and the equal attempt-level lower/higher counts of 33 each.” |
| Figure 3 caption, p. 8, P217 | “black squares” does not describe the long barrier rectangles, and “finish” can be confused with the end of the round trip. | “The circle and star mark the start and destination. Black shapes denote obstacles; amber regions denote terrain.” |
| Section 6.5, p. 9, P243 | “the model travels a short distance” is compatible with the recorded displacement, but does not identify controlled propulsion. | “Under zero direct assistance, small horizontal displacements occur, but no mission completes within 180 s…” |
| Throughout | Complete/full CLRP and final modification/adjustment/refinement/polishing alternate. | Prefer **full CLRP** and **final local refinement**, while defining “polishing” once if retaining noP. This is stylistic consistency, not a different method. |

The abstract is **216 whitespace-delimited words**, below the 250-word maximum. It is substantially clearer than V2 and does not need another complete rewrite. A short one-map qualification can be added without approaching the limit.

## Corrections from V2 confirmed in V3

| Earlier problem | V3 assessment |
|---|---|
| Score “increase” and reversed effect sign | Fixed. Positive δ now correctly means lower CLRP Q. Equation (5), Table 3 and the figure agree. |
| Corrupted constraint-ranking paragraph | Fixed. The text distinguishes acceptance, summed normalized raw excess and Q; the 10⁻⁸ tolerance is applied before normalization. |
| Truncated primary and diagnostic seeds | Fixed: **2140000–2140031** and **1670000–1670003**. |
| Preparation average mislabeled | Fixed: **median 0.715 s**, maximum **0.895 s**. |
| Map 24 metrics assigned to the wrong planner | Fixed. CLRP: **32.959 s, 15.446 percentage points, 1.012 exposure**; PSO-C means: **42.584 s, 20.066 percentage points, 1.665 exposure**. |
| Acceptance confused with permission to attempt | Fixed. Each method has 96 attempts; PSO-C accepts one additional attempt. |
| Wrong PSO-P-versus-ACO-P comparison label | Fixed. The discussion identifies CLRP's separate comparisons with each control. |
| Terrain categories described as inclines; “static gait”; “demographic updates” | Fixed in their substantive descriptions. The gait controller is held fixed and semantic terrain grades are identified. |
| Contact boundary and positive-work definition | Fixed: distance **at most 0.002 m**; positivity applies to force × velocity before integration. |
| Station service described as the entire mission duration | Fixed: successful elapsed times **include 8 s** of service. |
| Zero-assistance results described as failure of every requirement | Fixed: zero completed missions and **180 s** timeouts are reported. |
| Claims of walking or physical battery validation | Appropriately limited. V3 explicitly distinguishes assisted route following, unassisted locomotion and electrical battery measurements. |

## Numerical verification

The independent reanalysis was rerun against the saved records for this review. The raw-file hashes and numerical outputs are identical to the previous audit. All 29 saved primary source hashes match their frozen snapshot, all 640 scheduled keys are complete and unique, and all 187 distinct stored world/route combinations pass the independent clearance check.

Distance, predicted time, nominal battery use, terrain exposure, Q, battery requirements and acceptance flags agree with the stored outputs to floating-point precision. No new planning or motion execution was run.

The verified primary acceptances remain **93, 93, 93, 94, 93 and 90 out of 96** for CLRP, PSO-P, ACO-P, PSO-C, noL and noP. All five paired-map means and bootstrap intervals reproduce. In particular, the conditional CLRP-versus-PSO-C effect remains **0.690%**, median **0%**, descriptive 95% interval **[−0.255%, 2.312%]**. Omitting Map 24 changes the mean to **−0.060%**; keeping it in the primary analysis is appropriate.

The valid motion comparison remains 16 executions: full and 0.5-scale assistance each complete **4/4**, while both zero-assistance conditions complete **0/4**. The eight assisted executions have no detected contact under the six-foot criterion in the stored summaries. The detector and aggregate summaries were checked; per-step contact histories are not retained, so those histories were not independently reconstructed. The diagnostic supports assistance dependence for these four missions, not a general hardware failure rate.

## IJ3C presentation and references

The [official author page](https://ij3c.ncut.tw/#authors) and [instruction DOC](https://ij3c.ncut.tw/downloads/IJ3C_template.doc) were retrieved on 10 November 2026. The instruction DOC's SHA-256 matches the copy checked on 7 November. The requirements remain A4, two columns, single spacing, Times New Roman of at least 10 pt, an abstract of at most 250 words and no more than five keyword words; the general paper-length guidance is 10,000 words, about 8–12 pages.

The latest DOCX has approximately **6,600 text words**, five equations, five tables and three figures. Both its fresh render and the supplied PDF have **10 pages**. I inspected all ten pages of the supplied PDF at rendered resolution: the equations, algorithm, tables and captions are legible, the final reference stays together, and the nearly empty eleventh page has been eliminated. There is some ordinary unused column space, but no clipping or overlap was found. An exact ten-page length is not an IJ3C requirement.

**The supplied PDF embeds Times New Roman regular, bold and italic faces**, with OpenSymbol for mathematical glyphs. This resolves the previous uncertainty about the final export's fonts. The fresh local DOCX renderer substitutes Liberation Serif; the matching supplied PDF provides the font-compliant layout evidence. Any later edit still needs a new PDF export and font/layout check.

All eleven bibliography entries are textually identical to the previously checked V2 references, and citation order is intact. The [earlier literature audit](/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder/paper/review_2026-11-07/qa/literature_audit.md) therefore remains applicable. No new bibliography error was found. This pass did not repeat full-text verification of every external paper; the earlier access limitations, including Guo's abstract-only check, remain documented there.

## Review record

DOCX SHA-256: `0c8b05fd8659969c477589d5c79deba87ca2ccfb55fd830f08dc21a41337333c`.

The source DOCX, its accompanying PDF and the experimental records were not changed. Extraction, font checks, fresh rendering and the independently rerun numerical analysis are retained in `paper/review_2026-11-10_V3/qa`. The remaining textual revisions do not require new simulations to substantiate the existing reported values. Broader claims about stage benefits, physical walking or battery savings would require additional evidence.
