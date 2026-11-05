# Reorganization and preservation record

Prepared on 3 November 2026. The request was to understand the senior's work, make the folder navigable, and prepare the newcomer to continue the draft.

## What changed

The root README now identifies the research question, current paper, code workspace and next steps. Its original bytes are retained in `docs/legacy_guides/ORIGINAL_ROOT_README.md`.

`paper/` collects relative links to the latest DOCX/PDF, analysis source, tables, figures, frozen evidence, offline comparison, electrical protocol and ZIP. `archive/` gives ordered links to earlier report families and demo backups. `docs/` contains the research explanation, paper roadmap, file map, legacy-guide links and verification records. These navigation links do not copy or move the original drafts or data.

`workbench/` is a separate 75 MB portable reproduction copy, so changes for learning or future experiments cannot overwrite original scientific sources. It comes from the existing final package, whose scene already has documented path-only relocation. During the handoff a complete planning command exposed a NumPy JSON serialization failure that the 50 existing unit tests missed. The workbench's `mujoco/research/run.py` now converts NumPy scalars/arrays at the JSON persistence boundary while preserving rejection of nonfinite numbers. Two focused regression tests were added in `test_handoff_persistence.py`. The original `mujoco/research/run.py` and frozen evidence were not changed.

Three `tools/` scripts provide evidence reconciliation, a V6 internal audit with temporary in-memory asset relocation, and original-file/navigation verification. They write reports beneath `docs/verification/`. The audit helper leaves the frozen audit report unchanged.

## Why the original layout remains

The directory initially occupied approximately 1.4 GB and included over ten thousand files: multiple manuscript generations, packaged copies of evidence, native dependencies, render assets and demo history. Source locks, checksum manifests, script-relative roots and legacy absolute paths tie this material together. Moving those folders into a new physical hierarchy would risk breaking provenance or old builders. The handoff therefore organizes access through curated paper/archive links and a separate runnable workbench.

No original scientific file, manuscript, mesh, saved run or package was deleted or moved. Test/audit imports regenerated one pre-existing Python cache; its original bytes were restored from the backup before preservation verification. Newly generated caches are ordinary runtime artifacts. No Git commit, branch change or push was made. The initial Git status listed Pathfinder as untracked; this handoff did not establish who created the local folder or how it reached the checkout.

## Backup and undo

The pre-handoff snapshot is `/home/user123456/Desktop/Pathfinder_handoff_backup_2026-11-03/Pathfinder`. Its inventory is `/home/user123456/Desktop/Pathfinder_handoff_backup_2026-11-03/original_inventory.json`, with 10,659 original file records. The backup occupies additional disk space and was deliberately retained.

To recover the old entry point, copy `docs/legacy_guides/ORIGINAL_ROOT_README.md` over the root README. The new handoff directories can be removed separately if no later work has been saved in them. Do not blindly replace the entire folder with the snapshot after beginning new research; first preserve subsequent changes. The old file locations remain available, so no path migration needs to be reversed.

## What did not happen

The manuscript was not rewritten, the original experiments were not rerun to generate new performance evidence, and no hardware or electrical data were fabricated or collected. The one-record smoke run is an explicitly separate workbench check. The live demo, dashboard interactions, document rebuild/render pipeline and journal/reference requirements were not fully validated. See [verification notes](verification/README.md) for the exact checks and limits.
