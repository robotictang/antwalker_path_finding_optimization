"""Expanded-map route access, frozen comparison, and durable history integration."""
import json,math,tempfile,csv,io
from pathlib import Path
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from planning_lab import PlanningLab
from multiobjective_planner import MODES
from mission_history import HistoryStore,HistoryRecorder
from destination_routing import DestinationMission
from multi_place_config import DEST_BASE,MISSION_TARGETS
from energy_model import objective_score
from expanded_world import NEW_ROADS
ROOT=Path(__file__).resolve().parent
m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);nav=SafeNavigator(m,d)
assert nav.upper-nav.lower==96.
assert len(NEW_ROADS)==12
hazards=[i for i in range(m.ngeom) if m.geom(i).name.startswith(('wide_road_boulder_','wide_road_cone_')) and m.geom_contype[i]]
assert len(hazards)==40
points=[DEST_BASE]+[t['pos'] for t in MISSION_TARGETS];checks=[]
for i,start in enumerate(points):
 for j,goal in enumerate(points):
  if i==j:continue
  for mode in MODES:
   path=nav.plan(start,goal,mode=mode,yaw=math.pi/2)
   assert np.linalg.norm(path[-1]-goal)<1e-8
   assert all(nav.segment_clear(a,b) for a,b in zip([start]+path,path))
   checks.append(dict(origin=i,destination=j,mode=mode,**nav.route_metrics([start]+path,math.pi/2)))
with tempfile.TemporaryDirectory() as folder:
 path=Path(folder)/'history.sqlite3';store=HistoryStore(path);recorder=HistoryRecorder(store);lab=PlanningLab(store)
 pose=d.qpos.copy();mode=nav.current_mode
 result=lab.compare(nav,'origin',1)
 assert np.array_equal(d.qpos,pose) and nav.current_mode==mode
 eligible=[r for r in result['rows'] if r['feasible']]
 shorter=min(eligible,key=lambda r:objective_score(r,'balanced',[90,5,5]))
 faster=min(eligible,key=lambda r:objective_score(r,'balanced',[5,90,5]))
 assert shorter['id']!=faster['id'] and shorter['distance_m']<faster['distance_m'] and faster['estimated_seconds']<shorter['estimated_seconds']
 lab.record_choice(result['id'],[90,5,5]);lab.record_choice(result['id'],[5,90,5])
 mission=DestinationMission(nav);mission.pose(DEST_BASE,0.);mission.dispatch(0);recorder.observe(mission)
 # A reset creates a new controller, and must preserve previous rows.
 before=store.page()['total'];mission=DestinationMission(nav);mission.pose(points[1],0.);mission.dispatch(2);recorder.observe(mission)
 store=HistoryStore(path);assert store.page()['total']>before
 seen=[];after=0
 while True:
  page=store.page(after=after,limit=2);seen.extend(r['id'] for r in page['records'])
  if not page['has_more']:break
  after=page['next_after']
 assert len(seen)==len(set(seen))==store.page()['total']
 rows=list(csv.DictReader(io.StringIO(store.csv().decode())))
 assert any(r['From']=='Origin depot' and r['To']=='Forest' for r in rows)
 assert any(r['From']=='Forest' and r['To']=='Marsh' for r in rows)
 with store.connect() as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
output=dict(world_size_m=[96,96],new_road_links=len(NEW_ROADS),additional_physical_road_obstacles=len(hazards),ordered_location_pairs=20,objective_route_checks=len(checks),all_routes_continuously_clear=True,comparison_does_not_move_robot=True,priority_switch_changes_route=True,shorter_example=shorter,faster_example=faster,history_reset_restart_and_incremental_paging=True,csv_origin_destination_labels=True,sqlite_integrity=True,routes=checks)
(ROOT/'outputs/explorer_validation.json').write_text(json.dumps(output,indent=2))
print('PASS: 80 routes across 20 ordered pairs; weights change the fixed-start winner; history survives controller reset and DB reopen with From/To CSV labels.')
