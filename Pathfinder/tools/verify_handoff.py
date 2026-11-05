"""Check original-file preservation and relative navigation links after handoff."""
from pathlib import Path
import argparse
import hashlib
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=Path('/home/user123456/Desktop/Pathfinder_handoff_backup_2026-11-03/original_inventory.json'))
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    missing, changed = [], []
    for row in inventory:
        path = ROOT / row['path']
        if row['path'] == 'README.md':
            path = ROOT / 'docs/legacy_guides/ORIGINAL_ROOT_README.md'
        if not path.is_file():
            missing.append(row['path'])
        elif digest(path) != row['sha256']:
            changed.append(row['path'])
    broken = [str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_symlink() and not p.exists()]
    backup_root = args.inventory.parent / 'Pathfinder'
    inherited_broken = [name for name in broken if (backup_root / name).is_symlink()
                        and (backup_root / name).readlink() == (ROOT / name).readlink()
                        and not (backup_root / name).exists()]
    new_broken = [name for name in broken if name not in inherited_broken]
    docs = [ROOT / 'README.md', ROOT / 'paper/README.md', ROOT / 'archive/README.md', ROOT / 'workbench/README.md', *sorted((ROOT / 'docs').glob('*.md')), ROOT / 'docs/verification/README.md']
    bad_links = []
    for doc in docs:
        if not doc.exists():
            bad_links.append(str(doc.relative_to(ROOT)))
            continue
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            target = unquote(target.split('#', 1)[0])
            if target and '://' not in target and not (doc.parent / target).exists():
                bad_links.append(dict(document=str(doc.relative_to(ROOT)), target=target))
    report = dict(original_files_checked=len(inventory), original_files_missing=missing,
                  original_bytes_changed=changed, original_readme_preserved_at='docs/legacy_guides/ORIGINAL_ROOT_README.md',
                  broken_handoff_symbolic_links=new_broken, preexisting_broken_symbolic_links=inherited_broken,
                  broken_handoff_document_links=bad_links,
                  note='Only root README was intentionally replaced; its original bytes are preserved. Frozen scientific files are compared with the pre-handoff inventory.')
    (ROOT / 'docs/verification/preservation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(bool(missing or changed or new_broken or bad_links))


if __name__ == '__main__':
    raise SystemExit(main())
