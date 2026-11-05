# Supplied-mesh-only hexapod

Robot visuals now use the source files in `../meshes/` directly, with the supplied
URDF transforms, millimetre-to-metre scale, and colors. No STL files were edited,
simplified, regenerated, or replaced. No extra battery box, wheels, lights, hooks,
antenna, scanner, feet, fasteners, or cover panels are drawn. Features already
contained inside `top_cover.stl` remain because they are part of the supplied mesh.
The environment is retained. Invisible collision proxies come from the supplied URDF.

## Inspect the source assembly

```bash
./view_source_asset.sh
```

This is a static inspection viewer. It does not run mission control or physics.
The source URDF places base, cover, and six coxa/femur/tibia assemblies (20 mesh visuals).

## Reported errors and omissions

`./run_simulation.sh` now raises `MissingAssetError` and exits before launching the
hybrid controller: no wheel mesh/assembly or wheel joints are provided.

`rs04_actuator.stl` is present but has no visual placement in the supplied URDF.
It also contains 294,305 triangles, exceeding the installed MuJoCo STL decoder's
200,000-triangle limit. It is not placed, simplified, or substituted.

Foot spheres in the source URDF are collision-only; no extra foot visuals are added.
The supplied top cover is loaded unchanged; no separate battery enclosure is invented.

Exact source paths, SHA-256 hashes, and errors: `outputs/asset_integrity.json`.
Missing/corrupt source meshes fail immediately. Source comments with invalid XML
hyphen sequences are ignored in memory when reading the assembly; the URDF itself
is unchanged. Previous modified-robot reports are archived under
`outputs/legacy_modified_robot/` and do not validate this source-only model.

Rebuild: `python3 generate_multi_place_scene_xml.py`.
Preview: `MUJOCO_GL=egl python3 preview_source_asset.py --render outputs/source_mesh_only.png`.
