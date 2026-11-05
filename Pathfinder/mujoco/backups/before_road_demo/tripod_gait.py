"""Ground-referenced tripod gait with planted stance feet and smooth swing IK.

The mission preview retains assisted chassis velocity/attitude control. This gait
is not a balance controller or proof of torque-feasible hardware locomotion.
"""
import math
import numpy as np


class TripodGait:
    def __init__(self):
        self.time = 0.0
        self.feet = None
        self.swing_start = np.zeros((6,3))
        self.swing_end = np.zeros((6,3))
        self.was_swing = np.zeros(6,dtype=bool)
        self.hips = np.array([[.32,.41],[0,.41],[-.32,.41],[.32,-.41],[0,-.41],[-.32,-.41]])
        self.home = np.array([[.73,1.26],[0,1.45],[-.73,1.26],[.73,-1.26],[0,-1.45],[-.73,-1.26]])
        self.phase = np.array([0,.5,0,.5,0,.5])

    def reset(self):
        self.feet = None
        self.was_swing[:] = False
        self.time = 0.0

    def targets(self, xy, yaw, height, speed, omega, dt=.016):
        rotation = np.array([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]])
        home_world = self.home @ rotation.T + xy
        if self.feet is None:
            self.feet = np.column_stack([home_world,np.full(6,.050)])
        moving = abs(speed)>.005 or abs(omega)>.005
        # Finish any swing already started before settling at rest.
        if moving or self.was_swing.any():
            self.time += dt
        frequency, duty = .95, .60
        poses=[]
        for i in range(6):
            phi=(self.time*frequency+self.phase[i])%1
            swing=phi>=duty and (moving or self.was_swing[i])
            if swing:
                if not self.was_swing[i]:
                    self.swing_start[i]=self.feet[i]
                    horizon=.5/frequency
                    future_yaw=yaw+omega*horizon
                    r=np.array([[math.cos(future_yaw),-math.sin(future_yaw)],[math.sin(future_yaw),math.cos(future_yaw)]])
                    future_xy=xy+speed*horizon*np.array([math.cos(yaw),math.sin(yaw)])
                    self.swing_end[i,:2]=future_xy+r@self.home[i]
                    self.swing_end[i,2]=.050
                u=(phi-duty)/(1-duty)
                ease=u**3*(10+u*(-15+6*u))
                self.feet[i]=(1-ease)*self.swing_start[i]+ease*self.swing_end[i]
                self.feet[i,2]+=.13*math.sin(math.pi*u)**2
            elif self.was_swing[i]:
                self.feet[i]=self.swing_end[i]
            self.was_swing[i]=swing
            local=(self.feet[i,:2]-xy)@rotation-self.hips[i]
            if i>=3:
                local=-local
            radial=np.linalg.norm(local)-.157
            z=self.feet[i,2]-height-.1085
            knee=-math.acos(float(np.clip((radial**2+z**2-.700**2-.764**2)/(2*.700*.764),-1,1)))
            femur=math.atan2(z,radial)-math.atan2(.764*math.sin(knee),.700+.764*math.cos(knee))
            hip=math.atan2(-local[0],local[1])
            poses.extend([np.clip(hip,-.785,.785),np.clip(femur,-1.047,1.047),np.clip(knee,-2.094,.349)])
        return np.array(poses)


def clear_transform_feet(pose, body_height):
    """Keep folded/deploying feet above the ground during assisted morphing."""
    safe = np.asarray(pose).copy()
    for i in range(6):
        femur, knee = safe[3*i+1:3*i+3]
        minimum_sine = (.053-body_height-.1085-.700*math.sin(femur))/.764
        lower_knee = math.asin(float(np.clip(minimum_sine,-1,1)))-femur
        safe[3*i+2] = max(knee,lower_knee)
    return safe
