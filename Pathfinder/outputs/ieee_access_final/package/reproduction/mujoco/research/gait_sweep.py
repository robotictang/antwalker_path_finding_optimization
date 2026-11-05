"""Matched physics gait trials, separate from path-planner comparisons."""
import argparse
from datetime import datetime,timezone
from itertools import product
import json
import math
from pathlib import Path
import time
import numpy as np
import mujoco
from safe_navigation import SafeNavigator
from terrain_profile import severity_at
from research.execution import execute
from research.run import OUT,atomic_json,model_for_case,experiment_lock

def find_tracks(model,length=3.):
    d=mujoco.MjData(model);mujoco.mj_forward(model,d);nav=SafeNavigator(model,d,resolution=.25)
    rng=np.random.default_rng(4104)
    xy=nav.lower+np.indices((nav.n,nav.n)).transpose(1,2,0)*nav.resolution
    grade=severity_at(xy,margin=1.1);tracks=[]
    for level in (0,1,2):
        candidates=np.argwhere((~nav.blocked)&(grade==level));rng.shuffle(candidates)
        for cell in candidates[:2500]:
            a=nav.point(cell)
            for direction in ([1.,0.],[0.,1.],[-1.,0.],[0.,-1.]):
                b=a+length*np.asarray(direction)
                samples=np.linspace(a,b,12)
                if np.all(severity_at(samples,margin=1.1)==level) and nav.segment_clear(a,b,margin=.12):
                    tracks.append(dict(grade=level,route=[a.tolist(),b.tolist()],speed=.30 if level==2 else .50))
                    break
            if tracks and tracks[-1]['grade']==level:break
    return tracks

def _run_sweep(quick=False,progress=None):
    model=model_for_case();tracks=find_tracks(model)
    settings=[dict(period=1/1.45,duty=.6,lift=.13,swing_profile='quintic')]
    settings.extend(dict(period=t,duty=d,lift=.13,swing_profile='quintic') for t,d in product([.6,.8,1.],[.55,.65,.75]))
    if quick:settings=[settings[i] for i in (0,2,5)]
    run_id='gait_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    result=dict(schema_version=1,run_id=run_id,state='running',created_at=datetime.now(timezone.utc).isoformat(),
      kind='gait_sweep',settings=settings,tracks=tracks,records=[],
      caveats=['Fixed-speed straight-track assisted-physics trials, not Smart Gait reproduction.',
       'Selection is calibration only; validation on unseen tracks is required.',
       'Positive actuator work is mechanical work, not measured electrical battery energy.',
       'Assisted posture and gravity compensation can hide balance failures.'])
    path=OUT/f'{run_id}.json';OUT.mkdir(exist_ok=True,parents=True)
    def save():atomic_json(path,result);atomic_json(OUT/'latest_gait.json',result)
    save()
    try:
        for track in tracks:
            for index,setting in enumerate(settings):
                ex=execute(model,track['route'],walking_only=True,gait=setting,speed_cap=track['speed'],max_seconds=35.,record_every=10)
                work_per_m=ex['positive_leg_work_j']/ex['distance_m'] if ex['distance_m']>0 else None
                eligible=bool(ex['success'] and ex['max_tilt_deg']<15. and not ex['penetration_substeps'] and not ex['solver_warnings'])
                result['records'].append(dict(grade=track['grade'],setting=index,is_default=index==0,gait=setting,eligible=eligible,leg_work_per_m_j=work_per_m,execution=ex))
                save();message=f"Gait grade {track['grade']} setting {index}: {ex['outcome']}"
                print(message,flush=True)
                if progress:progress(len(result['records']),len(tracks)*len(settings),message)
        result['selected_by_grade']={}
        for track in tracks:
            valid=[r for r in result['records'] if r['grade']==track['grade'] and r['eligible'] and r['leg_work_per_m_j'] is not None]
            if valid:
                chosen=min(valid,key=lambda r:r['leg_work_per_m_j'])
                result['selected_by_grade'][str(track['grade'])]=dict(gait=chosen['gait'],leg_work_per_m_j=chosen['leg_work_per_m_j'],calibration_only=True)
        result['state']='complete';save()
    except BaseException:result['state']='interrupted';save();raise
    return result

def run_sweep(*args,**kwargs):
    with experiment_lock():return _run_sweep(*args,**kwargs)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--quick',action='store_true');a=p.parse_args()
    print(json.dumps(run_sweep(a.quick).get('selected_by_grade',{}),indent=2))
