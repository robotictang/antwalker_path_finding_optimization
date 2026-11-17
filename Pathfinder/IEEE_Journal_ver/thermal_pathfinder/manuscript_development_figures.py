"""Reproduce the course diagram and pause-duration paper figures."""

import os
from pathlib import Path
import shutil

import matplotlib.pyplot as plt
import numpy as np

from .manuscript_figures import BLUE, GRAY, ORANGE, save
from .margin_profiles import digest
from .mission_profiles import design
from .pause_confirmation import CONFIG
from .pause_forecast_study import read
from .walking import SAMPLE_SECONDS


def plot_course(output):
    _, networks, _, _, _ = design(CONFIG)
    network = networks["switch_shallow"]
    fig, ax = plt.subplots(figsize=(3.62, 2.27), layout="constrained")
    for stage, section in enumerate(network.sections):
        origin = network.junctions[stage]
        for edge in network.edges[stage]:
            shift = section["shifts_m"][edge.branch]
            begin = origin + section["turn_m"] + shift
            y = section["offsets_m"][edge.branch]
            ax.fill_betweenx([y - 0.48, y + 0.48], begin, begin + section["bank_m"],
                             color="#d9eafa", zorder=0)
            route = network.route((edge,), local_start=True)
            shown = route.x <= route.goal_x
            ax.plot(route.x[shown] + origin, route.y[shown], lw=1.25, color=BLUE)
            angle = section["banks_deg"][edge.branch]
            ax.text(begin + section["bank_m"] / 2, y + np.sign(y) * 0.57,
                    f"{angle:+.1f}°",
                    ha="center", va="center", fontsize=8)
    ax.scatter(network.junctions, [0, 0, 0], c="#182431", s=17, zorder=4)
    for x, label in zip(network.junctions, ("Start", "Pause junction", "Goal"), strict=True):
        ax.annotate(label, (x, 0), xytext=(0, 9), textcoords="offset points",
                    ha="center", fontsize=8)
    ax.set(xlabel="Forward position (m)", ylabel="Lateral position (m)",
           xlim=(-4, network.junctions[-1] + 4), ylim=(-3.4, 3.4),
           yticks=[-3, -2, -1, 0, 1, 2, 3])
    ax.grid(axis="x", color="#e7ebf1", lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, output, "two_stage_course")


def plot_duration(output):
    folder = Path("results/junction_pause")
    manifest = read(folder / "manifest.json")
    summary = read(folder / "summary.json")
    control = summary["zero_pause_check"]
    key = control["execution"]
    candidates = sorted((row for row in summary["schedules"] if row["baseline_execution"] == key),
                        key=lambda row: row["pause_s"])
    if [row["pause_s"] for row in candidates] != [6, 12, 24] or not control["identical_arrays"]:
        raise ValueError("Expected the matched archived pilot schedule and all three durations")
    reference = manifest["reference_traces"][key]
    control_path = Path(reference["path"])
    if digest(control_path) != reference["sha256"]:
        raise ValueError(f"Pilot control changed: {control_path}")
    cases = [{
        "pause_s": 0, "trace": control_path, "trace_sha256": reference["sha256"],
        "failure": "thermal_limit",
    }] + [row | {"trace": folder / row["trace"]} for row in candidates]
    fig, (hold, finish) = plt.subplots(2, 1, figsize=(3.62, 3.9), layout="constrained")
    for row, color, style in zip(cases, (GRAY, ORANGE, BLUE, "#8155a5"),
                                 ("--", "-.", "-", ":"), strict=True):
        path = row["trace"]
        if digest(path) != row["trace_sha256"]:
            raise ValueError(f"Pilot trace changed: {path}")
        with np.load(path) as trace:
            hottest = trace["temperature_c"].max(axis=1)
        elapsed = np.arange(len(hottest)) * SAMPLE_SECONDS
        for ax in (hold, finish):
            ax.plot(elapsed, hottest, color=color, ls=style, lw=1.25,
                    label=f"{row['pause_s']:g} s")
        markers = {None: "o", "thermal_limit": "x", "deadline": "s"}
        finish.plot(elapsed[-1], hottest[-1], color=color, marker=markers[row["failure"]],
                    ms=4, clip_on=False)
        if row.get("pause"):
            resumed = row["pause"]["resumed_s"]
            sample = int(round(resumed / SAMPLE_SECONDS))
            hold.plot(resumed, hottest[sample], color=color, marker="o", ms=3)
    arrival = candidates[0]["pause"]["started_s"]
    hold.axvline(arrival, color="#b8c1cc", lw=0.85)
    hold.text(arrival + 0.4, 67.02, "Junction", fontsize=7, va="top", color=GRAY)
    hold.set(xlim=(arrival - 3, arrival + 32), ylim=(64.6, 67.12))
    hold.set_title("(a) Junction entry and restart", loc="left", fontsize=9)
    hold.legend(ncol=4, frameon=False, fontsize=7, loc="lower left", columnspacing=1.05)
    finish.axhline(manifest["limit_c"], color="#747e8b", lw=0.9, ls="--")
    finish.axvline(manifest["deadline_s"], color="#747e8b", lw=0.9, ls="--")
    finish.text(301.4, 70.07, "Thermal limit", color=GRAY, fontsize=7, va="bottom")
    finish.text(351.4, 67.14, "Deadline", color=GRAY, fontsize=7, ha="right", va="bottom")
    finish.set(xlim=(300, 354.5), ylim=(67.0, 70.43), xlabel="Elapsed mission time (s)")
    finish.set_title("(b) Thermal stops (×), finish (●), deadline (■)", loc="left", fontsize=9)
    for ax in (hold, finish):
        ax.set_ylabel("Hottest motor (°C)", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e7ebf1", lw=0.6)
    save(fig, output, "pause_pilot_durations")


def main():
    output = Path("docs/figures")
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    plt.rcParams.update({"font.size": 9, "svg.hashsalt": "pathfinder-study"})
    plot_course(output)
    plot_duration(output)
    for name in ("two_stage_course.png", "pause_pilot_durations.png"):
        shutil.copyfile(output / name, Path("manuscript/ieee-access/figures") / name)


if __name__ == "__main__":
    main()
