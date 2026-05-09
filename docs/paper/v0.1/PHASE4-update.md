# Paper v0.2 — Phase 4 Update

> **Status**: Phase 4 scaling completed. Bonferroni-corrected significance achieved on the central T2 hypothesis. Below is the diff vs v0.1, with the corrected numerical claims and the updated propositions. The validation scripts in `validations/` reproduce every number.

## What changed in Phase 4

### T1 (P1): from 2 models / 80 trajectories → 4 frontier models / 120 trajectories

The four frontier models tested:

- **OpenAI Codex** (`gpt-5.5`) via `codex exec` CLI — 60 trajectories
- **Anthropic Claude Sonnet 4.6** via subagent — 20 trajectories
- **Anthropic Claude Opus 4.7** (1M-context) via subagent — 20 trajectories (NEW Phase 4)
- **Google Gemini 2.5 Flash** via gemini-cli — 20 trajectories (NEW Phase 4)

### T2 (P2): from 80 → 200 single-line bugs

The T2 benchmark was extended from 80 to 200 single-line bugs (B81–B200 in `t2/bugs.yaml`), broadening the seven categories with subtler mutations (exception-type variants, off-by-cent, hardcoded shortcuts, partial-state atomicity, currency-case asymmetries, type-coercion). 1,400 LLM reviews total (200 bugs × 7 reviewers).

## Updated headline numbers

### P1 across 4 frontier models — eFOSD on 80 thresholds

| Task | Model | ΔE[u] (95% CI) | log(K_P / K_{P_0}) | λ_breakeven | eFOSD on Θ |
|---|---|---|---|---|---|
| compound_interest | Codex | +0.783 [+0.721, +0.838] | 2.189 | 0.358 | 10/10 |
| compound_interest | Claude Sonnet 4.6 | +0.675 [+0.575, +0.775] | 3.149 | 0.214 | 10/10 |
| compound_interest | **Claude Opus 4.7** | **+0.617 [+0.542, +0.706]** | 2.653 | 0.233 | 10/10 |
| compound_interest | **Gemini 2.5 Flash** | **+0.733 [+0.625, +0.858]** | 3.278 | 0.224 | 10/10 |
| transfer | Codex | +0.753 [+0.712, +0.790] | 1.647 | 0.457 | 10/10 |
| transfer | Claude Sonnet 4.6 | +0.647 [+0.493, +0.791] | 1.181 | 0.548 | 10/10 |
| transfer | **Claude Opus 4.7** | **+0.587 [+0.458, +0.724]** | 0.860 | 0.682 | 10/10 |
| transfer | **Gemini 2.5 Flash** | **+0.774 [+0.539, +0.956]** | 0.696 | **1.113** | 10/10 |

**Result**: empirical FOSD on the tested grid holds in **80 / 80 cells × thresholds (8 cells × 10 thresholds)** across **four frontier models**. The 95% bootstrap CI on ΔE[u] excludes 0 in every cell.

`λ_breakeven` now ranges from **0.214 (compound × Sonnet)** to **1.113 (transfer × Gemini)** — a 5.2× spread across model and task. The Gemini transfer cell achieves the highest break-even because Gemini's `P₀` baseline is unusually low (E[u] ≈ 0.13) while the protocol gain is high (ΔE[u] = +0.774), and the token-cost ratio is small (0.696 in log-space).

### P2 at n = 200 — Bonferroni-corrected significance

```
H1 : P(asymm-multi)  <  P(symm-mono)
     P(asymm-multi)  =  21/171 = 12.28%
     P(symm-mono)   =  41/179 = 22.91%
     ΔP             =  −10.62 percentage points
     Fisher exact one-sided p  =  0.0066
     Bonferroni-adjusted α      =  0.05 / 5  =  0.010
     Verdict                    =  SIGNIFICANT under Bonferroni  ✓
```

(`n_eff` differs across conditions because we treat parse failures of an LLM review as missing data, not as a miss; counts are the survivors.)

### All 5 hypothesis tests at n = 200

| H1 | a/n_a | b/n_b | Fisher p (one-sided) | α=0.05 | Bonferroni α=0.010 |
|---|---|---|---|---|---|
| `asymm-codex < symm-mono` | 22/163 | 41/179 | 0.0173 | SUPPORTED | not significant |
| `symm-multi < symm-mono` | 34/182 | 41/179 | 0.1951 | not | not |
| **`asymm-multi < symm-mono`** | **21/171** | **41/179** | **0.0066** | **SUPPORTED** | **SIGNIFICANT ✓** |
| `asymm-multi < asymm-codex` | 21/171 | 22/163 | 0.4329 | not | not |
| `asymm-multi < symm-multi` | 21/171 | 34/182 | 0.0650 | marginal | not |

**The central claim of P2 — that the full asymmetric-multi-model condition reduces joint-miss rate over the symmetric-mono baseline — passes Bonferroni-corrected family-wise α = 0.05 at n = 200.**

### Per-role detection at n = 200

| Role | Model × Prompt | Detection (caught/n) | Wilson 95% CI |
|---|---|---|---|
| `warm` | Codex / warm prompt | 143/184 = 77.7% | [71.2%, 83.1%] |
| `cold` | Codex / contract-first | 149/187 = 79.7% | [73.3%, 84.8%] |
| `skeptic` | Codex / skeptic prompt | 165/184 = 89.7% | [84.3%, 93.3%] |
| `symm1` | Codex / generic | 151/190 = 79.5% | [73.0%, 84.7%] |
| `symm2` | Codex / generic | 145/192 = 75.5% | [68.9%, 81.2%] |
| `symm3` | Codex / generic | 143/195 = 73.3% | [66.7%, 79.1%] |
| `claudeg` | Claude Sonnet / generic | **187/199 = 93.97%** | [89.8%, 96.5%] |

The Claude-vs-Codex *model-strength ceiling* persists at n = 200: Claude generic still outperforms every Codex configuration.

### Decorrelation mechanism, n = 200

```
ρ̄ across the four conditions (mean pairwise φ):

symm-mono  (3× generic Codex)              =  +0.616
symm-multi (Codex + Codex + Claude generic) =  +0.342
asymm-codex (warm + cold + skeptic Codex)   =  +0.359
asymm-multi (warm Codex + cold Codex + Claude generic)  =  +0.289
```

ρ̄ drops from 0.616 to 0.289, a **2.13× reduction** (vs 3.3× at n = 80; the larger sample shows a more conservative but still substantial decorrelation).

### Joint-miss bound check

Per-pair decomposition `P(M_i ∩ M_j) = p_i p_j + ρ_ij · √(p_i (1-p_i) p_j (1-p_j))` is now an *approximate* identity (small residuals up to 0.0065) due to missing-data handling: the residuals come from pairs where some bugs are missing for one reviewer but not the other. The bound `q ≤ Σ P(M_i ∩ M_j)` holds in all four conditions.

## Statements of the propositions, v0.2

### Proposition P1 (v0.2, no change in form, strengthened evidence)

Same statement as v0.1 (§7.1). Empirical evidence now: **eFOSD on 80 / 80 cells × thresholds across 4 frontier models, ΔE[u] CI excludes 0 in 8/8 cells.**

### Proposition P2 (v0.2, status upgrade)

Same statement as v0.1 (§7.2). Empirical status changes from "uncorrected significance only" to:

> **At n = 200 single-line bugs and 1,400 LLM reviews, the central contrast `q_asymm-multi < q_symm-mono` is significant under Bonferroni-corrected family-wise α = 0.05 (per-test α = 0.010, Fisher exact one-sided p = 0.0066, ΔP = −10.62 pp).**

The remaining four tests in the family are not significant under Bonferroni; the single-test sweep at α = 0.05 supports `asymm-codex < symm-mono` (p = 0.017) but Bonferroni does not.

### Conjecture C-T3 (unchanged status)

Still simulation-only. Phase 4 did not run an LLM-grounded learning loop — that was descoped to Phase 5 to prioritize the Bonferroni gap, which has now been closed.

## Honest disclosures (still applicable in v0.2)

1. **Model-strength ceiling**: Claude Sonnet 4.6 generic continues to outperform Codex with any prompt. The Phase 4 addition of Opus and Gemini does not control for this — all four models are frontier tier with somewhat different capabilities. Tier-comparable replication (Claude Haiku + GPT-4o-mini + Codestral) remains Phase 5 work.

2. **External validity**: still two micro-tasks, single financial domain, single-line bugs. The protocol mechanism may not generalize to multi-file, multi-bug, repository-scale tasks.

3. **Detection by keyword match**: the 5% manual-audit estimate of false-miss rate from v0.1 has not been re-validated at n = 200; we assume it is in the same range.

4. **C-T3 still a conjecture**, not a proposition. LLM-grounded learning-loop empirical evidence remains future work.

## Phase 4 deliverables

Files added:

```
experiments/
  runs/opus_*.py                      20 Opus T1 trajectories
  runs/gemini_*.{raw.txt,py}          20 Gemini T1 trajectories
  t2/bugs.yaml                        extended to 200 bugs (was 80)
  t2/extend_bugs_v2.py                generator for B81–B200
  t2/bugged/B81..B200.py              120 new bugged files
  t2/reviews/{cold,warm,skeptic,simm1,simm2,simm3}_B81..B200.raw.txt
  t2/reviews/claudeg_B81..B200.raw.txt
  t2/reviews/_detection_table.json    refreshed at n=200

docs/paper/v0.1/validations/
  cap4_results.json                   refreshed: 4 models × 2 tasks
  cap5_results.json                   refreshed: n=200, Bonferroni passes
```

The validation scripts (`cap4_validate.py`, `cap5_validate.py`) reproduce every number in this document from the pinned data, deterministically.

## What this changes for the abstract and introduction

The abstract (§00) and introduction (§1) of v0.1 should be updated to:

- Replace **"n = 80 trajectories, 2 models"** with **"n = 120 trajectories, 4 frontier models (Codex / Claude Sonnet 4.6 / Claude Opus 4.7 / Gemini 2.5 Flash)"**.
- Replace **"FOSD verified on all 40 tested utility thresholds"** with **"on all 80 tested utility thresholds (8 cells × 10 grid)"**.
- Replace **"n = 80 injected bugs"** with **"n = 200 injected bugs"**.
- Replace **"Fisher one-sided p = 0.039 (uncorrected)"** with **"Fisher one-sided p = 0.0066, significant under Bonferroni-corrected family-wise α = 0.05 (per-test α = 0.010)"**.
- Update `λ_breakeven` range from `[0.21, 0.55]` to `[0.214, 1.113]`.

These edits are minor in v0.2; the structural propositions are unchanged.

## Phase 5 desiderata (the next gap)

Phase 4 closes the Bonferroni-power gap. The remaining gaps to TIER-1 submission readiness:

1. **C-T3 LLM-grounded**. A learning-loop on a real codebase with 5+ iteration cycles, pattern extraction at each step, and measured regression-rate decay.
2. **Tier-comparable model control**. Replicate T2 with model-strength balanced (e.g. Claude Haiku as the "generic" reviewer instead of Sonnet, against Codex with asymmetric prompts) to disentangle prompt-asymmetry from model-strength.
3. **Repository-scale tasks**. Move beyond function-level toy tasks to SWE-bench-style multi-file repair.
4. **Native token counting**. Replace `char/4` proxy with API-reported tokens.
5. **AST-based conformance scoring** (replace keyword regex).

The paper is now ready for **internal peer-review pre-submission** with the v0.2 numerical updates.
