"""Verify unchanged screenshot embedding and preservation of preceding prose."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re
from lxml import etree
import pdfplumber
from PIL import Image
B=Path(__file__).resolve().parents[1];previous=B.parent/'publication_2026_11_04_plain_language'
p=json.loads((B/'results/screenshot_provenance.json').read_text());sha=p['sha256'];asset=B/p['copied_asset']
assert hashlib.sha256(asset.read_bytes()).hexdigest()==sha
if Path(p['source']).is_file():assert hashlib.sha256(Path(p['source']).read_bytes()).hexdigest()==sha
with ZipFile(B/'IJ3C_Manuscript.docx') as z:
 matches=[n for n in z.namelist() if n.startswith('word/media/') and hashlib.sha256(z.read(n)).hexdigest()==sha]
 assert len(matches)==1
 n={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
 root=etree.fromstring(z.read('word/document.xml'));rels=etree.fromstring(z.read('word/_rels/document.xml.rels'))
 rid=next(x.get('Id') for x in rels if x.get('Target')=='media/'+Path(matches[0]).name)
 assert root.xpath('count(//a:blip[@r:embed="'+rid+'"])',namespaces=n)==1
 assert root.xpath('count(//w:drawing)',namespaces=n)==7
old=(B/'template/preceding_manuscript.md').read_text();new=(B/'IJ3C_Manuscript.md').read_text()
old=re.sub(r'Figure (\d+)',lambda m:'Figure '+str(int(m.group(1))+1),old)
intro='Figure 1 shows the simulated robot in a road scene with colored route lines and labeled locations. The view illustrates the robot and demonstration environment. The planning results in Section 6 use the maps and task limits specified in Section 5.'
caption='Figure 1. Simulation view of the hexapod in the demonstration environment. Colored lines show displayed routes, and location labels identify points in the scene.'
addition=intro+'\n\n!['+caption+'](figures/simulation_overview.png)\n\n'+caption+'\n\n'
assert new.replace(addition,'',1)==old,'Unexpected prose change outside screenshot insertion and figure renumbering'
image_pages=[];dimensions=Image.open(asset).size
with pdfplumber.open(B/'IJ3C_Manuscript.pdf') as pdf:
 for i,page in enumerate(pdf.pages,1):
  for im in page.images:
   if im['srcsize']==dimensions:
    image_pages.append(i);assert im['x1']-im['x0']>400
    assert caption[:70] in page.extract_text()
assert image_pages==[2]
report=dict(state='passed',screenshot_sha256=sha,embedded_once_without_modification=True,pdf_page=2,full_width=True,prior_prose_preserved_except_added_description_and_figure_renumbering=True,total_figures=7)
(B/'qa/screenshot_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
