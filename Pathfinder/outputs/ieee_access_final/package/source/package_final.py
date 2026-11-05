"""Package the reviewed final manuscript and unchanged simulation evidence."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,xml.etree.ElementTree as ET
from PIL import Image,ImageOps,ImageDraw,ImageFont
import pdfplumber
B=Path(__file__).resolve().parents[1];ROOT=B.parents[1];M=ROOT/'mujoco';S=M/'outputs/research/final_validation_v6'
DEST=Path('/home/user123456/Downloads/Hexapod_Final_V6');STAGE=B/'package';STAGE.mkdir(exist_ok=True)
A=json.loads((B/'source/final_analysis.json').read_text());audit=json.loads((S/'audit.json').read_text());assert audit['state']=='passed'
gate=json.loads((B/'qa/review_gate.json').read_text());assert gate['all_manuscript_pages_visually_reviewed']
DOCX=B/'IEEE_Access_Hexapod_Final_Manuscript.docx';PDF=B/'qa/final4/IEEE_Access_Hexapod_Final_Manuscript.pdf'
with pdfplumber.open(PDF) as p:pages=len(p.pages);extracted='\n'.join(x.extract_text() or '' for x in p.pages)
assert len(gate['page_numbers_reviewed'])==pages
assert 'FINAL PIPELINE' in extracted and 'TOMATO' in extracted and '1,200' in extracted
with ZipFile(DOCX) as z:
 assert z.testzip() is None
 text=z.read('word/document.xml').decode();assert not any(x in text for x in ['[[TABLE:','[[FIG:','[[ALG:'])
for p in [DOCX,PDF]:shutil.copy2(p,STAGE/p.name)
for name in ['source','figures','tables','template','electrical_validation']:
 dest=STAGE/name;dest.mkdir(exist_ok=True)
 for p in (B/name).iterdir():
  if p.is_file() and p.name!='authored_working.docx':shutil.copy2(p,dest/p.name)
shutil.copy2(B/'artifact.md',STAGE/'artifact.md')
qa=STAGE/'verification';qa.mkdir(exist_ok=True)
for name in ['review_gate.json','website_verification.json','accessibility.json','manuscript_integrity.json','portable_smoke.json','launch_verification.json']:
 shutil.copy2(B/'qa'/name,qa/name)
for name in ['final_v6_tests.log','final_v6_delivery_tests.log','final_validation_v6.log','final_v6_completed_reload.log']:shutil.copy2(M/'outputs'/name,qa/name)
evidence=STAGE/'evidence';evidence.mkdir(exist_ok=True)
# Earlier evidence is copied byte-for-byte; the full detailed S2 paper is retained.
prior=ROOT/'outputs/ieee_access_validation/package'
for name in ['S1_Unchanged_V4_Evidence.zip','advanced_study_v4','validation_extension_v5','S2_archived_sources','S2_archived_models']:
 src=prior/'evidence'/name;dest=evidence/name
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 else:shutil.copy2(src,dest)
supp=STAGE/'prior_full_report';supp.mkdir(exist_ok=True)
for name in ['IEEE_Access_Hexapod_Validated_Manuscript.docx','IEEE_Access_Hexapod_Validated_Manuscript.pdf']:shutil.copy2(prior/name,supp/name)
shutil.copytree(S,evidence/'final_validation_v6',dirs_exist_ok=True)
for phase in S.glob('v6_*.json'):
 r=json.loads(phase.read_text())
 if 'records' not in r:continue
 shutil.copytree(M/'outputs/research'/r['source_snapshot'],evidence/'S3_archived_sources'/r['source_snapshot'],dirs_exist_ok=True)
 for c in r['cases']:
  src=M/'outputs/research'/c['model_xml'];dest=evidence/'S3_archived_models'/c['model_xml'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
shutil.copy2(M/'outputs/research/tracking_v6_regression.json',evidence/'Development_Tracking_Regression.json')
shutil.copy2(S/'audit.json',STAGE/'Final_Audit.json')
# Separate portable assets; authoritative original XML remains in archives.
rep=STAGE/'reproduction';rm=rep/'mujoco';rm.mkdir(parents=True,exist_ok=True)
for p in M.glob('*.py'):shutil.copy2(p,rm/p.name)
(rm/'research').mkdir(exist_ok=True)
for p in (M/'research').iterdir():
 if p.is_file() and p.suffix in ('.py','.json','.md','.txt'):shutil.copy2(p,rm/'research'/p.name)
shutil.copytree(M/'research/web',rm/'research/web',dirs_exist_ok=True)
for name in ['textures','models','derived_meshes','research_vendor']:shutil.copytree(M/name,rm/name,dirs_exist_ok=True)
shutil.copytree(ROOT/'meshes',rep/'meshes',dirs_exist_ok=True)
for name in ['dist','src/content']:
 shutil.copytree(M/'research_dashboard'/name,rm/'research_dashboard'/name,dirs_exist_ok=True)
for name in ['AGENTS.md','src/data.json']:shutil.copy2(M/'research_dashboard'/name,rm/'research_dashboard'/name)
src=M/'hybrid_hexapod_multi_place.xml';tree=ET.parse(src);relocations=[]
for item in tree.getroot().iter():
 value=item.get('file')
 if value and Path(value).is_absolute():
  path=Path(value)
  if path.is_relative_to(M):replacement=str(path.relative_to(M))
  elif path.is_relative_to(ROOT):replacement='../'+str(path.relative_to(ROOT))
  else:raise RuntimeError('Unresolved asset '+value)
  item.set('file',replacement);relocations.append(dict(original=value,relocated=replacement))
tree.write(rm/src.name,encoding='unicode')
(rep/'Relocation_Log.json').write_text(json.dumps(dict(scope='Asset file locations and XML serialization change only in this portable copy. Original archived XML, Python sources and hashes remain authoritative.',changes=relocations,original_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),relocated_sha256=hashlib.sha256((rm/src.name).read_bytes()).hexdigest()),indent=2))
for directory in ['advanced_study_v4','validation_extension_v5']:
 target=rm/'outputs/research'/directory;target.mkdir(parents=True,exist_ok=True)
 for name in ['manifest.json','source_lock.json']:shutil.copy2(M/'outputs/research'/directory/name,target/name)
(rep/'requirements-pinned.txt').write_text('mujoco==3.9.0\nnumpy==2.2.6\nscipy==1.15.3\nompl==2.0.1\nPillow>=10\n')
(rep/'REPRODUCE.txt').write_text('''TESTED SCIENTIFIC RUNTIME
Linux x86_64, Python 3.10.12, MuJoCo 3.9.0, NumPy 2.2.6, SciPy 1.15.3, OMPL 2.0.1. Native isolation requires fork. research_vendor includes the tested CPython 3.10 Linux wheel files and its licenses; another platform needs a compatible installation and a new native provenance record. Use an isolated environment.

From reproduction/mujoco:
python3 -m unittest research.test_v6 research.test_v5 research.test_v4 research.test_v3 research.test_research research.test_reliability research.test_server
python3 -m research.final_study --directory outputs/research/reproduction_v6

This creates a new complete campaign. Do not point it at the frozen evidence directory. Wall-clock termination and workload mean route coordinates, profile choices and runtime can vary on another run or computer. The preserved records, not bit-identical fresh outcomes, support this manuscript. Original source/model snapshots are archived separately; the portable model has documented path-only asset edits. Previous manifest and source-lock files are included because final_study checks prior world hashes and the scientific source list.

MANUSCRIPT
Install python-docx, lxml, NumPy and Matplotlib in an authoring environment. From package root run source/analyze_final.py, then source/build_manuscript.py. They read the included evidence directories and original official template. source/update_manuscript.py is the preparation record with task-host fallback paths; manuscript.md and build_manuscript.py are the portable authored source. render_paper.py is a task-host rendering wrapper; use a compatible Word/PDF renderer elsewhere.

COMPARISON
Double-click Comparison_Offline.html for the portable primary-data dashboard. Or start python3 -m research.server --port 8771 from reproduction/mujoco and open http://127.0.0.1:8771/comparison/. The compiled dashboard is included. Authoring source is provided under research_dashboard/src/content; rebuilding requires the installed Data plugin runtime. Original frozen run folders remain under evidence and are not automatically populated into the portable server run selector.

ELECTRICAL DATA
Read electrical_validation/MEASUREMENT_PROTOCOL.md. Templates contain no measurements. Real voltage/current and external measured mission data are required. No real electrical profile or hardware result is supplied.
''')
# Requested quick preview is distinct from internal rendered Word page images.
canvas=Image.new('RGB',(1800,1450),'white');draw=ImageDraw.Draw(canvas);fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f=lambda n:ImageFont.truetype(fontpath,n);fb=lambda n:ImageFont.truetype(bold,n)
p=next(x for x in A['primary'] if x['method']=='proposed_v4');safe=next(x for x in A['physics'] if x['phase']=='v6_physics_safe' and x['method']=='proposed_v4');legacy=next(x for x in A['physics'] if x['phase']=='v6_physics_legacy' and x['method']=='proposed_v4')
draw.text((55,30),'Hexapod final research package',font=fb(42),fill='#171717')
draw.text((55,95),'1,200 new records | 48 fresh primary worlds | Six planner configurations',font=f(26),fill='#333333')
draw.text((55,141),f"Proposal: {p['admitted']}/96 admitted plans. Exact-route safe tracking: {safe['successful']}/12 successes; legacy: {legacy['successful']}/12.",font=f(24),fill='#333333')
draw.text((55,183),'Conditional simulation evidence. Ties and losses retained. Hardware and electrical validation pending.',font=f(23),fill='#333333')
for name,box in [('final1',(40,250,1760,770)),('final3',(40,845,1760,1390))]:
 im=ImageOps.contain(Image.open(B/'figures'/(name+'.png')).convert('RGB'),(box[2]-box[0],box[3]-box[1]));canvas.paste(im,(box[0]+(box[2]-box[0]-im.width)//2,box[1]))
canvas.save(STAGE/'Research_Preview.png')
shutil.copy2(M/'research_dashboard/.data-app-offline/exports/Hexapod_Final_Comparison.html',STAGE/'Comparison_Offline.html')
readme=f'''HEXAPOD FINAL SIMULATION PACKAGE

START HERE
1. IEEE_Access_Hexapod_Final_Manuscript.docx: full editable {pages}-page article.
2. Matching PDF: fixed-layout reading copy.
3. Research_Preview.png: quick result comparison.
4. Comparison_Offline.html: double-click to inspect all 576 fresh primary planning records without a local server.
5. tables/All_1200_Final_Attempts.csv: every new scheduled record, including rejected plans and failed missions.

WHAT WAS IMPLEMENTED
Shared safe follower with alignment hysteresis, checked waypoint connectors, braking and bounded checked recovery; actual OMPL 2.0.1 RRT*, RRT* with a common candidate-pool incumbent, and RRTConnect plus shared final polishing; two-profile development selection per method; fresh standard/shifted worlds; weight and budget sensitivity; exact saved-primary-route controller replays; independent audit; improved missing-value explanations; direct local download buttons; full journal revision and real electrical-data ingestion/calibration templates.

WHAT THE RESULTS MEAN
The proposal admits {p['admitted']}/96 primary attempts. See the article for every control and the conditional paired score results; it does not win every experiment or every metric. Revised safe tracking yields {safe['successful']}/12 scheduled proposal successes versus {legacy['successful']}/12 legacy successes on the exact same saved routes. V6 names the mission pipeline and final protocol, while the route optimizer remains V4. The earlier V5 adaptive planner returned identical routes to V4 and was not promoted as a better algorithm.

EVIDENCE
S1: unchanged original 1,232 attempts, 24 test worlds. S2: separate 800 attempts, 48 new test worlds. S3: final 1,200 scheduled records, 48 new test worlds, 12 phases. Total 3,232 records are not 3,232 independent maps. Each primary method in S3 has two repeats on the same 48 worlds. Sensitivity and physics replays reuse subsets. SHA256SUMS.json hashes every package payload. The full earlier 18-page report remains in prior_full_report.

WEBSITE ON THE ORIGINAL COMPUTER
http://127.0.0.1:8771/ — experiment console.
http://127.0.0.1:8771/comparison/ — side-by-side charts.
Choose “Load completed final comparison” to restore the final primary dataset. Saved phase links distinguish planning, weights, budgets and assisted execution. Use “Use selected run in charts” after selecting another saved phase. Final DOCX/PDF/ZIP download links appear in the console. This is a local service, not a public website. The offline HTML is the portable alternative.

REMAINING AUTHOR AND SCIENTIFIC WORK
The package is finalized for its present simulation scope and supervisor review, not guaranteed journal acceptance. Author full identity, institution, email, biography, ORCID, funding, declarations and public evidence archive need confirmation. Review the contribution and references with your supervisor. Simulation still uses prescribed body assistance and gravity compensation. Terrain exposure is a proxy and battery use is a nominal ledger. No real battery reading, unassisted locomotion or physical robot result was obtained. Empty electrical templates are a workflow, not completed hardware validation. Broader native heading-state and unrestricted continuous swarm controls remain useful future comparisons. No paper has been submitted or published.

VERIFICATION
All manuscript pages and scientific figures were visually reviewed. Fifty automated software checks passed. The final 1,200-record audit passed. Dashboard build, raw-data row reconciliation and loopback HTTP delivery were checked. No enabled browser surface was available; browser filter/theme/export interactions were not visually certified.
'''
(STAGE/'READ_ME_FIRST.txt').write_text(readme)
verification=dict(status='final current-scope simulation package for supervisor review',pages=pages,original_attempts=1232,replication_attempts=800,final_records=1200,final_primary_worlds=48,final_audit=audit,software_tests=50,manuscript_counts=json.loads((B/'source/build_report.json').read_text())['counts'],all_manuscript_pages_visually_reviewed=True,browser_interactive_visual_verification='Unavailable; no enabled browser surfaces',hardware_electrical_validation='Pending real external measurements')
(STAGE/'Final_Verification.json').write_text(json.dumps(verification,indent=2))
for cache in sorted(STAGE.rglob('__pycache__'),key=lambda p:len(p.parts),reverse=True):shutil.rmtree(cache)
for p in STAGE.rglob('*.pyc'):p.unlink()
hashes={str(p.relative_to(STAGE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
(STAGE/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
archive=B/'Hexapod_Final_V6_Package.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(STAGE))
with ZipFile(archive) as z:
 assert z.testzip() is None
 for name,digest in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
DEST.mkdir(exist_ok=True)
for name in [DOCX.name,PDF.name,'Research_Preview.png','Comparison_Offline.html','READ_ME_FIRST.txt','Final_Verification.json']:shutil.copy2(STAGE/name,DEST/name)
shutil.copy2(B/'tables/All_1200_Final_Attempts.csv',DEST/'All_1200_Final_Attempts.csv');shutil.copy2(archive,DEST/archive.name)
print(json.dumps(dict(delivery=str(DEST),pages=pages,hashed_payload_files=len(hashes),zip_bytes=archive.stat().st_size),indent=2))
