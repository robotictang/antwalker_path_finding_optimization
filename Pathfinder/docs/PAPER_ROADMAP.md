# Continuing the scientific paper

**4 November update:** The [IJ3C revision](../publication_2026_11_04/README.md) and [readiness assessment](../publication_2026_11_04/READINESS.md) supersede this guide for current results and publication status. The text below preserves the 3 November handoff context; manuscript links refer to the previous IEEE draft.

Start from the [current Word draft](../paper/previous_ieee_manuscript.docx) and [19-page PDF](../paper/previous_ieee_manuscript.pdf). The immediate task is to verify the contribution with your supervisor and decide which evidence needs strengthening. The remaining work is scientific positioning, validation and authorship, not simply adding pages. No manuscript text was changed during this handoff.

## Agree the scope

The present framing is an evaluated resource-constrained planning and assisted-execution pipeline for a simulated hexapod. Its useful features include common mission constraints, collision-checked refinement, representation controls, preserved negative results and traceable evidence. The stronger swarm comparisons show small gains and many ties. Landmark diversification was not consistently beneficial on the reported ablation subset. Let these facts shape the contribution statement.

Real battery savings, dynamically stable walking or hardware autonomy require additional evidence. Treat that as a scope decision. The IEEE Access template identifies a draft target; it does not prove journal fit or acceptance prospects. Current journal requirements and reference accuracy were not externally audited during this handoff.

## Verify before editing

1. Read the [project guide](PROJECT_GUIDE.md) and current PDF. Mark claims you cannot explain in your own words.
2. Review the [verification notes](verification/README.md), raw V6 JSON and saved tables.
3. Trace a success, a rejection and a proposal loss. Explain the constraints and Q ranking.
4. Read the closest original papers and check the baseline implementations against their claimed scope. The existing notes disclose only a partial review of the delivery-planning paper.
5. Meet your supervisor with the counts, limitations and a proposed contribution sentence. Agree the scope and author responsibilities before another enhancement.

You are ready to revise when you can explain the planner, evaluator, data splits, assistance and statistics without relying on the draft's phrasing.

## Review the draft by section

| Portion | What to check |
|---|---|
| Title and Abstract | Match the agreed contribution; distinguish V4 optimizer from V6 protocol; preserve conditional wording. |
| I–II | Establish a specific gap against the closest comparable work; verify original sources. |
| III | Explain units, assumptions, return reserve, known-map scope and proxies. |
| IV | Separate established techniques from the integration contribution; trace pseudocode to code. |
| V–VI | Clearly label S1; preserve losses, ties, failures and limited ablation evidence. |
| VII | Retain the negative V5 enhancement result. |
| VIII | Make S3 the latest evaluation; explain the OMPL internal-cost and common-incumbent limitations. |
| IX–X | Discuss practical effect size and runtime; keep physical claims within the evidence. |
| Availability and declarations | Confirm authors, affiliation, email, funding, conflicts and an accessible versioned evidence archive. |

The article carries much of the original S1 narrative before adding S2/S3. A revision could make this relationship clearer with a common protocol overview and consistent names. Decide with the supervisor which campaign carries the main claim before restructuring the article.

## Choose experiments that resolve a specific gap

For a simulation paper, stronger controls could give the native planner a heading-state objective or give swarm methods unrestricted continuous waypoint representations. These address whether gains depend on representation and adapter choices. If landmarks are central to the contribution, test their benefit across broader independent map sources.

For physical relevance, first obtain a dynamically actuated controller without chassis velocity overwrites, then validate locomotion and record genuine synchronized voltage/current and mission measurements. Use disjoint calibration and validation maps/missions. The [existing electrical protocol](../paper/electrical_validation/MEASUREMENT_PROTOCOL.md) is a workflow, not completed validation or a sample-size justification.

Before testing, specify the question, practical effect threshold, independent map unit, failures, development process, profile selection and computational allowance. Select sample size from variability, desired precision, runtime and the intended claim with supervisory/statistical input. More repeated seeds alone do not add independent maps.

## Keep new evidence separate

Use `workbench/` for learning and edits. Preserve S1/S2/S3 code, manifests and records. Once you use a test outcome to design a change, those maps become development material for that change. New confirmation needs new seeds and a new protocol.

`research.final_study --directory NEW_DIRECTORY` repeats the existing V6 protocol and seeds in a separate location. It is useful for reproduction, but is not a new held-out study of an improved algorithm. A method change needs a versioned study definition and source/settings freeze.

Keep admission separate from execution success. Include all scheduled attempts in the relevant denominators. Compare Q on jointly admitted pairs while reporting other categories. Average repeats within worlds for uncertainty calculations, and do not compare scores across different objective weights as though the score were unchanged.

## Prepare authorship and submission

Confirm who did and can take responsibility for each contribution. `TOMATO` is a placeholder, not an instruction to assign authorship. Agree author order, institution, corresponding email, funding, conflicts, biography and any required identifiers. Verify citations and permissions, retain accurate AI disclosures, and check the current target journal requirements when preparing submission.

Keep a dated revision log linking manuscript changes to data and analysis versions. Share a submission package only after the supervisor approves the claims and author information.

| Next session | Concrete output |
|---|---|
| Orientation | One-page explanation of question, pipeline and strongest limitation |
| Evidence walkthrough | Three annotated trials and one table traced to JSON |
| Supervisor discussion | Agreed contribution, responsibilities and validation scope |
| Reproduction | Check logs and a controlled fresh run labelled reproduction |
| Study design | New written protocol addressing one agreed scientific gap |
| Revision | Updated narrative and claims tied to the selected frozen evidence |
