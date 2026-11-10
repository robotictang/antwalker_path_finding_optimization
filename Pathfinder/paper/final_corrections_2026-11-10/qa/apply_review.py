from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree
import argparse, hashlib, json, importlib.util

BASE = Path('/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder')
SOURCE = BASE / 'paper/NoReferences-Minimal-Factual-Corrections-Highlighted.docx'
OUTPUT = BASE / 'paper/Pathfinder-IJ3C-Final-Corrections-Highlighted.docx'
QA = Path(__file__).resolve().parent
EXPECTED = '52f8a783cc392dbc8100f6921d8aa33e29845d55470187714f022d4f45d9ea96'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
Q = '{' + W + '}'

# Reuse the previously checked span editor; it preserves unaffected run formatting.
spec = importlib.util.spec_from_file_location('span_editor', BASE / 'paper/minimal_factual_edit_2026-11-10/qa/edit_minimal.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

PATCHES = [
 (2, 'Research Center for Human Machine Collaboration (HUMAC)', 'Research Centre for Human-Machine Collaboration (HUMAC)', 'Official institutional name'),
 (2, 'Sunway University No. 5', 'Sunway University, No. 5', 'Affiliation punctuation'),
 (2, 'Selangor Darul, Ehsan', 'Selangor Darul Ehsan', 'Postal address punctuation'),
 (5, 'the zero median and the descriptive 95 % bootstrap interval is [−0.255, 2.312] %', 'the median is zero, and the descriptive 95% bootstrap interval is [−0.255, 2.312]%', 'Repair abstract grammar; values unchanged'),
 (8, 'refinement during planning affects', 'refinement during planning affect', 'Subject–verb agreement'),
 (10, 'The ant system bases on', 'Ant System uses', 'Repair sentence construction'),
 (10, 'the best candidate in the world', 'a global optimum', 'Precise optimization terminology'),
 (10, 'minimizing the length one route', 'minimizing route length', 'Repair sentence construction'),
 (10, 'Does not make use of or test their controller.', 'The present study does not use or test their controller.', 'Give the sentence a subject'),
 (18, 'No physical measurements of motor torque-speed characteristics, battery depletion or robot mass.', 'Motor torque–speed characteristics, battery depletion and robot mass were not physically measured.', 'Repair sentence fragment'),
 (18, 'Also modifies horizontal velocity', 'It also modifies horizontal velocity', 'Give the sentence a subject'),
 (18, 'route choice choices', 'route choices', 'Remove duplicated word'),
 (18, 'Not including sensor noise, localization errors and map reconstruction.', 'Sensor noise, localization errors and map reconstruction are not included.', 'Repair sentence fragment'),
 (27, 'Acceptance" means', 'Acceptance means', 'Remove stray quotation mark'),
 (29, 'Both rules are not statistically calibrated probability', 'Neither rule provides a statistically calibrated probability', 'Repair sentence construction'),
 (29, 'The candidate ranking process first determines if routes meet all constraints, and then if they do not.', 'Candidates are ranked first by feasibility, then by total normalized violation, and finally by Q.', 'State ranking order clearly'),
 (42, 'Does not only focus on the impact of representation.', 'The comparison does not isolate the effect of representation.', 'Repair fragment and clarify comparison scope'),
 (66, 'Last 25% of time; CLRP steps', 'Reserved 25% time allowance; CLRP steps', 'Distinguish reserved allowance from realized refinement timing'),
 (70, 'Start and destination proposals are sampled between −17 and 17 m (with a starting distance of 12–26 m) on each axis. Proposals are moved to free grid locations and kept if their eventual separation is ≥ 10 m.', 'Start and destination coordinates are sampled between −17 and 17 m on each axis, with an initial Euclidean separation of 12–26 m. The endpoints are then moved to free grid locations and retained if their final Euclidean separation is at least 10 m.', 'Report Euclidean separation separately from coordinate bounds'),
 (72, 'The alternative CLRP profile consists of a combination of initial-search fraction of 0.55, extra-point fraction of 0.25, 60 points, 12 labels per state, and local move sizes of 0.50, 0.15 and 0.05 m. All other settings are unchanged from their respective default settings.', 'In all four alternative profiles, the initial-search time fraction is 0.55 and the local-refinement move sizes are 0.50, 0.15 and 0.05 m. Alternative CLRP additionally uses a landmark-search time fraction of 0.25 and a maximum of 60 landmark points. Its executed initial refiner retains eight labels per state. Apart from these changes and the method-specific settings listed above, other effective settings remain at their respective defaults.', 'Describe executed settings and shared alternative changes'),
 (72, 'Exact ties', 'exact ties', 'Correct capitalization'),
 (72, '576 shots', '576 planning attempts', 'Use study terminology'),
 (78, 'Mission times are completed and includes', 'Completed mission times include', 'Repair sentence construction'),
 (133, 'Search effort for all 96 search efforts for each method', 'Search effort across all 96 attempts for each method', 'Remove duplicated wording'),
 (172, 'relative score improvements achieved with paired-maps', 'relative score effects across paired maps', 'Use a signed-effect term for negative and positive observations'),
 (172, 'figure 2', 'Figure 2', 'Consistent figure reference'),
 (172, 'For the noP comparison, it is leave-one-map-out, remain positive,', 'For the noP comparison, the leave-one-map-out means remain positive,', 'Repair sentence construction'),
 (177, 'This is why you are seeing the scores of the returned routes vary, but it does not specify one particular internal factor in the optimizer.', 'The returned routes therefore have different scores, although this does not identify a particular internal cause in the optimizer.', 'Use direct scientific prose without attributing an untested mechanism'),
 (179, 'black squares', 'black shapes', 'Caption includes rectangular corridor barriers'),
 (180, 'It is a one instance', 'It is one instance', 'Remove incorrect article'),
 (206, 'Under the tested settings final local adjustment is more accepted and gives lower scores in more accepted attempts than landmark search.', 'Under the tested settings, final local adjustment has a larger observed acceptance effect and gives lower scores in more accepted attempts than landmark search.', 'Clarify the observed stage-removal comparison'),
 (206, 'a loss of recorded computation', 'a reduction in recorded computation', 'Describe lower recorded computation unambiguously'),
 (206, 'map 24 has significant impact', 'Map 24 has a strong influence', 'Avoid implying an unperformed significance test'),
 (206, 'non-corridor action', 'non-corridor attempt', 'Use study terminology'),
 (206, 'corridor actions', 'corridor attempts', 'Use study terminology'),
 (208, 'the description 95% bootstrap interval', 'the descriptive 95% bootstrap interval', 'Correct word choice'),
]

# Layout cleanup is deliberately unhighlighted.
LAYOUT_TEXT_REMOVALS = [
 (32, ' Algorithm 1.'),
 (44, ' Table 1. Selected search settings: noL omits landmark search; noP omits final adjustment.'),
]

def txt(node):
    return ''.join(node.xpath('.//w:t/text()', namespaces=NS))

def split_payload_runs(p):
    # Preserve the affiliation's explicit line break when splitting text spans.
    for run in list(p.findall('w:r', NS)):
        payload = [c for c in run if c.tag != Q+'rPr']
        if len(payload) <= 1:
            continue
        index = p.index(run)
        props = run.find('w:rPr', NS)
        for i, child in enumerate(payload):
            r = etree.Element(Q+'r')
            if props is not None:
                r.append(deepcopy(props))
            r.append(deepcopy(child))
            p.insert(index+i, r)
        p.remove(run)

def set_cell_margins(cell, pad):
    pr=cell.find('w:tcPr',NS)
    mar=pr.find('w:tcMar',NS)
    if mar is None:
        mar=etree.SubElement(pr,Q+'tcMar')
    for edge in ['left','right','start','end']:
        e=mar.find('w:'+edge,NS)
        if e is None:e=etree.SubElement(mar,Q+edge)
        e.set(Q+'w',str(pad));e.set(Q+'type','dxa')

def table_widths(table,widths,pad=60):
    assert sum(widths)==4320
    columns=table.findall('w:tblGrid/w:gridCol',NS)
    assert len(columns)==len(widths)
    for col,width in zip(columns,widths):col.set(Q+'w',str(width))
    for row in table.findall('w:tr',NS):
        cells=row.findall('w:tc',NS)
        assert len(cells)==len(widths)
        for cell,width in zip(cells,widths):
            tcw=cell.find('w:tcPr/w:tcW',NS)
            tcw.set(Q+'w',str(width));tcw.set(Q+'type','dxa')
            set_cell_margins(cell,pad)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--replace-generated',action='store_true')
    args=parser.parse_args()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'Source changed since review.'
    with ZipFile(SOURCE) as zin:
        root=etree.fromstring(zin.read('word/document.xml'))
        paragraphs=root.findall('.//w:p',NS)
        original=[txt(p) for p in paragraphs]
        expected=list(original)
        log=[];formats=[]
        split_payload_runs(paragraphs[2])
        for pid,old,new,reason in PATCHES:
            assert expected[pid].count(old)==1,(pid,old)
            helper.replace_span(paragraphs[pid],old,new)
            expected[pid]=expected[pid].replace(old,new,1)
            runs=paragraphs[pid].xpath('./w:r[w:rPr/w:highlight[@w:val="yellow"]]',namespaces=NS)
            assert any(txt(r)==new for r in runs),(pid,new)
            log.append(dict(paragraph=pid,old=old,new=new,reason=reason,highlight='yellow'))
        for pid,old in LAYOUT_TEXT_REMOVALS:
            assert expected[pid].endswith(old),(pid,expected[pid][-150:])
            remaining=len(old)
            for node in reversed(paragraphs[pid].xpath('.//w:t',namespaces=NS)):
                if not remaining:break
                value=node.text or ''
                removed=min(remaining,len(value))
                node.text=value[:-removed] if removed else value
                remaining-=removed
            assert remaining==0
            for run in list(paragraphs[pid].findall('w:r',NS)):
                if not txt(run) and run.find('w:t',NS) is not None:
                    paragraphs[pid].remove(run)
            expected[pid]=expected[pid][:-len(old)]
            formats.append(dict(paragraph=pid,change='Remove duplicated layout label',removed=old,highlight=False))
        # Single provided affiliation: remove the six unmatched superscript markers.
        author=paragraphs[1];removed=0
        for run in list(author.findall('w:r',NS)):
            if txt(run)=='1' and run.find('w:rPr/w:vertAlign[@w:val="superscript"]',NS) is not None:
                author.remove(run);removed+=1
        assert removed==6
        expected[1]=txt(author)
        formats.append(dict(paragraph=1,change='Remove six inconsistent single-affiliation superscripts',highlight=False))
        tables=root.findall('.//w:tbl',NS)
        # Remove only the prior formatting-only highlights from Table 3.
        cleared=0
        for h in tables[2].xpath('.//w:highlight',namespaces=NS):
            h.getparent().remove(h);cleared+=1
        assert cleared==7,cleared
        formats.append(dict(table=3,change='Remove prior formatting-only cell highlights',count=cleared,highlight=False))
        for index,widths in [(0,[1010,2110,1200]),(3,[1114,900,650,1011,645]),(4,[1438,800,938,1144])]:
            table_widths(tables[index],widths)
            formats.append(dict(table=index+1,change='Adjust column widths and cell padding; labels and numbers retained',widths=widths,highlight=False))
        assert [txt(p) for p in paragraphs]==expected
        # Exact preservation of all result tables, mathematical formulas, figures and bibliography.
        original_root=etree.fromstring(zin.read('word/document.xml'))
        oldtables=original_root.findall('.//w:tbl',NS)
        for a,b in zip(oldtables[1:],tables[1:]):assert txt(a)==txt(b)
        def nodes_xml(r,xpath):return [etree.tostring(x) for x in r.xpath(xpath,namespaces=NS)]
        assert nodes_xml(original_root,'//m:oMath')==nodes_xml(root,'//m:oMath')
        assert nodes_xml(original_root,'//w:drawing')==nodes_xml(root,'//w:drawing')
        assert original[210:]==expected[210:]
        assert not tables[2].xpath('.//w:highlight',namespaces=NS)
        for i in [0,3,4]:
            header=tables[i].find('w:tr',NS)
            assert not header.xpath('.//w:highlight',namespaces=NS)
        abstract=expected[5]
        assert len(abstract.split())<=250
        xml=etree.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
        if args.write:
            assert not OUTPUT.exists() or args.replace_generated,'Do not overwrite existing output.'
            with ZipFile(OUTPUT,'w') as zout:
                for info in zin.infolist():zout.writestr(info,xml if info.filename=='word/document.xml' else zin.read(info.filename))
            QA.mkdir(parents=True,exist_ok=True)
            (QA/'changes.json').write_text(json.dumps(log,indent=2,ensure_ascii=False)+'\n')
            (QA/'formatting_changes.json').write_text(json.dumps(formats,indent=2,ensure_ascii=False)+'\n')
            (QA/'output_paragraphs.txt').write_text('\n\n'.join(f'P{i}: {t}' for i,t in enumerate(expected) if t.strip()))
            (QA/'verification.json').write_text(json.dumps(dict(source=str(SOURCE),source_sha256=EXPECTED,output=str(OUTPUT),output_sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),wording_replacements=len(log),changed_paragraphs=len({x['paragraph'] for x in log}),formatting_operations=len(formats),new_wording_highlighted=True,formatting_highlighted=False,prior_formatting_only_highlights_removed=cleared,result_tables_text_unchanged=True,equation_xml_unchanged=True,drawing_xml_unchanged=True,references_unchanged=True,abstract_words=len(abstract.split()),visual_review='Pending'),indent=2)+'\n')
        print(json.dumps(dict(wording_replacements=len(log),formatting_operations=len(formats),abstract_words=len(abstract.split()),write=args.write,output=str(OUTPUT)),indent=2))

if __name__=='__main__':main()
