"""V4: geometry diversification plus feasibility-ranked continuous route polishing.

Existing v3 refinement supplies a charged incumbent. A small visibility roadmap
can explore outside its waypoint subsequences. Local coordinate search then
moves vertices under the unchanged continuous evaluator and collision rules.
No result from another method's trial is read or used by this planner.
"""
import copy,heapq,math,time
import numpy as np
import energy_model as em
from research.swarm import quality,rank

PARAMETERS=dict(seed_fraction=.40,roadmap_fraction=.32,max_landmarks=44,polish_steps=[.75,.25,.08],max_evaluations=240)
METHODS=('proposed_v4','proposed_v4_no_polish','proposed_v4_no_landmarks','pso_polished','aco_polished')

class Candidates:
    def __init__(self,graph,limits,return_energy,yaw,begin,end,used=0):
        self.graph=graph;self.limits=limits;self.return_energy=return_energy;self.yaw=yaw;self.begin=begin;self.end=end
        self.evaluations=used;self.checks=0;self.cache={};self.best=None;self.trace=[];self.accepted_moves=0;self.roadmap_edges=0;self.roadmap_expansions=0
    def live(self):return time.perf_counter()<self.end and self.evaluations<PARAMETERS['max_evaluations']
    def clear(self,a,b):
        if time.perf_counter()>=self.end:return False
        self.checks+=1
        return self.graph.nav.segment_clear(a,b,margin=self.graph.nav.tracking_margin)
    def evaluate(self,points,known_metrics=None):
        if not self.live():return None
        points=[np.asarray(p,float) for p in points]
        if len(points)<2 or not np.isfinite(points).all():return None
        signature=tuple(tuple(np.round(p,7)) for p in points)
        if signature in self.cache:return self.cache[signature]
        if known_metrics is None:
            if any(not self.clear(a,b) for a,b in zip(points,points[1:])):return None
            m=self.graph.metrics(points,self.yaw);self.evaluations+=1
        else:m=known_metrics
        item=(rank(m,self.limits,self.return_energy),points,m);self.cache[signature]=item
        if self.best is None or item[0]<self.best[0]:
            self.best=item;self.trace.append(dict(elapsed_s=time.perf_counter()-self.begin,evaluations=self.evaluations,score=item[0][2],feasible=item[0][0]==0))
        return item

def landmarks(pool,start,goal,seed_routes,cap):
    nav=pool.graph.nav;a=np.asarray(start,float);b=np.asarray(goal,float);raw=[a,b]
    for route in seed_routes:raw.extend(route[1:-1])
    pad=nav.radius+nav.tracking_margin+.06
    for lo,hi in np.asarray(nav.boxes).reshape(-1,2,2):
        raw.extend([np.array([x,y]) for x in (lo[0]-pad,hi[0]+pad) for y in (lo[1]-pad,hi[1]+pad)])
    # Grade boundaries guide alternative routes around slow patches. Query exact
    # scoped terrain severity, not observed evaluation outcomes or hidden data.
    bounds=getattr(getattr(pool.graph.nav,'research_terrain',None),'bounds',None)
    if bounds is None:
        from research import planning
        owner=getattr(planning.severity_at,'__self__',None);bounds=getattr(owner,'bounds',[])
    for x0,x1,y0,y1 in bounds:
        raw.extend([np.array([x,y]) for x in (x0-1.22,x1+1.22) for y in (y0-1.22,y1+1.22)])
    seen={tuple(a),tuple(b)};extra=[]
    for p in raw[2:]:
        if time.perf_counter()>=pool.end:break
        key=tuple(np.round(p,6))
        if key in seen:continue
        seen.add(key)
        if np.any(p<nav.lower) or np.any(p>nav.upper) or not pool.clear(p,p):continue
        extra.append(p)
    # Geometry-only ranking, independent of method outcomes and test scores.
    extra.sort(key=lambda p:float(np.linalg.norm(p-a)+np.linalg.norm(p-b)))
    return [a,b]+extra[:max(0,cap-2)]

def visibility_search(pool,nodes,end,expansion_cap):
    n=len(nodes);adj=[[] for _ in nodes];overhead=np.array([0.,.6,em.START_STOP_PERCENT+.6*em.HOTEL_PERCENT_PER_S,0.])
    pairs=sorted(((float(np.linalg.norm(nodes[j]-nodes[i])),i,j) for i in range(n) for j in range(i+1,n)))
    for _,i,j in pairs:
        if time.perf_counter()>=end:break
        if not pool.clear(nodes[i],nodes[j]):continue
        heading=math.atan2(*(nodes[j]-nodes[i])[::-1]);m=pool.graph.metrics([nodes[i],nodes[j]],heading)
        v=np.maximum(np.array([m[k] for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']])-overhead,0.)
        adj[i].append((j,v));adj[j].append((i,v));pool.roadmap_edges+=1
    if not adj[0] or not adj[1]:return []
    routes=[];weights=[np.array([1/50,1/90,1/30,.25/20]),np.array([0.,1.,0.,0.]),np.array([0.,0.,1.,0.])]
    for w in weights:
        if time.perf_counter()>=end or pool.roadmap_expansions>=expansion_cap:break
        queue=[(0.,0.,(-1,0))];costs={(-1,0):0.};parents={}
        while queue and time.perf_counter()<end and pool.roadmap_expansions<expansion_cap:
            _,cost,state=heapq.heappop(queue)
            if cost>costs.get(state,float('inf'))+1e-10:continue
            previous,current=state
            if current==1:
                path=[1];cursor=state
                while cursor in parents:cursor=parents[cursor];path.append(cursor[1])
                route=[nodes[k] for k in reversed(path)];pool.evaluate(route);routes.append(route);break
            pool.roadmap_expansions+=1
            incoming=pool.yaw if previous<0 else math.atan2(*(nodes[current]-nodes[previous])[::-1])
            for nxt,vector in adj[current]:
                if nxt==previous or nxt==0:continue
                heading=math.atan2(*(nodes[nxt]-nodes[current])[::-1]);turn=abs((heading-incoming+math.pi)%(2*math.pi)-math.pi)
                step=vector+np.array([0.,turn,turn*(em.TURN_PERCENT_PER_RAD+em.HOTEL_PERCENT_PER_S),0.]);value=cost+float(step@w);key=(current,nxt)
                if value>=costs.get(key,float('inf'))-1e-10:continue
                costs[key]=value;parents[key]=state
                remaining=float(np.linalg.norm(nodes[1]-nodes[nxt]));bound=np.array([remaining,remaining/.75,em.WALK_PERCENT_PER_M*remaining+em.HOTEL_PERCENT_PER_S*remaining/.75,0.])
                heapq.heappush(queue,(value+float(bound@w),value,key))
    return routes

def polish(pool):
    if pool.best is None:return
    directions=np.array([(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)],float)
    directions[4:]/=math.sqrt(2)
    for step in PARAMETERS['polish_steps']:
        changed=True;passes=0
        while changed and pool.live() and passes<3:
            changed=False;passes+=1;route=[p.copy() for p in pool.best[1]]
            # Whole-route shortcut candidates and freely moved internal vertices.
            for i in range(1,len(route)-1):
                if not pool.live():return
                before=pool.best[0]
                pool.evaluate(route[:i]+route[i+1:])
                if pool.best[0]<before:pool.accepted_moves+=1;changed=True;break
                a,p,b=route[i-1:i+2];delta=b-a;fraction=float(np.clip((p-a)@delta/max(delta@delta,1e-12),0.,1.));projection=a+fraction*delta
                candidates=[p+.5*(projection-p),.5*(a+b),*[p+step*v for v in directions]]
                for q in candidates:
                    if not pool.live():return
                    if np.linalg.norm(q-a)<.03 or np.linalg.norm(q-b)<.03:continue
                    trial=route[:i]+[q]+route[i+1:];before=pool.best[0];pool.evaluate(trial)
                    if pool.best[0]<before:pool.accepted_moves+=1;changed=True;route=[p.copy() for p in pool.best[1]];break
                if changed:break

def optimize(graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search):
    from research.swarm import optimize as old_optimize
    if not graph.walking_only:raise ValueError('Version 4 visibility and continuous refinement currently supports walking only')
    config=copy.deepcopy(PARAMETERS);base='pso' if method=='pso_polished' else 'aco' if method=='aco_polished' else 'proposed'
    use_landmarks=method.startswith('proposed_v4') and method!='proposed_v4_no_landmarks';use_polish=method!='proposed_v4_no_polish'
    seed_end=min(end,begin+config['seed_fraction']*limits.planning_seconds)
    initial=old_optimize(graph,start,goal,base,limits,return_energy,yaw,seed,begin,seed_end,scalar_search)
    used=initial['optimizer']['fitness_evaluations'];pool=Candidates(graph,limits,return_energy,yaw,begin,end,used)
    if initial['points'] is not None:pool.evaluate(initial['points'],known_metrics=graph.metrics(initial['points'],yaw))
    # A direct candidate is safe only when the exact common collision query says so.
    pool.evaluate([start,goal]);nodes=[]
    if use_landmarks and pool.live():
        nodes=landmarks(pool,start,goal,[initial['points']] if initial['points'] is not None else [],config['max_landmarks'])
        roadmap_end=min(end,time.perf_counter()+config['roadmap_fraction']*limits.planning_seconds)
        visibility_search(pool,nodes,roadmap_end,max(0,limits.max_expansions-initial['expanded']))
    if use_polish:polish(pool)
    best=pool.best;trace=initial['optimizer'].get('convergence',[])+pool.trace;trace.sort(key=lambda r:r['elapsed_s']);convergence=[];lowest=float('inf')
    for point in trace:
        if point['feasible'] and point['score']<lowest-1e-12:lowest=point['score'];convergence.append(point)
    config.update(landmark_diversification=use_landmarks,continuous_polish=use_polish,initial_refiner=base)
    return dict(points=best[1] if best else None,status='found' if best else initial['status'],expanded=initial['expanded']+pool.roadmap_expansions,candidates=[v[2] for v in pool.cache.values()],
      optimizer=dict(algorithm=method,seed=int(seed),parameters=config,fitness_evaluations=pool.evaluations,
        visibility_checks=initial['optimizer']['visibility_checks']+pool.checks,seed_status=initial['optimizer']['seed_status'],seed_attempts=initial['optimizer']['seed_attempts'],
        resumed_seed=initial['optimizer']['resumed_seed'],distance_fallback=initial['optimizer']['distance_fallback'],seed_families=initial['optimizer']['seed_families'],
        convergence=convergence,continuous_moves=pool.accepted_moves,roadmap_nodes=len(nodes),roadmap_edges=pool.roadmap_edges,roadmap_expansions=pool.roadmap_expansions,
        representation='A* seeded incumbent plus geometry landmarks and collision-checked continuous waypoint movement',seed_and_refinement_share_budget=True,
        comparison_scope='New representation can explore outside old waypoint subsequences. Polished PSO and ACO controls use the same polishing operator and total budget.',
        common_quality='distance/50 + time/90 + energy/30 + 0.25*terrain_exposure/20'))
