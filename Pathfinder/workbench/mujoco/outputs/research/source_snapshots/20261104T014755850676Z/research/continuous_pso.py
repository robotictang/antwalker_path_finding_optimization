"""A coordinate-PSO representation control, not a new proposed algorithm.

Endpoints are fixed. Internal vertices can move anywhere within map bounds;
vertex count is fixed per trial. Colliding candidates are discarded, never
repaired with an unchecked segment. Common seed and final polish are charged.
"""
import copy
import time
import numpy as np
from research import advanced, swarm

PARAMETERS=dict(particles=12,iterations=40,inertia=.65,cognitive=1.4,social=1.4,
                jitter_m=2.,minimum_internal_vertices=6,polish_fraction=.25)


def subdivide(points, minimum_internal_vertices):
    points=[np.asarray(p,float).copy() for p in points]
    while len(points)<minimum_internal_vertices+2:
        i=int(np.argmax([np.linalg.norm(b-a) for a,b in zip(points,points[1:])]))
        points.insert(i+1,(points[i]+points[i+1])/2)
    return points


def optimize(graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search):
    if not graph.walking_only:raise ValueError('Coordinate PSO supports walking only')
    cfg=copy.deepcopy(PARAMETERS);before=copy.deepcopy(swarm.PARAMETERS['proposed'])
    try:
        swarm.PARAMETERS['proposed']=copy.deepcopy(advanced.DEFAULT_INITIAL)
        initial=swarm.optimize(graph,start,goal,'proposed',limits,return_energy,yaw,seed,begin,
                              min(end,begin+advanced.PARAMETERS['seed_fraction']*limits.planning_seconds),scalar_search)
    finally:swarm.PARAMETERS['proposed']=before
    pool=advanced.Candidates(graph,limits,return_energy,yaw,begin,end,initial['optimizer']['fitness_evaluations'])
    if initial['points'] is not None:pool.evaluate(initial['points'],known_metrics=graph.metrics(initial['points'],yaw))
    pool.evaluate([start,goal]);iterations=0;raw_candidates=0;accepted_particles=0
    search_end=end-cfg['polish_fraction']*limits.planning_seconds
    if pool.best is not None and pool.live():
        route=subdivide(pool.best[1],cfg['minimum_internal_vertices']);origin=np.asarray(route[1:-1]);rng=np.random.default_rng(seed)
        n=cfg['particles'];shape=origin.shape
        positions=np.repeat(origin[None],n,axis=0)
        positions[1:]+=rng.normal(0,cfg['jitter_m'],size=positions[1:].shape)
        positions=np.clip(positions,graph.nav.lower,graph.nav.upper)
        velocities=np.zeros_like(positions);personal=np.repeat(origin[None],n,axis=0)
        best_rank=pool.best[0];ranks=[best_rank]*n;global_best=origin.copy();global_rank=best_rank
        while pool.live() and time.perf_counter()<search_end and iterations<cfg['iterations']:
            for i in range(n):
                if not pool.live() or time.perf_counter()>=search_end:break
                trial=[np.asarray(start),*positions[i],np.asarray(goal)];raw_candidates+=1
                item=pool.evaluate(trial)
                if item is None:continue
                accepted_particles+=1
                if item[0]<ranks[i]:personal[i]=positions[i].copy();ranks[i]=item[0]
                if item[0]<global_rank:global_best=positions[i].copy();global_rank=item[0]
            iterations+=1
            velocities=cfg['inertia']*velocities+cfg['cognitive']*rng.random(positions.shape)*(personal-positions)+cfg['social']*rng.random(positions.shape)*(global_best-positions)
            positions=np.clip(positions+np.clip(velocities,-cfg['jitter_m'],cfg['jitter_m']),graph.nav.lower,graph.nav.upper)
    advanced.polish(pool);best=pool.best
    return dict(points=best[1] if best else None,status='found' if best else initial['status'],expanded=initial['expanded'],
        candidates=[x[2] for x in pool.cache.values()],optimizer=dict(algorithm=method,seed=int(seed),parameters=cfg,
        fitness_evaluations=pool.evaluations,visibility_checks=initial['optimizer']['visibility_checks']+pool.checks,
        seed_status=initial['optimizer']['seed_status'],seed_attempts=initial['optimizer']['seed_attempts'],
        seed_families=initial['optimizer']['seed_families'],resumed_seed=initial['optimizer']['resumed_seed'],
        distance_fallback=initial['optimizer']['distance_fallback'],convergence=pool.trace,continuous_moves=pool.accepted_moves,
        iterations=iterations,raw_particle_candidates=raw_candidates,collision_free_particle_candidates=accepted_particles,
        representation='Fixed-count continuous internal xy vertices within map bounds; fixed endpoints; shared incumbent retained.',
        seed_and_refinement_share_budget=True,scope='A coordinate-representation control; not every possible continuous swarm planner.'))
