"""Package reviewed manuscript, frozen evidence and an explicit relocation copy."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,shutil,xml.etree.ElementTree as ET
from PIL import Image,ImageOps,ImageDraw,ImageFont
import pdfplumber
B=Path(__file__).resolve().parents[1];ROOT=B.parents[1];M=ROOT/'mujoco';S=M/'outputs/research/validation_extension_v5'
DEST=Path('/home/user123456/Downloads/Hexapod_Validated_Review');STAGE=B/'package';STAGE.mkdir(exist_ok=True)
A=json.loads((B/'source/extension_analysis.json').read_text());audit=json.loads((S/'audit.json').read_text());assert audit['state']=='passed'
DOCX=B/'IEEE_Access_Hexapod_Validated_Manuscript.docx';PDF=B/'qa/final2/IEEE_Access_Hexapod_Validated_Manuscript.pdf'
assert DOCX.exists() and PDF.exists()
with pdfplumber.open(PDF) as p:
 pages=len(p.pages);extracted='\n'.join(x.extract_text() or '' for x in p.pages)
assert 'PROSPECTIVE VALIDATION' in extracted and 'TOMATO' in extracted and '800' in extracted
with ZipFile(DOCX) as z:
 assert z.testzip() is None
 text=z.read('word/document.xml').decode()
 assert '[[TABLE:' not in text and '[[FIG:' not in text and '[[ALG:' not in text
for p in [DOCX,PDF]:shutil.copy2(p,STAGE/p.name)
for name in ['source','figures','tables','template']:
 dest=STAGE/name;dest.mkdir(exist_ok=True)
 for p in (B/name).iterdir():
  if p.is_file() and p.name!='authored_working.docx':shutil.copy2(p,dest/p.name)
shutil.copy2(B/'artifact.md',STAGE/'artifact.md')
evidence=STAGE/'evidence';evidence.mkdir(exist_ok=True)
shutil.copy2(Path('/home/user123456/Downloads/Hexapod_V4_Results/Hexapod_V4_Evidence.zip'),evidence/'S1_Unchanged_V4_Evidence.zip')
shutil.copytree(M/'outputs/research/advanced_study_v4',evidence/'advanced_study_v4',dirs_exist_ok=True)
shutil.copy2(B.parent/'ieee_access_v4/source/analyze_and_plot.py',STAGE/'source/analyze_original_v4.py')
new=evidence/'validation_extension_v5';shutil.copytree(S,new,dirs_exist_ok=True)
for phase in S.glob('v5_*.json'):
 r=json.loads(phase.read_text())
 if 'records' not in r:continue
 shutil.copytree(M/'outputs/research'/r['source_snapshot'],evidence/'S2_archived_sources'/r['run_id'],dirs_exist_ok=True)
 for c in r['cases']:
  src=M/'outputs/research'/c['model_xml'];dest=evidence/'S2_archived_models'/r['run_id']/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
shutil.copy2(S/'audit.json',STAGE/'Extension_Audit.json')
# This copy changes asset locations only. Original snapshot bytes remain above.
rep=STAGE/'reproduction';rm=rep/'mujoco';rm.mkdir(parents=True,exist_ok=True)
for p in M.glob('*.py'):shutil.copy2(p,rm/p.name)
(rm/'research').mkdir(exist_ok=True)
for p in (M/'research').iterdir():
 if p.is_file() and p.suffix in ('.py','.json','.md','.txt'):shutil.copy2(p,rm/'research'/p.name)
for name in ['textures','models','derived_meshes']:shutil.copytree(M/name,rm/name,dirs_exist_ok=True)
shutil.copytree(ROOT/'meshes',rep/'meshes',dirs_exist_ok=True)
src=M/'hybrid_hexapod_multi_place.xml';tree=ET.parse(src);relocations=[]
for item in tree.getroot().iter():
 value=item.get('file')
 if value and Path(value).is_absolute():
  path=Path(value)
  if path.is_relative_to(M):replacement=str(path.relative_to(M))
  elif path.is_relative_to(ROOT):replacement='../'+str(path.relative_to(ROOT))
  else:raise RuntimeError('Unresolved external asset '+value)
  item.set('file',replacement);relocations.append(dict(original=value,relocated=replacement))
tree.write(rm/src.name,encoding='unicode')
(rep/'Relocation_Log.json').write_text(json.dumps(dict(scope='Only XML serialization and asset file locations differ; scientific Python sources copied unchanged. Archived original XML and hashes remain authoritative.',changes=relocations,original_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),relocated_sha256=hashlib.sha256((rm/src.name).read_bytes()).hexdigest()),indent=2))
old=rm/'outputs/research/advanced_study_v4';old.mkdir(parents=True,exist_ok=True)
for name in ['manifest.json','source_lock.json']:shutil.copy2(M/'outputs/research/advanced_study_v4'/name,old/name)
(rep/'requirements-pinned.txt').write_text('mujoco==3.9.0\nnumpy==2.2.6\nscipy==1.15.3\nPillow>=10\n')
(rep/'REPRODUCE.txt').write_text('Use Python 3.10 or a compatible supported version in an isolated environment. Install requirements-pinned.txt. From reproduction/mujoco run:\npython3 -m research.extension_study --directory outputs/research/reproduction_v5\n\nThis writes a new campaign. It does not overwrite archived results. Fixed wall-clock budgets mean routes and selected profiles can vary on different machines. The relocation log distinguishes asset-path edits from unchanged archived scientific sources. See source/analysis_plan.json for analysis rules. To reproduce manuscript analysis, install NumPy and Matplotlib and run source/analyze_extension.py; it reads evidence/validation_extension_v5. Run source/analyze_original_v4.py to recompute the original study analysis. To rebuild the Word manuscript, install python-docx and lxml and run source/build_manuscript.py. The retained official Word template is included. render_paper.py is a task-host QA wrapper with local runtime paths; use a compatible Word/PDF renderer on another machine.\n')
# A deliberate visual preview requested by the user, not a QA contact sheet.
canvas=Image.new('RGB',(1800,1510),'white');draw=ImageDraw.Draw(canvas)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
f=lambda n:ImageFont.truetype(fontpath,n);fb=lambda n:ImageFont.truetype(bold,n)
draw.text((60,35),'Hexapod research: validation preview',font=fb(43),fill='#171717')
draw.text((60,102),'800 new attempts | 48 fresh test worlds | Original V4 evidence preserved',font=f(27),fill='#333333')
draw.text((60,153),'V5 tied V4 on all saved routes. V4 remains the recommended configuration.',font=f(25),fill='#333333')
draw.text((60,190),'Mean gains versus polished controls are about 1.4%; median gain is zero.',font=f(24),fill='#333333')
for name,box in [('ext1',(45,250,890,850)),('ext4',(930,250,1760,850)),('ext3',(45,950,1755,1450))]:
 im=Image.open(B/'figures'/(name+'.png')).convert('RGB');im=ImageOps.contain(im,(box[2]-box[0],box[3]-box[1]));canvas.paste(im,(box[0]+(box[2]-box[0]-im.width)//2,box[1]))
canvas.save(STAGE/'Research_Preview.png')
offline=M/'research_dashboard/.data-app-offline/exports/Hexapod_Validation_Comparison.html'
assert offline.exists();shutil.copy2(offline,STAGE/'Comparison_Offline.html')
readme=f'''HEXAPOD SUPERVISOR REVIEW - 29 OCTOBER 2026

Open these first:
1. Research_Preview.png: quick visual summary.
2. IEEE_Access_Hexapod_Validated_Manuscript.pdf: full {pages}-page paper.
3. The matching .docx: editable manuscript using the official IEEE Access template.
4. Comparison_Offline.html: double-click to inspect fresh primary results without the local server. Choose PSO + polishing or ACO + polishing as baseline. Choosing V4 will correctly show ties with V5.

Local website: http://127.0.0.1:8771/comparison/
Experiment console: http://127.0.0.1:8771/
Use "Load completed V5 comparison" for the extension. Use "Load preserved V4 comparison" for the original campaign. Saved phase links distinguish physics, planning, candidate caps and budget tests.

WHAT CHANGED
Added 800 scheduled attempts across nine phases, 8 fresh development worlds and 48 fresh primary test worlds. Each competitive method received two development profiles. Parameters and sources were frozen before test outcomes. Feature-removal controls, shorter budgets, an 80-route-candidate ceiling, all-metric-call counters and assistance sensitivity were added.

MAIN FINDING
V4 and V5 each admit 94/96 fresh primary attempts. Polished PSO and ACO each admit 92/96. V4 and V5 return identical saved route coordinates in all 96 matched attempts; V5 takes more planner time on average. V4 therefore remains recommended. Paired mean gains over polished controls are about 1.42% and 1.41%, with world-level uncertainty in the paper. Median world improvement is zero; one 41.1% improvement has a large influence on the mean. Physics failures are retained; planning admission does not guarantee mission completion. Exact results and diagnostics are in tables and source/extension_analysis.json.

EVIDENCE AND REPRODUCTION
S1 retains the original 1,232-attempt evidence ZIP unchanged. S2 contains the 800-attempt campaign, original source snapshots and original model XML. A separate reproduction copy includes assets with documented path-only relocation. SHA256SUMS.json inventories package payloads. Repeated seeds and secondary phases do not create additional independent worlds. Audits check internal provenance and arithmetic, not physical realism.

REVIEW STATUS: SHARE WITH CAVEATS
Read the limitations before submission. Dynamic execution can fail despite planning admission. Assistance blending is not unassisted locomotion; gravity compensation remains active. Battery coefficients are nominal and mechanical work is not electrical consumption. No physical robot or real battery measurement was performed. Broader external planner implementations and out-of-distribution maps remain future work.

Author shown as Tomato. Affiliation, corresponding email, biography, funding and declarations need author confirmation. Public repository/DOI has not been assigned. Final technical review, reference checks and novelty assessment remain for the author and supervisor. The AI-assistance disclosure is retained. No paper has been submitted or published.

VERIFICATION LIMIT
All final manuscript pages and scientific figures were visually reviewed. The dashboard was built and its served snapshot/HTTP delivery verified. No browser surface was available for interactive visual testing; browser-only filter, theme and export interactions have not been visually certified.
'''
(STAGE/'READ_ME_FIRST.txt').write_text(readme)
verification=dict(status='share with caveats',original_attempts=1232,extension_attempts=800,fresh_test_worlds=48,pages=pages,extension_audit=audit,
  manuscript_counts=json.loads((B/'source/build_report.json').read_text())['counts'],v4_v5_exact_coordinate_pairs=A['v4_v5_exact_coordinate_pairs'],
  browser_interactive_verification='Unavailable: no enabled browser surfaces',all_manuscript_pages_visually_reviewed=True)
(STAGE/'Review_Verification.json').write_text(json.dumps(verification,indent=2))
for cache in sorted(STAGE.rglob('__pycache__'),key=lambda p:len(p.parts),reverse=True):shutil.rmtree(cache)
hashes={str(p.relative_to(STAGE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(STAGE.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.json'}
(STAGE/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2))
archive=B/'Hexapod_Validated_Review_Package.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for p in sorted(STAGE.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(STAGE))
with ZipFile(archive) as z:assert z.testzip() is None
DEST.mkdir(exist_ok=True)
for name in [DOCX.name,PDF.name,'Research_Preview.png','Comparison_Offline.html','READ_ME_FIRST.txt','Review_Verification.json']:
 shutil.copy2(STAGE/name,DEST/name)
shutil.copy2(B/'tables/All_800_Extension_Attempts.csv',DEST/'All_800_Extension_Attempts.csv');shutil.copy2(archive,DEST/archive.name)
print(json.dumps(dict(delivery=str(DEST),pages=pages,hashed_payload_files=len(hashes),zip_bytes=archive.stat().st_size),indent=2))
