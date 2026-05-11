# Mixed-effects logistic model — tool choice rationale

Stream B (statistician) for paper v1.4. This directory contains the
mixed-effects logistic-regression re-analysis that promotes mixed-effects
to **primary inference** for C1 cells. Cluster-robust permutation
(`experiments/cluster_robust_c1.py`) becomes the comparator. McNemar exact
remains as the legacy literature comparator.

## Frozen model specification

```
logit P(detect = 1)
  = β_0
  + β_cond            · I(condition = cold)
  + β_family_opus     · I(family    = opus)
  + β_family_gemini   · I(family    = gemini)
  + β_libclass        · I(library_class = third_party)
  + β_cond_x_opus     · I(cond=cold AND family=opus)
  + β_cond_x_gemini   · I(cond=cond=cold AND family=gemini)
  + β_cond_x_libclass · I(cond=cold AND library_class=third_party)
  + u_bug[bug_id]    ~ Normal(0, σ_bug²)      (random intercept per bug)
  + u_module[module] ~ Normal(0, σ_module²)   (random intercept per module/domain)
```

Reference levels: `condition=mismatched`, `family=codex`, `library_class=stdlib`.

Library class assignment:
- stdlib: `csv_dom`, `urllib_dom`, `jsondec_dom`
- third_party: `dateutil_dom`, `parsy_dom`, `chardet_dom`

P11 is **excluded** from the primary fit because its design varies the
cover-story label (treatment of Stream C / §7.9), not the cold-vs-mismatched
contrast. The 14 cells with both `cold` and `cold_mismatched` come from:
P9 stdlib (3 cells × Codex) + P9 csv cross-family (2 cells × Opus, Gemini)
+ P10 third-party (3 domains × 3 families = 9 cells) = **14 cells**, 30
paired bugs per cell, 840 bug-level rows (one per condition per bug).

## Tool ladder (decided 2026-05-11)

Decision priority — fit in this order, stop at the first that converges:

1. **`statsmodels.genmod.bayes_mixed_glm.BinomialBayesMixedGLM`** (PRIMARY).
   Variational Bayes binomial GLMM with normal random effects. The cleanest
   pure-Python option for a binomial outcome with two crossed random effects.
   Produces approximate posterior means and standard deviations for the
   fixed effects (which we report as point estimate ± approximate Wald-style
   95% interval β ± 1.96·SE on the logit scale), plus posterior means for
   the random-effect variances σ_bug² and σ_module². LRT p-values are
   computed by re-fitting nested models (drop each fixed effect, compare
   −2·log-likelihood-bound via χ² with df = 1).

2. **`statsmodels.genmod.generalized_estimating_equations.GEE`** with
   `family=Binomial()`, `cov_struct=Exchangeable()` grouped by `module`
   (fallback A). GEE is not a true random-effects model but provides
   cluster-robust standard errors that approximate the inferential intent
   for our sample size. Use if (1) fails to converge or produces
   pathological estimates.

3. Drop `u_module` (fallback B). Refit (1) with only `u_bug` as random
   effect.

4. Drop both random effects (fallback C). Fit a plain logistic regression
   via `statsmodels.GLM(family=Binomial())` and report cluster-robust
   standard errors via `get_robustcov_results(cov_type='cluster', groups=module)`.

Every fallback step is logged in `fallback_log.md`.

## Tools that were considered and rejected

- **`statsmodels.formula.api.mixedlm`** — Gaussian random-effects only;
  cannot do binomial. Rejected.

- **`pymer4` / R `lme4::glmer`** — Would have been the canonical choice
  (Laplace-approximate ML for binomial GLMM). R is **not installed** on
  the orchestrator's machine (`R --version` returns "command not found"),
  and the orchestrator did not authorize system package install for this
  stream. Rejected on environment grounds.

- **`pyhglm`** — Not in the available environment; pip install would
  succeed but reproducibility across CI/coauthors would be unclear.
  Rejected.

- **Custom Laplace-approximation likelihood** — Possible but introduces
  ~200 lines of numerical code that is itself a reviewer-attack surface.
  Rejected in favour of using vetted statsmodels code paths.

## Pre-registered acceptance criterion

The qualitative finding **cold > cold_mismatched** must survive the
re-analysis: at least 14/14 cells previously significant under permutation
(`results_cluster_robust.json`) must show a positive predicted marginal
contrast (cold − mismatched) with a 95% interval excluding 0, OR the
cross-phase pooled β_cond must remain positive with LRT p < 0.025. Any
cell that flips is documented in `discrepancies.md` (one paragraph
diagnosis, no fix attempt — per protocol constraint).

## Pre-registered risks

- Mixed-effects may flag effects the permutation did not (or vice-versa);
  the qualitative finding must survive in either direction.
- Singular fits (σ_module² → 0) are **acceptable**; we report and do not
  refit.
- Convergence failure triggers the fallback ladder; no further
  specification changes.

## Reproducibility note

- `statsmodels==0.14.6` (upgraded from 0.14.2 to recover compatibility
  with `scipy==1.17.1`'s relocation of `_lazywhere`).
- `numpy==2.2.6`, `pandas==2.3.3`, `scipy==1.17.1`.
- Frozen seed: 20260511.
