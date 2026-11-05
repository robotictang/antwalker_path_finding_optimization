# Hexapod road, charging, and route comparison demo

Run `./run_simulation.sh`, then open **http://127.0.0.1:8767** for the mission control panel.
The robot waits at the depot. Choose Forest, Quarry, Marsh, or Desert with the buttons.
The scene includes four gravel/rut road sections, shallow physical gravel pads,
12 additional small rocks and 12 cones, and a staged roadwork obstruction.

## Controls without the former viewer shortcut conflicts

Use the button panel, or these **numeric keypad** keys (not the top-row numbers):

| Key | Action |
| --- | --- |
| KP1–KP4 | Choose destination 1–4 |
| KP0 | Center charging station |
| KP5 | Toggle shortest / fastest |
| KP6 | Cycle camera |
| KP7 | Manual transformation override |
| KP8 | Restore automatic terrain selection |
| KP9 | Battery test: 18% |
| KP decimal | Cancel mission |

The same keypad controls work while the browser panel is focused, including with
Num Lock off. Regular letters and top-row numbers are no longer mission controls;
MuJoCo retains its normal shortcuts. The panel has explicit **Follow shortest**,
**Follow fastest**, and **Reset demonstration** buttons. Reset returns to the depot,
restores 100% battery, removes staged roadwork, and repeats the accelerated first cycle.

## Automatic transformation and faster movement

Automatic terrain selection is the default. The depot starts on a gravel section,
so the first dispatch visibly unfolds the legs before traveling. Smooth sections
use wheels; rough road, forest, quarry, marsh, and sand sections use legs. Terrain
lookahead and hysteresis avoid rapid toggling at boundaries. The robot brakes to a
standstill, transforms over 3.6 seconds, and continues. The camera automatically
shows a close-up during each transformation and then restores the previous view.
Driving speed is **1.65 m/s** (previously 0.85); walking is **0.75 m/s** (previously 0.42).
Acceleration and braking limits are increased together with the safety braking model.

## See both objectives, rather than only a mode label

Every plan compares both objectives from the same current position and heading.
The MuJoCo view and browser map show **pink = shortest distance**, **green = fastest
estimated time**, **amber = walking sections**, and **purple = traveled path**.
Distance, time, walking distance, and mode changes are shown for both alternatives.
The 3-second overview preview precedes movement. The robot stops at the requested
place and waits; no automatic site tour runs in normal operation.

The previous clear-straight-line shortcut incorrectly skipped terrain-aware time
search. Fastest planning now searches alternatives whenever the direct path includes
rough terrain, and compares the simplified distance candidate under the same time
model. Identical objectives are reported honestly when the same corridor wins.

Example from the depot to Quarry, before roadwork or battery interruptions:

| Objective | Distance | Estimated travel | Walking | Mode changes |
| --- | ---: | ---: | ---: | ---: |
| Shortest | 47.0 m | 87.8 s | 26.7 m | 7 |
| Fastest | 71.5 m | 73.1 s | 10.6 m | 3 |

The longer smooth-ground route saves approximately 14.7 seconds in this model.
`outputs/shortest_vs_fastest.png` and `outputs/road_route_comparison.json` show the
actual alternatives. Switching objectives replans from the robot's current position,
so later values differ from this fixed-start example.

Planning uses a 0.25 m eight-neighbor A* grid, 1.82 m full-leg swept radius, 0.12 m
tracking margin, continuous segment checks, and a braking clearance guard. Time cost
includes terrain speeds, turns, and 4.8 seconds per transformation including stop/start.
Fastest is relative to this model and conservative grid; it is not a hardware guarantee.

## Obstacle avoidance while following the displayed route

Known rocks, cones, buildings, curbs, and other blocking geometry shape the initial
route. Added debris is positioned without disconnecting the destination network or
forcing excessive map-wide detours.

A physical striped roadwork barrier is staged on the planned lane during the initial
preview, only after a safe replacement path is verified. The initial map predates that
roadwork. At 8 m range, a simulated proximity detector updates the map, announces
**OBSTACLE DETECTED**, brakes, and plans a checked detour. The previous route is dashed
red and the replacement route is displayed before movement resumes. This is an explicit
roadwork/proximity demonstration, not an actual LiDAR perception implementation.
A protective clearance stop also triggers a fresh plan rather than getting stuck.

## Battery below 20% interrupts the destination

Below **20%**, the red beacon pulses and the interface announces the charging diversion.
The robot stops following the destination route, previews an alternative route through
the station's front entrance, charges to 100%, holds green for 2.4 seconds, then plans
an entirely new route from the station to the interrupted destination.

The **first battery cycle is accelerated** at 3.5 percentage points per meter so the
interruption appears on the first trip. Subsequent cycles use 0.55 points/m; emergency
return uses 0.22 points/m. Active travel adds 0.05 points/s. Charging is accelerated at
22 points/s. These are presentation settings, not an energy prediction for hardware.
The panel displays the active consumption mode. No manual battery test is necessary.

## Original assets and simulation scope

Original six STL files and source URDF remain unchanged. Procedural wheels, battery
cassette, status lighting, cover details, hooks and visual suspension are demonstration
additions. The actuator uses the previously authorized reduced mesh in `derived_meshes/`.
The source-only model remains in `source_only_hexapod.xml` / `./view_source_asset.sh`.

Chassis velocity, height and attitude and transformation joints are assisted, with
ideal limb gravity compensation. The gait samples shallow pad height and keeps feet
referenced to the terrain. Suspension links, individual gravel stones and ruts are
visual details; there is no deformable mud/sand or validated hardware balance model.
The collision solver permits millimeter-scale support contact compliance.

## Reproduce validation

```bash
python3 preview_multi_place_mission.py --headless --steps 50000 --sequence 2,3,4,1 --report outputs/road_full_validation.json
python3 preview_multi_place_mission.py --headless --steps 24000 --dispatch 4 --route-mode shortest --stop-on-arrival --report outputs/road_shortest_validation.json
python3 compare_road_routes.py
python3 validate_hybrid_routes.py   # optional SciPy independent Dijkstra comparison
python3 render_route_comparison.py # optional matplotlib exported comparison
```

`--sequence` is test-only. `--no-roadwork` disables the staged obstruction for baseline
checks; `--no-panel` disables the local HTTP panel; `--control-port` changes its port.
Scripted key events use `KP1`…`KP9`, `KP0`, `KP_DECIMAL`, `SHORTEST`, or `FASTEST`.
Scene generation must run from this directory: `python3 generate_multi_place_scene_xml.py`.
Previous working code/model are preserved in `backups/before_road_demo/`.
