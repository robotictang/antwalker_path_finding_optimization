"""Check all destination pairs and compare weighted A* with independent Dijkstra."""
from pathlib import Path
import json,math
import numpy as np
import mujoco
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from safe_navigation import SafeNavigator
from terrain_profile import rough_at,TRANSFORM_COST_SECONDS
from multi_place_config import DEST_BASE,MISSION_TARGETS

ROOT=Path(__file__).resolve().parent
m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d)
nav=SafeNavigator(m,d);points=[DEST_BASE]+[t['pos'] for t in MISSION_TARGETS]
records=[]
for source,start in enumerate(points):
    nav.current_mode='legs' if bool(rough_at(start)) else 'wheels'
    for target,goal in enumerate(points):
        if source==target:continue
        options={}
        for mode in ('shortest','fastest'):
            path=nav.plan(start,goal,mode=mode,yaw=math.pi/2)
            assert all(nav.segment_clear(a,b) for a,b in zip([start]+path,path))
            assert np.linalg.norm(path[-1]-goal)<1e-8
            options[mode]=nav.route_metrics([start]+path,math.pi/2)
        records.append(dict(source=source,target=target,options=options))

# Construct an independent sparse directed graph, with heading state for time cost.
n=nav.n;ids=np.arange(n*n).reshape(n,n);xgrid,ygrid=np.indices((n,n));free=~nav.blocked
moves=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
heads=np.array([math.atan2(y,x) for x,y in moves]);edges=[]
for k,(dx,dy) in enumerate(moves):
    x,y=np.where(free&(xgrid+dx>=0)&(xgrid+dx<n)&(ygrid+dy>=0)&(ygrid+dy<n))
    valid=free[x+dx,y+dy]
    if dx and dy:valid&=free[x+dx,y]&free[x,y+dy]
    x,y=x[valid],y[valid]
    a=ids[x,y];b=ids[x+dx,y+dy];length=nav.resolution*math.hypot(dx,dy)
    rough0=nav.rough_grid[x,y];rough1=nav.rough_grid[x+dx,y+dy]
    seconds=length/np.where(rough0|rough1,nav.walk_speed,nav.wheel_speed)+(rough0!=rough1)*TRANSFORM_COST_SECONDS
    edges.append((k,a,b,length,seconds))
source=nav.cell(points[0]);goal=nav.cell(points[1])
graph=coo_matrix((np.concatenate([np.full(len(a),length) for _,a,b,length,t in edges]),
                 (np.concatenate([a for _,a,b,l,t in edges]),np.concatenate([b for _,a,b,l,t in edges]))),shape=(n*n,n*n)).tocsr()
reference_distance=float(dijkstra(graph,indices=int(ids[source]))[int(ids[goal])])
nav.plan(points[0],points[1],mode='shortest',yaw=math.pi/2)
assert abs(reference_distance-nav.last_grid_cost)<1e-8
rs=[];rt=[];rw=[]
for k,a,b,length,seconds in edges:
    for incoming in range(8):
        turn=abs((heads[k]-heads[incoming]+math.pi)%(2*math.pi)-math.pi)
        rs.append(a*8+incoming);rt.append(b*8+k);rw.append(seconds+turn)
graph=coo_matrix((np.concatenate(rw),(np.concatenate(rs),np.concatenate(rt))),shape=(n*n*8,n*n*8)).tocsr()
values=dijkstra(graph,indices=int(ids[source])*8+2)
reference_time=float(values[int(ids[goal])*8:int(ids[goal])*8+8].min())
nav.plan(points[0],points[1],mode='fastest',yaw=math.pi/2)
assert abs(reference_time-nav.last_grid_cost)<1e-8
report=dict(ordered_pairs_checked=len(records),modes_per_pair=2,routes=records,
 distance_astar_matches_dijkstra=True,time_astar_matches_dijkstra=True,
 reference_distance_m=reference_distance,reference_grid_time_seconds=reference_time,
 grid_resolution_m=nav.resolution,swept_radius_m=nav.radius,tracking_margin_m=nav.tracking_margin,
 driving_speed=nav.wheel_speed,walking_speed=nav.walk_speed,transform_cost_seconds=TRANSFORM_COST_SECONDS)
(ROOT/'outputs/hybrid_planner_validation.json').write_text(json.dumps(report,indent=2))
print('All 20 ordered pairs passed in both modes; weighted A* matches independent Dijkstra.',flush=True)
