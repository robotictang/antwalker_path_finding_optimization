"""Check final paper data/link consistency and package the review deliverables."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import csv,hashlib,json,re,shutil
from lxml import etree
from docx import Document
import pdfplumber
B=Path(__file__).resolve().parents[1];R=B.parents[1];S=R/'mujoco/outputs/research/advanced_study_v4';Q=B/'qa/delivery';dest=Path('/home/user123456/Downloads/Hexapod_IEEE_Access_Paper')
P=json.load(open(S/'v4_heldout_planning.json'));C=json.load(open(S/'comparison.json'));PH=json.load(open(S/'v4_heldout_physics.json'));build=json.load(open(B/'source/build_report.json'));D=Document(B/'IEEE_Access_Hexapod_V4_Manuscript.docx');assert len(D.tables)==9
for tab,rows,fields in [(D.tables[3],P['summary'],['admissible','mean_quality_score','mean_planning_seconds']),(D.tables[5],C['comparisons'],['wins','ties','losses']),(D.tables[8],PH['summary'],['successes','mean_task_time_s','mean_positive_work_j'])]:
 assert len(tab.rows)==len(rows)+1
 for tr,r in zip(tab.rows[1:],rows):
  c=[x.text for x in tr.cells]
  if 'mean_quality_score' in fields:assert c[1]==f"{r['admissible']}/72" and c[2]==f"{r['mean_quality_score']:.6f}" and c[3]==f"{r['mean_planning_seconds']:.4f}"
  elif 'mean_task_time_s' in fields:assert c[1]==f"{r['successes']}/{r['attempts']}" and c[2]==f"{r['mean_task_time_s']:.4f}" and c[3]==f"{r['mean_positive_work_j']:.2f}"
  else:assert list(map(int,c[1:4]))==[r[k] for k in fields]
with ZipFile(B/'IEEE_Access_Hexapod_V4_Manuscript.docx') as z:
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/package/2006/relationships','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
 root=etree.fromstring(z.read('word/document.xml'));alltext=' '.join(root.xpath('//w:t/text()',namespaces=ns));assert '[[' not in alltext and '[@' not in alltext and 'Preparation of Papers for IEEE Access' not in alltext
 anchors=root.xpath('//w:hyperlink/@w:anchor',namespaces=ns);marks=set(root.xpath('//w:bookmarkStart/@w:name',namespaces=ns));assert all(a in marks for a in anchors);assert len({x for x in marks if x.startswith('reference_')})==20
 rels=etree.fromstring(z.read('word/_rels/document.xml.rels'));links=rels.xpath('//*[local-name()="Relationship" and @TargetMode="External"]/@Target');assert all(r['url'] in links for r in build['reference_order'] if r['url'])
 assert all(root.xpath('//wp:docPr/@descr',namespaces=ns));assert root.xpath('count(//m:oMath)',namespaces=ns)>=13
 tabrefs=root.xpath('//w:pPr/w:pStyle[@w:val="TableCaption"]',namespaces=ns)
# Use the PDF emitted directly by the reviewed canonical render; no DOCX conversion/save.
shutil.copy2(Q/'IEEE_Access_Hexapod_V4_Manuscript.pdf',B/'IEEE_Access_Hexapod_V4_Manuscript.pdf')
with pdfplumber.open(B/'IEEE_Access_Hexapod_V4_Manuscript.pdf') as pdf:
 assert len(pdf.pages)==14;outside=[]
 for i,p in enumerate(pdf.pages,1):
  assert len(p.extract_text() or '')>500
  outside += [(i,c['text']) for c in p.chars if c['x0']< -1 or c['x1']>p.width+1 or c['top']< -1 or c['bottom']>p.height+1]
 assert not outside,outside[:10]
plain=json.load(open(B/'source/verified_paper_analysis.json'));assert plain['attempts']==1232
maxplan=max(r['plan']['planning_seconds'] for r in P['records']);over=sum(r['plan']['planning_seconds']>2 for r in P['records']);assert over==39 and abs(maxplan-2.0231498039793223)<1e-10
for f,sha in json.load(open(S/'source_lock.json')).items():assert hashlib.sha256((R/'mujoco'/f).read_bytes()).hexdigest()==sha
# Export complete native data tables, preserving displayed units and conditional scopes.
(B/'tables').mkdir(exist_ok=True)
for i,t in enumerate(D.tables,1):
 with (B/'tables'/f'table_{i:02d}.csv').open('w',newline='') as f:csv.writer(f).writerows([[c.text for c in r.cells] for r in t.rows])
checks=dict(state='passed_with_research_limitations',rendered_pages=14,all_pages_visually_reviewed=True,identical_reviewed_prefix_pages=[1,2,3,4,5,6],figures=7,tables=9,numbered_equations=10,algorithms=2,references=20,reference_anchors_valid=True,external_reference_targets_present=True,paper_tables_match_archived_results=True,independent_analysis='11 baseline pair counts, world averaged percentages and 5000-sample whole-world intervals recalculated directly from raw JSON',scientific_attempts=1232,primary_independent_test_worlds=24,primary_timing_over_nominal=over,primary_max_planning_seconds=maxplan,scientific_source_lock='19 files unchanged',template_preserve_only_parts=30,accessibility=json.load(open(B/'qa/accessibility_final.json')),browser_qa='unavailable; served snapshot hash verified',renderer='canonical Documents renderer with explicit /usr/bin/soffice compatibility override after bundled GLIBC failure',pending=['Author affiliation, email, biography, ORCID and declarations','Human technical and reference approval','Public data archive location','Scientific novelty and wider physical validation remain limitations'],docx_sha256=hashlib.sha256((B/'IEEE_Access_Hexapod_V4_Manuscript.docx').read_bytes()).hexdigest(),pdf_sha256=hashlib.sha256((B/'IEEE_Access_Hexapod_V4_Manuscript.pdf').read_bytes()).hexdigest())
(B/'Manuscript_Verification.json').write_text(json.dumps(checks,indent=2))
readme=B/'README_Paper_Package.txt';readme.write_text(readme.read_text().replace('verified metadata for seven DOI records','verified metadata for six DOI records'))
dest.mkdir(exist_ok=True)
for name in ['IEEE_Access_Hexapod_V4_Manuscript.docx','IEEE_Access_Hexapod_V4_Manuscript.pdf','README_Paper_Package.txt','Manuscript_Verification.json','artifact.md']:shutil.copy2(B/name,dest/name)
for name in ['figures','tables','template']:shutil.copytree(B/name,dest/name,dirs_exist_ok=True)
(dest/'source').mkdir(exist_ok=True)
for p in (B/'source').iterdir():
 if p.is_file() and p.name!='authored_working.docx':shutil.copy2(p,dest/'source'/p.name)
shutil.copytree(S,dest/'evidence/advanced_study_v4',dirs_exist_ok=True)
v4=Path('/home/user123456/Downloads/Hexapod_V4_Results');shutil.copy2(v4/'Hexapod_V4_Evidence.zip',dest/'S1_Simulation_Evidence.zip')
for name in ['All_1232_Attempts.csv','Every_Experiment.csv','Paired_Comparison.csv','Hexapod_V4_Comparison.html']:shutil.copy2(v4/name,dest/name)
assert all((dest/f).stat().st_size<40_000_000 for f in ['IEEE_Access_Hexapod_V4_Manuscript.docx','IEEE_Access_Hexapod_V4_Manuscript.pdf'])
for path in ['S1_Simulation_Evidence.zip']:
 with ZipFile(dest/path) as z:assert z.testzip() is None
hashes={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file() and p.name not in ['SHA256SUMS.json','IEEE_Access_V4_Paper_Package.zip']}
(dest/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2));zpath=dest/'IEEE_Access_V4_Paper_Package.zip'
with ZipFile(zpath,'w',ZIP_DEFLATED,compresslevel=6) as z:
 for p in dest.rglob('*'):
  if p.is_file() and p!=zpath:z.write(p,str(p.relative_to(dest)))
with ZipFile(zpath) as z:
 assert z.testzip() is None
 for name,sha in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
print(json.dumps(dict(delivery=str(dest),pages=14,files_hashed=len(hashes),zip_bytes=zpath.stat().st_size,docx_bytes=(dest/'IEEE_Access_Hexapod_V4_Manuscript.docx').stat().st_size,pdf_bytes=(dest/'IEEE_Access_Hexapod_V4_Manuscript.pdf').stat().st_size,validation='passed with stated research limitations'),indent=2))
