# Text corrections for Pathfinder Robot V2

The corrected document is **Pathfinder-Robot-V2-Text-Corrected.docx**. The original V1 file is unchanged. Section numbers below refer to the manuscript headings and remain valid if page numbers change.

This edit corrects the requested technical statements, Algorithm 1 and prose grammar. It preserves the existing formatting settings, reference entries and citation markers, all five tables, all three images and all three native equations. Text changes can alter line wrapping and pagination. This is a text correction pass, not a formatting or reference audit.

## Exact replacements for the requested passages

### 1. Score ties

**Location:** Section 5.3, first paragraph

**Find:**

> Scores within 0.01 of each other are considered ties.

**Replace with:**

> Absolute differences between Q_c and Q_v of at most 10⁻⁸ are counted as ties.

This tolerance applies to the absolute difference between the original Q scores, not to percentage improvements. It preserves the tie counts calculated by the analysis script.
### 2. Constraint tolerance and ranking

**Location:** Section 3.3, final paragraph, beginning “If any hard threshold…”

**Find:**

> If any hard threshold is exceeded, a pathway is still eliminated even if its score is lower. The first candidate is able to differentiate between routes which satisfy all constraints and those which don’t. If a route is rejected, the excess over each threshold is divided by the threshold. The positive ratios are added together. The goal is to get a lower total, where differences of 0.01 or less are negligible. For approved pathways, prioritize lower Q ranks first. This regulation permits a search phase to improve both acceptance and scoring, while avoiding to replace an accepted path by a later rejected candidate.

**Replace with:**

> Candidate ranking first distinguishes routes that satisfy all constraints from those that do not. For each constraint, raw excesses of at most 10⁻⁸ are treated as zero. Larger positive excesses are divided by their corresponding limits and summed. Lower total normalized violation ranks first, followed by lower Q when total violations are equal. Among accepted routes, lower Q ranks first. A rejected candidate cannot replace an accepted route.

The incorrect phrase is “where differences of 0.01 or less are negligible.” Replace the whole paragraph to make the operation order explicit: test raw excess against 10⁻⁸, then normalize retained positive excesses and sum them. This is separate from the score-tie rule in Section 5.3.
### 3. Comparison methods

**Location:** Section 1, second paragraph

**Find:**

> It has mechanisms like particle swarm and ant inspired schedules, a particle swarm optimizer with varying point coordinates, and two iterations without the V4 phase.

**Replace with:**

> The comparison includes particle swarm and ant-based planners that select points from initial routes, a particle swarm planner that moves intermediate point coordinates, and two V4 variants with one search stage removed.
### 4. Positive actuator work

**Location:** Section 5.4, final paragraph

**Find:**

> Positive actuator work includes the product of positive actuator force and actuator velocity .

**Replace with:**

> Positive actuator work is calculated by multiplying actuator force by actuator velocity, retaining only positive power, integrating over time and summing over actuators.

Replace the entire sentence rather than only “positive force.” Positivity applies to force × velocity: W⁺ = Σᵢ ∫ max(Fᵢvᵢ, 0) dt. A negative force multiplied by a negative velocity also gives positive power. The manuscript retains the prose definition without adding another numbered equation.
### 5. Timeout and completion

**Location:** Section 5.4, second paragraph

**Find:**

> A pending task has already missed its deadline.

**Replace with:**

> Unfinished missions time out at 180 s; this execution limit is distinct from the planner’s outward-route deadline.

The ambiguous conclusion is also replaced in Section 8:

**Find:**

> The sixteen legitimate motion executions give an independent diagnosis: the four evaluated missions are executed with full or partial assistance and end at zero assistance, with or without confirmed leg gravity compensation.

**Replace with:**

> Full and half-scale assistance each complete all four missions. Both zero-assistance conditions complete none and time out at 180 s, with or without verified leg-body gravity compensation.
### 6. Foot contact and propulsion

**Location:** Section 6.5, final paragraph

**Find:**

> This shows the augmented body model following a path, without generating thrust from foot-ground interactions.

**Replace with:**

> These results demonstrate route following with direct body assistance and do not validate propulsion through foot–ground interaction.

The preceding sentence now states that no foot contact was recorded at any sampled physics step. A detector limited to six foot geometries does not establish the absence of all propulsive forces or all other robot contacts.
### 7. Statistical interpretation

**Location:** Section 7, second paragraph

**Find:**

> The mean score of V4 is not better than that of PSO-C.

**Replace with:**

> The study does not demonstrate a mean score advantage for V4 over PSO-C.

The revised paragraph also states: “An interval spanning zero establishes neither equality nor inferiority.” The same interpretation appears in the abstract and conclusion.

In Section 8, replace:

> V4 does not have a higher mean score than PSO-C. Its paired-map mean is 0.690%, with a median of zero and a descriptive interval that includes zero.

with:

> The study does not demonstrate a mean score advantage over PSO-C: the mean paired-map relative improvement is 0.690%, the median is zero, and the descriptive 95% bootstrap interval includes zero.

The reported 0.690% is a mean **relative improvement**, not a mean Q score. Lower Q scores are better. This terminology is corrected throughout the abstract, results, discussion and conclusion. The 0.924% comparison with noL is also labeled as a relative score improvement.
### 8. Terrain patch counts

**Location:** Section 5.1, second paragraph

**Find:**

> The terrain patches are numbered 1, 2, 4 and 3.

**Replace with:**

> The four families contain 1, 2, 4 and 3 terrain patches, respectively.

The preceding sentence names the families in order: open, cluttered, rough and corridor. The numbers count patches; they are not patch identifiers.
### 9. Endpoint-generation order

**Location:** Section 5.1, third paragraph

**Find:**

> If the final distance is at least 10 meters, they are moved to empty grid cells and saved.

**Replace with:**

> The proposals are moved to free grid locations and retained if their final separation is at least 10 m.
### 10. Bootstrap interval wording

**Location:** Abstract

**Find:**

> an overall 95% bootstrap interval of [−0.255, 2.312]% that includes zero

**Replace with:**

> a descriptive 95% bootstrap interval of [−0.255, 2.312]%

“Overall” is removed. Section 5.3 explicitly states that the five intervals are not adjusted for multiple comparisons. The confidence level and numerical interval are unchanged.
### 11. Whole-mission and outward-route measurements

**Location:** Section 3.3, penultimate paragraph

**Find:**

> Thus, the distance and time of the mission are larger than the initial D and T.

**Replace with:**

> Whole-mission distance and elapsed time describe execution of the destination-and-return task, whereas D and T describe the planned outward route. Failed executions can end before completing either leg.

The revision explains measurement scope without claiming that every execution travels farther or takes longer than the planned outward route. Section 6.5 separately reports the short distances traveled before the zero-assistance timeouts.

## Revised Algorithm 1

Algorithm 1. Complete V4 route search.

Inputs: known obstacle geometry and terrain; start, destination and initial heading; task constraints and fixed return allowance; random seed; a 2 s search-time limit and a 240-route-evaluation limit.

1. Run the initial resource-aware refiner for up to 40% of the nominal search time. Charge its route evaluations to the shared limit and retain its best available route.

2. Test the direct start-to-destination route if budget remains. Reject invalid or blocked geometry. Evaluate valid routes using the common metrics and constraint-ranking rule; reuse cached evaluations for repeated geometry.

3. Collect the initial route’s internal points, inflated obstacle corners and points around terrain boundaries. Remove duplicate, out-of-bounds and blocked points. Sort the remaining candidates by the sum of their distances to the start and destination. Retain at most 44 points, including the start and destination.

4. Build collision-free visibility connections. Search the resulting graph with heading-aware states using score, time and battery weighting in turn. Limit this stage to its 32% nominal-time allocation and the remaining expansion budget. Evaluate complete routes with the common ranking rule.

5. Adjust the best retained route by testing internal-point deletion, movement halfway toward the neighboring-segment projection, midpoint replacement and moves in eight directions at step sizes of 0.75, 0.25 and 0.08 m. Retain only improvements in rank. At each step size, stop after three passes, a pass with no improvement, or exhaustion of the shared budget.

Output: the best retained route and its metrics, or the initial search status if no route is retained. Accepted routes always rank ahead of rejected routes.

## Additional factual and grammatical corrections

- **Section 3.1:** “with a total mass of 46 kg” → “and a base mass of 46 kg”; total assembled mass remains 113.32 kg. Mass replaces weight where kilograms are reported.
- **Section 3.1:** the contradictory sensor-input sentence is replaced by “These inputs are not estimated from sensor measurements.” The previous sentence states that the inputs come directly from the simulator.
- **Section 3.1:** “This remuneration” → “Gravity compensation”; “leg structures” → “leg bodies”; assistance level 0.5 is written consistently and described as velocity blending.
- **Section 3.2:** second-person and pedestrian language is replaced with robot-specific descriptions of grid moves, terrain difficulty and body-route clearance.
- **Section 3.3:** “determinants” → “denominators”; “subscript r” → “subscript return” to match equation (2); missing punctuation and the doubled period are corrected.
- **Sections 4.1–4.3:** “changes the routes completely,” “communal,” “condensed versions” and related wording are clarified as route adjustment, common procedures and reduced variants. The final adjustment is distinguished from processing within the initial refiner.
- **Section 4.2:** “The start and end point are fixed” → “The start and end points are fixed”; both x and y coordinate movement remains explicit.
- **Section 5.2:** profile-selection fragments are replaced with complete sentences. The default profile wins exact ties. Development and main-test counts are expressed as 64 + 576 = 640 attempts.
- **Section 5.2:** the averaging procedure is corrected: average paired effects within a map, then summarize equally weighted maps. Three repetitions do not create three independent maps.
- **Section 5.3:** the reversed interpretation of negative relative score differences is corrected: a negative difference means the comparison method has the lower score.
- **Section 5.3:** “familial disaggregation” and “averaged re-calibrated” are replaced with map-family breakdowns and recalculation of the mean. The processor description is repaired as a complete sentence.
- **Section 5.4:** the exclusion and rerun of the four incorrectly initialized no-compensation executions is stated clearly. The final diagnostic still contains 16 valid executions.
- **Section 6.1:** acceptance counts and paired results are expressed in complete sentences; one PSO-C-only acceptance and two jointly rejected attempts are distinguished from paired accepted comparisons.
- **Section 6.2:** map-family acceptance counts and computational measurements are rewritten to remove sentence fragments. Search timers are distinguished from shared preparation.
- **Sections 6.3–6.4:** “versions” and “iterations” are corrected to repetitions where they refer to repeated trials. Omitting map 24 leaves 30 paired maps; the full analysis retains all 31 paired maps.
- **Section 6.5:** “a score of 0/4” is corrected to zero completed missions. Full and half-scale assistance each complete four missions; zero assistance completes none.
- **Sections 7–8:** “feature not a bug,” second-person wording and unsupported statistical conclusions are replaced with formal, evidence-based statements. Route acceptance, motion completion and physical validation remain distinct.

No new experiments were run, and no numerical results were changed. The wording corrections were checked against the existing planner, analysis and telemetry implementations and retained study results. Reference content and formatting compliance are outside this pass.
