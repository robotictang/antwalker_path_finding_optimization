"""Shared landscape metadata, physical no-go terrain and named road decals."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from terrain_classes import EXTREME_BOUNDS,ROAD_LABELS
rng=np.random.default_rng(1810)
MAP_TREES=[dict(x=float(s*(43.+rng.uniform(-.55,.55))),y=float(y+rng.uniform(-1.8,1.8)),r=float(rng.uniform(.65,1.1))) for s in (-1,1) for y in np.arange(-35,39,7)]
WATER=[[-45.,-34.],[-40.,-29.],[-42.,-25.],[-40.,-21.],[-42.,-17.],[-45.,-14.]]


def add_terrain_scenery(root):
    world=root.find('worldbody');asset=root.find('asset');rng=np.random.default_rng(846)
    def g(name,kind,pos,size,color,physical=False):
        return ET.SubElement(world,'geom',name=name,type=kind,pos=' '.join(map(str,pos)),size=' '.join(map(str,size)),rgba=' '.join(map(str,color)),contype='1' if physical else '0',conaffinity='7' if physical else '0',friction='1.3 .02 .002')
    for i,(x0,x1,y0,y1) in enumerate(EXTREME_BOUNDS):
        g(f'extreme_base_{i}','box',[(x0+x1)/2,(y0+y1)/2,.1],[(x1-x0)/2,(y1-y0)/2,.1],[.26,.20,.15,1],True)
        for j in range(14):
            e=g(f'extreme_rock_{i}_{j}','ellipsoid',[rng.uniform(x0+.25,x1-.25),rng.uniform(y0+.25,y1-.25),rng.uniform(.15,.35)],[rng.uniform(.4,.85),rng.uniform(.3,.65),rng.uniform(.35,.7)],[.39,.32,.25,1],True)
            e.set('euler',f'{rng.uniform(-.3,.3)} {rng.uniform(-.3,.3)} {rng.uniform(-3,3)}')
        for side in (-1,1):
            x,y=(x0+x1)/2,y0-1.2 if side<0 else y1+1.2
            g(f'extreme_post_{i}_{side}','cylinder',[x,y,.65],[.045,.65],[.5,.5,.48,1])
            g(f'extreme_board_{i}_{side}','box',[x,y,1.25],[.5,.045,.3],[.98,.43,.08,1])
            for k in (-1,1):
                e=g(f'extreme_cross_{i}_{side}_{k}','box',[x,y-.05,1.25],[.32,.012,.035],[.15,.08,.05,1]);e.set('euler',f'0 {k*.6} 0')
    for e in world:
        if e.tag=='geom' and e.get('name','').startswith('mount_'):
            size=np.fromstring(e.get('size'),sep=' ');r,h=size[0],size[-1]
            e.set('type','ellipsoid');e.set('size',f'{r*1.1} {r*.85} {h*.64}')
            p=np.fromstring(e.get('pos'),sep=' ');p[2]=h*.4;e.set('pos',' '.join(map(str,p)))
    for i,(x,y) in enumerate([(-43.,-29.),(-43.5,-25.),(-43.,-21.),(-44.,-17.)]):
        g(f'river_bank_{i}','ellipsoid',[x,y,.006],[2.5,3.1,.007],[.32,.29,.17,1])
        g(f'river_pool_{i}','ellipsoid',[x,y,.019],[1.8,2.7,.008],[.13,.36,.39,.95])
    from PIL import Image,ImageDraw,ImageFont
    out=Path(__file__).resolve().parent/'textures';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',60)
    for i,road in enumerate(ROAD_LABELS):
        path=out/f'road_name_{i}.png';im=Image.new('RGB',(768,128),(33,41,41));draw=ImageDraw.Draw(im)
        draw.rounded_rectangle((4,4,764,124),radius=16,outline=(177,190,162),width=3)
        draw.text((384,64),road['name'],font=font,anchor='mm',fill=(240,232,194));im.save(path)
        ET.SubElement(asset,'texture',name=f'road_name_tex_{i}',type='2d',file=str(path))
        ET.SubElement(asset,'material',name=f'road_name_mat_{i}',texture=f'road_name_tex_{i}',texrepeat='1 1',texuniform='false')
        x,y=road['label'];e=g(f'road_name_decal_{i}','box',[x,y,.022],[3.,.52,.001],[1,1,1,1]);e.set('material',f'road_name_mat_{i}');e.set('euler',f"0 0 {math.radians(-road['angle'])}")
