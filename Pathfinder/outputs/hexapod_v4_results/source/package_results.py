"""Package frozen evidence without changing its paths, metrics or outcomes."""
import argparse,csv,hashlib,json,shutil,sys,zipfile
from pathlib import Path
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--project-root',type=Path,default=BASE.parents[1]);args=parser.parse_args()
ROOT=args.project_root;M=ROOT/'mujoco';OUT=M/'outputs/research';S=OUT/'advanced_study_v4'
sys.path.insert(0,str(M))
from research.run import flat_rows
from research.audit_advanced_study import PHASES
runs={p:json.loads((S/(p+'.json')).read_text()) for p in PHASES}
audit=json.loads((S/'audit.json').read_text());assert audit['state']=='passed' and audit['attempts']==1232
assert all(r['state']=='complete' for r in runs.values())
rows=[]
for phase,r in runs.items():
 cases={c['id']:c for c in r['cases']}
 for flat,raw in zip(flat_rows(r),r['records']):
  # No execution means not tested, not a failed mission. Raw success remains archived.
  flat['success']=raw['success'] if r['execute'] else None
  rows.append(dict(phase=phase,run_id=r['run_id'],split=r['study']['split'],physics_scheduled=r['execute'],physics_executed=bool(raw.get('execution')),**flat))
with (BASE/'All_1232_Attempts.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
verification=dict(verified_at_utc=datetime.now(timezone.utc).isoformat(),automated_tests=dict(count=30,status='passed',command='python3 -m unittest research.test_research research.test_reliability research.test_server research.test_v3 research.test_v4'),scientific_audit=audit,static_figures='visually reviewed',website_build='verified separate-data build and exact served HTML/snapshot hashes',browser_interaction_qa='not performed: no browser surface available',csv_semantics='success blank on planning-only rows; raw recorded flags unchanged in archived JSON')
(BASE/'Verification.json').write_text(json.dumps(verification,indent=2))
notes='''VERSION 4 EVIDENCE AND REPRODUCTION NOTES

Raw records are preserved under evidence/mujoco/outputs/research. Their source_snapshot and model_xml entries are relative to that outputs/research directory. Manifest, source_lock, locked_parameters, comparison and audit files are in its advanced_study_v4 folder. Whole-world bootstrap intervals are descriptive and do not correct for multiple comparisons.

The complete campaign contains 1,232 scheduled attempts: 128 development, 864 primary planning, 72 feature removal, 96 shorter budget, 72 physics. Planning and physics must not be pooled to inflate an independent test sample. Main primary test has 24 worlds, not 72 independent worlds.

reproduction/mujoco contains the implementation and test sources used in the working project; source_snapshots are the exact per-run scientific archives. Raw XML asset references intentionally retain the original /home/user123456/Downloads/hexapod_asset paths to preserve their recorded hashes. Meshes and model assets are included. On the original computer, run from the original mujoco workspace:

python3 -m research.audit_advanced_study
python3 -m unittest research.test_research research.test_reliability research.test_server research.test_v3 research.test_v4
python3 -m research.advanced_study

The last command resumes verified completed phases; it does not manufacture additional trials. On another machine, restore the original asset paths or explicitly relocate references in a separate copy. A relocated rerun has new source/model hashes and belongs in a new study directory. Never replace the archived XML or source files while claiming their original hashes. The audit also checks the prior v3 manifest; that manifest is included as historical context, not pooled observations.

requirements.txt and recorded versions in each phase describe dependencies. Wall-clock limits can produce different endpoints under a different workload or machine. This bundle is evidence and source code, not a self-installing virtual environment. Plot scripts additionally need matplotlib, listed in source/plot-requirements.txt. The frozen physics uses body assistance and uncalibrated nominal energy; this is not electrical hardware validation.

Dashboard authored content is in reproduction/mujoco/research_dashboard/src/content with its reviewed src/data.json snapshot. It depends on the installed Data app runtime; the delivered standalone HTML works without that runtime. No publication, sharing, or hosted site destination was changed.

All_1232_Attempts.csv leaves success blank for planning-only rows. On scheduled physics rows, false includes rejected missions and unsuccessful executions. Use physics_executed to distinguish them. Raw recorded JSON is unchanged. Every_Experiment.csv is the 72 primary world/repetition verdicts, not 864 independent maps.

SHA256SUMS.json covers the archived payload; outer Delivery_SHA256.json covers the delivered files except itself. The old version 3 Word manuscript remains separate and is not a version 4 paper.
'''
(BASE/'REPRODUCTION.txt').write_text(notes)
(BASE/'source/plot-requirements.txt').write_text('matplotlib>=3.6\nnumpy>=1.26\n')
zip_path=BASE/'Hexapod_V4_Evidence.zip';payload={}
def add_file(path,arc):
 path=Path(path)
 if path.is_file():payload[str(arc)]=path
for p in S.iterdir():
 if p.is_file():add_file(p,Path('evidence/mujoco/outputs/research/advanced_study_v4')/p.name)
for r in runs.values():
 for p in (OUT/r['source_snapshot']).rglob('*'):
  if p.is_file():add_file(p,Path('evidence/mujoco/outputs/research')/p.relative_to(OUT))
 for c in r['cases']:
  p=OUT/c['model_xml'];add_file(p,Path('evidence/mujoco/outputs/research')/c['model_xml'])
add_file(OUT/'strong_study_v3/manifest.json','evidence/mujoco/outputs/research/strong_study_v3/manifest.json')
for p in M.glob('*.py'):add_file(p,Path('reproduction/mujoco')/p.name)
for p in (M/'research').iterdir():
 if p.is_file():add_file(p,Path('reproduction/mujoco/research')/p.name)
for folder in ['research/web','models','derived_meshes','research_dashboard/src/content']:
 for p in (M/folder).rglob('*'):
  if p.is_file():add_file(p,Path('reproduction/mujoco')/p.relative_to(M))
for p in (ROOT/'meshes').rglob('*'):
 if p.is_file():add_file(p,Path('reproduction/meshes')/p.relative_to(ROOT/'meshes'))
for f in ['requirements.txt','hybrid_hexapod_multi_place.xml','research_dashboard/src/data.json','research_dashboard/AGENTS.md']:
 add_file(M/f,Path('reproduction/mujoco')/f)
for p in BASE.rglob('*'):
 if p.is_file() and p.suffix!='.zip' and p.name!='Delivery_SHA256.json':add_file(p,Path('results')/p.relative_to(BASE))
hashes={arc:hashlib.sha256(p.read_bytes()).hexdigest() for arc,p in sorted(payload.items())}
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for arc,p in sorted(payload.items()):z.write(p,arc)
 z.writestr('SHA256SUMS.json',json.dumps(hashes,indent=2))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for arc,sha in hashes.items():assert hashlib.sha256(z.read(arc)).hexdigest()==sha
DEST=Path('/home/user123456/Downloads/Hexapod_V4_Results');DEST.mkdir(exist_ok=True)
for p in BASE.iterdir():
 if p.is_file() and p.name!='Delivery_SHA256.json':shutil.copy2(p,DEST/p.name)
for sub in ['figures','source']:shutil.copytree(BASE/sub,DEST/sub,dirs_exist_ok=True)
outer={str(p.relative_to(DEST)):hashlib.sha256(p.read_bytes()).hexdigest() for p in DEST.rglob('*') if p.is_file() and p.name!='Delivery_SHA256.json'}
(DEST/'Delivery_SHA256.json').write_text(json.dumps(outer,indent=2));(BASE/'Delivery_SHA256.json').write_text(json.dumps(outer,indent=2))
print(json.dumps(dict(delivery=str(DEST),attempt_rows=len(rows),archive_payload_files=len(payload),archive_bytes=zip_path.stat().st_size,verified_hashes=len(hashes)),indent=2))
