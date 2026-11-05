# Road demonstration validation

The four-destination run completed Quarry → Marsh → Desert → Forest in 507.4 simulated seconds, with 23 automatic transformations and 2 charging interruptions/resumptions. There were zero obstacle contacts, penetrations into blocking obstacles, route failures, or solver warnings. Two protective clearance stops replanned successfully; the robot reached every destination.

The separate shortest-route Desert run also detected roadwork, diverted below 20%, charged to 100%, resumed, and arrived with zero obstacle contacts, route failures, or safety stops. Both runs reached 1.65 m/s. Manual transforms passed in both directions using the new keypad input mapping.

All 20 ordered base/destination pairs passed both objectives, including continuous clearance checks. Weighted A* costs matched independently constructed Dijkstra graphs. The final time comparison includes the distance candidate after continuous simplification. Quarry baseline alternatives: 47.0 m / 87.8 s shortest; 71.5 m / 73.1 s fastest estimate. Forest shares the same winning corridor for both objectives; the interface reports identical results honestly.

Shallow terrain support contact compliance stayed within 3 mm in the tested runs (minimum foot-to-surface values are recorded). Chassis movement/attitude and transformations remain assisted. This is not proof of hardware balance, real sensing, tire traction, or real battery endurance.

The final express-road asphalt/markings are visual additions. A compiled comparison confirmed that all tested collision geometry/transforms, body inertias, and actuator gains/limits remained unchanged. The final model also passed the manual transformation smoke test.

Browser UI checks verified destination dispatch, route objective switching, the battery test, and reset (idle at depot, 100%, wheels/AUTO, staged obstacle removed). The control panel remains available at http://127.0.0.1:8767 .

Original six STL files and source URDF match preserved SHA-256 fingerprints. Detailed results and final source/model hashes are in `road_validation_manifest.json`. Actual route alternatives are in `road_route_comparison.json`, with exported `shortest_vs_fastest.png`.
