# Destination-driven path finding validation

- Base and four places: all 20 ordered endpoint pairs planned in both modes; every returned segment passed continuous swept-footprint clearance checks.
- Independent SciPy Dijkstra comparison: distance A* and heading-aware time A* matched optimal grid costs for base-to-forest (47.995689 m and 118.987839 s before continuous shortcuts).
- Physical dispatch sequence 1 -> 2 -> 3 -> 4 -> 1: all arrivals completed, with approximately 10 cm position errors and no forced return-to-base or inspection loops.
- Mid-trip destination change, P mode switch, X cancellation, then Place 3: passed; final mode shortest, destination 3 reached.
- Low-battery interruption: center charging, then a fresh route to Place 2 and arrival passed.
- Arrival hold: Place 4 remained stopped after arrival instead of starting another mission.
- Idle startup: 16 simulated seconds waiting without a route or departure passed.
- Blocked target: explicit no-safe-route state; no substitute destination or robot teleport.
- All physical runs: zero obstacle contacts, obstacle penetrations, navigation failures, or solver warnings, with finite state throughout.
- Robot scene hash exactly matches the previous walking-only version; route visualization is separate viewer geometry.

Optimality is relative to the conservative 0.25 m grid and the stated static travel-time model. Continuous shortcuts are validated for clearance. Arrival tolerance is 22 cm. Original invisible foot support contacts retain solver compliance; chassis motion and limb stabilization remain assisted.
