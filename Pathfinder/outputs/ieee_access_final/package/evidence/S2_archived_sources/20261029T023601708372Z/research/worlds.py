"""Deterministic procedural worlds with matching physical and planner terrain.

Bindings are changed only in the isolated research subprocess, for one scoped
case, and restored even on failure. Production source files are never edited.
"""
from contextlib import contextmanager
import copy,hashlib,importlib,json,math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import mujoco

FAMILIES=('open','clutter','rough','corridor')
def identity(spec):return hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def make_world(seed,family):
    if family not in FAMILIES:raise ValueError('Unknown world family')
    rng=np.random.default_rng(seed)
    stations=[dict(name='West station',key='west',pos=[-19.,-19.],via=[]),dict(name='East station',key='east',pos=[19.,-19.],via=[]),dict(name='North station',key='north',pos=[0.,19.],via=[])]
    obstacles=[]
    if family=='corridor':
        # Two interrupted barriers with independently sampled gaps.
        for x in (-5.,5.):
            gap=float(rng.uniform(-9,9))
            for lo,hi in [(-16.,gap-3.2),(gap+3.2,16.)]:
                if hi-lo>1:obstacles.append(dict(x=x,y=(lo+hi)/2,sx=.45,sy=(hi-lo)/2,height=.75))
    count={'open':5,'clutter':16,'rough':7,'corridor':4}[family]
    for _ in range(count):
        for attempt in range(100):
            x,y=rng.uniform(-14,14,2);sx,sy=rng.uniform(.25,.8,2)
            if any(np.linalg.norm(np.array([x,y])-np.array([b['x'],b['y']]))<3.7 for b in obstacles):continue
            obstacles.append(dict(x=float(x),y=float(y),sx=float(sx),sy=float(sy),height=float(rng.uniform(.35,.8))));break
    patches=[];tiles=[]
    n={'open':1,'clutter':2,'rough':4,'corridor':3}[family]
    for i in range(n):
        cx,cy=rng.uniform(-13,13,2);sx,sy=rng.uniform(2.0,4.0,2);grade=2 if family=='rough' or i%2 else 1
        bound=[float(cx-sx),float(cx+sx),float(cy-sy),float(cy+sy)]
        patches.append(dict(bounds=bound,grade=grade))
        for j in range(12):
            x=rng.uniform(bound[0]+.3,bound[1]-.3);y=rng.uniform(bound[2]+.3,bound[3]-.3)
            tiles.append(dict(x=float(x),y=float(y),sx=float(rng.uniform(.16,.35)),sy=float(rng.uniform(.16,.35)),height=float(rng.uniform(.04,.085) if grade==2 else rng.uniform(.025,.045))))
    spec=dict(version=1,seed=int(seed),family=family,half_extent=24.,friction_scale=float(rng.choice([.8,1.,1.2])),obstacles=obstacles,patches=patches,tiles=tiles,stations=stations)
    return spec

class Terrain:
    def __init__(self,spec):
        self.spec=spec;self.bounds=np.asarray([p['bounds'] for p in spec['patches']],float).reshape(-1,4)
        self.grades=np.asarray([p['grade'] for p in spec['patches']],int)
        self.tiles=np.asarray([[t[k] for k in ('x','y','sx','sy','height')] for t in spec['tiles']],float).reshape(-1,5)
    def covered(self,points,margin=0):
        p=np.asarray(points,float);b=self.bounds
        return (p[...,None,0]>=b[:,0]-margin)&(p[...,None,0]<=b[:,1]+margin)&(p[...,None,1]>=b[:,2]-margin)&(p[...,None,1]<=b[:,3]+margin)
    def severity_at(self,points,margin=0):
        return np.max(np.where(self.covered(points,margin),self.grades,0),axis=-1,initial=0)
    def rough_at(self,points,margin=1.1):return self.severity_at(points,margin)>0
    def ground_height(self,points,radius=0):
        p=np.asarray(points,float);t=self.tiles
        pad=np.where(np.any(self.covered(p,radius),axis=-1),.02,0.)
        covered=(abs(p[...,None,0]-t[:,0])<=t[:,2]+radius)&(abs(p[...,None,1]-t[:,1])<=t[:,3]+radius)
        return np.maximum(pad,np.max(np.where(covered,t[:,4],0.),axis=-1,initial=0.))
    def ground_clearance(self,point,radius=1.9):return float(self.ground_height(point,radius))
    def travel_speed(self,points,walking=False):
        grade=self.severity_at(points,margin=1.1)
        return np.minimum(np.where(grade>=2,.38,np.where(grade==1,.65,1.65)),.75 if walking else 1.65)
    def split_segment(self,start,end):
        a,b=np.asarray(start,float),np.asarray(end,float);delta=b-a;events=[0.,1.]
        bounds=self.bounds+np.array([-1.1,1.1,-1.1,1.1])
        for axis,cols in [(0,(0,1)),(1,(2,3))]:
            if abs(delta[axis])>1e-10:
                for col in cols:events.extend(float(x) for x in (bounds[:,col]-a[axis])/delta[axis] if 0<x<1)
        events=sorted(set(events))
        return [(a+lo*delta,a+hi*delta,bool(self.rough_at(a+(lo+hi)/2*delta))) for lo,hi in zip(events,events[1:])]

@contextmanager
def terrain_context(spec):
    if spec is None:yield;return
    terrain=Terrain(spec);saved=[]
    names=('ground_height','ground_clearance','severity_at','rough_at','travel_speed','split_segment')
    try:
        for modname in ['road_demo','terrain_profile','safe_navigation','tripod_gait','hybrid_locomotion','research.planning','research.execution']:
            mod=importlib.import_module(modname)
            for name in names:
                if hasattr(mod,name):saved.append((mod,name,getattr(mod,name)));setattr(mod,name,getattr(terrain,name))
        nav=importlib.import_module('safe_navigation');saved.extend([(nav,'EXTREME_BOUNDS',nav.EXTREME_BOUNDS),(nav,'MAP_HALF_EXTENT',nav.MAP_HALF_EXTENT)])
        nav.EXTREME_BOUNDS=np.empty((0,4));nav.MAP_HALF_EXTENT=spec['half_extent']
        yield terrain
    finally:
        for mod,name,value in reversed(saved):setattr(mod,name,value)

def world_model(spec,xml_output=None):
    rootdir=Path(__file__).resolve().parents[1]
    root=ET.parse(rootdir/'hybrid_hexapod_multi_place.xml').getroot();world=root.find('worldbody')
    robot=world.find("body[@name='robot']")
    if robot is None:raise RuntimeError('Robot body is missing')
    used={g.get('mesh') for g in robot.iter('geom') if g.get('mesh')}
    for child in list(world):
        if child is not robot and child.tag not in ('light','camera'):world.remove(child)
    for asset in list(root.find('asset')):
        if asset.tag=='mesh' and asset.get('name') not in used:root.find('asset').remove(asset)
    for item in root.iter():
        if item.get('file'):item.set('file',str((rootdir/item.get('file')).resolve()))
    def geom(name,pos,size,**kwargs):
        return ET.SubElement(world,'geom',name=name,type=kwargs.pop('type','box'),pos=' '.join(map(str,pos)),size=' '.join(map(str,size)),contype='1',conaffinity='7',friction=f"{1.3*spec.get('friction_scale',1.)} .02 .002",**kwargs)
    geom('research_ground',[0,0,0],[spec['half_extent'],spec['half_extent'],.1],type='plane',rgba='.62 .65 .59 1')
    for i,b in enumerate(spec['obstacles']):geom(f'research_obstacle_{i}',[b['x'],b['y'],b['height']/2],[b['sx'],b['sy'],b['height']/2],rgba='.42 .36 .3 1')
    for i,p in enumerate(spec['patches']):
        x0,x1,y0,y1=p['bounds'];geom(f'research_pad_{i}',[(x0+x1)/2,(y0+y1)/2,.01],[(x1-x0)/2,(y1-y0)/2,.01],rgba='.38 .31 .2 1')
    for i,t in enumerate(spec['tiles']):geom(f'research_tile_{i}',[t['x'],t['y'],t['height']/2],[t['sx'],t['sy'],t['height']/2],rgba='.4 .37 .3 1')
    xml=ET.tostring(root,encoding='unicode');model=mujoco.MjModel.from_xml_string(xml)
    if xml_output:
        path=Path(xml_output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(xml)
    return model


def sample_cases(count,seed_base,split='exploratory'):
    cases=[]
    for i in range(count):
        seed=int(seed_base)+i;spec=make_world(seed,FAMILIES[i%4]);rng=np.random.default_rng(seed+12345)
        model=world_model(spec);data=mujoco.MjData(model);mujoco.mj_forward(model,data)
        from safe_navigation import SafeNavigator
        with terrain_context(spec):
            nav=SafeNavigator(model,data,resolution=.25)
            for attempt in range(200):
                a,b=rng.uniform(-17,17,(2,2))
                if not 12<=np.linalg.norm(b-a)<=26:continue
                try:
                    start=nav.point(nav.nearest_free(a)).tolist();goal=nav.point(nav.nearest_free(b)).tolist()
                    if np.linalg.norm(np.array(goal)-start)<10:continue
                    break
                except ValueError:continue
            else:raise RuntimeError('Cannot sample safe task endpoints')
        cases.append(dict(id=f'{split}_{i+1:02d}',split=split,layout_id=f'{split}_world_{seed}',seed=seed,
          world=spec,world_sha256=identity(spec),variant=0,start=start,goal=goal,
          deadline_s=float(rng.choice([45,70,110,160])),battery_percent=float(rng.choice([45,65,85,100])),
          risk_budget=float(rng.choice([10,20,40])),energy_multiplier=float(rng.choice([.85,1.,1.2]))))
        print(f'Manifest {split} {i+1}/{count} · {spec["family"]}',flush=True)
    return cases
