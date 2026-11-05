"""Export the actual route alternatives and cost estimates for the quarry."""
import json
from pathlib import Path
import numpy as np
import mujoco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from safe_navigation import SafeNavigator
from terrain_profile import BOUNDS
from road_demo import ROAD_LINES
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'outputs/road_route_comparison.json').read_text())
row=rows[1]
m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);nav=SafeNavigator(m,d)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':'#e6edf3','axes.labelcolor':'#adbaca','xtick.color':'#9bafbd','ytick.color':'#9bafbd'})
fig,axes=plt.subplots(1,2,figsize=(13,8),facecolor='#0c131d')
for ax,mode,color in zip(axes,['shortest','fastest'],['#ff68b6','#58efab']):
    ax.set_facecolor('#101e2b')
    for x0,x1,y0,y1 in BOUNDS:ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#8e6c32',alpha=.45))
    for road in ROAD_LINES:ax.plot(*road.T,color='#243b4d',lw=13,alpha=.7,zorder=0)
    for lo,hi in nav.boxes:ax.add_patch(Rectangle(lo,*(hi-lo),facecolor='#627587',alpha=.65))
    points=np.array(row[mode]['points']);ax.plot(*points.T,color=color,lw=2.6,zorder=5)
    ax.scatter(*points[0],c='white',s=38,zorder=6);ax.annotate('DEPOT',points[0],xytext=(-14,-20),textcoords='offset points',color='white',fontsize=9)
    ax.scatter(*points[-1],c=color,s=48,zorder=6);ax.annotate('QUARRY',points[-1],xytext=(9,4),textcoords='offset points',color=color,fontsize=10)
    ax.scatter(0,1.2,c='#64dfea',s=40);ax.text(.9,1.2,'CHARGER',color='#64dfea',fontsize=8)
    a=row[mode]
    ax.set_title(f'{mode.upper()}\n{a["distance_m"]:.1f} m  ·  {a["estimated_seconds"]:.1f} s estimated',color=color,fontsize=16,pad=14)
    ax.text(.02,.02,f'{a["walking_distance_m"]:.1f} m walking  /  {a["transformations"]} mode changes',transform=ax.transAxes,color='#ecddc0',fontsize=10)
    ax.set(xlim=(-27,32),ylim=(-31,25),aspect='equal');ax.set_xlabel('Map X (m)');ax.grid(alpha=.07)
    for spine in ax.spines.values():spine.set_color('#314557')
a,b=row['shortest'],row['fastest']
fig.suptitle('Same destination. Different route objectives.',fontsize=23,x=.5,y=.97)
fig.text(.5,.905,f'Quarry: fastest adds {b["distance_m"]-a["distance_m"]:.1f} m, saves about {a["estimated_seconds"]-b["estimated_seconds"]:.1f} s, and needs fewer terrain changes.',ha='center',color='#c0ceda',fontsize=12)
fig.text(.5,.055,'Brown = rough ground requiring legs   ·   Gray = physical obstacles\nBaseline estimates before roadwork detection or charging diversion; the live mission replans after either event.',ha='center',color='#a4b6c5',fontsize=10,linespacing=1.7)
fig.subplots_adjust(left=.05,right=.98,top=.81,bottom=.16,wspace=.16)
fig.savefig(ROOT/'outputs/shortest_vs_fastest.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
print(ROOT/'outputs/shortest_vs_fastest.png')
