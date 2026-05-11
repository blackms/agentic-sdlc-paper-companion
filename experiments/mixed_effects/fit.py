"""Mixed-effects logistic regression on the 14-cell long-format CSV.

Frozen model (see README "Frozen model specification"):

    logit P(detect=1) = β_0 + β_cond·cond + β_opus·fam_opus
                        + β_gemini·fam_gemini + β_lib·libclass_tp
                        + β_cond:opus + β_cond:gemini + β_cond:lib
                        + u_bug[bug_id_within_cell] + u_module[domain]

Random effects: u_bug ~ N(0, σ_bug²),  u_module ~ N(0, σ_module²).

Fit via `statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM.fit_vb`
(mean-field variational Bayes). Reported quantities per fixed effect:

  - posterior mean  (point estimate on the logit scale)
  - posterior SD
  - 95% approximate Wald interval  mean ± 1.96·SD
  - z = mean / SD
  - two-sided Wald p = 2·(1 − Φ(|z|))

Random effect variance components: posterior mean of log(σ) is exponentiated
to give σ on the SD scale (with a 95% interval on σ derived from log(σ)
± 1.96·sd).

Per-cell predicted marginal contrast (cold − mismatched) on the response
scale: for each of the 14 cells we compute
    p̂_cold       = σ(η_cold)
    p̂_mismatched = σ(η_mismatched)
    Δ̂           = p̂_cold − p̂_mismatched
where η is built from the cell's family and library_class with both
random effects evaluated at zero (population-average contrast at the modal
random-effect value). Uncertainty on Δ̂ is propagated by Monte-Carlo draws
of the fixed effects from N(fe_mean, diag(fe_sd²)) and reporting the
2.5/97.5 quantiles of the resulting Δ̂ distribution.

LRT-style p for cond: refit a nested model dropping `cond` and all three
`cond_x_*` interactions, compare 2·(ELBO_full − ELBO_reduced). This is an
*approximate* likelihood-ratio diagnostic under the VB lower bound — not a
true LRT, but reported as a sanity check alongside the cross-Wald result.

Outputs `results.json` and prints a one-screen summary.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

ROOT = Path(__file__).resolve().parent
SEED = 20260511


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def wald_p_two(z: float) -> float:
    return 2.0 * (1.0 - normal_cdf(abs(z)))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def load_data() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "long_format.csv")
    df["cond"] = (df["condition"] == "cold").astype(int)
    df["fam_opus"] = (df["family"] == "opus").astype(int)
    df["fam_gemini"] = (df["family"] == "gemini31").astype(int)
    df["libclass_tp"] = (df["library_class"] == "third_party").astype(int)
    df["cond_x_opus"] = df["cond"] * df["fam_opus"]
    df["cond_x_gemini"] = df["cond"] * df["fam_gemini"]
    df["cond_x_libclass"] = df["cond"] * df["libclass_tp"]
    # Within-cell unique bug id: same bug_id appears in multiple cells
    # (cross-family P9 and P10), but the unit "this bug seen by this
    # reviewer family" is the cluster of interest.
    df["bug_uid"] = df["domain"] + "__" + df["family"] + "__" + df["bug_id"]
    df["module"] = df["domain"]
    return df


def fit_full(df: pd.DataFrame):
    formula = ("detected ~ cond + fam_opus + fam_gemini + libclass_tp + "
               "cond_x_opus + cond_x_gemini + cond_x_libclass")
    vc_formulas = {
        "bug":    "0 + C(bug_uid)",
        "module": "0 + C(module)",
    }
    model = BinomialBayesMixedGLM.from_formula(formula, vc_formulas, df)
    result = model.fit_vb()
    return model, result


def fit_no_cond(df: pd.DataFrame):
    """Reduced model — drops cond and all three cond_x_* terms.
    Used for an approximate LRT-style ELBO comparison on the joint
    cond + cond×family + cond×libclass effect.
    """
    formula = "detected ~ fam_opus + fam_gemini + libclass_tp"
    vc_formulas = {
        "bug":    "0 + C(bug_uid)",
        "module": "0 + C(module)",
    }
    model = BinomialBayesMixedGLM.from_formula(formula, vc_formulas, df)
    result = model.fit_vb()
    return model, result


def per_cell_contrasts(fe_mean, fe_sd, exog_names, cells, module_re,
                       n_mc=20000):
    """For each cell, build η_cold and η_mismatched and return Δ̂ on the
    response scale.

    The per-module random-effect posterior mean u_module[domain] is added
    to η so that per-cell predictions reflect the model's actual fit to
    that module's data (otherwise all stdlib-codex cells would predict
    identically, since the fixed-effect grid only has 6 distinct (family,
    libclass) cells). The per-bug random effect is *not* added: it enters
    symmetrically in both conditions and cancels in the within-bug
    contrast on the logit scale (it slightly attenuates on the response
    scale, but the BLUP for the cell-level mean is zero by design).

    Uncertainty bands: Monte-Carlo over the fixed-effects posterior
    (treated as factored Gaussian under VB). Module RE BLUPs are treated
    as plug-in (their VB SD shrinks below ~0.05 here, so this is a
    minor approximation).
    """
    rng = np.random.default_rng(SEED)
    name_to_idx = {n: i for i, n in enumerate(exog_names)}
    fe_mean = np.asarray(fe_mean)
    fe_sd = np.asarray(fe_sd)
    draws = rng.normal(fe_mean, fe_sd, size=(n_mc, len(fe_mean)))
    out = []
    for cell in cells:
        family = cell["family"]
        domain = cell["domain"]
        lib_tp = 1 if cell["library_class"] == "third_party" else 0
        fam_opus = 1 if family == "opus" else 0
        fam_gemini = 1 if family == "gemini31" else 0
        u_mod = module_re.get(domain, 0.0)

        def eta(cond_val, betas):
            v = betas[name_to_idx["Intercept"]]
            v += cond_val * betas[name_to_idx["cond"]]
            v += fam_opus * betas[name_to_idx["fam_opus"]]
            v += fam_gemini * betas[name_to_idx["fam_gemini"]]
            v += lib_tp * betas[name_to_idx["libclass_tp"]]
            v += cond_val * fam_opus * betas[name_to_idx["cond_x_opus"]]
            v += cond_val * fam_gemini * betas[name_to_idx["cond_x_gemini"]]
            v += cond_val * lib_tp * betas[name_to_idx["cond_x_libclass"]]
            v += u_mod
            return v

        eta_cold = eta(1, fe_mean)
        eta_mm = eta(0, fe_mean)
        d_mean = float(sigmoid(eta_cold) - sigmoid(eta_mm))

        eta_cold_mc = np.array([eta(1, b) for b in draws])
        eta_mm_mc = np.array([eta(0, b) for b in draws])
        d_mc = sigmoid(eta_cold_mc) - sigmoid(eta_mm_mc)
        lo, hi = np.quantile(d_mc, [0.025, 0.975])
        out.append({
            "label": cell["label"],
            "domain": cell["domain"],
            "family": cell["family"],
            "library_class": cell["library_class"],
            "u_module_blup": float(u_mod),
            "delta_hat": d_mean,
            "ci95_low": float(lo),
            "ci95_high": float(hi),
            "p_cold_hat": float(sigmoid(eta_cold)),
            "p_mismatched_hat": float(sigmoid(eta_mm)),
        })
    return out


def extract_module_blups(result) -> dict:
    """Pull the posterior-mean random effect per module from the
    `random_effects()` DataFrame.

    Index labels look like: 'C(module)[csv_dom]'  →  domain key 'csv_dom'.
    """
    re_df = result.random_effects()
    blups = {}
    for idx, row in re_df.iterrows():
        s = str(idx)
        if s.startswith("C(module)["):
            key = s[len("C(module)["):].rstrip("]")
            blups[key] = float(row["Mean"])
    return blups


CELLS_META = [
    {"label": "P9 csv (Codex)",        "domain": "csv_dom",     "family": "codex",    "library_class": "stdlib"},
    {"label": "P9 urllib (Codex)",     "domain": "urllib_dom",  "family": "codex",    "library_class": "stdlib"},
    {"label": "P9 jsondec (Codex)",    "domain": "jsondec_dom", "family": "codex",    "library_class": "stdlib"},
    {"label": "P9 csv (Opus)",         "domain": "csv_dom",     "family": "opus",     "library_class": "stdlib"},
    {"label": "P9 csv (Gemini 3.1)",   "domain": "csv_dom",     "family": "gemini31", "library_class": "stdlib"},
    {"label": "P10 dateutil (Codex)",       "domain": "dateutil_dom","family": "codex",    "library_class": "third_party"},
    {"label": "P10 dateutil (Opus)",        "domain": "dateutil_dom","family": "opus",     "library_class": "third_party"},
    {"label": "P10 dateutil (Gemini 3.1)",  "domain": "dateutil_dom","family": "gemini31", "library_class": "third_party"},
    {"label": "P10 parsy (Codex)",          "domain": "parsy_dom",   "family": "codex",    "library_class": "third_party"},
    {"label": "P10 parsy (Opus)",           "domain": "parsy_dom",   "family": "opus",     "library_class": "third_party"},
    {"label": "P10 parsy (Gemini 3.1)",     "domain": "parsy_dom",   "family": "gemini31", "library_class": "third_party"},
    {"label": "P10 chardet (Codex)",        "domain": "chardet_dom", "family": "codex",    "library_class": "third_party"},
    {"label": "P10 chardet (Opus)",         "domain": "chardet_dom", "family": "opus",     "library_class": "third_party"},
    {"label": "P10 chardet (Gemini 3.1)",   "domain": "chardet_dom", "family": "gemini31", "library_class": "third_party"},
]


def main():
    print("=" * 78)
    print("Mixed-effects logistic regression (BinomialBayesMixedGLM, VB)")
    print("=" * 78)
    df = load_data()
    print(f"Data: {len(df)} bug-level rows, "
          f"{df['bug_uid'].nunique()} bug clusters, "
          f"{df['module'].nunique()} module clusters")

    try:
        model, result = fit_full(df)
    except Exception as exc:
        print(f"PRIMARY FIT FAILED: {exc}")
        # Write a fallback marker. Per protocol we would then go to GEE, but
        # we expect the primary to converge based on the smoke test.
        raise

    fe_mean = np.asarray(result.fe_mean)
    fe_sd = np.asarray(result.fe_sd)
    vcp_mean = np.asarray(result.vcp_mean)   # log SD posterior means
    vcp_sd = np.asarray(result.vcp_sd)
    names = model.exog_names

    # Map VC parameter names (order matches `vc_formulas` dict order).
    vc_names = ["bug", "module"]

    print("\n## Fixed effects (logit scale)")
    fe_summary = []
    print(f"{'name':22s}  {'mean':>8s}  {'sd':>6s}  "
          f"{'95% Wald lo':>12s}  {'95% Wald hi':>12s}  "
          f"{'z':>6s}  {'p_two':>8s}")
    for i, name in enumerate(names):
        m, s = float(fe_mean[i]), float(fe_sd[i])
        lo, hi = m - 1.96 * s, m + 1.96 * s
        z = m / s if s > 0 else float("inf")
        p_two = wald_p_two(z)
        print(f"{name:22s}  {m:+8.4f}  {s:6.4f}  {lo:+12.4f}  {hi:+12.4f}  "
              f"{z:+6.2f}  {p_two:8.4g}")
        fe_summary.append({
            "name": name, "mean": m, "sd": s,
            "ci95_low": lo, "ci95_high": hi,
            "z": z, "p_wald_two": p_two,
        })

    print("\n## Random-effect variance components (posterior on log SD)")
    vcp_summary = []
    for i, name in enumerate(vc_names):
        log_sd_mean = float(vcp_mean[i])
        log_sd_sd = float(vcp_sd[i])
        sd_mean = math.exp(log_sd_mean)
        sd_lo = math.exp(log_sd_mean - 1.96 * log_sd_sd)
        sd_hi = math.exp(log_sd_mean + 1.96 * log_sd_sd)
        var_mean = sd_mean ** 2
        var_lo = sd_lo ** 2
        var_hi = sd_hi ** 2
        print(f"  sigma_{name:7s}: SD mean = {sd_mean:.4f}  95% [{sd_lo:.4f}, {sd_hi:.4f}]  "
              f"var = {var_mean:.4f}  95% [{var_lo:.4f}, {var_hi:.4f}]")
        vcp_summary.append({
            "name": name,
            "log_sd_mean": log_sd_mean,
            "log_sd_sd": log_sd_sd,
            "sd_mean": sd_mean, "sd_ci95_low": sd_lo, "sd_ci95_high": sd_hi,
            "var_mean": var_mean, "var_ci95_low": var_lo,
            "var_ci95_high": var_hi,
        })

    # Approximate LRT-style: refit reduced model (drop cond + all
    # cond_x_*). Report Δ(2·ELBO) and an *approximate* chi-square p with
    # df = 4 (cond + 3 interactions). Flag as approximate because ELBO is a
    # lower bound on log marginal likelihood, not the likelihood itself.
    print("\n## Approximate LRT for joint effect of condition "
          "(cond + 3 cond×* interactions, df=4)")
    try:
        model_red, result_red = fit_no_cond(df)
        # vb_elbo signature: (vb_mean, vb_sd). VB mean/sd vectors are
        # concatenated [fe || vcp || vc] in that order; their full
        # vectors live in `result.params` and `result.cov_params()` SDs.
        # We reconstruct them from the result attributes.
        full_mean = np.concatenate([result.fe_mean, result.vcp_mean,
                                    result.vc_mean])
        full_sd = np.concatenate([result.fe_sd, result.vcp_sd,
                                  result.vc_sd])
        red_mean = np.concatenate([result_red.fe_mean,
                                   result_red.vcp_mean,
                                   result_red.vc_mean])
        red_sd = np.concatenate([result_red.fe_sd, result_red.vcp_sd,
                                 result_red.vc_sd])
        elbo_full = float(model.vb_elbo(full_mean, full_sd))
        elbo_red = float(model_red.vb_elbo(red_mean, red_sd))
        D = 2.0 * (elbo_full - elbo_red)
        from math import erf, sqrt
        # chi-square survival with df=4: 1 - F(D; df=4)
        # We use scipy.stats.chi2 if available; else fall back to a
        # crude bound.
        try:
            from scipy.stats import chi2
            p_lrt = float(chi2.sf(D, df=4))
        except Exception:
            p_lrt = float("nan")
        print(f"  ELBO_full      = {elbo_full:.4f}")
        print(f"  ELBO_reduced   = {elbo_red:.4f}")
        print(f"  D ≈ 2(ΔELBO)   = {D:.4f}")
        print(f"  approx LRT p   = {p_lrt:.4g}   (df=4, approximate under VB)")
        lrt_summary = {
            "elbo_full": elbo_full, "elbo_reduced": elbo_red,
            "D_approx": D, "df": 4, "p_lrt_approx": p_lrt,
            "note": "ELBO-based; lower bound on log marginal likelihood",
        }
    except Exception as exc:
        print(f"  Approximate LRT skipped: {exc}")
        lrt_summary = {"error": str(exc)}

    # Per-cell predicted marginal contrasts
    module_blups = extract_module_blups(result)
    print("\n## Module random-effect BLUPs (logit-scale posterior means)")
    for k, v in sorted(module_blups.items()):
        print(f"  u_module[{k:14s}] = {v:+.4f}")

    print("\n## Per-cell predicted marginal contrasts (cold − mismatched)")
    contrasts = per_cell_contrasts(fe_mean, fe_sd, names, CELLS_META,
                                   module_blups)
    print(f"{'cell':30s}  {'p̂_cold':>8s}  {'p̂_mm':>6s}  "
          f"{'Δ̂':>7s}  {'CI95 low':>9s}  {'CI95 high':>9s}")
    for c in contrasts:
        print(f"{c['label']:30s}  {c['p_cold_hat']*100:7.1f}%  "
              f"{c['p_mismatched_hat']*100:5.1f}%  "
              f"{c['delta_hat']*100:+6.1f}pp  "
              f"{c['ci95_low']*100:+8.1f}pp  {c['ci95_high']*100:+8.1f}pp")

    out = {
        "model": {
            "formula": ("detected ~ cond + fam_opus + fam_gemini + "
                        "libclass_tp + cond_x_opus + cond_x_gemini + "
                        "cond_x_libclass"),
            "random_effects": {"bug": "0 + C(bug_uid)",
                               "module": "0 + C(module)"},
            "fit_method": "variational_bayes (BinomialBayesMixedGLM.fit_vb)",
            "n_rows": int(len(df)),
            "n_bug_clusters": int(df["bug_uid"].nunique()),
            "n_module_clusters": int(df["module"].nunique()),
            "seed": SEED,
        },
        "fixed_effects": fe_summary,
        "random_effect_variances": vcp_summary,
        "approx_lrt_condition_block": lrt_summary,
        "per_cell_contrasts": contrasts,
    }
    out_path = ROOT / "results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
