"""Run the packaged renderer using bundled binaries and an isolated ABI loader.

The host GLIBC is older than the bundled LibreOffice/Poppler require. The
wrappers use the preserved task-local compatibility libraries and execute the
bundled binaries; installed desktop LibreOffice is not used. DOCX is not resaved.
"""
import importlib.util,os,sys
from pathlib import Path
B=Path(__file__).resolve().parents[1]
skill=Path('/home/user123456/.codex/plugins/cache/openai-primary-runtime/documents/26.1030.10813/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('pathfinder_renderer',skill)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
wrappers=B/'qa/runtime'
module._resolve_soffice=lambda:str(wrappers/'soffice')
# LibreOffice's OMML importer otherwise chooses its default Math font despite
# the Word run font. Configure the isolated render profile, not desktop settings.
original_env=module._build_lo_env
def render_env(user_profile):
    env=original_env(user_profile)
    props=lambda values: ''.join('<prop oor:name="'+key+'" oor:op="fuse"><value>'+str(value)+'</value></prop>' for key,value in values.items())
    nodes=''
    for name,italic in [('TNRRoman',0),('TNRItalic',2)]:
        nodes+='<node oor:name="'+name+'" oor:op="replace">'+props(dict(Name='Times New Roman',CharSet=0,Family=3,Pitch=2,Weight=5,Italic=italic))+'</node>'
    font_item='<item oor:path="/org.openoffice.Office.Math/FontFormatList">'+nodes+'</item>'
    standard='<item oor:path="/org.openoffice.Office.Math/StandardFormat">'+props(dict(VariableFont='TNRItalic',FunctionFont='TNRRoman',NumberFont='TNRRoman',TextFont='TNRRoman',SerifFont='TNRRoman'))+'</item>'
    content='<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry">'+font_item+standard+'</oor:items>'
    profile=Path(user_profile)/'user';profile.mkdir(parents=True,exist_ok=True)
    (profile/'registrymodifications.xcu').write_text(content)
    return env
module._build_lo_env=render_env
os.environ['PATH']=str(wrappers)+':'+str(Path(sys.executable).parent)+':/usr/bin:/bin'
sys.argv=[str(skill),str(B/'IJ3C_Manuscript.docx'),'--output_dir',str(B/'qa/render-delivery'),'--emit_pdf']
module.main()
