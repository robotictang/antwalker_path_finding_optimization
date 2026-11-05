"""Terrain limits for this assisted demonstration (not measured robot capability)."""
import numpy as np
# More uneven but traversable: cobbles up to 10.5 cm, slow leg gait.
HIGH_PATCH_INDICES=(1,2,4,6,8,10)
# No-go washed-out road sections; clearance includes the entire leg sweep.
EXTREME_BOUNDS=np.array([[14.,20.,-32.,-28.],[-8.,-2.,26.,30.],[22.,25.,.5,3.5]])
MILD_SPEED=.75
HIGH_SPEED=.38
CAUTION_SPEED=.50

ROAD_LABELS=[
 dict(name='Durian Road',points=[[-35.,-30.],[35.,-30.]],label=[-17.,-30.],angle=0),
 dict(name='Banana Road',points=[[35.,-30.],[35.,28.]],label=[35.,-2.],angle=-90),
 dict(name='Wan Road',points=[[-35.,28.],[35.,28.]],label=[8.,28.],angle=0),
 dict(name='Khem Road',points=[[-35.,-30.],[-35.,28.]],label=[-35.,-1.],angle=-90),
 dict(name='Potato Road',points=[[0.,-20.],[0.,-30.]],label=[0.,-26.],angle=-90),
 dict(name='Tomato Road',points=[[-35.,2.],[-10.,2.]],label=[-24.,2.],angle=0),
 dict(name='Fishy Road',points=[[35.,2.],[10.,2.]],label=[29.,2.],angle=0),
 dict(name='Tea Road',points=[[-18.,16.],[-18.,28.]],label=[-18.,23.],angle=-90),
]


def inside(points,bounds,margin=0.):
    p=np.asarray(points,dtype=float);b=np.asarray(bounds)
    return np.any((p[...,None,0]>=b[:,0]-margin)&(p[...,None,0]<=b[:,1]+margin)&
                  (p[...,None,1]>=b[:,2]-margin)&(p[...,None,1]<=b[:,3]+margin),axis=-1)
