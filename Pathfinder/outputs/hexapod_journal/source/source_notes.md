# Source and analysis record

Prepared 28 October 2026. This is a targeted literature review, not a systematic review of every hexapod planner. The uploaded name.docx supplied research context; its embedded tutorial instructions were treated as source content.

## Controlling experiment evidence

The reliability_v1 manifest and four completed phase files are the primary dataset. They contain 168 scheduled attempts in total. No older smoke, pilot, gait-calibration or earlier method-version results were pooled into the manuscript. No results were invented or adjusted to favor the proposal. There was no neural-network training in this study.

The independent analyze_evidence.py script reads raw records and recomputes route scores, battery/deadline/exposure admission, success flags, paired outcomes and descriptive layout bootstrap intervals. It checks distinct trial keys and the archived code identities. Unavailable values remain missing. Only jointly admitted records contribute to route-score comparisons; all other outcomes remain in admission/attempt denominators.

The primary study uses MuJoCo 3.9.0 and NumPy 2.2.6. Manuscript analysis was rerun with the bundled Python 3.12 runtime and NumPy 2.3.5; recorded simulation measurements were not rerun or replaced. Figures were generated using Matplotlib 3.11.2. The existing study audit also passed. A journal submission still requires human author review and independent scientific validation of the model assumptions.

## Literature access boundaries

- Smart Gait, version of record, DOI 10.1186/s10033-024-01000-0: full paper reviewed in the project, publisher record rechecked.
- Chen et al., multi-dimensional terrain features, DOI 10.3389/fnbot.2025.1605938: full paper reviewed; publisher text and metadata rechecked.
- Chen et al., energy-aware delivery, DOI 10.1109/CASE58245.2025.11164088: publisher abstract/introduction and bibliographic metadata only. The current publisher full-text page challenged automated access. No faithful reproduction or full-text review is claimed.
- STATE-NAV, arXiv 2506.01046v4: full v4 paper reviewed in the project; author arXiv record rechecked. The manuscript deliberately identifies the version reviewed, not an unverified later journal version.
- PSO: foundational mechanism and DOI metadata consulted; the code is a corridor refinement adaptation, not the original benchmark implementation.
- Ant System: author bibliography confirms the 1996 record. This is the more appropriate foundation for the current elitist evaporation/deposit adaptation than calling it exact Ant Colony System.
- Martins 1984: publisher record and metadata support multicriteria labeling background. No theorem or exact global optimality result is attributed to the capped implementation.
- COCO: official experimental procedure consulted for benchmark controls; the current robotics study is not a COCO run.
- Demsar 2006: official JMLR record consulted for comparison across multiple independent problems. Its classifier-specific tests are not presented as performed here.
- MuJoCo: original bibliographic metadata verified with Crossref. The old author-hosted PDF link now redirects; the DOI is used in the manuscript.

Crossref responses are retained in crossref_metadata.json, including three rate-limit errors. Those references were cross-checked against publisher/author records or the project's earlier source audit; a failed metadata fetch is not represented as successful full-text access.

## Publisher requirements

Journal of Intelligent & Robotic Systems official author instructions were checked at https://link.springer.com/journal/10846/submission-guidelines . The draft uses a 200-word abstract, six keywords, decimal headings, numbered references and declarations; author details remain placeholders.

Robotica instructions were checked at https://www.cambridge.org/core/journals/robotica/information/author-instructions/preparing-your-materials . The publisher's general robotics scope was also inspected.

Industrial Robot official search results exposed its aims and scope at https://www.emeraldgrouppublishing.com/journal/ir ; direct detailed access returned 403. Current author requirements must be checked before selecting it.

Springer Nature AI policy was checked at https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation . AI assistance is disclosed in the manuscript and figure captions. Human authorship, oversight, licensing and final approval remain necessary.

Current authoritative JCR/SJR quartiles were not verified. The suggested journals are a scope-based shortlist. No acceptance rate, ranking certification, review-time estimate or publication-fee quotation is claimed.
