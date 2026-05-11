"""Export bug-level long-format CSV for the mixed-effects re-analysis.

For each of the 14 cells covered by cluster_robust_c1.py (P9 stdlib Codex +
P9 csv cross-family + P10 third-party × 3 families) and for each of the
30 bugs per cell, emit two rows: one for the `cold` (aligned) condition
and one for the `cold_mismatched` (misaligned) condition.

Output columns:
  phase           "P9_stdlib", "P9_csv_cross_family", "P10_thirdparty"
  domain          module name: csv_dom, urllib_dom, jsondec_dom,
                  dateutil_dom, parsy_dom, chardet_dom
  family          codex, opus, gemini31
  library_class   stdlib | third_party
  condition       cold | mismatched
  bug_id          P9c_B01 ... etc.
  detected        0/1 (strict; unparsed = 0)
  parsed          0/1

P11 cells are intentionally excluded from the main long-format export
(see README "Frozen model specification"). P11 truthful conditions are
the same review files we already pick up via the P9 csv cold cell and the
P10 chardet cold_codex cell, so nothing new would be added. P11 relabel
conditions are the treatment of Stream C and are not the cold-vs-mismatched
contrast of interest here.

Run:
    python3 export_longformat.py
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP_ROOT = ROOT.parent
# Make cluster_robust.{extract_json,detects} importable
sys.path.insert(0, str(EXP_ROOT))
from cluster_robust import extract_json, detects  # noqa: E402

# Cell registry — mirrors cluster_robust_c1.CELLS but with metadata for the
# long-format export.
CELLS = [
    # phase, domain, family, library_class, detection_json, reviews_dir,
    # cold_role, mismatched_role
    ("P9_stdlib", "csv_dom",     "codex",    "stdlib",
        "p9_real/csv_dom/detection.json",    "p9_real/csv_dom/reviews",
        "cold", "cold_mismatched"),
    ("P9_stdlib", "urllib_dom",  "codex",    "stdlib",
        "p9_real/urllib_dom/detection.json", "p9_real/urllib_dom/reviews",
        "cold", "cold_mismatched"),
    ("P9_stdlib", "jsondec_dom", "codex",    "stdlib",
        "p9_real/jsondec_dom/detection.json","p9_real/jsondec_dom/reviews",
        "cold", "cold_mismatched"),

    ("P9_csv_cross_family", "csv_dom", "opus",     "stdlib",
        "p9_real/csv_dom/detection.json", "p9_real/csv_dom/reviews",
        "cold_opus", "cold_mismatched_opus"),
    ("P9_csv_cross_family", "csv_dom", "gemini31", "stdlib",
        "p9_real/csv_dom/detection.json", "p9_real/csv_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31"),

    ("P10_thirdparty", "dateutil_dom", "codex",    "third_party",
        "p10_thirdparty/dateutil_dom/detection.json",
        "p10_thirdparty/dateutil_dom/reviews",
        "cold_codex", "cold_mismatched_codex"),
    ("P10_thirdparty", "dateutil_dom", "opus",     "third_party",
        "p10_thirdparty/dateutil_dom/detection.json",
        "p10_thirdparty/dateutil_dom/reviews",
        "cold_opus", "cold_mismatched_opus"),
    ("P10_thirdparty", "dateutil_dom", "gemini31", "third_party",
        "p10_thirdparty/dateutil_dom/detection.json",
        "p10_thirdparty/dateutil_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31"),

    ("P10_thirdparty", "parsy_dom",    "codex",    "third_party",
        "p10_thirdparty/parsy_dom/detection.json",
        "p10_thirdparty/parsy_dom/reviews",
        "cold_codex", "cold_mismatched_codex"),
    ("P10_thirdparty", "parsy_dom",    "opus",     "third_party",
        "p10_thirdparty/parsy_dom/detection.json",
        "p10_thirdparty/parsy_dom/reviews",
        "cold_opus", "cold_mismatched_opus"),
    ("P10_thirdparty", "parsy_dom",    "gemini31", "third_party",
        "p10_thirdparty/parsy_dom/detection.json",
        "p10_thirdparty/parsy_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31"),

    ("P10_thirdparty", "chardet_dom",  "codex",    "third_party",
        "p10_thirdparty/chardet_dom/detection.json",
        "p10_thirdparty/chardet_dom/reviews",
        "cold_codex", "cold_mismatched_codex"),
    ("P10_thirdparty", "chardet_dom",  "opus",     "third_party",
        "p10_thirdparty/chardet_dom/detection.json",
        "p10_thirdparty/chardet_dom/reviews",
        "cold_opus", "cold_mismatched_opus"),
    ("P10_thirdparty", "chardet_dom",  "gemini31", "third_party",
        "p10_thirdparty/chardet_dom/detection.json",
        "p10_thirdparty/chardet_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31"),
]


def emit_rows(cell):
    (phase, domain, family, lib_class, det_path, rev_dir,
     cold_role, mm_role) = cell
    det = json.loads((EXP_ROOT / det_path).read_text())
    bugs = det["bugs"]
    rev = EXP_ROOT / rev_dir
    out = []
    for bug in bugs:
        bid = bug["bug_id"]
        for role, cond_label in ((cold_role, "cold"),
                                 (mm_role, "mismatched")):
            raw_path = rev / f"{role}_{bid}.raw.txt"
            found = extract_json(raw_path)
            parsed = 0 if found is None else 1
            if found is None:
                detected = 0  # strict-unparsed-as-miss
            else:
                detected = 1 if detects(bug, found) else 0
            out.append({
                "phase": phase,
                "domain": domain,
                "family": family,
                "library_class": lib_class,
                "condition": cond_label,
                "bug_id": bid,
                "detected": detected,
                "parsed": parsed,
            })
    return out


def main():
    rows = []
    per_cell_counts = []
    for cell in CELLS:
        cell_rows = emit_rows(cell)
        rows.extend(cell_rows)
        per_cell_counts.append((cell[0], cell[1], cell[2], len(cell_rows)))

    out_path = ROOT / "long_format.csv"
    fieldnames = ["phase", "domain", "family", "library_class",
                  "condition", "bug_id", "detected", "parsed"]
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"Cells: {len(CELLS)} (expected: 14)")
    expected = len(CELLS) * 30 * 2  # n_bugs × 2 conditions per cell
    print(f"Expected total rows = 14 × 30 × 2 = {expected}; got {len(rows)} "
          f"({'OK' if len(rows) == expected else 'MISMATCH'})")
    print()
    print("Per-cell breakdown:")
    for phase, dom, fam, n in per_cell_counts:
        print(f"  {phase:22s} {dom:14s} {fam:8s}  rows={n}")

    # Parse-rate sanity check
    parsed_count = sum(r["parsed"] for r in rows)
    print(f"\nOverall parse rate: {parsed_count}/{len(rows)} = "
          f"{100*parsed_count/len(rows):.1f}%")


if __name__ == "__main__":
    main()
