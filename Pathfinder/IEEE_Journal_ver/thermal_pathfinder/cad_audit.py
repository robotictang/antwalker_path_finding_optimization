"""Record the source OBJ checksum and dimensions of selected assembly groups."""

import argparse
import hashlib
import json
from pathlib import Path

GROUPS = frozenset((
    "Main_Chassis_Base_Body", "Coxa_Link_Main_Body",
    "Coxa_Femur_Service_Cheek_Body", "FEMUR_PRINT_SECTION_HIP",
    "FEMUR_PRINT_SECTION_KNEE_HOOK", "Femur_Tibia_Service_Cheek_Body",
    "TIBIA_PRINT_SECTION_KNEE", "TIBIA_PRINT_SECTION_FOOT",
))


def audit(source):
    checksum = hashlib.sha256()
    groups = {}
    totals = {"vertices": 0, "faces": 0, "groups": 0}
    selected = None
    with source.open("rb") as file:
        for line in file:
            checksum.update(line)
            if line.startswith(b"g "):
                totals["groups"] += 1
                name = line[2:].decode(errors="replace").strip()
                selected = None
                if name.split(":", 1)[0] in GROUPS:
                    selected = groups.setdefault(name, {"vertices": 0, "faces": 0})
            elif line.startswith(b"v "):
                totals["vertices"] += 1
                if selected is not None:
                    coords = [float(value) for value in line.split()[1:4]]
                    selected["vertices"] += 1
                    selected["min"] = list(map(min, zip(selected.get("min", coords), coords, strict=True)))
                    selected["max"] = list(map(max, zip(selected.get("max", coords), coords, strict=True)))
            elif line.startswith(b"f "):
                totals["faces"] += 1
                if selected is not None:
                    selected["faces"] += 1
    missing = GROUPS - {name.split(":", 1)[0] for name in groups}
    if missing:
        raise ValueError(f"Missing expected OBJ groups: {sorted(missing)}")
    return {"source": source.name, "sha256": checksum.hexdigest(), "counts": totals,
            "bounds_in_export_coordinates": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(audit(args.source), indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
