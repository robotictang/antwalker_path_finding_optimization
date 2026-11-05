"""Independent weighted-search checks, Pareto safety, and shared energy accounting."""
import heapq,json,math
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from multiobjective_planner import MultiObjectivePlanner,MODES,pareto_front
from destination_routing import DestinationMission
from energy_model import *
from terrain_profile import rough_at,WHEEL_SPEED,WALK_SPEED,TRANSFORM_COST_SECONDS
from multi_place_config import DEST_BASE,MISSION_TARGETS
ROOT=Path(__file__).resolve().parent

# A small obstacle/terrain grid enables a fully independent, uninformed Dijkstra
# reference over every heading state, including diagonal corner exclusions.
nav=object.__new__(SafeNavigator)
nav.lower=-8.;nav.upper=8.;nav.resolution=.5;nav.n=33;nav.radius=.10;nav.tracking_margin=0.
nav.hybrid=True;nav.current_mode='wheels';nav.force_mode=None;nav.wheel_speed=WHEEL_SPEED;nav.walk_speed=WALK_SPEED
nav.boxes=np.array([[[-.8,-3.],[1.5,3.]]])
xy=nav.lower+np.indices((nav.n,nav.n)).transpose(1,2,0)*nav.resolution
nav.blocked=np.zeros((nav.n,nav.n),bool)
for lo,hi in nav.boxes:
    delta=np.maximum(np.maximum(lo-xy,xy-hi),0)
    nav.blocked|=(delta**2).sum(2)<=(nav.radius+nav.resolution*math.sqrt(2)/2+.005)**2
nav.rough_grid=rough_at(xy)
start=np.array([-6.,-6.]);goal=np.array([7.,1.]);yaw=math.pi/2
moves=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
angles=[math.atan2(y,x) for x,y in moves]
def independent_dijkstra(weights):
    weights=np.asarray(weights)/OBJECTIVE_SCALES;s=nav.cell(start);g=nav.cell(goal)
    queue=[(0.,(*s,-1))];cost={(*s,-1):0.}
    while queue:
        distance,state=heapq.heappop(queue)
        if distance!=cost[state]:continue
        x,y,h=state
        if (x,y)==g:return distance
        for k,(dx,dy) in enumerate(moves):
            nx,ny=x+dx,y+dy
            if not(0<=nx<nav.n and 0<=ny<nav.n) or nav.blocked[nx,ny]:continue
            if dx and dy and (nav.blocked[x+dx,y] or nav.blocked[x,y+dy]):continue
            length=nav.resolution*math.hypot(dx,dy)
            incoming=yaw if h==-1 else angles[h]
            turn=abs((angles[k]-incoming+math.pi)%(2*math.pi)-math.pi)
            a,b=bool(nav.rough_grid[x,y]),bool(nav.rough_grid[nx,ny]);change=int(a!=b)
            seconds=length/(WALK_SPEED if a or b else WHEEL_SPEED)+turn+TRANSFORM_COST_SECONDS*change
            energy=length*(WALK_PERCENT_PER_M if a or b else DRIVE_PERCENT_PER_M)+seconds*HOTEL_PERCENT_PER_S+turn*TURN_PERCENT_PER_RAD+change*TRANSFORM_PERCENT
            value=distance+float(weights@np.array([length,seconds,energy]));nxt=(nx,ny,k)
            if value<cost.get(nxt,float('inf')):cost[nxt]=value;heapq.heappush(queue,(value,nxt))
    raise AssertionError('Reference graph disconnected')
checks=[]
for mode in MODES:
    weights=objective_weights(mode,[.2,.3,.5])
    route=nav.plan(start,goal,mode=mode,yaw=yaw,weights=weights)
    reference=independent_dijkstra(weights)
    assert nav.last_grid_cost is not None and abs(reference-nav.last_grid_cost)<1e-9,(mode,reference,nav.last_grid_cost)
    assert all(nav.segment_clear(a,b) for a,b in zip([start]+route,route))
    checks.append(dict(mode=mode,astar_cost=nav.last_grid_cost,dijkstra_cost=reference))

m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d)
nav=SafeNavigator(m,d);planner=MultiObjectivePlanner(nav);rows=[]
for i,t in enumerate(MISSION_TARGETS):
    front,representatives=planner.alternatives(DEST_BASE,t['pos'],math.pi/2)
    assert len(pareto_front(front))==len(front)
    for c in front:
        assert all(nav.segment_clear(a,b) for a,b in zip(c.points,c.points[1:]))
        assert c.metrics['energy_percent']>0
    for mode,c in representatives.items():assert abs(objective_score(c.metrics,mode)-min(objective_score(o.metrics,mode) for o in front))<1e-10
    rows.append(dict(destination=i+1,frontier=[c.record() for c in front],objectives={k:c.metrics for k,c in representatives.items()}))

# Motion, hotel load, turns, and the one-off transformation fee share coefficients.
mission=DestinationMission(nav);mission.battery=50.;mission.stage='idle';mission.next_energy_check=float('inf');mission.last_yaw=0.
mission.update(np.array([0.,0.]),1.,.2,0.,0.,dt=1.,locomotion_mode='legs')
assert abs(mission.energy_used-(WALK_PERCENT_PER_M+.2*TURN_PERCENT_PER_RAD+HOTEL_PERCENT_PER_S))<1e-10
before=mission.energy_used
mission.update(np.array([0.,0.]),0.,.2,0.,0.,dt=1.,transforming=True,motion_paused=True)
mission.update(np.array([0.,0.]),0.,.2,0.,0.,dt=1.,transforming=True,motion_paused=True)
assert abs(mission.energy_used-before-(TRANSFORM_PERCENT+2*HOTEL_PERCENT_PER_S))<1e-10
assert abs(50.-mission.battery-mission.energy_used)<1e-10
for bad in ([0,0,0],[-1,1,1],[float('nan'),1,1]):
    try:normalize_weights(bad)
    except ValueError:pass
    else:raise AssertionError('Invalid weights accepted')

result=dict(weighted_astar_matches_independent_dijkstra=checks,actual_map_routes=rows,shared_motion_energy_accounting=True,invalid_weight_rejection=True,pareto_set='sampled supported non-dominated routes',objective_scales=OBJECTIVE_SCALES.tolist(),default_weights=DEFAULT_WEIGHTS.tolist())
(ROOT/'outputs/multiobjective_algorithm_validation.json').write_text(json.dumps(result,indent=2))
print('PASS: all four scalarizations match independent Dijkstra; all destinations have checked non-dominated alternatives; shared energy ledger and weight validation passed.')
