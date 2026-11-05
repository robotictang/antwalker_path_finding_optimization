"""Visible, stationary wheel/leg transformations with assisted posture and height."""
import math
import numpy as np
import mujoco
from tripod_gait import TripodGait,clear_transform_feet
from terrain_profile import rough_at,TRANSFORM_SECONDS
from road_demo import ground_clearance
from hybrid_demo_design import DRIVE_HEIGHT,WALK_HEIGHT,WHEEL_RADIUS,WHEEL_TRACK

LEGS=('LF','LM','LR','RF','RM','RR')
STOW=np.array([0.,1.047,-2.]*6)


def ease(t):
    t=float(np.clip(t,0,1))
    return t**3*(10+t*(-15+6*t))


class HybridLocomotion:
    def __init__(self,m,d):
        self.m=m;self.d=d
        self.qids=np.array([int(m.joint(kind+'_joint_'+leg).qposadr[0]) for leg in LEGS for kind in ('coxa','femur','tibia')])
        self.dofs=np.array([int(m.joint(kind+'_joint_'+leg).dofadr[0]) for leg in LEGS for kind in ('coxa','femur','tibia')])
        self.aids=np.array([m.actuator('act_'+leg+'_'+kind).id for leg in LEGS for kind in ('hip','femur','tibia')])
        self.wheel_dofs=np.array([int(m.joint('wheel_'+name+'_joint').dofadr[0]) for name in ('FL','FR','RL','RR')])
        self.wheel_aids=np.array([m.actuator('act_wheel_'+name).id for name in ('FL','FR','RL','RR')])
        self.foot_ids=[m.geom('foot_'+leg).id for leg in LEGS]
        self.gait=TripodGait();self.mode='wheels';self.override=None
        self.target=None;self.elapsed=0.;self.transforming=False;self.braking=False
        self.start_pose=STOW.copy();self.height=DRIVE_HEIGHT
        self.phase='LATCHED / DRIVE';self.events=[];self.clock=0.
        for leg in LEGS:
            for part in ('coxa','femur','tibia'):
                m.body_gravcomp[m.body(part+'_'+leg).id]=1.
        d.qpos[self.qids]=STOW;d.ctrl[self.aids]=STOW

    @property
    def busy(self):return self.transforming or self.braking

    @property
    def progress(self):return min(1.,self.elapsed/TRANSFORM_SECONDS) if self.transforming else 0.

    def toggle(self):
        current=self.target if self.busy else self.mode
        self.override='legs' if current=='wheels' else 'wheels'
        print('Manual transformation requested:',self.override,flush=True)

    def automatic(self):
        self.override=None
        print('Automatic terrain transformation enabled.',flush=True)

    def should_stop(self,xy,goal,moving):
        if self.busy:return True
        if not moving and self.override is None:return False
        if self.override is not None:
            desired=self.override
        else:
            desired='legs' if bool(rough_at(xy,margin=1.6 if self.mode=='legs' else 1.1)) else 'wheels'
            if moving:
                delta=np.asarray(goal)-xy;distance=float(np.linalg.norm(delta))
                if distance>1e-8 and bool(rough_at(xy+delta/distance*min(1.2,distance))):
                    desired='legs'
        if desired!=self.mode:
            self.target=desired;self.braking=True;self.phase='BRAKING BEFORE TRANSFORM'
            return True
        return False

    def tick(self,xy,yaw,speed,omega,dt=.016):
        self.clock+=dt
        if self.braking and abs(speed)<.015 and abs(omega)<.03:
            self.braking=False;self.transforming=True;self.elapsed=0.
            self.start_pose=self.d.qpos[self.qids].copy();self.gait.reset()
            self.events.append(dict(time=self.clock,event='begin',from_mode=self.mode,to_mode=self.target,position=np.asarray(xy).tolist()))
            print('TRANSFORM:',self.mode,'->',self.target,'(stationary)',flush=True)
        if self.transforming:
            self.elapsed=min(TRANSFORM_SECONDS,self.elapsed+dt)
            p=self.progress
            # Static IK holds feet above the ground while the chassis changes height.
            self.gait.reset()
            stand=self.gait.targets(xy,yaw,float(self.d.qpos[2]),0.,0.)
            if self.target=='legs':
                if p<.2:
                    self.phase='UNLATCH SIDE HOOKS'
                    pose=self.start_pose.copy()
                    pose[1::3]-=.12*math.sin(math.pi*p/.2)
                    self.height=DRIVE_HEIGHT
                elif p<.65:
                    self.phase='UNFOLD AND PLANT SIX FEET'
                    blend=ease((p-.2)/.45)
                    pose=(1-blend)*STOW+blend*stand
                    self.height=DRIVE_HEIGHT
                else:
                    self.phase='RAISE CHASSIS / UNLOAD WHEELS'
                    self.height=DRIVE_HEIGHT+(WALK_HEIGHT-DRIVE_HEIGHT)*ease((p-.65)/.35)
                    pose=stand
            else:
                if p<.2:
                    self.phase='GATHER LEGS INTO STANCE'
                    pose=(1-ease(p/.2))*self.start_pose+ease(p/.2)*stand
                    self.height=WALK_HEIGHT
                elif p<.5:
                    self.phase='LOWER ONTO FOUR WHEELS'
                    self.height=WALK_HEIGHT+(DRIVE_HEIGHT-WALK_HEIGHT)*ease((p-.2)/.3)
                    pose=stand
                elif p<.9:
                    self.phase='FOLD LEGS INTO SIDE POCKETS'
                    blend=ease((p-.5)/.4)
                    pose=(1-blend)*stand+blend*STOW
                    self.height=DRIVE_HEIGHT
                else:
                    self.phase='ENGAGE HOOK LATCHES'
                    pose=STOW.copy();pose[1::3]-=.035*math.sin(math.pi*(p-.9)/.1)
                    self.height=DRIVE_HEIGHT
            pose=clear_transform_feet(pose,float(self.d.qpos[2]),ground_clearance(xy))
            self.d.qpos[self.qids]=pose;self.d.qvel[self.dofs]=0.;self.d.ctrl[self.aids]=pose
            if self.elapsed>=TRANSFORM_SECONDS:
                old=self.mode;self.mode=self.target;self.transforming=False;self.target=None
                self.height=WALK_HEIGHT if self.mode=='legs' else DRIVE_HEIGHT
                self.gait.reset()
                self.events.append(dict(time=self.clock,event='complete',from_mode=old,to_mode=self.mode,position=np.asarray(xy).tolist()))
                print('Transformation complete:',self.mode,flush=True)
        elif self.mode=='wheels':
            self.phase='LATCHED / DRIVE';self.height=DRIVE_HEIGHT
            self.d.qpos[self.qids]=STOW;self.d.qvel[self.dofs]=0.;self.d.ctrl[self.aids]=STOW
            self.gait.reset()
        else:
            self.phase='GROUNDED TRIPOD WALK';self.height=WALK_HEIGHT
            self.d.ctrl[self.aids]=self.gait.targets(xy,yaw,float(self.d.qpos[2]),speed,omega)
        if self.mode=='wheels' and not self.busy:
            left=(speed-omega*WHEEL_TRACK/2)/WHEEL_RADIUS
            right=(speed+omega*WHEEL_TRACK/2)/WHEEL_RADIUS
            self.d.ctrl[self.wheel_aids]=[left,right,left,right]
            self.d.qvel[self.wheel_dofs]=[left,right,left,right]
        else:
            self.d.ctrl[self.wheel_aids]=0.;self.d.qvel[self.wheel_dofs]=0.

    def update_lights(self,battery,charging):
        pulse=.6+.4*math.sin(self.clock*2*math.pi*1.4)
        if battery<20 and not charging:color=[pulse,.025,.015,1.]
        elif charging and battery<85:color=[1.,.4+.2*pulse,.03,1.]
        elif charging and battery<100:color=[.06,.5+.5*pulse,.18,1.]
        elif battery<65:color=[1.,.55,.025,1.]
        else:color=[.06,1.,.2,1.]
        for material in ('battery_light','battery_halo_mat'):
            mid=self.m.material(material).id;self.m.mat_rgba[mid]=color;self.m.mat_emission[mid]=.8
        count=int(np.ceil(battery/20))
        for i in range(1,6):
            mid=self.m.material('bat_led_mat_'+str(i)).id
            self.m.mat_rgba[mid]=color if i<=count else [.035,.045,.035,1.]
        self.d.ctrl[self.m.actuator('act_lidar_pan').id]=.65*math.sin(self.clock*2*math.pi*.4)
