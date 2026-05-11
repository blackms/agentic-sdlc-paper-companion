# Pre-registration — Phase 11 Replication at n=100 (Stream C)

**Date frozen**: 2026-05-11
**Branch**: `v1.4/exp-p11-rep`
**Working dir**: `.worktrees/exp-p11-rep/experiments/p11_replication/`
**Stream-D-variant**: (not applicable to Stream C)

## Motivation

v1.3 P11 was underpowered (n=30 per cell; power to detect Δ ≥ 20 pp at base ~45–50% was high, but Δ ≤ 10 pp effects could not be detected). The v1.3 conclusion ("anti-stdlib carelessness as the dominant mechanism: not supported") leaves a ≤ 10 pp residual undetectable. Stream C bounds the residual at n=100 per cell.

## Hypotheses (frozen)

- **H1a (csv stdlib → fake third-party label)**: relabeled detection rate > truthful detection rate (anti-stdlib carelessness hypothesis: removing the "trusted stdlib" prior should increase scrutiny). One-sided.
- **H1b (chardet third-party → fake stdlib label)**: relabeled detection rate < truthful detection rate (label-bias hypothesis: adding the "trusted stdlib" prior should decrease scrutiny). One-sided.
- **H0**: no detection difference between truthful and relabeled conditions.

## Metrics

- **Primary**: per-cell paired McNemar exact one-sided p-value.
- **Secondary 1**: cluster-robust paired permutation (n_perm = 20,000) one-sided p-value.
- **Secondary 2**: percentile-bootstrap 95 % CI on Δ (cold_relabeled − cold_truthful).

## α threshold

- **0.025 per cell** (Bonferroni-corrected for 2 cells × 1 family).
- Family-wise α = 0.05.

## Sample size & power

- n = 100 per cell (= 100 truthful + 100 relabeled per side; 200 paired Codex calls per side; **400 total Codex calls**).
- **Correction to plan.md / budget.md**: the planner doc cites 600 calls (200 paired × 2 sides + 100 buffer). The frozen sample is 100 per side × 2 sides × 2 conditions = 400 calls. Buffer for retries: +50, so plan for ≤ 450 calls.
- Power to detect Δ = 10 pp at base ~45-50 % with α = 0.025 paired one-sided: ~0.80 (computed via simulation in `experiments/p11_replication/power.py`, committed alongside this pre-reg).

## Inclusion / exclusion criteria

- **Same 30 P11 bugs reused identically** + 70 new AST mutations per side on same modules with same operator-mix proportions.
- AST mutator: `experiments/p9_real/ast_mutator.py` (frozen, sha256 verified).
- Seed: `20260511` (v1.4 epoch, distinct from v1.3 seed `20260510`).
- Operator-mix: stratified to match v1.3 distribution on the same module (AOR/ROR/BOR proportions identical).
- New bugs hashed: sha256 of the bug-id ↔ mutation-spec manifest committed at start.

## Cover stories (frozen, byte-identical to v1.3)

For csv bugs:
```
This code is from `csv_processing`, a niche third-party Python library for CSV manipulation (not part of the Python standard library). The library has approximately 500 downloads/month on PyPI. Treat this as unfamiliar third-party code.
```

For chardet bugs:
```
This code is from `charset_module`, part of the Python standard library, available as `from charset_module import ...` since Python 3.10. Treat this as standard-library code.
```

## Reviewer

- Codex `gpt-5.5` only (same family as v1.3 P11; this is a replication, not a cross-family extension).
- Cross-family extension is Phase-12 desideratum, not in scope for Stream C.

## Decision rules

| Outcome | Interpretation |
|---|---|
| Both H1a and H1b reach p < 0.025 | Anti-stdlib carelessness + label-bias **confirmed** as contributors at the n=100 power; effect magnitudes reported with 95% CIs. |
| Exactly one of H1a / H1b reaches p < 0.025 | Asymmetric label effect: report direction explicitly; partial confirmation. |
| Both p ≥ 0.025 | **v1.3 conclusion stands** at higher power: residual label effect bounded by detected CI bounds (likely ≤ ~10 pp); v1.4 §7.9 reports the tighter bound. |
| Significance reverses sign from v1.3 directional trend (e.g., csv relabel now decreases detection) | **Protocol halt #6**: re-read §1, §7.9, §8 conclusions; empirically informative either way but requires reframing. |

## Risks acknowledged

1. **70 new bugs may have different difficulty distribution.** Mitigation: same operator-mix proportions, frozen seed, sha256 the mutation set. Sanity: compute per-bug detection rate under TRUTHFUL condition only and compare to v1.3 distribution; report if KS test rejects same-distribution.
2. **Codex `gpt-5.5` may have drifted between v1.3 (2026-05-10) and v1.4 (~2026-05-13).** Mitigation: re-run truthful condition concurrently with relabeled on the same call schedule; the drift is absorbed in the truthful baseline. Report observed drift on the 30 reused bugs as a separate diagnostic.
3. **Cover-story plausibility unchanged** (csv.py is widely known to be stdlib; cover may be detectable). Mitigation: out-of-band probe asks reviewer to identify the actual library source (does NOT enter detection metric). Report cover-detection rate as diagnostic.
4. **Rate limits** (Codex auth refresh observed in v1.3): chunked execution CHUNK=12 with retry, expected 10 % overhead.

## Validation script

`experiments/p11_replication/analyze.py` — recomputes p-values, CIs, contingency tables from raw outputs. Frozen at this pre-registration commit.

## Discipline statements

- This pre-registration is committed **before any reviewer call**.
- No prompt changes between v1.3 and v1.4 (sha256 of `cold_bankcheck.txt` and the two cover-story prefixes verified at first call).
- No detection-criterion changes (same AST-derived line/function-name match).
- No iteration on prompts, contracts, sampling, or detection after observing results.
- Raw outputs all committed.

## After running

- §7.9 in v1.4 main paper reports: v1.3 (n=30) vs v1.4 (n=100) side-by-side table with per-cell Δ, 95 % CI, p-values from both primary (McNemar) and secondary (permutation) tests.
- Drift diagnostic (Codex v1.3 vs v1.4 baseline on the 30 reused bugs) reported as footnote.
