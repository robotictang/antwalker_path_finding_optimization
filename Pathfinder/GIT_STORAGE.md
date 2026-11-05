# Pathfinder Git storage cleanup

The rejected November 2026 push included repeated ZIP handoffs, intermediate document renders and locally installed rendering libraries. These generated files remain on this workstation but are excluded from Git by the Pathfinder-specific `.gitignore`.

The final Word/PDF manuscripts, publication figures, source code, meshes, robot descriptions, raw study records, frozen source snapshots and numerical audit reports remain versioned. The historical S1 evidence archives and the trained navigation model ZIPs also remain versioned; the cleanup does not apply a blanket ZIP exclusion.

## Local generated material

- `publication_*/IJ3C_Review_Bundle.zip`, plus the large final/validation handoff ZIPs under `outputs/`, duplicate their unpacked source material.
- Page images, intermediate PDFs and working DOCX copies beneath `qa/` are rendering intermediates. Final manuscript documents and figures outside `qa/` remain tracked.
- `outputs/word_guide_deps/`, `outputs/hexapod_journal/deps/`, the compatibility loader libraries and font caches are workstation dependencies, rather than research code or experimental inputs.
- `paper/review_package.zip` is a local convenience link to the generated review bundle. It is intentionally absent from a fresh clone.
- The two `workbench/mujoco/outputs/*_demo_history.sqlite3` databases are mutable local demo state. They and their SQLite sidecars stay local. Experiment/validation history databases are retained in Git.

The manuscript-generation and packaging scripts remain under each publication revision's `source/` directory. The current packaging entry point is `publication_2026_11_04_robot_figure/source/package_review.py`. Document rendering requires the recorded local runtime and fonts; this cleanup does not turn that workstation-specific rendering setup into a portable installation.

## Recovery

The original unpublished commit is preserved in local branch `backup/pathfinder-before-storage-cleanup-20261105`. A verified incremental Git bundle and a per-file cleanup inventory are stored outside the repository at `/home/user123456/Desktop/Pathfinder_git_cleanup_backup_2026-11-05/`. The bundle records its required parent commit, which remains in the repository history. These are local recovery copies and should not be pushed with `git push --all`.

No local manuscript, evidence or generated file was deleted. Only Git tracking was removed for the listed generated material. The unpublished `Add pathfinder` commit was amended so excluded blobs are absent from the ancestry sent by a normal push of `main`; adding a later deletion commit would still transmit them.

This reduces the new transfer but cannot establish how much GitLab project storage remains. No push or remote-history rewrite is part of this cleanup.
