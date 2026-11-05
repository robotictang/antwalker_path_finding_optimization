"""Exact enumeration reference for small synthetic forward-visibility graphs.

These are software-validation fixtures, never empirical robot experiments.
"""
import argparse,itertools,json,math,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import energy_model as em
from research.planning import Limits,feasible
from research.swarm import Corridor,resource_label_search,rank

class ReferenceGraph:
    walking_only=True
    def __init__(self):self.nav=SimpleNamespace(walk_speed=.75,tracking_margin=0.,segment_clear=self.clear)
    @staticmethod
    def clear(a,b,margin=0.):
        a,b=np.asarray(a,float),np.asarray(b,float);delta=b-a
        t=np.clip(np.dot(np.array([4.,0.])-a,delta)/max(1e-12,delta@delta),0,1)
        return float(np.linalg.norm(a+t*delta-np.array([4.,0.])))>.6
    def metrics(self,points,yaw=0.):
        points=np.asarray(points,float);delta=np.diff(points,axis=0);lengths=np.linalg.norm(delta,axis=1)
        headings=np.arctan2(delta[:,1],delta[:,0]);turn=float(abs((np.diff(np.r_[yaw,headings])+math.pi)%(2*math.pi)-math.pi).sum())
        length=float(lengths.sum());seconds=length/.75+turn+.6
        exposure=float(sum(l*(.1+.03*(a[1]**2+a[1]*b[1]+b[1]**2)/3) for a,b,l in zip(points,points[1:],lengths)))
        return dict(distance_m=length,estimated_seconds=seconds,energy_percent=em.energy_cost(0.,length,seconds,turn,0),terrain_exposure=exposure)

def exhaustive(graph,points,limits,return_energy=3.):
    if len(points)>16:raise ValueError('Exact enumeration is restricted to at most 16 corridor nodes')
    best=None;checked=0
    for mask in range(1<<(len(points)-2)):
        indices=[0]+[j+1 for j in range(len(points)-2) if mask&(1<<j)]+[len(points)-1]
        route=[points[j] for j in indices]
        if not all(graph.nav.segment_clear(a,b) for a,b in zip(route,route[1:])):continue
        metrics=graph.metrics(route,0.);value=rank(metrics,limits,return_energy);checked+=1
        if best is None or value<best[0]:best=(value,route,metrics)
    return best,checked

def validate(count=24):
    records=[]
    for seed in range(65000,65000+count):
        rng=np.random.default_rng(seed);g=ReferenceGraph()
        points=[np.array([0.,0.])]+[np.array([float(i),float(rng.uniform(1.1,2.6))]) for i in range(1,8)]+[np.array([8.,0.])]
        assert all(g.clear(a,b) for a,b in zip(points,points[1:]))
        limits=Limits(float(rng.choice([14.,18.,24.])),float(rng.choice([15.,20.,30.])),float(rng.choice([1.5,3.,6.])),1.)
        exact,checked=exhaustive(g,points,limits)
        begin=time.perf_counter();c=Corridor(g,points,0.,limits,3.,begin+1.,begin);c.initialize();resource_label_search(c)
        exact_admitted=exact is not None and exact[0][0]==0;label_admitted=c.best is not None and c.best[0][0]==0
        gap=c.best[0][2]-exact[0][2] if exact_admitted and label_admitted else None
        records.append(dict(seed=seed,exact_candidates=checked,exact_admitted=exact_admitted,label_admitted=label_admitted,score_gap=gap))
    mismatches=[r for r in records if r['exact_admitted']!=r['label_admitted'] or (r['score_gap'] is not None and abs(r['score_gap'])>1e-8)]
    return dict(kind='synthetic_reference_validation',cases=count,records=records,mismatches=mismatches,state='passed' if not mismatches else 'failed',
      scope='Exhaustive subset enumeration on small additive synthetic graphs only. No optimality certificate for full MuJoCo worlds or bounded large searches.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=validate();a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2));print(r['state'],r['cases'],'synthetic cases;',len(r['mismatches']),'mismatches')
