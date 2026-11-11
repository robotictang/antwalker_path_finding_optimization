"""Insert the direct static capture of the primary MuJoCo robot model."""
import hashlib,json,re

def insert(B,texts,figures):
    def shift(s):return re.sub(r'Figure (\d+)',lambda m:'Figure '+str(int(m.group(1))+1),s)
    for key in texts:texts[key]=shift(texts[key])
    for key,(name,caption) in list(figures.items()):figures[key]=(name,shift(caption))
    provenance=json.loads((B/'results/screenshot_provenance.json').read_text())
    assert hashlib.sha256((B/provenance['copied_asset']).read_bytes()).hexdigest()==provenance['sha256']
    figures['FIG_OVERVIEW']=('simulation_overview.png','Figure 1. Static view of the simulated hexapod in its walking configuration. The wheels and scanner remain part of the assembly.')
