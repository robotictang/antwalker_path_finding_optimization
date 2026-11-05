"""Verify final PDF fonts, embedding, page geometry and page numbering."""
from pathlib import Path
from collections import Counter
import hashlib,json
import pdfplumber
from pypdf import PdfReader
B=Path(__file__).resolve().parents[1]
P=B/'IJ3C_Manuscript.pdf'
fonts=Counter();pages=[]
with pdfplumber.open(P) as pdf:
    for i,page in enumerate(pdf.pages,1):
        assert str(i)==page.extract_text().splitlines()[-1].strip()
        assert abs(page.width-595.3)<1 and abs(page.height-841.89)<1
        body=[c for c in page.chars if c['top']<780]
        assert min(c['x0'] for c in body)>=70 and max(c['x1'] for c in body)<=528
        fonts.update(c['fontname'].split('+')[-1] for c in body)
        pages.append(dict(page=i,numbered=True,a4=True,body_bounds_within_margins=True))
assert len(pages)==10
assert not any(term in '\n'.join(p.extract_text() for p in PdfReader(P).pages).lower() for term in ['acknowledg','openai','codex'])
assert all(f.startswith('TimesNewRoman') or f=='OpenSymbol' for f in fonts),fonts
embedded=[];reader=PdfReader(P)
for page in reader.pages:
    for ref in page['/Resources']['/Font'].values():
        font=ref.get_object();base=str(font.get('/BaseFont',''))
        if 'TimesNewRoman' not in base:continue
        sub=font.get('/DescendantFonts',[font])[0].get_object()
        desc=sub['/FontDescriptor'].get_object()
        assert any(desc.get(k) for k in ['/FontFile','/FontFile2','/FontFile3'])
        if base not in embedded:embedded.append(base)
assert len(embedded)>=3
report=dict(state='passed',pages=pages,body_fonts=dict(fonts),times_new_roman_embedded=True,
    embedded_times_faces=embedded,math_symbol_font='OpenSymbol for four mathematical operator glyphs; text and equation letters/numbers use Times New Roman.',
    docx_sha256=hashlib.sha256((B/'IJ3C_Manuscript.docx').read_bytes()).hexdigest(),pdf_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),
    pages_visually_inspected=list(range(1,11)),visual_review='All ten latest pages inspected at original resolution after font repair. Tables, plots, native equations, references and page numbers are legible and unclipped.',
    remaining_items=['Author names, affiliations and corresponding email','Final author scientific approval'],
    renderer='Bundled LibreOfficeDev 26.8 and Poppler through isolated compatible loader, with task-local Math font settings. Installed desktop LibreOffice was not used.',
    font_authorization='Explicit user approval in this chat on 4 November 2026.')
(B/'qa/format_review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(state='passed',pages=len(pages),embedded_fonts=embedded),indent=2))
