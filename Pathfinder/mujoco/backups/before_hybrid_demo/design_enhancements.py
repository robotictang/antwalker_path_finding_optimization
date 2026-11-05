"""Repeatable CAD detailing and scene layout with full leg clearance."""
import math
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from multi_place_config import MISSION_TARGETS, DEST_BASE, DEST_KIOSK_ENTRY, DEST_KIOSK_PAD, get_kiosk_departure_corridor


def add_design_details(root):
    asset = root.find('asset')
    for name,rgba in [('service_silver','.52 .59 .64 1'),('pack_orange','.94 .31 .055 1'),('panel_dark','.065 .09 .115 1'),('route_teal','.18 .31 .14 1')]:
        ET.SubElement(asset,'material',name=name,rgba=rgba,specular='.45',shininess='.4')
    world=root.find('worldbody')
    def geom(name,kind,size,pos,mat,parent=world,**kw):
        return ET.SubElement(parent,'geom',name=name,type=kind,size=size,pos=pos,material=mat,contype='0',conaffinity='0',density='.01',**kw)
    # Richer perimeter landscaping, with a clear distance from the mission roads.
    world=root.find('worldbody')
    for side in (-1,1):
        for k in range(10):
            x,y=side*29.,-22.+k*5.
            geom(f'landscape_bed_{side}_{k}','box','1.1 1.1 .07',f'{x} {y} .07','concrete_pad_mat',parent=world)
            geom(f'landscape_shrub_{side}_{k}','ellipsoid','.85 .85 .55',f'{x} {y} .5','route_teal',parent=world)
    # Wayfinding pylons off the routes; site colors match the four biomes.
    for idx,(x,y,color) in enumerate([(-25,10,'.15 .5 .25 1'),(25,10,'.6 .48 .3 1'),(-25,-18,'.08 .48 .6 1'),(25,-18,'.85 .52 .13 1')],1):
        mat=f'site_identity_{idx}';ET.SubElement(asset,'material',name=mat,rgba=color,emission='.25')
        geom(f'wayfinding_post_{idx}','box','.07 .07 1.',f'{x} {y} 1.','service_silver',parent=world)
        geom(f'wayfinding_panel_{idx}','box','.65 .10 .38',f'{x} {y} 1.8',mat,parent=world)
        for bar in range(idx):
            geom(f'wayfinding_digit_{idx}_{bar}','box','.035 .01 .22',f'{x-.15*(idx-1)+bar*.3} {y-.115} 1.8','honda_white_fascia',parent=world)


def reserve_route_clearance(root, radius=2.08):
    """Move roadside props as assemblies, opening continuous lanes for the leg sweep.

    This is a static scene preparation step, not runtime collision suppression.
    All existing physical contacts stay enabled.
    """
    segments=[]
    def route(points):
        for a,b in zip(points,points[1:]):
            segments.append((np.asarray(a,dtype=float),np.asarray(b,dtype=float)))
    for t in MISSION_TARGETS:
        route(t['approach'])
        route([t['approach'][-1]]+[s['pos'] for s in t['circuit']])
        route([t['circuit'][-1]['pos']]+t['return_corridor'])
        route(get_kiosk_departure_corridor(MISSION_TARGETS.index(t)))
    route([DEST_BASE,DEST_KIOSK_ENTRY,DEST_KIOSK_PAD])
    # The charging approach crosses the highway at y=-4 on either side.
    route([[-10,-10],[-10,-4],[0,-4],[10,-4],[10,16]])
    a=np.array([s[0] for s in segments]);b=np.array([s[1] for s in segments]);v=b-a;vv=np.sum(v*v,axis=1)
    def distance(points):
        w=points[:,None,:]-a
        frac=np.clip(np.sum(w*v,axis=2)/np.maximum(vv,1e-8),0,1)
        return np.sqrt(np.min(np.sum((w-frac[:,:,None]*v)**2,axis=2),axis=1))
    world=root.find('worldbody');owners={};elements={}
    for k,elem in enumerate(world):
        if elem.tag not in ('geom','body') or elem.get('name')=='robot':continue
        for j,g in enumerate([elem] if elem.tag=='geom' else elem.iter('geom')):
            if not g.get('name'):g.set('name',f'layout_geom_{k}_{j}')
            owners[g.get('name')]=k
        elements[k]=elem
    # MuJoCo resolves defaults, body transforms, and mesh hull extents for us.
    m=mujoco.MjModel.from_xml_string(ET.tostring(root,encoding='unicode'))
    d=mujoco.MjData(m);mujoco.mj_forward(m,d)
    groups={}
    bounds={}
    for i in range(m.ngeom):
        name=m.geom(i).name
        if name not in owners or not(m.geom_contype[i] or m.geom_conaffinity[i]) or m.geom_type[i] in (0,1):continue
        rot=d.geom_xmat[i].reshape(3,3);center=d.geom_xpos[i]+rot@m.geom_aabb[i,:3];extent=np.abs(rot)@m.geom_aabb[i,3:]
        if center[2]+extent[2]<.12 or center[2]-extent[2]>1.65:continue
        # Sample edges too, so long logs or building walls never clip a lane.
        samples=np.array([center[:2]+extent[:2]*[x,y] for x in np.linspace(-1,1,5) for y in np.linspace(-1,1,5)])
        groups.setdefault(owners[name],[]).extend(samples)
        bounds.setdefault(owners[name],[]).append((center[:2]-extent[:2],center[:2]+extent[:2]))
    moved=[]
    candidates=sorted([(x*.5,y*.5) for x in range(-20,21) for y in range(-20,21) if x or y],key=lambda p:p[0]**2+p[1]**2)
    for owner,points in groups.items():
        points=np.array(points)
        if distance(points).min()>radius:continue
        others=np.array([box for key,boxes in bounds.items() if key != owner for box in boxes])
        own=np.array(bounds[owner])
        for shift in candidates:
            if distance(points+shift).min()>radius+.10:
                shifted=own+np.array(shift)
                separation=np.maximum(others[None,:,0]-shifted[:,None,1],shifted[:,None,0]-others[None,:,1])
                if np.any(np.all(separation < .08,axis=2)):
                    continue
                elem=elements[owner];pos=np.fromstring(elem.get('pos','0 0 0'),sep=' ')
                pos[:2]+=shift;elem.set('pos',' '.join(map(str,pos)))
                bounds[owner]=list(shifted)
                moved.append((elem.get('name',elem.tag),shift));break
        else:raise RuntimeError(f'Cannot provide leg clearance around {elements[owner].get("name")}')
    print(f'Reserved full-leg mission lanes: repositioned {len(moved)} roadside/site assemblies')
    return moved


def enhance_scene(path):
    tree=ET.parse(path);root=tree.getroot()
    from strict_asset import finalize_source_robot
    finalize_source_robot(root)
    add_design_details(root);reserve_route_clearance(root)
    ET.indent(tree,space='  ');tree.write(path,encoding='unicode')
