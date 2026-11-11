# IJ3C simulation study revision

Prepared 4 November 2026. This revision strengthens the evidence and narrows the claims to simulation, as requested. The user confirmed that only simulation files are available and asked to leave author details pending. Nothing has been submitted or published.

Read [the revised manuscript](IJ3C_Hexapod_Review_Draft.docx), [its Markdown source](IJ3C_Manuscript.md), and [the readiness assessment](READINESS.md). The matching PDF is a reading copy of the same draft. Original S1-S3 evidence and the earlier IEEE-formatted manuscript remain unchanged.

## What was improved

The workbench now includes a continuous-coordinate PSO representation control, rather than comparing only refinements of fixed corridor subsequences. A locally frozen prospective campaign used eight development worlds, 32 new primary worlds, six configurations and three primary repetitions, with 640 total planning records. Two development profiles were offered equally to the four base configurations; component removals inherited the selected V4 profile. All records and unfavorable outcomes were retained.

The independent analysis module reconciles trial keys, settings, source/model hashes, collision geometry, metric arithmetic and development selection. It passed all 640 records, checked 187 distinct routes and recomputed 748 metric values. The software log contains 63 passing test executions, including imported existing cases and three new representation checks.

The new result is nuanced: V4 admits 93/96 primary attempts and continuous-coordinate PSO admits 94/96. V4's mean paired score effect against that control is 0.690%, median 0%, with descriptive 95% whole-world interval [-0.255%, 2.312%]. This does not establish a reliable nonzero mean score advantage. Mean effects against landmark and polishing removal are 0.924% and 0.794% respectively, conditional on joint admission. See [all comparisons](results/paired_comparisons.csv) for ties, losses, admission categories and ranges.

A model audit identifies a source URDF mass of 97.52 kg versus a compiled MuJoCo assembly mass of about 113.32 kg; the chassis changes from 35 to 46 kg. A separate 16-execution diagnostic on four already observed V6 routes found 4/4 arrivals under full assistance, 4/4 under reduced blending, and 0/4 under zero chassis assistance, both with and without limb gravity compensation. Those zero-assistance runs timed out; they were not automatically classified as falls. These diagnostic routes are not fresh held-out locomotion evidence.

The paper is rewritten as a focused comparison and fidelity-boundary study. It uses the journal's stated A4/two-column/minimum-10-pt format, a short abstract, five keywords, numbered references, three figures, four tables and two native Word equations. The downloaded legacy sample's corrupted character spacing, blank title page and old publication metadata were replaced with clean author-guide-compliant formatting. The official files are retained under `template/`.

## Find the evidence

| File or folder | Purpose |
|---|---|
| [results/study_analysis.json](results/study_analysis.json) | Audit outcome and all main statistics |
| [results/all_640_attempts.csv](results/all_640_attempts.csv) | Every scheduled new planning attempt |
| [results/paired_comparisons.csv](results/paired_comparisons.csv) | Paired effects, intervals and admission categories |
| [results/world_effects.csv](results/world_effects.csv) | World-level effects, including ties/losses |
| [results/realism_probe.json](results/realism_probe.json) | All 16 assistance diagnostic executions |
| [results/model_audit.json](results/model_audit.json) | Actual source and compiled model specifications |
| [raw_study/](raw_study/) | Manifest, frozen profiles, source lock and full phase JSON |
| [source/](source/) | Analysis, diagnostic, manuscript and render scripts |
| [qa/](qa/) | Software tests, study audit, rendering and build reports |

## See pathfinding in action

Open [Live Pathfinder](http://127.0.0.1:8784/). This displays live MuJoCo frames beside the existing mission-control panel. Select a destination, compare Shortest/Fastest/Lowest energy/Balanced, and watch the robot/route. A task can be rejected when its modeled destination-plus-return requirement exceeds the battery; that rejection is intentional. The native viewer closed immediately on this host, so the new display wrapper supplies a browser renderer without changing the planner or controller equations.

To restart it from Pathfinder:

```bash
DISPLAY=:1 python3 tools/live_pathfinder.py
```

The browser-rendered mission is the existing assisted **hybrid demo**, not a live run of the controlled walking-only S4 benchmark. Its original mission-control HTML was missing from the reproduction package and was restored from the unchanged original. The portable asset helper now resolves local workbench assets, and a workbench URDF copy removes invalid XML comments only. These portability changes do not validate the physical model.

## Reproduction

The new raw study is in `../workbench/mujoco/outputs/research/publication_ij3c_20261104/`. Its per-phase `source_snapshot` and per-case `model_xml` entries locate frozen artifacts under the same `outputs/research/` root. Preserve these bytes. The review ZIP includes the runtime copy and snapshots needed for inspection.

From `workbench/mujoco`, `python3 -m research.publication_study` checks the freeze and loads completed phases; it does not add independent evidence. To test changed code, define a new protocol/version and new seeds. Rerunning a completed directory or renaming it does not create a new independent test. The scientific runtime remains the inherited Python 3.10/Linux/MuJoCo 3.9/NumPy 2.2.6/SciPy 1.15.3 configuration.

From Pathfinder, `python3 publication_2026_11_04/source/analyze_study.py` repeats the internal audit/analysis. `source/realism_probe.py` replays the diagnostic's saved S3 input; it is not a hardware test. Document generation uses the bundled authoring Python with the packages listed in `source/authoring-requirements.txt`. On this host, Matplotlib was added under `/tmp/pathfinder_plot_deps`; no global environment was changed. The packaged renderer uses an explicit system LibreOffice/Poppler compatibility override because the bundled binaries require newer GLIBC/GLIBCXX versions. Rendering does not resave the final DOCX.

The software was run on a shared desktop, with background simulation/authoring workloads. Per-method wall timing and finite-budget search are workload-dependent. The locally frozen analysis is descriptive, not externally preregistered or multiplicity-adjusted. Only four related procedural families are covered. These limitations remain in the manuscript.

## Review bundle boundaries

`IJ3C_Review_Bundle.zip` unpacks into `publication_2026_11_04/`, `workbench/`, `tools/`, the original `hexapod.urdf` and historical manifest inputs. It includes the new raw phases, frozen source snapshots, generated model files and local runtime assets. `payload_sha256.json` inventories every payload; `qa/package_check.json` beside the ZIP reports archive, source and model integrity checks. That report is intentionally external to the archive because it contains the ZIP checksum. Historical S1-S3 packages remain in the original project and are not fully duplicated in this ZIP; the diagnostic's exact S3 input is included separately.

Frozen generated XML contains absolute paths from the study machine and is retained unchanged for hash verification. The analysis reconstructs worlds from their saved specifications using the local runtime assets. Directly opening an archived XML after relocating the ZIP requires a separately documented asset-path adaptation; never rewrite the frozen originals. The bundled Linux/CPython 3.10 OMPL library and authoring tools impose environment requirements. This is an inspectable reproduction bundle, not a verified universal installer or clean-environment replication.

For manuscript edits, change `source/article.md`, then use an authoring Python with `source/authoring-requirements.txt` installed to run `source/build_manuscript.py`. On this host the command is:

```bash
PYTHONPATH=/tmp/pathfinder_plot_deps /home/user123456/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 publication_2026_11_04/source/build_manuscript.py
```

Then run `source/check_manuscript.py` with that Python, render with `source/render_manuscript.py`, inspect every rendered page, and copy the matching rendered PDF into the revision folder. The renderer override names this host's installed skill and system tools; adapt it explicitly on another machine. Finally, `python3 publication_2026_11_04/source/package_review.py` refreshes the ZIP and checksums. Manual DOCX edits are not synchronized back to Markdown.
