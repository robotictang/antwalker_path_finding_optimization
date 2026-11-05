"""Run the canonical renderer with an explicitly selected compatible LibreOffice."""
import importlib.util,sys
from pathlib import Path
P=Path('/home/user123456/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
s=importlib.util.spec_from_file_location('canonical_docs_renderer',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
# Bundled LibreOffice requires GLIBC 2.38 / GLIBCXX 3.4.31 unavailable on this host.
# This diagnosed, explicit override does not alter the packaged skill or save the DOCX.
m._resolve_soffice=lambda:'/usr/bin/soffice';sys.argv=[str(P),*sys.argv[1:]];m.main()
