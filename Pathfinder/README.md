# Pathfinder research handoff

**Start here if you are taking over the paper.** This project studies how a simulated six-legged robot chooses routes while respecting a deadline, a modeled battery allowance and terrain limits. The working manuscript and saved evidence document a simulation study.

Start with the [current IJ3C manuscript](paper/latest/Pathfinder-IJ3C-Final.docx), focused on constrained planning and stage-removal results. The guides below describe the original 3 November handoff. Read the [newcomer guide](docs/PROJECT_GUIDE.md), then the [paper continuation plan](docs/PAPER_ROADMAP.md). The [file map](docs/FILE_MAP.md) explains which code and data to open.

## Find the right material

| Your task | Start here |
|---|---|
| Read or edit the current IJ3C manuscript | [Current Word file](paper/latest/Pathfinder-IJ3C-Final.docx) |
| Find earlier manuscript versions and reviews | [Paper index](paper/README.md) |
| Inspect results without running experiments | [IJ3C results](publication_2026_11_05_revised/results/) and [earlier offline comparison](paper/archive/reference-links/offline_comparison.html) |
| Learn or change the scientific code | [Portable workbench](workbench/README.md) |
| Trace a claim to data | [Evidence map](docs/FILE_MAP.md#trace-a-claim-to-its-evidence) |
| Read older manuscripts | [Archive index](archive/README.md) |
| See what was checked | [Verification notes](docs/verification/README.md) |

## Folder arrangement

```text
Pathfinder/
  README.md              This entry point
  docs/                  Newcomer guide, continuation plan, file map and checks
  paper/                 Latest Word manuscript and archived iterations
  workbench/             Independent portable code copy for learning and edits
  archive/               Ordered links to earlier studies and drafts
  tools/                 Evidence inspection and audit helpers
  mujoco/                Original source, demo, frozen studies and backups
  outputs/               Original reports, packages and authoring assets
  meshes/                Original robot geometry
  hexapod.urdf           Original robot description
  hexapod_cfg.py         Original Isaac Lab configuration
  convert_urdf_to_usd.py  Original Isaac conversion utility
```

`paper/latest/` contains the working Word file. `paper/archive/` contains earlier drafts, reviews and shortcuts to preserved packages. `workbench/` is a real independent copy of the existing portable reproduction package and has 63 passing test executions, including imported existing cases and three new representation checks. Use it for research commands: the original scene still names a missing Downloads folder.

Original research files stay in their existing locations to preserve hashes and path relationships. This organization adds clear entry points and a working area without moving frozen evidence. The former root README, mainly about the older Isaac asset/demo, is saved under [legacy guides](docs/legacy_guides/ORIGINAL_ROOT_README.md).

## What the latest evidence says

The new S4 campaign has 640 planning records on eight development and 32 new primary worlds. V4 admits 93/96 primary attempts; continuous-coordinate PSO admits 94/96. V4's mean paired score improvement against that control is 0.690%, median zero, with a descriptive 95% interval spanning zero. This supports a careful comparative simulation paper, with no established mean score advantage against the new control. All adverse outcomes are retained.

The live demo and research server are stopped at the user's request. The [earlier offline comparison](paper/archive/reference-links/offline_comparison.html) remains available. Figure 1 in the current manuscript shows the simulated hexapod and its planned route on corridor Map 24.

## Earlier evidence (preserved)

The V6 campaign contains 1,200 scheduled records, including 576 primary planning attempts: six configurations × 48 worlds × two repetitions. The route optimizer is still called V4. It admits 90/96 primary attempts. Its mean score advantages over polished PSO and ACO are about 0.24% and 0.47% on jointly admitted cases; both median world improvements are zero. These are small conditional benefits, with ties and losses retained.

Motion remains assisted, battery use is modeled and hardware validation is pending. Admission is different from successful execution. Read the [guide](docs/PROJECT_GUIDE.md) before using these results in writing.

## Preservation and next step

The full pre-handoff backup is at `/home/user123456/Desktop/Pathfinder_handoff_backup_2026-11-03/Pathfinder`, with a SHA-256 inventory beside it. No commit or push was made. Git initially reported the entire Pathfinder directory as untracked.

First read the guide and [current Word manuscript](paper/latest/Pathfinder-IJ3C-Final.docx), then discuss the contribution and validation scope with your supervisor using the [roadmap](docs/PAPER_ROADMAP.md).
