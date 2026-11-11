"""Build an IJ3C-format simulation review draft from audited saved results."""
import copy,hashlib,json,re
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches,Pt,RGBColor

B=Path(__file__).resolve().parents[1];ROOT=B.parent
REF=B/'template/IJ3C_Sample-file.docx'
NAMES={'proposed_v4':'V4','pso_polished':'PSO-P','aco_polished':'ACO-P','continuous_pso':'PSO-C',
       'proposed_v4_no_landmarks':'V4 noL','proposed_v4_no_polish':'V4 noP'}
ORDER=list(NAMES)


def main():
    analysis=json.loads((B/'results/study_analysis.json').read_text());assert analysis['state']=='passed'
    probe=json.loads((B/'results/realism_probe.json').read_text());assert probe['state']=='complete'
    corrected=json.loads((B/'results/corrected_gravity_probe.json').read_text());assert corrected['state']=='complete'
    probe['records']=[r for r in probe['records'] if r['gravity_compensation']]+corrected['records']
    model=json.loads((B/'results/model_audit.json').read_text())
    reference_hash=hashlib.sha256(REF.read_bytes()).hexdigest()
    assert reference_hash in (B/'artifact.md').read_text()
    summary={r['method']:r for r in analysis['primary_summary']};paired={r['baseline']:r for r in analysis['paired_comparisons']}
    fontdir=Path.home()/'.local/share/fonts/pathfinder-corefonts'
    for fontfile in fontdir.glob('*.TTF'):font_manager.fontManager.addfont(str(fontfile))
    assert font_manager.findfont('Times New Roman',fallback_to_default=False)
    plt.rcParams.update({'font.family':'Times New Roman','font.size':11,'axes.titlesize':11,'axes.labelsize':11,'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':11})
    fig,ax=plt.subplots(figsize=(3.1,2.3));values=[summary[m]['admitted'] for m in ORDER]
    bars=ax.barh(range(6),values,color=['#17686f']+['#7c96ae']*5);ax.set_yticks(range(6),[NAMES[m] for m in ORDER]);ax.invert_yaxis();ax.set_xlim(0,108);ax.set_xlabel('Admitted / 96 attempts')
    for bar,value in zip(bars,values):ax.text(value+1,bar.get_y()+bar.get_height()/2,str(value),va='center')
    fig.tight_layout();fig.savefig(B/'figures/fresh_admission.png',dpi=400);fig.savefig(B/'figures/fresh_admission.pdf');plt.close(fig)
    p=list(paired.values());fig,ax=plt.subplots(figsize=(3.1,3.0))
    for y,row in enumerate(p):
        mean=row['mean_improvement_percent'];lo=row['ci95_low'];hi=row['ci95_high']
        ax.errorbar(mean,y,xerr=[[max(0,mean-lo)],[max(0,hi-mean)]],fmt='o',color='#17686f',capsize=3)
    ax.axvline(0,color='grey',linewidth=.8);ax.set_yticks(range(len(p)),[NAMES[r['baseline']] for r in p]);ax.invert_yaxis();ax.set_xlabel('V4 paired Q improvement (%)');ax.grid(axis='x',alpha=.15)
    fig.tight_layout();fig.savefig(B/'figures/fresh_effects.png',dpi=400);fig.savefig(B/'figures/fresh_effects.pdf');plt.close(fig)
    # The first primary case and repeat are fixed independently of score effects.
    from matplotlib.patches import Rectangle
    primary=json.loads((B/'raw_study/primary.json').read_text());case=primary['cases'][0]
    fig,ax=plt.subplots(figsize=(3.1,3.0))
    for region in case['world']['patches']:
        x0,x1,y0,y1=region['bounds'];ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#dfb76e',alpha=.45,edgecolor='none'))
    for obstacle in case['world']['obstacles']:
        ax.add_patch(Rectangle((obstacle['x']-obstacle['sx'],obstacle['y']-obstacle['sy']),2*obstacle['sx'],2*obstacle['sy'],facecolor='#393939'))
    for method,color,ls,width in [('proposed_v4','#17686f','-',2.5),('continuous_pso','#a64b16','--',1.3)]:
        record=next(x for x in primary['records'] if x['case_id']==case['id'] and x['repeat']==0 and x['method']==method)
        points=np.asarray(record['plan']['points']);ax.plot(points[:,0],points[:,1],ls,color=color,linewidth=width,label=NAMES[method])
    ax.scatter(*case['start'],marker='o',color='black',s=24,zorder=5);ax.scatter(*case['goal'],marker='*',color='black',s=55,zorder=5)
    ax.set(xlim=(-24,24),ylim=(-24,24),xlabel='x (m)',ylabel='y (m)');ax.set_aspect('equal');ax.legend(loc='upper left',frameon=False);ax.grid(alpha=.15)
    fig.tight_layout();fig.savefig(B/'figures/primary_world.png',dpi=400);fig.savefig(B/'figures/primary_world.pdf');plt.close(fig)
    counts=[]
    for assistance,grav,label in [(1.,True,'Full + GC'),(.5,True,'Blend + GC'),(0.,True,'Zero + GC'),(0.,False,'Zero, no GC')]:
        rows=[r for r in probe['records'] if r['assistance']==assistance and r['gravity_compensation']==grav]
        executed=[r for r in rows if 'execution' in r];arrived=sum(r['execution']['outcome']=='arrived' for r in executed)
        counts.append(dict(label=label,scheduled=len(rows),executed=len(executed),arrived=arrived,outcomes={k:sum(r['execution']['outcome']==k for r in executed) for k in sorted({r['execution']['outcome'] for r in executed})}))
    q=paired['continuous_pso'];ablation=paired['proposed_v4_no_landmarks'];polish=paired['proposed_v4_no_polish']
    abstract=(f'This study evaluates waypoint representation and component removal in resource-constrained route planning for a simulated hexapod. '
        f'Six configurations share geometric clearance checks, mission limits and a distance, time, nominal battery and terrain score. '
        f'A locally frozen campaign comprises eight development worlds and 32 primary worlds, yielding 640 planning records. '
        f'The complete geometric refiner, V4, admits {summary["proposed_v4"]["admitted"]}/96 primary attempts; a continuous-coordinate particle swarm control admits {summary["continuous_pso"]["admitted"]}/96. '
        f'On joint admissions, V4 has a mean world-level score improvement of {q["mean_improvement_percent"]:.3f}%, a median of {q["median_improvement_percent"]:.3f}% and a descriptive 95% bootstrap interval of [{q["ci95_low"]:.3f}, {q["ci95_high"]:.3f}]%. '
        f'The interval spans zero. Removing landmarks retains 93 admissions; removing polishing reduces admissions to 90. '
        f'A separate diagnostic replays four archived missions under four assistance conditions. Full and reduced chassis assistance each complete all four missions; zero assistance times out on all four, with or without limb gravity compensation. '
        f'The findings quantify configuration-specific planning trade-offs and assistance dependence in the declared simulator. No physical robot performance or electrical energy saving is established.')
    assert len(abstract.split())<=250
    fresh=('All 640 scheduled records completed. Development selected the default profile for every base configuration. '
        f'V4, PSO-P, ACO-P and V4 noL each admit 93/96 primary attempts; PSO-C admits 94/96 and V4 noP admits 90/96. '
        'Table 2 reports admission and mean planner wall time; Figure 2 shows the admission counts. '
        f'V4 records a mean search time of {summary["proposed_v4"]["mean_planning_seconds"]:.3f} s, compared with {summary["continuous_pso"]["mean_planning_seconds"]:.3f} s for PSO-C. '
        'All non-admitted primary outcomes are resource rejections; no primary trial has an error status.')
    paired_text=(f'Against PSO-C, V4 has {q["wins"]} lower-score pairs, {q["ties"]} ties and {q["losses"]} higher-score pairs among joint admissions. '
        f'There are {q["proposal_only"]} V4-only admissions, {q["baseline_only"]} PSO-C-only admission and {q["both_rejected"]} mutual rejections. '
        f'The world-averaged score effect is {q["mean_improvement_percent"]:.3f}% with a descriptive 95% interval [{q["ci95_low"]:.3f}, {q["ci95_high"]:.3f}]%, based on {q["paired_worlds"]} worlds. '
        f'The median is {q["median_improvement_percent"]:.3f}%; world effects range from {q["minimum_world_improvement_percent"]:.3f}% to {q["maximum_world_improvement_percent"]:.3f}%, with {q["worlds_improved_over_0p5_percent"]}/31 above the declared 0.5% reference. '
        f'The mean effects against PSO-P and ACO-P are {paired["pso_polished"]["mean_improvement_percent"]:.3f}% and {paired["aco_polished"]["mean_improvement_percent"]:.3f}%, respectively, both with zero median. '
        f'The component comparisons yield mean effects of {ablation["mean_improvement_percent"]:.3f}% against V4 noL and {polish["mean_improvement_percent"]:.3f}% against V4 noP. '
        f'Against V4 noL, V4 has {ablation["wins"]} lower-score pairs, {ablation["ties"]} ties and {ablation["losses"]} higher-score pairs. '
        f'Against V4 noP, it has {polish["wins"]} lower-score pairs, {polish["ties"]} ties and {polish["losses"]} higher-score pairs, plus {polish["proposal_only"]} V4-only admissions. '
        'Table 3 and Figure 3 report the corresponding conditional mean effects and intervals.')
    probe_text=('Full assistance and 0.5 assistance each complete 4/4 missions. Both zero-assistance conditions time out on all four missions before the 180 s limit. '
        'GC in Table 4 denotes limb gravity compensation. A timeout records failure to complete the saved destination-and-return mission within the configured duration; it does not classify a fall. '
        'These outcomes apply to the four archived routes and do not estimate hardware failure rates.')
    audit=(f'An internal record audit reconciles all {analysis["records"]} records, checks {analysis["unique_routes_checked"]} distinct route geometries and recomputes {analysis["metric_values_recomputed"]} metric values without an error. '
        'It verifies trial keys, development selection, source/model hashes, endpoints, clearance and score/admission arithmetic. '
        'These checks establish consistency with the declared evaluator, not independent physical validation.')
    conclusion=(f'Under the frozen 32-world primary protocol, V4 admits 93/96 attempts and PSO-C admits 94/96. '
        f'The V4 paired mean score effect against PSO-C is {q["mean_improvement_percent"]:.3f}% with a zero median and an interval spanning zero; the campaign does not demonstrate a mean score advantage over that control. '
        'Polishing removal reduces admissions from 93 to 90, while landmark removal retains admission and lowers recorded search time at a small conditional score cost. '
        'All four archived diagnostic missions complete with full or reduced chassis assistance and time out after assistance removal.')
    refs=json.loads((B/'source/references.json').read_text())
    keys=['mujoco','astar','pso','aco','visibility','smartgait','terrain','cocoprocedure','bootstrap']
    references='\n\n'.join(f'[{i}] {refs[k]["text"]}' for i,k in enumerate(keys,1))
    texts=dict(AUTHORS='[Author names and affiliations]\n[Corresponding author email]',ABSTRACT=abstract,
        FRESH_RESULTS=fresh,PAIRED_RESULTS=paired_text,PROBE_RESULTS=probe_text,AUDIT_RESULTS=audit,CONCLUSION_RESULTS=conclusion,REFERENCES=references)
    tables={
        'TABLE_MODEL':('Table 1. Declared source and simulation parameters.',[['Parameter','Source URDF','MuJoCo assembly'],['Total mass (kg)','97.52','113.32'],['Base mass (kg)','35.00','46.00'],['Leg joints','18','18'],['Added mechanisms','No wheel joints','Wheels and scanner']]),
        'TABLE_PRIMARY':('Table 2. Primary admission and mean planner wall time.',[['Method','Admitted / 96','Mean time (s)']]+[[NAMES[m],str(summary[m]['admitted']),f'{summary[m]["mean_planning_seconds"]:.3f}'] for m in ORDER]),
        'TABLE_PAIRED':('Table 3. V4 score effects; n is the paired world count.',[['Control','n','Mean (%)','95% interval (%)']]+[[NAMES[r['baseline']],str(r['paired_worlds']),f'{r["mean_improvement_percent"]:.3f}',f'[{r["ci95_low"]:.3f}, {r["ci95_high"]:.3f}]'] for r in p]),
        'TABLE_PROBE':('Table 4. Diagnostic replay outcomes on observed routes.',[['Condition','Arrived / 4','Timeout / 4']]+[[c['label'],str(c['arrived']),str(c['outcomes'].get('timeout',0))] for c in counts])}
    figures={'FIG_MODEL':('primary_world.png','Figure 1. First primary world, seed 2140000, repetition 0. Circles and stars mark start and goal; black blocks are obstacles and amber regions are terrain patches. Coincident route segments overlap.'),
             'FIG_PRIMARY':('fresh_admission.png','Figure 2. Primary admission counts across all scheduled attempts.'),
             'FIG_EFFECTS':('fresh_effects.png','Figure 3. Conditional V4 score effects and descriptive 95% intervals. Positive values favor V4.')}
    from extended_content import expand
    expand(B,texts,tables,figures)
    from plain_content import rewrite
    rewrite(B,texts,tables,figures)
    from add_overview import insert
    insert(B,texts,figures)
    abstract=texts['ABSTRACT']
    template=(B/'source/article.md').read_text()
    for key,value in texts.items():template=template.replace('{{'+key+'}}',value)
    assembled=template
    for key,(caption,data) in tables.items():
        md=caption+'\n\n'+'\n'.join('| '+' | '.join(row)+' |' for row in [data[0],['---']*len(data[0]),*data[1:]])
        assembled=assembled.replace('{{'+key+'}}',md)
    for key,(name,caption) in figures.items():assembled=assembled.replace('{{'+key+'}}',f'![{caption}](figures/{name})\n\n{caption}')
    formulas={'EQ_SCORE':r'Q(P)=D/50+T/90+E/30+R/80',
              'EQ_BATTERY':r'B_{\mathrm{req}}=1.25(E+E_{\mathrm{return}})+6',
              'EQ_EFFECT':r'\delta=100(Q_c-Q_v)/Q_c'}
    for i,(key,formula) in enumerate(formulas.items(),1):
        assembled=assembled.replace('{{'+key+'}}','$$'+formula+r'\qquad ('+str(i)+')$$')
    (B/'IJ3C_Manuscript.md').write_text(assembled+'\n')
    doc=Document(REF)
    # Clear all sample running content before replacing its body/sections.
    for section in doc.sections:
        for box in [section.header,section.footer,section.first_page_header,section.first_page_footer,section.even_page_header,section.even_page_footer]:
            for paragraph in box.paragraphs:paragraph.clear()
    body=doc._element.body
    for child in list(body):
        if child.tag!=qn('w:sectPr'):body.remove(child)
    for name in ['Normal','Body Text','Abstract Text','Author','Title','Heading 1','Heading 2','Caption']:
        if name not in doc.styles:
            created=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH);created.base_style=doc.styles['Normal']
        style=doc.styles[name];style.font.name='Times New Roman';style.font.size=Pt(10);style.font.color.rgb=RGBColor(0,0,0);style.font.italic=False
        style.paragraph_format.line_spacing=1;style.paragraph_format.space_before=Pt(0);style.paragraph_format.space_after=Pt(4)
        rpr=style.element.get_or_add_rPr()
        for tag in ['spacing','kern']:
            for element in list(rpr.findall(qn('w:'+tag))):rpr.remove(element)
    doc.styles['Title'].font.size=Pt(16);doc.styles['Title'].font.bold=True
    doc.styles['Author'].font.size=Pt(11)
    doc.styles['Caption'].paragraph_format.keep_together=True
    for name,size in [('Heading 1',11),('Heading 2',10.5)]:
        doc.styles[name].font.size=Pt(size);doc.styles[name].font.bold=True
        doc.styles[name].paragraph_format.space_before=Pt(8);doc.styles[name].paragraph_format.keep_with_next=True
    def section_setup(s,n):
        s.page_width=Inches(8.2681);s.page_height=Inches(11.6931)
        s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Inches(.9847)
        s.header_distance=Inches(.38);s.footer_distance=Inches(.38)
        cols=s._sectPr.find(qn('w:cols'))
        if cols is None:cols=OxmlElement('w:cols');s._sectPr.append(cols)
        cols.set(qn('w:num'),str(n));cols.set(qn('w:space'),'424')
        for child in list(cols):cols.remove(child)
        for tag in ['docGrid','pgNumType']:
            for e in list(s._sectPr.findall(qn('w:'+tag))):s._sectPr.remove(e)
    section_setup(doc.sections[0],1)
    title=template.splitlines()[0][2:];p=doc.add_paragraph(title,'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=doc.add_paragraph(texts['AUTHORS'],'Author');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),2)
    for s in doc.sections:
        s.different_first_page_header_footer=False
        hp=s.header.paragraphs[0];hp.text='';hp.style=doc.styles['Normal']
        fp=s.footer.paragraphs[0];fp.clear();fp.style=doc.styles['Normal'];fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');run=OxmlElement('w:r');t=OxmlElement('w:t');t.text='1';run.append(t);field.append(run);fp._p.append(field)
    settings=doc.settings.element
    math_properties=OxmlElement('m:mathPr');math_font=OxmlElement('m:mathFont');math_font.set(qn('m:val'),'Times New Roman');math_properties.append(math_font);settings.append(math_properties)
    for element in list(settings.iter(qn('w:evenAndOddHeaders'))):element.getparent().remove(element)
    for element in list(settings.iter(qn('w:doNotBalanceTextColumns'))):element.getparent().remove(element)
    update=settings.find(qn('w:updateFields'))
    if update is None:update=OxmlElement('w:updateFields');settings.append(update)
    update.set(qn('w:val'),'true')
    def paragraph(text,style='Body Text'):
        p=doc.add_paragraph(text,style);p.paragraph_format.widow_control=True
        if style=='Body Text':p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;p.paragraph_format.first_line_indent=Inches(.14)
        return p
    def table(caption,rows):
        number=int(caption.split('.')[0].split()[-1])
        widths={1:[1.0,1.0,1.0],2:[1.05,.95,1.0],3:[.60,.25,.55,1.60],4:[.70,.48,.60,.52,.70],5:[.65,.55,.55,.70,.55],6:[.60,.25,1.10,1.05],7:[1.40,.80,.80],8:[1.30,.85,.85],9:[1.15,.75,1.10]}[number]
        cp=paragraph(caption,'Caption');cp.paragraph_format.keep_with_next=True
        t=doc.add_table(rows=1,cols=len(rows[0]));t.autofit=False
        for column,w in zip(t.columns,widths):column.width=Inches(w)
        width=t._tbl.tblPr.find(qn('w:tblW'));width.set(qn('w:type'),'dxa');width.set(qn('w:w'),'4320')
        for i,text in enumerate(rows[0]):t.rows[0].cells[i].text=text
        for row in rows[1:]:
            cells=t.add_row().cells
            for cell,text in zip(cells,row):cell.text=text
        for row_index,row in enumerate(t.rows):
            for cell_index,cell in enumerate(row.cells):
                cell.width=Inches(widths[cell_index])
                tcpr=cell._tc.get_or_add_tcPr();borders=OxmlElement('w:tcBorders')
                for edge in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
                tcpr.append(borders)
                margins=OxmlElement('w:tcMar')
                for side in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+side);e.set(qn('w:w'),'55');e.set(qn('w:type'),'dxa');margins.append(e)
                tcpr.append(margins)
                for p in cell.paragraphs:
                    p.style=doc.styles['Normal'];p.paragraph_format.space_after=Pt(2);p.paragraph_format.space_before=Pt(2)
                    p.paragraph_format.keep_together=True;p.paragraph_format.keep_with_next=row_index<len(t.rows)-1
        trpr=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
        for cell in t.rows[0].cells:
            shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E7EDF0');cell._tc.get_or_add_tcPr().append(shade)
            for run in cell.paragraphs[0].runs:run.bold=True
        paragraph('','Normal')
    def equation(value,number):
        p=paragraph('','Normal');p.paragraph_format.tab_stops.add_tab_stop(Inches(1.40),WD_TAB_ALIGNMENT.CENTER);p.paragraph_format.tab_stops.add_tab_stop(Inches(3.0),WD_TAB_ALIGNMENT.RIGHT);p.add_run('\t')
        mathp=OxmlElement('m:oMath')
        def run(parent,text,roman=False):
            mr=OxmlElement('m:r');props=OxmlElement('m:rPr');sty=OxmlElement('m:sty');sty.set(qn('m:val'),'p' if roman else 'i');props.append(sty);mr.append(props)
            wp=OxmlElement('w:rPr');font=OxmlElement('w:rFonts');font.set(qn('w:ascii'),'Times New Roman');font.set(qn('w:hAnsi'),'Times New Roman');wp.append(font);size=OxmlElement('w:sz');size.set(qn('w:val'),'20');wp.append(size);mr.append(wp)
            mt=OxmlElement('m:t');mt.text=text;mr.append(mt);parent.append(mr)
        def sub(parent,base,index):
            e=OxmlElement('m:sSub');base_e=OxmlElement('m:e');run(base_e,base);e.append(base_e);sub_e=OxmlElement('m:sub');run(sub_e,index,True);e.append(sub_e);parent.append(e)
        def fraction(parent,numerator,denominator):
            e=OxmlElement('m:f');n=OxmlElement('m:num');d=OxmlElement('m:den');run(n,numerator);run(d,denominator,True);e.append(n);e.append(d);parent.append(e)
        if number=='1':
            run(mathp,'Q(P) = ')
            for i,(top,bottom) in enumerate([('D','50'),('T','90'),('E','30'),('R','80')]):
                if i:run(mathp,' + ',True)
                fraction(mathp,top,bottom)
        elif number=='2':
            sub(mathp,'B','req');run(mathp,' = 1.25(',True);run(mathp,'E');run(mathp,' + ',True);sub(mathp,'E','return');run(mathp,') + 6',True)
        else:
            run(mathp,'δ = 100 ',True)
            frac=OxmlElement('m:f');num=OxmlElement('m:num');den=OxmlElement('m:den');sub(num,'Q','c');run(num,' - ',True);sub(num,'Q','v');sub(den,'Q','c');frac.append(num);frac.append(den);mathp.append(frac)
        p._p.append(mathp);p.add_run(f'\t({number})')
    for block in template.split('\n\n')[2:]:
        block=block.strip()
        if not block or block==texts['AUTHORS']:continue
        if block.startswith('### '):paragraph(block[4:],'Heading 2')
        elif block.startswith('## '):paragraph(block[3:],'Heading 1')
        elif block in ['{{'+k+'}}' for k in tables]:table(*tables[block[2:-2]])
        elif block in ['{{'+k+'}}' for k in figures]:
            key=block[2:-2];name,caption=figures[key]
            if key=='FIG_OVERVIEW':section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),1)
            p=paragraph('','Normal');p.paragraph_format.keep_with_next=True
            if key=='FIG_OVERVIEW':p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            picture=p.add_run().add_picture(str(B/'figures'/name),width=Inches(6.0 if key=='FIG_OVERVIEW' else 3.0))
            picture._inline.docPr.set('descr',caption)
            paragraph(caption,'Caption')
            if key=='FIG_OVERVIEW':section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),2)
        elif block=='{{EQ_SCORE}}':equation('Q(P) = wᵀ [D, T, E, R]','1')
        elif block=='{{EQ_BATTERY}}':equation('B_req = 1.25(E + E_return) + 6','2')
        elif block=='{{EQ_EFFECT}}':equation('delta = 100 (Q_c - Q_v) / Q_c','3')
        elif re.match(r'^\[\d+\]',block):
            rp=paragraph(block);rp.alignment=WD_ALIGN_PARAGRAPH.LEFT;rp.paragraph_format.left_indent=Inches(.15);rp.paragraph_format.first_line_indent=Inches(-.15);rp.paragraph_format.keep_together=True
        else:paragraph(block)
    # An empty continuous terminator balances the final article columns.
    section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),2)
    doc.core_properties.title=title;doc.core_properties.author='';doc.core_properties.last_modified_by='' 
    doc.core_properties.subject='Comparative simulation study of waypoint representations and chassis assistance'
    temp=B/'qa/authored_working.docx';doc.save(temp)
    final=B/'IJ3C_Manuscript.docx'
    allowed={'word/document.xml','word/styles.xml','word/settings.xml','word/_rels/document.xml.rels','[Content_Types].xml','docProps/core.xml','docProps/app.xml'}
    preserved=[];changes=[]
    from lxml import etree
    import posixpath
    with ZipFile(REF) as src,ZipFile(temp) as authored:
        originals=set(src.namelist());outputs=set(authored.namelist());parts={}
        for name in src.namelist():
            permitted=name in allowed or re.fullmatch(r'word/(header|footer)\d+\.xml',name)
            parts[name]=authored.read(name) if permitted and name in outputs else src.read(name)
        for name in outputs-originals:parts[name]=authored.read(name)
        document=etree.fromstring(parts['word/document.xml'])
        rns='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
        usedids={value for element in document.iter() for attr,value in element.attrib.items() if attr.startswith('{'+rns+'}')}
        rels=etree.fromstring(parts['word/_rels/document.xml.rels']);deleted=[]
        for rel in list(rels):
            kind=rel.get('Type').rsplit('/',1)[-1]
            if kind in {'image','hyperlink'} and rel.get('Id') not in usedids:
                if rel.get('TargetMode')!='External':
                    target=posixpath.normpath('word/'+rel.get('Target'))
                    if target in parts:parts.pop(target);deleted.append(target)
                rels.remove(rel)
        parts['word/_rels/document.xml.rels']=etree.tostring(rels,xml_declaration=True,encoding='UTF-8',standalone=True)
        # Unreferenced sample author footnotes are not article content.
        for name in ['word/footnotes.xml','word/endnotes.xml']:
            if name not in parts:continue
            node=etree.fromstring(parts[name])
            for child in list(node):
                if child.get(qn('w:type')) not in {'separator','continuationSeparator'}:node.remove(child)
            parts[name]=etree.tostring(node,xml_declaration=True,encoding='UTF-8',standalone=True)
        types=etree.fromstring(parts['[Content_Types].xml'])
        for child in list(types):
            if child.get('PartName','').lstrip('/') in deleted:types.remove(child)
        parts['[Content_Types].xml']=etree.tostring(types,xml_declaration=True,encoding='UTF-8',standalone=True)
        for name in originals:
            if name not in parts:continue
            if parts[name]==src.read(name):preserved.append(name)
            else:changes.append(name)
        with ZipFile(final,'w',ZIP_DEFLATED) as dest:
            for name,blob in parts.items():dest.writestr(name,blob)
    with ZipFile(final) as z:
        assert z.testzip() is None
        assert not re.search(r'\{\{[A-Z_]+\}\}',z.read('word/document.xml').decode())
    (B/'qa/build_report.json').write_text(json.dumps(dict(reference_sha256=reference_hash,reference_unchanged=hashlib.sha256(REF.read_bytes()).hexdigest()==reference_hash,
        preserve_only_parts_checked=len(preserved),changed_parts=changes,removed_unused_sample_parts=deleted,abstract_words=len(abstract.split()),approximate_manuscript_words=len(assembled.split()),
        figures=len(figures),tables=len(tables),equations=3,references=len(keys),author_details='Pending at user request',stage='Review draft; no submission',scope='A4 25 mm margins, continuous two-column body, >=10 pt Times New Roman; source sample character-spacing corruption repaired.'),indent=2)+'\n')
    assert len(assembled.split())<10000
    print(final)


if __name__=='__main__':main()
