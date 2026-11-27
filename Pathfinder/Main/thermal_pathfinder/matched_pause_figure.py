"""Render course outcomes and route-level forecast changes for the matched experiment."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from .matched_pause import METHODS, OUTPUT, admissible
from .pause_confirmation import read


def render(results, destination):
    summary = read(results / "summary.json")
    plans = read(results / "plans.json")
    courses = list(summary["by_map"])
    completion = np.array([
        [summary["by_map"][course][method].get("completed", 0) for method in METHODS]
        for course in courses
    ])
    plot_labels = [name.removeprefix("matched_").replace("_", " ") for name in courses]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "matched-pause"})
    fig, (courses_ax, change_ax) = plt.subplots(1, 2, figsize=(10, 4.3), width_ratios=(1, 1.2),
                                               layout="constrained")
    y = np.arange(len(courses))
    control, treatment = "#374758", "#146a57"
    for index, (zero, enabled) in enumerate(completion):
        courses_ax.plot([zero, enabled], [index, index], color="0.6", linewidth=1.1)
    courses_ax.scatter(completion[:, 0], y, facecolors="white", edgecolors=control, linewidth=1.0, s=46,
                       label="Governor only", zorder=3)
    courses_ax.scatter(completion[:, 1], y, color=treatment, s=15, label="Pause available", zorder=4)
    courses_ax.set(yticks=y, yticklabels=plot_labels, xlim=(-.35, 6.35), xticks=np.arange(7),
                   xlabel="Completed starts (of 6)", title="(a) Paired course outcomes")
    courses_ax.invert_yaxis()
    courses_ax.grid(axis="x", color="0.88", linewidth=.6)
    courses_ax.legend(loc="lower right", frameon=False, fontsize=8)

    changes, passed, selected = [], [], []
    for case in plans:
        arm = case["methods"][METHODS[1]]
        zero = {tuple(c["route"]): c for c in arm["candidates"] if c["pause_s"] == 0}
        for paused in arm["candidates"]:
            if not paused["pause_s"]:
                continue
            baseline = zero[tuple(paused["route"])]
            changes.append((paused["predicted_peak_c"] - baseline["predicted_peak_c"],
                            paused["predicted_elapsed_s"] - baseline["predicted_elapsed_s"]))
            passed.append(admissible(paused, case["deadline_s"], case["ceiling_c"]))
            selected.append(paused == arm["selected"])
    deltas = np.asarray(changes)
    passed, selected = np.asarray(passed), np.asarray(selected)
    change_ax.axvline(0, color="0.5", linewidth=.7)
    change_ax.axhline(0, color="0.5", linewidth=.7)
    change_ax.scatter(*deltas[~passed].T, s=14, alpha=.52, color="#878b93", edgecolors="none",
                      label="Paused forecast rejected")
    change_ax.scatter(*deltas[passed].T, s=16, alpha=.68, color=treatment, edgecolors="none",
                      label="Paused forecast admitted")
    if selected.any():
        change_ax.scatter(*deltas[selected].T, s=70, marker="s", facecolors="none", edgecolors="#962e19",
                          linewidth=1.2, label="Paused route selected")
    change_ax.set(xlabel=r"Change in predicted peak ($^\circ$C)", ylabel="Change in predicted arrival (s)",
                  title="(b) Adding 12 s to the same route")
    change_ax.legend(frameon=True, facecolor="white", edgecolor="none", fontsize=8)
    for suffix in ("png", "svg"):
        metadata = {"Date": None} if suffix == "svg" else {}
        path = destination / f"matched_pause_outcomes.{suffix}"
        fig.savefig(path, dpi=300, metadata=metadata)
        if suffix == "svg":
            path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=OUTPUT)
    parser.add_argument("--destination", type=Path, default=Path("docs/figures"))
    args = parser.parse_args()
    render(args.results, args.destination)


if __name__ == "__main__":
    main()
