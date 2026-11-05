# File map and evidence trace

Paths below are relative to Pathfinder. Original locations are retained because scripts, source locks, relative imports and generated packages depend on them. The organized `paper/` and `archive/` links provide shorter entry points. Use `workbench/` when editing or running code.

## Manuscript and analysis

| Location | Purpose |
|---|---|
| [paper/current_manuscript.docx](../paper/current_manuscript.docx) | Latest review draft, linked to `outputs/ieee_access_final/IEEE_Access_Hexapod_Final_Manuscript.docx` |
| [paper/current_manuscript.pdf](../paper/current_manuscript.pdf) | Matching 19-page reading copy in the final package |
| [source/manuscript.md](../outputs/ieee_access_final/source/manuscript.md) | Builder input with equation/table/figure markers; not a fully rendered article |
| [source/analyze_final.py](../outputs/ieee_access_final/source/analyze_final.py) | Reads saved JSON, computes comparisons, writes tables/figures/analysis |
| [source/build_manuscript.py](../outputs/ieee_access_final/source/build_manuscript.py) | Builds Word from narrative, generated material and template |
| [source/final_analysis.json](../outputs/ieee_access_final/source/final_analysis.json) | Saved detailed final analysis, including paired effects and regimes |
| [source/check_manuscript.py](../outputs/ieee_access_final/source/check_manuscript.py) | Existing structural/quantitative DOCX and CSV checks; writes QA output |
| [package/](../outputs/ieee_access_final/package/) | Frozen portable delivery with DOCX/PDF, evidence, code, tables and checksums |
| [paper/offline_comparison.html](../paper/offline_comparison.html) | Portable visualization of the final 576 primary records |

## Scientific code

The following files exist beneath both the original `mujoco/` and the portable `workbench/mujoco/`. Use the workbench copy for future changes.

| File | Question it answers |
|---|---|
| `research/run.py` | How are cases, planner calls, results and execution organized? |
| `research/worlds.py` | How are procedural worlds sampled and connected to physics/terrain queries? |
| `safe_navigation.py` | How does footprint clearance and conservative grid navigation work? |
| `research/planning.py` | How are graph metrics, constraints and planner dispatch defined? |
| `research/swarm.py` | How do the shared score, ranking, PSO, ACO and initial refiner work? |
| `research/advanced.py` | What does the retained V4 optimizer do? |
| `research/adaptive.py` | What was the V5 enhancement candidate? |
| `research/external_planners.py` | How are the actual OMPL controls adapted and timed? |
| `research/final_study.py` | Which cases, profiles, phases and seeds define V6? |
| `research/execution.py` and `tracking.py` | How are routes followed and assistance applied? |
| `research/telemetry.py` | How are mechanical work and contact/tilt diagnostics measured? |
| `energy_model.py` | Which battery coefficients are assumed? |
| `research/electrical_logging.py` and `calibration.py` | How would real electrical data be integrated and fitted? |
| `research/audit_final.py` | Which internal consistency and geometry checks are performed? |

The interactive demo uses `preview_multi_place_mission.py`, `destination_routing.py`, `mission_control.py`, `hybrid_locomotion.py`, `tripod_gait.py` and `mission_history.py`. It is useful background but is not the primary statistical experiment. `research_dashboard/` is an existing generated web app with its own AGENTS.md restrictions. No dashboard code was edited in this handoff.

## Trace a claim to its evidence

For the statement “V4 admitted 90/96 final primary attempts”:

1. Open [v6_primary.json](../mujoco/outputs/research/final_validation_v6/v6_primary.json).
2. Filter its `records` to `method == "proposed_v4"`. There are 96 records across 48 `case_id` values and two `repeat` values.
3. Count `plan.admissible == true`: 90. Do not use the top-level `success` field as a planning-admission flag; planning-only records have no executed mission success.
4. Compare with [Final_Primary_Summary.csv](../paper/previous_ieee_tables/Final_Primary_Summary.csv).
5. For a score comparison, pair records by `(case_id, repeat)`, keep jointly admitted pairs, calculate `100 × (baseline_Q − proposal_Q) / baseline_Q`, average repetitions within worlds, then average worlds.

The [manifest](../mujoco/outputs/research/final_validation_v6/manifest.json) defines cases/protocol. [locked_parameters.json](../mujoco/outputs/research/final_validation_v6/locked_parameters.json) records selected settings. [source_lock.json](../mujoco/outputs/research/final_validation_v6/source_lock.json) identifies scientific sources. Per-run `source_snapshot` and case `model_xml` fields locate archived source/model bytes beneath `mujoco/outputs/research/`.

`v6_physics_safe.json`, `v6_physics_legacy.json` and `v6_physics_reduced.json` contain execution records and `prediction_validation` residuals. They replay subsets of existing primary routes, not new independent worlds. CSV rows are convenient flattened summaries; JSON retains routes, constraints, settings and traces.

## Historical and generated material

Use [archive/README.md](../archive/README.md) for older studies. `mujoco/backups/` holds engineering snapshots. `mujoco/outputs/` mixes demo logs, images, mission-history databases and research results. `outputs/` holds manuscript generations, copied evidence/packages, render QA and authoring dependencies. Large repeated files are often packaged evidence copies, not additional experiments.

Do not begin by deleting apparent duplicates. Package checksums and old builders depend on them. The handoff's checks verify the final package byte-for-byte; they do not certify every historical report. `__pycache__/` is generated Python cache, not scientific evidence. The original README and older student guide are available in [legacy guides](legacy_guides/).
