# Hybrid hexapod demonstration and path finding

Run `./run_simulation.sh`. The restored demonstration robot waits at base for a destination.
It has the earlier orange/charcoal cover, battery cassette, five-bar gauge, status
beacon, hook pockets, articulated legs, and four wheels.

## Demonstration controls

- **1 / 2 / 3 / 4**: Forest / Quarry / Marsh / Desert destination.
- **M**: manually transform to the other locomotion mode. This overrides automatic mode selection.
- **A**: restore automatic terrain selection.
- **C**: cycle chase / overview / free orbit / close-up views.
- **P**: fastest estimated travel / shortest distance.
- **X**: cancel the current destination.
- **B**: test 18% battery; pulsing red beacon and autonomous charger return.
- **0**: request the center charger.

In automatic mode the robot drives on smooth ground and switches to legs before
forest, quarry, mud, or sand regions. It brakes to a standstill, unlatches the hooks,
unfolds and plants the six feet, and raises the body off the wheels. On leaving
rough terrain it lowers onto the wheels, folds the legs, and engages the latches.
The visible transition takes about 2.8 seconds. Hysteresis and forward terrain
lookahead prevent repeated mode switching near region boundaries.

## Path finding

Choose a place and the robot plans from its current position. A 1.5-second map
preview shows the complete route before movement; the camera then returns to the
previous chase/close-up view. Cyan route sections indicate driving, amber sections
walking, purple the traveled path, and orange the destination. The overlay shows
mode, transformation phase, route length, estimated time, remaining distance, and battery.

The robot follows the route, stops at the destination, and waits for another input.
There is no automatic site tour or mandatory return to base. New destinations and
manual mode changes trigger fresh planning after stopping. **P** compares shortest
geometry and heading/terrain-aware travel-time candidates.

Planning uses a 0.25 m, eight-neighbor A* grid, the full 1.82 m swept robot radius,
and an additional 0.12 m planning margin for tracking. Continuous shortcuts and
live braking clearance are checked against the known static collision map.
The fastest-time model uses 0.85 m/s driving, 0.42 m/s walking, turning time, and
3.6 seconds per mode change (2.8 seconds animation plus brake/restart allowance).
The estimate and grid optimum are planning models, not guarantees of globally
minimum time on hardware. Arrival tolerance is 22 cm; tested stops are near 10 cm.

Battery depletion prioritizes the charger. The physical beacon pulses red at low
charge, amber during charging, and green at full charge. The robot holds 100% for
2.4 seconds, then generates a new route to the interrupted or queued destination.
Charging is intentionally accelerated for demonstration. The charger is approached/departed
through its front opening; visible plaza curbs are included as collision obstacles.

## Restored design and realism improvements

- Four 300 mm tires with beadlock details, 20 tread blocks each, a wider axle stance,
  and visible suspension links/dampers. Wheel angular speed follows velocity and turning commands.
- Separate battery casing, vents, lid seal, handles, latches, visible gauge, and beacon.
- Femur hook tips align with the side-pocket sockets in the folded pose.
- Foot clearance is maintained during folding; grounded IK is used in walking mode.
- Explicit prototype body/wheel inertias prevent collision-envelope volumes from
  producing unrealistic masses. Limb masses/inertias derive from the supplied asset.
- Scanner hardware is retained; the oversized decorative laser fan is removed.

Original STL and URDF files are unchanged. The demonstration deliberately adds
procedural wheels and detailing, as authorized for this restored presentation.
The reduced actuator copy remains under `derived_meshes/`. Current provenance:
`outputs/asset_integrity.json`. The earlier mesh-only model remains preserved as
`source_only_hexapod.xml`, viewable with `./view_source_asset.sh`.

**Simulation scope:** chassis velocity/height/attitude and transformation joints
are assisted, with ideal limb gravity compensation. Suspension links are visual,
not validated spring/damper physics. Terrain classes select locomotion modes;
this does not simulate deformable mud, sand traction, or hardware balance. The
scanner is illustrative; navigation uses the known static collision map.

## Validation and previews

```bash
python3 preview_multi_place_mission.py --headless --steps 46000 --sequence 1,2,3,4,1 --report outputs/hybrid_destination_sequence.json
python3 preview_multi_place_mission.py --headless --steps 18000 --dispatch 2 --stop-on-arrival --battery-test-step 700 --report outputs/hybrid_recharge.json
python3 preview_multi_place_mission.py --headless --steps 700 --commands outputs/hybrid_manual_events.json --report outputs/hybrid_manual_validation.json
MUJOCO_GL=egl python3 render_hybrid_showcase.py
```

`--sequence` and scripted inputs are test-only options; normal startup waits for
the user. Current reports use `hybrid_*`; earlier walking-only reports describe
previous versions. The wheel, leg, red-battery, and transformation GIF previews
are in `outputs/`. Backups of the mesh-only/path-finding version are in
`backups/before_hybrid_demo/`.

Optional independent planner verification (requires SciPy): `python3 validate_hybrid_routes.py`.
