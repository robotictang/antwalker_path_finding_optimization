"""V5 candidate: direct-route bound, geometry allocation and resource search.

This is an experimental hypothesis, not an assertion of superiority. It never
reads a saved result or another method's incumbent. Every candidate is ranked
by the unchanged feasible-first balanced objective.
"""
import copy,heapq,math,time
import numpy as np
import energy_model as em
from research import advanced,swarm

PARAMETERS=dict(seed_clear=.25,seed_blocked=.40,roadmap_clear=.20,
                roadmap_blocked=.45,direct_gap=.002,max_landmarks=52,
                resource_search=True)

def optimistic_score(graph,start,goal):
    distance=float(np.linalg.norm(np.asarray(goal)-start))
    seconds=distance/graph.nav.walk_speed+graph.nav.walk_speed/1.25
    energy=em.WALK_PERCENT_PER_M*distance+em.HOTEL_PERCENT_PER_S*seconds+em.START_STOP_PERCENT
    return distance/50+seconds/90+energy/30

def search_weights(pool,adaptive=True):
    balanced=np.array([1/50,1/90,1/30,.25/20])
    weights=[balanced,np.array([0.,1.,0.,0.]),np.array([0.,0.,1.,0.])]
    if not adaptive:return weights,[]
    weights.append(np.array([0.,0.,0.,1.]))
    if pool.best is None:return weights,[]
    m=pool.best[2];ratios=[m['estimated_seconds']/max(pool.limits.deadline_s,1e-9),
      (1.25*(m['energy_percent']+pool.return_energy)+6)/max(pool.limits.battery_percent,1e-9),
      m['terrain_exposure']/max(pool.limits.risk_budget,1e-9)]
    # A violated resource gets first use of the roadmap search stage. This
    # changes exploration order only, never the shared final ranking.
    if pool.best[0][0]:
        priority=int(np.argmax(ratios))+1
        weights=[weights[priority]]+[w for i,w in enumerate(weights) if i!=priority]
    return weights,ratios

def visibility_search(pool,nodes,end,expansion_cap,adaptive):
    n=len(nodes);adj=[[] for _ in nodes]
    stop=pool.graph.nav.walk_speed/1.25
    overhead=np.array([0.,stop,em.START_STOP_PERCENT+stop*em.HOTEL_PERCENT_PER_S,0.])
    pairs=sorted(((float(np.linalg.norm(nodes[j]-nodes[i])),i,j) for i in range(n) for j in range(i+1,n)),key=lambda t:(0 if t[1] in (0,1) else 1,t[0]))
    build_end=time.perf_counter()+.60*max(0.,end-time.perf_counter())
    for _,i,j in pairs:
        if time.perf_counter()>=build_end:break
        if not pool.clear(nodes[i],nodes[j]):continue
        heading=math.atan2(*(nodes[j]-nodes[i])[::-1]);m=pool.graph.metrics([nodes[i],nodes[j]],heading)
        v=np.maximum(np.array([m[k] for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']])-overhead,0.)
        adj[i].append((j,v));adj[j].append((i,v));pool.roadmap_edges+=1
    weights,ratios=search_weights(pool,adaptive)
    if not adj[0] or not adj[1]:return ratios
    for w in weights:
        if time.perf_counter()>=end or pool.roadmap_expansions>=expansion_cap or not pool.live():break
        queue=[(0.,0.,(-1,0))];costs={(-1,0):0.};parents={}
        while queue and time.perf_counter()<end and pool.roadmap_expansions<expansion_cap:
            _,cost,state=heapq.heappop(queue)
            if cost>costs.get(state,float('inf'))+1e-10:continue
            previous,current=state
            if current==1:
                path=[1];cursor=state
                while cursor in parents:cursor=parents[cursor];path.append(cursor[1])
                pool.evaluate([nodes[k] for k in reversed(path)]);break
            pool.roadmap_expansions+=1
            incoming=pool.yaw if previous<0 else math.atan2(*(nodes[current]-nodes[previous])[::-1])
            for nxt,vector in adj[current]:
                if nxt==previous or nxt==0:continue
                heading=math.atan2(*(nodes[nxt]-nodes[current])[::-1]);turn=abs((heading-incoming+math.pi)%(2*math.pi)-math.pi)
                step=vector+np.array([0.,turn,turn*(em.TURN_PERCENT_PER_RAD+em.HOTEL_PERCENT_PER_S),0.]);value=cost+float(step@w);key=(current,nxt)
                if value>=costs.get(key,float('inf'))-1e-10:continue
                costs[key]=value;parents[key]=state
                distance=float(np.linalg.norm(nodes[1]-nodes[nxt]));seconds=distance/pool.graph.nav.walk_speed
                bound=np.array([distance,seconds,em.WALK_PERCENT_PER_M*distance+em.HOTEL_PERCENT_PER_S*seconds,0.])
                heapq.heappush(queue,(value+float(bound@w),value,key))
    return ratios

def optimize(graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search):
    if not graph.walking_only:raise ValueError('V5 supports walking only')
    cfg=copy.deepcopy(PARAMETERS);fixed=method=='proposed_v5_fixed'
    use_landmarks=method!='proposed_v5_no_landmarks';use_polish=method!='proposed_v5_no_polish'
    pool=advanced.Candidates(graph,limits,return_energy,yaw,begin,end)
    direct=pool.evaluate([start,goal]);direct_clear=direct is not None
    lower=optimistic_score(graph,np.asarray(start,float),goal);early=False
    initial=None;nodes=[];ratios=[];expanded=0
    if not fixed and direct is not None and direct[0][0]==0 and direct[0][2]<=lower*(1+cfg['direct_gap'])+1e-10:
        early=True
    else:
        seed_fraction=advanced.PARAMETERS['seed_fraction'] if fixed else cfg['seed_clear' if direct_clear else 'seed_blocked']
        roadmap_fraction=advanced.PARAMETERS['roadmap_fraction'] if fixed else cfg['roadmap_clear' if direct_clear else 'roadmap_blocked']
        seed_end=min(end,begin+seed_fraction*limits.planning_seconds)
        previous=copy.deepcopy(swarm.PARAMETERS['proposed']);previous_cap=swarm.FITNESS_CAP
        try:
            swarm.PARAMETERS['proposed']=copy.deepcopy(advanced.DEFAULT_INITIAL)
            swarm.FITNESS_CAP=max(0,previous_cap-pool.evaluations)
            initial=swarm.optimize(graph,start,goal,'proposed',limits,return_energy,yaw,seed,begin,seed_end,scalar_search)
        finally:
            swarm.PARAMETERS['proposed']=previous;swarm.FITNESS_CAP=previous_cap
        pool.evaluations+=initial['optimizer']['fitness_evaluations'];expanded=initial['expanded']
        if initial['points'] is not None:pool.evaluate(initial['points'],known_metrics=graph.metrics(initial['points'],yaw))
        if use_landmarks and pool.live():
            nodes=advanced.landmarks(pool,start,goal,[initial['points']] if initial['points'] is not None else [],cfg['max_landmarks'])
            roadmap_end=min(end,time.perf_counter()+roadmap_fraction*limits.planning_seconds)
            ratios=visibility_search(pool,nodes,roadmap_end,max(0,limits.max_expansions-expanded),not fixed and cfg['resource_search'])
        if use_polish:advanced.polish(pool)
        cfg.update(actual_seed_fraction=seed_fraction,actual_roadmap_fraction=roadmap_fraction)
    opt=initial['optimizer'] if initial else {};best=pool.best
    trace=opt.get('convergence',[])+pool.trace;trace.sort(key=lambda p:p['elapsed_s']);convergence=[];lowest=float('inf')
    for p in trace:
        if p['feasible'] and p['score']<lowest-1e-12:convergence.append(p);lowest=p['score']
    cfg.update(fixed_allocation=fixed,landmark_diversification=use_landmarks,continuous_polish=use_polish,common_polish=copy.deepcopy(advanced.PARAMETERS))
    return dict(points=best[1] if best else None,status='found' if best else initial['status'] if initial else 'no_route',
      expanded=expanded+pool.roadmap_expansions,candidates=[v[2] for v in pool.cache.values()],
      optimizer=dict(algorithm=method,parameters=cfg,seed=int(seed),fitness_evaluations=pool.evaluations,
       visibility_checks=opt.get('visibility_checks',0)+pool.checks,seed_status=opt.get('seed_status',[]),
       seed_attempts=opt.get('seed_attempts',[]),resumed_seed=opt.get('resumed_seed',False),distance_fallback=opt.get('distance_fallback',False),
       seed_families=opt.get('seed_families',0),convergence=convergence,continuous_moves=pool.accepted_moves,
       roadmap_nodes=len(nodes),roadmap_edges=pool.roadmap_edges,roadmap_expansions=pool.roadmap_expansions,
       direct_bound_exit=early,optimistic_score=lower,resource_pressure=ratios,direct_clear=direct_clear,
       representation='Direct-route bound check, geometry-dependent stage allocation, resource-prioritized visibility search and common continuous polishing',
       seed_and_refinement_share_budget=True,common_quality='distance/50 + time/90 + energy/30 + 0.25*terrain_exposure/20'))
