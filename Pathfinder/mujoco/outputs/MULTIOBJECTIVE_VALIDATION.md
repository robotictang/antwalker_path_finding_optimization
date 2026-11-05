# Multi-objective validation

Balanced planning completed Quarry → Marsh → Desert → Forest in 379.8 simulated seconds with 15 automatic transformations and 1 energy-triggered charging stop(s). Minimum battery: 23.1%. There were zero blocking-obstacle contacts/penetrations, route failures, and solver warnings. Protective clearance stops: 1.

Starting at 45%, the robot charged before the task and above the 20% fallback threshold, then generated a station-to-Quarry route and arrived. It handled roadwork detection/clearance and energy replanning. There were zero obstacle contacts or route failures, and 1 protective clearance stop(s). Every recorded departure budget fit available energy; both successful runs closed the battery ledger numerically.

The demonstration roadwork barrier clears after 90 simulated seconds, producing an external map revision and fresh energy checks. Permanent scenery obstacles remain fixed. In the separately preserved persistent-barrier case, the round-trip requirement exceeded 100%; the robot correctly stopped at the full charger instead of looping through charging. A 2% initial-battery test also stopped without movement because the charger itself was unreachable.

All four scalarized grid objectives matched independent Dijkstra. Every destination had continuously checked non-dominated route alternatives. Tests covered shared motion/transform energy accounting, invalid weights, idle charger reserve, and impossible full-capacity tasks. Cached energy estimates use unique map revisions so obsolete obstruction costs are not reused.

The browser panel accepted energy-only preference weights, restored equal weights, and displayed all four objective alternatives with distance/time/energy and a hard battery budget. The 45% demonstration button is provided for repeatable preemptive charging.

These are assisted simulation tests with explicit, uncalibrated energy coefficients and a 25% prediction allowance; they are not a hardware endurance/balance/sensing guarantee or an exhaustive Pareto frontier. Original STL/URDF hashes remain unchanged. Final model/code hashes and detailed results are in `multiobjective_validation_manifest.json`.
