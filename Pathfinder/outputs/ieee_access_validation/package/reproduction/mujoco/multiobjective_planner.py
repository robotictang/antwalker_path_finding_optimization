"""Supported Pareto route search with normalized distance/time/energy scalarizations.

Weighted heading-state A* runs on the conservative collision grid. Multiple
scalarizations produce candidate routes; dominated solutions are removed before
energy feasibility and the user's preference select a route. This is a sampled
supported Pareto set, not exhaustive enumeration of every continuous path.
"""
from dataclasses import dataclass
import math
import numpy as np
from energy_model import objective_score,objective_weights,normalize_weights,DEFAULT_WEIGHTS

MODES=('balanced','shortest','fastest','energy')


@dataclass
class RouteCandidate:
    points:list
    metrics:dict
    search_weights:list

    def record(self,with_points=True):
        result=dict(self.metrics,search_weights=self.search_weights)
        if with_points:result['points']=[p.tolist() for p in self.points]
        return result


def pareto_front(candidates):
    def vector(c):return np.array([c.metrics[k] for k in ('distance_m','estimated_seconds','energy_percent')])
    unique=[]
    for candidate in candidates:
        if not any(np.allclose(vector(candidate),vector(other),rtol=0,atol=1e-7) for other in unique):unique.append(candidate)
    return [c for c in unique if not any(np.all(vector(o)<=vector(c)+1e-8) and np.any(vector(o)<vector(c)-1e-8) for o in unique if o is not c)]


class MultiObjectivePlanner:
    def __init__(self,navigator):self.nav=navigator

    def path(self,start,goal,yaw,mode='balanced',weights=None,via=()):
        start=np.asarray(start,dtype=float);points=[start.copy()];heading=yaw
        for endpoint in [*via,np.asarray(goal,dtype=float)]:
            endpoint=np.asarray(endpoint,dtype=float)
            if np.linalg.norm(endpoint-points[-1])<1e-7:continue
            segment=self.nav.plan(points[-1],endpoint,mode=mode,yaw=heading,weights=weights)
            points.extend(np.asarray(p).copy() for p in segment)
            if len(points)>1:
                delta=points[-1]-points[-2];heading=math.atan2(delta[1],delta[0])
        if len(points)==1:points.append(points[0].copy())
        return RouteCandidate(points,self.nav.route_metrics(points,yaw),list(objective_weights(mode,weights)))

    def alternatives(self,start,goal,yaw,weights=DEFAULT_WEIGHTS,via=()):
        weights=normalize_weights(weights)
        samples=[(1.,0.,0.),(0.,1.,0.),(0.,0.,1.),tuple(weights),(.60,.20,.20),(.20,.60,.20),(.20,.20,.60)]
        candidates=[];seen=set()
        for w in samples:
            w=tuple(normalize_weights(w))
            if w in seen:continue
            seen.add(w)
            mode=('shortest','fastest','energy')[w.index(1.)] if 1. in w else 'balanced'
            candidates.append(self.path(start,goal,yaw,mode=mode,weights=w,via=via))
        frontier=pareto_front(candidates)
        representatives={mode:min(frontier,key=lambda c:objective_score(c.metrics,mode,weights)) for mode in MODES}
        return frontier,representatives
