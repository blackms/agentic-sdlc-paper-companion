# Phase 7 Report — C1 Replicated Across Two Domains (Ablation-Controlled)

> **Status**: Phase 7 replicates the Phase-6 C1 finding (cold reviewer domain transfer via auto-extracted contracts) on a second, structurally unrelated domain (a hand-written JSON parser). All three pre-registered metrics pass, including a Bonferroni-corrected paired McNemar test. **C1 is now "replicated across two domains, ablation-supported", not "generalized"** — additional domains are required for the latter claim.

## P7 — JSON parser replication of C1

### Pre-registration (frozen 2026-05-10)

Committed before any P7 LLM calls in `experiments/p7_parser/PREREGISTRATION.md`. Key elements:

- Hand-write a minimal JSON parser reference (~200 LOC, recursive descent, NOT copied from a real library).
- Inject 15 single-line bugs across 7 categories (off-by-one, contract, logic, precision, atomicity, currency-as-locale, exception).
- Auto-extract contracts from the REF via single Codex call (no bug-aware guidance).
- Run cold reviewer with **aligned** parser contracts (PRIMARY).
- **Ablation**: run cold reviewer with **mismatched** bankcheck contracts on the same parser bugs.
- Pre-registered metrics:
  - Primary: cold detection (aligned) > 50%.
  - Ablation: cold detection (mismatched) < 30%.
  - Specificity: aligned − mismatched ≥ 20 percentage points.

### Detection rate per role at n = 15

| Role | Caught / Parsed | Rate |
|---|---|---|
| warm | 12/15 | 80.00% |
| **cold (aligned, parser contracts)** | **10/10** | **100.00%** ← PRIMARY |
| **cold_mismatched (bankcheck contracts on parser)** | **4/15** | **26.67%** ← ABLATION |
| skeptic | 12/14 | 85.71% |
| simm1 | 12/15 | 80.00% |
| simm2 | 11/14 | 78.57% |
| simm3 | 10/13 | 76.92% |

### Pre-registered metrics outcome

| Metric | Threshold | Result | Verdict |
|---|---|---|---|
| Primary (cold aligned) | > 50% | **100.00%** | **PASS** |
| Ablation (cold mismatched) | < 30% | **26.67%** | **PASS** |
| Specificity (aligned − mismatched) | ≥ 20 pp | **73.3 pp** | **PASS** |

### Paired McNemar (cold_aligned vs cold_mismatched, same bugs)

```
n_paired = 10
discordant: b = 0 (aligned miss / mismatched catch)
            c = 7 (aligned catch / mismatched miss)
McNemar one-sided p (H1: aligned > mismatched) = 0.0078
```

**Bonferroni-corrected family-wise α = 0.05 (per-test α = 0.010): PASSES.**

This is the strongest paired-McNemar effect we have measured in the entire paper: discordant counts (0, 7) are maximally asymmetric — every bug where the two cold variants disagree is one that the aligned variant catches.

### Per-condition q (≥ 2 reviewer miss)

| Condition | q | n_eff |
|---|---|---|
| `asymm-codex` (cold aligned) | **0.1111** (1/9) | 9 |
| `asymm-codex-mismatched` (cold mismatched) | 0.2143 (3/14) | 14 |
| `symm-mono` | 0.2500 (3/12) | 12 |

## Cross-domain comparison: C1 in two domains

| Domain | Cold (mismatched/finance) | Cold (aligned) | Δ | McNemar p |
|---|---|---|---|---|
| **bankcheck.py** (CI checks, P6.1) | 11.11% (3/27) | 73.08% (19/26) | +62 pp | not formally tested |
| **JSON parser** (P7) | 26.67% (4/15) | 100.00% (10/10) | +73 pp | **0.0078, BONF✓** |

In both domains the cold reviewer with aligned auto-extracted contracts outperforms the cold reviewer with mismatched contracts by 60+ percentage points. The parser domain replication adds the formal Bonferroni-significant paired McNemar test that P6.1 lacked due to small n and symmetric discordants.

## Honest claim positioning (peer-review-mediated)

The Codex peer review of P7 returned **REQUEST_CHANGES** specifically on claim scope:

> "C1 è ora **replicated across two domains**, non 'generalizable' in senso pieno. La formulazione corretta è: *'C1 shows strong evidence across two distinct domains, with ablation support for domain-aligned contracts as the causal ingredient.'* Non: *'C1 is generalizable.'* Per arrivare lì servono almeno 4-6 domini eterogenei, codebase non giocattolo, contratti rumorosi/incompleti, e reviewer diversi."

The Gemini peer review returned **APPROVE** with the same caveat: *"C1 al momento è ancora 'two-domain only'."*

We adopt the Codex framing. The paper-v0.6 claim language for C1 is:

> **C1 (Two-domain replication of cold reviewer transfer, ablation-controlled)**: in two structurally unrelated code domains (bankcheck CI checks, ~600 LOC; JSON parser, ~200 LOC), auto-extracting contracts from the domain reference and supplying them to the cold contract-first reviewer recovers detection rate from misaligned-baseline (11–27%) to aligned-detection (73–100%). Ablation in P7 with mismatched contracts confirms the domain-alignment is the causal ingredient (paired McNemar p = 0.0078 under Bonferroni). C1 is *replicated*, not *generalized*: two domains is not "general" — full generalization requires 4–6 heterogeneous domains, real codebases, noisy/incomplete contracts, and reviewer-family variation.

## Limitations honestly catalogued

1. **n = 15 P7 sample size**. Bonferroni-significant paired result, but the effect needs to hold at scale and on noisier code.
2. **JSON parser is "clean"**. Hand-written REF, single-file, idiomatic Python. Real codebases are multi-file, with implicit contracts and idiom drift.
3. **Codex training-data familiarity**. Parser code is plausibly well-represented in Codex's pretraining; this may inflate detection rates *generally* (not specifically for the aligned-vs-mismatched contrast, which is what we measure).
4. **Reviewer family fixed**. All cold/warm/skeptic/symm runs use Codex (`gpt-5.5`); only `claudeg` is Claude. C1 holds *for this reviewer model on these two domains*; cross-model robustness is not established.
5. **The asymm-codex aggregate q (11%)** is lower than symm-mono (25%) but n = 9–12 paired is too small for a formal P2-style test in this domain. We do not claim P2 transfer to JSON parser in aggregate.

## Updates to the paper

The v0.6 paper should:

1. **Promote C1 to "two-domain replicated, ablation-controlled"** in abstract and §5.
2. **Add §5.x "Two-domain replication of C1"** with both bankcheck and parser tables side by side.
3. **Add §9.x "What C1 does NOT show"** with the 5 limitations above. Most important: "two domains ≠ general; full generalization requires 4–6 heterogeneous domains, real codebases, noisy contracts."
4. **The eight failure modes**: "out-of-domain prompt collapse" failure mode now has a *replicated* recovery mechanism, not just a single-instance one. Update the catalogue accordingly.

## Phase 7 deliverables

```
experiments/p7_parser/
  PREREGISTRATION.md                     frozen protocol (2026-05-10)
  ref/jsonparse.py                       hand-written JSON parser (~200 LOC)
  bugs_p7.yaml                           15 bug schema, 7 categories
  bugged/P7_B*.py                        15 bugged versions
  contracts/parser_contracts.md          auto-extracted, 149 lines
  contracts/parser_contracts_raw.txt     full Codex extraction transcript
  reviews/cold_P7_B*.raw.txt             15 reviews (aligned)
  reviews/cold_mismatched_P7_B*.raw.txt  15 reviews (ablation)
  reviews/{warm,skeptic,simm1-3}_P7_B*.raw.txt  reviews for full-condition reconstruction
  inject_bugs.py, analyze_p7.py          reproducibility scripts
  results/p7_analysis.json               full numerical output
```

## Honest summary

P7 **replicates C1 across two unrelated domains** with all three pre-registered metrics passing and the paired McNemar Bonferroni-significant. The cold reviewer's domain-transferability via auto-extracted contracts is the only positive Phase-5/6/7 result that survives every adversarial check we have run on it. The claim is now strong enough to label **C1 as a confirmed empirical finding in the paper** — bounded by "two domains, controlled reviewer, single model family" — but explicitly distinguished from a "general" claim.
