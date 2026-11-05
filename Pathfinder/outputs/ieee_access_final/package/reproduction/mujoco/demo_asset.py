"""Integrity report for the user-authorized restored demonstration model."""
from pathlib import Path
import json
from strict_asset import validate_sources as validate_sources,write_report as source_report


def write_report(path):
    report=source_report(path)
    report['mission_mode']='hybrid demonstration: wheels on smooth terrain, legs on rough terrain'
    report['visual_policy']='Prior demonstration design restored with procedural wheels, battery enclosure/status lights, hook latches, cover detailing, and scanner hardware. Original source STL and URDF files are unchanged.'
    report['demo_additions']=['four 300 mm tires with beadlock rims and tread','wider axle stance and visual suspension links','top battery cassette with latches, vents, handles and 5-bar charge gauge','pulsing low-battery beacon','phased wheel/leg transformation']
    report['foot_policy']='Restored visible rubber feet and matching contact spheres are part of the demonstration assembly.'
    report['actuator_mounting']='Restored demonstration joint mounts use the authorized reduced RS04 mesh.'
    report['dynamics_scope']='Assisted chassis velocity/height/attitude and kinematic transformation joints; ideal limb gravity compensation. Visual suspension linkage is not a validated suspension model.'
    Path(path).write_text(json.dumps(report,indent=2))
    return report
