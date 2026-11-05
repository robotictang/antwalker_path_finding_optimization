"""Scene-derived, footprint-inflated A* routing and swept motion checks.

Plans against physical static geometry rather than a second hand-maintained map.
The disc includes the full leg sweep, including transformation and turning.
"""
import heapq
import math
import numpy as np
import mujoco
from terrain_profile import rough_at,split_segment,WHEEL_SPEED,WALK_SPEED,TRANSFORM_COST_SECONDS


class SafeNavigator:
    def __init__(self, model, data, radius=1.82, resolution=0.25):
        self.radius, self.resolution = radius, resolution
        self.tracking_margin=.12
        self.hybrid=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,"wheel_FL_joint")>=0
        self.force_mode=None
        self.current_mode="wheels" if self.hybrid else "legs"
        self.wheel_speed=WHEEL_SPEED if self.hybrid else WALK_SPEED
        self.walk_speed=WALK_SPEED
        self.lower, self.upper = -34.0, 34.0
        self.n = round((self.upper-self.lower)/resolution)+1
        robot = model.body('robot').id
        descendants = {robot}
        for body in range(robot+1, model.nbody):
            if model.body_parentid[body] in descendants:
                descendants.add(body)
        self.robot_geoms = np.array([i for i in range(model.ngeom) if model.geom_bodyid[i] in descendants and (model.geom_contype[i] or model.geom_conaffinity[i])])
        boxes = []
        self.obstacle_geoms = []
        for i in range(model.ngeom):
            if model.geom_bodyid[i] in descendants or not (model.geom_contype[i] or model.geom_conaffinity[i]):
                continue
            if model.geom_type[i] in (mujoco.mjtGeom.mjGEOM_PLANE, mujoco.mjtGeom.mjGEOM_HFIELD):
                continue
            rotation = data.geom_xmat[i].reshape(3,3)
            center = data.geom_xpos[i] + rotation @ model.geom_aabb[i,:3]
            extent = np.abs(rotation) @ model.geom_aabb[i,3:]
            # Flat road/terrain surfaces support the robot rather than block it.
            if center[2]+extent[2] < 0.12 or center[2]-extent[2] > 1.65:
                continue
            boxes.append((center[:2]-extent[:2], center[:2]+extent[:2]))
            self.obstacle_geoms.append(i)
        self.robot_geom_set = set(map(int,self.robot_geoms))
        self.obstacle_geom_set = set(self.obstacle_geoms)
        self.boxes = np.asarray(boxes)
        xy = self.lower + np.indices((self.n,self.n)).transpose(1,2,0)*resolution
        self.rough_grid=rough_at(xy) if self.hybrid else np.ones((self.n,self.n),dtype=bool)
        self.blocked = np.zeros((self.n,self.n),dtype=bool)
        for lo, hi in self.boxes:
            delta = np.maximum(np.maximum(lo-xy, xy-hi),0)
            self.blocked |= np.sum(delta*delta,axis=2) <= (radius + self.tracking_margin + resolution*math.sqrt(2)/2 + .005)**2
        self.path = []
        self.goal_key = None
        self.adjusted_goal = None
        self.replans = 0

    def clear(self, point, margin=0.0):
        p = np.asarray(point)
        if np.any(p < self.lower) or np.any(p > self.upper):
            return False
        delta = np.maximum(np.maximum(self.boxes[:,0]-p,p-self.boxes[:,1]),0)
        return bool(np.all(np.sum(delta*delta,axis=1) > (self.radius+margin)**2))

    def segment_clear(self, start, end, margin=0.):
        """Exact segment-to-AABB clearance, including the inflated robot radius."""
        start,end=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
        if np.any(np.minimum(start,end)<self.lower) or np.any(np.maximum(start,end)>self.upper):
            return False
        vector=end-start
        # If the segment intersects an obstacle rectangle, the distance is zero.
        near=np.full(len(self.boxes),-np.inf);far=np.full(len(self.boxes),np.inf)
        for axis in range(2):
            if abs(vector[axis])<1e-12:
                outside=(start[axis]<self.boxes[:,0,axis]) | (start[axis]>self.boxes[:,1,axis])
                near[outside]=np.inf
            else:
                t0=(self.boxes[:,0,axis]-start[axis])/vector[axis]
                t1=(self.boxes[:,1,axis]-start[axis])/vector[axis]
                near=np.maximum(near,np.minimum(t0,t1));far=np.minimum(far,np.maximum(t0,t1))
        if np.any(np.maximum(near,0)<=np.minimum(far,1)):
            return False
        lo,hi=self.boxes[:,0],self.boxes[:,1]
        corners=np.stack([lo,hi,np.column_stack((lo[:,0],hi[:,1])),np.column_stack((hi[:,0],lo[:,1]))],axis=1)
        t=np.clip(np.sum((corners-start)*vector,axis=2)/max(float(vector@vector),1e-20),0,1)
        distances=np.min(np.sum((corners-start-t[:,:,None]*vector)**2,axis=2),axis=1)
        for endpoint in (start,end):
            delta=np.maximum(np.maximum(lo-endpoint,endpoint-hi),0)
            distances=np.minimum(distances,np.sum(delta*delta,axis=1))
        return bool(np.all(distances>(self.radius+margin+.005)**2))

    def cell(self, point):
        return tuple(np.clip(np.rint((np.asarray(point)-self.lower)/self.resolution).astype(int),0,self.n-1))

    def point(self, cell):
        return self.lower+np.asarray(cell)*self.resolution

    def nearest_free(self, point, max_distance=3.0):
        c = self.cell(point)
        if not self.blocked[c] and self.clear(point):
            return c
        candidates = np.argwhere(~self.blocked)
        distances = np.linalg.norm(self.lower+candidates*self.resolution-point,axis=1)
        idx = int(np.argmin(distances))
        if distances[idx] > max_distance:
            raise RuntimeError(f'No safe standing area within {max_distance}m of {point}')
        return tuple(candidates[idx])

    def motion_segments(self,start,end):
        if self.force_mode is not None:
            return [(np.asarray(start),np.asarray(end),self.force_mode=='legs')]
        return split_segment(start,end)

    def route_metrics(self,points,yaw=0.,speed=None,turn_rate=1.):
        points=np.asarray(points,dtype=float)
        deltas=np.diff(points,axis=0)
        lengths=np.linalg.norm(deltas,axis=1)
        headings=np.arctan2(deltas[:,1],deltas[:,0])[lengths>1e-8]
        turns=np.diff(np.r_[yaw,headings]);turns=(turns+math.pi)%(2*math.pi)-math.pi
        length=float(lengths.sum());seconds=float(np.abs(turns).sum())/turn_rate
        drive=walk=0.;changes=0
        walking=self.current_mode=='legs'
        initial_speed=self.walk_speed if walking else self.wheel_speed
        for a,b in zip(points,points[1:]):
            for lo,hi,rough in self.motion_segments(a,b):
                rough=rough or not self.hybrid
                distance=float(np.linalg.norm(hi-lo))
                if distance<1e-9:continue
                if rough!=walking:
                    seconds+=TRANSFORM_COST_SECONDS;changes+=1;walking=rough
                if rough:walk+=distance
                else:drive+=distance
                seconds+=distance/(self.walk_speed if rough else self.wheel_speed)
        if length>1e-8:
            final_speed=self.walk_speed if walking else self.wheel_speed
            seconds+=(initial_speed+final_speed)/(2*1.25)
        return dict(distance_m=length,estimated_seconds=seconds,
                    driving_distance_m=drive,walking_distance_m=walk,transformations=changes)

    def plan(self, start, goal, mode='fastest', yaw=0.):
        """Optimal 8-neighbor A* for distance or distance/speed + heading turns.

        The 0.25m grid conservatively covers the 1.82m swept footprint. Fastest
        refers to this static-map travel-time model, not a hardware guarantee.
        """
        if mode not in ('shortest','fastest'):
            raise ValueError('Route mode must be shortest or fastest')
        start,goal=np.asarray(start,dtype=float),np.asarray(goal,dtype=float)
        if not self.clear(start) or not self.clear(goal):
            raise RuntimeError('Start or requested destination lies inside robot obstacle clearance')
        if np.linalg.norm(goal-start)<1e-8:
            return [goal.copy()]
        if self.segment_clear(start,goal,margin=self.tracking_margin) and (mode=='shortest' or not any(r for _,_,r in self.motion_segments(start,goal))):
            self.last_grid_cost=None
            return [goal.copy()]
        s,g=self.nearest_free(start),self.nearest_free(goal)
        if not self.segment_clear(start,self.point(s)) or not self.segment_clear(self.point(g),goal):
            raise RuntimeError('Cannot connect requested endpoints to safe navigation grid')
        speed,turn_rate=self.wheel_speed,1.
        directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
        headings=[math.atan2(dy,dx) for dx,dy in directions]
        initial_heading=yaw
        if np.linalg.norm(self.point(s)-start)>1e-8:
            initial_heading=math.atan2(*(self.point(s)-start)[::-1])
        initial=(s[0],s[1],-1)
        costs={initial:0.};parent={};closed=set()
        heuristic=lambda c: math.hypot(g[0]-c[0],g[1]-c[1])*self.resolution/(speed if mode=='fastest' else 1.)
        queue=[(heuristic(s),0.,initial)]
        final=None
        while queue:
            _,cost,state=heapq.heappop(queue)
            if cost!=costs.get(state) or state in closed:
                continue
            closed.add(state)
            if state[:2]==g:
                final=state;break
            for heading,(dx,dy) in enumerate(directions):
                nx,ny=state[0]+dx,state[1]+dy
                if not(0<=nx<self.n and 0<=ny<self.n) or self.blocked[nx,ny]:
                    continue
                if dx and dy and (self.blocked[state[0]+dx,state[1]] or self.blocked[state[0],state[1]+dy]):
                    continue
                length=self.resolution*math.hypot(dx,dy)
                if mode=='shortest':
                    edge=length
                    nxt=(nx,ny,0)
                else:
                    incoming=initial_heading if state[2]<0 else headings[state[2]]
                    turn=abs((headings[heading]-incoming+math.pi)%(2*math.pi)-math.pi)
                    rough0=bool(self.rough_grid[state[0],state[1]]) if self.force_mode is None else self.force_mode=="legs"
                    rough1=bool(self.rough_grid[nx,ny]) if self.force_mode is None else self.force_mode=="legs"
                    surface_speed=self.walk_speed if rough0 or rough1 else self.wheel_speed
                    edge=length/surface_speed+turn/turn_rate+(TRANSFORM_COST_SECONDS if rough0!=rough1 else 0.)
                    nxt=(nx,ny,heading)
                new=cost+edge
                if new<costs.get(nxt,float('inf')):
                    costs[nxt]=new;parent[nxt]=state
                    heapq.heappush(queue,(new+heuristic((nx,ny)),new,nxt))
        if final is None:
            raise RuntimeError(f'No collision-free route from {start} to {goal}')
        self.last_grid_cost=costs[final]
        states=[final]
        while states[-1]!=initial:
            states.append(parent[states[-1]])
        raw=[start]+[self.point(c[:2]) for c in reversed(states)]+[goal]
        # Remove duplicate and collinear vertices without changing the grid path.
        compressed=[]
        for point in raw:
            if compressed and np.linalg.norm(point-compressed[-1])<1e-8:
                continue
            while len(compressed)>=2:
                a,b=compressed[-2],compressed[-1]
                u,v=b-a,point-b
                if abs(u[0]*v[1]-u[1]*v[0])>1e-8 or float(u@v)<0:
                    break
                compressed.pop()
            compressed.append(point)
        # Cost-aware shortcuts over the grid route. Never accept an unsafe segment.
        changed=True
        while changed:
            changed=False
            for i in range(len(compressed)-2):
                for j in range(len(compressed)-1,i+1,-1):
                    if not self.segment_clear(compressed[i],compressed[j],margin=self.tracking_margin):
                        continue
                    candidate=compressed[:i+1]+compressed[j:]
                    old=self.route_metrics(compressed,yaw)
                    new=self.route_metrics(candidate,yaw)
                    key='distance_m' if mode=='shortest' else 'estimated_seconds'
                    if new[key]<=old[key]+1e-8:
                        compressed=candidate;changed=True;break
                if changed:
                    break
        if not all(self.segment_clear(a,b) for a,b in zip(compressed,compressed[1:])):
            raise RuntimeError('Route failed continuous swept-footprint validation')
        if mode=='fastest':
            # Continuous simplification can improve the distance candidate beyond
            # the heading-grid candidate. Compare using the same final time model.
            grid_cost=self.last_grid_cost
            distance_candidate=[start]+self.plan(start,goal,mode='shortest',yaw=yaw)
            self.last_grid_cost=grid_cost
            if self.route_metrics(distance_candidate,yaw)['estimated_seconds']<self.route_metrics(compressed,yaw)['estimated_seconds']:
                compressed=distance_candidate
        self.adjusted_goal=goal.copy()
        return [np.asarray(point) for point in compressed[1:]]

    def steer(self, start, goal):
        key = tuple(np.round(goal,3))
        if key != self.goal_key or not self.path or not self.segment_clear(start,self.path[0]):
            self.path = self.plan(start,goal)
            self.goal_key = key
            self.replans += 1
        while len(self.path)>1 and np.linalg.norm(self.path[0]-start)<0.35:
            if not self.segment_clear(start,self.path[1]):
                break
            self.path.pop(0)
        return self.path[0]

    def limit_motion(self, position, yaw, speed, omega, dt=0.016):
        # Check braking horizon as well as this frame; fail closed before contact.
        horizon = max(dt,abs(speed)/1.25+0.12)
        for t in np.linspace(0,horizon,12)[1:]:
            if abs(omega)>1e-5:
                p = position + speed/omega*np.array([math.sin(yaw+omega*t)-math.sin(yaw), math.cos(yaw)-math.cos(yaw+omega*t)])
            else:
                p = position + speed*t*np.array([math.cos(yaw),math.sin(yaw)])
            if not self.clear(p):
                return 0.0, omega
        return speed,omega
