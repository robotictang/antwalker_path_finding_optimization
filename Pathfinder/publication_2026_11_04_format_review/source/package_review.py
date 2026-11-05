"""Package review artifacts and runtime without changing frozen evidence."""
import hashlib
import json
from pathlib import Path
import zipfile

B = Path(__file__).resolve().parents[1]
ROOT = B.parent
DEST = B / 'IJ3C_Review_Bundle.zip'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    paths = []
    for directory in [B, ROOT / 'workbench']:
        for p in directory.rglob('*'):
            if 'before_core_fonts' in p.parts or 'qa/runtime' in str(p.relative_to(ROOT)) or p.name.startswith('superseded_') or p.name=='authored_working.docx':
                continue
            if not p.is_file() or p.is_symlink():
                continue
            if '__pycache__' in p.parts or p.suffix in {'.pyc', '.sqlite3', '.db'}:
                continue
            if p.name in {'experiment.lock', 'latest.json', 'console_job.log',
                          'payload_sha256.json', 'package_check.json', DEST.name, 'live_demo.log'}:
                continue
            if '.sqlite3-' in p.name:
                continue
            paths.append(p)
    paths += [ROOT / 'hexapod.urdf', ROOT / 'tools/live_pathfinder.py']
    # Preserve the historical manifest inputs to the fresh-world overlap check.
    paths += list((ROOT / 'mujoco/outputs/research').glob('*/manifest.json'))
    payloads = {str(p.relative_to(ROOT)): p.read_bytes() for p in sorted(set(paths))}
    hashes = {name: digest(data) for name, data in payloads.items()}
    (B / 'payload_sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
    with zipfile.ZipFile(DEST, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, data in payloads.items():
            z.writestr(name, data)
        z.write(B / 'payload_sha256.json', 'publication_2026_11_04_format_review/payload_sha256.json')
    with zipfile.ZipFile(DEST) as z:
        assert z.testzip() is None
        assert all(digest(z.read(name)) == sha for name, sha in hashes.items())
        scientific = 'workbench/mujoco/'
        study = scientific + 'outputs/research/publication_ij3c_20261104/'
        lock = json.loads(z.read(study + 'source_lock.json'))
        for name, sha in lock.items():
            assert digest(z.read(scientific + name)) == sha, name
        for phase in ['development_default', 'development_alternative', 'primary']:
            data = json.loads(z.read(study + phase + '.json'))
            for name, sha in data['source_sha256'].items():
                assert digest(z.read(scientific + 'outputs/research/' + data['source_snapshot'] + '/' + name)) == sha
            for case in data['cases']:
                assert digest(z.read(scientific + 'outputs/research/' + case['model_xml'])) == case['model_xml_sha256']
            assert z.read(study + phase + '.json') == z.read('publication_2026_11_04_format_review/raw_study/' + phase + '.json')
    report = dict(state='passed', payload_files=len(payloads), zip_bytes=DEST.stat().st_size,
                  zip_sha256=digest(DEST.read_bytes()), checks=['CRC', 'every payload SHA-256',
                  'scientific source lock', 'all phase snapshots and model hashes', 'raw phase copy identity'],
                  exclusions='Caches, mutable live databases, duplicate latest.json, console/live logs; original historical packages remain outside this bundle.',
                  scope='Archive integrity and dependency inspection; not a clean-environment execution test.')
    (B / 'qa/package_check.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
