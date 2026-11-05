# Enhanced MuJoCo hexapod mission

Run `./run_simulation.sh` from this folder. Dependencies are in `requirements.txt`.
The live Desktop project was also updated at `/home/user123456/Desktop/llmforhexapod`.

## Controls

- **C**: chase / overview / free orbit / close-up camera.
- **M**: transform between wheels and six legs.
- **B**: set battery to 18%; pulsing red beacon and charger diversion.
- **1–4**: autonomous dispatch to the four places.
- **0**: go to the central charging station.
- **K**: manual mode; WASD/arrows drive. **R** resets to base.

At 35% or lower the charger takes priority over destination dispatch. Charging occurs
at the center pad [0, 1.2], entered through [0, -4]. The robot charges gradually to
100%, holds green for 2.4 seconds, then resumes its interrupted destination/scan.

## Design and navigation changes

The original Fusion STL chassis, links, and top-cover silhouette are retained.
The added battery cassette has orange end caps, a silver housing, vents, latches,
handles, a lid seal, charge LEDs, and a raised beacon. Cover supports, fasteners,
service panels, perimeter landscaping, and four site identity pylons add detail.

A* routes derive from actual static MuJoCo collision geometry, inflated by a
1.82m swept leg radius. The controller checks braking clearance before motion,
turns on the spot for large heading changes, and keeps physical contacts enabled.
Blocked routes produce a navigation hold instead of skipping an objective or
blindly reversing. Scene preparation repositions 56 roadside/site assemblies to
reserve continuous walking lanes, with checks against overlapping other props.

The tripod gait uses inverse kinematics, planted stance feet, a 60% stance duty,
and a 13cm swing lift with smooth endpoints. Acceleration and yaw-rate changes
are limited. Ideal limb gravity compensation and ground-clearance constraints
prevent the assisted transformation sequence from pushing feet below the floor. Original CAD meshes and the original URDF remain one level up.

## Scope

This remains a **navigation and design preview with assisted chassis velocity,
height, and attitude control**. It is not a torque-feasible balance controller or
hardware locomotion validation. The visible LiDAR is illustrative; routing uses
the known static scene. Battery drain and charging are simulated state values.
The planner must be rebuilt if static obstacles are edited during a run.

## Rebuild and validate

Run `python3 generate_multi_place_scene_xml.py` to rebuild the scene and clearance layout.

```bash
MUJOCO_GL=egl python3 preview_multi_place_mission.py --headless --steps 60000 --battery-test-step 700 --report outputs/final_mission_validation.json
MUJOCO_GL=egl python3 preview_multi_place_mission.py --headless --steps 15000 --dispatch 4 --battery-test-step 7000 --report outputs/final_desert_recharge.json
```

Reports count physical robot/obstacle contacts at every physics substep, including
legs, feet, body, and battery enclosure. Ground support contacts are expected and
excluded. Validation reports and previews are in `outputs/`.

Original Desktop files were backed up under
`/home/user123456/Desktop/llmforhexapod/backups/20261021_design_navigation/`.
