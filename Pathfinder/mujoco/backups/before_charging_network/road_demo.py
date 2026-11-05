"""Road surfaces and physical debris added separately from original robot assets."""
import math
import xml.etree.ElementTree as ET
import numpy as np

# x-low, x-high, y-low, y-high. The first strip guarantees an early visible
# terrain decision on the ordinary depot exit; later patches create time/distance choices.
EXPRESS_BYPASS=np.array([[0.,-20.],[3.25,-25.],[21.5,-25.],[27.75,-19.],[27.75,-1.75],[18.,7.75],[18.,16.]])
ROAD_LINES=[EXPRESS_BYPASS,np.array([[0.,-20.],[0.,-10.],[-10.,-10.],[-10.,16.],[-18.,16.]]),np.array([[-18.,-10.],[18.,-10.]]),np.array([[0.,-10.],[10.,-10.],[10.,11.],[18.,16.]])]

ROAD_PATCHES=np.array([[-3.5,3.5,-21.,-17.],[-12.,-8.,-6.,1.],
                      [8.,12.,-4.,3.],[-5.,2.,-12.,-8.]],dtype=float)


def ground_height(xy):
    """Height of the shallow, physical gravel pads (not deformable terrain)."""
    p=np.asarray(xy,dtype=float)
    inside=np.any((p[...,None,0]>=ROAD_PATCHES[:,0])&(p[...,None,0]<=ROAD_PATCHES[:,1])&
                  (p[...,None,1]>=ROAD_PATCHES[:,2])&(p[...,None,1]<=ROAD_PATCHES[:,3]),axis=-1)
    return np.where(inside,.035,0.)


def ground_clearance(xy,radius=1.9):
    p=np.asarray(xy)
    return .035 if np.any((p[0]>=ROAD_PATCHES[:,0]-radius)&(p[0]<=ROAD_PATCHES[:,1]+radius)&(p[1]>=ROAD_PATCHES[:,2]-radius)&(p[1]<=ROAD_PATCHES[:,3]+radius)) else 0.


def add_road_demo(root):
    world=root.find('worldbody')
    def geom(name,kind,pos,size,rgba,physical=True,parent=world):
        return ET.SubElement(parent,'geom',name=name,type=kind,pos=' '.join(map(str,pos)),
            size=' '.join(map(str,size)),rgba=' '.join(map(str,rgba)),
            contype='1' if physical else '0',conaffinity='7' if physical else '0',friction='1.3 .02 .002')
    for j,(a,b) in enumerate(zip(EXPRESS_BYPASS,EXPRESS_BYPASS[1:])):
        delta=b-a;length=float(np.linalg.norm(delta));direction=delta/length
        yaw=math.atan2(delta[1],delta[0])
        road=geom(f'express_asphalt_{j}','box',[*(a+b)/2,.008],[length/2,1.65,.003],[.085,.10,.115,1],False)
        road.set('euler',f'0 0 {yaw}')
        for k,t in enumerate(np.arange(.5,length,1.6)):
            mark=geom(f'express_dash_{j}_{k}','box',[*(a+t*direction),.013],[.38,.035,.003],[.92,.83,.43,1],False)
            mark.set('euler',f'0 0 {yaw}')
    rng=np.random.default_rng(20261022)
    for k,(x0,x1,y0,y1) in enumerate(ROAD_PATCHES):
        geom(f'rough_road_pad_{k}','box',[(x0+x1)/2,(y0+y1)/2,.010],[(x1-x0)/2,(y1-y0)/2,.025],[.28,.22,.15,1])
        # Shallow stones are supports; taller debris below are real blocking obstacles.
        for j in range(95):
            x,y=rng.uniform(x0,x1),rng.uniform(y0,y1)
            geom(f'gravel_{k}_{j}','ellipsoid',[x,y,.027],[rng.uniform(.04,.11),rng.uniform(.035,.08),.008],[.43,.37,.28,1],False)
        for j in range(4):
            y=y0+(j+.5)*(y1-y0)/4
            geom(f'road_rut_{k}_{j}','box',[(x0+x1)/2,y,.036],[(x1-x0)/2,.028,.002],[.12,.10,.08,1],False)
        geom(f'rough_sign_post_{k}','cylinder',[x1+.2,y0, .6],[.035,.6],[.6,.6,.64,1],False)
        geom(f'rough_sign_{k}','box',[x1+.2,y0,1.12],[.025,.40,.22],[1.,.64,.02,1],False)
    # Separated small road hazards. None is hidden from the global map.
    sites=[(-8.4,-3.8),(-11.8,5.5),(8.3,5.8),(11.8,-5.8),
           (-5.4,-11.8),(5.6,-8.3),(-5.2,-16.),(5.3,-15.8),
           (-14.0,14.2),(14.,11.7),(-14.,-11.8),(14.,-8.2)]
    for j,(x,y) in enumerate(sites):
        geom(f'small_road_rock_{j}','ellipsoid',[x,y,.22],[.22,.18,.22],[.36,.31,.25,1])
        geom(f'hazard_cone_{j}','cylinder',[x+.38,y,.16],[.10,.16],[1.,.28,.02,1])
        geom(f'hazard_reflector_{j}','cylinder',[x+.38,y,.20],[.102,.025],[1.,.96,.8,1],False)
    body=ET.SubElement(world,'body',name='roadwork_obstacle',mocap='true',pos='100 100 0')
    geom('roadwork_collision','box',[0,0,.32],[.38,.30,.32],[1.,.28,.02,1],True,body)
    for i in range(4):
        geom(f'roadwork_stripe_{i}','box',[-.29+i*.19,-.305,.33],[.045,.008,.27],[.08,.08,.08,1],False,body)
    geom('roadwork_beacon','sphere',[0,0,.72],[.10],[1.,.05,.02,1],False,body)


def reserve_debris_passages(root):
    """Place added hazards without sealing a full-leg-width access corridor."""
    import mujoco
    from safe_navigation import SafeNavigator
    from multi_place_config import DEST_BASE,DEST_KIOSK_PAD,MISSION_TARGETS
    from collections import deque
    model=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
    data=mujoco.MjData(model);mujoco.mj_forward(model,data)
    groups=[[model.geom(f'small_road_rock_{j}').id,model.geom(f'hazard_cone_{j}').id] for j in range(12)]
    for ids in groups:model.geom_contype[ids]=0;model.geom_conaffinity[ids]=0
    targets=[np.asarray(DEST_BASE),np.asarray(DEST_KIOSK_PAD)]+[np.asarray(t['pos']) for t in MISSION_TARGETS]
    baseline=None
    def distances(nav):
        if not all(nav.clear(p) for p in targets):return None
        cells=[nav.nearest_free(p) for p in targets]
        remaining=set(cells[1:]);q=deque([cells[0]]);seen={cells[0]:0};found={}
        while q and remaining:
            x,y=q.popleft()
            if (x,y) in remaining:remaining.remove((x,y));found[(x,y)]=seen[(x,y)]*nav.resolution
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                c=(x+dx,y+dy)
                if 0<=c[0]<nav.n and 0<=c[1]<nav.n and c not in seen and not nav.blocked[c]:seen[c]=seen[(x,y)]+1;q.append(c)
        return None if remaining else [found[c] for c in cells[1:]]
    baseline=distances(SafeNavigator(model,data))
    if baseline is None:raise RuntimeError('Baseline destination network is disconnected')
    for j,ids in enumerate(groups):
        original=model.geom_pos[ids].copy()
        shifts=[(0,0)]+[(dx*r,dy*r) for r in (1.,2.,3.,4.) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1))]
        for shift in shifts:
            model.geom_pos[ids,:2]=original[:,:2]+shift
            model.geom_contype[ids]=1;model.geom_conaffinity[ids]=7
            mujoco.mj_forward(model,data);nav=SafeNavigator(model,data)
            lengths=distances(nav)
            if lengths is not None and all(a<=b*1.22+3. for a,b in zip(lengths,baseline)):break
        else:raise RuntimeError(f'Cannot place road hazard {j} with safe destination access')
        for name in (f'small_road_rock_{j}',f'hazard_cone_{j}',f'hazard_reflector_{j}'):
            element=root.find(f".//geom[@name='{name}']")
            pos=np.fromstring(element.get('pos'),sep=' ');pos[:2]+=shift;element.set('pos',' '.join(map(str,pos)))
        if shift!=(0,0):print('Preserved debris detour clearance:',j,shift)
