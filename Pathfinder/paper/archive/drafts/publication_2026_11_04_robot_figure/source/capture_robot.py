"""Capture the exact primary model in its walking initialization, without stepping."""
from pathlib import Path
import os,sys,json,hashlib,math
os.environ.setdefault('MUJOCO_GL','egl')
B=Path(__file__).resolve().parents[1];ROOT=B.parent
sys.path.insert(0,str(ROOT/'workbench/mujoco'))
import numpy as np
import mujoco
from PIL import Image
from hybrid_locomotion import HybridLocomotion
from hybrid_demo_design import WALK_HEIGHT
from road_demo import ground_height

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
campaign=json.loads((B/'raw_study/primary.json').read_text())
case=campaign['cases'][0]
source=ROOT/'workbench/mujoco/outputs/research'/case['model_xml']
assert sha(source)==case['model_xml_sha256']
model=mujoco.MjModel.from_xml_path(str(source));data=mujoco.MjData(model)
loc=HybridLocomotion(model,data)
initial=np.asarray(case['start'],float);yaw=math.pi/2
data.qpos[:3]=[*initial,WALK_HEIGHT+float(ground_height(initial))]
data.qpos[3:7]=[math.cos(yaw/2),0.,0.,math.sin(yaw/2)]
loc.mode='legs';loc.override='legs';loc.height=WALK_HEIGHT
pose=loc.gait.targets(initial,yaw,float(data.qpos[2]),0.,0.)
data.qpos[loc.qids]=pose;data.ctrl[loc.aids]=pose
mujoco.mj_forward(model,data)
camera=mujoco.MjvCamera();camera.lookat[:]=[*initial,.62]
camera.distance=4.3;camera.elevation=-29.;camera.azimuth=120.
ground=model.geom('research_ground').id
# Isolate the unchanged robot geometry in the renderer, with a neutral floor.
environment=(model.geom_bodyid==0)&(np.arange(model.ngeom)!=ground)
model.geom_group[environment]=5
model.geom_rgba[ground]=[.90,.90,.90,1.]
model.light_active[:]=False
model.vis.headlight.ambient[:]=[.65,.65,.65]
model.vis.headlight.diffuse[:]=[.35,.35,.35]
model.vis.global_.offwidth=2400;model.vis.global_.offheight=1500
opt=mujoco.MjvOption();opt.label=mujoco.mjtLabel.mjLABEL_NONE
opt.geomgroup[5]=0
with mujoco.Renderer(model,height=1500,width=2400) as renderer:
    renderer.update_scene(data,camera=camera,scene_option=opt)
    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION]=False
    renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
    Image.fromarray(renderer.render()).save(B/'figures/simulation_overview.png')
assert data.time==0.
provenance=dict(source=str(source),source_model_sha256=sha(source),source_case=case['id'],
    copied_asset='figures/simulation_overview.png',sha256=sha(B/'figures/simulation_overview.png'),
    image_size_px=[2400,1500],capture='Direct MuJoCo EGL static render; no physics steps, viewer or HTTP server.',
    state='Walking initialization copied from research/execution.py; not an observed mission outcome.',
    camera=dict(lookat=camera.lookat.tolist(),distance=camera.distance,elevation=camera.elevation,azimuth=camera.azimuth),
    data_time=float(data.time),qpos=data.qpos.tolist(),
    visualization_changes=['Offscreen resolution 2400 by 1500','Camera framing','Labels disabled','Reflections and shadows disabled','World obstacle geometry hidden in renderer','Neutral gray floor display color','Even headlight illumination in place of world lights'],
    modification='No image editing, cropping, recoloring, annotation or AI generation; native renderer output.',
    manuscript_width_inches=4.5,role='Robot model illustration, not physical validation or a locomotion result.')
(B/'results/screenshot_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print(json.dumps({k:provenance[k] for k in ['source_case','sha256','image_size_px','data_time']},indent=2))
