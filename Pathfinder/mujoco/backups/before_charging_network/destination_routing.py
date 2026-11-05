"""User-directed point-to-point missions and route visualization annotations."""
import math
import uuid
from mission_history import location_name,LOCATION_NAMES
import numpy as np
import mujoco
from multi_place_config import MISSION_TARGETS, DEST_KIOSK_PAD, DEST_KIOSK_ENTRY
from multiobjective_planner import MultiObjectivePlanner,MODES
from terrain_profile import rough_at
from energy_model import (DEFAULT_WEIGHTS,normalize_weights,objective_score,required_energy,DRIVE_PERCENT_PER_M,WALK_PERCENT_PER_M,HOTEL_PERCENT_PER_S,TURN_PERCENT_PER_RAD,TRANSFORM_PERCENT,START_STOP_PERCENT,TASK_RESERVE_PERCENT,CHARGER_RESERVE_PERCENT,LOW_BATTERY_PERCENT)

PLACES=[np.asarray(t['pos'],dtype=float) for t in MISSION_TARGETS]
NAMES=[t['name'] for t in MISSION_TARGETS]


class DestinationMission:
    def __init__(self, navigator, mode='balanced'):
        self.navigator=navigator
        self.mode=mode
        self.weights=DEFAULT_WEIGHTS.copy()
        self.frontier=[]
        self.energy_status={}
        self.energy_used=0.
        self.energy_added=0.
        self.last_transforming=False
        self.last_yaw=None
        self.next_energy_check=0.
        self.return_cache={}
        self.return_energy=0.
        self.idle_escape_cache={}
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
        self.comparisons={}
        self.comparison_paths={}
        self.previous_route=[]
        self.events=[]
        self.journey_origin='Origin depot'
        self.journey_destination=''
        self.request_id=None
        self.request_energy_start=0.
        self.notice='Choose a destination in the control panel'
        self.notice_until=0.

    def pose(self,xy,yaw):
        self.position=np.asarray(xy).copy();self.yaw=float(yaw)

    def dispatch(self,target):
        if not 0<=target<4:
            raise ValueError('Choose Place 1, 2, 3, or 4')
        self.journey_origin=location_name(self.position)
        self.journey_destination=LOCATION_NAMES[target+1]
        self.request_id=uuid.uuid4().hex[:10]
        self.request_energy_start=self.energy_used
        self.events.append(dict(event='destination_requested',time=self.elapsed,origin=self.journey_origin,to_name=self.journey_destination,request_id=self.request_id,status='queued' if self.charging or self.divert else 'requested',mode=self.mode))
        if self.charging or self.divert:
            self.resume_target=target
            if not self.divert and not self.charging:
                self.charge(self.position)
            print(f'{NAMES[target]} queued after charging.',flush=True)
            return
        self.comparisons={};self.comparison_paths={};self.frontier=[]
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

    def charge(self,xy,reason="manual"):
        if reason not in ("manual","low_battery","insufficient_energy"):raise ValueError(reason)
        if self.divert or self.charging:
            return
        if self.stage in ('moving','preview','stopping') and self.target is not None:
            self.resume_target=self.target
        self.divert=True
        self.pending_target='charger'
        self.stage='stopping'
        self.full_route=[]
        self.previous_route=[]
        self.error=None
        self.notice=(f'INSUFFICIENT TASK ENERGY - need {self.energy_status.get("required_percent",self.battery):.1f}%, have {self.battery:.1f}%; charging first' if reason=='insufficient_energy' else 'BATTERY BELOW 20% - rerouting to charging station' if reason=='low_battery' else 'Routing to charging station')
        self.notice_until=self.elapsed+10.
        self.events.append(dict(event='low_battery_diversion' if reason=='low_battery' else 'energy_charging_diversion' if reason=='insufficient_energy' else 'charging_requested',reason=reason,task_requirement_percent=self.energy_status.get('required_percent'),time=self.elapsed,battery=self.battery,position=self.position.tolist(),resume_destination=None if self.resume_target is None else self.resume_target+1))
        print(self.notice,flush=True)

    def cancel(self):
        self.events.append(dict(event='destination_cancelled',time=self.elapsed,origin=location_name(self.position),to_name=self.journey_destination,request_id=self.request_id,status='cancelled'))
        if self.divert or self.charging:
            self.resume_target=None
            return
        self.stage='idle';self.pending_target=None;self.target=None
        self.route=[];self.full_route=[];self.error=None
        self.comparison_paths={};self.comparisons={};self.previous_route=[]
        print('Destination cancelled. Waiting for Place 1-4.',flush=True)

    def set_mode(self,mode):
        if mode not in MODES:raise ValueError('Unknown objective mode')
        self.mode=mode
        if self.stage in ('moving','preview','blocked'):
            self.pending_target='charger' if self.divert else self.target
            self.stage='stopping'
        self.events.append(dict(event='objective_changed',time=self.elapsed,mode=mode,weights=self.weights.tolist(),origin=location_name(self.position),to_name=self.journey_destination))
        print('Route mode:',self.mode,flush=True)

    def toggle_mode(self):self.set_mode(MODES[(MODES.index(self.mode)+1)%len(MODES)])

    def set_weights(self,weights):
        self.weights=normalize_weights(weights)
        self.set_mode('balanced')

    def _return_cost(self,target):
        key=(self.navigator.revision,target,self.navigator.force_mode)
        if key not in self.return_cache:
            old=self.navigator.current_mode
            self.navigator.current_mode='legs' if bool(rough_at(PLACES[target],margin=1.6)) else 'wheels'
            try:
                _,options=MultiObjectivePlanner(self.navigator).alternatives(PLACES[target],DEST_KIOSK_PAD,0.,weights=self.weights,via=[DEST_KIOSK_ENTRY])
                self.return_cache[key]=options['energy'].metrics['energy_percent']
            finally:self.navigator.current_mode=old
        return self.return_cache[key]

    def _block_energy(self,reason):
        self.energy_status['decision']='blocked'
        self.energy_status['reason']=reason
        self.notice=reason;self.notice_until=self.elapsed+60.
        self.route=[];self.full_route=[];self.frontier=[];self.comparison_paths={};self.comparisons={}
        self.events.append(dict(event='energy_infeasible',time=self.elapsed,battery=self.battery,reason=reason))
        raise RuntimeError(reason)

    def avoid_obstacle(self):
        self.previous_route=[p.copy() for p in self.full_route]
        self.pending_target='charger' if self.divert else self.target
        self.stage='stopping'
        self.notice='OBSTACLE DETECTED - braking and planning a safe detour'
        self.notice_until=self.elapsed+10.
        self.events.append(dict(event='obstacle_detected',time=self.elapsed,position=self.position.tolist()))
        print(self.notice,flush=True)

    def _plan(self):
        optimizer=MultiObjectivePlanner(self.navigator)
        if self.divert:
            if np.linalg.norm(self.position-DEST_KIOSK_PAD)<.24:
                self.charging=True;self.stage='charging';self.green_hold=0.;return
            charger_front,charger_options=optimizer.alternatives(self.position,DEST_KIOSK_PAD,self.yaw,weights=self.weights,via=[DEST_KIOSK_ENTRY])
            candidate=charger_options['energy']
            needed=required_energy(candidate.metrics['energy_percent'],CHARGER_RESERVE_PERCENT)
            self.energy_status=dict(decision='charging_route',available_percent=self.battery,required_percent=needed,route_energy_percent=candidate.metrics['energy_percent'],return_energy_percent=0.,reserve_percent=CHARGER_RESERVE_PERCENT)
            if needed>self.battery+1e-8:
                self._block_energy(f'Charger unreachable with current energy: need {needed:.1f}%, have {self.battery:.1f}%. Stop for assistance.')
            selected=candidate;frontier=charger_front;representatives={'energy':candidate}
        else:
            via=[DEST_KIOSK_ENTRY] if self.depart_station else []
            frontier,representatives=optimizer.alternatives(self.position,PLACES[self.pending_target],self.yaw,weights=self.weights,via=via)
            self.return_energy=self._return_cost(self.pending_target)
            def required(c):return required_energy(c.metrics['energy_percent']+self.return_energy)
            feasible=[c for c in frontier if required(c)<=self.battery+1e-8]
            self.energy_status=dict(decision='feasible' if feasible else 'recharge_first',available_percent=self.battery,required_percent=min(map(required,frontier)),return_energy_percent=self.return_energy,reserve_percent=TASK_RESERVE_PERCENT)
            if not feasible:
                if self.battery>=99.5 and np.linalg.norm(self.position-DEST_KIOSK_PAD)<.25:
                    self._block_energy('Requested destination plus safe charger return exceeds full battery capacity. Choose a nearer task or add a charger.')
                self.charge(self.position,reason='insufficient_energy')
                self._plan();return
            representatives={mode:min(feasible,key=lambda c:objective_score(c.metrics,mode,self.weights)) for mode in MODES}
            selected=representatives[self.mode]
            self.energy_status.update(required_percent=required(selected),route_energy_percent=selected.metrics['energy_percent'],predicted_destination_percent=self.battery-selected.metrics['energy_percent'])
        self.frontier=[dict(c.record(),energy_feasible=(required_energy(c.metrics['energy_percent']+(0. if self.divert else self.return_energy),CHARGER_RESERVE_PERCENT if self.divert else TASK_RESERVE_PERCENT)<=self.battery+1e-8),score=objective_score(c.metrics,'energy' if self.divert else self.mode,self.weights)) for c in frontier]
        self.route=[p.copy() for p in selected.points[1:]]
        self.full_route=[p.copy() for p in selected.points]
        self.comparison_paths={mode:[p.copy() for p in c.points] for mode,c in representatives.items()}
        self.comparisons={mode:dict(c.metrics) for mode,c in representatives.items()}
        if self.travel_start is None:self.trail=[self.position.copy()]
        self.index=0;self.metrics=dict(selected.metrics)
        self.stage='preview';self.preview_remaining=3.;self.error=None
        self.next_energy_check=self.elapsed+1.
        if self.initial_metrics is None:self.initial_metrics=dict(self.metrics)
        self.plans.append(dict(from_name=location_name(self.position),to_name='Charging station' if self.divert else LOCATION_NAMES[self.target+1],request_id=self.request_id,origin=self.journey_origin,time=self.elapsed,destination='charger' if self.divert else self.target+1,mode='energy' if self.divert else self.mode,weights=self.weights.tolist(),points=[p.tolist() for p in self.full_route],energy_budget=dict(self.energy_status),pareto_front=self.frontier,**self.metrics))
        self.events.append(dict(event='energy_plan_checked',time=self.elapsed,**self.energy_status))
        self.navigator.replans+=1
        print(f'ROUTE READY: {self.destination_name} | {"energy-to-charger" if self.divert else self.mode} | {self.metrics["distance_m"]:.1f} m | {self.metrics["estimated_seconds"]:.0f} s | {self.metrics["energy_percent"]:.1f}% energy | budget {self.energy_status["required_percent"]:.1f}% / available {self.battery:.1f}%',flush=True)

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

    def update(self,xy,traveled,yaw,speed,omega,dt=.016,motion_paused=False,locomotion_mode='wheels',transforming=False):
        self.pose(xy,yaw);self.elapsed+=dt
        if self.travel_start is not None and self.stage in ('moving','stopping','preview'):
            self.actual_distance+=traveled
        if not self.trail or np.linalg.norm(xy-self.trail[-1])>.15:
            self.trail.append(np.asarray(xy).copy())
        if self.charging:
            before=self.battery
            self.battery=min(100.,self.battery+22.*dt)
            self.energy_added+=self.battery-before
            self.last_yaw=yaw;self.last_transforming=False
            self.green_hold=self.green_hold+dt if self.battery>=100 else 0.
            if self.green_hold>=2.4:
                self.charges+=1;self.charging=self.divert=False
                self.depart_station=True
                target=self.resume_target;self.resume_target=None
                self.stage='arrived';self.pending_target=None
                self.route=[]
                if target is not None:
                    self.dispatch(target)
                else:
                    self.target=None;self.stage='idle';self.full_route=[]
                    self.comparisons={};self.comparison_paths={};self.frontier=[]
                    self.metrics={'distance_m':0.,'estimated_seconds':0.}
                    self.journey_origin='Charging station';self.journey_destination=''
                self.events.append(dict(event='charge_complete',time=self.elapsed,battery=self.battery,resume_destination=None if target is None else target+1))
                self.notice='CHARGED TO 100% - new route to requested destination'
                self.notice_until=self.elapsed+10.
                print(self.notice,flush=True)
            return
        turn=0. if self.last_yaw is None else abs((yaw-self.last_yaw+math.pi)%(2*math.pi)-math.pi)
        self.last_yaw=yaw
        draw=traveled*(WALK_PERCENT_PER_M if locomotion_mode=='legs' else DRIVE_PERCENT_PER_M)+turn*TURN_PERCENT_PER_RAD
        if self.stage not in ('blocked',):draw+=HOTEL_PERCENT_PER_S*dt
        if transforming and not self.last_transforming:draw+=TRANSFORM_PERCENT
        self.last_transforming=transforming
        draw=min(self.battery,draw)
        self.battery-=draw;self.energy_used+=draw
        if self.stage!='blocked' and not self.divert and self.battery<LOW_BATTERY_PERCENT:
            self.charge(xy,reason='low_battery')
        if self.stage in ('moving','preview') and not self.divert and self.elapsed>=self.next_energy_check:
            self.next_energy_check=self.elapsed+1.
            remaining=self.navigator.route_metrics([self.position]+self.route[self.index:],yaw)
            needed=required_energy(remaining['energy_percent']+self.return_energy)
            self.energy_status.update(available_percent=self.battery,required_percent=needed,route_energy_percent=remaining['energy_percent'],predicted_destination_percent=self.battery-remaining['energy_percent'])
            if self.battery<needed:
                self.charge(xy,reason='insufficient_energy')
        if self.stage in ('idle','arrived') and not self.divert and self.elapsed>=self.next_energy_check:
            self.next_energy_check=self.elapsed+1.
            key=(self.navigator.revision,tuple(np.round(self.position,2)),self.navigator.current_mode,self.navigator.force_mode)
            if key not in self.idle_escape_cache:
                if np.linalg.norm(self.position-DEST_KIOSK_PAD)<.24:self.idle_escape_cache[key]=0.
                else:
                    try:
                        _,options=MultiObjectivePlanner(self.navigator).alternatives(self.position,DEST_KIOSK_PAD,yaw,weights=self.weights,via=[DEST_KIOSK_ENTRY])
                        escape=options['energy']
                        self.idle_escape_cache[key]=required_energy(escape.metrics['energy_percent'],CHARGER_RESERVE_PERCENT)
                    except RuntimeError:self.idle_escape_cache[key]=float('inf')
            if self.battery<=self.idle_escape_cache[key]+1.:
                self.energy_status=dict(required_percent=self.idle_escape_cache[key]+1.,available_percent=self.battery,decision='idle_return')
                self.charge(xy,reason='insufficient_energy')
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
                allowance=min(self.battery,START_STOP_PERCENT)
                self.battery-=allowance;self.energy_used+=allowance
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
            record=dict(origin=self.journey_origin,to_name=LOCATION_NAMES[self.target+1],request_id=self.request_id,time=self.elapsed,status='arrived',mode=self.mode,actual_energy_percent=self.energy_used-self.request_energy_start,destination=self.target+1,position=np.asarray(xy).tolist(),
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
    for mode,points in mission.comparison_paths.items():
        color={'shortest':[1.,.2,.72,.8],'fastest':[.20,1.,.55,.8],'energy':[.35,.55,1.,.9],'balanced':[.1,.95,1.,.9]}[mode]
        for a,b in zip(points,points[1:]):line(a,b,color,width=.03,z=.15 if mode=='shortest' else .20)
    for a,b in zip(mission.previous_route,mission.previous_route[1:]):
        length=float(np.linalg.norm(b-a))
        for t in np.arange(0.,length,.8):
            if length>1e-8:line(a+(b-a)*t/length,a+(b-a)*min(length,t+.35)/length,[1.,.25,.25,.65],width=.025,z=.24)
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
