"""96 m navigation area, wide bypasses, site connectors and blocking road debris."""
import math
import xml.etree.ElementTree as ET
import numpy as np

MAP_HALF_EXTENT=48.
NEW_ROADS=[
 np.array([[-35.,-30.],[35.,-30.],[35.,28.],[-35.,28.],[-35.,-30.]]),
 np.array([[0.,-20.],[0.,-30.]]),
 np.array([[-18.,16.],[-18.,28.]]),np.array([[18.,16.],[18.,28.]]),
 np.array([[-18.,-10.],[-35.,-10.]]),np.array([[18.,-10.],[35.,-10.]]),
 np.array([[-35.,16.],[-26.,16.],[-18.,16.]]),
 np.array([[35.,16.],[26.,16.],[18.,16.]]),
 np.array([[-18.,-10.],[-24.,-20.],[-24.,-30.]]),
 np.array([[18.,-10.],[24.,-20.],[24.,-30.]]),
 np.array([[-35.,2.],[-28.,2.],[-10.,2.]]),
 np.array([[35.,2.],[28.,2.],[10.,2.]])]


def extend_world(root):
    world=root.find('worldbody')
    ground=world.find("geom[@name='ground']");ground.set('size','50 50 .1')
    for element in list(world):
        name=element.get('name','')
        if name.startswith(('mount_','tower_nw','tower_ne','tower_sw','tower_se')):
            p=np.fromstring(element.get('pos','0 0 0'),sep=' ');p[:2]*=1.45;element.set('pos',' '.join(map(str,p)))
        elif name.startswith(('landscape_bed_','landscape_shrub_')):
            p=np.fromstring(element.get('pos','0 0 0'),sep=' ');p[0]=math.copysign(44.,p[0]);element.set('pos',' '.join(map(str,p)))
    def geom(name,kind,pos,size,color,physical=False):
        return ET.SubElement(world,'geom',name=name,type=kind,pos=' '.join(map(str,pos)),size=' '.join(map(str,size)),rgba=' '.join(map(str,color)),contype='1' if physical else '0',conaffinity='7' if physical else '0',friction='1.3 .02 .002')
    for r,road in enumerate(NEW_ROADS):
        for j,(a,b) in enumerate(zip(road,road[1:])):
            delta=b-a;length=float(np.linalg.norm(delta));direction=delta/length;yaw=math.atan2(*delta[::-1])
            g=geom(f'wide_road_{r}_{j}','box',[*(a+b)/2,.007],[length/2,4.2,.003],[.115,.13,.145,1]);g.set('euler',f'0 0 {yaw}')
            normal=np.array([-direction[1],direction[0]])
            for k,t in enumerate(np.arange(.5,length,2.)):
                g=geom(f'wide_dash_{r}_{j}_{k}','box',[*(a+t*direction),.012],[.45,.04,.002],[.98,.84,.31,1]);g.set('euler',f'0 0 {yaw}')
            for side in [-1,1]:
                g=geom(f'wide_edge_{r}_{j}_{side}','box',[*((a+b)/2+normal*side*3.95),.012],[length/2,.045,.002],[.8,.86,.88,1]);g.set('euler',f'0 0 {yaw}')
    from multi_place_config import CHARGING_STATIONS,MISSION_TARGETS,DEST_BASE
    # Service bays share one UI command; each has a usable pad and a cabinet off its approach.
    for station in CHARGING_STATIONS[1:]:
        x,y=station['pos'];side=-1 if x<0 else 1;key=station['key']
        geom(f'{key}_charging_apron','box',[x,y,.011],[3.6,3.,.006],[.18,.28,.28,1])
        geom(f'{key}_charging_pad','cylinder',[x,y,.021],[1.15,.005],[.14,.67,.48,1])
        geom(f'{key}_charger_cabinet','box',[x+side*4.,y,.9],[.65,.65,.9],[.84,.9,.88,1],True)
        geom(f'{key}_charger_screen','box',[x+side*3.34,y,1.15],[.012,.37,.23],[.08,.75,.62,1])
        geom(f'{key}_charger_canopy','box',[x+side*3.,y,2.65],[1.7,1.3,.10],[.14,.24,.30,1])
        geom(f'{key}_charger_post','cylinder',[x+side*4.6,y,1.3],[.08,1.3],[.6,.65,.68,1],True)
        geom(f'{key}_charging_symbol','box',[x,y,.03],[.65,.10,.002],[.75,1.,.22,1])
    for i,t in enumerate(MISSION_TARGETS[4:],5):
        x,y=t['pos'];side=-1 if x<0 else 1
        geom(f'site_{i}_apron','box',[x,y,.008],[3.9,3.7,.004],[.26,.29,.22,1])
        geom(f'site_{i}_cabin','box',[x+side*6.6,y,1.0],[1.1,1.6,1.0],[.31,.41,.37,1],True)
        geom(f'site_{i}_roof','box',[x+side*6.6,y,2.1],[1.35,1.8,.12],[.18,.24,.28,1])
        geom(f'site_{i}_door','box',[x+side*5.48,y,.7],[.02,.38,.7],[.13,.20,.23,1])
        geom(f'site_{i}_marker','cylinder',[x,y,.04],[.9,.012],[.91,.65,.22,1])
    # Seeded irregular scatter: no mirrored rows, equal intervals or paired cones.
    # Every proposed blocking object must keep ALL destinations and chargers connected.
    import mujoco
    from safe_navigation import SafeNavigator
    from scipy.ndimage import label
    rng=np.random.default_rng(20261023)
    targets=[np.asarray(DEST_BASE)]+[np.asarray(t['pos']) for t in MISSION_TARGETS]+[np.asarray(t['pos']) for t in CHARGING_STATIONS]
    accepted=[];segments=[(a,b) for road in NEW_ROADS for a,b in zip(road,road[1:])]
    model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
    data=mujoco.MjData(model);mujoco.mj_forward(model,data);nav=SafeNavigator(model,data)
    xy=nav.lower+np.indices((nav.n,nav.n)).transpose(1,2,0)*nav.resolution
    occupied=nav.blocked.copy();cells=[nav.nearest_free(p) for p in targets]
    if not all(nav.clear(p) for p in targets):raise RuntimeError('New site or charging pad is obstructed')
    for attempt in range(4000):
        if len(accepted)>=72:break
        a,b=segments[int(rng.integers(len(segments)))];d=b-a;length=np.linalg.norm(d);normal=np.array([-d[1],d[0]])/length
        point=a+rng.uniform(.05,.95)*d+normal*rng.uniform(-2.9,2.9)
        if min(np.linalg.norm(point-q) for q in targets)<5.0:continue
        if accepted and min(np.linalg.norm(point-q) for q in accepted)<rng.uniform(3.0,4.0):continue
        sx,sy=rng.uniform(.16,.48,2);top=rng.uniform(.22,.65);yaw=rng.uniform(-math.pi,math.pi)
        ext=np.abs([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]])@np.array([sx,sy])
        lo,hi=point-ext,point+ext
        delta=np.maximum(np.maximum(lo-xy,xy-hi),0)
        proposal=occupied|(np.sum(delta*delta,axis=2)<=(nav.radius+nav.tracking_margin+nav.resolution*.71+.005)**2)
        labels,_=label(~proposal);ids=[labels[c] for c in cells]
        if not ids[0] or len(set(ids))!=1:continue
        occupied=proposal;accepted.append(point);j=len(accepted)-1
        kind='ellipsoid' if j%4 else 'box';color=[.34,.29,.23,1] if j%3 else [.43,.42,.38,1]
        g=geom(f'scattered_road_hazard_{j}',kind,[*point,top/2],[sx,sy,top/2],color,True);g.set('euler',f'0 0 {yaw}')
    if len(accepted)!=72:raise RuntimeError(f'Only {len(accepted)} of 72 irregular hazards could be placed safely')
    # Roadside detail stays outside the full-width road and swept foot envelope.
    for side in [-1,1]:
        for k,y in enumerate(np.arange(-35,39,7)):
            geom(f'outer_tree_trunk_{side}_{k}','cylinder',[side*43.,y,.9],[.15,.9],[.23,.17,.10,1])
            geom(f'outer_tree_crown_{side}_{k}','ellipsoid',[side*43.,y,2.2],[.85,.85,1.4],[.12,.30,.18,1])
    print('Expanded world: 6 destinations, 3 charging stations, 72 irregular road hazards, 12 rough road sections.')
