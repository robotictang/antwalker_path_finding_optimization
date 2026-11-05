# Destination-driven hexapod path finding

Run `./run_simulation.sh`. The robot waits at base until you select a destination.

1. Press **1** Forest, **2** Quarry, **3** Marsh, or **4** Desert.
2. The simulation computes a safe route from the robot's current position and shows
   it for 1.5 seconds before moving. Cyan arrows show the planned route; purple
   shows the traveled path; orange marks the selected destination.
3. The robot follows that route, reports arrival, stops, and waits for your next
   destination. It does not automatically tour sites or return to base.

The overlay shows the requested place, state, route length, estimated travel time,
remaining distance, and battery. Changing the destination stops the robot and plans
from its new position. **C** cycles cameras; **X** cancels a trip.

## Shortest and fastest routes

**P** switches between **FASTEST** (default) and **SHORTEST**:

- Shortest minimizes route distance.
- Fastest minimizes estimated travel time, including heading changes at the
  configured 0.42 m/s walking speed and 1 rad/s turn limit. It compares the distance
  and time candidates and selects the lower estimated time.

A* searches an eight-neighbor, 0.25 m grid, conservatively inflated for the full
1.82 m swept robot radius. The distance and heading-aware time searches have been
checked against independent SciPy Dijkstra results. Continuous shortcuts are
accepted only after exact segment-to-obstacle clearance checks. Braking clearance
is checked during motion, and any needed replan updates the displayed route.

Optimality applies to that grid and static travel-time model. The estimated fastest
route is not a guarantee of globally minimum time on physical hardware. Shortest
and fastest often select the same route; turns can make them differ. Arrival uses
a 22 cm tolerance, with tested stops approximately 10 cm from the target.

## Battery behavior

**B** tests an 18% battery state; **0** requests the center charger. At 35% or lower,
charging has priority. The charger is entered/exited through its front opening.
After charging to 100% and holding for 2.4 seconds, the robot generates a fresh
route to the interrupted or newly queued destination. Cancelling a charging return
clears the queued place while preserving the charger trip.

## Robot asset policy

Original files in `../meshes/` and `../hexapod.urdf` are unchanged. Original base,
cover, coxa, femur, and tibia meshes use the supplied URDF placements, colors, and
unit scale. Only the authorized actuator uses a 30,000-triangle reduced copy under
`derived_meshes/`, mounted at the 18 existing joint pivots. No wheels or other
robot visual parts were added. Route lines and markers are viewer annotations,
separate from the robot and physics. **M** reports that wheels are unavailable.

Missing source/replacement files or invalid actuator provenance raise errors.
Source hashes: `outputs/asset_integrity.json`; actuator provenance:
`derived_meshes/actuator_provenance.json`. A static model viewer remains available
with `./view_source_asset.sh`.

Chassis motion/attitude and limb gravity compensation remain assisted. Ground
support contacts are expected; obstacle contacts are tracked separately. This is
a static-map navigation preview rather than a hardware balance validation.

## Reproduce validation

```bash
python3 preview_multi_place_mission.py --headless --steps 50000 --sequence 1,2,3,4,1 --report outputs/destination_sequence.json
python3 preview_multi_place_mission.py --headless --steps 24000 --dispatch 2 --stop-on-arrival --battery-test-step 700 --report outputs/destination_recharge.json
python3 preview_multi_place_mission.py --headless --steps 22000 --dispatch 1 --stop-on-arrival --commands outputs/destination_input_events.json --report outputs/destination_input_validation.json
```

`--sequence` and `--commands` are explicit test inputs; neither is active during
normal startup. Reports use the `destination_*` prefix. Previous automatic-tour
reports describe older controller behavior.
