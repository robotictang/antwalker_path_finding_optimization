"""Fit a battery ledger only from externally measured electrical energy.

Simulation-ledger readings are deliberately not accepted as calibration truth.
No hardware calibration is claimed when this command has not received real data.
"""
import argparse,csv,hashlib,json
from contextlib import contextmanager
from pathlib import Path
import numpy as np
from scipy.optimize import nnls
import energy_model as em

COLUMNS=['mission_id','map_id','split','distance_m','seconds','turn_radians','electrical_energy_wh']
COEFFICIENTS=['WALK_PERCENT_PER_M','HOTEL_PERCENT_PER_S','TURN_PERCENT_PER_RAD','START_STOP_PERCENT']
def fit(csv_path,metadata_path):
    csv_path,metadata_path=Path(csv_path),Path(metadata_path)
    metadata=json.loads(metadata_path.read_text())
    if metadata.get('measurement_origin')!='external_hardware':raise ValueError('Real external electrical measurements are required; simulator ledgers are not calibration truth')
    capacity=float(metadata.get('usable_battery_capacity_wh',0))
    if not np.isfinite(capacity) or capacity<=0 or not metadata.get('sensor_description'):raise ValueError('Specify usable battery capacity in Wh and the measurement sensor')
    with csv_path.open() as f:
        reader=csv.DictReader(f)
        if not set(COLUMNS).issubset(reader.fieldnames or []):raise ValueError('Missing calibration CSV columns')
        rows=list(reader)
    groups={split:[r for r in rows if r['split']==split] for split in ['calibration','validation']}
    if len(groups['calibration'])<12 or len(groups['validation'])<6 or sum(map(len,groups.values()))!=len(rows):raise ValueError('Use at least 12 calibration and 6 held-out validation observations with explicit splits')
    ids={split:{r['mission_id'] for r in values} for split,values in groups.items()}
    maps={split:{r['map_id'] for r in values} for split,values in groups.items()}
    if any(not r['mission_id'] or not r['map_id'] for r in rows):raise ValueError('Every row needs a mission and map identifier')
    if ids['calibration']&ids['validation'] or maps['calibration']&maps['validation']:raise ValueError('Calibration and validation must use disjoint missions and maps')
    if len(ids['calibration'])<3 or len(ids['validation'])<3:raise ValueError('At least three distinct missions are required in each split')
    def arrays(values):
        x=np.array([[float(r[k]) for k in ['distance_m','seconds','turn_radians']]+[1.] for r in values])
        y=np.array([100*float(r['electrical_energy_wh'])/capacity for r in values])
        if not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(x<0) or np.any(y<0):raise ValueError('Measurements must be finite and nonnegative')
        return x,y
    x,y=arrays(groups['calibration']);vx,vy=arrays(groups['validation'])
    if np.linalg.matrix_rank(x)<4:raise ValueError('Calibration inputs do not identify four separate coefficients; vary speed, distance and turning')
    coef,_=nnls(x,y);pred=vx@coef;residual=pred-vy
    return dict(version=1,status='fitted_external_hardware',measurement_origin='external_hardware',
      coefficients=dict(zip(COEFFICIENTS,map(float,coef))),metadata=metadata,
      csv_sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(),metadata_sha256=hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
      calibration_rows=len(x),validation_rows=len(vx),validation_mae_pp=float(np.mean(abs(residual))),validation_rmse_pp=float(np.sqrt(np.mean(residual**2))),
      scope='Walking-only nonnegative linear electrical-energy ledger. External sensor and capacity accuracy still require human verification.')

def validate_profile(profile):
    if isinstance(profile,(str,Path)):profile=json.loads(Path(profile).read_text())
    if profile is None:return None
    if profile.get('status')!='fitted_external_hardware' or profile.get('measurement_origin')!='external_hardware':raise ValueError('Only externally measured fitted energy profiles may be applied')
    values=profile.get('coefficients',{})
    if set(values)!=set(COEFFICIENTS) or not all(np.isfinite(v) and v>=0 for v in values.values()):raise ValueError('Invalid energy coefficients')
    return profile

@contextmanager
def energy_context(profile):
    profile=validate_profile(profile)
    if profile is None:yield;return
    import safe_navigation
    previous=[]
    try:
        for module in [em,safe_navigation]:
            for key,value in profile['coefficients'].items():
                if hasattr(module,key):previous.append((module,key,getattr(module,key)));setattr(module,key,value)
        yield
    finally:
        for module,key,value in reversed(previous):setattr(module,key,value)

def write_template(directory):
    directory=Path(directory);directory.mkdir(exist_ok=True,parents=True)
    with (directory/'electrical_measurements.csv').open('w',newline='') as f:csv.writer(f).writerow(COLUMNS)
    (directory/'metadata.json').write_text(json.dumps(dict(measurement_origin='external_hardware',usable_battery_capacity_wh=None,sensor_description='',notes='Replace with actual measured capacity and sensor details. Do not enter simulation-ledger readings.'),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',type=Path);p.add_argument('--csv',type=Path);p.add_argument('--metadata',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.template:write_template(a.template)
    elif a.csv and a.metadata and a.out:a.out.write_text(json.dumps(fit(a.csv,a.metadata),indent=2));print(a.out)
    else:p.error('Choose --template DIRECTORY or --csv FILE --metadata FILE --out PROFILE')
