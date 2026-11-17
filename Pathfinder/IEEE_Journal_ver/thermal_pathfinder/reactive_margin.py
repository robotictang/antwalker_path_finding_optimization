"""Calibrate temperature and deadline margins from archived reactive replays."""

from collections import Counter
from dataclasses import asdict, dataclass
from itertools import product
import json
from pathlib import Path

from .margin_profiles import digest
from .mission_profiles import arguments

DEFAULT_CONFIG = Path("experiments/reactive_margin_transfer.json")
DEFAULT_OUTPUT = Path("results/reactive_margin_transfer")
DEFAULT_REFERENCE = Path("results/reactive_forecast")


@dataclass(frozen=True)
class Margins:
    temperature_c: float
    deadline_s: float

    def admits(self, peak, elapsed, limit, deadline):
        return bool(peak < limit - self.temperature_c and elapsed <= deadline - self.deadline_s)


@dataclass(frozen=True)
class Observation:
    course: str
    execution: str
    peak: float
    elapsed: float
    limit: float
    deadline: float
    outcome: str


def observations(forecasts, runs, courses, thermal):
    if set(forecasts) != set(runs):
        raise ValueError("Every forecasted schedule needs exactly one replay")
    rows = []
    for key, variants in sorted(forecasts.items()):
        course, = [item for item in courses if key.startswith(item["id"] + "_")]
        remainder = key.removeprefix(course["id"] + "_")
        setting, = [name for name in thermal if remainder.startswith(name + "_")]
        pred = variants["progress_reactive"]
        run = runs[key]
        rows.append(Observation(course["id"], key, pred["peak_c"], pred["elapsed_s"],
                                thermal[setting]["limit_c"], course["deadline_s"], run["failure"] or "completed"))
    return rows


def screen(margins, rows):
    counts = Counter()
    for row in rows:
        passed = margins.admits(row.peak, row.elapsed, row.limit, row.deadline)
        counts[f"{'admit' if passed else 'reject'}/{row.outcome}"] += 1
    return dict(counts)


def calibrate(rows, grid):
    sweep = []
    for temperature, time in product(grid["temperature_grid_c"], grid["deadline_grid_s"]):
        margins = Margins(temperature, time)
        counts = screen(margins, rows)
        thermal_leaks = sum(row.outcome == "thermal_limit" and row.peak < row.limit - temperature
                            for row in rows)
        feasible = thermal_leaks == 0 and all(
            key == "admit/completed" or not key.startswith("admit/") for key in counts
        )
        sweep.append({"margins": asdict(margins), "screening": counts, "feasible": feasible,
                      "thermal_stops_passing_temperature_gate": thermal_leaks})
    eligible = [row for row in sweep if row["feasible"]]
    if not eligible:
        raise ValueError("No margin pair passed the development failure criteria")
    selected = max(eligible, key=lambda row: (
        row["screening"].get("admit/completed", 0), row["margins"]["temperature_c"], row["margins"]["deadline_s"]
    ))
    return selected, sweep


def freeze(config, output, reference):
    spec = json.loads(config.read_text())
    files = ("manifest.json", "forecast_manifest.json", "schedule_forecasts.json", "executions.json")
    archive, source_lock, forecasts, runs = (json.loads((reference / name).read_text()) for name in files)
    if source_lock["nominal_manifest_sha256"] != digest(reference / "manifest.json"):
        raise ValueError("Reference forecast provenance is inconsistent")
    if set(source_lock["sources"]) != {"reactive_study.py", "reactive_forecast.py"} or any(
        digest(Path(__file__).with_name(name)) != sha for name, sha in source_lock["sources"].items()
    ):
        raise ValueError("Reactive forecast source differs from the calibration run")
    dev = archive["study"]
    if archive["base"] != json.loads(config.with_name(spec["base_config"]).read_text()):
        raise ValueError("The development and transfer simulator settings differ")
    for field in ("base_config", "speed_fractions", "reactive", "transition_s", "progress_bin_m", "forecast_step_s"):
        if dev[field] != spec[field]:
            raise ValueError(f"Calibration and transfer have different {field}")
    if any(old["id"] == new["id"] or old["stages"] == new["stages"]
           for old, new in product(dev["maps"], spec["maps"])):
        raise ValueError("Transfer course duplicates a development course")
    rows = observations(forecasts, runs, dev["maps"], archive["thermal"])
    chosen, sweep = calibrate(rows, spec["calibration"])
    folds = {}
    for course in dev["maps"]:
        name = course["id"]
        fit, _ = calibrate([row for row in rows if row.course != name], spec["calibration"])
        folds[name] = {"margins": fit["margins"],
                       "held_out_screening": screen(Margins(**fit["margins"]), [row for row in rows if row.course == name])}
    lock = {
        "held_out_config_sha256": digest(config), "development_sha256": {name: digest(reference / name) for name in files},
        "source_sha256": {name: digest(Path(__file__).with_name(name))
                          for name in ("reactive_margin.py", "reactive_margin_study.py", "reactive_forecast.py", "reactive_study.py")},
        "development_profiles": len(rows), "selected": chosen, "grid_results": sweep,
        "fixed_baseline": {"margins": asdict(Margins(spec["thermal_margin_c"], 0.0)),
                           "screening": screen(Margins(spec["thermal_margin_c"], 0.0), rows)},
        "leave_one_course_out": folds,
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "calibration.json").open("x") as artifact:
        artifact.write(json.dumps(lock, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: lock[key] for key in ("selected", "fixed_baseline", "leave_one_course_out")}, indent=2))


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=DEFAULT_CONFIG, output=DEFAULT_OUTPUT)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    args = parser.parse_args()
    freeze(args.config, args.output, args.reference)


if __name__ == "__main__":
    main()
