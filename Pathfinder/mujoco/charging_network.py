"""Energy-constrained selection across all stations behind one Charge command."""
import numpy as np
from multi_place_config import CHARGING_STATIONS
from multiobjective_planner import MultiObjectivePlanner
from energy_model import required_energy,CHARGER_RESERVE_PERCENT,objective_score


def station_at(point,tolerance=.30):
    return next((s for s in CHARGING_STATIONS if np.linalg.norm(np.asarray(point)-s['pos'])<tolerance),None)


def escape_options(nav,start,yaw=0.,departure=()):
    """Minimum predicted energy to every reachable station, with actual approach lanes."""
    result=[];planner=MultiObjectivePlanner(nav)
    for station in CHARGING_STATIONS:
        try:
            candidate=planner.path(start,station['pos'],yaw,mode='energy',via=[*departure,*station['via']])
            result.append((station,candidate))
        except RuntimeError:continue
    return result


def select_charger(nav,start,yaw,battery,mode='balanced',weights=None,departure=()):
    rows=[];candidates=[];planner=MultiObjectivePlanner(nav)
    for station in CHARGING_STATIONS:
        try:
            front,_=planner.alternatives(start,station['pos'],yaw,weights=weights,via=[*departure,*station['via']])
            for c in front:
                needed=required_energy(c.metrics['energy_percent'],CHARGER_RESERVE_PERCENT)
                candidates.append((station,c,needed))
            minimum=min(front,key=lambda c:c.metrics['energy_percent'])
            rows.append(dict(name=station['name'],key=station['key'],reachable=True,required_percent=required_energy(minimum.metrics['energy_percent'],CHARGER_RESERVE_PERCENT),**minimum.metrics))
        except RuntimeError:rows.append(dict(name=station['name'],key=station['key'],reachable=False))
    feasible=[x for x in candidates if x[2]<=battery+1e-8]
    if not feasible:raise RuntimeError('No charging station can be reached with the available battery and safety reserve. Stop for assistance.')
    selected=min(feasible,key=lambda x:(objective_score(x[1].metrics,mode,weights),x[2]))
    return (*selected,rows)
