#!/usr/bin/env python3
"""Restored hybrid demonstration with user-directed terrain-aware path finding.

Chassis velocity and attitude are assisted. This is a navigation/design preview,
not hardware balance validation. The visual suspension and assisted transformations are demonstration features.
"""
import argparse
from contextlib import nullcontext
import json
import math
from pathlib import Path
import time
import numpy as np
import mujoco
import mujoco.viewer
from demo_asset import validate_sources, write_report
from safe_navigation import SafeNavigator
from hybrid_locomotion import HybridLocomotion
from hybrid_demo_design import DRIVE_HEIGHT
from terrain_profile import WHEEL_SPEED,WALK_SPEED
from mission_routes import get_kiosk_approach_corridor
from multi_place_config import MISSION_TARGETS, DEST_BASE, DEST_KIOSK_PAD, get_kiosk_departure_corridor

ROOT=Path(__file__).resolve().parent
DT=.016
LEGS=('LF','LM','LR','RF','RM','RR')


def angle(value):
    return (value+math.pi)%(2*math.pi)-math.pi


def yaw_of(data):
    w,x,y,z=data.qpos[3:7]
    return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))


from destination_routing import DestinationMission, draw_route


def configure_camera(camera, preset, model, data):
    camera.type=mujoco.mjtCamera.mjCAMERA_FREE
    if preset==1:
        camera.lookat[:]=[0,-2,0]
        camera.distance=58.
        camera.elevation=-58.
        camera.azimuth=90.
    elif preset==2:
        camera.lookat[:]=data.qpos[:3]
        camera.distance=12.
        camera.elevation=-35.
    else:
        camera.type=mujoco.mjtCamera.mjCAMERA_TRACKING
        camera.trackbodyid=model.body('robot').id
        camera.lookat[:]=data.qpos[:3]
        camera.distance=5. if preset==3 else 7.
        camera.elevation=-25.
        camera.azimuth=130.


def run_mission(args):
    validate_sources()
    write_report(ROOT/'outputs/asset_integrity.json')
    m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'))
    d=mujoco.MjData(m)
    locomotion=HybridLocomotion(m,d)
    d.qpos[:3]=[float(DEST_BASE[0]),float(DEST_BASE[1]),DRIVE_HEIGHT]
    d.qpos[3:7]=[math.sqrt(.5),0,0,math.sqrt(.5)]
    mujoco.mj_forward(m,d)
    navigator=SafeNavigator(m,d)
    mission=DestinationMission(navigator,mode=args.route_mode)
    mission.pose(d.qpos[:2],yaw_of(d))
    sequence=[int(x)-1 for x in args.sequence.split(',')] if args.sequence else []
    sequence_index=0
    if sequence:
        if any(x not in range(4) for x in sequence):
            raise ValueError("Sequence must contain only places 1-4")
        mission.dispatch(sequence[0]);sequence_index=1
    if args.dispatch:
        mission.dispatch(args.dispatch-1)
    camera_preset=0
    pending_keys=[]
    scheduled={}
    if args.commands:
        for event in json.loads(Path(args.commands).read_text()):
            scheduled.setdefault(int(event['step']),[]).append(ord(str(event['key']).upper()))
    def on_key(key):
        # Viewer callback only queues events; all state changes occur on the simulation thread.
        pending_keys.append(key)
    if args.headless:
        class HeadlessViewer:
            cam=mujoco.MjvCamera()
            def is_running(self):return True
            def sync(self):pass
        context=nullcontext(HeadlessViewer())
    else:
        context=mujoco.viewer.launch_passive(m,d,key_callback=on_key)
    step=0
    speed=omega=0.
    previous=d.qpos[:2].copy()
    collision_count=contacts=holds=route_errors=0
    min_foot=float('inf')
    last_error=None
    max_tilt=0.
    trace=[]
    print('HYBRID DEMO: 1-4 destinations | M transform | A automatic terrain | P fastest/shortest | C camera | B battery test | 0 charge',flush=True)
    preview_camera=None
    previous_stage=mission.stage
    with context as viewer:
        configure_camera(viewer.cam,camera_preset,m,d)
        if not args.headless:
            viewer.opt.geomgroup[3]=0
        while viewer.is_running() and (not args.headless or step<args.steps):
            started=time.monotonic()
            step+=1
            pending_keys.extend(scheduled.get(step,[]))
            xy=d.qpos[:2].copy()
            yaw=yaw_of(d)
            navigator.current_mode=locomotion.mode
            navigator.force_mode=locomotion.override
            mission.pose(xy,yaw)
            if sequence and mission.stage=='arrived' and not mission.divert and not mission.charging and sequence_index<len(sequence):
                mission.dispatch(sequence[sequence_index]);sequence_index+=1
            if args.battery_test_step==step:
                pending_keys.append(66)
            while pending_keys:
                key=pending_keys.pop(0)
                if key in (67,99):
                    preview_camera=None
                    camera_preset=(camera_preset+1)%4
                    configure_camera(viewer.cam,camera_preset,m,d)
                elif key in (66,98):
                    mission.battery=18.
                elif key==48:
                    mission.charge(xy)
                elif key in (49,50,51,52):
                    mission.dispatch(key-49)
                elif key in (80,112):
                    mission.toggle_mode()
                elif key in (88,120):
                    mission.cancel()
                elif key in (77,109):
                    locomotion.toggle()
                    navigator.force_mode=locomotion.override
                    if mission.stage in ('moving','preview','blocked'):
                        mission.stage='stopping'
                        mission.pending_target='charger' if mission.divert else mission.target
                elif key in (65,97):
                    locomotion.automatic()
                    navigator.force_mode=None
                    if mission.stage in ('moving','preview','blocked'):
                        mission.stage='stopping'
                        mission.pending_target='charger' if mission.divert else mission.target
            mission.update(xy,float(np.linalg.norm(xy-previous)),yaw,speed,omega,motion_paused=locomotion.busy)
            previous=xy
            desired_speed=desired_omega=0.
            transform_stop=locomotion.should_stop(xy,mission.goal,mission.stage=='moving')
            if mission.stage=='moving' and not transform_stop:
                try:
                    waypoint=mission.goal
                    if not navigator.segment_clear(xy,waypoint):
                        mission.stage='stopping'
                        mission.pending_target='charger' if mission.divert else mission.target
                        raise RuntimeError('Replanning to keep the displayed route collision-free')
                    delta=waypoint-xy
                    heading=angle(math.atan2(delta[1],delta[0])-yaw)
                    desired_speed=min(WALK_SPEED if locomotion.mode=='legs' else WHEEL_SPEED,math.sqrt(.9*max(0.,float(np.linalg.norm(delta))-.1)))*max(0.,math.cos(heading))**3
                    desired_omega=1.0*math.tanh(2.1*heading)
                    last_error=None
                except RuntimeError as error:
                    if str(error)!=last_error:
                        if mission.stage!='stopping':
                            route_errors+=1
                        last_error=str(error)
                        print('[NAVIGATION HOLD]',error,flush=True)
            speed=float(np.clip(desired_speed,speed-.010,speed+.010))
            omega=float(np.clip(desired_omega,omega-.030,omega+.030))
            safe_speed,omega=navigator.limit_motion(xy,yaw,speed,omega)
            if abs(safe_speed-speed)>1e-6:
                holds+=1
                if mission.stage=='moving':
                    mission.stage='stopping'
                    mission.pending_target='charger' if mission.divert else mission.target
            speed=safe_speed
            locomotion.tick(xy,yaw,speed,omega,DT)
            locomotion.update_lights(mission.battery,mission.charging)
            if locomotion.transforming:
                speed=omega=0.
            d.qvel[0:2]=speed*np.array([math.cos(yaw),math.sin(yaw)])
            d.qvel[5]=omega
            w,x,y,z=d.qpos[3:7]
            roll=math.atan2(2*(w*x+y*z),1-2*(x*x+y*y))
            pitch=math.asin(float(np.clip(2*(w*y-z*x),-1,1)))
            d.qvel[2]=float(np.clip(8*(locomotion.height-d.qpos[2]),-1.5,1.5))
            d.qvel[3:5]=np.clip([-10*roll,-10*pitch],-2.5,2.5)
            for _ in range(4):
                # The assisted base velocity servo runs at the physics timestep,
                # reducing lateral wheel-contact drift at route corners.
                d.qvel[0:2]=speed*np.array([math.cos(yaw),math.sin(yaw)])
                d.qvel[5]=omega
                mujoco.mj_step(m,d)
                for contact in d.contact:
                    a,b=int(contact.geom1),int(contact.geom2)
                    if ((a in navigator.robot_geom_set and b in navigator.obstacle_geom_set) or
                        (b in navigator.robot_geom_set and a in navigator.obstacle_geom_set)):
                        contacts+=int(contact.dist<=.001)
                        collision_count+=int(contact.dist<-.001)
            min_foot=min(min_foot,min(float(d.geom_xpos[i,2]-.045) for i in locomotion.foot_ids))
            max_tilt=max(max_tilt,abs(roll),abs(pitch))
            if step%250==0:
                trace.append({'step':step,'xy':xy.tolist(),'battery':mission.battery,'stage':mission.stage,'charging':mission.charging,'locomotion':locomotion.mode,'transforming':locomotion.transforming})
            if not args.headless:
                if mission.stage=='preview' and previous_stage!='preview' and camera_preset in (0,3):
                    preview_camera={name:getattr(viewer.cam,name) for name in ('type','trackbodyid','distance','azimuth','elevation')}
                    preview_camera['lookat']=viewer.cam.lookat.copy()
                    configure_camera(viewer.cam,1,m,d)
                elif mission.stage!='preview' and previous_stage=='preview' and preview_camera is not None:
                    for name,value in preview_camera.items():
                        if name=='lookat':viewer.cam.lookat[:]=value
                        else:setattr(viewer.cam,name,value)
                    preview_camera=None
                state=mission.stage.upper()
                if mission.stage=='idle':state='WAITING FOR DESTINATION'
                if mission.stage=='preview':state=f'ROUTE PREVIEW ({max(0.,mission.preview_remaining):.1f}s)'
                if mission.stage=='arrived':state='ARRIVED - choose next place'
                if mission.error:state='NO SAFE ROUTE: '+mission.error
                phase_label=locomotion.phase+(f' ({locomotion.progress*100:.0f}%)' if locomotion.transforming else '')
                viewer.set_texts([
                    (mujoco.mjtFont.mjFONT_NORMAL,mujoco.mjtGridPos.mjGRID_TOPLEFT,
                     'HYBRID PATH FINDING\nLocomotion\nTransformation\nDestination\nStatus\nPlanner\nRoute length\nEstimated travel\nRemaining\nBattery',
                     f'Demonstration model\n{locomotion.mode.upper()} ({"AUTO" if locomotion.override is None else "MANUAL"})\n{phase_label}\n{mission.destination_name}\n{state}\n{mission.mode.upper()}\n{mission.metrics["distance_m"]:.1f} m\n{mission.metrics["estimated_seconds"]:.0f} s (estimate)\n{mission.remaining_distance:.1f} m\n{mission.battery:.1f}%'),
                    (mujoco.mjtFont.mjFONT_NORMAL,mujoco.mjtGridPos.mjGRID_TOPRIGHT,
                     'CHOOSE DESTINATION\n1\n2\n3\n4\nP\nC / X\nM / A\nRoute colors',
                     'Press a number\nForest\nQuarry\nMarsh\nDesert\nFastest / shortest\nCamera / cancel\nTransform / auto terrain\nCyan: drive | Amber: walk | Purple: traveled')])
                with viewer.lock():
                    draw_route(viewer.user_scn,mission)
            previous_stage=mission.stage
            viewer.sync()
            if step%2000==0:
                print(f'Step {step}: {mission.stage}, destination {mission.destination_name}, battery {mission.battery:.1f}%, contacts {contacts}, route errors {route_errors}',flush=True)
            if args.headless and mission.stage=='arrived' and not mission.divert and not mission.charging:
                if (args.stop_on_arrival and not sequence) or (sequence and sequence_index==len(sequence)):
                    break
            if not args.headless:
                time.sleep(max(0.,DT-(time.monotonic()-started)))
    report=dict(steps=step,simulation_seconds=float(d.time),mode='hybrid_demo',transformations=locomotion.events,
        position=d.qpos[:3].tolist(),battery=mission.battery,visited_places=sorted(mission.visited),
        stage=mission.stage,arrivals=mission.arrivals,planned_routes=mission.plans,route_mode=mission.mode,
        charge_completed=mission.charges,collision_substeps=collision_count,obstacle_contact_substeps=contacts,
        safety_stops=holds,route_failures=route_errors,minimum_foot_bottom=min_foot,
        max_body_tilt_degrees=math.degrees(max_tilt),finite_state=bool(np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()),
        solver_warnings=int(sum(w.number for w in d.warning)),trace=trace)
    if args.report:
        Path(args.report).write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='trace'},indent=2),flush=True)
    if args.snapshot:
        from PIL import Image
        camera=mujoco.MjvCamera();configure_camera(camera,1,m,d)
        renderer=mujoco.Renderer(m,800,1200)
        renderer.update_scene(d,camera=camera)
        draw_route(renderer.scene,mission,reset=False)
        Image.fromarray(renderer.render()).save(args.snapshot)
        renderer.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--steps',type=int,default=100000)
    parser.add_argument('--battery-test-step',type=int,default=0)
    parser.add_argument('--dispatch',type=int,choices=range(1,5),default=None)
    parser.add_argument('--route-mode',choices=['fastest','shortest'],default='fastest')
    parser.add_argument('--sequence',help='Validation sequence, e.g. 1,2,3,4; disabled by default')
    parser.add_argument('--stop-on-arrival',action='store_true')
    parser.add_argument('--commands',help='Optional JSON list of {step, key} input events for reproducible testing')
    parser.add_argument('--report')
    parser.add_argument('--snapshot')
    run_mission(parser.parse_args())
