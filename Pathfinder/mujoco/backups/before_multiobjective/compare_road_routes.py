"""Compare both objectives from identical start/heading; preserve routes for visual QA."""
import json,math
from pathlib import Path
import mujoco,numpy as np
from safe_navigation import SafeNavigator
from multi_place_config import DEST_BASE,MISSION_TARGETS
ROOT=Path(__file__).resolve().parent
m=mujoco.MjModel.from_xml_path(str(ROOT/'hybrid_hexapod_multi_place.xml'));d=mujoco.MjData(m);mujoco.mj_forward(m,d);n=SafeNavigator(m,d)
results=[]
for i,t in enumerate(MISSION_TARGETS):
    row={'destination':i+1}
    for mode in ['shortest','fastest']:
        path=[DEST_BASE]+n.plan(DEST_BASE,t['pos'],mode=mode,yaw=math.pi/2)
        assert all(n.segment_clear(a,b) for a,b in zip(path,path[1:]))
        row[mode]=dict(points=[np.asarray(p).tolist() for p in path],**n.route_metrics(path,math.pi/2))
    results.append(row)
    print(i+1,{k:{a:round(v,2) if isinstance(v,float) else v for a,v in row[k].items() if a!='points'} for k in ['shortest','fastest']},flush=True)
(ROOT/'outputs/road_route_comparison.json').write_text(json.dumps(results,indent=2))
