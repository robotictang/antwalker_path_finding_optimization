"""Execute planned routes in the existing MuJoCo model without live history writes."""
import math
import numpy as np
import energy_model as em
import mujoco
from safe_navigation import SafeNavigator
from hybrid_locomotion import HybridLocomotion
from tripod_gait import TripodGait
from hybrid_demo_design import DRIVE_HEIGHT, WALK_HEIGHT
from road_demo import ground_height
from terrain_profile import travel_speed, severity_at
from energy_model import energy_cost
from research.telemetry import Telemetry

DT=.016
def angle(v):return (v+math.pi)%(2*math.pi)-math.pi
def yaw_of(data):
    w,x,y,z=data.qpos[3:7]
    return math.atan2(2*(w*z+x*y),1-2*(y*y+z*z))

def execute(model,route,initial_battery=100.,walking_only=True,gait=None,
            max_seconds=400.,energy_multiplier=1.,speed_cap=None,return_route=None,
            service='charge',service_seconds=8.,record_every=25):
    if not route or len(route)<2:raise ValueError('Execution needs a route with two points')
    data=mujoco.MjData(model)
    loc=HybridLocomotion(model,data)
    loc.gait=TripodGait(**(gait or {}))
    initial=np.asarray(route[0],float)
    data.qpos[:3]=[*initial,(WALK_HEIGHT if walking_only else DRIVE_HEIGHT)+float(ground_height(initial))]
    # Paired planner trials start at the same heading used for prediction.
    yaw=math.pi/2
    data.qpos[3:7]=[math.cos(yaw/2),0.,0.,math.sin(yaw/2)]
    if walking_only:
        loc.mode='legs';loc.override='legs';loc.height=WALK_HEIGHT
        pose=loc.gait.targets(initial,yaw,float(data.qpos[2]),0.,0.)
        data.qpos[loc.qids]=pose;data.ctrl[loc.aids]=pose
    mujoco.mj_forward(model,data)
    nav=SafeNavigator(model,data,resolution=.25)
    nav.current_mode='legs' if walking_only else 'wheels';nav.force_mode='legs' if walking_only else None
    telemetry=Telemetry(model,loc.foot_ids,loc.aids)
    target=np.asarray(route[-1]);points=[np.asarray(p,float) for p in route]
    if return_route:
        points.extend(np.asarray(p,float) for p in return_route[1:])
    task_end=len(route)-1;waypoint=1
    previous=data.qpos[:2].copy();last_yaw=yaw
    speed=omega=0.;distance=0.;battery=float(initial_battery);used=0.
    contacts=penetrations=0;limit_violations=0;safety_stops=0
    trace=[];task_time=None;task_distance=None;task_energy=None
    outcome='timeout';charges=swaps=0
    max_frames=int(max_seconds/DT)
    for frame in range(max_frames):
        xy=data.qpos[:2].copy();yaw=yaw_of(data)
        if frame and frame%record_every==0:trace.append(dict(t=float(data.time),xy=xy.tolist(),battery=battery,mode=loc.mode))
        while waypoint<len(points) and np.linalg.norm(points[waypoint]-xy)<.28:
            if waypoint==task_end and task_time is None:
                task_time=float(data.time);task_distance=distance;task_energy=used
            waypoint+=1
        if waypoint>=len(points):outcome='arrived';break
        delta=points[waypoint]-xy
        turn=angle(math.atan2(delta[1],delta[0])-yaw)
        allowed=float(travel_speed(xy,walking=loc.mode=='legs'))
        if speed_cap is not None:allowed=min(allowed,float(speed_cap))
        look=xy+delta/max(float(np.linalg.norm(delta)),1e-9)*min(1.2,float(np.linalg.norm(delta)))
        allowed=min(allowed,float(travel_speed(look,walking=loc.mode=='legs')))
        moving=not loc.should_stop(xy,points[waypoint],True)
        desired=min(allowed,math.sqrt(1.8*max(0.,float(np.linalg.norm(delta))-.10)))*max(0.,math.cos(turn))**3 if moving else 0.
        desired_omega=math.tanh(2.1*turn) if moving else 0.
        speed=float(np.clip(desired,speed-.02,speed+.02));speed=min(speed,allowed)
        omega=float(np.clip(desired_omega,omega-.03,omega+.03))
        safe,omega=nav.limit_motion(xy,yaw,speed,omega)
        if abs(safe-speed)>1e-7:safety_stops+=1
        speed=safe
        loc.tick(xy,yaw,speed,omega,DT)
        if loc.transforming:speed=omega=0.
        # Same explicit base assistance as the existing preview; never hidden.
        w,x,y,z=data.qpos[3:7]
        roll=math.atan2(2*(w*x+y*z),1-2*(x*x+y*y));pitch=math.asin(float(np.clip(2*(w*y-z*x),-1,1)))
        data.qvel[2]=float(np.clip(8*(loc.height+float(ground_height(xy))-data.qpos[2]),-1.5,1.5))
        data.qvel[3:5]=np.clip([-10*roll,-10*pitch],-2.5,2.5)
        for substep in range(4):
            data.qvel[:2]=speed*np.array([math.cos(yaw),math.sin(yaw)]);data.qvel[5]=omega
            mujoco.mj_step(model,data)
            telemetry.sample(data,float(model.opt.timestep))
            for c in data.contact:
                a,b=int(c.geom1),int(c.geom2)
                if (a in nav.robot_geom_set and b in nav.obstacle_geom_set) or (b in nav.robot_geom_set and a in nav.obstacle_geom_set):
                    contacts+=int(c.dist<=.001);penetrations+=int(c.dist<-.001)
        xy1=data.qpos[:2].copy();travel=float(np.linalg.norm(xy1-previous));distance+=travel
        yaw1=yaw_of(data);change=abs(angle(yaw1-last_yaw))
        cost=(travel*(em.WALK_PERCENT_PER_M if loc.mode=='legs' else em.DRIVE_PERCENT_PER_M)+DT*em.HOTEL_PERCENT_PER_S+change*em.TURN_PERCENT_PER_RAD)*energy_multiplier
        if frame==0:cost+=em.START_STOP_PERCENT
        if loc.events and loc.events[-1].get('event')=='begin' and abs(loc.events[-1]['time']-loc.clock)<1e-6:cost+=em.TRANSFORM_PERCENT*energy_multiplier
        used+=cost;battery-=cost;previous=xy1;last_yaw=yaw1
        limit_violations+=int(abs(speed)>float(travel_speed(xy,walking=loc.mode=='legs'))+.025)
        if battery<2.:outcome='battery_guard';break
        if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():outcome='nonfinite';break
        if penetrations:outcome='obstacle_penetration';break
        if telemetry.max_tilt>30.:outcome='tilt_guard';break
    if task_time is None and outcome=='arrived':
        task_time=float(data.time);task_distance=distance;task_energy=used
    # Service is modeled downtime; no claim of a physical replacement mechanism.
    elapsed=float(data.time)
    if outcome=='arrived' and return_route:
        if service=='swap':swaps=1
        elif service=='charge':charges=1
        elapsed+=service_seconds;battery=100.
    report=dict(outcome=outcome,success=outcome=='arrived',destination_reached=task_time is not None,
      task_time_s=task_time,task_distance_m=task_distance,task_energy_percent=task_energy,
      elapsed_s=elapsed,motion_seconds=float(data.time),distance_m=distance,
      energy_consumed_percent=used,battery_percent=battery,minimum_battery_percent=initial_battery-used,
      charging_stops=charges,modeled_swap_events=swaps,service_seconds=service_seconds if charges or swaps else 0.,
      obstacle_contact_substeps=contacts,penetration_substeps=penetrations,
      terrain_speed_violations=limit_violations,safety_stops=safety_stops,
      solver_warnings=int(sum(w.number for w in data.warning)),trace=trace,
      gait=dict(period=loc.gait.period,duty=loc.gait.duty,lift=loc.gait.lift,swing_profile=loc.gait.swing_profile),
      locomotion='walking_only' if walking_only else 'hybrid',energy_multiplier=energy_multiplier,
      transforms=len([e for e in loc.events if e['event']=='complete']),**telemetry.result())
    return report
