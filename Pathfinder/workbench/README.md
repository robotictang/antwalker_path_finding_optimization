# 4 November 2026 update

The [IJ3C revision](../publication_2026_11_04/README.md) adds a frozen 640-record campaign, coordinate PSO control and representation checks. Current scientific code is locked by that campaign: use a new protocol/version before changing it. The latest test log has 63 passing executions, including imported existing cases and three new representation checks. The [live browser demo](http://127.0.0.1:8784/) was verified through a completed Marsh trip. Start it from Pathfinder with `DISPLAY=:1 python3 tools/live_pathfinder.py`. It is the assisted hybrid demo, distinct from the walking-only planning study. Portable URDF/asset resolution and restored mission-control HTML are documented with the revision.

The dated handoff notes below describe the earlier state and its verification scope.

# Portable scientific workbench

This is an independent copy of `outputs/ieee_access_final/package/reproduction`, created for the handoff on 3 November 2026. Its scene already contains the documented asset-path relocation from the senior's missing Downloads folder. Original sources and saved evidence remain outside this directory.

All 50 existing software tests and two added persistence regression tests pass here (52 total). An end-to-end planning run exposed NumPy values that the original JSON writer could not save. Only this workbench now converts those values at the persistence boundary; the scientific planner and the original frozen code are unchanged. This validates tested software behavior, not robot performance. The tested local scientific runtime is Python 3.10.12, MuJoCo 3.9.0, NumPy 2.2.6, SciPy 1.15.3 and the bundled OMPL 2.0.1 CPython 3.10 Linux library. See [REPRODUCE.txt](REPRODUCE.txt) and [requirements-pinned.txt](requirements-pinned.txt) for the inherited environment instructions. Native OMPL uses Linux process forking; the bundled binaries are not platform-independent. No package installation was made in this handoff.

## Start with tests

```bash
cd "/home/user123456/Desktop/Git/antwalker/Foo Jin Wayne/Pathfinder/workbench/mujoco"
python3 -m unittest research.test_research research.test_reliability research.test_v3 research.test_v4 research.test_v5 research.test_v6 research.test_server research.test_handoff_persistence
```

## Learn with a small planning run

```bash
python3 -m research.run --suite smoke --methods b1_distance --planning-seconds 0.5
```

This command was tested during the handoff. It creates one exploratory record under this workbench's `mujoco/outputs/research/`; no physics is executed. It is not added to the manuscript evidence. To explore more cases after reading the code:

```bash
python3 -m research.run --suite procedural4 --world-seed 1760000 --methods b1_distance b3_energy proposed_v4 --planning-seconds 0.5
```

That second example was not run during the handoff. It is a learning example, not a predeclared confirmatory study. Omitting `--execute` keeps it planning-only; adding it requests assisted physics execution.

## Console and saved comparisons

`python3 -m research.server --port 8771` starts the inherited local console. That UI workflow was not browser-tested in this handoff. The copy does not contain the original raw run history, and final-download endpoints retain assumptions about the old delivery layout. Read the existing final data using [the offline comparison](../paper/archive/reference-links/offline_comparison.html) or [frozen JSON](../mujoco/outputs/research/final_validation_v6/) instead.

The original interactive demo launchers and top-level Isaac asset utilities are not a verified workflow in this reproduction copy. Use the scientific `research.run` entry point for learning. GUI scene behavior, dashboard rebuilding, live downloads and hardware were not validated here.

## Future changes

Edit this copy and keep a record of modifications. Its packaged V4/V5 manifest/source-lock files are prerequisites for the inherited V6 runner, not complete historical datasets. `python3 -m research.final_study --directory outputs/research/reproduction_v6` requests the existing 1,200-record protocol on its existing seeds; it can be expensive and is not new independent test evidence. It was not run in this handoff.

For a changed method, version the protocol, choose new development/test seeds and freeze settings before a new held-out evaluation. Read [the roadmap](../docs/PAPER_ROADMAP.md). Do not copy exploratory results into S1/S2/S3 directories or change their manifests to make them match new code.
