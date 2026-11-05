"""Diagnostic assistance removal on four previously observed V6 saved routes.

This is a sensitivity diagnostic, not a new held-out locomotion benchmark.
"""
from pathlib import Path
import json,sys
B=Path(__file__).resolve().parents[1];ROOT=B.parent;M=ROOT/'workbench/mujoco'
sys.path.insert(0,str(M))
from research.worlds import terrain_context,world_model
from research.execution import execute


def main():
    primary=json.loads((B/'results/realism_probe_input_v6.json').read_text())
    rows=[];cases=primary['cases'][:4]
    protocol=dict(cases=[c['id'] for c in cases],conditions=[dict(assistance=1.,gravity_compensation=True),dict(assistance=.5,gravity_compensation=True),dict(assistance=0.,gravity_compensation=True),dict(assistance=0.,gravity_compensation=False)],
        scope='Post-hoc diagnostic on four already observed V6 worlds; cannot validate real-world fidelity. Zero velocity assistance alone still retains ideal gravity compensation.',max_seconds=180.)
    (B/'results/realism_probe_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for case in cases:
        p=next(r['plan'] for r in primary['records'] if r['case_id']==case['id'] and r['repeat']==0 and r['method']=='proposed_v4')
        for condition in protocol['conditions']:
            row=dict(case=case['id'],family=case['world']['family'],**condition,admitted=p.get('admissible',False))
            if p.get('admissible'):
                with terrain_context(case['world']):
                    model=world_model(case['world'])
                    if not condition['gravity_compensation']:model.body_gravcomp[:]=0
                    result=execute(model,p['points'],case['battery_percent'],walking_only=True,max_seconds=180.,return_route=case['return_route'],
                        assistance_scale=condition['assistance'],tracking_policy='safe_v6')
                row['execution']=result
            rows.append(row);(B/'results/realism_probe.json').write_text(json.dumps(dict(protocol=protocol,records=rows,state='running'),indent=2)+'\n')
            print(case['id'],condition,row.get('execution',{}).get('outcome','not admitted'),flush=True)
    (B/'results/realism_probe.json').write_text(json.dumps(dict(protocol=protocol,records=rows,state='complete'),indent=2)+'\n')


if __name__=='__main__':main()
