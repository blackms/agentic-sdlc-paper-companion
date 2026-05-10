# Phase 11 Report — Provenance-Label Experiment: Anti-Stdlib Carelessness Falsified

> **Status**: Pre-registered before any reviewer call (2026-05-10, `experiments/p11_provenance/PREREGISTRATION.md`). Codex peer review on Phase 10 explicitly required: *"manipulate provenance labels, familiarity, and contract source"* to demonstrate anti-stdlib carelessness. **Result: both pre-registered hypotheses fail; anti-stdlib carelessness is rejected as the causal mechanism behind the P9-P10 sample gap.**

## Design

- Stdlib bugs (csv P9, n=30) → relabeled as fake third-party library `csv_processing`.
- Third-party bugs (chardet P10, n=30) → relabeled as fake stdlib module `charset_module`.
- Bugged code: byte-identical across conditions. Auto-extracted contracts: byte-identical.
- Only the 1-line provenance cover story changes.
- Reviewer: Codex gpt-5.5 only (the family with the largest stdlib→third-party gap: 43% → 96.7%).
- 60 review calls total.

## Pre-registered hypotheses

| Hypothesis | Prediction | Result | p (one-sided) | Verdict |
|---|---|---|---|---|
| **H1.csv** | `cold_relabeled_thirdparty` > `cold_truthful_stdlib` (relabeling stdlib as third-party INCREASES detection) | Δ = +6.7pp | 0.3438 | NS, **FAIL** |
| **H1.chardet** | `cold_relabeled_stdlib` < `cold_truthful_thirdparty` (relabeling third-party as stdlib DECREASES detection) | Δ = −10.0pp | 0.1250 | NS, **FAIL** |

Both effects are in the **direction predicted by anti-stdlib carelessness** but neither is statistically significant.

## Detailed table

| Sample | Condition | n | Caught | Rate | Wilson 95% |
|---|---|---|---|---|---|
| csv (P9 stdlib) | truthful_stdlib | 30 | 13 | 43.33% | [27.4, 60.8] |
| csv (P9 stdlib) | relabeled_thirdparty | 30 | 15 | 50.00% | [33.2, 66.9] |
| chardet (P10 third-party) | truthful_thirdparty | 30 | 29 | 96.67% | [83.3, 99.4] |
| chardet (P10 third-party) | relabeled_stdlib | 30 | 26 | 86.67% | [70.3, 94.7] |

Paired contingency tables:

**csv (n=30 paired)**:

| | relabeled-catches | relabeled-misses |
|---|---|---|
| truthful-catches | 11 | 2 |
| truthful-misses | 4 | 13 |

**chardet (n=30 paired)**:

| | relabeled-catches | relabeled-misses |
|---|---|---|
| truthful-catches | 26 | 3 |
| truthful-misses | 0 | 1 |

## Interpretation

The anti-stdlib carelessness hypothesis predicts a substantial directional effect:
- Relabel stdlib as third-party → detection rises (the reviewer scrutinizes harder).
- Relabel third-party as stdlib → detection falls (the reviewer becomes complacent).

**Effects are directionally correct but tiny** (+6.7pp / −10pp) and **statistically indistinguishable from chance** at α = 0.05. With n = 30 per cell, we cannot rule out an effect of magnitude up to ~10pp (the chardet drop is within margin), but **the P9-P10 sample gap of ~50pp on the same reviewer cannot be explained by labels alone**:

| Effect size | Source | Magnitude |
|---|---|---|
| Label-only effect (csv stdlib→3p relabel) | P11 | +6.7pp |
| Label-only effect (chardet 3p→stdlib relabel) | P11 | −10.0pp |
| **Full sample gap (csv→chardet, same Codex reviewer)** | P9 vs P10 | **+53.3pp** |

The label effect accounts for at most **~6-10pp** out of the **~53pp** sample gap. **~40-47pp of the gap is unexplained by labels** and must be driven by code-intrinsic factors:
- mutation salience (operator changes in heavy stdlib idioms vs explicit third-party logic);
- contract extraction quality differences;
- local-invariant clarity;
- contract document length and informativeness;
- baseline complexity of the reference code.

## What Phase 11 establishes

**Anti-stdlib carelessness is rejected as the primary causal mechanism** for the P9-P10 sample gap. The Codex peer-review critique on P10 v1.0 was correct: the v0.9 / v1.0 framings overclaimed. The honest sample-level statement (v1.0.5 abstract) is correct: cold detection differs across samples, but library-class / familiarity-prior **does not causally moderate** the difference at the magnitude observed.

## What Phase 11 does NOT rule out

1. **Larger-magnitude label effects**: with n=30 per cell, we have power to detect ~20pp+ effects. A real ~10pp label effect would not be detected at this sample size with high probability.
2. **Cover-story plausibility**: the relabel claim ("csv.py is a third-party library `csv_processing`") may have been detectable by the reviewer; if Codex internally recognized the code, the manipulation failed.
3. **Cross-family generalization**: P11 used only Codex. Opus and Gemini may respond differently to provenance labels.
4. **Asymmetric label effects**: the csv direction (+6.7pp) is smaller than the chardet direction (−10pp). A label effect may be asymmetric (e.g., "trust stdlib" stronger than "scrutinize third-party").

## Updated framing for paper v1.1

The C1 statement should drop the "anti-stdlib carelessness" mechanism candidate and replace with **code-intrinsic factors as the dominant moderator**:

> **C1 (Cold reviewer transfer — contract-aligned specificity replicates across 3 reviewer families on a 3-library third-party sample; code-intrinsic factors are the dominant moderator of absolute detection)**: the Phase-11 provenance-label experiment (Codex, n=30 per cell on csv stdlib and chardet third-party) tests whether labels/familiarity priors cause the P9-P10 absolute-detection gap. Both pre-registered H1 fail at α=0.05 (csv: +6.7pp, p=0.34; chardet: −10pp, p=0.13). Effects are directionally consistent with a small label-only contribution (~6-10pp) but the full sample gap (~53pp on the same Codex reviewer) cannot be explained by labels alone. Phase-12 desiderata: contract informativeness audit, matched-LOC stdlib/third-party experiments, operator-mix balancing, no-contract baseline.

## Failure-mode taxonomy update

Failure mode "anti-stdlib carelessness" is **REMOVED** from the taxonomy (Phase 10 speculation was rejected by Phase 11 experiment). The renamed failure mode "sample-dependent reviewer-choice sensitivity" remains, but is now annotated as **mechanism unknown** rather than attributed to familiarity priors.

## Deliverables

```
experiments/p11_provenance/
  PREREGISTRATION.md
  launch_p11.sh
  analyze_p11.py
  reviews/csv_relabel_thirdparty_P9c_B*.raw.txt   (30)
  reviews/chardet_relabel_stdlib_P10c_B*.raw.txt  (30)
  results/p11_analysis.json
```
