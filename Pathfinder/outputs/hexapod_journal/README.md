# Hexapod manuscript and evidence package

Prepared 28 October 2026 for author and supervisor review. No journal submission or public publication has been made.

## Start here

1. Read `Hexapod_Supervisor_and_Publication_Guide.docx` first for the plain-language explanation, website instructions, scope-based journal shortlist, evidence gaps and next experiment plan.
2. Review `Hexapod_Journal_Manuscript.docx` for the full scientific draft. It contains six figures, three algorithm listings, four native Word equations, six data tables including the appendix, and eleven linked scientific references.
3. Fill actual author details and declarations only after agreeing them with the research team. The current evidence supports a preliminary assisted simulation study, not broad algorithmic superiority, hardware battery savings or unassisted balance.

The rendered manuscript has 15 pages and the supervisor guide has six pages. All pages were visually inspected. Public journal quartiles were not certified; verify the relevant database, subject category and year with your institution.

## Evidence

- `evidence/reliability_v1/manifest.json`: cases and tuning profiles fixed before evaluation.
- `locked_parameters.json` in that directory: selected parameters frozen before testing.
- `development_default.json` and `development_alternative.json`: 48 planning attempts across two profiles.
- `heldout_planning.json`: 108 attempts, comprising 12 layouts, three paired seeds and three methods.
- `heldout_physics.json`: 12 scheduled attempts; nine rejected plans and three completed executions on the same case.
- `evidence/source_snapshots/`: source identities used by all four phases, as referenced by the raw records.
- `source/all_168_trials.csv`: compact attempt table; missing quantities remain empty.
- `source/verified_analysis.json`: independently recomputed summaries, paired differences and measurement scope.
- `source/source_notes.md`: source-access boundaries and publisher guidance.

All three methods admit 9/36 held-out planning attempts. Proposed has small conditional common-score improvements; descriptive intervals include zero. Executed physics measurements tie exactly because the chosen routes and deterministic controller are identical. These results must not be presented as demonstrated overall superiority.

The base terrain is shared. Moved obstacles and different starts/goals do not create independent terrain worlds. Planning predictions are separate from measured physics. Positive actuator work is not electrical battery energy. Rejections are retained in their proper denominators.

## Recompute the paper numbers

From the extracted package root, with Python and NumPy installed:

```bash
python source/analyze_evidence.py --study evidence/reliability_v1 --out analysis
```

This checks archived source hashes, unique trial keys, resource decisions and paired counts. It writes fresh analysis files and does not execute or alter the simulator.

The original frozen study was audited again during manuscript preparation. Reanalysis of the copied package reproduced the same summaries. Analysis and plotting source files are included for inspection.

With NumPy and Matplotlib installed, regenerate figures using:

```bash
python source/make_figures.py
```

The plotting script reads `source/verified_analysis.json` and the raw evidence. Figures are supplied as high-resolution PNG, editable vector SVG and vector PDF. No raster image generator was used. Figure geometry and values come from recorded routes or documented implementation.

With python-docx and the supplied figures, rebuild the Word files using:

```bash
python source/build_documents.py
```

Review rebuilt documents before use: fonts and pagination can differ across word processors. The Word equations are native Office Math, not screenshots of equations.

A full simulation rerun additionally needs the original project, meshes and software dependencies. The package does not redistribute source-paper PDFs or the original robot mesh assets. Resolve model-asset permissions, a full software/environment record and a public archive before a journal submission.

## Journal preparation

The manuscript uses the conventional structure and selected formatting requirements in the Journal of Intelligent & Robotic Systems instructions. Robotica and Industrial Robot are additional scope-based options for discussion. This is not certification of current Q2/Q3 status or a prediction of acceptance.

Human authors must verify and approve the content, contribution, references, authorship, funding and competing-interest statements. AI assistance is disclosed in the manuscript and figure captions. The supervisor guide explains why the present scientific evidence needs strengthening before a strong original-research submission.

`SHA256SUMS.txt` records the identity of files in this package. Accessibility checks found no high- or medium-severity issues; low-level raw-URL notices are retained because explicit reference links were requested.
