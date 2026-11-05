import importlib.util,sys
from pathlib import Path
skill=Path('/home/user123456/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('renderer',skill)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m._resolve_soffice=lambda:str(Path(__file__).parent/'soffice')
sys.argv=['render_docx.py','outputs/Hexapod_Student_Guide_and_Publication_Plan.docx','--output_dir','outputs/word_guide_qa','--emit_pdf']
m.main()
