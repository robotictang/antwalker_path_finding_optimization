"""Read source declarations and compiled MuJoCo parameters, without calibration."""
import hashlib,json,re,sys
from pathlib import Path
import xml.etree.ElementTree as ET
B=Path(__file__).resolve().parents[1];ROOT=B.parent;M=ROOT/'workbench/mujoco'
sys.path.insert(0,str(M))
import mujoco
source=ROOT/'hexapod.urdf'
if not source.exists():source=ROOT/'workbench/hexapod.urdf'
urdf=ET.fromstring(re.sub(r'<!--.*?-->','',source.read_text(),flags=re.S))
scene=M/'hybrid_hexapod_multi_place.xml';model=mujoco.MjModel.from_xml_path(str(scene))
robot=model.body('robot').id
record=dict(source_robot_name=urdf.get('name'),source_urdf_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    scene_sha256=hashlib.sha256(scene.read_bytes()).hexdigest(),
    source_total_link_mass_kg=sum(float(x.get('value')) for x in urdf.findall('.//inertial/mass')),
    source_base_mass_kg=float(urdf.find("link[@name='base_link']/inertial/mass").get('value')),
    source_revolute_joints=len(urdf.findall("joint[@type='revolute']")),
    source_motor_comment='RS04, 60 Nm peak and 20 rad/s declared in URDF comment; not independently measured',
    mujoco_model_name=ET.parse(scene).getroot().get('model'),mujoco_robot_subtree_mass_kg=float(model.body_subtreemass[robot]),
    mujoco_base_mass_kg=float(model.body_mass[robot]),mujoco_total_joints=int(model.njnt),mujoco_actuators=int(model.nu),
    mujoco_timestep_s=float(model.opt.timestep),mujoco_gravity=model.opt.gravity.tolist(),
    gravity_compensated_bodies=[model.body(i).name for i in range(model.nbody) if model.body_gravcomp[i]>0],
    mass_scope='Different source and demo mass models; no hardware weighing or inertia validation available.',
    motor_validation='Configured torque limits are not hardware torque-speed, thermal or efficiency measurements.')
(B/'results/model_audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
