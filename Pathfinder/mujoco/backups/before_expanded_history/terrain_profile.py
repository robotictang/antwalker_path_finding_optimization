"""Terrain policy shared by hybrid routing, visualization, and transformation control."""
import numpy as np
from multi_place_config import ZONE_BBOX_FOREST,ZONE_BBOX_ROCKY,ZONE_BBOX_MUD,ZONE_BBOX_SAND

WHEEL_SPEED=1.65
WALK_SPEED=.75
TRANSFORM_SECONDS=3.6
TRANSFORM_COST_SECONDS=4.8  # includes a small brake/restart allowance
from road_demo import ROAD_PATCHES
BOUNDS=np.vstack([np.asarray([ZONE_BBOX_FOREST,ZONE_BBOX_ROCKY,ZONE_BBOX_MUD,ZONE_BBOX_SAND],dtype=float),ROAD_PATCHES])


def rough_at(points,margin=1.1):
    p=np.asarray(points,dtype=float)
    return np.any((p[...,None,0]>=BOUNDS[:,0]-margin)&(p[...,None,0]<=BOUNDS[:,1]+margin)&
                  (p[...,None,1]>=BOUNDS[:,2]-margin)&(p[...,None,1]<=BOUNDS[:,3]+margin),axis=-1)


def split_segment(start,end):
    start,end=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
    delta=end-start;events=[0.,1.]
    for axis,columns in [(0,(0,1)),(1,(2,3))]:
        if abs(delta[axis])<1e-10:continue
        for column in columns:
            offsets=BOUNDS[:,column]+(-1.1 if column in (0,2) else 1.1)
            events.extend(t for t in (offsets-start[axis])/delta[axis] if 0<t<1)
    events=sorted(set(events));pieces=[]
    for lo,hi in zip(events,events[1:]):
        walking=bool(rough_at(start+(lo+hi)/2*delta))
        a,b=start+lo*delta,start+hi*delta
        if pieces and pieces[-1][2]==walking:
            pieces[-1]=(pieces[-1][0],b,walking)
        else:pieces.append((a,b,walking))
    return pieces
