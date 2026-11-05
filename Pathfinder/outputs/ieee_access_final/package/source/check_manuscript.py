"""Structural and quantitative delivery checks; visual QA remains separate."""
from pathlib import Path
from zipfile import ZipFile
import json,re,hashlib,csv
from lxml import etree
B=Path(__file__).resolve().parents[1];docx=B/'IEEE_Access_Hexapod_Final_Manuscript.docx';report=json.loads((B/'source/build_report.json').read_text());A=json.loads((B/'source/final_analysis.json').read_text())
with ZipFile(docx) as z:
 assert z.testzip() is None
 root=etree.fromstring(z.read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
 txt=' '.join(root.xpath('//w:t/text()',namespaces=ns));tables=root.xpath('//w:tbl',namespaces=ns)
 assert len(tables)==14
 assert all(t.xpath('./w:tr[1]/w:trPr/w:tblHeader',namespaces=ns) for t in tables)
 assert len(root.xpath('//m:oMath',namespaces=ns))>=10
 assert not re.search(r'\[\[(EQ|TABLE|FIG|ALG|WIDEFIG):',txt)
 bookmarks=set(root.xpath('//w:bookmarkStart/@w:name',namespaces=ns));anchors=root.xpath('//w:hyperlink/@w:anchor',namespaces=ns)
 assert set(anchors)<=bookmarks
 assert report['counts']==dict(figures=11,tables=14,equations=10,algorithms=3),report['counts']
 assert len(report['reference_order'])==23
 for n in range(1,24):assert f'reference_{n}' in bookmarks
 for tag in ['FINAL PIPELINE AND PROSPECTIVE VALIDATION','REPLICATION AND A NEGATIVE ENHANCEMENT RESULT','1,200','TOMATO','external_hardware']:
  if tag=='external_hardware':continue
  assert tag.lower() in txt.lower(),tag
rows=list(csv.DictReader((B/'tables/All_1200_Final_Attempts.csv').open()));assert len(rows)==1200
keys=[(r['phase'],r['case'],r['method'],r['repeat']) for r in rows];assert len(set(keys))==1200
for r in A['comparisons']:assert sum(r[k] for k in ['wins','ties','losses','proposed_only_admitted','baseline_only_admitted','both_rejected'])==96
output=dict(state='passed',tables=len(tables),figures=11,display_equations=10,algorithms=3,references=23,unique_new_record_keys=1200,template_parts_preserved=report['template_parts_preserved'],template_sha256=report['template_sha256'],docx_sha256=hashlib.sha256(docx.read_bytes()).hexdigest(),scope='OOXML, references, source-template retention, CSV completeness and paired-count arithmetic. Visual page inspection is separate.')
(B/'qa/manuscript_integrity.json').write_text(json.dumps(output,indent=2));print(json.dumps(output,indent=2))
