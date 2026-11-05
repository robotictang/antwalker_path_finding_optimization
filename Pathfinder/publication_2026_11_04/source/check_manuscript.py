"""Check manuscript structure, statements, minimum type sizes and provenance."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re
from lxml import etree
B=Path(__file__).resolve().parents[1]
doc=B/'IJ3C_Hexapod_Review_Draft.docx';build=json.loads((B/'qa/build_report.json').read_text())
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with ZipFile(doc) as z:
    assert z.testzip() is None
    root=etree.fromstring(z.read('word/document.xml'));text=' '.join(root.xpath('//w:t/text()',namespaces=ns))
    assert not re.search(r'\{\{[A-Z_]+\}\}',text)
    assert len(root.xpath('//w:tbl',namespaces=ns))==4
    assert len(root.xpath('//m:oMath',namespaces=ns))==2
    assert len(root.xpath('//w:drawing',namespaces=ns))==3
    assert 'TOMATO' not in text and 'Gwo-Jen' not in text
    assert all(token in text for token in ['93/96','94/96','0.690','97.52','113.32','640','pending confirmation'])
    for table in root.xpath('//w:tbl',namespaces=ns):assert table.xpath('./w:tr[1]/w:trPr/w:tblHeader',namespaces=ns)
    for section in root.xpath('//w:sectPr',namespaces=ns):
        size=section.find('w:pgSz',ns);assert abs(int(size.get('{'+ns['w']+'}w'))-11906)<3
    sizes=[int(x) for x in root.xpath('//w:sz/@w:val',namespaces=ns)]
    assert all(x>=20 for x in sizes)
    styles=etree.fromstring(z.read('word/styles.xml'))
    used=set(root.xpath('//w:pStyle/@w:val',namespaces=ns))|{'Normal'}
    for s in styles.xpath('//w:style',namespaces=ns):
        if s.get('{'+ns['w']+'}styleId') in used:
            assert all(int(v)>=20 for v in s.xpath('./w:rPr/w:sz/@w:val',namespaces=ns))
    body=text[:text.rfind('References')]
    seen=[]
    for number in re.findall(r'\[(\d+)\]',body):
        if number not in seen:seen.append(number)
    assert seen==[str(i) for i in range(1,13)],seen
assert build['abstract_words']<=250 and build['approximate_manuscript_words']<10000
assert build['reference_unchanged']
report=dict(state='passed',figures=3,tables=4,native_equations=2,references=12,
    abstract_words=build['abstract_words'],approximate_words=build['approximate_manuscript_words'],
    page_size='A4',body_columns=2,minimum_font_pt=10,author_details='Pending by user request',
    docx_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),scope='Structural/numeric document checks; visual review is recorded separately.')
(B/'qa/manuscript_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
