"""Verify shared terrain grades, metric integration and hard no-go clearance."""
from pathlib import Path
import json,math
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from multiobjective_planner import MultiObjectivePlanner
from terrain_profile import travel_speed,severity_at,split_segment
from terrain_classes import EXTREME_BOUNDS,ROAD_LABELS
from multi_place_config import MISSION_TARGETS,CHARGING_STATIONS,DEST_BASE
from scipy.ndimage import label
root=Path(__file__).parent
m=mujoco.MjModel.from_xml_path(str(root/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);nav=SafeNavigator(m,d)
assert float(travel_speed([0.,-19.],walking=True))==.75
assert float(travel_speed([-10.,-3.],walking=True))==.38
for b in EXTREME_BOUNDS:
 center=np.array([(b[0]+b[1])/2,(b[2]+b[3])/2]);assert severity_at(center)==3 and travel_speed(center)==0
 assert not nav.clear(center)
 for force in (None,'wheels','legs'):
  nav.force_mode=force
  try:nav.plan(DEST_BASE,center)
  except RuntimeError:pass
  else:raise AssertionError('Extreme terrain accepted as a goal')
nav.force_mode=None
points=[DEST_BASE]+[t['pos'] for t in MISSION_TARGETS]+[s['pos'] for s in CHARGING_STATIONS]
assert all(nav.clear(p) for p in points);labels,_=label(~nav.blocked);assert len({labels[nav.nearest_free(p)] for p in points})==1
checks=0
for start in points[:7]:
 for target in [t['pos'] for t in MISSION_TARGETS]:
  if np.linalg.norm(start-target)<.1:continue
  for mode in ('shortest','fastest','energy','balanced'):
   c=MultiObjectivePlanner(nav).path(start,target,math.pi/2,mode=mode)
   assert all(nav.segment_clear(a,b) for a,b in zip(c.points,c.points[1:]));checks+=1
print('All',checks,'route checks avoid extreme terrain',flush=True)
# Same distance on more uneven terrain must take longer and consume more hotel energy.
nav.current_mode='legs'
a=nav.route_metrics([np.array([0.,-19.]),np.array([0.,-18.])],math.pi/2)
b=nav.route_metrics([np.array([-10.,-3.]),np.array([-10.,-2.])],math.pi/2)
assert b['estimated_seconds']>a['estimated_seconds'] and b['energy_percent']>a['energy_percent']
assert {r['name'] for r in ROAD_LABELS}=={'Durian Road','Banana Road','Wan Road','Khem Road','Potato Road','Tomato Road','Fishy Road','Tea Road'}
r=dict(route_checks=checks,all_routes_clear_of_extreme=True,manual_overrides_cannot_enter_extreme=True,all_destinations_and_stations_connected=True,mild_speed=.75,more_uneven_speed=.38,extreme_speed=0.,mild_one_metre=a,more_uneven_one_metre=b,road_names=[r['name'] for r in ROAD_LABELS])
(root/'outputs/terrain_grades_validation.json').write_text(json.dumps(r,indent=2));print('PASS terrain grades',flush=True)
