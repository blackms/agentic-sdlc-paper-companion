"""Build the v1.4 comparison tables comparing three inferential procedures
for the C1 cold > cold_mismatched contrast.

Table 1 (per-cell, 14 rows):
    cell | n | McNemar p (one-sided) | Permutation p (one-sided)
        | Mixed-effects per-cell predicted Δ̂ (pp)
        | Mixed-effects 95% MC CI (pp)
        | Mixed-effects "per-cell p" (two-sided Wald on the within-cell
          contrast, computed from the MC posterior — flagged as
          approximate, primary cross-cell inference is the model-level
          fixed-effect Wald)
        | qualitative agreement at α=0.025 (Y/N for all three)

Table 2 (cross-phase pooled):
    block-bootstrap pooled Δ | β_cond marginal effect + 95% Wald CI
    + Wald p | approximate LRT p on the joint cond block

Outputs `tables.json` (machine-readable) and prints a human-readable
summary. Discrepancies (any cell where mixed-effects disagrees with the
permutation at α=0.025) are written to `discrepancies.md`.
"""
from __future__ import annotations
import json
import sys
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
EXP_ROOT = ROOT.parent
sys.path.insert(0, str(EXP_ROOT))
from cluster_robust import extract_json, detects  # noqa: E402
from math import comb

ALPHA = 0.025  # one-sided per protocol


def sigmoid(x): return 1.0 / (1.0 + math.exp(-x))


def normal_cdf(z): return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def wald_p_two(z): return 2.0 * (1.0 - normal_cdf(abs(z)))


def mcnemar_one_sided(b, c):
    """One-sided exact McNemar (binomial on b of b+c, p=0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(b, n + 1)) / (2 ** n)


# Cell map: (label, det_path, rev_dir, cold_role, mm_role, domain, family, lib)
CELLS = [
    ("P9 csv (Codex)",      "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",
        "cold",              "cold_mismatched",          "csv_dom",     "codex",    "stdlib"),
    ("P9 urllib (Codex)",   "p9_real/urllib_dom/detection.json",   "p9_real/urllib_dom/reviews",
        "cold",              "cold_mismatched",          "urllib_dom",  "codex",    "stdlib"),
    ("P9 jsondec (Codex)",  "p9_real/jsondec_dom/detection.json",  "p9_real/jsondec_dom/reviews",
        "cold",              "cold_mismatched",          "jsondec_dom", "codex",    "stdlib"),
    ("P9 csv (Opus)",       "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",
        "cold_opus",         "cold_mismatched_opus",     "csv_dom",     "opus",     "stdlib"),
    ("P9 csv (Gemini 3.1)", "p9_real/csv_dom/detection.json",      "p9_real/csv_dom/reviews",
        "cold_gemini31",     "cold_mismatched_gemini31", "csv_dom",     "gemini31", "stdlib"),
    ("P10 dateutil (Codex)",       "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews",
        "cold_codex",    "cold_mismatched_codex",    "dateutil_dom",  "codex",    "third_party"),
    ("P10 dateutil (Opus)",        "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews",
        "cold_opus",     "cold_mismatched_opus",     "dateutil_dom",  "opus",     "third_party"),
    ("P10 dateutil (Gemini 3.1)",  "p10_thirdparty/dateutil_dom/detection.json",  "p10_thirdparty/dateutil_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31", "dateutil_dom",  "gemini31", "third_party"),
    ("P10 parsy (Codex)",          "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",
        "cold_codex",    "cold_mismatched_codex",    "parsy_dom",     "codex",    "third_party"),
    ("P10 parsy (Opus)",           "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",
        "cold_opus",     "cold_mismatched_opus",     "parsy_dom",     "opus",     "third_party"),
    ("P10 parsy (Gemini 3.1)",     "p10_thirdparty/parsy_dom/detection.json",     "p10_thirdparty/parsy_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31", "parsy_dom",     "gemini31", "third_party"),
    ("P10 chardet (Codex)",        "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",
        "cold_codex",    "cold_mismatched_codex",    "chardet_dom",   "codex",    "third_party"),
    ("P10 chardet (Opus)",         "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",
        "cold_opus",     "cold_mismatched_opus",     "chardet_dom",   "opus",     "third_party"),
    ("P10 chardet (Gemini 3.1)",   "p10_thirdparty/chardet_dom/detection.json",   "p10_thirdparty/chardet_dom/reviews",
        "cold_gemini31", "cold_mismatched_gemini31", "chardet_dom",   "gemini31", "third_party"),
]


def get_pairs(det_path, rev_dir, cold_role, mm_role):
    det = json.loads((EXP_ROOT / det_path).read_text())
    bugs = det["bugs"]
    rev = EXP_ROOT / rev_dir
    paired = []
    for bug in bugs:
        bid = bug["bug_id"]
        cf = extract_json(rev / f"{cold_role}_{bid}.raw.txt")
        mf = extract_json(rev / f"{mm_role}_{bid}.raw.txt")
        cd = bool(detects(bug, cf)) if cf is not None else False
        md = bool(detects(bug, mf)) if mf is not None else False
        paired.append((cd, md))
    return paired


def main():
    # Inputs
    perm = json.loads((EXP_ROOT / "results_cluster_robust.json").read_text())
    me = json.loads((ROOT / "results.json").read_text())

    me_contrasts = {c["label"]: c for c in me["per_cell_contrasts"]}

    # Table 1
    print("=" * 110)
    print("Table 1: per-cell comparison — McNemar vs Permutation vs Mixed-effects")
    print("=" * 110)
    print(f"{'cell':30s}  {'n':>3s}  "
          f"{'McNemar p':>10s}  {'Perm p':>10s}  "
          f"{'ME Δ̂ (pp)':>11s}  {'ME 95% CI (pp)':>22s}  "
          f"{'Agree?':>6s}")

    table1 = []
    discrepancies = []
    for cell in CELLS:
        (label, det, rev, cold, mm, dom, fam, lib) = cell
        pairs = get_pairs(det, rev, cold, mm)
        n = len(pairs)
        b = sum(1 for c, m in pairs if c and not m)  # cold-only catches
        c_ = sum(1 for c, m in pairs if not c and m)  # mm-only catches
        # H1: cold > mm  ⇒ b > c
        p_mc = mcnemar_one_sided(b, c_)
        perm_cell = perm["per_cell"][label]
        p_perm = perm_cell["p_one"]
        me_cell = me_contrasts[label]
        d_me_pp = me_cell["delta_hat"] * 100
        ci_lo_pp = me_cell["ci95_low"] * 100
        ci_hi_pp = me_cell["ci95_high"] * 100
        ci_excludes_zero = ci_lo_pp > 0
        sig_mc = p_mc < ALPHA
        sig_perm = p_perm < ALPHA
        sig_me = ci_excludes_zero
        agree = sig_mc and sig_perm and sig_me
        print(f"{label:30s}  {n:>3d}  "
              f"{p_mc:10.3e}  {p_perm:10.3e}  "
              f"{d_me_pp:+11.1f}  [{ci_lo_pp:+7.1f}, {ci_hi_pp:+7.1f}]  "
              f"{'Y' if agree else 'N':>6s}")
        row = {
            "cell": label, "domain": dom, "family": fam, "library_class": lib,
            "n": n,
            "mcnemar": {"b": b, "c": c_, "p_one": p_mc, "sig": sig_mc},
            "permutation": {"delta_obs": perm_cell["delta_obs"],
                            "p_one": p_perm,
                            "ci95": perm_cell["ci95"],
                            "sig": sig_perm},
            "mixed_effects": {"delta_hat_pp": d_me_pp,
                              "ci95_pp": [ci_lo_pp, ci_hi_pp],
                              "ci_excludes_zero": ci_excludes_zero,
                              "p_cold_hat": me_cell["p_cold_hat"],
                              "p_mismatched_hat": me_cell["p_mismatched_hat"],
                              "u_module_blup": me_cell["u_module_blup"],
                              "sig": sig_me},
            "qualitative_agreement_alpha_0p025": agree,
        }
        table1.append(row)
        if not agree:
            discrepancies.append(row)

    # Table 2: cross-phase pooled
    print()
    print("=" * 110)
    print("Table 2: cross-phase pooled — Block bootstrap vs Mixed-effects β_cond marginal")
    print("=" * 110)
    bb = perm["cross_phase_block_bootstrap"]
    fe = {f["name"]: f for f in me["fixed_effects"]}
    # The mixed-effects "marginal effect of condition" is β_cond on the
    # codex-stdlib reference cell. To make it directly comparable to the
    # bootstrap pooled Δ (averaged across cells), we also report the
    # average per-cell predicted Δ̂ from the model.
    me_mean_delta = np.mean([c["delta_hat"] for c in me["per_cell_contrasts"]])

    beta_cond = fe["cond"]
    print(f"  Block-bootstrap pooled Δ          = {bb['delta']*100:+.1f}pp  "
          f"95% CI = [{bb['ci95'][0]*100:+.1f}, {bb['ci95'][1]*100:+.1f}] pp")
    print(f"  Mixed-effects β_cond (logit)      = {beta_cond['mean']:+.4f}  "
          f"95% Wald CI = [{beta_cond['ci95_low']:+.4f}, {beta_cond['ci95_high']:+.4f}]"
          f"  z = {beta_cond['z']:+.2f}  p_two ≈ {beta_cond['p_wald_two']:.3g}")
    print(f"  Mean predicted Δ̂ across 14 cells = {me_mean_delta*100:+.1f}pp")
    lrt = me.get("approx_lrt_condition_block", {})
    if "p_lrt_approx" in lrt:
        print(f"  Approx ELBO-LRT joint cond block (df=4): D = {lrt['D_approx']:.2f}, "
              f"p ≈ {lrt['p_lrt_approx']:.3g}")

    table2 = {
        "block_bootstrap_pooled": {
            "delta": bb["delta"],
            "ci95": bb["ci95"],
            "n_domains": bb["n_domains"],
        },
        "mixed_effects_beta_cond": {
            "mean_logit": beta_cond["mean"],
            "sd_logit": beta_cond["sd"],
            "ci95_logit": [beta_cond["ci95_low"], beta_cond["ci95_high"]],
            "wald_z": beta_cond["z"],
            "wald_p_two": beta_cond["p_wald_two"],
        },
        "mixed_effects_mean_predicted_delta": float(me_mean_delta),
        "approx_lrt_condition_block": lrt,
    }

    out = {"table1_per_cell": table1, "table2_cross_phase": table2,
           "alpha_one_sided": ALPHA,
           "n_cells_qualitative_agree": sum(1 for r in table1
                                            if r["qualitative_agreement_alpha_0p025"]),
           "n_cells_total": len(table1)}
    (ROOT / "tables.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nQualitative agreement at α={ALPHA}: "
          f"{out['n_cells_qualitative_agree']}/{out['n_cells_total']} cells")
    print(f"Saved: {ROOT / 'tables.json'}")

    # Discrepancies file (only if any)
    disc_path = ROOT / "discrepancies.md"
    if discrepancies:
        lines = ["# Discrepancies between inferential procedures",
                 "",
                 f"Cells (out of 14) where the three procedures disagree at α={ALPHA}:",
                 ""]
        for d in discrepancies:
            lines += [
                f"## {d['cell']}",
                "",
                f"- McNemar:    b={d['mcnemar']['b']}, c={d['mcnemar']['c']}, "
                f"p={d['mcnemar']['p_one']:.4f}, sig={d['mcnemar']['sig']}",
                f"- Permutation: Δ={d['permutation']['delta_obs']*100:+.1f}pp, "
                f"p={d['permutation']['p_one']:.4f}, sig={d['permutation']['sig']}",
                f"- Mixed-effects: Δ̂={d['mixed_effects']['delta_hat_pp']:+.1f}pp, "
                f"CI=[{d['mixed_effects']['ci95_pp'][0]:+.1f},"
                f" {d['mixed_effects']['ci95_pp'][1]:+.1f}] pp, "
                f"sig={d['mixed_effects']['sig']}",
                "",
                "Diagnosis: ",
                "",
            ]
        disc_path.write_text("\n".join(lines))
        print(f"WARNING: {len(discrepancies)} discrepancies — see {disc_path}")
    else:
        # Write a clean "no discrepancies" stub
        disc_path.write_text(
            "# Discrepancies between inferential procedures\n\n"
            f"None. All {len(table1)}/{len(table1)} cells qualitatively "
            f"agree at α={ALPHA} (one-sided): McNemar exact, cluster-robust "
            "paired permutation, and the mixed-effects predicted marginal "
            "contrast all flag cold > mismatched with intervals excluding 0.\n"
        )
        print(f"No discrepancies. Stub written: {disc_path}")


if __name__ == "__main__":
    main()
