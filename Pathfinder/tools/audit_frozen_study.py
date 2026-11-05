"""Audit saved V6 evidence without editing frozen sources, models or reports.

The original scene names a missing Downloads directory. During this audit only,
ET.parse relocates that scene's asset references in memory to this checkout.
The original auditor still verifies the unchanged on-disk XML/source hashes.
No experiment or physics execution is started; geometry is reconstructed.
"""
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mujoco"))
from research import audit_final  # noqa: E402


def main():
    original_parse = ET.parse
    scene = ROOT / "mujoco/hybrid_hexapod_multi_place.xml"
    legacy = "/home/user123456/Downloads/hexapod_asset/"
    relocated = {}

    def parse(source, *args, **kwargs):
        tree = original_parse(source, *args, **kwargs)
        if Path(source).resolve() == scene:
            for item in tree.getroot().iter():
                value = item.get("file", "")
                if value.startswith(legacy):
                    replacement = ROOT / value[len(legacy):]
                    if not replacement.is_file():
                        raise FileNotFoundError(replacement)
                    item.set("file", str(replacement))
                    relocated[value] = str(replacement)
        return tree

    reports = {}
    ET.parse = parse
    original_writer = audit_final.atomic_json
    audit_final.atomic_json = lambda path, value: reports.update({str(path): value})
    try:
        report = audit_final.audit()
    finally:
        ET.parse = original_parse
        audit_final.atomic_json = original_writer
    result = dict(
        report=report,
        asset_path_relocations_in_memory=relocated,
        frozen_files_written=False,
        fresh_experiments_run=False,
        scope="Existing auditor with path-only in-memory asset relocation. Internal provenance and numerical checks; not independent scientific replication or hardware validation.",
    )
    target = ROOT / "docs/verification/frozen_v6_audit.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return int(report["state"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
