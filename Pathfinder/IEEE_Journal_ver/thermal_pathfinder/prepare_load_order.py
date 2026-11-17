"""Reuse verified nominal profiles for the matched-course thermal follow-up."""

import argparse
import json
from pathlib import Path
import shutil

from .audit_network import require
from .margin_profiles import digest
from .mission_profiles import design
from .network_study import write_json


def prepare(config, source_config, source, output):
    original, *_ = design(source_config)
    manifest, *_ = design(config)
    require(json.loads(json.dumps(original)) == json.loads((source / "manifest.json").read_text()),
            "The saved profile source does not match its original manifest")
    study_keys = ("maps", "edge_deadline_s", "resolution_m", "speed_fractions", "transition_s")
    require(all(original["study"][k] == manifest["study"][k] for k in study_keys)
            and original["base"] == manifest["base"], "The follow-up geometry or nominal profile inputs differ")
    shared_hashes = set(original["sha256"]) & set(manifest["sha256"])
    require(all(original["sha256"][key] == manifest["sha256"][key] for key in shared_hashes),
            "The two experiments use different shared code or settings")
    files = [source / "edge_profiles.json", *sorted((source / "profiles").glob("*.npz")),
             *sorted(source.glob("*.xml"))]
    expected = set(json.loads(files[0].read_text()))
    require(expected == {file.name for file in files if file.suffix == ".npz"},
            "The source profile inventory is incomplete")
    (output / "profiles").mkdir(parents=True, exist_ok=False)
    for path in files:
        shutil.copy2(path, output / path.relative_to(source))
    write_json(output / "manifest.json", manifest)
    write_json(output / "profile_provenance.json", {
        "source_manifest_sha256": digest(source / "manifest.json"),
        "files": {str(path.relative_to(source)): digest(path) for path in files},
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("experiments/matched_load_order_boundary.json"))
    parser.add_argument("--source-config", type=Path, default=Path("experiments/matched_load_order.json"))
    parser.add_argument("--source", type=Path, default=Path("results/matched_load_order"))
    parser.add_argument("--output", type=Path, default=Path("results/matched_load_order_boundary"))
    args = parser.parse_args()
    prepare(args.config, args.source_config, args.source, args.output)


if __name__ == "__main__":
    main()
