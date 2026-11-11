"""Packaged DOCX renderer with explicit host-tool compatibility override.

The bundled Linux LibreOffice/Poppler require GLIBC_2.38 and GLIBCXX_3.4.31,
which this host lacks. Use the bundled Python and packaged render workflow,
with the installed system LibreOffice and Poppler solely for PDF/PNG render.
The DOCX itself is not resaved by LibreOffice.
"""
import importlib.util,os,sys
from pathlib import Path
B=Path(__file__).resolve().parents[1]
skill=Path('/home/user123456/.codex/plugins/cache/openai-primary-runtime/documents/26.1026.10807/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('pathfinder_renderer',skill)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module._resolve_soffice=lambda:'/usr/bin/libreoffice'
os.environ['PATH']=str(Path(sys.executable).parent)+':/usr/bin:/bin'
sys.argv=[str(skill),str(B/'IJ3C_Hexapod_Review_Draft.docx'),'--output_dir',str(B/'qa/render'),'--emit_pdf']
module.main()
