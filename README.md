# Hexapod Path Planning and Optimization

This repository contains the **Pathfinder** simulation study and its scientific manuscript. The project compares route planners for a six-legged robot under obstacle-clearance, travel-time, nominal battery and terrain constraints. The research implementation uses MuJoCo; older Isaac Lab asset-import files are also retained.

Start with the current paper, then follow its results back to the saved records and research code. All paths below are relative to this repository.

## Start here

1. Read the latest manuscript: [PDF](Pathfinder/publication_2026_11_05_revised/IJ3C_Manuscript.pdf) or [editable Word document](Pathfinder/publication_2026_11_05_revised/IJ3C_Manuscript.docx).
2. Open the [current revision overview](Pathfinder/publication_2026_11_05_revised/README.md) and [evidence map](Pathfinder/publication_2026_11_05_revised/Evidence_Map.md) to understand which records support the article.
3. Use the folder map below to find the code, data or earlier drafts you need.

The current manuscript is the **9-page IJ3C revision focused on constrained planning and stage-removal comparisons**, stored in `publication_2026_11_05_revised/`. Its main planning campaign contains 640 records, including 576 primary attempts on 32 test maps. Older IEEE drafts and campaigns remain available as history; their counts and comparisons describe different experiments.

## Folder map

```text
Pathfinder/
├── README.md                    Detailed project handoff
├── paper/                       Shortcuts to the current paper and its material
├── publication_2026_11_*/     Preserved manuscript revisions
├── workbench/                   Research working copy and environment notes
│   └── mujoco/
│       ├── research/            Planners, study protocols, execution and tests
│       └── outputs/research/    Saved campaigns, source snapshots and models
├── docs/                        Background guides, file map and verification notes
├── archive/                     Shortcuts to earlier studies and manuscripts
├── mujoco/                      Original implementation, demo and historical results
├── outputs/                     Earlier paper packages, reports and supporting material
├── meshes/                      Original robot geometry
├── hexapod.urdf                 Original robot description
├── hexapod_cfg.py               Older Isaac Lab configuration
├── convert_urdf_to_usd.py        Older Isaac asset-conversion utility
├── tools/                       Demo launcher and evidence-inspection helpers
└── GIT_STORAGE.md               Files deliberately excluded from Git
```

## Find material by task

| What you want to do | Where to look |
|---|---|
| Read or edit the current paper | [Latest revision](Pathfinder/publication_2026_11_05_revised/) |
| Read the article as plain text | [Assembled manuscript](Pathfinder/publication_2026_11_05_revised/IJ3C_Manuscript.md) |
| Find the narrative used by the builder | [Article source](Pathfinder/publication_2026_11_05_revised/source/article.md) and [source scripts](Pathfinder/publication_2026_11_05_revised/source/) |
| Inspect the paper's tables and computed comparisons | [Current results](Pathfinder/publication_2026_11_05_revised/results/) |
| Inspect individual planning attempts and returned routes | [Raw primary records](Pathfinder/publication_2026_11_05_revised/raw_study/primary.json) |
| Check the study design and selected parameters | [Manifest](Pathfinder/publication_2026_11_05_revised/raw_study/manifest.json) and [locked parameters](Pathfinder/publication_2026_11_05_revised/raw_study/locked_parameters.json) |
| Locate the article's images | [Publication figures](Pathfinder/publication_2026_11_05_revised/figures/) |
| Check template formatting and revision decisions | [Template review](Pathfinder/publication_2026_11_05_revised/Template_Review.md) and [revision notes](Pathfinder/publication_2026_11_05_revised/Review_Changes.md) |
| Understand or extend the research implementation | [Workbench](Pathfinder/workbench/README.md) and [research code](Pathfinder/workbench/mujoco/research/) |
| Browse an older campaign interactively | Download and open the [offline comparison HTML](Pathfinder/outputs/ieee_access_final/package/Comparison_Offline.html); it covers the earlier V6 campaign |
| Find previous drafts and engineering snapshots | [Archive index](Pathfinder/archive/README.md), [original backups](Pathfinder/mujoco/backups/) and [older outputs](Pathfinder/outputs/) |

Within the latest publication folder, `raw_study/` contains saved planning inputs and records; `results/` contains analyses and motion diagnostics; `source/` contains the article builder and checking scripts; `template/` retains the journal instructions and sample; and `qa/` contains retained verification reports. Its [evidence map](Pathfinder/publication_2026_11_05_revised/Evidence_Map.md) explains how these pieces support specific claims.

## Read the code in this order

Use `Pathfinder/workbench/mujoco/` as the working area. The original `mujoco/` tree and frozen source/model snapshots provide historical provenance.

| File beneath `workbench/mujoco/` | Purpose |
|---|---|
| [research/publication_study.py](Pathfinder/workbench/mujoco/research/publication_study.py) | Defines the current IJ3C planning campaign |
| [research/run.py](Pathfinder/workbench/mujoco/research/run.py) and [research/worlds.py](Pathfinder/workbench/mujoco/research/worlds.py) | Organize cases, generated maps and result records |
| [research/planning.py](Pathfinder/workbench/mujoco/research/planning.py) and [research/swarm.py](Pathfinder/workbench/mujoco/research/swarm.py) | Define shared route metrics, constraints and optimizer logic |
| [research/advanced.py](Pathfinder/workbench/mujoco/research/advanced.py) | Implements the retained V4 planner |
| [research/continuous_pso.py](Pathfinder/workbench/mujoco/research/continuous_pso.py) | Implements the coordinate-based PSO comparison |
| [research/execution.py](Pathfinder/workbench/mujoco/research/execution.py) and [research/tracking.py](Pathfinder/workbench/mujoco/research/tracking.py) | Follow routes and apply body assistance |
| [research/telemetry.py](Pathfinder/workbench/mujoco/research/telemetry.py) | Records contact, tilt and actuator-work diagnostics |

Environment information is in the [workbench README](Pathfinder/workbench/README.md), [reproduction notes](Pathfinder/workbench/REPRODUCE.txt) and [pinned requirements](Pathfinder/workbench/requirements-pinned.txt). Some scripts and archived model files retain paths from the original workstation. Check path resolution before running them in a new checkout. Create a new protocol/version and output directory for new experiments; preserve the existing evidence and source locks.

## Manuscript revisions

These folders preserve successive revisions of the article; they are not separate independent experiments.

| Folder | Role |
|---|---|
| [publication_2026_11_04](Pathfinder/publication_2026_11_04/) | Initial IJ3C revision and current planning campaign analysis |
| [publication_2026_11_04_format_review](Pathfinder/publication_2026_11_04_format_review/) | Formatting and font revision |
| [publication_2026_11_04_ten_page](Pathfinder/publication_2026_11_04_ten_page/) | Expanded ten-page article |
| [publication_2026_11_04_plain_language](Pathfinder/publication_2026_11_04_plain_language/) | Separate plain-language revision |
| [publication_2026_11_04_illustrated](Pathfinder/publication_2026_11_04_illustrated/) | Added demonstration screenshot |
| [publication_2026_11_04_template_checked](Pathfinder/publication_2026_11_04_template_checked/) | Further template and Word-style corrections |
| [publication_2026_11_04_robot_figure](Pathfinder/publication_2026_11_04_robot_figure/) | Preserved version with the direct MuJoCo model capture |
| **[publication_2026_11_05_revised](Pathfinder/publication_2026_11_05_revised/)** | **Current revision with focused claims, algorithm/settings and combined displays** |

The background [project guide](Pathfinder/docs/PROJECT_GUIDE.md), [file map](Pathfinder/docs/FILE_MAP.md) and [paper roadmap](Pathfinder/docs/PAPER_ROADMAP.md) preserve earlier handoff context. Some passages describe the previous IEEE manuscript. Use the current revision and its evidence map for the latest article's methods and results.

## Shortcuts and generated files

`paper/` and `archive/` contain relative symbolic links. On Linux, editing through a paper shortcut changes its target file. The `plain_language_manuscript` shortcuts currently point to the same latest article as `current_manuscript`; the earlier separate copy remains in `publication_2026_11_04_plain_language/`. Use the direct links above when browsing on GitHub.

Large review ZIPs, intermediate page renders, local rendering libraries and mutable demo databases are excluded from Git. They may be absent in a fresh clone. See [Git storage notes](Pathfinder/GIT_STORAGE.md) for the exclusions and packaging entry point. Final manuscripts, publication figures, research code and raw study evidence remain versioned.

The live hybrid demonstration is separate from the paper's walking-only planning experiments. The study uses assisted body motion and nominal battery costs; the saved results do not establish hardware performance or measured electrical savings. Author/contact fields and the deferred acknowledgment remain pending author decisions.
