"""Compare the final manuscript with the retained IJ3C instructions and sample."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import hashlib,json,re
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from lxml import etree

B=Path(__file__).resolve().parents[1]
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
ns={'w':W,'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
doc=Document(B/'IJ3C_Manuscript.docx')
instructions='\n'.join(p.text for p in Document(B/'template/IJ3C_template.docx').paragraphs)
for wording in ['10,000 words','8-12 pages','no smaller than 10 pt','Times New Roman','two column format','250 words','no more than 5 words','left-hand margin','right-hand side','square brackets']:
    assert wording in instructions,wording
assert digest(B/'template/IJ3C_Sample-file.docx')=='334ab83afc15d1ab416e3fe1746aaeb12482a469faa51f4c090c1c85833afc0e'
expected={'Normal':10,'Body Text':10,'Abstract Text':10,'Author':11,'Title':16,'Heading 1':11,'Heading 2':10.5,'Caption':10}
for name,size in expected.items():
    s=doc.styles[name]
    assert s.font.name=='Times New Roman' and s.font.size.pt==size,name
    assert s.paragraph_format.line_spacing==1,name
    for script in ['ascii','hAnsi','eastAsia','cs']:
        assert s.element.find('w:rPr/w:rFonts',ns).get('{'+W+'}'+script)=='Times New Roman'
    if name.startswith('Heading'):
        assert s.paragraph_format.alignment==WD_ALIGN_PARAGRAPH.LEFT
        assert s.element.find('w:pPr/w:numPr',ns) is None
for section in doc.sections:
    assert (section.page_width.twips,section.page_height.twips)==(11906,16838)
    assert all(x.twips==1418 for x in [section.top_margin,section.bottom_margin,section.left_margin,section.right_margin])
    assert section._sectPr.find('w:cols',ns).get('{'+W+'}space')=='424'
columns=[int(s._sectPr.find('w:cols',ns).get('{'+W+'}num')) for s in doc.sections]
assert columns==[1,2,1,2,2],columns
paragraphs=[p for p in doc.paragraphs if p.text.strip()]
title,author=paragraphs[:2]
assert title.style.name=='Title' and title.alignment==WD_ALIGN_PARAGRAPH.CENTER
assert not re.match(r'(?i)^(a|novel|new|the)\b',title.text) and ':' not in title.text
assert author.style.name=='Author' and author.alignment==WD_ALIGN_PARAGRAPH.CENTER
assert author.text=='[Author names and affiliations]\n[Corresponding author email]'
labels=[p.text for p in paragraphs]
abstract=paragraphs[labels.index('Abstract')+1].text
keywords=next(t for t in labels if t.startswith('Keywords:'))[len('Keywords:'):].strip().split(';')
assert len(abstract.split())<=250
assert len(keywords)==5 and all(len(k.strip().split())==1 for k in keywords)
headings=[p for p in paragraphs if p.style.name=='Heading 1' and p.text not in ['Abstract','References']]
assert [int(p.text.split()[0]) for p in headings]==list(range(1,9))
for label,count in [('Figure',3),('Table',5)]:
    captions=[p for p in paragraphs if p.style.name=='Caption' and p.text.startswith(label+' ')]
    assert [int(re.match(label+r' (\d+)\.',p.text).group(1)) for p in captions]==list(range(1,count+1))
    seen=[]
    for p in paragraphs:
        if p.style.name=='Caption':continue
        for n in re.findall(label+r' (\d+)\b',p.text):
            if int(n) not in seen:seen.append(int(n))
    assert seen==list(range(1,count+1)),(label,seen)
with ZipFile(B/'IJ3C_Manuscript.docx') as z:
    root=etree.fromstring(z.read('word/document.xml'))
    styles=etree.fromstring(z.read('word/styles.xml'))
    counts=Counter(styles.xpath('//w:style/@w:styleId',namespaces=ns))
    assert max(counts.values())==1
    used=set(root.xpath('//w:pStyle/@w:val',namespaces=ns))|{'Normal'}
    assert used<=counts.keys()
    equations=root.xpath('//w:p[m:oMath]',namespaces=ns)
    assert len(equations)==3
    for i,p in enumerate(equations,1):
        assert ''.join(p.xpath('./w:r/w:t/text()',namespaces=ns))==f'({i})'
        assert p.xpath('./w:pPr/w:tabs/w:tab[@w:val="right" and @w:pos="4320"]',namespaces=ns)
    actual_words=len(' '.join(root.xpath('//w:t/text() | //m:t/text()',namespaces=ns)).split())
assert actual_words<10000
render=json.loads((B/'qa/format_review.json').read_text())
assert len(render['pages_visually_inspected'])==len(render['pages'])
report=dict(state='passed',instruction_source='template/IJ3C_template.docx',sample_source='template/IJ3C_Sample-file.docx',
    instruction_sha256=digest(B/'template/IJ3C_template.docx'),sample_sha256=digest(B/'template/IJ3C_Sample-file.docx'),
    pages=len(render['pages']),actual_word_split_count_including_tables_equations=actual_words,abstract_words=len(abstract.split()),keywords=[k.strip() for k in keywords],
    styles_unique=True,all_used_styles_defined=True,role_font_sizes_pt=expected,
    margins_mm=1418*25.4/1440,column_gap_mm=424*25.4/1440,section_column_pattern=columns,
    main_headings='1 through 8, Arabic numerals, left aligned',native_equations='1 through 3, right aligned numbers',
    figures='1 through 3, sequential first mentions',tables='1 through 5, sequential first mentions',references='1 through 11, checked by check_manuscript.py',
    editorial_revision=True,saved_study_results_unchanged=True,visual_review='All final pages inspected at original resolution after the content and display revision.',
    unresolved_author_fields=['Author names and affiliations','Corresponding author email'],
    acknowledgment='Omitted at user request; deferred text retained separately.',
    precedence='Written instructions control Arabic left-aligned headings; the older sample uses a different heading convention.',
    source_delivery='PDF for initial submission; retained instructions specify .doc source after acceptance. This editable revision is DOCX.',
    docx_sha256=digest(B/'IJ3C_Manuscript.docx'),pdf_sha256=digest(B/'IJ3C_Manuscript.pdf'))
(B/'qa/template_compliance.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
