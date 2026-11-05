"""Physics-substep measurements, explicitly separate from battery assumptions."""
import math
import numpy as np
import mujoco
from scipy.spatial import ConvexHull, QhullError

class Telemetry:
    def __init__(self,model,foot_ids,leg_actuators):
        self.model=model;self.foot_ids=set(map(int,foot_ids));self.leg_actuators=np.asarray(leg_actuators)
        self.robot=model.body('robot').id
        self.work=0.;self.leg_work=0.;self.abs_work=0.;self.peak_power=0.
        self.tilt_sum=0.;self.max_tilt=0.;self.samples=0
        self.support_sum=0.;self.min_support=6;self.no_support=0
        self.slip_distance=0.;self.slip_sum=0.;self.slip_samples=0
        self.margin_sum=0.;self.margin_samples=0;self.min_margin=None

    def sample(self,data,dt):
        power=data.actuator_force*data.actuator_velocity
        positive=np.maximum(power,0.)
        self.work+=float(positive.sum())*dt
        self.leg_work+=float(positive[self.leg_actuators].sum())*dt
        self.abs_work+=float(np.abs(power).sum())*dt
        self.peak_power=max(self.peak_power,float(positive.sum()))
        w,x,y,z=data.xquat[self.robot]
        tilt=math.degrees(math.acos(float(np.clip(1-2*(x*x+y*y),-1,1))))
        self.max_tilt=max(self.max_tilt,tilt);self.tilt_sum+=tilt*tilt;self.samples+=1
        contact=set()
        for c in data.contact:
            if c.dist>.002:continue
            a,b=int(c.geom1),int(c.geom2)
            if a in self.foot_ids and b not in self.foot_ids:contact.add(a)
            if b in self.foot_ids and a not in self.foot_ids:contact.add(b)
        self.support_sum+=len(contact);self.min_support=min(self.min_support,len(contact));self.no_support+=int(not contact)
        for foot in contact:
            velocity=np.zeros(6)
            mujoco.mj_objectVelocity(self.model,data,mujoco.mjtObj.mjOBJ_GEOM,foot,velocity,0)
            slip=float(np.linalg.norm(velocity[3:5]))
            self.slip_distance+=slip*dt;self.slip_sum+=slip;self.slip_samples+=1
        if len(contact)>=3:
            pts=np.asarray([data.geom_xpos[i,:2] for i in contact])
            try:
                hull=ConvexHull(pts)
                # Signed distance from projected subtree COM to support edges.
                equations=hull.equations
                com=data.subtree_com[self.robot,:2]
                margin=float(np.min(-(equations[:,:2]@com+equations[:,2])/np.linalg.norm(equations[:,:2],axis=1)))
                self.min_margin=margin if self.min_margin is None else min(self.min_margin,margin)
                self.margin_sum+=margin;self.margin_samples+=1
            except QhullError:pass

    def result(self):
        return dict(positive_actuator_work_j=self.work,positive_leg_work_j=self.leg_work,
          absolute_actuator_work_j=self.abs_work,peak_positive_actuator_power_w=self.peak_power,
          max_tilt_deg=self.max_tilt,rms_tilt_deg=math.sqrt(self.tilt_sum/max(1,self.samples)),
          mean_contact_feet=self.support_sum/max(1,self.samples),minimum_contact_feet=self.min_support,
          no_foot_contact_fraction=self.no_support/max(1,self.samples),
          mean_contact_slip_mps=self.slip_sum/self.slip_samples if self.slip_samples else None,
          summed_contact_slip_m=self.slip_distance,
          min_support_margin_m=self.min_margin,
          mean_support_margin_m=self.margin_sum/self.margin_samples if self.margin_samples else None,
          physics_samples=self.samples,
          assisted_model=True,mechanical_work_is_battery_energy=False)
