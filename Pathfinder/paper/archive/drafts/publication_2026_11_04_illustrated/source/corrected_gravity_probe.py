"""Post hoc correction of the requested no-gravity-compensation diagnostic.

The archived probe changed model fields before HybridLocomotion initialization,
which restored the 18 limb values. This wrapper changes fields after initialization
and records the realized setting without editing the frozen research sources.
"""
from pathlib import Path
import hashlib,json,sys
import numpy as np
B=Path(__file__).resolve().parents[1];M=B.parent/'workbench/mujoco'
sys.path.insert(0,str(M))
import research.execution as ex
from research.worlds import terrain_context,world_model
Original=ex.HybridLocomotion
settings=[]
class WithoutGravityCompensation(Original):
    def __init__(self,model,data):
        super().__init__(model,data)
        enabled_before=int(np.count_nonzero(model.body_gravcomp))
        model.body_gravcomp[:]=0
        settings.append(dict(enabled_before=enabled_before,enabled_after=int(np.count_nonzero(model.body_gravcomp)),values_after=model.body_gravcomp.tolist()))
ex.HybridLocomotion=WithoutGravityCompensation
raw=B/'results/realism_probe_input_v6.json'
source=json.loads(raw.read_text());rows=[]
protocol=dict(scope='Post hoc correction on four previously observed routes; not a held-out locomotion test',input_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),assistance=0.,gravity_compensation=False,max_seconds=180.,correction='Disable gravity compensation after HybridLocomotion constructor, which otherwise enables the 18 limb bodies',frozen_execution_sha256=hashlib.sha256((M/'research/execution.py').read_bytes()).hexdigest(),frozen_locomotion_sha256=hashlib.sha256((M/'hybrid_locomotion.py').read_bytes()).hexdigest())
for case in source['cases'][:4]:
    plan=next(r['plan'] for r in source['records'] if r['case_id']==case['id'] and r['repeat']==0 and r['method']=='proposed_v4')
    assert plan['admissible']
    with terrain_context(case['world']):
        model=world_model(case['world'])
        result=ex.execute(model,plan['points'],case['battery_percent'],walking_only=True,max_seconds=180.,return_route=case['return_route'],assistance_scale=0.,tracking_policy='safe_v6')
    assert settings[-1]['enabled_before']==18 and settings[-1]['enabled_after']==0
    rows.append(dict(case=case['id'],family=case['world']['family'],assistance=0.,gravity_compensation=False,realized_settings=settings[-1],execution=result))
    (B/'results/corrected_gravity_probe.json').write_text(json.dumps(dict(state='complete' if len(rows)==4 else 'running',protocol=protocol,records=rows),indent=2)+'\n')
    print(case['id'],result['outcome'],result['distance_m'],result['elapsed_s'],flush=True)
