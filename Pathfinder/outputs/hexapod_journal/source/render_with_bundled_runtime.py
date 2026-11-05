"""Use the skill renderer and bundled office with task-local compatibility libs.

The host libc is older than the bundled office binary. No system packages or
managed runtime files are modified. Office and Poppler remain bundled binaries.
"""
import functools,importlib.util,os,sys
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RUNTIME=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies'
LIB=BASE/'qa/render_runtime/root/usr/lib/x86_64-linux-gnu';WRAPPERS=BASE/'qa/render_runtime/wrappers';WRAPPERS.mkdir(exist_ok=True)
LO=RUNTIME/'native/libreoffice-headless/libreoffice/program';POP=RUNTIME/'native/poppler/poppler'
for name,binary,libpath in [('soffice',LO/'soffice.bin',LO),('pdfinfo',POP/'bin/pdfinfo',POP/'lib'),('pdftoppm',POP/'bin/pdftoppm',POP/'lib')]:
 path=WRAPPERS/name
 path.write_text('#!/bin/sh\n'+f'export FONTCONFIG_FILE="{POP}/etc/fonts/fonts.conf"\nexport POPPLER_DATADIR="{POP}/share/poppler"\n'+f'exec "{LIB}/ld-linux-x86-64.so.2" --library-path "{LIB}:{libpath}" "{binary}" "$@"\n')
 path.chmod(0o755)
SKILL=Path.home()/'.codex/plugins/cache/openai-primary-runtime/documents/26.1025.11240/skills/documents/render_docx.py'
spec=importlib.util.spec_from_file_location('skill_renderer',SKILL);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module._resolve_soffice=lambda:str(WRAPPERS/'soffice')
module.pdfinfo_from_path=functools.partial(module.pdfinfo_from_path,poppler_path=str(WRAPPERS))
module.convert_from_path=functools.partial(module.convert_from_path,poppler_path=str(WRAPPERS))
module.main()
