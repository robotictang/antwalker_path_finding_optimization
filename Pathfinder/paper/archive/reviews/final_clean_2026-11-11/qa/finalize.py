from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from collections import Counter
from lxml import etree
import argparse, hashlib, json, re

base=Path('/home/dewayne/Desktop/Github/antwalker_path_finding_optimization/Pathfinder')
source=Path('/home/dewayne/Downloads/Pathfinder-IJ3C-Final.docx')
layout=base/'paper/Pathfinder-IJ3C-Final-Corrections-Highlighted.docx'
out=base/'paper/Pathfinder-IJ3C-Final-Clean.docx'
qa=Path(__file__).resolve().parent
w='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
m='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
space='{http://www.w3.org/XML/1998/namespace}space'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=lambda el:''.join(x.text or '' for x in el.iter(w+'t'))
sha='5fce1ab6961fd206fb65b458ae08f7a8529561896fa60b08c279fef13b50b22f'

def change(p,old,new):
    assert p.count(old)==1,old
    return p.replace(old,new,1)

def plain_text(p,value):
    runs=p.findall(w+'r')
    assert runs and all(c.tag in {w+'t',w+'rPr'} for r in runs for c in r)
    props=deepcopy(runs[0].find(w+'rPr'))
    for r in runs:p.remove(r)
    r=etree.SubElement(p,w+'r')
    if props is not None:r.append(props)
    t=etree.SubElement(r,w+'t');t.set(space,'preserve');t.text=value
    assert text(p)==value

parser=argparse.ArgumentParser()
parser.add_argument('--write',action='store_true')
parser.add_argument('--replace-generated',action='store_true')
parser.add_argument('--no-balance',action='store_true')
args=parser.parse_args()
assert digest(source)==sha
with ZipFile(source) as src, ZipFile(layout) as fmt:
    a=etree.fromstring(src.read('word/document.xml'))
    b=etree.fromstring(fmt.read('word/document.xml'))
    ap=list(a.iter(w+'p')); bp=list(b.iter(w+'p'))
    assert len(ap)==len(bp)==222
    cur=list(map(text,ap)); old=list(map(text,bp))
    assert {i for i,(x,y) in enumerate(zip(cur,old)) if x!=y}=={1,2,5,18,25,29,36,37,38,39,72,81,131,172,174,175,204,206,208,*range(211,222)}
    assert len(list(a.iter(m+'oMath')))==0 and len(list(b.iter(m+'oMath')))==5
    original_math=[etree.tostring(x) for x in b.iter(m+'oMath')]
    original_figures=[etree.tostring(x) for x in b.iter(w+'drawing')]
    assert sorted(hashlib.sha256(src.read(n)).hexdigest() for n in src.namelist() if n.startswith('word/media/') and not n.endswith('/'))==sorted(hashlib.sha256(fmt.read(n)).hexdigest() for n in fmt.namelist() if n.startswith('word/media/') and not n.endswith('/'))
    assert [text(t) for t in a.iter(w+'tbl')]==[text(t) for t in b.iter(w+'tbl')]
    final=cur[:]
    final[5]=change(cur[5],cur[5][cur[5].index('Landmark search removal'):],
        'Removing landmark search leaves 93 acceptances and reduces mean search time from 0.376 to 0.196 s. Complete CLRP has a conditional mean paired-map relative score improvement of 0.924% over this reduced version. Against PSO-C, the mean paired-map relative score effect is 0.690%, the median is zero, and the descriptive 95% bootstrap interval is [−0.255%, 2.312%]. The interval includes zero and does not establish a mean score advantage. A separate diagnostic comprises 16 executions: four missions under four assistance conditions. Full-scale and half-scale assistance each complete all four missions. Neither zero-assistance condition completes any mission before the 180 s timeout. No foot contact is detected in the assisted executions under the six-foot criterion. Results quantify the planning tradeoffs and dependence on direct body assistance. Battery costs are nominal model estimates without physical or electrical validation.')
    final[36]='2. Test the straight route from start to destination. Reject routes that fail the clearance check. Evaluate valid routes with the common metrics and ranking rule, reusing cached evaluations for repeated geometry.'
    final[38]='4. Construct collision-free visibility links. Search the graph with heading-aware states, in turn by score, time and battery use. Limit this stage to the remaining expansion budget (40,000 minus expansions used by the initial refiner) and 32% of nominal search time. Evaluate full routes using the common ranking rule.'
    final[72]=change(cur[72], 'When the two profiles have the same number of accepted attempts, the one with more attempts is picked first. If the acceptance counts are equal, the profile of the lowest mean score of the accepted attempts is selected.', 'Select the profile with the most accepted attempts. If acceptance counts are equal, select the profile with the lowest mean score among accepted attempts.')
    final[72]=change(final[72],'The fraction of the initial-search time is 0.55 for all four alternative profiles, as are the local-refinement move sizes of 0.50, 0.15 and 0.05 m. Alternative CLRP also utilizes the 0.25 landmark-search time fraction and 60 maximum landmark points. It has eight labels per state on its executed initial refiner. Other effective settings are at their default except for these changes and the changes for the methods listed above..','All four alternative profiles use an initial-search time fraction of 0.55 and local-refinement move sizes of 0.50, 0.15 and 0.05 m. Alternative CLRP also uses a landmark-search time fraction of 0.25 and a maximum of 60 landmark points. Its executed initial refiner retains eight labels per state. Other effective settings remain at their defaults except for the method-specific changes listed above.')
    final[81]=change(cur[81],cur[81][cur[81].index('CLRP, PSO-P, ACO-P'):], 'CLRP, PSO-P, ACO-P and CLRP noL each accept 93 of 96 attempts, PSO-C accepts 94, and CLRP noP accepts 90. All 20 rejected main-test attempts exceed the predicted outbound deadline; their battery and terrain-exposure checks pass.')
    final[131]=change(cur[131],'Conditional score comparisons are not substitutes for the scores for the total sample.','Conditional score comparisons do not replace the acceptance results for the full sample.')
    final[172]=change(cur[172],'The noP comparison is leave-one-map-out (or "remain positive"): ranging from 0.682% to 0.822%.','For the noP comparison, the leave-one-map-out means remain positive, ranging from 0.682% to 0.822%.')
    final[174]='Figure 2. Mean relative score difference between CLRP and PSO-C across jointly accepted repetitions within each paired map. Positive values favor CLRP. All points are included in the primary mean.'
    final[175]=change(cur[175],"This map's positive mean comes from a zero map-level median and equal numbers of lower and higher scores at the attempt level against PSO-C.", 'Map 24 drives the positive mean against PSO-C. The map-level median is zero, and the numbers of lower and higher scores are equal at the attempt level.')
    final[204]=change(cur[204],'Mission times are completed times including 8 seconds of station service. When there is no direct assistance, the traveled distance is 0.324-0.326 m with leg-body gravity compensation, and 0.376-0.381 m without it.', 'Completed mission times include 8 seconds of station service. Without direct assistance, distances at timeout are 0.324–0.326 m with leg-body gravity compensation and 0.376–0.381 m without it.')
    final[204]=change(final[204],'These findings support only route following with direct body assistance, and not propulsion through foot–ground interaction. With zero direct assistance, small horizontal motions are observed, but none of the four missions are completed within 180 s, under either leg-body gravity compensation being enabled or verified disabled.', 'These findings demonstrate route following with direct body assistance and do not validate propulsion through foot–ground interaction. Without direct assistance, small horizontal motions occur, but no mission completes within 180 s with leg-body gravity compensation either enabled or verified disabled.')
    final[206]=change(cur[206],cur[206][:cur[206].index('The retained route')], 'Removing final local refinement loses three acceptances, all repetitions of one corridor map (seed 2140011). Removing landmark search reduces recorded computation without changing acceptance. Among jointly accepted attempts, complete CLRP scores lower in 57 comparisons with CLRP noP and in 27 with CLRP noL. ')
    final[208]=change(cur[208],cur[208][:cur[208].index('There is no mean score advantage')], 'Final local refinement increases acceptance from 90 to 93 of 96 attempts; the three additional acceptances are repetitions of one corridor map. Landmark search leaves acceptance at 93 of 96. Complete CLRP has a conditional mean paired-map relative score improvement of 0.924% over CLRP noL. Mean search time is 0.196 s without landmark search and 0.376 s with it. ')
    final[208]=change(final[208], 'PSO-C has one more scheduled attempt. In a separate diagnostic there are 16 valid motion executions. Full-scale and half-scale assistance fully completed all four missions. Zero assistance is complete none and time out at 180 s, leg body gravity compensation is enabled or verified disabled. Under the defined 6-foot test, all assisted executions show no foot contact. The study, therefore, distinguishes between the acceptance of a limited body route and the validation of an unassisted locomotion of the body.', 'PSO-C accepts one more attempt than CLRP; both have 96 scheduled attempts. A separate diagnostic comprises 16 valid motion executions. Full-scale and half-scale assistance each complete all four missions. Both zero-assistance conditions time out at 180 s without completing any mission, with leg-body gravity compensation either enabled or verified disabled. Under the six-foot contact criterion, no foot contact is detected in any assisted execution. The study distinguishes acceptance of a planned body route from validation of unassisted locomotion.')
    assert len(final[5].split())<=250
    # Strip highlighting only; preserve intentional table shading.
    removed=0
    for h in list(b.iter(w+'highlight')):
        h.getparent().remove(h);removed+=1
    for i,(x,y) in enumerate(zip(old,final)):
        if x==y:continue
        if i>=211:
            assert re.sub(r'^(\[\d+\])\s+',r'\1',y)==x
            final[i]=x # Journal layout uses a tab, not an ordinary space.
        elif i==2:
            assert x.rstrip()==y
            last=list(bp[i].iter(w+'t'))[-1]
            assert not (last.text or '').strip()
            last.text=''
        else:
            plain_text(bp[i],y)
    assert list(map(text,bp))==final
    assert [etree.tostring(x) for x in b.iter(m+'oMath')]==original_math
    assert [etree.tostring(x) for x in b.iter(w+'drawing')]==original_figures
    assert [text(t) for t in a.iter(w+'tbl')]==[text(t) for t in b.iter(w+'tbl')]
    assert not list(b.iter(w+'highlight'))
    if not args.no_balance:
        # A continuous section boundary balances the final two-column reference page.
        body=b.find(w+'body');last=body.find(w+'sectPr')
        p=etree.Element(w+'p');pr=etree.SubElement(p,w+'pPr')
        spacing=etree.SubElement(pr,w+'spacing')
        for k,v in {'before':'0','after':'0','line':'20','lineRule':'exact'}.items():spacing.set(w+k,v)
        pr.append(deepcopy(last));body.insert(body.index(last),p)
        last.find(w+'cols').set(w+'num','1')
    changes=[i for i,(x,y) in enumerate(zip(cur,final)) if x.strip()!=y.strip() and i<211]
    v=dict(source=str(source),source_sha256=sha,layout_base=str(layout),equations_restored=5,figures_preserved=3,tables_unchanged=5,highlights_remaining=0,abstract_words=len(final[5].split()),corrected_paragraphs=changes,reference_text_unchanged=True,balanced_final_columns=not args.no_balance)
    if args.write:
        assert not out.exists() or args.replace_generated
        with ZipFile(out,'w') as dst:
            for item in fmt.infolist():
                val=fmt.read(item.filename)
                if item.filename=='word/document.xml':
                    val=etree.tostring(b,encoding='UTF-8',xml_declaration=True,standalone=True)
                elif item.filename.startswith('word/') and item.filename.endswith('.xml'):
                    part=etree.fromstring(val)
                    hs=list(part.iter(w+'highlight'))
                    if hs:
                        for h in hs:h.getparent().remove(h)
                        val=etree.tostring(part,encoding='UTF-8',xml_declaration=True,standalone=True)
                dst.writestr(item,val)
        v.update(output=str(out),output_sha256=digest(out))
        (qa/'verification.json').write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps(v,indent=2))
