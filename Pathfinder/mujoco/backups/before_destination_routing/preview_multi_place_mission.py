#!/usr/bin/env python3
"""Walking-only source-mesh mission. Only the authorized actuator visual is replaced.

Chassis velocity and attitude are assisted. This is a navigation/design preview,
not hardware balance validation. No wheels or additional robot geometry are used.
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
from strict_asset import validate_sources, write_report
from safe_navigation import SafeNavigator
from tripod_gait import TripodGait
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


class Mission:
    def __init__(self):
        self.target=0
        self.stage='approach'
        self.route=list(MISSION_TARGETS[0]['approach'])
        self.index=0
        self.battery=100.
        self.divert=False
        self.charging=False
        self.saved=None
        self.resume=None
        self.dwell=0.
        self.green_hold=0.
        self.charges=0
        self.laps=0
        self.visited=set()
        self.scans=set()

    def dispatch(self, target):
        if self.battery<=35 or self.charging:
            print('Battery priority: finish charging before site dispatch.',flush=True)
            return
        self.target=target
        self.stage='approach'
        self.route=[MISSION_TARGETS[target]['pos']]
        self.index=0
        self.divert=False
        self.dwell=0.
        self.resume=None
        print('Dispatch:',MISSION_TARGETS[target]['name'],flush=True)

    def charge(self, xy):
        if self.divert:
            return
        self.saved=(self.target,self.stage,list(self.route),self.index)
        self.divert=True
        self.charging=False
        self.dwell=0.
        self.route=get_kiosk_approach_corridor(xy)
        self.index=0
        print(f'LOW BATTERY / CHARGE REQUEST: {self.battery:.1f}% -> center charging pad',flush=True)

    @property
    def goal(self):
        return np.asarray(self.route[self.index],dtype=float)

    def update(self, xy, traveled):
        if self.charging:
            self.battery=min(100.,self.battery+15.625*DT)
            if self.battery>=100.:
                self.green_hold+=DT
            if self.green_hold>=2.4:
                self.charges+=1
                self.charging=self.divert=False
                self.green_hold=0.
                self.target,old_stage,old_route,old_index=self.saved
                self.index=0
                if old_stage=='return':
                    self.stage='return'
                    self.route=list(get_kiosk_departure_corridor(99))
                elif old_stage in ('circuit','resume'):
                    self.stage='resume'
                    self.route=list(get_kiosk_departure_corridor(self.target))
                    self.resume=(old_route[old_index:] if old_stage=='circuit' else self.resume)
                else:
                    self.stage='approach'
                    self.route=list(get_kiosk_departure_corridor(self.target))
                print('Charged to 100%; resuming',MISSION_TARGETS[self.target]['name'],flush=True)
            return
        self.battery=max(0.,self.battery-traveled*.20-.0006)
        if self.battery<=35 and not self.divert:
            self.charge(xy)
        if self.dwell>0:
            self.dwell=max(0.,self.dwell-DT)
            return
        if np.linalg.norm(self.goal-xy)>.32:
            return
        if self.stage=='circuit' and not self.divert:
            self.scans.add((self.target+1,self.index))
            self.dwell=.6
        if self.index<len(self.route)-1:
            self.index+=1
            return
        self.index=0
        if self.divert:
            self.charging=True
            self.green_hold=0.
            print('Docked at center pad; charging.',flush=True)
        elif self.stage=='approach':
            self.visited.add(self.target+1)
            self.stage='circuit'
            self.route=[item['pos'] for item in MISSION_TARGETS[self.target]['circuit']]
            self.dwell=.6
            print('Arrived:',MISSION_TARGETS[self.target]['name'],flush=True)
        elif self.stage=='resume':
            self.stage='circuit'
            self.route=self.resume
            self.resume=None
        elif self.stage=='circuit':
            self.stage='return'
            self.route=list(MISSION_TARGETS[self.target]['return_corridor'])
            print('Site scan complete; returning to base.',flush=True)
        else:
            self.dwell=.9
            self.target=(self.target+1)%4
            if self.target==0:
                self.laps+=1
                print('Completed four-site tour and returned to base.',flush=True)
            self.stage='approach'
            self.route=list(MISSION_TARGETS[self.target]['approach'])


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
    joint_names=[leg+'_'+kind+'_joint' for leg in LEGS for kind in ('hip','femur','tibia')]
    qpos_ids=np.array([int(m.joint(name).qposadr[0]) for name in joint_names])
    actuator_ids=np.array([m.actuator('source_act_'+name).id for name in joint_names])
    foot_ids=[m.geom('source_collision_'+leg+'_foot_0').id for leg in LEGS]
    # Ideal gravity compensation for limb tracking; source inertias and geometry remain intact.
    for leg in LEGS:
        for part in ('coxa','femur','tibia','foot'):
            m.body_gravcomp[m.body(leg+'_'+part).id]=1.
    gait=TripodGait()
    d.qpos[:3]=[float(DEST_BASE[0]),float(DEST_BASE[1]),.48]
    d.qpos[3:7]=[math.sqrt(.5),0,0,math.sqrt(.5)]
    d.qpos[qpos_ids]=gait.targets(d.qpos[:2],math.pi/2,.48,0.,0.)
    d.ctrl[actuator_ids]=d.qpos[qpos_ids]
    mujoco.mj_forward(m,d)
    navigator=SafeNavigator(m,d)
    mission=Mission()
    if args.dispatch:
        mission.dispatch(args.dispatch-1)
    camera_preset=0
    pending_keys=[]
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
    print('WALKING ONLY: C camera | B 18% battery | 1-4 dispatch | 0 charge | M wheels unavailable',flush=True)
    with context as viewer:
        configure_camera(viewer.cam,camera_preset,m,d)
        if not args.headless:
            viewer.opt.geomgroup[3]=0
        while viewer.is_running() and (not args.headless or step<args.steps):
            started=time.monotonic()
            step+=1
            xy=d.qpos[:2].copy()
            yaw=yaw_of(d)
            if args.battery_test_step==step:
                pending_keys.append(66)
            while pending_keys:
                key=pending_keys.pop(0)
                if key in (67,99):
                    camera_preset=(camera_preset+1)%4
                    configure_camera(viewer.cam,camera_preset,m,d)
                elif key in (66,98):
                    mission.battery=18.
                elif key==48:
                    mission.charge(xy)
                elif key in (49,50,51,52):
                    mission.dispatch(key-49)
                elif key in (77,109):
                    print('Wheels are excluded; six-legged walking remains active.',flush=True)
            mission.update(xy,float(np.linalg.norm(xy-previous)))
            previous=xy
            desired_speed=desired_omega=0.
            if not mission.charging and mission.dwell<=0:
                try:
                    waypoint=navigator.steer(xy,mission.goal)
                    delta=waypoint-xy
                    heading=angle(math.atan2(delta[1],delta[0])-yaw)
                    desired_speed=min(.42,math.sqrt(.9*max(0.,float(np.linalg.norm(delta))-.1)))*max(0.,math.cos(heading))**3
                    desired_omega=1.0*math.tanh(2.1*heading)
                    last_error=None
                except RuntimeError as error:
                    if str(error)!=last_error:
                        route_errors+=1
                        last_error=str(error)
                        print('[NAVIGATION HOLD]',error,flush=True)
            speed=float(np.clip(desired_speed,speed-.010,speed+.010))
            omega=float(np.clip(desired_omega,omega-.030,omega+.030))
            safe_speed,omega=navigator.limit_motion(xy,yaw,speed,omega)
            if abs(safe_speed-speed)>1e-6:
                holds+=1
                navigator.goal_key=None
            speed=safe_speed
            # Feet finish their swing smoothly even when the chassis stops for a scan.
            d.ctrl[actuator_ids]=gait.targets(xy,yaw,float(d.qpos[2]),speed,omega)
            d.qvel[0:2]=speed*np.array([math.cos(yaw),math.sin(yaw)])
            d.qvel[5]=omega
            w,x,y,z=d.qpos[3:7]
            roll=math.atan2(2*(w*x+y*z),1-2*(x*x+y*y))
            pitch=math.asin(float(np.clip(2*(w*y-z*x),-1,1)))
            d.qvel[2]=float(np.clip(8*(.48-d.qpos[2]),-1.5,1.5))
            d.qvel[3:5]=np.clip([-10*roll,-10*pitch],-2.5,2.5)
            for _ in range(4):
                mujoco.mj_step(m,d)
                for contact in d.contact:
                    a,b=int(contact.geom1),int(contact.geom2)
                    if ((a in navigator.robot_geom_set and b in navigator.obstacle_geom_set) or
                        (b in navigator.robot_geom_set and a in navigator.obstacle_geom_set)):
                        contacts+=int(contact.dist<=.001)
                        collision_count+=int(contact.dist<-.001)
            min_foot=min(min_foot,min(float(d.geom_xpos[i,2]-.045) for i in foot_ids))
            max_tilt=max(max_tilt,abs(roll),abs(pitch))
            if step%250==0:
                trace.append({'step':step,'xy':xy.tolist(),'battery':mission.battery,'stage':mission.stage,'charging':mission.charging})
            if not args.headless:
                state='CHARGING' if mission.charging else ('LOW BATTERY - RETURN TO CHARGER' if mission.divert else mission.stage.upper())
                viewer.set_texts((mujoco.mjtFont.mjFONT_NORMAL,mujoco.mjtGridPos.mjGRID_TOPLEFT,
                    'WALKING ONLY\nBattery\nStatus\nDestination\nControls',
                    f'Source meshes + replacement motors\n{mission.battery:.1f}%\n{state}\n{MISSION_TARGETS[mission.target]["name"]}\nC camera | B low battery | 1-4 places | 0 charge'))
            viewer.sync()
            if step%2000==0:
                print(f'Step {step}: {mission.stage}, place {mission.target+1}, battery {mission.battery:.1f}%, contacts {contacts}, route errors {route_errors}',flush=True)
            if args.stop_after_tour and mission.laps:
                break
            if not args.headless:
                time.sleep(max(0.,DT-(time.monotonic()-started)))
    report=dict(steps=step,simulation_seconds=float(d.time),mode='walking_only',
        position=d.qpos[:3].tolist(),battery=mission.battery,visited_places=sorted(mission.visited),
        scanned_sectors=sorted([list(x) for x in mission.scans]),completed_tours=mission.laps,
        charge_completed=mission.charges,collision_substeps=collision_count,obstacle_contact_substeps=contacts,
        safety_stops=holds,route_failures=route_errors,minimum_foot_bottom=min_foot,
        max_body_tilt_degrees=math.degrees(max_tilt),finite_state=bool(np.isfinite(d.qpos).all() and np.isfinite(d.qvel).all()),
        solver_warnings=int(sum(w.number for w in d.warning)),trace=trace)
    if args.report:
        Path(args.report).write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='trace'},indent=2),flush=True)
    if args.snapshot:
        from PIL import Image
        camera=mujoco.MjvCamera();configure_camera(camera,3,m,d)
        renderer=mujoco.Renderer(m,800,1200)
        renderer.update_scene(d,camera=camera)
        Image.fromarray(renderer.render()).save(args.snapshot)
        renderer.close()
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless',action='store_true')
    parser.add_argument('--steps',type=int,default=100000)
    parser.add_argument('--battery-test-step',type=int,default=0)
    parser.add_argument('--dispatch',type=int,choices=range(1,5),default=None)
    parser.add_argument('--stop-after-tour',action='store_true')
    parser.add_argument('--report')
    parser.add_argument('--snapshot')
    run_mission(parser.parse_args())
