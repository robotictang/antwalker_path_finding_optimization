IEEE ACCESS HEXAPOD MANUSCRIPT DRAFT
Prepared 29 October 2026 for Tomato

Title
Resource Constrained Hexapod Path Planning With Visibility Search and Continuous Waypoint Refinement

Open IEEE_Access_Hexapod_V4_Manuscript.pdf for the stable 14-page reading version. Edit IEEE_Access_Hexapod_V4_Manuscript.docx in Word. Both come from the same manuscript. The official IEEE Access Word template controls the page geometry and two-column body. Native Word mathematics, numeric references, algorithm descriptions and measured tables are included.

What is included
- 7 figures, supplied separately as 600 dpi PNG and vector PDF.
- 9 native tables, also exported as CSV.
- 10 numbered equations and 2 pseudocode algorithms.
- 20 references with internal citation navigation and external source links where available.
- Frozen 1,232-attempt evidence across development, primary planning, feature removal, budget sensitivity and assisted physics. The primary independent test sample is 24 worlds.
- Source manuscript text, plotting and construction scripts, independent calculations and QA records.
- Supplementary Evidence S1 archive containing raw records, source snapshots, model assets, settings and audit. No new neural-network training was performed for this paper.

Read first
The Abstract gives the scope and central outcome. Section IV explains V4. Tables IV to VI show the main comparison. Figure 5 shows saved side-by-side routes, including a V4 loss. Section VI reports feature removal, runtime, budget and physics results. Section VII explains limitations. The existing V3 Word report remains an earlier document and is not the source of the new V4 numerical claims.

Before submission
Confirm the publication name Tomato and supply affiliation, email, author biography, ORCID, funding and conflict declarations. Add a persistent accessible repository location to Data and Code Availability. The paper reports limited simulation evidence; assisted body control, nominal battery coefficients, small physics coverage and uncertain gains over polished ACO remain material limitations. Discuss novelty and validation with the supervisor and approve every claim and reference. The draft has not been submitted, accepted or assigned a DOI.

IEEE Access currently requests source plus matching PDF in its two-column template and specifies AI-content disclosure. An explicit acknowledgment identifies the assistance used in this work. Verify requirements at submission:
https://ieeeaccess.ieee.org/authors/submission-guidelines/
https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/

Reference checks
Relevant publisher, author and project sources were consulted. Crossref verified metadata for six DOI records; six additional registry requests were rate-limited. This does not represent a full-text review of every cited paper. The delivery-planning paper was accessible only as publisher abstract/introduction and is labeled accordingly. Source links are provided for human review.

Reproduction of paper calculations and figures
Install compatible python-docx, lxml, numpy, matplotlib and Pillow. From the package root, run:
python source/analyze_and_plot.py
python source/build_manuscript.py
These scripts prefer the packaged evidence/advanced_study_v4 JSON files and do not run the physics study. Figure files will be regenerated from saved records. Word source creation uses the retained template in template/. PDF creation needs a compatible Word/LibreOffice installation. source/render_paper.py records the renderer workaround used on the original machine and depends on its installed Documents skill path.

For scientific experiment reproduction, read the REPRODUCTION.txt inside S1_Simulation_Evidence.zip. Its original model/source hashes are preserved. Relocating asset references must be done in a separate copy with new hashes. Never replace the old held-out observations with retuned results.

Verification scope
All 14 final pages were visually inspected; unchanged pages were confirmed by exact image hashes against the reviewed render. Citation anchors and source relationships were checked. Paper statistics were independently recomputed from JSON. The campaign audit passed with no errors or warnings, and an accessibility check found no issues. The comparison website's served snapshot hash and dataset were checked; browser interaction testing was unavailable. These are internal checks, not independent peer replication or physical-robot validation.
