"""Plot the paper's examples and benchmark results from the audited traces."""

from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .margin_profiles import digest
from .mission_profiles import arguments, design
from .pause_confirmation import CONFIG, OUTPUT
from .pause_forecast_study import METHODS, read
from .published_speed_baseline import DEFAULT_OUTPUT as PUBLISHED_OUTPUT, METHOD as PUBLISHED_METHOD

BLUE = "#0072B2"
ORANGE = "#D55E00"
GRAY = "#525b65"


def save(fig, output, name):
    vector = output / f"{name}.svg"
    fig.savefig(vector)
    vector.write_text("\n".join(line.rstrip() for line in vector.read_text().splitlines()) + "\n")
    fig.savefig(output / f"{name}.png", dpi=400)
    plt.close(fig)


def plot_routes(config, results, output):
    manifest, networks, _, _, _ = design(config)
    if manifest["study"] != read(results / "manifest.json")["study"]:
        raise ValueError("Course definitions differ from the benchmark")
    plans = read(results / "plans.json")
    replays = read(results / "executions.json")
    audit = read(results / "confirmation_audit.json")
    gains = {(row["map"], row["setting"], row["start"]) for row in audit["additional_finishes"]}
    course, = {name for name, _, _ in gains}
    network = networks[course]
    rows = [row for row in plans
            if row["method"] == METHODS[-1] and (row["map"], row["setting"], row["start"]) in gains]
    fig, (paths, thermal) = plt.subplots(2, 1, figsize=(7.05, 4.55), layout="constrained",
                                        gridspec_kw={"height_ratios": [1, 1.28]})
    for edges in product(*network.edges.values()):
        route = network.route(edges)
        shown = route.x <= route.goal_x
        paths.plot(route.x[shown], route.y[shown], ls="--", color="#9ba3ab", lw=0.8)
    for row, color in zip(rows, (BLUE, ORANGE), strict=True):
        record = replays[row["execution"]]
        path = results / record["trace"]
        if digest(path) != record["trace_sha256"]:
            raise ValueError(f"Replay changed: {path}")
        with np.load(path) as trace:
            body = trace["body_xyz_m"]
            hottest = trace["temperature_c"].max(axis=1)
        label = f"{row['start'].split('_')[0].capitalize()} side warm"
        style = "-" if color == BLUE else (0, (5, 2))
        paths.plot(body[:, 0], body[:, 1], color=color, ls=style, lw=1.65, label=label)
        elapsed = np.arange(len(hottest)) * manifest["sample_interval_s"]
        thermal.plot(elapsed, hottest, color=color, ls=style, lw=1.45)
        hold = record["pause"]
        thermal.axvspan(hold["started_s"], hold["resumed_s"], color=color, alpha=0.13, lw=0)
        thermal.plot(elapsed[-1], hottest[-1], marker="o", ms=3.5, color=color)
    paths.scatter(network.junctions, np.zeros_like(network.junctions), c=GRAY, s=13, zorder=6)
    for x, label in zip(network.junctions, ("Start", "Pause junction", "Goal"), strict=True):
        paths.annotate(label, (x, 0), (0, 8), textcoords="offset points", ha="center", color=GRAY, fontsize=8)
    paths.set(xlabel="Forward position (m)", ylabel="Lateral position (m)", xlim=(-1.9, network.junctions[-1] + 1.9),
              ylim=(-2.7, 3.3))
    paths.set_title("(a) Chassis paths on the shallow alternating-bank course", loc="left")
    paths.legend(loc="upper center", bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False)
    thermal.axhline(70, color=GRAY, ls=":", lw=0.9)
    thermal.text(3, 70.06, "70 °C execution stop", fontsize=8, color=GRAY, va="bottom")
    thermal.set(xlabel="Elapsed mission time (s)", ylabel="Hottest motor (°C)", xlim=(0, 348),
                ylim=(min(thermal.get_ylim()[0], 64), 70.55))
    thermal.set_title("(b) Temperature traces and 12 s junction pauses", loc="left")
    thermal.grid(axis="y", alpha=0.22)
    save(fig, output, "junction_paths_and_temperatures")


def plot_benchmark(results, output, published):
    audit = read(results / "confirmation_audit.json")["primary"]
    screen = read(results / "screening_diagnostic.json")
    if any(digest(results / name) != sha for name, sha in screen["source_sha256"].items()):
        raise ValueError("Screening inputs changed")
    fig, (counts, forecasts) = plt.subplots(1, 2, figsize=(7.05, 2.75), layout="constrained",
                                            gridspec_kw={"width_ratios": [1.04, 1]})
    entries = dict(zip(METHODS, ("Fixed reactive", "Time-only fallback", "Per-motor forecast"), strict=True))
    outcomes = {method: audit["by_method"][method]["outcomes"] for method in METHODS}
    if published.is_dir():
        comparison = read(published / "summary.json")
        reference = read(published / "manifest.json")["reference_hashes"]
        if any(digest(results / name) != checksum for name, checksum in reference.items()):
            raise ValueError("Published controller comparison uses a different benchmark")
        outcomes[PUBLISHED_METHOD] = comparison["outcomes"][PUBLISHED_METHOD]
        entries[PUBLISHED_METHOD] = "Published controller (adapted)"
    order = list(entries)
    known = {"completed", "no_route", "thermal_limit", "deadline"}
    for counts_by_outcome in outcomes.values():
        counts_by_outcome["other"] = sum(value for key, value in counts_by_outcome.items() if key not in known)
    y = np.arange(len(order))
    left = np.zeros(len(order), dtype=int)
    for status, label, color, fg in (
        ("completed", "Completed", BLUE, "white"),
        ("no_route", "Rejected", "#cfd7de", "#17202a"),
        ("thermal_limit", "Thermal stop", ORANGE, "#13191f"),
        ("deadline", "Deadline", "#56616e", "white"),
        ("other", "Other failure", "#c9a14e", "#17202a"),
    ):
        values = np.array([outcomes[method].get(status, 0) for method in order])
        if not np.any(values):
            continue
        counts.barh(y, values, left=left, height=0.58, color=color, label=label, edgecolor="white", linewidth=0.5)
        for row, (origin, value) in enumerate(zip(left, values, strict=True)):
            if value >= 4:
                counts.text(origin + value / 2, row, str(value), ha="center", va="center", color=fg, fontsize=8)
            elif value:
                counts.text(origin + value / 2, row + 0.39, str(value), ha="center", va="center", color="#17202a", fontsize=8)
        left += values
    counts.set(xlim=(0, 72), ylim=(len(order) - 0.37, -0.57), xticks=(0, 24, 48, 72), xlabel="Starts",
               yticks=y, yticklabels=tuple(entries.values()))
    counts.set_title("(a) Planner outcomes", loc="left")
    counts.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.55, -0.28), frameon=False,
                  columnspacing=0.85, handlelength=1.1)

    cut, = {row["ceiling_c"] for row in screen["cases"]}
    limit, = {row["limit_c"] for row in screen["cases"]}
    forecasts.axvspan(cut, limit, color="#e5ebef", lw=0)
    forecasts.axvline(cut, color=GRAY, lw=0.85, ls="--")
    forecasts.axvline(limit, color=GRAY, lw=0.85, ls=":")
    for outcome, label, color, marker in (
        ("thermal_limit", "Thermal stop", ORANGE, "x"),
        ("completed", "Completed", BLUE, "o"),
    ):
        rows = [row for row in screen["cases"] if row["actual_outcome"] == outcome]
        forecasts.scatter([row["predicted_peak_c"] for row in rows],
                          [row["deadline_s"] - row["predicted_elapsed_s"] for row in rows],
                          c=color, marker=marker, linewidths=0.9, s=15, label=label, zorder=5)
    forecasts.set_title("(b) Time-only fallback schedules", loc="left")
    forecasts.set(xlabel="Predicted paused peak (°C)", ylabel="Predicted time to spare (s)")
    forecasts.set_xticks([cut, limit, 71, 72], ["69.5", "70", "71", "72"])
    forecasts.grid(axis="y", alpha=0.22)
    forecasts.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2, frameon=False,
                     columnspacing=0.85, handletextpad=0.2)
    save(fig, output, "benchmark_outcomes_and_screening")


def main():
    parser = arguments(__doc__)
    parser.set_defaults(config=CONFIG, output=OUTPUT)
    parser.add_argument("--figures", type=Path, default=Path("docs/figures"))
    parser.add_argument("--published", type=Path, default=PUBLISHED_OUTPUT)
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9,
                         "axes.spines.top": False, "axes.spines.right": False, "svg.fonttype": "none"})
    plot_routes(args.config, args.output, args.figures)
    plot_benchmark(args.output, args.figures, args.published)


if __name__ == "__main__":
    main()
