#!/usr/bin/env python3
"""Static inspection of supplied mesh visuals and the authorized actuator replacement."""
import argparse
from pathlib import Path
import time
import mujoco
import mujoco.viewer
from strict_asset import validate_sources, write_report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',type=Path)
    args=parser.parse_args()
    validate_sources()
    root=Path(__file__).resolve().parent
    write_report(root/'outputs/source_only_integrity.json')
    m=mujoco.MjModel.from_xml_path(str(root/'source_only_hexapod.xml'))
    d=mujoco.MjData(m)
    for side in ('L','R'):
        for index,position in zip(('F','M','R'),(-.45,0,.45)):
            prefix=side+index
            for name,value in [('hip',position if side=='L' else -position),('femur',.2),('tibia',-1.3)]:
                joint=m.joint(prefix+'_'+name+'_joint')
                d.qpos[int(joint.qposadr[0])]=value
    mujoco.mj_forward(m,d)
    camera=mujoco.MjvCamera()
    camera.lookat[:]=[0,-20,.7]
    camera.distance=5.
    camera.azimuth=130.
    camera.elevation=-25.
    option=mujoco.MjvOption();option.geomgroup[3]=0
    if args.render:
        from PIL import Image
        renderer=mujoco.Renderer(m,800,1200)
        renderer.update_scene(d,camera=camera,scene_option=option)
        Image.fromarray(renderer.render()).save(args.render)
        renderer.close()
        return
    print('STATIC ASSET INSPECTION. Source meshes + authorized replacement motors. Run ./run_simulation.sh for walking-only missions.',flush=True)
    with mujoco.viewer.launch_passive(m,d) as viewer:
        viewer.cam.lookat[:]=camera.lookat
        viewer.cam.distance=camera.distance
        viewer.cam.azimuth=camera.azimuth
        viewer.cam.elevation=camera.elevation
        viewer.opt.geomgroup[3]=0
        while viewer.is_running():
            viewer.sync()
            time.sleep(.03)


if __name__=='__main__':
    main()
