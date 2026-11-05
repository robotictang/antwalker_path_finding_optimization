"""Check self-contained wording and the retained map-specific evidence."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,re,statistics
from lxml import etree
B=Path(__file__).resolve().parents[1]
text=(B/'IJ3C_Manuscript.md').read_text();body=text.split('## References')[0]
patterns=[r'\barchiv(?:e|ed)\b',r'\bmanifest\b',r'\bchecksum\b',r'\bsupplement(?:ary|al)?\b',r'\bsaved (?:files?|records?|routes?)\b',r'\blocal files?\b',r'\bworking directory\b',r'\brepository\b',r'\bsource snapshots?\b',r'\bsupplied input\b',r'/home/',r'\.json\b',r'\.xml\b',r'\b(?:maybe|perhaps|might|probably|possibly|presumably|guess|uncertain)\b']
for pattern in patterns:assert not re.search(pattern,body,re.I),pattern
assert 'Data and code availability' not in body
raw=json.loads((B/'raw_study/primary.json').read_text());first=raw['cases'][0]
first_routes=[next(r['plan']['points'] for r in raw['records'] if r['case_id']==first['id'] and r['method']==m and r['repeat']==0) for m in ['proposed_v4','continuous_pso']]
assert first_routes[0]==first_routes[1] and len(first_routes[0])==2
case=raw['cases'][23];assert case['seed']==2140023 and case['world']['family']=='corridor'
a=json.loads((B/'results/map24_analysis.json').read_text());assert a['case']==case['id']
rows={m:sorted([r for r in raw['records'] if r['case_id']==case['id'] and r['method']==m],key=lambda r:r['repeat']) for m in ['proposed_v4','continuous_pso']}
v=rows['proposed_v4'];c=rows['continuous_pso'];assert all(r['plan']['admissible'] for r in v+c)
assert v[0]['plan']['points']==v[1]['plan']['points']==v[2]['plan']['points']
for key in ['distance_m','estimated_seconds','energy_percent','terrain_exposure']:
 for left,right in zip(v,c):assert left['plan']['metrics'][key]<right['plan']['metrics'][key]
 for method,group in rows.items():assert abs(statistics.mean(r['plan']['metrics'][key] for r in group)-a['means'][method][key])<1e-12
for method,group in rows.items():assert abs(statistics.mean(r['plan']['quality_score'] for r in group)-a['means'][method]['quality_score'])<1e-12
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(B/'IJ3C_Manuscript.docx') as z:
 root=etree.fromstring(z.read('word/document.xml'));paragraphs=[''.join(p.xpath('.//w:t/text()',namespaces=ns)) for p in root.xpath('//w:body/w:p',namespaces=ns)]
 for kind,n in [('Figure',3),('Table',5)]:
  numbers=[int(m.group(1)) for p in paragraphs if (m:=re.match(kind+r' (\d+)\.',p))]
  assert numbers==list(range(1,n+1)),numbers
report=dict(state='passed',self_contained_wording_patterns=len(patterns),no_local_file_dependency=True,no_unsupported_data_availability_promise=True,map24_metrics_checked=10,map24_per_repetition_component_order_checked=True,first_map_overlap_verified=True,tables_in_order=5,figures_in_order=3,primary_data_sha256=hashlib.sha256((B/'raw_study/primary.json').read_bytes()).hexdigest(),docx_sha256=hashlib.sha256((B/'IJ3C_Manuscript.docx').read_bytes()).hexdigest(),scope='Wording and raw-data reconciliation; statistical intervals and actual simulation limits are retained as facts')
(B/'qa/plain_language_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
