"""User-directed point-to-point missions and route visualization annotations."""
import math
import numpy as np
import mujoco
from multi_place_config import MISSION_TARGETS, DEST_KIOSK_PAD, DEST_KIOSK_ENTRY

PLACES=[np.asarray(t['pos'],dtype=float) for t in MISSION_TARGETS]
NAMES=[t['name'] for t in MISSION_TARGETS]


class DestinationMission:
    def __init__(self, navigator, mode='fastest'):
        self.navigator=navigator
        self.mode=mode
        self.target=None
        self.stage='idle'
        self.battery=100.
        self.divert=self.charging=False
        self.resume_target=None
        self.pending_target=None
        self.position=np.zeros(2)
        self.yaw=0.
        self.route=[]
        self.index=0
        self.full_route=[]
        self.trail=[]
        self.preview_remaining=0.
        self.green_hold=0.
        self.charges=0
        self.visited=set()
        self.arrivals=[]
        self.plans=[]
        self.metrics={'distance_m':0.,'estimated_seconds':0.}
        self.error=None
        self.elapsed=0.
        self.depart_station=False
        self.travel_start=None
        self.initial_metrics=None
        self.actual_distance=0.

    def pose(self,xy,yaw):
        self.position=np.asarray(xy).copy();self.yaw=float(yaw)

    def dispatch(self,target):
        if not 0<=target<4:
            raise ValueError('Choose Place 1, 2, 3, or 4')
        if self.battery<=35 or self.charging or self.divert:
            self.resume_target=target
            if not self.divert and not self.charging:
                self.charge(self.position)
            print(f'{NAMES[target]} queued after charging.',flush=True)
            return
        self.target=target
        self.pending_target=target
        self.stage='stopping'
        self.error=None
        self.full_route=[]
        self.trail=[]
        self.travel_start=None
        self.initial_metrics=None
        self.actual_distance=0.
        self.metrics={'distance_m':0.,'estimated_seconds':0.}
        print('Requested:',NAMES[target],flush=True)

    def charge(self,xy):
        if self.divert or self.charging:
            return
        if self.stage in ('moving','preview','stopping') and self.target is not None:
            self.resume_target=self.target
        self.divert=True
        self.pending_target='charger'
        self.stage='stopping'
        self.full_route=[]
        self.error=None
        print('Battery priority: route to center charger.',flush=True)

    def cancel(self):
        if self.divert or self.charging:
            self.resume_target=None
            return
        self.stage='idle';self.pending_target=None;self.target=None
        self.route=[];self.full_route=[];self.error=None
        print('Destination cancelled. Waiting for Place 1-4.',flush=True)

    def toggle_mode(self):
        self.mode='shortest' if self.mode=='fastest' else 'fastest'
        if self.stage in ('moving','preview','blocked'):
            self.pending_target='charger' if self.divert else self.target
            self.stage='stopping'
        print('Route mode:',self.mode,flush=True)

    def _best_path(self,start,goal,yaw):
        candidates=[self.navigator.plan(start,goal,mode=mode,yaw=yaw) for mode in ('shortest','fastest')]
        key='distance_m' if self.mode=='shortest' else 'estimated_seconds'
        return min(candidates,key=lambda path:self.navigator.route_metrics([start]+path,yaw)[key])

    def _plan(self):
        goal=DEST_KIOSK_PAD if self.pending_target=='charger' else PLACES[self.pending_target]
        start=self.position.copy();heading=self.yaw;path=[]
        # Access constraint: enter/leave the charging plaza through its front opening.
        via=[np.asarray(DEST_KIOSK_ENTRY,dtype=float)] if self.divert or self.depart_station else []
        for endpoint in via+[np.asarray(goal,dtype=float)]:
            if np.linalg.norm(endpoint-start)<.05:
                continue
            segment=self._best_path(start,endpoint,heading)
            if segment:
                direction=segment[-1]-(segment[-2] if len(segment)>1 else start)
                heading=math.atan2(direction[1],direction[0])
            path+=segment;start=endpoint
        self.route=[np.asarray(p).copy() for p in path] or [np.asarray(goal).copy()]
        self.full_route=[self.position.copy()]+[p.copy() for p in self.route]
        if self.travel_start is None:
            self.trail=[self.position.copy()]
        self.index=0
        self.metrics=self.navigator.route_metrics(self.full_route,self.yaw)
        self.stage='preview';self.preview_remaining=1.5
        self.error=None
        if self.initial_metrics is None:
            self.initial_metrics=dict(self.metrics)
        self.plans.append(dict(destination='charger' if self.divert else self.target+1,
            mode=self.mode,points=[p.tolist() for p in self.full_route],**self.metrics))
        self.navigator.replans+=1
        print(f'ROUTE READY: {self.destination_name} | {self.mode} | '
              f'{self.metrics["distance_m"]:.1f} m | estimated {self.metrics["estimated_seconds"]:.0f} s | '
              f'{len(self.route)} segments',flush=True)

    @property
    def destination_name(self):
        if self.divert or self.charging:
            return 'Center charging station'
        return NAMES[self.target] if self.target is not None else 'Choose Place 1-4'

    @property
    def goal(self):
        return self.route[self.index] if self.route else self.position

    @property
    def remaining_distance(self):
        if not self.route or self.stage not in ('moving','preview'):
            return 0.
        return self.navigator.route_metrics([self.position]+self.route[self.index:],self.yaw)['distance_m']

    def update(self,xy,traveled,yaw,speed,omega,dt=.016,motion_paused=False):
        self.pose(xy,yaw);self.elapsed+=dt
        if self.travel_start is not None and self.stage in ('moving','stopping','preview'):
            self.actual_distance+=traveled
        if not self.trail or np.linalg.norm(xy-self.trail[-1])>.15:
            self.trail.append(np.asarray(xy).copy())
        if self.charging:
            self.battery=min(100.,self.battery+15.625*dt)
            self.green_hold=self.green_hold+dt if self.battery>=100 else 0.
            if self.green_hold>=2.4:
                self.charges+=1;self.charging=self.divert=False
                self.depart_station=True
                target=self.resume_target;self.resume_target=None
                self.stage='arrived';self.pending_target=None
                self.route=[]
                if target is not None:
                    self.dispatch(target)
                print('Battery 100%; charging complete.',flush=True)
            return
        self.battery=max(0.,self.battery-traveled*.2-(.0006 if self.stage=='moving' else 0.))
        if self.battery<=35 and not self.divert:
            self.charge(xy)
        if motion_paused:
            return
        if self.stage=='stopping':
            if abs(speed)<.015 and abs(omega)<.03:
                try:
                    self._plan()
                except RuntimeError as error:
                    self.stage='blocked';self.error=str(error)
                    print('[NO SAFE ROUTE]',error,flush=True)
            return
        if self.stage=='preview':
            self.preview_remaining-=dt
            if self.preview_remaining<=0:
                self.stage='moving'
                if self.travel_start is None:
                    self.travel_start=self.elapsed
            return
        if self.stage!='moving':
            return
        if self.depart_station and np.linalg.norm(xy-DEST_KIOSK_ENTRY)<.25:
            self.depart_station=False
        final=self.index==len(self.route)-1
        tolerance=.22 if final else .12
        if np.linalg.norm(self.goal-xy)>tolerance or abs(speed)>.025:
            return
        if not final:
            if not self.navigator.segment_clear(xy,self.route[self.index+1]):
                self.stage='stopping'
                self.pending_target='charger' if self.divert else self.target
            else:
                self.index+=1
            return
        if self.divert:
            self.charging=True;self.stage='charging';self.green_hold=0.
            print('Arrived at charging station.',flush=True)
        else:
            self.stage='arrived';self.depart_station=False
            self.visited.add(self.target+1)
            record=dict(destination=self.target+1,position=np.asarray(xy).tolist(),
                error_m=float(np.linalg.norm(PLACES[self.target]-xy)),
                travel_seconds=self.elapsed-self.travel_start,actual_distance_m=self.actual_distance,**self.initial_metrics)
            self.arrivals.append(record)
            print(f'ARRIVED: {self.destination_name}. Waiting for next destination.',flush=True)


def draw_route(scene,mission,reset=True):
    """Viewer-only annotations: no change to robot geometry or physics."""
    if reset:
        scene.ngeom=0
    def add(kind,size,pos,color,label=''):
        if scene.ngeom>=scene.maxgeom:return None
        geom=scene.geoms[scene.ngeom]
        mujoco.mjv_initGeom(geom,kind,np.asarray(size,dtype=float),np.asarray(pos,dtype=float),np.eye(3).ravel(),np.asarray(color,dtype=np.float32))
        geom.label=label
        scene.ngeom+=1
        return geom
    def line(a,b,color,width=.025,z=.10):
        geom=add(mujoco.mjtGeom.mjGEOM_CAPSULE,[width,1,1],[0,0,0],color)
        if geom is not None:
            mujoco.mjv_connector(geom,mujoco.mjtGeom.mjGEOM_CAPSULE,width,np.r_[a,z],np.r_[b,z])
    for index,point in enumerate(PLACES):
        selected=mission.target==index and not mission.divert
        color=[1.,.55,.08,1.] if selected else [.25,.7,.45,.8]
        add(mujoco.mjtGeom.mjGEOM_SPHERE,[.15,0,0],[*point,.3],color,label='' if selected else f'Place {index+1}')
    for a,b in zip(mission.full_route,mission.full_route[1:]):
        for lo,hi,walking in mission.navigator.motion_segments(a,b):
            color=[1.,.68,.08,1.] if walking else [.04,.85,1.,1.]
            line(lo,hi,color,width=.055)
            distance=float(np.linalg.norm(hi-lo))
            if distance>1e-6:
                direction=(hi-lo)/distance;normal=np.array([-direction[1],direction[0]])
                for t in np.arange(1.,distance,2.):
                    tip=lo+t*direction
                    line(tip-.22*direction+.10*normal,tip,color,width=.018)
                    line(tip-.22*direction-.10*normal,tip,color,width=.018)
    for a,b in zip(mission.trail,mission.trail[1:]):
        line(a,b,[.7,.3,1.,1.],width=.018,z=.13)
    if mission.full_route:
        goal=mission.full_route[-1]
        add(mujoco.mjtGeom.mjGEOM_SPHERE,[.24,0,0],[*goal,.15],[1.,.55,.08,.9],label=mission.destination_name)
