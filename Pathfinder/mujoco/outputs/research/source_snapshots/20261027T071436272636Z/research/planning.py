"""Shared scene graph and bounded comparison planners. No production monkeypatches."""
from dataclasses import dataclass, asdict
import heapq
import math
import time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import distance_transform_edt
from energy_model import energy_cost, UNCERTAINTY_FACTOR, TASK_RESERVE_PERCENT
from terrain_profile import severity_at, travel_speed, split_segment, TRANSFORM_COST_SECONDS
from road_demo import ground_height

DIRECTIONS=np.array([(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)])
ANGLES=np.arctan2(DIRECTIONS[:,1],DIRECTIONS[:,0])
METHODS={
 'b1_distance':'B1 Distance A*',
 'b2_terrain':'B2 Terrain A*',
 'b3_energy':'B3 Energy A*',
 'b4_weighted':'B4 Sampled weighted sum',
    'proposed':'Proposed seeded constrained Pareto',
}

@dataclass
class Limits:
    deadline_s: float=200.
    battery_percent: float=100.
    risk_budget: float=40.
    planning_seconds: float=2.
    max_expansions: int=40000
    labels_per_state: int=8

class SceneGraph:
    """Every algorithm uses these SAME edge metrics and clearance map."""
    def __init__(self,nav,walking_only=True):
        self.nav=nav;self.n=nav.n;self.walking_only=walking_only
        self.xy=nav.lower+np.indices((self.n,self.n)).transpose(1,2,0)*nav.resolution
        self.grade=severity_at(self.xy,margin=1.1)
        self.speed=travel_speed(self.xy,walking=walking_only)
        # A footprint window measures ground height range, slope and variation.
        samples=[]
        for dx in (-nav.radius,0.,nav.radius):
            for dy in (-nav.radius,0.,nav.radius):samples.append(ground_height(self.xy+np.array([dx,dy])))
        heights=np.asarray(samples)
        self.height_range=heights.max(0)-heights.min(0)
        self.undulation=heights.std(0)
        mean_height=heights.mean(0)
        gx,gy=np.gradient(mean_height,nav.resolution)
        self.slope=np.arctan(np.hypot(gx,gy))
        self.softness=np.take(np.array([0.,.25,.6,1.]),self.grade)
        self.difficulty=np.clip(.25*(self.slope/.25+self.height_range/.12+self.undulation/.04+self.softness),0.,2.)
        self.clearance=distance_transform_edt(~nav.blocked)*nav.resolution
        self.neighbors=np.full((self.n*self.n,8),-1,dtype=np.int32)
        self.edges=np.zeros((self.n*self.n,8,4),float)
        self.turn=np.abs((ANGLES[None,:]-ANGLES[:,None]+math.pi)%(2*math.pi)-math.pi)
        xs,ys=np.where(~nav.blocked)
        for k,(dx,dy) in enumerate(DIRECTIONS):
            nx,ny=xs+dx,ys+dy
            valid=(nx>=0)&(ny>=0)&(nx<self.n)&(ny<self.n)
            x,y,nx,ny=xs[valid],ys[valid],nx[valid],ny[valid]
            valid=~nav.blocked[nx,ny]
            if dx and dy:valid&=(~nav.blocked[x+dx,y])&(~nav.blocked[x,y+dy])
            x,y,nx,ny=x[valid],y[valid],nx[valid],ny[valid]
            length=nav.resolution*math.hypot(dx,dy)
            walking=np.ones(len(x),bool) if walking_only else (self.grade[x,y]>0)|(self.grade[nx,ny]>0)
            changes=np.zeros(len(x)) if walking_only else ((self.grade[x,y]>0)!=(self.grade[nx,ny]>0)).astype(float)
            seconds=length/np.maximum(.01,np.minimum(self.speed[x,y],self.speed[nx,ny]))+changes*TRANSFORM_COST_SECONDS
            energy=length*np.where(walking,.7,.25)+seconds*.015+changes*.5
            exposure=length*(self.difficulty[x,y]+self.difficulty[nx,ny])/2
            ids=x*self.n+y
            self.neighbors[ids,k]=nx*self.n+ny
            self.edges[ids,k,:]=np.column_stack((np.full(len(x),length),seconds,energy,exposure))
        self._bounds={}

    def node(self,p):
        c=self.nav.nearest_free(np.asarray(p));return c[0]*self.n+c[1]

    def point(self,node):return self.nav.point((node//self.n,node%self.n))

    def bounds(self,goal):
        if goal not in self._bounds:
            src,k=np.where(self.neighbors>=0);dst=self.neighbors[src,k]
            # Goal distance on reversed graph is valid for directed edge metrics.
            values=[]
            for j in range(4):
                matrix=coo_matrix((self.edges[src,k,j],(dst,src)),shape=(self.n*self.n,)*2).tocsr()
                values.append(dijkstra(matrix,indices=goal,directed=True))
            self._bounds[goal]=np.asarray(values).T
        return self._bounds[goal]

    def step(self,node,heading,k,yaw):
        v=self.edges[node,k].copy()
        angle=abs((ANGLES[k]-yaw+math.pi)%(2*math.pi)-math.pi) if heading==8 else self.turn[heading,k]
        v[1]+=angle;v[2]+=angle*(.08+.015)
        return v

    def connectors(self,start,goal):
        s,g=self.node(start),self.node(goal)
        if not self.nav.segment_clear(start,self.point(s),margin=self.nav.tracking_margin):raise ValueError('Unsafe start connector')
        if not self.nav.segment_clear(self.point(g),goal,margin=self.nav.tracking_margin):raise ValueError('Unsafe goal connector')
        return s,g

    def metrics(self,points,yaw=math.pi/2):
        """Common continuous evaluation, including endpoints and start/stop cost."""
        nav=self.nav
        old,old_mode=nav.force_mode,nav.current_mode
        nav.force_mode='legs' if self.walking_only else None
        nav.current_mode='legs' if self.walking_only else 'wheels'
        # A forced leg mode must still split long straight segments at terrain
        # speed boundaries. A midpoint-only estimate can miss a rough section.
        integration_points=[np.asarray(points[0],float)]
        for a,b in zip(points,points[1:]):
            for lo,hi,_ in split_segment(a,b):
                if np.linalg.norm(hi-integration_points[-1])>1e-9:integration_points.append(hi)
        if len(integration_points)==1:integration_points.append(integration_points[0])
        try:m=nav.route_metrics(integration_points,yaw)
        finally:nav.force_mode=old;nav.current_mode=old_mode
        exposure=0.
        for a,b in zip(points,points[1:]):
            length=float(np.linalg.norm(np.asarray(b)-a))
            count=max(2,int(math.ceil(length/(nav.resolution/2)))+1)
            sample=np.linspace(a,b,count)
            cell=np.clip(np.rint((sample-nav.lower)/nav.resolution).astype(int),0,self.n-1)
            exposure+=length*float(np.mean(self.difficulty[cell[:,0],cell[:,1]]))
        m['terrain_exposure']=exposure
        return m


def path_points(graph,states,start,goal):
    points=[np.asarray(start,dtype=float)]
    for node in states:
        p=graph.point(node)
        if np.linalg.norm(p-points[-1])>1e-8:points.append(p)
    if np.linalg.norm(np.asarray(goal)-points[-1])>1e-8:points.append(np.asarray(goal,dtype=float))
    if len(points)==1:points.append(points[0].copy())
    # Preserve geometry; remove only collinear vertices, not shortcut across terrain.
    out=[]
    for p in points:
        while len(out)>1:
            a,b=out[-2:];u=b-a;v=p-b
            if abs(u[0]*v[1]-u[1]*v[0])>1e-8 or u@v<0:break
            out.pop()
        out.append(p)
    if not all(graph.nav.segment_clear(a,b,margin=graph.nav.tracking_margin) for a,b in zip(out,out[1:])):raise ValueError('Continuous route clearance failed')
    return out

def scalar_search(graph,start,goal,weights,yaw,end_time,expansion_limit):
    s,g=graph.connectors(start,goal);bounds=graph.bounds(g)
    if not np.isfinite(bounds[s,0]):return None,0,'disconnected_graph'
    weights=np.asarray(weights,float)
    state=(s,8);costs={state:0.};parent={};queue=[(float(bounds[s]@weights),0.,state)]
    expanded=0
    while queue:
        if expanded%64==0 and time.perf_counter()>end_time:return None,expanded,'timeout'
        _,cost,state=heapq.heappop(queue)
        if cost>costs.get(state,float('inf'))+1e-10:continue
        node,heading=state
        if node==g:
            nodes=[g]
            while state in parent:state=parent[state];nodes.append(state[0])
            return path_points(graph,nodes[::-1],start,goal),expanded,'found'
        expanded+=1
        if expanded>expansion_limit:return None,expanded,'expansion_limit'
        for k,nxt in enumerate(graph.neighbors[node]):
            if nxt<0:continue
            value=cost+float(graph.step(node,heading,k,yaw)@weights);key=(int(nxt),k)
            if value<costs.get(key,float('inf'))-1e-10:
                costs[key]=value;parent[key]=state
                heapq.heappush(queue,(value+float(bounds[nxt]@weights),value,key))
    return None,expanded,'no_route'

def feasible(metrics,limits,return_energy):
    required=UNCERTAINTY_FACTOR*(metrics['energy_percent']+return_energy)+TASK_RESERVE_PERCENT
    return dict(deadline_ok=metrics['estimated_seconds']<=limits.deadline_s+1e-8,
                battery_ok=required<=limits.battery_percent+1e-8,
                terrain_budget_ok=metrics['terrain_exposure']<=limits.risk_budget+1e-8,
                required_battery_percent=required)

def plan(graph,start,goal,method,limits,return_energy=0.,yaw=math.pi/2):
    if method not in METHODS:raise ValueError('Unknown method')
    # Bounds are shared case preparation, not charged to just one method.
    graph.bounds(graph.node(goal))
    begin=time.perf_counter();end=begin+limits.planning_seconds
    result={'method':method,'label':METHODS[method],'status':'no_route','points':[], 'metrics':None,'expanded':0,'candidates':[],'approximate':method=='proposed'}
    if method=='proposed':
        # First secure an energy-aware incumbent, then spend the remaining SAME
        # budget looking for constrained trade-offs. Never discard a feasible
        # incumbent solely because the multi-label refinement times out.
        seed,seed_expanded,seed_status=scalar_search(graph,start,goal,[0,0,1.,0],yaw,
            min(end,begin+limits.planning_seconds*.35),limits.max_expansions)
        seed_metrics=graph.metrics(seed,yaw) if seed is not None else None
        seed_feasible=seed_metrics is not None and all(v for k,v in feasible(seed_metrics,limits,return_energy).items() if k.endswith('_ok'))
        remaining=Limits(**asdict(limits));remaining.max_expansions=max(0,limits.max_expansions-seed_expanded)
        if remaining.max_expansions>0 and time.perf_counter()<end:
            points,expanded,status,candidates=constrained_search(graph,start,goal,remaining,return_energy,yaw,end)
        else:points,expanded,status,candidates=None,0,'budget_exhausted',[]
        if seed_feasible:
            candidates.append(seed_metrics)
            if points is None or seed_metrics['distance_m']<graph.metrics(points,yaw)['distance_m']:
                points=seed
            result['search_termination']=status;status='found'
        result.update(expanded=expanded+seed_expanded,status=status,candidates=candidates,seed_status=seed_status,seed_admissible=seed_feasible)
    else:
        patterns={
          'b1_distance':[[1.,0,0,0]],'b2_terrain':[[1.,0,0,2.]],
          'b3_energy':[[0,0,1.,0]],
          'b4_weighted':[[1/50,0,0,0],[0,1/90,0,0],[0,0,1/30,0],
            [1/150,1/270,1/90,0],[.6/50,.2/90,.2/30,0],[.2/50,.6/90,.2/30,0],[.2/50,.2/90,.6/30,0]]}
        candidates=[];status='no_route'
        for w in patterns[method]:
            if time.perf_counter()>=end:status='timeout';break
            route,count,status=scalar_search(graph,start,goal,w,yaw,end,limits.max_expansions-result['expanded'])
            result['expanded']+=count
            if route is not None:
                m=graph.metrics(route,yaw);candidates.append((route,m))
            if result['expanded']>=limits.max_expansions:break
        valid=[c for c in candidates if all(v for k,v in feasible(c[1],limits,return_energy).items() if k.endswith('_ok'))]
        pool=valid or candidates
        chosen=min(pool,key=lambda x: x[1]['distance_m']/50+x[1]['estimated_seconds']/90+x[1]['energy_percent']/30) if pool else None
        points=chosen[0] if chosen else None
        result['candidates']=[c[1] for c in candidates]
        result['status']='found' if chosen else status
        result['search_termination']=status
    if points is not None:
        result['points']=[p.tolist() for p in points]
        m=graph.metrics(points,yaw);result['metrics']=m
        result.update(feasible(m,limits,return_energy))
        result['admissible']=all(result[k] for k in ('deadline_ok','battery_ok','terrain_budget_ok'))
    else:result['admissible']=False
    result['planning_seconds']=time.perf_counter()-begin
    result['limits']=asdict(limits)
    return result

def constrained_search(graph,start,goal,limits,return_energy,yaw,end):
    """Bounded multi-label resource-constrained A*, with explicit approximation."""
    s,g=graph.connectors(start,goal);bound=graph.bounds(g)
    if not np.isfinite(bound[s,0]):return None,0,'disconnected_graph',[]
    budget=np.array([np.inf,limits.deadline_s,(limits.battery_percent-TASK_RESERVE_PERCENT)/UNCERTAINTY_FACTOR-return_energy-.2,limits.risk_budget])
    if np.any(budget[1:]<0):return None,0,'infeasible_budget',[]
    # Absolute bins bound label diversity; they do not certify exact dominance.
    bins=np.array([.5,1.,.25,.25])
    labels=[(s,8,np.zeros(4),-1)];active={0};by_state={(s,8):[0]}
    weights=np.array([1/50,1/90,1/30,.25/20])
    queue=[(float(bound[s]@weights),0)];expanded=0;solutions=[]
    while queue:
        if expanded%32==0 and time.perf_counter()>end:break
        _,idx=heapq.heappop(queue)
        if idx not in active:continue
        node,heading,values,previous=labels[idx]
        if node==g:
            nodes=[node];cur=idx
            while labels[cur][3]>=0:cur=labels[cur][3];nodes.append(labels[cur][0])
            route=path_points(graph,nodes[::-1],start,goal);metrics=graph.metrics(route,yaw)
            checks=feasible(metrics,limits,return_energy)
            if all(v for k,v in checks.items() if k.endswith('_ok')):
                solutions.append((route,metrics))
                if len(solutions)>=12:break
            continue
        expanded+=1
        if expanded>=limits.max_expansions:break
        for k,nxt in enumerate(graph.neighbors[node]):
            if nxt<0:continue
            v=values+graph.step(node,heading,k,yaw)
            if np.any(v[1:]+bound[nxt,1:]>budget[1:]+1e-8):continue
            key=(int(nxt),k);ids=by_state.get(key,[])
            if any(np.all(labels[j][2]<=v+1e-9) for j in ids):continue
            cell=np.floor(v/bins)
            same=[j for j in ids if np.array_equal(np.floor(labels[j][2]/bins),cell)]
            if same and min(float(labels[j][2]@weights) for j in same)<=float(v@weights):continue
            kept=[]
            for j in ids:
                if j in same or np.all(v<=labels[j][2]+1e-9):active.discard(j)
                else:kept.append(j)
            new=len(labels);labels.append((int(nxt),k,v,idx));kept.append(new);active.add(new)
            if len(kept)>limits.labels_per_state:
                worst=max(kept,key=lambda j:float(labels[j][2]@weights));kept.remove(worst);active.discard(worst)
            by_state[key]=kept
            if new in active:heapq.heappush(queue,(float((v+bound[nxt])@weights),new))
    if solutions:
        route,_=min(solutions,key=lambda x:(x[1]['distance_m'],x[1]['energy_percent']))
        return route,expanded,'found',[m for _,m in solutions]
    reason='timeout' if time.perf_counter()>=end else 'expansion_limit' if expanded>=limits.max_expansions else 'no_feasible_route'
    return None,expanded,reason,[]
