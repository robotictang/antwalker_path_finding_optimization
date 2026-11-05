# Walking-only hexapod: original meshes, replacement actuators

Launch the active mission with `./run_simulation.sh`. Inspect a stationary pose with
`./view_source_asset.sh`. Wheels are intentionally excluded while under development.

## Geometry policy

- Original files in `../meshes/` and `../hexapod.urdf` are untouched.
- Base, top cover, coxa, femur, and tibia visuals load those exact source meshes,
  with the original URDF positions, rotations, colors, and unit scale.
- Only the actuator is replaced: `derived_meshes/rs04_actuator_mujoco.stl` is a
  30,000-triangle simplified copy of the 294,305-triangle source. Its original file
  remains unchanged. Provenance and hashes are in `derived_meshes/actuator_provenance.json`.
- The source URDF has no actuator visual mounts, so the replacement motors are
  placed at its 18 existing joint pivots, with shaft axes aligned to the joint axes.
- No extra wheel, battery enclosure, cover, light, scanner, hook, antenna, foot,
  panel, handle, or fastener visuals are added. Features already embedded in the
  supplied top-cover mesh remain unchanged. Original foot spheres are invisible
  collision proxies, as in the source URDF.
- Missing/invalid source files, missing replacement files, or mismatched actuator
  provenance raise `MissingAssetError`. Wheels are not required in walking-only mode.

## Controls

- **C**: cycle chase / overview / free orbit / close-up cameras.
- **B**: set battery to 18%; autonomous return to the center charger.
- **1–4**: dispatch to a place. Charging has priority when battery is low.
- **0**: return to the charger immediately.
- **M**: reports that wheels are excluded; robot continues walking.

Battery and mission status appear in the viewer overlay, preserving the robot's
original appearance. The battery charges gradually to 100%, holds for 2.4 seconds,
then resumes the interrupted mission. Each site has its original inspection loop.

## Controller scope

Navigation uses the known static collision scene, A* with a 1.82 m swept leg radius,
and a braking clearance check. Tripod IK keeps stance feet planted and lifts swing
feet with smooth endpoints. Chassis velocity/attitude and limb gravity compensation
remain assisted; this preview does not validate hardware balance or torque feasibility.
Source link masses/inertias and 60 Nm joint force limits are retained. The environment
and its previously reserved walking lanes remain in place.

## Rebuild and validation

Rebuild the scene with `python3 generate_multi_place_scene_xml.py`.
The actuator rebuild script is `derived_meshes/build_actuator.py`; it requires
`trimesh` and `fast-simplification` only for rebuilding, not for simulation.

```bash
python3 preview_multi_place_mission.py --headless --steps 115000 --stop-after-tour --battery-test-step 700 --report outputs/walking_full_validation.json
python3 preview_multi_place_mission.py --headless --steps 19000 --dispatch 4 --battery-test-step 6500 --report outputs/walking_desert_charge.json
```

Current source hashes: `outputs/asset_integrity.json`. Current walking-only test
reports: `outputs/walking_*`. Older hybrid and static-only results describe previous
versions and do not validate this controller.
