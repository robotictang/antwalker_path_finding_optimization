from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
base=Path(__file__).resolve().parents[1]
fig,ax=plt.subplots(figsize=(9,8));ax.set_xlim(0,10);ax.set_ylim(-.6,10.5);ax.axis('off')
steps=[('Same input for every method','Map, start, goal, deadline, battery and terrain limits'),('Safe starting route','V3 search time counts toward the same total planning allowance'),('Geometry alternatives','Try direct visibility and obstacle / terrain landmarks'),('Small visibility roadmap','Search alternative connections with heading-aware costs'),('Continuous polishing','Remove or move waypoints; keep feasible-first improvements'),('Final common evaluation','Recheck collisions, resources and unchanged balanced score')]
ys=[9.3,7.8,6.3,4.8,3.3,1.8]
for j,((title,body),y) in enumerate(zip(steps,ys)):
 ax.add_patch(FancyBboxPatch((.8,y-.55),8.4,1.05,boxstyle='round,pad=.08',linewidth=1.2,edgecolor='#355d80',facecolor='#eff3f6'))
 ax.text(5,y+.12,title,ha='center',va='center',fontsize=12,weight='bold',color='#22394b');ax.text(5,y-.23,body,ha='center',va='center',fontsize=9,color='#364b5a')
 if j<5:ax.annotate('',xy=(5,ys[j+1]+.58),xytext=(5,y-.64),arrowprops=dict(arrowstyle='->',color='#355d80',lw=1.5))
ax.text(5,.35,'Keep the best known safe route if time or candidate limits stop the search.',ha='center',fontsize=10,color='#22394b')
ax.text(5,-.08,'Balanced score = D/50 + T/90 + E/30 + 0.25 H/20   •   Lower is better',ha='center',fontsize=10,color='#364b5a')
ax.text(5,-.43,'D: metres   T: seconds   E: modeled battery percentage points   H: terrain exposure',ha='center',fontsize=8,color='#364b5a')
fig.tight_layout();fig.savefig(base/'figures/V4_Method_Flow.png',dpi=200,bbox_inches='tight');plt.close(fig)
