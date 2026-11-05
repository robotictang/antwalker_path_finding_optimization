"""Replace the short delivery report and refresh the evidence ZIP without modifying experiments."""
import hashlib,json,os,shutil,zipfile
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from pypdf import PdfReader
BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];DELIVERY=Path('/home/user123456/Downloads/Hexapod_V3_Upgrade');ARCHIVE=DELIVERY/'Archive';ARCHIVE.mkdir(exist_ok=True)
report=BASE/'Hexapod_V3_Upgrade_Report.docx';d=Document(report);render=BASE/'qa/delivery_final';pdf=PdfReader(render/'Hexapod_V3_Upgrade_Report.pdf');assert len(pdf.pages)==28
texts=[' '.join(p.extract_text().split()) for p in pdf.pages]
for e in json.loads((BASE/'source/section_pages.json').read_text()):
 hits=[i+1 for i,t in enumerate(texts) if i>1 and e['title'] in t];assert hits[0]==e['page']+1
names={n.get(qn('w:name')) for n in d.element.iter(qn('w:bookmarkStart'))}
anchors=[n.get(qn('w:anchor')) for n in d.element.iter(qn('w:hyperlink')) if n.get(qn('w:anchor'))];assert len(anchors)==27 and all(x in names for x in anchors)
assert len(d.tables)==17 and len(list(d.element.iter(qn('m:oMath'))))==9
external=[x for x in d.part.rels.values() if x.reltype.endswith('/hyperlink') and x.is_external];assert len(external)==15
A=json.loads((BASE/'source/verified_analysis.json').read_text());evidence=ROOT/'mujoco/outputs/research/strong_study_v3'
for name,digest in A['evidence_sha256'].items():assert hashlib.sha256((evidence/name).read_bytes()).hexdigest()==digest
qa=dict(pages=28,all_pages_visually_inspected=True,contents_entries_verified=27,internal_links_verified=27,external_reference_links=15,tables=17,figures=11,native_equations=9,source_evidence_unchanged=True,docx_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),review_directory=str(render),scope='Full document render and evidence consistency. Does not certify hardware validity or journal acceptance.')
(BASE/'source/qa_validation.json').write_text(json.dumps(qa,indent=2))
old=DELIVERY/'Hexapod_V3_Upgrade_Report.docx';archived=ARCHIVE/'Hexapod_V3_Short_Supplement_Original.docx'
if not archived.exists():shutil.copy2(old,archived)
readme=DELIVERY/'START_HERE.txt'
if not (ARCHIVE/'START_HERE_Before_Full_Report.txt').exists():shutil.copy2(readme,ARCHIVE/'START_HERE_Before_Full_Report.txt')
shutil.copy2(report,old)
readme.write_text('''HEXAPOD VERSION 3 COMPLETE WORD REPORT\n\nOpen Hexapod_V3_Upgrade_Report.docx. It is now the complete 28-page report, replacing the short four-page supplement. Close and reopen an already-open Word copy to see the update.\n\nThe report contains a linked contents page, 11 figures, 17 tables, 9 editable equations and 15 references with links. It explains robot simulation, multiobjective optimization, A*, PSO, ACO, the proposed method, parameters, the 684-attempt protocol, actual results, prediction errors, calibration, limitations and publication steps.\n\nQuick reading: page 2 contents; pages 7-12 concepts and algorithms; pages 15-22 results and limitations; page 26 exact experiment settings; page 28 simple supervisor explanation. All contents entries and 28 rendered pages were checked.\n\nThe experimental data has not been changed to create better-looking comparisons. PSO and ACO still mostly tie the proposal. The six assisted-physics test worlds do not establish a physical-performance advantage. Real electrical and physical robot validation remain outstanding. The complete report is not a guaranteed journal acceptance or a publisher-approved submission.\n\nOpen Hexapod_V3_Comparison.html in a browser for the frozen planning dashboard without the local server. It includes all 432 primary planning attempts, and cannot run new experiments.\nLive experiment console on this computer: http://127.0.0.1:8771/?run=20261028T065751941702Z\nLive comparison: http://127.0.0.1:8771/comparison/\n\nThe Calibration_Template folder is empty and requires REAL sensor measurements. Experiment_Guide.txt provides additional commands. The original short supplement is preserved in Archive. The older journal manuscript in Downloads/Hexapod_Journal_Package describes version 1; use this full version 3 report for the current methods and evidence.\n\nThe ZIP contains the full report, figures, source analysis, unchanged frozen evidence, code snapshots and offline comparison. Report generation scripts reuse formatting helpers from the earlier local project; they are intended to run from the existing hexapod_asset workspace.\n''')
zip_path=DELIVERY/'Hexapod_V3_Evidence_and_Updates.zip';temp=zip_path.with_suffix('.tmp');files={}
with zipfile.ZipFile(zip_path) as src:
 for name in src.namelist():
  if name=='SHA256SUMS.json':continue
  if name in ['Hexapod_V3_Upgrade_Report.docx','START_HERE.txt']:continue
  if name.startswith('report/'):files['archive/short_report_source/'+name[len('report/'):]]=src.read(name)
  else:files[name]=src.read(name)
files['Hexapod_V3_Upgrade_Report.docx']=report.read_bytes();files['START_HERE.txt']=readme.read_bytes();files['Archive/Hexapod_V3_Short_Supplement_Original.docx']=archived.read_bytes()
for path in (BASE/'source').glob('*'):
 if path.is_file():files['report/source/'+path.name]=path.read_bytes()
for path in (BASE/'figures').glob('*.png'):files['report/figures/'+path.name]=path.read_bytes()
files['report/report_text.md']=(BASE/'report_text.md').read_bytes()
sha={name:hashlib.sha256(body).hexdigest() for name,body in sorted(files.items())}
with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as dest:
 for name,body in sorted(files.items()):dest.writestr(name,body)
 dest.writestr('SHA256SUMS.json',json.dumps(sha,indent=2))
os.replace(temp,zip_path)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for name,digest in sha.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
assert hashlib.sha256(old.read_bytes()).hexdigest()==qa['docx_sha256']
older=Path('/home/user123456/Downloads/Hexapod_Journal_Package/VERSION_3_UPDATE_READ_FIRST.txt')
older.write_text('The manuscript in this folder describes version 1. The complete 28-page version 3 report is Downloads/Hexapod_V3_Upgrade/Hexapod_V3_Upgrade_Report.docx. It includes the updated methods, evidence, references and practical guidance. Review and adapt the current report before any journal submission. Original version 1 files remain preserved.\n')
print(json.dumps(qa,indent=2));print('Delivered',old,old.stat().st_size,'bytes');print('Evidence ZIP',len(files)+1,'files',zip_path.stat().st_size,'bytes')
