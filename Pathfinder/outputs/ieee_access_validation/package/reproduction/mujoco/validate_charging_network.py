"""Reachability and energy-constrained station choice on the actual expanded scene."""
import json,math
from pathlib import Path
import numpy as np
import mujoco
from scipy.ndimage import label
from safe_navigation import SafeNavigator
from charging_network import select_charger,escape_options
from multi_place_config import MISSION_TARGETS,CHARGING_STATIONS,DEST_BASE
from destination_routing import DestinationMission
from multiobjective_planner import MultiObjectivePlanner
from energy_model import required_energy,CHARGER_RESERVE_PERCENT,objective_score
from terrain_profile import rough_at

root=Path(__file__).parent
m=mujoco.MjModel.from_xml_path(str(root/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);nav=SafeNavigator(m,d)
points=[DEST_BASE]+[t['pos'] for t in MISSION_TARGETS]+[s['pos'] for s in CHARGING_STATIONS]
assert all(nav.clear(p) for p in points)
labels,_=label(~nav.blocked);assert len({labels[nav.nearest_free(p)] for p in points})==1
checks=0
for start in points[:7]:
 for target in [t['pos'] for t in MISSION_TARGETS]:
  if np.linalg.norm(start-target)<.1:continue
  for mode in ('shortest','fastest','energy','balanced'):
   path=MultiObjectivePlanner(nav).path(start,target,math.pi/2,mode=mode)
   assert all(nav.segment_clear(a,b) for a,b in zip(path.points,path.points[1:]));checks+=1
print('All',checks,'destination objective paths clear',flush=True)
choices=[]
for start,expected in [(np.array([-35.,-20.]),'west'),(np.array([35.,22.]),'east'),(DEST_BASE,'central')]:
 nav.current_mode='legs' if rough_at(start) else 'wheels'
 station,route,needed,rows=select_charger(nav,start,math.pi/2,100.,'balanced',np.ones(3)/3)
 assert station['key']==expected,(start,station['key'])
 assert needed<=100 and all(nav.segment_clear(a,b) for a,b in zip(route.points,route.points[1:]))
 # An ample budget chooses by balanced score; insufficient budget cannot choose an unreachable station.
 for budget in (20.,40.):
  options=escape_options(nav,start,math.pi/2)
  if any(required_energy(c.metrics['energy_percent'],CHARGER_RESERVE_PERCENT)<=budget for _,c in options):
   st,c,cost,_=select_charger(nav,start,math.pi/2,budget,'fastest',np.ones(3)/3);assert cost<=budget
  else:
   try:select_charger(nav,start,math.pi/2,budget,'fastest',np.ones(3)/3)
   except RuntimeError:pass
   else:raise AssertionError('Unsafe charging route was accepted')
 choices.append(dict(origin=start.tolist(),selected=station['name'],required=needed,stations=rows))
try:select_charger(nav,DEST_BASE,0.,.1,'balanced',np.ones(3)/3)
except RuntimeError:pass
else:raise AssertionError('Empty battery accepted')
# Charge completion works at all stations and resumes a destination without central-entry teleportation.
for station in CHARGING_STATIONS:
 mission=DestinationMission(nav);mission.pose(station['pos'],0.);mission.divert=mission.charging=True;mission.selected_station=station;mission.battery=100.;mission.green_hold=2.5;mission.resume_target=4
 mission.update(station['pos'],0.,0.,0.,0.)
 assert mission.stage=='stopping' and mission.pending_target==4
 assert mission.depart_station==bool(station['via'])
report=dict(destinations=len(MISSION_TARGETS),charging_stations=len(CHARGING_STATIONS),continuous_route_checks=checks,all_routes_clear=True,station_choices=choices,insufficient_battery_rejected=True,all_station_resume_checks=True)
(root/'outputs/charging_network_validation.json').write_text(json.dumps(report,indent=2));print('PASS charging network',flush=True)
