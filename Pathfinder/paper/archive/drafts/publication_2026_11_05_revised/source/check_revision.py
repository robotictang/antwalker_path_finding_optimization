"""Reconcile the revised displays and preserved evidence; no simulations run."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
from docx import Document

B=Path(__file__).resolve().parents[1]
OLD=B.parent/'publication_2026_11_04_robot_figure'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((B/'qa/baseline_hashes.json').read_text())
for name,digest in base.items():
    assert sha(OLD/name)==digest,name
    if name.startswith(('raw_study/','results/')):assert sha(B/name)==digest,name
summary=json.loads((B/'results/study_analysis.json').read_text())
expanded=json.loads((B/'results/expanded_analysis.json').read_text())
methods=['proposed_v4','pso_polished','aco_polished','continuous_pso','proposed_v4_no_landmarks','proposed_v4_no_polish']
names=dict(zip(methods,['V4','PSO-P','ACO-P','PSO-C','V4 noL','V4 noP']))
doc=Document(B/'IJ3C_Manuscript.docx')
rows=lambda t:[[c.text for c in r.cells] for r in t.rows]
tables=[rows(t) for t in doc.tables]
assert len(tables)==5
s={r['method']:r for r in summary['primary_summary']}
assert tables[1][1:]==[[names[m],str(s[m]['admitted']),f"{s[m]['mean_planning_seconds']:.3f}"] for m in methods]
p=summary['paired_comparisons']
assert tables[2][1:]==[[names[r['baseline']],str(r['paired_worlds']),f"{r['mean_improvement_percent']:.3f}",f"[{r['ci95_low']:.3f}, {r['ci95_high']:.3f}]"] for r in p]
assert tables[3][1:]==[[names[r['method']],f"{r['median_seconds']:.3f}",f"{r['maximum_seconds']:.3f}",f"{r['median_evaluations']:g}",str(r['at_ceiling'])] for r in expanded['computation']]
def rng(v,d=3):return f'{v[0]:.{d}f}' if abs(v[0]-v[1])<10**(-d-1) else f'{v[0]:.{d}f}–{v[1]:.{d}f}'
for cells,c in zip(tables[4][1:],expanded['diagnostic_conditions']):
    assert cells[1:]==[str(c['arrived']),rng(c['mean_contact_range']),rng([100*x for x in c['no_contact_range']],2)]
text=' '.join(p.text for p in doc.paragraphs)
assert 'Algorithm 1.' in text and 'noP removes only the final adjustment stage' in text
assert '−0.060%' in text and '23.202%' in text
assert 'Four preliminary runs' in text and 'verified removal' in text
assert 'with compensation' in text or 'with leg gravity compensation' in text
assert sha(B/'figures/simulation_overview.png')==sha(OLD/'figures/simulation_overview.png')
with ZipFile(B/'IJ3C_Manuscript.docx') as z:
    matches=[f for f in z.namelist() if f.startswith('word/media/') and hashlib.sha256(z.read(f)).hexdigest()==sha(B/'figures/simulation_overview.png')]
    assert len(matches)==1
assert len(doc.inline_shapes)==3
report={'state':'passed','preserved_evidence_and_prior_manuscript_hashes':len(base),'numeric_tables_reconciled':4,'figures':3,'tables':5,'robot_image_original_bytes_embedded_once':True,'new_experiments':0,'docx_sha256':sha(B/'IJ3C_Manuscript.docx'),'scope':'Editorial revision of unchanged evidence; raw-data reconciliation, not hardware validation.'}
(B/'qa/revision_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
