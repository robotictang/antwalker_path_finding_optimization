"""Read saved phase JSON/CSV and package hashes; write a separate handoff report."""
from collections import Counter, defaultdict
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    package = ROOT / "outputs/ieee_access_final/package"
    checksums = json.loads((package / "SHA256SUMS.json").read_text())
    mismatches = [name for name, sha in checksums.items()
                  if not (package / name).is_file() or digest(package / name) != sha]
    study = ROOT / "mujoco/outputs/research/final_validation_v6"
    phases = {p.stem: json.loads(p.read_text()) for p in sorted(study.glob("v6_*.json"))}
    counts = {name: len(r["records"]) for name, r in phases.items()}
    primary = phases["v6_primary"]
    summary = []
    for method in primary["methods"]:
        rows = [r for r in primary["records"] if r["method"] == method]
        summary.append(dict(method=method, scheduled=len(rows),
                            admitted=sum(bool(r["plan"].get("admissible")) for r in rows),
                            mean_planning_s=statistics.mean(r["plan"]["planning_seconds"] for r in rows),
                            statuses=dict(Counter(r["status"] for r in rows))))
    index = {(r["case_id"], r["repeat"], r["method"]): r["plan"] for r in primary["records"]}
    comparisons = []
    for baseline in primary["methods"]:
        if baseline == "proposed_v4":
            continue
        worlds = defaultdict(list)
        for case in primary["cases"]:
            for repeat in range(primary["repeats"]):
                a = index[case["id"], repeat, "proposed_v4"]
                b = index[case["id"], repeat, baseline]
                if a.get("admissible") and b.get("admissible"):
                    worlds[case["id"]].append(100 * (b["quality_score"] - a["quality_score"]) / b["quality_score"])
        values = [statistics.mean(v) for v in worlds.values()]
        comparisons.append(dict(baseline=baseline, jointly_admitted_worlds=len(values),
                                mean_relative_percent=statistics.mean(values),
                                median_relative_percent=statistics.median(values)))
    paired_csv = list(csv.DictReader((ROOT / "outputs/ieee_access_final/tables/Final_Paired_Comparison.csv").open()))
    paired_match = all(math.isclose(r["mean_relative_percent"], float(next(x for x in paired_csv if x["baseline"] == r["baseline"])["mean_relative_percent"]), abs_tol=1e-10) for r in comparisons)
    rows = list(csv.DictReader((ROOT / "outputs/ieee_access_final/tables/All_1200_Final_Attempts.csv").open()))
    csvkeys = {(r["phase"], r["case"], r["method"], int(r["repeat"])) for r in rows}
    jsonkeys = {(phase, r["case_id"], r["method"], r["repeat"]) for phase, run in phases.items() for r in run["records"]}
    csv_match = len(rows) == len(csvkeys) == 1200 and csvkeys == jsonkeys
    result = dict(package_payloads_checked=len(checksums), package_hash_mismatches=mismatches,
                  phase_counts=counts, total_scheduled_records=sum(counts.values()),
                  primary_worlds=len(primary["cases"]), primary_summary=summary,
                  independently_recalculated_paired_means=comparisons,
                  paired_csv_matches=paired_match, attempt_csv_keys_match=csv_match,
                  scope="Read-only hash, record-key, admission, timing and paired-mean reconciliation. No new experiments or external literature verification.")
    dest = ROOT / "docs/verification/evidence_inventory.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("primary_summary", "independently_recalculated_paired_means")}, indent=2))
    return int(bool(mismatches) or not paired_match or not csv_match)


if __name__ == "__main__":
    raise SystemExit(main())
