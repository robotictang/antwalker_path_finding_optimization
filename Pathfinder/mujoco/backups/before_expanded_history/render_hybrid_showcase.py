"""Render the restored design and actual assisted transformation controller."""
from pathlib import Path
import math
import numpy as np
import mujoco
from PIL import Image
from hybrid_locomotion import HybridLocomotion,STOW
from hybrid_demo_design import DRIVE_HEIGHT,WALK_HEIGHT

ROOT=Path(__file__).resolve().parent


def main():
    m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m)
    loc=HybridLocomotion(m,d);d.qpos[:3]=[0,-20,DRIVE_HEIGHT]
    mujoco.mj_forward(m,d)
    camera=mujoco.MjvCamera();camera.lookat[:]=[0,-20,.74]
    camera.distance=6.2;camera.elevation=-28;camera.azimuth=130
    renderer=mujoco.Renderer(m,600,900)
    def render():
        renderer.update_scene(d,camera=camera)
        return Image.fromarray(renderer.render())
    loc.update_lights(100,False);render().save(ROOT/'outputs/hybrid_restored_wheels.png')
    loc.clock=.18;loc.update_lights(18,False);render().save(ROOT/'outputs/hybrid_low_battery.png')
    loc.update_lights(100,False)
    frames=[]
    loc.toggle()
    for step in range(440):
        if step==225:loc.toggle()
        loc.should_stop(d.qpos[:2],d.qpos[:2],False)
        loc.tick(d.qpos[:2],0.,0.,0.)
        d.qvel[:2]=0.;d.qvel[3:6]=0.
        d.qvel[2]=float(np.clip(8*(loc.height-d.qpos[2]),-1.5,1.5))
        for _ in range(4):mujoco.mj_step(m,d)
        if step%8==0:frames.append(render())
        if step==210:render().save(ROOT/'outputs/hybrid_restored_legs.png')
    frames=[f.resize((720,480)).quantize(colors=96) for f in frames]
    frames[0].save(ROOT/'outputs/hybrid_transformation.gif',save_all=True,append_images=frames[1:],duration=128,loop=0,optimize=True)
    renderer.close()
    print('Saved restored-wheel, walking, low-battery, and transformation previews.')


if __name__=='__main__':main()
