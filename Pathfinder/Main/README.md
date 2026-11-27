# Reproduce the hot-motor-swap study

See the [main study results](docs/hot_motor_swap.md) for the outcome summary and saved records. The [protocol](docs/hot_motor_swap_protocol.md) and [frozen configuration](experiments/hot_motor_swap.json) specify the main experiment. [Model provenance](Hexapod_Model/README.md) describes the simplified geometry.

## Environment

From this directory, use Python 3.12 on Linux or another platform with POSIX file locking. The frozen data record Python 3.12.14, MuJoCo 3.9.0, and NumPy 2.2.6. Use the recorded Python version when checking the frozen archives.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

## Run the exhaustive hot-motor-swap test

Choose an unused results directory for a fresh run. The first command profiles each branch at both nominal speeds. The second replays every supported route under both mirrored assignments and compares the two planners. A complete run records 96 nominal profiles and 288 warm walks. Adjust the worker count for the host.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.mission_profiles --config experiments/hot_motor_swap.json --output results/hot_motor_swap --workers 4
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m thermal_pathfinder.hot_motor_swap --config experiments/hot_motor_swap.json --output results/hot_motor_swap --workers 4
```

Restarting the warm-run command in the same output directory verifies the frozen inputs and resumes saved routes. The earlier staged-course configurations in `experiments/` serve as fixtures for checking that the new evaluation geometry is distinct.

## Verify the saved results

[Download the data archive](https://github.com/robotictang/antwalker_path_finding_optimization/archive/refs/tags/hot-motor-swap-data-v1.0.0.zip) and extract it into a separate directory. Copy its four result folders into this project's `results/` directory in a clean checkout. The commands below operate on those writable copies.

```bash
.venv/bin/python -m thermal_pathfinder.hot_motor_swap --workers 1
.venv/bin/python -m thermal_pathfinder.matched_pause_audit
.venv/bin/python -m thermal_pathfinder.pause_screening_diagnostic
```

The first command re-audits the saved warm traces and recomputes the main summary. The other two verify the matched-pause comparison and the 48 fixed schedules in Appendix B. [Earlier planner outcomes](https://github.com/robotictang/antwalker_path_finding_optimization/blob/hot-motor-swap-data-v1.0.0/results/published_speed_baseline/summary.json) links the saved comparison used in Appendix C.

To regenerate the matched-pause figure from the saved results, install Matplotlib 3.10.3 in the virtual environment and run `.venv/bin/python -m thermal_pathfinder.matched_pause_figure`.
