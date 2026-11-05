# Restored hybrid demonstration validation

The final scene completed destinations 1 → 2 → 3 → 4 → 1, including an automatic charging diversion and resumed mission, in 624.5 simulated seconds. It completed 11 terrain-driven transformations. Maximum arrival error: 0.100 m.

All simulation checks reported zero obstacle contacts, collision substeps, safety holds, route failures, and solver warnings, with finite states and positive foot clearance. Manual transformations passed in both directions, including mode changes during an active route. Transformation displacement stayed below 0.02 m.

All 20 ordered base/destination pairs passed both route modes. Independent Dijkstra comparisons matched distance and heading/terrain travel-time A* costs on the conservative grid. All route segments were checked continuously. The visible plaza curbs are included in collision planning.

The five-bar battery gauge, red low-battery pulse, amber charging, and full green indication passed. A separate forced-low-battery run charged and resumed Place 2 successfully.

Original six STL files and source URDF match their preserved SHA-256 fingerprints. Current code/model hashes and detailed report references are in `hybrid_validation_manifest.json`; individual results are in `hybrid_destination_sequence.json`, `hybrid_recharge.json`, `hybrid_manual_validation.json`, `hybrid_moving_mode_validation.json`, `hybrid_planner_validation.json`, and `hybrid_lights_validation.json`.

This is a presentation simulation: chassis movement/attitude and transformation joints are assisted, with ideal gravity compensation. Suspension detailing is visual; deformable terrain and hardware balance are not validated. Fastest routes are estimated using the declared grid and locomotion cost model.
