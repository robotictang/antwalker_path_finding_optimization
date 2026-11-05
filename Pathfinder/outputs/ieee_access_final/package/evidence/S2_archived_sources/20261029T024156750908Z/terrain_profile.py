"""Terrain policy shared by hybrid routing, visualization, and transformation control."""
import numpy as np
from multi_place_config import ZONE_BBOX_FOREST,ZONE_BBOX_ROCKY,ZONE_BBOX_MUD,ZONE_BBOX_SAND

WHEEL_SPEED=1.65
WALK_SPEED=.75
TRANSFORM_SECONDS=3.6
TRANSFORM_COST_SECONDS=4.8  # includes a small brake/restart allowance
from road_demo import ROAD_PATCHES
from terrain_classes import HIGH_PATCH_INDICES,EXTREME_BOUNDS,MILD_SPEED,HIGH_SPEED,CAUTION_SPEED,inside
BOUNDS=np.vstack([np.asarray([ZONE_BBOX_FOREST,ZONE_BBOX_ROCKY,ZONE_BBOX_MUD,ZONE_BBOX_SAND],dtype=float),ROAD_PATCHES])

HIGH_BOUNDS=ROAD_PATCHES[list(HIGH_PATCH_INDICES)]

def severity_at(points,margin=0.):
    mild=inside(points,BOUNDS,margin)
    high=inside(points,HIGH_BOUNDS,margin)
    extreme=inside(points,EXTREME_BOUNDS,margin)
    return np.where(extreme,3,np.where(high,2,np.where(mild,1,0)))

def travel_speed(points,walking=False):
    severity=severity_at(points,margin=1.1)
    speed=np.where(severity>=2,HIGH_SPEED,np.where(severity==1,MILD_SPEED,WHEEL_SPEED))
    speed=np.minimum(speed,WALK_SPEED if walking else WHEEL_SPEED)
    # Slow near an extreme patch, but never enter its excluded footprint.
    speed=np.where(inside(points,EXTREME_BOUNDS,3.0),np.minimum(speed,CAUTION_SPEED),speed)
    return np.where(inside(points,EXTREME_BOUNDS),0.,speed)

def rough_at(points,margin=1.1):
    p=np.asarray(points,dtype=float)
    return np.any((p[...,None,0]>=BOUNDS[:,0]-margin)&(p[...,None,0]<=BOUNDS[:,1]+margin)&
                  (p[...,None,1]>=BOUNDS[:,2]-margin)&(p[...,None,1]<=BOUNDS[:,3]+margin),axis=-1)


def split_segment(start,end):
    start,end=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
    delta=end-start;events=[0.,1.]
    split_bounds=np.vstack([BOUNDS+np.array([-1.1,1.1,-1.1,1.1]),EXTREME_BOUNDS+np.array([-3.,3.,-3.,3.])])
    for axis,columns in [(0,(0,1)),(1,(2,3))]:
        if abs(delta[axis])<1e-10:continue
        for column in columns:
            offsets=split_bounds[:,column]
            events.extend(t for t in (offsets-start[axis])/delta[axis] if 0<t<1)
    events=sorted(set(events));pieces=[]
    for lo,hi in zip(events,events[1:]):
        walking=bool(rough_at(start+(lo+hi)/2*delta))
        a,b=start+lo*delta,start+hi*delta
        # Preserve severity boundaries for speed and energy integration.
        pieces.append((a,b,walking))
    return pieces
