# Hexapod assembly

`Body+(backup+Assembly)+Copy.obj` is the original Autodesk assembly export. Its SHA-256 and the bounding boxes of the chassis and selected leg groups are in [cad-audit.json](cad-audit.json). The export is about 987 MiB and is kept as a local source asset. Its referenced MTL file was absent from the folder at intake.

Run this from `IEEE_Journal_ver` to regenerate the audit.

```bash
.venv/bin/python -m thermal_pathfinder.cad_audit 'Hexapod_Model/Body+(backup+Assembly)+Copy.obj' --output Hexapod_Model/cad-audit.json
```

The simulation uses a parametric model of this assembly. Export coordinates are interpreted as millimetres. The main chassis plate spans 840 × 1000 mm, and the three leg mounts on each side are spaced about 320 mm apart along the body. The pilot uses a 410 mm lateral hip offset and effective link lengths of 157, 550, and 740 mm. The lateral offset and link lengths are provisional estimates informed by the assembly bounds and the earlier project's kinematics. The OBJ provides geometry and group names. Joint centres and axes need verification against the original CAD constraints.

[model.py](../thermal_pathfinder/model.py) defines the simplified rigid links, foot spheres, assumed link masses and inertias, joint limits, and torque limits. The simulator derives inertias from the primitive collision shapes and assigned masses. Terrain collision is enabled for the robot geometry. Self-collision is outside this pilot. The MJCF is generated from Python and runs independently of the source OBJ.
