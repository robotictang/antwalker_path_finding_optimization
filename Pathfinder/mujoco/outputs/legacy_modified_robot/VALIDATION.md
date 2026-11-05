# Simulation validation

- Complete four-site loop and return to base: passed; 60,000 frames / 960 simulated seconds.
- Forced 18% battery return, recharge, and mission resumption: passed.
- Natural low-battery return during the full mission: passed; two charging cycles total.
- Interrupted desert scan, recharge, and resume remaining scan sectors: passed; 15,000 frames / 240 simulated seconds.
- Physical obstacle contacts and penetrations: zero in both final runs, checked at every physics substep.
- Navigation failures, safety holds, and MuJoCo solver warnings: zero in both runs.
- All model positions and velocities remained finite.
- Minimum foot underside height in active walking: approximately 13 mm above the base ground plane (decorative pavement tops are 8 mm).
- Additional planner test: an injected physical roadblock produced a verified detour with continuous segment clearance.

This validates the configured static scene and assisted navigation controller. Chassis
motion, body stabilization, limb gravity compensation, and transformations remain assisted;
these checks do not establish torque feasibility or balance on physical hardware.

See the JSON reports for exact values and `validation_manifest.json` for source hashes.
