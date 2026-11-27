"""Rank the same candidate routes using different temperature information."""

import numpy as np

from .thermal import ThermalState


def predict_peak(settings, initial_c, torque_profile, interval_s):
    thermal = ThermalState(settings, initial_c)
    for rms_torque_nm in torque_profile:
        thermal.advance(rms_torque_nm, interval_s)
    return float(thermal.peak_by_joint_c.max())


def rank_routes(method, settings, initial_c, profiles, interval_s):
    if method == "per_joint":
        assumed_c = initial_c
    elif method == "maximum_only":
        assumed_c = np.full_like(initial_c, np.max(initial_c))
    elif method == "mean_only":
        assumed_c = np.full_like(initial_c, np.mean(initial_c))
    elif method == "time_only":
        assumed_c = None
    else:
        raise ValueError(f"Unknown planning method: {method}")

    feasible = []
    predictions = {}
    for name, profile in profiles.items():
        if not profile.completed:
            predictions[name] = {"feasible": False, "failure": profile.failure, "peak_c": None}
            continue
        peak = None if assumed_c is None else predict_peak(settings, assumed_c, profile.torques, interval_s)
        accepted = peak is None or peak < settings.limit_c
        predictions[name] = {"feasible": accepted, "failure": None if accepted else "predicted_thermal_limit", "peak_c": peak}
        if accepted:
            # Minimize predicted peak first among routes meeting the deadline.
            feasible.append((peak if peak is not None else 0.0, profile.elapsed_s, name))
    return (min(feasible)[2] if feasible else None), predictions
