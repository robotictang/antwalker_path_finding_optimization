# Handoff verification

Checks performed locally on 3 November 2026. Saved original verification reports are useful historical records; the following checks were actually repeated for this handoff. No new manuscript-performance campaign was run.

| Check | Result and interpretation |
|---|---|
| Original source tests | 48/50 passed; two errors were missing assets under the old Downloads path. No failing scientific assertion was reported. |
| Portable-copy tests before persistence fix | All 50 existing tests passed. |
| Complete planning smoke command | Initially found a route but failed final JSON serialization of a NumPy float32. Initial failure log retained. Fixed only in the workbench and rerun; see the final logs below. |
| Final workbench tests | All 52 passed: 50 existing checks plus two persistence regressions; see `workbench_tests.log`. |
| Final package hashes | 1,027 payloads checked against its SHA256SUMS.json; no mismatches. |
| V6 record reconciliation | 1,200 unique scheduled trial keys across 12 phases; CSV and JSON keys agree. |
| Final primary arithmetic | Six admission counts, mean planning times and world-averaged paired improvements independently recalculated from saved JSON; paired means match CSV. |
| Existing V6 audit rerun | Passed: 1,200 records, 298 distinct routes collision-checked, 1,192 metric values recomputed, 95 physics execution records checked; no errors or warnings. This reconstructs geometry, not fresh physical executions. |
| Original-file preservation | All 10,659 original file records preserved, with original README saved separately; see `preservation.json`. A pre-existing broken documentation symlink inside an archived rendering runtime is recorded separately from the new navigation links. |
| Document inspection | Extracted current DOCX and source narrative, inspected matching PDF metadata and rendered first page; verified 19-page count and author placeholders. No new all-page layout certification. |

## Reports

- [evidence_inventory.json](evidence_inventory.json): package hashes, phase counts, independently recalculated admissions/times/paired means.
- [frozen_v6_audit.json](frozen_v6_audit.json) and [log](frozen_v6_audit.log): repeated original auditor with 14 path references relocated in memory; original on-disk source/model hashes remain authoritative.
- [workbench_tests.log](workbench_tests.log): final software test run.
- [workbench_smoke.log](workbench_smoke.log): final one-record end-to-end planning command.
- [workbench_smoke_initial_failure.log](workbench_smoke_initial_failure.log): initial persistence failure, retained for transparency.
- [preservation.json](preservation.json): original-byte and handoff-navigation checks.

## Repeat the checks

From Pathfinder:

```bash
python3 tools/inspect_evidence.py
python3 -B tools/audit_frozen_study.py
python3 tools/verify_handoff.py
```

The tools write their own reports in this directory. `-B` suppresses Python cache writes during the frozen audit. The audit uses the existing scientific auditor with path-only in-memory XML relocation; it is not an independent reimplementation of its geometry calculations. Its own score/provenance checks and the separate handoff arithmetic reconciliation provide different checks on the same saved observations.

For tests and a learning command, see [the workbench guide](../../workbench/README.md). Test outcomes do not validate hardware, novelty, journal suitability or the statistical power of the research. The full dashboard browser workflow, fresh 1,200-record reproduction, Word rebuilding, complete PDF layout, real electrical calibration and hardware execution were not run during this handoff.
