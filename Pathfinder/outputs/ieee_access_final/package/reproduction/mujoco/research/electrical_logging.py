"""Integrate externally recorded discharge voltage/current, without simulation truth."""
import argparse,csv,json,hashlib
from pathlib import Path
import numpy as np

def integrate(samples,metadata):
    samples,metadata=Path(samples),Path(metadata);meta=json.loads(metadata.read_text())
    if meta.get('measurement_origin')!='external_hardware' or not meta.get('sensor_description'):
        raise ValueError('External hardware origin and a sensor description are required')
    required=['mission_id','map_id','split','distance_m','turn_radians']
    if any(k not in meta for k in required) or meta['split'] not in ('calibration','validation'):raise ValueError('Supply mission, map, split, measured distance and measured turn')
    with samples.open() as f:
        reader=csv.DictReader(f)
        if not {'timestamp_s','voltage_v','discharge_current_a'}<=set(reader.fieldnames or []):raise ValueError('Missing raw electrical sample columns')
        rows=list(reader)
    if len(rows)<2:raise ValueError('At least two real electrical samples are required')
    a=np.array([[float(r[k]) for k in ['timestamp_s','voltage_v','discharge_current_a']] for r in rows])
    if not np.isfinite(a).all() or np.any(np.diff(a[:,0])<=0) or np.any(a[:,1]<=0) or np.any(a[:,2]<0):raise ValueError('Use finite strictly increasing timestamps, positive voltage and nonnegative discharge current; charging is excluded')
    power=a[:,1]*a[:,2];energy=float(np.sum(.5*(power[1:]+power[:-1])*np.diff(a[:,0]))/3600)
    values=dict(distance_m=float(meta['distance_m']),turn_radians=float(meta['turn_radians']))
    if not all(np.isfinite(v) and v>=0 for v in values.values()):raise ValueError('Measured distance and turning must be finite and nonnegative')
    return dict(mission_id=meta['mission_id'],map_id=meta['map_id'],split=meta['split'],**values,
      seconds=float(a[-1,0]-a[0,0]),electrical_energy_wh=energy,measurement_origin='external_hardware',
      sample_count=len(rows),samples_sha256=hashlib.sha256(samples.read_bytes()).hexdigest(),metadata_sha256=hashlib.sha256(metadata.read_bytes()).hexdigest(),
      scope='Trapezoidal integral of externally supplied discharge voltage times current. Sensor accuracy, timestamps and measurement origin still require human verification.')

def template(directory):
    d=Path(directory);d.mkdir(parents=True,exist_ok=True)
    (d/'raw_voltage_current.csv').write_text('timestamp_s,voltage_v,discharge_current_a\n')
    (d/'mission_metadata.json').write_text(json.dumps(dict(measurement_origin='external_hardware',sensor_description='',mission_id='',map_id='',split='calibration',distance_m=None,turn_radians=None),indent=2))
    from research.calibration import write_template
    write_template(d)
    (d/'MEASUREMENT_PROTOCOL.md').write_text('''# Electrical battery validation still requires real measurements

No sensor values or fitted coefficients are supplied in this package.

1. Record synchronized voltage, discharge current and timestamps from the robot battery while it follows a mission. Record actual odometry distance and accumulated absolute turning. Exclude charging/service periods. State whether all robot electronics are inside the measurement boundary.
2. Fill mission_metadata.json with the real instrument, mission/map identifiers, measured distance/turning and calibration or validation split. Use raw_voltage_current.csv for the real samples; positive current means discharge.
3. Run: python3 -m research.electrical_logging --samples raw_voltage_current.csv --metadata mission_metadata.json --out integrated_mission.json
4. Put each integrated observation into electrical_measurements.csv using its existing header. Keep missions and maps disjoint between calibration and validation. The current four-coefficient model requires varied distance, duration and turning: at least 12 calibration and 6 validation observations, at least three missions per split, and a full-rank design.
5. Fill metadata.json with measured usable battery capacity in Wh and sensor details. Run: python3 -m research.calibration --csv electrical_measurements.csv --metadata metadata.json --out fitted_profile.json
6. Inspect held-out error, residuals versus time/terrain/payload, sensor uncertainty and coefficient stability before applying the profile. Independent hardware review is required. Refit only on the calibration split; evaluate changes on new held-out missions. Mechanical actuator work and simulated battery ledgers cannot replace electrical measurements.
''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--template',type=Path);p.add_argument('--samples',type=Path);p.add_argument('--metadata',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.template:template(a.template)
    elif a.samples and a.metadata and a.out:a.out.write_text(json.dumps(integrate(a.samples,a.metadata),indent=2))
    else:p.error('Use --template DIRECTORY, or --samples CSV --metadata JSON --out JSON')
