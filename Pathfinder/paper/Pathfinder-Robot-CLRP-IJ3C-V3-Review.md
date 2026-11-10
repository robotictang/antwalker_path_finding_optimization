# Review of the rewritten CLRP manuscript

Reviewed 6 November 2026. The attached V2 ODT remains unchanged. A separate V3 contains the corrections. The review addressed scientific meaning, spelling, grammar, references and IJ3C presentation; it did not optimize text for an AI detector or run new simulations.

## Scientific meaning repaired

| Location | Problem in V2 | Correction in V3 |
|---|---|---|
| Abstract | A “score increase of 0.924%” suggests a worse result, although lower Q is better. | A conditional mean paired-map relative **score improvement** of 0.924% over the version without landmark search. |
| Abstract and assistance sections | “Comprehensive and partial support” does not identify the tested conditions. | **Full and half-scale body assistance**, distinguished from both zero-assistance conditions. |
| Related literature | Particle positions were called “optimal”; “demographic updates” and a “static gait controller” changed the technical meaning. | **Best positions found**, **population updates**, and a gait controller **held fixed across comparisons**. |
| Section 3.2 | Terrain grades 0, 1 and 2 became “inclines”; sampled heights became measurements; variable definitions ran together. | Semantic **terrain grades**, **sampled** heights and complete definitions of s, h, u and f. |
| Section 3.3 | “The title is in radians” and “normal battery usage” obscure the model definitions. | **Initial heading π/2 radians** and **nominal battery use**. |
| Section 3.3 | The ranking paragraph included stray numbered fragments and introduced an extra violation-ranking step. | Accepted routes rank first; raw constraint excesses **≤ 10⁻⁸** are ignored; remaining positive excesses are normalized and summed; lower Q breaks equal normalized-violation ranks. |
| Sections 3.3 and 5.4 | Whole-mission and outward-route measurements were mixed, and station service was described as the mission duration. | D and T describe the **planned outward route**; execution measures the destination-and-return mission. Completed mission times **include eight seconds** of station service. |
| Section 4.1 | “Remarkable cap,” different “titles,” and a “frequent shortcoming” replaced algorithm concepts. | **Landmark cap**, **headings**, and the **common ceiling on route evaluations**. |
| Section 4.2 | The retained initial route was called “optimal,” and the coordinate-update sentence was incomplete. | **Initial best route**, Gaussian initialization with **2 m standard deviation**, and a **±2 m bound on each coordinate update**. |
| Section 5.1 | The main-test seed range began at **2140**. | **2140000–2140031**. Development remains **2130000–2130007**. |
| Section 5.1 | Map categories changed between “cluttered,” “disorganized,” “disordered,” “rugged” and “rough.” | Use the defined families consistently: **open, cluttered, rough and corridor**. |
| Section 5.1 | Endpoints were retained only when separation was “more than 10 meters.” | Proposals are moved to free grid locations first and retained at a final separation of **at least 10 m**, matching the inclusive implementation. |
| Section 5.2 | The parameter-selection tie rule was an incomplete fragment. | Equal acceptance counts favor lower mean accepted-route score; exact ties retain the default profile. |
| Section 5.3 | A positive score difference was said to make CLRP worse, reversing equation (5). | With δ = 100(Qc − Qv)/Qc, **positive δ favors CLRP** and **negative δ favors the comparison method**. |
| Section 5.3 | “Mean and median are the average map values” did not describe the aggregation correctly. | Average jointly accepted repetitions within each map, then summarize those map averages using their **mean and median**. Bootstrap resampling keeps repetitions grouped by map. |
| Section 5.4 | The diagnostic seed range began at **1670**. | **1670000–1670003**, a separate diagnostic set from the 32 main-test maps. |
| Section 5.4 | Foot contact used a strict distance “less than 0.002 m.” | Contact distance **at most 0.002 m**, matching the detector. |
| Section 5.4 | Actuator “performance” blurred a specific recorded quantity. | **Positive actuator work** retains positive force-times-velocity power, integrates it over time and sums over actuators. Direct body-assistance work is excluded. |
| Section 6.1 | “PSO-C only permits one try” and “CLRP only permits zero tries” suggest total acceptance counts. | **PSO-C alone accepts one paired attempt; CLRP alone accepts none; both reject two.** Overall counts remain 94/96 and 93/96. |
| Section 6.2 | Preparation time of 0.715 s was labeled an average. | **Median 0.715 s**, maximum 0.895 s. The arithmetic mean is approximately 0.720 s and is not substituted for the reported median. |
| Section 6.4 | The map-24 sentence assigned CLRP metrics ambiguously to PSO-C and omitted PSO-C’s corresponding values. | CLRP: **32.959 s, 15.446 percentage points, 1.012 exposure**. PSO-C means: **42.584 s, 20.066 percentage points, 1.665 exposure**. |
| Section 6.5 | Zero assistance was said to meet no requirements at all. | Neither zero-assistance condition **completes a mission within 180 s**. This does not imply failure of every individual planning constraint. |
| Discussion | “PSO-P versus ACO-P” was substituted for two comparisons involving CLRP. | **CLRP versus PSO-P** and **CLRP versus ACO-P**. |
| Discussion | Repetitions were described as diversity between maps, and the study was said not to involve walking. | Repetitions measure **algorithmic variation within a map**. The simulator uses walking mode, but **physical walking and sensor-based navigation are not evaluated**. |
| Conclusions | The reused motion missions were described as an “independent diagnosis.” | A **separate diagnostic**, without implying an independent test sample or hardware validation. |

The revised interpretation retains the limitation supported by the results: the study does **not demonstrate a mean score advantage over PSO-C**. An interval spanning zero establishes neither equality nor inferiority. No hardware, electrical-validation, global-optimality or universal-superiority claims were added.

## Spelling, grammar and terminology

British “s” spellings are valid English. The problem was mixing conventions and substituting words that no longer described the method. V3 consistently uses American English in the narrative and proofing settings. Published reference titles retain their original spelling.

Examples include:

- optimisation → **optimization**; minimising → **minimizing**;
- initialisation/initialised → **initialization/initialized**;
- normalised → **normalized**; localisation → **localization**;
- neighbouring → **neighboring**; behaviour → **behavior**;
- travelled → **traveled**; characterise → **characterize**;
- strategising → **planning** in the keywords;
- pedestrian speed limits → **walking-speed limits**;
- physical support/bodily support → **body assistance**, where referring to the simulator’s velocity corrections.

Sentence fragments, missing punctuation, unit spacing, stray quotation marks, “fulfilll,” and the second-person phrase “your trip” were corrected. The title, author name, email, section order and CLRP method name were retained. The corrections log records 78 edited paragraphs; changes were needed throughout the rewrite to repair terminology and meaning as well as grammar.

## Formatting and references

The reference used is the [IJ3C author instructions and template](https://ij3c.ncut.tw/#authors), checked earlier on the same review date. The manuscript retains A4 pages, two columns, single spacing, 10 pt Times New Roman body text, left-aligned numbered headings, serial equation numbers and captions paired with figures/tables. Mathematical indices and exponents use conventional smaller type.

- Standardized the native ODT equation font settings to Times New Roman. Their mathematical content is unchanged.
- Restored real subscripts and superscripts in explanatory text; the tolerance is 10⁻⁸, not “10 minus 8.”
- Kept Algorithm 1 together in one column.
- Corrected accidental paragraph chains and table breaks; retained table headers and intact rows.
- Removed an empty paragraph producing a literature-section gap.
- Removed the nearly empty eleventh page through corrected prose and pagination. Both editable versions render as **10 pages**.
- Preserved all three figure image binaries, all five tables’ text/numbers and all five native equation contents in the ODT.
- Confirmed that references **[1]–[11]** are cited in first-use order and that all eleven bibliography entries remain present. Their previously verified bibliographic information was retained.

The descriptions of [Smart Gait](https://link.springer.com/article/10.1186/s10033-024-01000-0), [terrain-aware hexapod motion planning](https://www.frontiersin.org/journals/neurorobotics/articles/10.3389/fnbot.2025.1605938/full) and [COCO’s experimental procedure](https://numbbo.github.io/coco-doc/experimental-setup/) were checked against their primary sources. The research descriptions distinguish gait/foothold validation in those studies from the current body-route and assistance diagnostic.

## Verification and remaining author information

Checks against the retained records reproduced the 640 planning-attempt count, the six main-test acceptance totals, all five paired means/medians/bootstrap intervals, map-24 metrics, preparation-time median and all sixteen motion outcomes. The frozen implementation files still match their saved hashes. No live simulation was started and no experimental records were changed.

The original ODT is unchanged. Corrected ODT and DOCX versions were rendered and visually checked page by page. The delivered PDF is exported from the corrected ODT.

**The institutional affiliation is still missing and must be supplied before submission.** The acknowledgment remains deferred as previously requested. These editing and consistency checks do not replace scientific peer review or guarantee acceptance.
