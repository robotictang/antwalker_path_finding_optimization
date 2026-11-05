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
    sites=[(-35,-24),(-35,-3),(-35,18),(35,-24),(35,-2),(35,20),
           (-27,-30),(-13,-30),(9,-30),(26,-30),(-26,28),(-7,28),(9,28),(27,28),
           (-24,-24),(24,-24),(-29,2),(29,2),(-30,16),(30,16)]
    for j,(x,y) in enumerate(sites):
        shift=.65 if j%2 else -.65
        geom(f'wide_road_boulder_{j}','ellipsoid',[x+shift,y,.28],[.32,.26,.28],[.4,.34,.27,1],True)
        geom(f'wide_road_cone_{j}','cylinder',[x-shift,y+.55,.19],[.12,.19],[1.,.28,.025,1],True)
        geom(f'wide_road_cone_stripe_{j}','cylinder',[x-shift,y+.55,.24],[.122,.03],[1.,.95,.85,1])
    # Roadside detail stays outside the full-width road and swept foot envelope.
    for side in [-1,1]:
        for k,y in enumerate(np.arange(-35,39,7)):
            geom(f'outer_tree_trunk_{side}_{k}','cylinder',[side*43.,y,.9],[.15,.9],[.23,.17,.10,1])
            geom(f'outer_tree_crown_{side}_{k}','ellipsoid',[side*43.,y,2.2],[.85,.85,1.4],[.12,.30,.18,1])
    print('Expanded navigation area: 96 x 96 m; 12 new road links, 8.4 m wide; 40 additional physical hazards.')
