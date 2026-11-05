"""Build the V4 paper by filling the retained official IEEE Access Word template."""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,json,re
from lxml import etree
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_BREAK,WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
B=Path(__file__).resolve().parents[1];R=B.parents[1];S=B/'evidence/advanced_study_v4' if (B/'evidence/advanced_study_v4').exists() else R/'mujoco/outputs/research/advanced_study_v4';T=B/'template/Access-Template-2024.docx'
D=Document(T);A=json.loads((B/'source/verified_paper_analysis.json').read_text());P=json.loads((S/'v4_heldout_planning.json').read_text());C=json.loads((S/'comparison.json').read_text());PH=json.loads((S/'v4_heldout_physics.json').read_text());AB=json.loads((S/'ablation_comparison.json').read_text());REF=json.loads((B/'source/references.json').read_text())
N={'b1_distance':'Distance A*','b2_terrain':'Terrain A*','b3_energy':'Energy A*','b4_weighted':'Weighted search','b7_greedy':'Greedy shortcut','pso':'PSO','aco':'ACO','proposed_v1':'Grid Pareto','proposed':'Corridor Pareto','pso_polished':'PSO + polish','aco_polished':'ACO + polish','proposed_v4':'V4 proposal'}
front=deepcopy(D.sections[0]._sectPr);body=deepcopy(D.sections[1]._sectPr)
# Retain the source geometry and header logos; update only declared metadata slots.
for e in [front,body]:
 for x in e.findall(qn('w:pgNumType')):e.remove(x)
 for x in e.findall(qn('w:headerReference'))+e.findall(qn('w:footerReference')):e.remove(x)
 for tag,rid in [('headerReference','rId9'),('footerReference','rId10')]:
  x=OxmlElement('w:'+tag);x.set(qn('w:type'),'default');x.set(qn('r:id'),rid);e.insert(0,x)
for x in list(D._element.body):D._element.body.remove(x)
D._element.body.append(deepcopy(body))
# Source-derived styles; do not replace the retained style system.
if 'Title' not in D.styles:D.styles.add_style('Title',WD_STYLE_TYPE.PARAGRAPH)
D.styles['Title'].base_style=D.styles['Paper Title'];D.styles['Title'].font.name='Helvetica';D.styles['Title'].font.size=Pt(22);D.styles['Title'].font.bold=True
D.styles['Title'].paragraph_format.space_before=Pt(24);D.styles['Title'].paragraph_format.space_after=Pt(15)
for name in ['Title','Paper Title','H1','H1_List (No Space)','H1_List (Space)','H2_First','H2_Cont','Heading 1','Heading 2']:
 if name in D.styles:D.styles[name].font.color.rgb=RGBColor(0,0,0)
D.core_properties.title='Resource Constrained Hexapod Path Planning With Visibility Search and Continuous Waypoint Refinement';D.core_properties.author='Tomato';D.core_properties.subject='IEEE Access manuscript reporting V4 and a separately frozen prospective validation extension';D.core_properties.keywords='hexapod; path planning; PSO; ACO; simulation';D.core_properties.last_modified_by='Manuscript preparation'
setting=D.settings.element.find(qn('w:updateFields'))
if setting is None:setting=OxmlElement('w:updateFields');D.settings.element.append(setting)
setting.set(qn('w:val'),'true')
# Clear source footer's example volume and fixed page number. Preserve its part relationship.
fpart=D.part.rels['rId10'].target_part;footer=etree.fromstring(fpart.blob)
for ch in list(footer):footer.remove(ch)
p=OxmlElement('w:p');pr=OxmlElement('w:pPr');tabs=OxmlElement('w:tabs');tab=OxmlElement('w:tab');tab.set(qn('w:val'),'right');tab.set(qn('w:pos'),'10040');tabs.append(tab);pr.append(tabs);p.append(pr)
def wr(t,size=15):
 r=OxmlElement('w:r');rp=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),str(size));rp.append(sz);r.append(rp);x=OxmlElement('w:t');x.text=t;x.set(qn('xml:space'),'preserve');r.append(x);return r
p.append(wr('REVIEW DRAFT   29 OCTOBER 2026'));tr=OxmlElement('w:r');tr.append(OxmlElement('w:tab'));p.append(tr)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');f.append(wr('1'));p.append(f);footer.append(p)
footer_bytes=etree.tostring(footer,xml_declaration=True,encoding='UTF-8',standalone=True)
ref_order=[];cites={};counts=dict(figures=0,tables=0,equations=0,algorithms=0);paragraph_log=[]
def no_num(p):
 n=OxmlElement('w:numPr');i=OxmlElement('w:numId');i.set(qn('w:val'),'0');n.append(i);p._p.get_or_add_pPr().append(n)
def bookmark(p,name,identifier):
 a=OxmlElement('w:bookmarkStart');a.set(qn('w:id'),str(identifier));a.set(qn('w:name'),name);z=OxmlElement('w:bookmarkEnd');z.set(qn('w:id'),str(identifier));p._p.insert(0,a);p._p.append(z)
def citation(p,key):
 assert key in REF,key
 if key not in cites:cites[key]=len(cites)+1;ref_order.append(key)
 n=cites[key];h=OxmlElement('w:hyperlink');h.set(qn('w:anchor'),f'reference_{n}');h.append(wr(f'[{n}]',20));p._p.append(h)
INLINE={'p_s':('p','s'),'p_g':('p','g'),'l_j':('l','j'),'v_j':('v','j'),'E_ret':('E','ret'),'B_0':('B','0'),'T_max':('T','max'),'H_max':('H','max'),'f_a':('f','a'),'v_a':('v','a'),'I_invalid':('I','invalid'),'g_k':('g','k'),'b_k':('b','k'),'W_b':('W','b'),'J_wb':('J','wb'),'Q_bwj':('Q','bwj'),'Q_vwj':('Q','vwj'),'n_wb':('n','wb'),'N_b':('N','b')}
def text(p,t):
 pos=0;pattern=r'\[@([a-z]+)\]|(?<![A-Za-z_])('+ '|'.join(INLINE)+r')(?![A-Za-z_])'
 for m in re.finditer(pattern,t):
  p.add_run(t[pos:m.start()])
  if m.group(1):citation(p,m.group(1))
  else:
   om=OxmlElement('m:oMath');om.append(sub(*INLINE[m.group(2)]));p._p.append(om)
  pos=m.end()
 p.add_run(t[pos:]);paragraph_log.append(t)
def para(t='',style='PARA_Indent'):
 p=D.add_paragraph(style=style);text(p,t);p.paragraph_format.widow_control=True;return p
def h(t,sub=False):
 t=re.sub(r'^([A-Z]) ',r'\1. ',t) if sub else re.sub(r'^([IVX]+) ',r'\1. ',t)
 p=D.add_paragraph(style='H2_First' if sub else 'H1');no_num(p);text(p,t.upper());p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
 for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
 return p
def section_break(props):
 p=D.add_paragraph();p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=Pt(1);p._p.get_or_add_pPr().append(deepcopy(props));return p
# Front matter uses the source full-width pattern.
para('Research manuscript draft prepared 29 October 2026','DOP');para('Not submitted   No DOI assigned','DOI')
p=para(D.core_properties.title,'Title');p.paragraph_format.keep_with_next=True
para('TOMATO','AU');para('[Department and institution to be supplied], [City and country to be supplied]','PI_No Space');para('Corresponding author: Tomato ([email to be supplied]).','PI_No Space')
p=para('Funding and conflict-of-interest declarations require author confirmation. This document is a review draft.','footnote text');p.paragraph_format.space_after=Pt(14)
content=(B/'source/manuscript.md').read_text();abstract=content.split('@ABSTRACT\n',1)[1].split('\n\n@KEYWORDS',1)[0].strip();keywords=content.split('@KEYWORDS\n',1)[1].split('\n\n## ',1)[0].strip();assert 150<=len(abstract.split())<=250,len(abstract.split())
p=D.add_paragraph(style='Abstract');p.paragraph_format.right_indent=Inches(0);r=p.add_run('ABSTRACT  ');r.bold=True;p.add_run(abstract)
p=D.add_paragraph(style='IT');p.paragraph_format.right_indent=Inches(0);r=p.add_run('INDEX TERMS  ');r.bold=True;p.add_run(keywords)
section_break(front)
# Structured native Word math, including fractions, subscripts, superscripts and sums.
def mr(t):
 e=OxmlElement('m:r');rp=OxmlElement('m:rPr');sty=OxmlElement('m:sty');sty.set(qn('m:val'),'p' if t in ['max','clip','lex'] else 'i');rp.append(sty);e.append(rp);x=OxmlElement('m:t');x.text=t;e.append(x);return e
def nodes(x):return [mr(x)] if isinstance(x,str) else [mr(v) if isinstance(v,str) else v for v in x] if isinstance(x,list) else [x]
def sub(x,y):
 e=OxmlElement('m:sSub');a=OxmlElement('m:e');b=OxmlElement('m:sub');a.extend(nodes(x));b.extend(nodes(y));e.extend([a,b]);return e
def sup(x,y):
 e=OxmlElement('m:sSup');a=OxmlElement('m:e');b=OxmlElement('m:sup');a.extend(nodes(x));b.extend(nodes(y));e.extend([a,b]);return e
def frac(x,y):
 e=OxmlElement('m:f');a=OxmlElement('m:num');b=OxmlElement('m:den');a.extend(nodes(x));b.extend(nodes(y));e.extend([a,b]);return e
def summ(lo,hi,expr):
 e=OxmlElement('m:nary');pr=OxmlElement('m:naryPr');c=OxmlElement('m:chr');c.set(qn('m:val'),'∑');pr.append(c);lim=OxmlElement('m:limLoc');lim.set(qn('m:val'),'subSup');pr.append(lim)
 if hi=='':hidden=OxmlElement('m:supHide');hidden.set(qn('m:val'),'1');pr.append(hidden)
 e.append(pr)
 for tag,val in [('sub',lo),('sup',hi),('e',expr)]:a=OxmlElement('m:'+tag);a.extend(nodes(val));e.append(a)
 return e
def eq_line(parts,num=None):
 p=D.add_paragraph(style='Equation');p.paragraph_format.left_indent=Inches(0);p.paragraph_format.first_line_indent=Inches(0);p.paragraph_format.right_indent=Inches(0);p.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.line_spacing=None;p.paragraph_format.space_before=Pt(6);p.paragraph_format.space_after=Pt(6)
 p.paragraph_format.tab_stops.clear_all();p.paragraph_format.tab_stops.add_tab_stop(Inches(1.5),WD_TAB_ALIGNMENT.CENTER);p.paragraph_format.tab_stops.add_tab_stop(Inches(3.28),WD_TAB_ALIGNMENT.RIGHT)
 tabs=p._p.get_or_add_pPr().find(qn('w:tabs'));clear=OxmlElement('w:tab');clear.set(qn('w:val'),'clear');clear.set(qn('w:pos'),'4584');tabs.insert(0,clear)
 p.add_run('\t')
 m=OxmlElement('m:oMath');m.extend([mr(x) if isinstance(x,str) else x for x in parts]);p._p.append(m)
 if num:
  if num==5:p.add_run().add_break()
  label=p.add_run(('\t\t' if num==5 else '\t')+'('+str(num)+')');label.font.italic=False
 return p
def equation(key):
 counts['equations']+=1;n=counts['equations']
 if key=='route':parts=['P = (',sub('p','0'),', …, ',sub('p','n−1'),'), ',sub('p','0'),' = ',sub('p','s'),', ',sub('p','n−1'),' = ',sub('p','g')]
 elif key=='distance':parts=['D = ',summ('i=0','n−2',sub(['‖',sub('p','i+1'),' − ',sub('p','i'),'‖'],'2'))]
 elif key=='time':parts=['T = ',summ('j','',frac(sub('l','j'),sub('v','j'))),' + ',frac('Θ','ω'),' + 0.6,   ω = 1 rad/s']
 elif key=='energy':parts=['E = 0.70D + 0.015T + 0.08Θ + 0.10']
 elif key=='difficulty':parts=['h(x) = clip(',frac([frac('s(x)','0.25'),' + ',frac('r(x)','0.12'),' + ',frac('u(x)','0.04'),' + z(x)'],'4'),', 0, 2)']
 elif key=='score':parts=['Q = ',frac('D','50'),' + ',frac('T','90'),' + ',frac('E','30'),' + 0.25',frac('H','20')]
 elif key=='admission':
  p=eq_line(['T ≤ ',sub('T','max'),',   H ≤ ',sub('H','max')]);p.paragraph_format.keep_with_next=True;parts=['1.25(E + ',sub('E','ret'),') + 6 ≤ ',sub('B','0')]
 elif key=='rank':
  p=eq_line(['R(P) = (',sub('I','invalid'),', V(P), Q(P))']);p.paragraph_format.keep_with_next=True;parts=['V(P) = ',summ('k: gₖ>ε','',frac(sub('g','k'),['max(',sub('b','k'),', ',sup('10','−9'),')']))]
 elif key=='work':parts=['W⁺ ≈ ',summ('t','',['Δt ',summ('a','',['max(',sub('f','a'),'(t)',sub('v','a'),'(t), 0)'])])]
 elif key=='relative':
  p=eq_line([sub('r','wb'),' = ',frac('1',sub('n','wb')),summ('j∈Jwb','',['100 ',frac([sub('Q','bwj'),' − ',sub('Q','vwj')],sub('Q','bwj'))])]);p.paragraph_format.keep_with_next=True;parts=[sub('r̄','b'),' = ',frac('1',sub('N','b')),summ('w∈Wb','',sub('r','wb'))]
 else:raise ValueError(key)
 eq_line(parts,n)
# Tables stay native and source-derived.
def roman(n):
 out=''
 for a,b in [(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
  while n>=a:out+=b;n-=a
 return out
def table(caption,headers,rows,widths):
 counts['tables']+=1;p=para('TABLE '+roman(counts['tables'])+'  '+caption.upper(),'Table Caption');p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(8);p.paragraph_format.space_after=Pt(4)
 t=D.add_table(rows=1,cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for col,width in zip(t.columns,widths):col.width=Inches(width)
 pr=t._tbl.tblPr
 borders=OxmlElement('w:tblBorders')
 for edge in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'3');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 pr.append(borders);marg=OxmlElement('w:tblCellMar')
 for edge,val in [('top','45'),('bottom','45'),('left','45'),('right','45')]:e=OxmlElement('w:'+edge);e.set(qn('w:w'),val);e.set(qn('w:type'),'dxa');marg.append(e)
 pr.append(marg)
 for cells,vals,head in [(t.rows[0].cells,headers,True)]+[(t.add_row().cells,row,False) for row in rows]:
  for i,(c,v,w) in enumerate(zip(cells,vals,widths)):
   c.width=Inches(w);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;p=c.paragraphs[0];p.style=D.styles['PARA'];p.paragraph_format.first_line_indent=Inches(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=Pt(10);p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run(str(v));r.font.size=Pt(8);r.bold=head
   if head:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'F1F3F4');c._tc.get_or_add_tcPr().append(sh)
  trpr=cells[0]._tc.getparent().get_or_add_trPr();nr=OxmlElement('w:cantSplit');trpr.append(nr)
  if head:trpr.append(OxmlElement('w:tblHeader'))
 # Keep short parameter/comparison/budget tables intact across columns.
 if caption.startswith(('Selected settings','Paired primary','Shorter budget')):
  for ri,row in enumerate(t.rows):
   for cell in row.cells:
    for p in cell.paragraphs:p.paragraph_format.keep_with_next=ri<len(t.rows)-1
 # Other tables may continue with repeated headers and intact rows.
 para('').paragraph_format.space_after=Pt(2)
 return t

def named_table(key):
 if key=='notation':table('Notation and interpretation',['Symbol','Meaning and units'],[['D','Body route length (m)'],['T','Predicted destination time (s)'],['E','Nominal outbound battery use (percentage points)'],['H','Integrated terrain difficulty exposure'],['B, B₀','Planner wall allowance (s); available battery (%)'],['Q','Fixed normalized balanced route score'],['W⁺','Positive actuator work on full motion (J)']],[.55,2.78])
 elif key=='protocol':table('Frozen campaign phases',['Phase','Worlds','Methods','Repeats','Attempts'],[['Development default',8,4,2,64],['Development alternative',8,4,2,64],['Primary planning',24,12,3,864],['Feature removal',8,3,3,72],['0.5 s budget',4,12,1,48],['1.0 s budget',4,12,1,48],['Assisted physics',6,12,1,72],['Total scheduled','—','—','—',1232]],[1.18,.44,.53,.53,.65])
 elif key=='parameters':table('Selected settings and control scope',['Method','Selected parameters'],[['PSO','24 particles; inertia 0.55; c₁ 1.70; c₂ 1.30; velocity cap 0.25'],['ACO','12 ants; α 1; β 2; evaporation 0.20; deposit 1'],['Corridor refiner','8 labels/state; beam width 6; archive cap 16'],['V4','Initial fraction 0.40; roadmap fraction 0.32; 44 nodes; steps 0.75, 0.25, 0.08 m'],['All applicable refiners','240 route evaluations; 40 iterations/corridor for swarms'],['Main attempts','2 s; 40,000 search expansions; 0.25 m grid']],[1.02,2.31])
 elif key=='main':table('Primary means with conditional admission denominators',['Method','Admitted','Mean Q','Plan s'],[[N[r['method']],str(r['admissible'])+'/72',f"{r['mean_quality_score']:.6f}",f"{r['mean_planning_seconds']:.4f}"] for r in P['summary']],[1.1,.56,.87,.8])
 elif key=='components':table('Mean components on each method admitted set',['Method','D m','T s','E pp','H'],[[N[r['method']],*[f'{r[k]:.3f}' for k in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']]] for r in A['route_components']],[1.05,.57,.57,.57,.57])
 elif key=='paired':table('Paired primary scores on 22 jointly admitted worlds',['Baseline','Win','Tie','Loss','Mean %','95% interval %'],[[N[r['baseline']],r['wins'],r['ties'],r['losses'],f"{r['mean_relative_score_improvement_percent']:.3f}",f"[{r['relative_improvement_95_percent'][0]:.3f}, {r['relative_improvement_95_percent'][1]:.3f}]"] for r in C['comparisons']],[1.02,.27,.27,.29,.52,.76])
 elif key=='ablation':table('Feature removal on eight preselected worlds',['Variant removed','Win','Tie','Loss','Mean %','95% interval %'],[['Polishing' if r['baseline'].endswith('no_polish') else 'Landmarks',r['wins'],r['ties'],r['losses'],f"{r['mean_relative_score_improvement_percent']:.3f}",f"[{r['relative_improvement_95_percent'][0]:.3f}, {r['relative_improvement_95_percent'][1]:.3f}]"] for r in AB['comparisons']],[1.02,.27,.27,.29,.52,.76])
 elif key=='budgets':
  rows=[]
  for phase in ['v4_budget_0p5','v4_budget_1p0']:
   d=json.loads((S/(phase+'.json')).read_text())
   for r in d['summary']:
    if r['method'] in ['pso','aco','pso_polished','aco_polished','proposed_v4']:rows.append([str(d['planning_budget_s']),N[r['method']],str(r['admissible'])+'/4',f"{r['mean_quality_score']:.6f}"])
  table('Shorter budget subset admitted route scores',['Budget s','Method','Admitted','Mean Q'],rows,[.55,1.30,.6,.68])
 elif key=='physics':table('Assisted physics means over five successful missions',['Method','Success / scheduled','Time s','Work J'],[[N[r['method']],str(r['successes'])+'/'+str(r['attempts']),f"{r['mean_task_time_s']:.4f}",f"{r['mean_positive_work_j']:.2f}"] for r in PH['summary']],[1.05,.72,.72,.84])
 else:raise ValueError(key)
CAPS={
 'tomat1':'System architecture. A single world specification drives planning and assisted physics. The dashboard displays archived attempts, including rejections; it is not an independent measurement source.',
 'tomat2':'V4 search and refinement stages. B denotes the complete planner wall allowance. The best registered route is retained at termination; feasibility is checked before balanced score.',
 'tomat3':'All 72 paired experiments for each alternative. Wins, ties and losses concern jointly admitted scores; the final categories retain admission differences. No baseline-only admissions occur.',
 'tomat4':'Mean paired balanced-score improvement and descriptive 95% whole-world intervals. Positive values favor V4. Only jointly admitted worlds contribute; intervals are uncorrected for multiple comparisons.',
 'tomat5':'Saved side-by-side route evidence, repetition 1. Top: heldout_24 compares PSO with V4; the dashed baseline route is resource rejected, not an executed mission. Bottom: heldout_02 compares polished PSO with V4 and shows a small V4 loss. Axes match within each row. Gray rectangles are obstacles, shaded regions are terrain, circles mark starts, and squares mark destinations. These post hoc illustrations do not replace complete-set statistics.',
 'tomat6':'Separate assisted-physics comparison of the five strongest configurations. Each has five successful executions and one rejected scheduled task. Destination time and full-mission actuator work have different scopes. Mechanical work excludes body assistance and is not electrical battery energy.',
 'tomat7':'Primary verdicts by terrain family, including all repetitions. Each family contains six worlds and 18 world/repetition pairs. Repeated seeds are not additional independent maps.'}
def figure(key,wide=False):
 counts['figures']+=1;n=counts['figures']
 if wide:
  s=D.add_section(WD_SECTION_START.CONTINUOUS);s._sectPr.find(qn('w:cols')).set(qn('w:num'),'1')
 p=D.add_paragraph();p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(2);p.paragraph_format.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
 sh=p.add_run().add_picture(str(B/'figures'/(key+'.png')),width=Inches(6.94 if wide else 3.32));sh._inline.docPr.set('descr',CAPS[key]);cap=para('FIGURE '+str(n)+'.  '+CAPS[key],'Figure Caption');cap.paragraph_format.space_after=Pt(8);cap.paragraph_format.keep_together=True
 if wide:
  s=D.add_section(WD_SECTION_START.CONTINUOUS);s._sectPr.find(qn('w:cols')).set(qn('w:num'),'2')
ALGS={
 'v4':('Resource constrained visibility and continuous refinement',[
 'Input: map, start, goal, limits, allowance B, seed.',
 'Start one wall timer and expansion counter.',
 'Run fixed default corridor refiner until 0.40 B.',
 'Register its route and carry its evaluation count.',
 'Try the direct start-to-goal connection.',
 'If time and candidate allowance remain:',
 '  Build up to 44 valid geometry landmarks.',
 '  Connect visible pairs within the roadmap stage.',
 '  Search balanced, time and energy preferences.',
 '  Register each fully evaluated route by rank R.',
 'Polish the incumbent using the three step scales.',
 'Recheck final geometry and all resource limits.',
 'Return route, admission, metrics and diagnostics.']),
 'controls':('Polished swarm control and component removal',[
 'Input: selected swarm settings and V4 limits.',
 'Run PSO or ACO within the same initial fraction.',
 'Carry its route and evaluation count into the pool.',
 'Try the direct connection with common checks.',
 'Skip the V4 landmark diversification stage.',
 'Apply the identical continuous polishing operator.',
 'Keep all stages inside the same total allowance.',
 'Return the best ranked route and admission.',
 'Ablations instead remove polishing or landmarks.'])}
def algorithm(key):
 counts['algorithms']+=1;title,lines=ALGS[key];p=para('ALGORITHM '+str(counts['algorithms'])+'  '+title,'Table Caption');p.paragraph_format.keep_with_next=True;p.paragraph_format.space_after=Pt(4)
 for i,line in enumerate(lines,1):
  p=D.add_paragraph(style='PARA');p.paragraph_format.first_line_indent=Inches(0);p.paragraph_format.left_indent=Inches(.04);p.paragraph_format.line_spacing=Pt(10.5);p.paragraph_format.space_after=Pt(0);p.paragraph_format.keep_with_next=i<len(lines);p.paragraph_format.keep_together=True;r=p.add_run(f'{i:02d}  '+line);r.font.size=Pt(8.5)
 para('')
def external(p,label,url):
 h=OxmlElement('w:hyperlink');rid=p.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True);h.set(qn('r:id'),rid);r=wr(label,16);h.append(r);p._p.append(h)
def references():
 for key in ref_order:
  n=cites[key];p=D.add_paragraph(style='References');no_num(p);p.paragraph_format.left_indent=Inches(.22);p.paragraph_format.first_line_indent=Inches(-.22);p.paragraph_format.line_spacing=Pt(9.5);p.paragraph_format.space_after=Pt(4);p.paragraph_format.keep_together=True;bookmark(p,f'reference_{n}',500+n)
  val=REF[key]['text'];val=val.replace('https://','https://\u200b').replace('_','_\u200b')
  r=p.add_run(f'[{n}]  '+val);r.font.size=Pt(8)
  if REF[key]['url']:external(p,' Source',REF[key]['url'])

EXT=json.loads((B/'source/extension_analysis.json').read_text())
EN={'proposed_v4':'V4 retuned','pso_polished':'PSO + polish','aco_polished':'ACO + polish','proposed_v5':'V5 candidate'}
CAPS.update({
 'ext1':'Fresh paired score effects for V5 on 48 test worlds. Effects against polished controls use 46 jointly admitted worlds. V4 and V5 scores tie; their effects against controls are identical. Intervals are descriptive 95% whole-world bootstraps.',
 'ext2':'V5 feature controls on the first 16 predeclared worlds with two repetitions. All 32 scheduled pairs per control remain in the outcome categories; ties and control wins are retained.',
 'ext3':'Fresh primary computation costs. Planner wall time and all continuous metric calls have separate units. Shared scene preparation is excluded; equal ceilings do not equalize actual computation.',
 'ext4':'Execution outcomes on 12 predeclared worlds per method and assistance setting. Bars use scheduled denominators. Assistance 0.5 denotes repeated velocity blending, not half force or unassisted locomotion.',
 'ext5':'Budget sensitivity on the first eight fresh worlds. Positive paired score effects favor V5. Short-budget phases have one repetition; the 2 s subset has two. Joint-admission populations can change with budget.'})
ALGS['v5']=('Adaptive search candidate, evaluated without guaranteed improvement',[
 'Input: common map, limits, timer and candidate cap.',
 'Try an exact collision-checked direct connection.',
 'If feasible and within the declared model bound gap:',
 '  Return the registered direct incumbent.',
 'Otherwise allocate seed time from direct visibility.',
 'Run the fixed initial refiner and carry its count.',
 'Generate geometry landmarks within the node cap.',
 'Prioritize an internal search for a violated resource.',
 'Register candidates using unchanged feasible-first Q.',
 'Apply the common collision-checked local polishing.',
 'Return the best incumbent and all diagnostics.'])
original_named_table=named_table
def named_table(key):
 if not key.startswith('ext'):return original_named_table(key)
 if key=='extprotocol':table('Prospective extension phases',['Phase','Worlds','Methods','Repeats','Attempts'],[['Development, 2 profiles',8,4,1,64],['Fresh primary',48,4,2,384],['Feature controls',16,4,2,128],['0.5 and 1 s budgets',8,4,1,64],['80-candidate ceiling',16,4,1,64],['Assistance 1.0',12,4,1,48],['Assistance 0.5',12,4,1,48],['Total scheduled','-','-','-',800]],[1.18,.44,.53,.53,.65])
 elif key=='extmain':table('Fresh primary conditional means',['Method','Admitted','Mean Q','Plan s'],[[EN[r['method']],str(r['admitted'])+'/96',f"{r['mean_q']:.6f}",f"{r['mean_planning_s']:.4f}"] for r in EXT['primary']],[1.10,.56,.87,.80])
 elif key=='extpaired':table('Fresh V5 paired effects on jointly admitted worlds',['Baseline','Win','Tie','Loss','Mean %','95% interval %'],[[EN[r['baseline']],r['wins'],r['ties'],r['losses'],f"{r['mean_relative_percent']:.3f}",f"[{r['relative_ci95'][0]:.3f}, {r['relative_ci95'][1]:.3f}]"] for r in EXT['comparisons']],[1.02,.27,.27,.29,.52,.76])
 elif key=='extphysics':
  def val(x,places):return 'N/A' if x is None else f'{x:.{places}f}'
  table('Prospective assisted execution by condition',['Method / aid','Success / scheduled','Time s','Work J'],[[EN[r['method']]+' / '+str(r['assistance']),str(r['successful'])+'/'+str(r['scheduled']),val(r['mean_task_s'],3),val(r['mean_work_j'],1)] for r in EXT['physics']],[1.12,.72,.68,.81])
 else:raise ValueError(key)

# Build scientific body from inspectable text, replacing only explicit slots.
bodytext='## I Introduction'+content.split('## I Introduction',1)[1]
bodytext=re.sub(r'^(#{1,3} .+)$',r'\1\n',bodytext,flags=re.M)
for block in bodytext.split('\n\n'):
 block=block.strip()
 if not block:continue
 if block.startswith('### '):h(block[4:],True)
 elif block.startswith('## '):h(block[3:])
 elif block.startswith('[[EQ:'):equation(block[5:-2])
 elif block.startswith('[[TABLE:'):named_table(block[8:-2])
 elif block.startswith('[[WIDEFIG:'):figure(block[10:-2],True)
 elif block.startswith('[[FIG:'):figure(block[6:-2])
 elif block.startswith('[[ALG:'):algorithm(block[6:-2])
 elif block=='[[REFERENCES]]':references()
 else:para(block)
assert len(cites)==len(REF),(set(REF)-set(cites))
# Save with python-docx, then retain unchanged original package parts exactly.
temp=B/'source/authored_working.docx';D.save(temp);final=B/'IEEE_Access_Hexapod_Validated_Manuscript.docx'
allowed={'word/document.xml','word/styles.xml','word/settings.xml','word/_rels/document.xml.rels','docProps/core.xml','[Content_Types].xml'}
footer_name=str(fpart.partname).lstrip('/');allowed.add(footer_name)
with ZipFile(T) as orig,ZipFile(temp) as authored:
 old=set(orig.namelist());new=set(authored.namelist());edited=[]
 with ZipFile(final,'w',ZIP_DEFLATED) as z:
  for name in orig.namelist():
   payload=footer_bytes if name==footer_name else authored.read(name) if name in allowed else orig.read(name)
   z.writestr(name,payload)
   if payload!=orig.read(name):edited.append(name)
  for name in sorted(new-old):z.writestr(name,authored.read(name))
with ZipFile(T) as orig,ZipFile(final) as z:
 preserved=[n for n in orig.namelist() if n not in allowed];assert all(orig.read(n)==z.read(n) for n in preserved)
assert hashlib.sha256(T.read_bytes()).hexdigest()==re.search(r'SHA256: ([0-9a-f]{64})',(B/'artifact.md').read_text()).group(1)
report=dict(template_sha256=hashlib.sha256(T.read_bytes()).hexdigest(),template_parts_preserved=len(preserved),edited_parts=edited,added_parts=sorted(new-old),counts=counts,abstract_words=len(abstract.split()),body_source_words=len(content.split()),reference_order=[dict(number=cites[k],key=k,**REF[k]) for k in ref_order],native_math_elements=etree.fromstring(ZipFile(final).read('word/document.xml')).xpath('count(//m:oMath)',namespaces={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}),manuscript=str(final))
(B/'source/build_report.json').write_text(json.dumps(report,indent=2));(B/'source/numbered_references.json').write_text(json.dumps(report['reference_order'],indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['reference_order','added_parts']},indent=2))
