"""Seeded PSO, ACO and a Pareto-beam route refiner on safe visibility corridors.

These are explicitly HYBRID path optimizers: a charged A* seed supplies a valid
route. PSO optimizes random-key waypoint inclusion; ACO learns pheromones on
forward visible chords. All use the same continuous evaluator and constraints.
No method is promised to win. Wall time includes seeds, visibility and evaluation.
"""
import math
import time
import numpy as np

PARAMETERS={
 'pso':dict(particles=16,inertia=.72,cognitive=1.49,social=1.49,velocity_clip=.25,max_iterations=40),
 'aco':dict(ants=12,alpha=1.,beta=2.,evaporation=.2,deposit=1.,max_iterations=40),
 'proposed':dict(beam_width=6,archive_size=16,max_evaluations=240,portfolio=True),
 'b7_greedy':dict(max_evaluations=2),
}

def quality(metrics):
    """Declared common scalar preference for NEW methods; lower is better."""
    return float(metrics['distance_m']/50+metrics['estimated_seconds']/90+
                 metrics['energy_percent']/30+.25*metrics['terrain_exposure']/20)

def rank(metrics,limits,return_energy):
    required=1.25*(metrics['energy_percent']+return_energy)+6.
    violations=np.array([metrics['estimated_seconds']/max(limits.deadline_s,1e-9)-1,
      required/max(limits.battery_percent,1e-9)-1,
      metrics['terrain_exposure']/max(limits.risk_budget,1e-9)-1])
    violation=float(np.maximum(violations,0.).sum())
    return (int(violation>1e-9),violation,quality(metrics))

class Corridor:
    def __init__(self,graph,points,yaw,limits,return_energy,end,begin):
        self.graph=graph;self.points=[np.asarray(p,float) for p in points]
        self.yaw=yaw;self.limits=limits;self.return_energy=return_energy
        # A* already continuously checked each original segment inside the same
        # budget. Cache those proven edges without charging a duplicate check.
        self.end=end;self.begin=begin;self.edges={(i,i+1):True for i in range(len(points)-1)};self.cache={}
        self.evaluations=0;self.checks=0;self.trace=[];self.best=None
        self.archive=[];self.cap=240

    def visible(self,a,b):
        if b<=a:return False
        key=(a,b)
        if key not in self.edges:
            if time.perf_counter()>=self.end:return False
            self.checks+=1
            self.edges[key]=self.graph.nav.segment_clear(self.points[a],self.points[b],margin=self.graph.nav.tracking_margin)
        return self.edges[key]

    def decode(self,keys):
        wanted=[0]+[i+1 for i,k in enumerate(keys) if k>=.5]+[len(self.points)-1]
        result=[0]
        for target in wanted[1:]:
            while result[-1]<target:
                current=result[-1]
                # Unsafe omissions are repaired using the original safe corridor.
                nxt=next((j for j in range(target,current,-1) if self.visible(current,j)),None)
                if nxt is None:return None
                result.append(nxt)
        return tuple(result)

    def evaluate(self,indices):
        if indices is None:return None
        key=tuple(indices)
        if key in self.cache:return self.cache[key]
        if self.evaluations>=self.cap or time.perf_counter()>=self.end:return None
        if not all(self.visible(a,b) for a,b in zip(key,key[1:])):return None
        route=[self.points[i] for i in key]
        metrics=self.graph.metrics(route,self.yaw);value=rank(metrics,self.limits,self.return_energy)
        result=(value,key,metrics);self.cache[key]=result;self.evaluations+=1
        if self.best is None or value<self.best[0]:
            self.best=result
            self.trace.append(dict(evaluations=self.evaluations,elapsed_s=time.perf_counter()-self.begin,
                score=value[2],feasible=value[0]==0))
        vector=np.array([metrics[k] for k in ('distance_m','estimated_seconds','energy_percent','terrain_exposure')])
        if not any(np.all(v<=vector+1e-9) for v,_ in self.archive):
            self.archive=[(v,r) for v,r in self.archive if not np.all(vector<=v+1e-9)]
            self.archive.append((vector,result))
            self.archive=sorted(self.archive,key=lambda item:item[1][0])[:16]
        return result

    def initialize(self):
        # Both swarm methods receive exactly the same original and greedy seeds.
        self.evaluate(tuple(range(len(self.points))))
        self.evaluate(self.decode(np.zeros(max(0,len(self.points)-2))))

    def result(self):
        if self.best is None:return None
        return [self.points[i] for i in self.best[1]]

def particle_swarm(corridor,rng):
    p=PARAMETERS['pso'];dimensions=max(0,len(corridor.points)-2)
    if not dimensions:return dict(iterations=0)
    positions=rng.random((p['particles'],dimensions));positions[0]=0.;positions[1]=1.
    velocities=rng.uniform(-.1,.1,positions.shape);personal=positions.copy()
    values=[(2,float('inf'),float('inf'))]*len(positions);global_position=positions[0].copy();global_value=values[0]
    iterations=0
    for iteration in range(p['max_iterations']):
        if time.perf_counter()>=corridor.end or corridor.evaluations>=corridor.cap:break
        for i,x in enumerate(positions):
            if time.perf_counter()>=corridor.end:break
            result=corridor.evaluate(corridor.decode(x))
            if result is not None and result[0]<values[i]:values[i]=result[0];personal[i]=x.copy()
            if values[i]<global_value:global_value=values[i];global_position=personal[i].copy()
        r1,r2=rng.random(positions.shape),rng.random(positions.shape)
        velocities=np.clip(p['inertia']*velocities+p['cognitive']*r1*(personal-positions)+
          p['social']*r2*(global_position-positions),-p['velocity_clip'],p['velocity_clip'])
        positions=np.clip(positions+velocities,0.,1.);iterations=iteration+1
    return dict(iterations=iterations,particles=p['particles'])

def ant_colony(corridor,rng):
    p=PARAMETERS['aco'];n=len(corridor.points);pheromone=np.ones((n,n));iterations=0;ants_built=0
    for iteration in range(p['max_iterations']):
        if time.perf_counter()>=corridor.end or corridor.evaluations>=corridor.cap:break
        generation=[]
        for _ in range(p['ants']):
            if time.perf_counter()>=corridor.end:break
            path=[0]
            while path[-1]<n-1:
                current=path[-1]
                choices=[j for j in range(current+1,n) if corridor.visible(current,j)]
                if not choices:break
                lengths=np.array([np.linalg.norm(corridor.points[j]-corridor.points[current])+
                  np.linalg.norm(corridor.points[-1]-corridor.points[j]) for j in choices])
                # Favor larger safe progress without excluding near alternatives.
                eta=(np.array(choices)-current)/np.maximum(lengths,1e-6)
                probabilities=np.power(pheromone[current,choices],p['alpha'])*np.power(eta,p['beta'])
                probabilities/=probabilities.sum()
                path.append(int(rng.choice(choices,p=probabilities)))
            if path[-1]==n-1:
                ants_built+=1;result=corridor.evaluate(tuple(path))
                if result is not None:generation.append(result)
        pheromone*=1-p['evaporation']
        # Feasibility-first deposits; infeasible candidates get a penalty, never
        # become a fake successful route. Elitism retains the best-so-far path.
        for value,path,_ in generation+([corridor.best] if corridor.best is not None else []):
            deposit=p['deposit']/(1+value[2]+100*value[1]+100*value[0])
            for a,b in zip(path,path[1:]):pheromone[a,b]+=deposit
        np.clip(pheromone,1e-4,10.,out=pheromone);iterations=iteration+1
    return dict(iterations=iterations,ants_constructed=ants_built,ants_per_iteration=p['ants'])

def pareto_beam(corridor):
    """Resource-aware bounded subsequence search, distinct from swarm updates."""
    if corridor.best is None:return dict(iterations=0)
    original=corridor.cache.get(tuple(range(len(corridor.points))))
    beam=([original] if original is not None else [])+[r for _,r in corridor.archive]
    seen=set(corridor.cache);iterations=0
    while beam and corridor.evaluations<corridor.cap and time.perf_counter()<corridor.end:
        children=[]
        for _,path,_ in beam:
            # Removing several vertices at once allows coordinated shortcuts.
            for width in (8,4,2,1):
                for i in range(1,len(path)-width):
                    if time.perf_counter()>=corridor.end or corridor.evaluations>=corridor.cap:break
                    candidate=path[:i]+path[i+width:]
                    if candidate in seen:continue
                    seen.add(candidate)
                    value=corridor.evaluate(candidate)
                    if value is not None:children.append(value)
        beam=sorted(children,key=lambda r:r[0])[:PARAMETERS['proposed']['beam_width']]
        # Revisit diverse non-dominated branches, rather than retaining only a
        # single scalar incumbent. All evaluations still use the common budget.
        signatures={r[1] for r in beam}
        beam.extend(r for _,r in corridor.archive if r[1] not in signatures)
        beam=beam[:12];iterations+=1
        if not children:break
    return dict(iterations=iterations,archive_size=len(corridor.archive))

def optimize(graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search):
    rng=np.random.default_rng(seed);corridors=[];expanded=0;seed_status=[]
    weights=[[0.,0.,1.,0.]]
    if method=='proposed':weights.extend([[0.,1.,0.,0.],[1.,0.,0.,0.]])
    # Reserve a majority of the budget for the method's actual refinement.
    seed_deadline=min(end,begin+limits.planning_seconds*.30)
    seen=set()
    for w in weights:
        if time.perf_counter()>=seed_deadline or expanded>=limits.max_expansions:break
        route,count,status=scalar_search(graph,start,goal,w,yaw,seed_deadline,limits.max_expansions-expanded)
        expanded+=count;seed_status.append(status)
        if route is None:continue
        signature=tuple(tuple(p) for p in route)
        if signature in seen:continue
        seen.add(signature)
        c=Corridor(graph,route,yaw,limits,return_energy,end,begin);c.initialize();corridors.append(c)
        # Initialize the common incumbent early before spending on extra seeds.
    details=[]
    if corridors:
        if method in ('pso','aco'):
            details.append(particle_swarm(corridors[0],rng) if method=='pso' else ant_colony(corridors[0],rng))
        elif method=='proposed':
            ordered=sorted(corridors,key=lambda c:c.best[0] if c.best else (3,float('inf'),float('inf')))
            for i,c in enumerate(ordered):
                remaining=max(0.,end-time.perf_counter())
                c.end=min(end,time.perf_counter()+remaining/(len(ordered)-i))
                details.append(pareto_beam(c))
        # b7_greedy intentionally stops after common seed initialization.
    valid=[c for c in corridors if c.best is not None]
    best=min(valid,key=lambda c:c.best[0]) if valid else None
    traces=sorted([item for c in corridors for item in c.trace],key=lambda x:x['elapsed_s'])
    return dict(points=best.result() if best else None,expanded=expanded,
      status='found' if best else 'timeout' if time.perf_counter()>=end else 'no_route',
      candidates=[r[2] for c in corridors for _,r in c.archive],
      optimizer=dict(algorithm=method,seed=int(seed),parameters=PARAMETERS[method],details=details,
        seed_status=seed_status,fitness_evaluations=sum(c.evaluations for c in corridors),
        visibility_checks=sum(c.checks for c in corridors),convergence=traces,
        representation='A* seeded, forward collision-checked waypoint shortcut corridors',
        common_quality='distance/50 + time/90 + energy/30 + 0.25*terrain_exposure/20',
        seed_and_refinement_share_budget=True))
