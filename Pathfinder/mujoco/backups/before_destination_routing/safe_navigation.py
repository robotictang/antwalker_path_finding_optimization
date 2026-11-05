"""Scene-derived, footprint-inflated A* routing and swept motion checks.

Plans against physical static geometry rather than a second hand-maintained map.
The disc includes the full leg sweep, including transformation and turning.
"""
import heapq
import math
import numpy as np
import mujoco


class SafeNavigator:
    def __init__(self, model, data, radius=1.82, resolution=0.25):
        self.radius, self.resolution = radius, resolution
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
        self.blocked = np.zeros((self.n,self.n),dtype=bool)
        for lo, hi in self.boxes:
            delta = np.maximum(np.maximum(lo-xy, xy-hi),0)
            self.blocked |= np.sum(delta*delta,axis=2) <= radius**2
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

    def segment_clear(self, start, end):
        count = max(2, int(np.linalg.norm(np.asarray(end)-start)/0.10)+2)
        points = np.linspace(start,end,count)
        delta = np.maximum(np.maximum(self.boxes[:,0,None]-points,points-self.boxes[:,1,None]),0)
        return bool(np.all(np.sum(delta*delta,axis=2) > self.radius**2))

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

    def plan(self, start, goal):
        s, g = self.nearest_free(start), self.nearest_free(goal)
        if not self.segment_clear(start,self.point(s)):
            raise RuntimeError(f'Robot starts inside inflated obstacle at {start}')
        self.adjusted_goal = np.asarray(goal) if self.clear(goal) else self.point(g)
        if self.segment_clear(start,self.adjusted_goal):
            return [self.adjusted_goal]
        queue = [(0.,s)]
        costs, parent = {s:0.}, {}
        moves = [(x,y,math.hypot(x,y)) for x in (-1,0,1) for y in (-1,0,1) if x or y]
        while queue:
            _, c = heapq.heappop(queue)
            if c == g:
                break
            for dx,dy,cost in moves:
                nxt = (c[0]+dx,c[1]+dy)
                if not(0 <= nxt[0] < self.n and 0 <= nxt[1] < self.n) or self.blocked[nxt]:
                    continue
                if dx and dy and (self.blocked[c[0]+dx,c[1]] or self.blocked[c[0],c[1]+dy]):
                    continue
                new = costs[c]+cost
                if new < costs.get(nxt,float('inf')):
                    costs[nxt] = new
                    parent[nxt] = c
                    heapq.heappush(queue,(new+math.hypot(g[0]-nxt[0],g[1]-nxt[1]),nxt))
        if g not in costs:
            raise RuntimeError(f'No collision-free route from {start} to {goal}')
        cells, c = [g], g
        while c != s:
            c = parent[c]
            cells.append(c)
        raw = [np.asarray(start)] + [self.point(c) for c in reversed(cells)] + [self.adjusted_goal]
        # Shortcut only after checking the continuous segment, including corners.
        result, i = [], 0
        while i < len(raw)-1:
            j = len(raw)-1
            while j > i+1 and not self.segment_clear(raw[i],raw[j]):
                j -= 1
            result.append(raw[j]); i = j
        return result

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
        horizon = max(dt,abs(speed)/0.625+0.12)
        for t in np.linspace(0,horizon,12)[1:]:
            if abs(omega)>1e-5:
                p = position + speed/omega*np.array([math.sin(yaw+omega*t)-math.sin(yaw), math.cos(yaw)-math.cos(yaw+omega*t)])
            else:
                p = position + speed*t*np.array([math.cos(yaw),math.sin(yaw)])
            if not self.clear(p):
                return 0.0, omega
        return speed,omega
