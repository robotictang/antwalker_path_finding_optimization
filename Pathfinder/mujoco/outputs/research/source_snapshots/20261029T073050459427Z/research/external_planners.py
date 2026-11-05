"""Actual OMPL 2.0.1 baselines with common geometry and route polishing.

Each native trial runs in a forked worker. OMPL is imported before the planner
timer; fork, native solve, simplification, polishing and IPC share that timer.
The fresh worker seeds OMPL before constructing any native random generator.
"""
import copy,math,multiprocessing,time,sys
from pathlib import Path
import numpy as np
VENDOR=Path(__file__).resolve().parents[1]/'research_vendor'
if VENDOR.exists():sys.path.insert(0,str(VENDOR))
from ompl import base as ob,geometric as og,util as ou
from research import advanced,swarm
import energy_model as em

METHODS=('ompl_rrtstar','ompl_seeded_rrtstar','ompl_rrtconnect')
PARAMETERS=dict(range_m=4.,goal_bias=.15,seed_fraction=.40,polish_fraction=.35,simplify_steps=30)

def _worker(pipe,graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search,config):
    try:
        ou.RNG.setSeed(int(seed)%4294967295 or 1);ou.setLogLevel(ou.LOG_ERROR)
        original_metrics=graph.metrics;metric_calls=[0]
        def counted(*args,**kwargs):metric_calls[0]+=1;return original_metrics(*args,**kwargs)
        graph.metrics=counted
        pool=advanced.Candidates(graph,limits,return_energy,yaw,begin,end)
        initial=None;expanded=0
        if method=='ompl_seeded_rrtstar':
            previous=copy.deepcopy(swarm.PARAMETERS['proposed'])
            try:
                swarm.PARAMETERS['proposed']=copy.deepcopy(advanced.DEFAULT_INITIAL)
                initial=swarm.optimize(graph,start,goal,'proposed',limits,return_energy,yaw,seed,begin,min(end,begin+config['seed_fraction']*limits.planning_seconds),scalar_search)
            finally:swarm.PARAMETERS['proposed']=previous
            pool.evaluations=initial['optimizer']['fitness_evaluations'];expanded=initial['expanded']
            if initial['points'] is not None:pool.evaluate(initial['points'],known_metrics=graph.metrics(initial['points'],yaw))
        counts=dict(state_checks=0,motion_checks=0,edge_cost_calls=0)
        class Validity(ob.StateValidityChecker):
            def isValid(self,state):
                counts['state_checks']+=1
                return time.perf_counter()<end and graph.nav.clear(np.array([state[0],state[1]]),margin=graph.nav.tracking_margin+.005)
        class Motion(ob.MotionValidator):
            def checkMotion(self,a,b):
                counts['motion_checks']+=1
                return time.perf_counter()<end and graph.nav.segment_clear(np.array([a[0],a[1]]),np.array([b[0],b[1]]),margin=graph.nav.tracking_margin)
        class EdgeObjective(ob.OptimizationObjective):
            def stateCost(self,state):return ob.Cost(0.)
            def motionCost(self,a,b):
                counts['edge_cost_calls']+=1
                if time.perf_counter()>=end:return ob.Cost(1e12)
                pa,pb=np.array([a[0],a[1]]),np.array([b[0],b[1]])
                heading=math.atan2(*(pb-pa)[::-1]);m=graph.metrics([pa,pb],heading)
                overhead=graph.nav.walk_speed/1.25
                vector=np.array([m[k] for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']])
                vector-=np.array([0.,overhead,em.START_STOP_PERCENT+overhead*em.HOTEL_PERCENT_PER_S,0.])
                return ob.Cost(float(np.maximum(vector,0.)@swarm.QUALITY_WEIGHTS))
            def isSymmetric(self):return True
        space=ob.RealVectorStateSpace(2);space.setBounds(float(graph.nav.lower),float(graph.nav.upper))
        si=ob.SpaceInformation(space);validity=Validity(si);motion=Motion(si);objective=EdgeObjective(si)
        si.setStateValidityChecker(validity);si.setMotionValidator(motion);si.setup()
        a,b=space.allocState(),space.allocState()
        for i in range(2):a[i]=float(start[i]);b[i]=float(goal[i])
        problem=ob.ProblemDefinition(si);problem.setStartAndGoalStates(a,b,1e-7);problem.setOptimizationObjective(objective)
        planner=og.RRTConnect(si) if method=='ompl_rrtconnect' else og.RRTstar(si)
        planner.setRange(config['range_m'])
        if method!='ompl_rrtconnect':planner.setGoalBias(config['goal_bias'])
        planner.setProblemDefinition(problem);planner.setup()
        search_end=max(time.perf_counter(),end-config['polish_fraction']*limits.planning_seconds)
        def done():return time.perf_counter()>=search_end or counts['state_checks']>=max(0,limits.max_expansions-expanded) or not pool.live()
        exact=False;solutions=0;simplified=False
        while not done():
            chunk_end=min(search_end,time.perf_counter()+.15)
            planner.solve(ob.PlannerTerminationCondition(lambda:done() or time.perf_counter()>=chunk_end))
            if problem.hasExactSolution():
                exact=True;path=problem.getSolutionPath()
                points=[np.array([path.getState(i)[0],path.getState(i)[1]]) for i in range(path.getStateCount())]
                if len(points)>1 and np.linalg.norm(points[-1]-goal)<1e-6:
                    points[0]=np.asarray(start,float);points[-1]=np.asarray(goal,float);pool.evaluate(points);solutions+=1
                if method=='ompl_rrtconnect':
                    if pool.live():
                        simplifier=og.PathSimplifier(si,problem.getGoal(),objective)
                        simplified=bool(simplifier.reduceVertices(path,config['simplify_steps'],10))
                        points=[np.array([path.getState(i)[0],path.getState(i)[1]]) for i in range(path.getStateCount())]
                        if len(points)>1:points[0]=np.asarray(start,float);points[-1]=np.asarray(goal,float);pool.evaluate(points)
                    break
        advanced.polish(pool)
        best=pool.best;seed_opt=initial['optimizer'] if initial else {}
        result=dict(points=best[1] if best else None,status='found' if best else 'no_route',expanded=expanded+counts['state_checks'],candidates=[x[2] for x in pool.cache.values()],
          optimizer=dict(algorithm=method,library='OMPL',library_version='2.0.1',seed=int(seed),parameters=config,fitness_evaluations=pool.evaluations,
            visibility_checks=pool.checks+counts['motion_checks']+seed_opt.get('visibility_checks',0),
            seed_status=seed_opt.get('seed_status',[]),seed_attempts=seed_opt.get('seed_attempts',[]),seed_families=seed_opt.get('seed_families',0),resumed_seed=seed_opt.get('resumed_seed',False),distance_fallback=seed_opt.get('distance_fallback',False),
            convergence=pool.trace,continuous_moves=pool.accepted_moves,roadmap_nodes=0,roadmap_edges=0,
            worker_metric_calls=metric_calls[0],native_exact_solution=exact,native_solution_checks=solutions,ompl_vertex_reduction=simplified,
            native_counts=counts,native_objective='Additive translation/terrain balanced-cost relaxation; excludes turn history. Final feasibility and heading-aware Q are common.',
            representation='Actual OMPL planar geometric planner plus common continuous polishing',seed_and_refinement_share_budget=True))
        pipe.send(dict(final=result))
    except BaseException as e:
        import traceback
        pipe.send(dict(error=str(e),traceback=traceback.format_exc()))
    finally:pipe.close()

def optimize(graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search):
    if not graph.walking_only:raise ValueError('OMPL comparison currently supports walking only')
    if 'fork' not in multiprocessing.get_all_start_methods():raise RuntimeError('Native OMPL isolation in this version requires a platform with fork support')
    config=copy.deepcopy(PARAMETERS);config.update(common_polish=copy.deepcopy(advanced.PARAMETERS),score_weights=swarm.QUALITY_WEIGHTS.tolist())
    context=multiprocessing.get_context('fork');reader,writer=context.Pipe(duplex=False)
    process=context.Process(target=_worker,args=(writer,graph,start,goal,method,limits,return_energy,yaw,seed,begin,end,scalar_search,config))
    process.start();writer.close();message=None
    try:
        if reader.poll(max(0.,end-time.perf_counter())+.15):message=reader.recv()
        process.join(timeout=.02)
        if process.is_alive():process.terminate();process.join(timeout=.1)
        if message is None:raise RuntimeError('OMPL worker exceeded the wall allowance and cleanup grace')
        if 'error' in message:raise RuntimeError('OMPL worker: '+message['error']+'\n'+message.get('traceback',''))
        if process.exitcode not in (0,None):raise RuntimeError('OMPL worker exited abnormally: '+str(process.exitcode))
        result=message['final'];result['optimizer']['worker_exitcode']=process.exitcode
        return result
    finally:
        reader.close()
        if process.is_alive():process.terminate();process.join(timeout=.1)
