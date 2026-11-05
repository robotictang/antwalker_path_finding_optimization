# IJ3C ten page manuscript revision

The revised article is exactly 10 rendered pages, with expanded methods, family-specific admission counts, computation accounting, individual-world score effects and omission sensitivity, and replay/contact telemetry. It contains 5 figures, 8 tables, 3 native equations and 9 references. The unchanged frozen planning campaign contains 640 records.

- [PDF manuscript](IJ3C_Manuscript.pdf)
- [Editable Word manuscript](IJ3C_Manuscript.docx)
- [Submission audit](Submission_Audit.md)
- [Evidence map](Evidence_Map.md)
- [Narrative source](IJ3C_Manuscript.md)
- [Raw planning campaign](raw_study/)
- [Derived results](results/)
- [Deferred disclosure for supervisor consultation](Deferred_Disclosure.md)

The AI acknowledgment has been removed from the manuscript at the user's request; its wording is retained separately for later placement. Author/contact fields remain unfilled as requested. No journal submission has been made. The six-page revision is preserved in [the preceding revision](../publication_2026_11_04_format_review/README.md).

## Diagnostic correction

The earlier diagnostic requested gravity compensation removal before locomotion initialization, which restored 18 compensated limb bodies. Its four mislabeled records are preserved and excluded from the no-compensation comparison. Four corrected replays disable compensation after initialization and record realized values. The paper compares 12 valid original executions plus these 4 corrected executions; 20 execution records are retained in total. All corrected replays time out at 180 simulated seconds. See [the correction record](results/Diagnostic_Correction.md).

## Reproduction of the expanded report

The new post-hoc analysis is in source/extended_content.py and is independently reconciled by source/check_extended_analysis.py. Existing scientific sources and raw planning records remain frozen. The original diagnostic script is retained as source/legacy/realism_probe_initial.py for provenance; it is not an execution entry point. Use source/corrected_gravity_probe.py for the corrected four-run diagnostic.

The authoring builder requires python-docx, NumPy and Matplotlib with locally installed Times New Roman. Rendering uses the bundled LibreOffice runtime and an isolated compatibility loader and Math profile. All ten final pages were inspected; font embedding, page numbers, geometry and absence of the acknowledgment were checked. Rendering and formatting checks are separate from scientific author approval.
