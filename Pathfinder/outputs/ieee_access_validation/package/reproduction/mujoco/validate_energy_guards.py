"""Capacity refusal and idle recharge guard checks on the actual obstacle map."""
import json,math
from pathlib import Path
import mujoco,numpy as np
from destination_routing import DestinationMission,PLACES
from safe_navigation import SafeNavigator
from multi_place_config import DEST_KIOSK_PAD
ROOT=Path(__file__).resolve().parent
m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);nav=SafeNavigator(m,d)
capacity=DestinationMission(nav);capacity.pose(DEST_KIOSK_PAD,0.);capacity.depart_station=True;capacity.target=capacity.pending_target=1;capacity.stage='stopping'
capacity._return_cost=lambda target:101. # A return that cannot fit even a full pack.
capacity.update(DEST_KIOSK_PAD,0.,0.,0.,0.)
assert capacity.stage=='blocked' and not capacity.divert and not capacity.charging
assert 'full battery capacity' in capacity.error
idle=DestinationMission(nav);nav.current_mode='legs';idle.pose(PLACES[1],0.);idle.stage='arrived';idle.target=1
idle.update(PLACES[1],0.,0.,0.,0.,locomotion_mode='legs')
assert idle.idle_escape_cache
need=next(iter(idle.idle_escape_cache.values()));idle.battery=need+.5;idle.next_energy_check=0.
idle.update(PLACES[1],0.,0.,0.,0.,locomotion_mode='legs')
assert idle.divert and idle.stage=='preview' and not idle.charging
assert idle.battery>20. and idle.energy_status['required_percent']<=idle.battery
result=dict(full_capacity_infeasible_task_stops_without_charging_loop=True,idle_returns_before_losing_charger_reserve=True,idle_departure_battery=idle.battery,idle_charger_requirement=idle.energy_status['required_percent'])
(ROOT/'outputs/multiobjective_energy_guards.json').write_text(json.dumps(result,indent=2))
print('PASS:',result)
