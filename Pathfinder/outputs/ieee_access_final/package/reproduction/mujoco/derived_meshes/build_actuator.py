"""Rebuild the sole authorized mesh replacement. Requires trimesh and fast-simplification."""
from pathlib import Path
import hashlib
import json
import trimesh

root=Path(__file__).resolve().parents[2]
source=root/'meshes/rs04_actuator.stl'
model=trimesh.load_mesh(source,process=True)
replacement=model.simplify_quadric_decimation(face_count=30000)
destination=Path(__file__).with_name('rs04_actuator_mujoco.stl')
replacement.export(destination)
report=dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    source_triangles=len(model.faces),replacement=str(destination),
    replacement_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
    replacement_triangles=len(replacement.faces),source_bounds_mm=model.bounds.tolist(),
    replacement_bounds_mm=replacement.bounds.tolist(),
    method='Quadric edge-collapse simplification of the supplied actuator only; no source files modified.')
destination.with_name('actuator_provenance.json').write_text(json.dumps(report,indent=2))
print(destination)
