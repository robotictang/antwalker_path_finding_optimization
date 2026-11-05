"""Canonical Documents renderer using bundled LibreOffice through a glibc compatibility launcher."""
import importlib.util,sys
from pathlib import Path
P=Path('/home/user123456/.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py')
s=importlib.util.spec_from_file_location('canonical_docs_renderer',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
# The launcher executes the bundled LibreOffice 26.8 soffice.bin with task-local
# compatible glibc/libstdc++, and does not invoke the desktop LibreOffice.
# Original bundled wrapper failure on host glibc 2.35 was diagnosed previously.
m._resolve_soffice=lambda:'/home/user123456/Downloads/hexapod_asset/outputs/render_compat/soffice'
sys.argv=[str(P),*sys.argv[1:]];m.main()
