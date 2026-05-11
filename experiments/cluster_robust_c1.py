"""Cluster-robust paired permutation test applied to all C1 cells.

Aggregates cold vs cold_mismatched paired outcomes across:
  - P9 stdlib: csv_dom, urllib_dom, jsondec_dom (Codex)
  - P9 csv cross-family: cold_opus, cold_gemini31 (mismatched_opus, mismatched_gemini31)
  - P10 third-party: dateutil_dom, parsy_dom, chardet_dom × {codex, opus, gemini31}

Reports per-cell permutation p (one-sided, cold > mismatched) and Δ with
percentile-bootstrap CI. Cross-phase combined via block-bootstrap over
DOMAINS (the cluster unit).

Run:  python3 cluster_robust_c1.py
"""
from __future__ import annotations
import json
from pathlib import Path
from cluster_robust import extract_json, detects, cluster_perm_test, cluster_bootstrap_domains

ROOT = Path(__file__).parent

# (cell label, detection_json_path, reviews_dir, cold_role_name, mm_role_name)
CELLS = [
    # P9 Codex (stdlib) — original 3 domains
    ("P9 csv (Codex)",      "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",      "cold",              "cold_mismatched"),
    ("P9 urllib (Codex)",   "p9_real/urllib_dom/detection.json",   "p9_real/urllib_dom/reviews",   "cold",              "cold_mismatched"),
    ("P9 jsondec (Codex)",  "p9_real/jsondec_dom/detection.json",  "p9_real/jsondec_dom/reviews",  "cold",              "cold_mismatched"),
    # P9 csv cross-family (Opus, Gemini)
    ("P9 csv (Opus)",       "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",      "cold_opus",         "cold_mismatched_opus"),
    ("P9 csv (Gemini 3.1)", "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",      "cold_gemini31",     "cold_mismatched_gemini31"),
    # P10 third-party × 3 families
    ("P10 dateutil (Codex)",       "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews", "cold_codex",    "cold_mismatched_codex"),
    ("P10 dateutil (Opus)",        "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews", "cold_opus",     "cold_mismatched_opus"),
    ("P10 dateutil (Gemini 3.1)",  "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews", "cold_gemini31", "cold_mismatched_gemini31"),
    ("P10 parsy (Codex)",          "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",    "cold_codex",    "cold_mismatched_codex"),
    ("P10 parsy (Opus)",           "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",    "cold_opus",     "cold_mismatched_opus"),
    ("P10 parsy (Gemini 3.1)",     "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",    "cold_gemini31", "cold_mismatched_gemini31"),
    ("P10 chardet (Codex)",        "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",  "cold_codex",    "cold_mismatched_codex"),
    ("P10 chardet (Opus)",         "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",  "cold_opus",     "cold_mismatched_opus"),
    ("P10 chardet (Gemini 3.1)",   "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",  "cold_gemini31", "cold_mismatched_gemini31"),
]


def get_pairs(det_path, rev_dir, cold_role, mm_role):
    det = json.loads((ROOT / det_path).read_text())
    bugs = det["bugs"]
    rev = ROOT / rev_dir
    paired = []
    for bug in bugs:
        bid = bug["bug_id"]
        cf = extract_json(rev / f"{cold_role}_{bid}.raw.txt")
        mf = extract_json(rev / f"{mm_role}_{bid}.raw.txt")
        # Treat unparsed as miss (strict)
        cd = bool(detects(bug, cf)) if cf is not None else False
        md = bool(detects(bug, mf)) if mf is not None else False
        paired.append((cd, md))
    return paired


def main():
    print("=" * 80)
    print("Cluster-robust paired permutation test (cold > cold_mismatched, strict)")
    print("=" * 80)
    results = {}
    domain_pairs = {}
    for label, det, rev, cold, mm in CELLS:
        pairs = get_pairs(det, rev, cold, mm)
        domain_pairs[label] = pairs
        r = cluster_perm_test(pairs, n_perm=20000, seed=20260511)
        results[label] = r
        print(f"  {label:30s}: Δ={r['delta_obs']*100:+6.1f}pp  n={r['n']:3d}  "
              f"p_one={r['p_one']:.4f}  CI95=[{r['ci95'][0]*100:+5.1f}, {r['ci95'][1]*100:+5.1f}]")

    # Cross-phase block bootstrap (cluster = domain × family)
    print("\n## Cross-phase block bootstrap (cluster = cell)")
    combined = cluster_bootstrap_domains(domain_pairs, n_boot=10000, seed=20260511)
    print(f"  observed pooled Δ = {combined['delta']*100:+.1f}pp")
    print(f"  block-bootstrap 95% CI for population Δ: "
          f"[{combined['ci95'][0]*100:+.1f}, {combined['ci95'][1]*100:+.1f}] pp")
    print(f"  K = {combined['n_domains']} cells resampled with replacement")

    # Save
    out = {
        "per_cell": {label: {**r, "ci95": list(r["ci95"])} for label, r in results.items()},
        "cross_phase_block_bootstrap": {**combined, "ci95": list(combined["ci95"])},
    }
    out_path = ROOT / "results_cluster_robust.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
