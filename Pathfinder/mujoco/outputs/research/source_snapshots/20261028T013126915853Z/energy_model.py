"""Shared route prediction and measured-motion battery consumption, in % capacity.

Coefficients are explicit simulation assumptions, not hardware measurements.
There is no first-trip multiplier or cheaper energy during a charging diversion.
"""
import numpy as np

DRIVE_PERCENT_PER_M=.25
WALK_PERCENT_PER_M=.70
HOTEL_PERCENT_PER_S=.015
TURN_PERCENT_PER_RAD=.08
TRANSFORM_PERCENT=.50
START_STOP_PERCENT=.10
UNCERTAINTY_FACTOR=1.25
TASK_RESERVE_PERCENT=6.
CHARGER_RESERVE_PERCENT=2.
LOW_BATTERY_PERCENT=20.
OBJECTIVE_SCALES=np.array([50.,90.,30.]) # meters, seconds, percentage points
DEFAULT_WEIGHTS=np.array([1/3,1/3,1/3])


def energy_cost(drive,walk,seconds,turn_radians,transformations):
    return float(drive*DRIVE_PERCENT_PER_M+walk*WALK_PERCENT_PER_M+
                 seconds*HOTEL_PERCENT_PER_S+turn_radians*TURN_PERCENT_PER_RAD+
                 transformations*TRANSFORM_PERCENT+(START_STOP_PERCENT if drive+walk>1e-8 else 0.))


def normalize_weights(weights):
    value=np.asarray(weights,dtype=float)
    if value.shape!=(3,) or not np.isfinite(value).all() or np.any(value<0) or value.sum()<=0:
        raise ValueError('Distance/time/energy weights must be finite, nonnegative, with a positive sum')
    return value/value.sum()


def objective_weights(mode,weights=None):
    if mode in ('shortest','fastest','energy'):return np.eye(3)[('shortest','fastest','energy').index(mode)]
    if mode!='balanced':raise ValueError('Unknown path objective: '+mode)
    return normalize_weights(DEFAULT_WEIGHTS if weights is None else weights)


def objective_score(metrics,mode='balanced',weights=None):
    vector=np.array([metrics['distance_m'],metrics['estimated_seconds'],metrics['energy_percent']])
    return float(np.dot(objective_weights(mode,weights),vector/OBJECTIVE_SCALES))


def required_energy(energy,reserve=TASK_RESERVE_PERCENT):
    return float(UNCERTAINTY_FACTOR*energy+reserve)
