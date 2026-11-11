"""Build an IJ3C-format simulation review draft from audited saved results."""
import copy,hashlib,json,re
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    model=json.loads((B/'results/model_audit.json').read_text())
    reference_hash=hashlib.sha256(REF.read_bytes()).hexdigest()
    assert reference_hash in (B/'artifact.md').read_text()
    summary={r['method']:r for r in analysis['primary_summary']};paired={r['baseline']:r for r in analysis['paired_comparisons']}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':10,'axes.labelsize':10,'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':10})
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
    counts=[]
    for assistance,grav,label in [(1.,True,'Full + GC'),(.5,True,'Blend + GC'),(0.,True,'Zero + GC'),(0.,False,'Zero, no GC')]:
        rows=[r for r in probe['records'] if r['assistance']==assistance and r['gravity_compensation']==grav]
        executed=[r for r in rows if 'execution' in r];arrived=sum(r['execution']['outcome']=='arrived' for r in executed)
        counts.append(dict(label=label,scheduled=len(rows),executed=len(executed),arrived=arrived,outcomes={k:sum(r['execution']['outcome']==k for r in executed) for k in sorted({r['execution']['outcome'] for r in executed})}))
    q=paired['continuous_pso'];ablation=paired['proposed_v4_no_landmarks'];polish=paired['proposed_v4_no_polish']
    abstract=(f'Route-planning comparisons can confound search behavior with waypoint representation and simulation assistance. '
        f'This study evaluates a resource-constrained hexapod route-planning integration using a common distance, time, nominal battery and terrain score. '
        f'A locally frozen prospective campaign contains eight development worlds, 32 fresh primary worlds, six configurations and 640 planning records. '
        f'A continuous-coordinate particle swarm control and two component removals supplement polished swarm baselines. '
        f'The retained V4 configuration admits {summary["proposed_v4"]["admitted"]}/96 primary attempts. '
        f'The coordinate control admits {summary["continuous_pso"]["admitted"]}/96. '
        f'V4\'s mean world-level score improvement over the continuous-coordinate control is {q["mean_improvement_percent"]:.3f}% on jointly admitted cases, with median {q["median_improvement_percent"]:.3f}%. '
        f'The descriptive 95% interval [{q["ci95_low"]:.3f}, {q["ci95_high"]:.3f}]% includes zero. '
        f'An independent numeric and geometry audit checks all records. A separate 16-execution diagnostic examines chassis-assistance removal on four previously observed routes. '
        f'The source and simulated assemblies have different modeled masses, and electrical parameters remain uncalibrated. '
        f'The findings characterize a bounded engineering integration and its component trade-offs; they do not establish real battery savings or unassisted hardware locomotion.')
    assert len(abstract.split())<=250
    fresh=(f'All 640 scheduled planning records completed. The frozen profile choices were '+', '.join(f'{NAMES[k]}: {v}' for k,v in analysis['selected_profiles'].items())+'. '
        'Table 2 reports admission and per-method search time; Figure 2 shows admission counts. V4 noL removes landmark diversification and V4 noP removes polishing. PSO-P and ACO-P are the existing polished controls; PSO-C is the added continuous-coordinate control. '
        f'V4 admits {summary["proposed_v4"]["admitted"]}/96 attempts with mean search time {summary["proposed_v4"]["mean_planning_seconds"]:.3f} s. '
        f'PSO-C admits {summary["continuous_pso"]["admitted"]}/96 with mean search time {summary["continuous_pso"]["mean_planning_seconds"]:.3f} s. '
        'The coordinate control therefore admits one more primary attempt than V4 in this campaign. '
        'These are observed configuration-specific outcomes, not a claim about every implementation of either algorithm family.')
    paired_text=(f'Against PSO-C, V4 has {q["wins"]} lower-score pairs, {q["ties"]} ties and {q["losses"]} higher-score pairs among joint admissions. '
        f'The remaining categories are {q["proposal_only"]} V4-only admissions, {q["baseline_only"]} PSO-C-only admissions and {q["both_rejected"]} mutual rejections. '
        f'The world-averaged effect is {q["mean_improvement_percent"]:.3f}% (descriptive 95% interval [{q["ci95_low"]:.3f}, {q["ci95_high"]:.3f}]%), based on {q["paired_worlds"]} paired worlds. '
        f'The median is {q["median_improvement_percent"]:.3f}%; {q["worlds_improved_over_0p5_percent"]} paired worlds exceed the declared 0.5% reference. '
        f'World effects range from {q["minimum_world_improvement_percent"]:.3f}% to {q["maximum_world_improvement_percent"]:.3f}%. '
        'The interval against PSO-C spans zero, so this sample does not establish a reliable nonzero mean score advantage over that control. '
        f'Against V4 noL the mean effect is {ablation["mean_improvement_percent"]:.3f}% and against V4 noP it is {polish["mean_improvement_percent"]:.3f}%. '
        'Positive effects favor complete V4; negative effects favor the control. Table 3 retains the full intervals, including intervals spanning zero, and Figure 3 displays their direction. Component benefits must be interpreted on this new sample rather than inferred from the method name.')
    probe_text=('Table 4 separates completed routes from the conditions actually executed. '+
        '; '.join(f'{c["label"]}: {c["arrived"]}/{c["scheduled"]} arrived, outcomes {c["outcomes"]}' for c in counts)+'. '
        'GC denotes ideal limb gravity compensation. Timeouts mean the saved complete mission did not arrive within 180 simulated seconds, not necessarily that the robot fell. This diagnostic was conducted on already observed routes and cannot estimate general real-world failure rates. Nevertheless, a completion difference under assistance removal shows that assisted results cannot be treated as equivalent evidence for autonomous dynamic locomotion.')
    audit=(f'The new audit passes {analysis["records"]} records, checks {analysis["unique_routes_checked"]} distinct route geometries and recomputes {analysis["metric_values_recomputed"]} metric values with no reported errors. '
        'It also checks trial keys, frozen development selection, source snapshots, model hashes, endpoints and common score/admission arithmetic. The software verification log records 63 passing test executions, including imported existing cases and three new representation checks. No trial was removed to improve the reported result.')
    conclusion=(f'On 32 fresh generated primary worlds, V4 admits {summary["proposed_v4"]["admitted"]}/96 attempts. '
        f'The paired mean effect against the continuous-coordinate control is {q["mean_improvement_percent"]:.3f}%, with median {q["median_improvement_percent"]:.3f}%. '
        f'The component comparisons yield mean effects of {ablation["mean_improvement_percent"]:.3f}% against removal of landmarks and {polish["mean_improvement_percent"]:.3f}% against removal of polishing. '
        'These measured trade-offs and the assistance diagnostic constrain the claims that can be made from the simulator. Further algorithmic or physical conclusions require a separately designed evaluation addressing the corresponding limitation.')
    refs=json.loads((B/'source/references.json').read_text())
    keys=['mujoco','astar','pso','aco','visibility','martins','ompl','rrtstar','smartgait','terrain','coco','demsar']
    references='\n\n'.join(f'[{i}] {refs[k]["text"]}' for i,k in enumerate(keys,1))
    texts=dict(AUTHORS='[Author names, affiliations and corresponding email pending confirmation]',ABSTRACT=abstract,
        FRESH_RESULTS=fresh,PAIRED_RESULTS=paired_text,PROBE_RESULTS=probe_text,AUDIT_RESULTS=audit,CONCLUSION_RESULTS=conclusion,REFERENCES=references)
    tables={
        'TABLE_MODEL':('Table 1. Declared source and simulation parameters.',[['Parameter','Source URDF','MuJoCo assembly'],['Total mass (kg)','97.52','113.32'],['Base mass (kg)','35.00','46.00'],['Leg joints','18','18'],['Added mechanisms','No wheel joints','Wheels and scanner']]),
        'TABLE_PRIMARY':('Table 2. S4 admission and mean planner wall time.',[['Method','Admitted / 96','Mean time (s)']]+[[NAMES[m],str(summary[m]['admitted']),f'{summary[m]["mean_planning_seconds"]:.3f}'] for m in ORDER]),
        'TABLE_PAIRED':('Table 3. V4 relative score effects on joint admissions.',[['Control','Mean (%)','95% interval (%)']]+[[NAMES[r['baseline']],f'{r["mean_improvement_percent"]:.3f}',f'[{r["ci95_low"]:.3f}, {r["ci95_high"]:.3f}]'] for r in p]),
        'TABLE_PROBE':('Table 4. Diagnostic replay outcomes on observed routes.',[['Condition','Arrived / scheduled','Executed']]+[[c['label'],f'{c["arrived"]}/{c["scheduled"]}',str(c['executed'])] for c in counts])}
    figures={'FIG_MODEL':('live_demo_scene.jpg','Figure 1. Existing assisted hybrid demonstration, illustrative only; controlled planner experiments use walking.'),
             'FIG_PRIMARY':('fresh_admission.png','Figure 2. Fresh S4 primary admission counts; all scheduled attempts retained.'),
             'FIG_EFFECTS':('fresh_effects.png','Figure 3. V4 paired world-level effects and descriptive 95% intervals. Positive values favor V4.')}
    template=(B/'source/article.md').read_text()
    for key,value in texts.items():template=template.replace('{{'+key+'}}',value)
    assembled=template
    for key,(caption,data) in tables.items():
        md=caption+'\n\n'+'\n'.join('| '+' | '.join(row)+' |' for row in [data[0],['---']*len(data[0]),*data[1:]])
        assembled=assembled.replace('{{'+key+'}}',md)
    for key,(name,caption) in figures.items():assembled=assembled.replace('{{'+key+'}}',f'![{caption}](figures/{name})\n\n{caption}')
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
    p=doc.add_paragraph('Simulation-only review draft prepared 4 November 2026. Not submitted.');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),2)
    for s in doc.sections:
        s.different_first_page_header_footer=False
        hp=s.header.paragraphs[0];hp.text='Simulation study | Author review draft';hp.style=doc.styles['Normal']
        fp=s.footer.paragraphs[0];fp.clear();fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
        field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');run=OxmlElement('w:r');t=OxmlElement('w:t');t.text='1';run.append(t);field.append(run);fp._p.append(field)
    settings=doc.settings.element
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
        cp=paragraph(caption,'Caption');cp.paragraph_format.keep_with_next=True
        t=doc.add_table(rows=1,cols=len(rows[0]));t.autofit=False
        for column in t.columns:column.width=Inches(3.0/len(rows[0]))
        width=t._tbl.tblPr.find(qn('w:tblW'));width.set(qn('w:type'),'dxa');width.set(qn('w:w'),'4320')
        for i,text in enumerate(rows[0]):t.rows[0].cells[i].text=text
        for row in rows[1:]:
            cells=t.add_row().cells
            for cell,text in zip(cells,row):cell.text=text
        for row_index,row in enumerate(t.rows):
            for cell in row.cells:
                cell.width=Inches(3.0/len(rows[0]))
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
        p=paragraph('','Normal');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        mathp=OxmlElement('m:oMath');mr=OxmlElement('m:r');mt=OxmlElement('m:t');mt.text=value;mr.append(mt);mathp.append(mr);p._p.append(mathp)
        p.add_run(f'   ({number})')
    for block in template.split('\n\n')[2:]:
        block=block.strip()
        if not block or block==texts['AUTHORS']:continue
        if block.startswith('### '):paragraph(block[4:],'Heading 2')
        elif block.startswith('## '):paragraph(block[3:],'Heading 1')
        elif block in ['{{'+k+'}}' for k in tables]:table(*tables[block[2:-2]])
        elif block in ['{{'+k+'}}' for k in figures]:
            name,caption=figures[block[2:-2]];p=paragraph('','Normal');p.paragraph_format.keep_with_next=True;p.add_run().add_picture(str(B/'figures'/name),width=Inches(3.0));paragraph(caption,'Caption')
        elif block=='{{EQ_SCORE}}':equation('Q(P) = wᵀ [D, T, E, R]','1')
        elif block=='{{EQ_BATTERY}}':equation('B_req = 1.25(E + E_return) + 6','2')
        else:paragraph(block)
    # An empty continuous terminator balances the final article columns.
    section_setup(doc.add_section(WD_SECTION_START.CONTINUOUS),2)
    doc.core_properties.title=title;doc.core_properties.author='';doc.core_properties.last_modified_by='Research revision tools'
    doc.core_properties.subject='IJ3C-format simulation review draft; authors pending; no hardware claims'
    temp=B/'qa/authored_working.docx';doc.save(temp)
    final=B/'IJ3C_Hexapod_Review_Draft.docx'
    allowed={'word/document.xml','word/styles.xml','word/settings.xml','word/_rels/document.xml.rels','[Content_Types].xml','docProps/core.xml','docProps/app.xml'}
    preserved=[];changes=[]
    with ZipFile(REF) as src,ZipFile(temp) as authored,ZipFile(final,'w',ZIP_DEFLATED) as dest:
        originals=set(src.namelist());outputs=set(authored.namelist())
        for name in src.namelist():
            permitted=name in allowed or re.fullmatch(r'word/(header|footer)\d+\.xml',name)
            blob=authored.read(name) if permitted and name in outputs else src.read(name)
            dest.writestr(name,blob)
            if blob==src.read(name):preserved.append(name)
            else:changes.append(name)
        for name in outputs-originals:dest.writestr(name,authored.read(name))
    with ZipFile(final) as z:
        assert z.testzip() is None
        assert not re.search(r'\{\{[A-Z_]+\}\}',z.read('word/document.xml').decode())
    (B/'qa/build_report.json').write_text(json.dumps(dict(reference_sha256=reference_hash,reference_unchanged=hashlib.sha256(REF.read_bytes()).hexdigest()==reference_hash,
        preserve_only_parts_checked=len(preserved),changed_parts=changes,abstract_words=len(abstract.split()),approximate_manuscript_words=len(assembled.split()),
        figures=3,tables=4,equations=2,references=len(keys),author_details='Pending at user request',stage='Review draft; no submission',scope='A4 25 mm margins, continuous two-column body, >=10 pt Times New Roman; source sample character-spacing corruption repaired.'),indent=2)+'\n')
    assert len(assembled.split())<10000
    print(final)


if __name__=='__main__':main()
