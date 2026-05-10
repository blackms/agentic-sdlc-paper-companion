# Phase 9 Report — Real Codebases, AST Mutator: C1 Specificity Generalizes, Absolute Threshold Falsified

> **Status**: Phase 9 generalized C1 from 5 hand-written domains (P6/P7/P8) to 3 real Python stdlib codebases (`csv.py`, `urllib/parse.py`, `json/decoder.py`) using AST-level mutations rather than text substitution. Headline: **the specificity dimension of C1 generalizes massively (Fisher combined p = 2.4·10⁻¹¹), but the pre-registered absolute primary threshold "cold > 50%" fails on real codebases (3/3 strict, 1/3 with-parsed-policy).**

## Pre-registration (frozen 2026-05-10)

`experiments/p9_real/PREREGISTRATION.md` was committed before any reviewer call.

3 stdlib targets:

| Domain | Source | LOC | Total valid AST mutations | Sampled |
|---|---|---|---|---|
| `csv_dom` | `csv.py` | 451 | 53 | 30 |
| `urllib_dom` | `urllib/parse.py` | 1246 | 98 | 30 |
| `jsondec_dom` | `json/decoder.py` | 356 | 58 | 30 |

AST-level mutators (PRIORITY 1): AOR (`+↔−`, `*↔/`, `//↔%`), ROR (`==↔!=`, `<↔<=`, `>↔>=`), BOR (`and↔or`). Each mutant validated to compile + import. **Yield 100%** vs Phase 8's 44% — the protocol failure of P8 is fully resolved.

## Bug-injection yield

| Domain | Target | Generated | Yield |
|---|---|---|---|
| csv_dom | 30 | 30 | 100% |
| urllib_dom | 30 | 30 | 100% |
| jsondec_dom | 30 | 30 | 100% |

## Reviewers

7 Codex roles per bug × 3 domains × 30 bugs = **630 Codex review calls** (all completed). Each role gets a frozen prompt and either:
- `cold`: domain-aligned auto-extracted contracts (extracted from the *original* stdlib reference, not the bugged file).
- `cold_mismatched`: bankcheck CI/finance contracts (categorical mismatch from finance to stdlib).
- `warm`, `skeptic`, `simm1`, `simm2`, `simm3`: standard prompts.

## Detection criteria

Each AST mutation's "ground truth" detection is encoded by:
- The bug line number ±2 (matched as a number in `bugs_found`), OR
- The enclosing function/class name AND ≥1 operator keyword (`%`/modulo, `//`/floor division, `==`/equal, etc.).

This is auto-derived from the manifest in `experiments/p9_real/build_detection.py`; **no human inspection of reviews before classification**.

## Per-domain results

| Domain | warm | cold (PRIMARY) | cold_mismatched (ABLATION) | skeptic | simm1 | simm2 | simm3 | Δ (pp) |
|---|---|---|---|---|---|---|---|---|
| csv_dom (n=30) | 6.67% | 43.33% | **0.00%** | 60.00% | 76.67% | 66.67% | 60.00% | **43.3** |
| urllib_dom (n=30) | 43.33% | 50.00% | **0.00%** | 50.00% | 46.43% | 48.28% | 58.62% | **50.0** |
| jsondec_dom (n=30) | 6.67% | 52.00% (n=25) | **0.00%** | 39.13% (n=23) | 51.85% (n=27) | 56.00% (n=25) | 52.00% (n=25) | **52.0** |

Strict (unparsed-as-miss) policy:

| Domain | cold strict | cold_mm strict | Δ strict (pp) |
|---|---|---|---|
| csv_dom | 43.33% | 0.00% | 43.3 |
| urllib_dom | 50.00% | 0.00% | 50.0 |
| jsondec_dom | 43.33% | 0.00% | 43.3 |

## Pre-registered metrics — per-domain verdict

| Metric | csv_dom | urllib_dom | jsondec_dom |
|---|---|---|---|
| **Primary** cold > 50% (parsed-only) | ✗ (43.3%) | ✗ (50.0%) | ✓ (52.0%) |
| **Primary** cold > 50% (strict) | ✗ (43.3%) | ✗ (50.0%) | ✗ (43.3%) |
| **Ablation** cold_mismatched < 30% | ✓ (0%) | ✓ (0%) | ✓ (0%) |
| **Specificity** Δ ≥ 20pp | ✓ (43pp) | ✓ (50pp) | ✓ (52pp) |
| **McNemar paired** (cold > cold_mismatched), p < 0.010 | ✓ (p=0.000122) | ✓ (p=0.000031) | ✓ (p=0.000122) |

**Primary threshold cold > 50%: 1/3 PASS (parsed-only) → 0/3 PASS (strict). The absolute-detection criterion is falsified on real stdlib code.**
**Specificity dimension (Δ ≥ 20pp + ablation < 30% + McNemar p < 0.010): 3/3 PASS in both policies.**

## Cross-domain Fisher's combined (P7 + 3 P9)

```
P7 (json_parser, P7 hand-written): p = 0.0078   (n=10, b=0, c=7)
csv_dom                          : p = 0.000122 (n=30, b=0, c=13)
urllib_dom                       : p = 0.000031 (n=30, b=0, c=15)
jsondec_dom                      : p = 0.000122 (n=25, b=0, c=13)

Fisher χ²(8) = 66.5453
Combined p   = 2.386·10⁻¹¹
```

**Combined p = 2.4·10⁻¹¹ ≪ pre-registered primary threshold p < 0.001.** Strong cross-domain evidence on the specificity dimension.

## Honest framing

C1 has two distinct dimensions:
1. **Specificity** — cold-aligned contracts beat categorically-mismatched contracts. **Generalized**: 3/3 P9 stdlib domains, with `cold_mismatched = 0%` everywhere (perfect ablation), Δ ∈ [43, 52] pp, per-domain McNemar p < 0.001, Fisher combined p = 2.4·10⁻¹¹.
2. **Absolute detection** — cold detection > 50%. **Falsified on real codebases**: 0/3 under strict policy, 1/3 under parsed-only. urllib (1246 LOC) and csv (451 LOC) sit at 50% / 43% strict.

Pre-registration committed both dimensions. The specificity dimension passes by orders of magnitude; the absolute dimension fails. **We accept C1's specificity claim as generalized; we accept the absolute-threshold claim as falsified on realistic code.**

A secondary surprise: on csv_dom, generic prompts (simm1 76.67%, simm2 66.67%, skeptic 60%) substantially exceed cold (43.33%). The cold prompt's contract framing does *not* dominate other prompts uniformly — it dominates only the categorically-mismatched control. This narrows the practical claim: aligned contracts protect against mismatched contracts, not against well-engineered generic prompts.

## Updated C1 statement (for paper v0.8)

> **C1 (Cold reviewer transfer, specificity dimension generalized; absolute-threshold dimension falsified on realistic code)**: across two pilot domains (bankcheck CI, JSON parser), three Phase-8 hand-written pilots (expression evaluator, regex compiler, HTTP header parser), and **three Phase-9 real Python stdlib codebases (csv, urllib.parse, json.decoder, n = 30 AST-level mutations each, yield 100%)**, auto-extracting contracts from the domain reference produces a **specificity advantage** over categorically-mismatched contracts that generalizes strongly: cold_mismatched = 0% on all 3 stdlib domains, Δ ∈ [43, 52] pp, per-domain paired McNemar p < 0.001, **Fisher's combined cross-domain p = 2.4·10⁻¹¹** (P7 + 3 P9). The **absolute-detection threshold "cold > 50%" is falsified on realistic stdlib codebases** under the strict (unparsed-as-miss) policy, passing in 0/3 P9 domains. Cold detection sits at 43–52% on real codebases and is sometimes exceeded by well-engineered generic prompts (simm1 reaches 76.67% on csv). The protocol's contract-first framing protects against domain-mismatched contracts (a meaningful failure mode) but does not uniformly dominate other prompt strategies on real code.

## Limitations honestly catalogued (P9-specific)

1. **Stdlib training-data bias**: csv/urllib/json are heavily represented in Codex pretraining. P10 desideratum: lesser-known third-party libraries.
2. **Single-mutation bugs**: each bugged file has exactly one AST-level operator change. Naturalistic bugs are typically multi-line and span data-flow patterns. P10 desideratum: multi-mutation chains, inter-procedural bugs.
3. **Reviewer-family variation deferred**: P9 used Codex (gpt-5.5) as the only reviewer family. Opus 4.7 cold-reviewer subagent on 2 P9 domains was scoped but not run for v0.8 (60 Opus calls). The within-Codex generalization is itself novel and supports the specificity claim; cross-family confirmation is a v0.9 task.
4. **Detection-criterion strictness**: line ±2 OR (enclosing function name + operator keyword). Looser criteria would inflate all rates uniformly; the *contrast* is robust.
5. **Cold detection 43–52% on real code**: meaningful gap from the 50–80% rate on hand-written domains. Real codebases test the protocol harder.

## Phase 9 deliverables

```
experiments/p9_real/
  PREREGISTRATION.md          (frozen 2026-05-10)
  ast_mutator.py              (AST-level mutator, ~270 LOC)
  build_detection.py          (auto-builds per-bug detection criteria)
  analyze_p9.py               (per-domain + Fisher cross-domain)
  csv_dom/{ref/, bugged/, contracts/, reviews/, detection.json}
  urllib_dom/{...}
  jsondec_dom/{...}
  results/p9_analysis.json
  launch_reviews.sh
```

## Next phase desiderata

- **P10.1 reviewer-family**: Opus 4.7, GPT-5, Gemini 2.5 Pro on the same 90 P9 bugs.
- **P10.2 third-party libraries**: pick 2 mid-popularity (e.g., `python-dateutil`, `chardet`) for less training-data presence.
- **P10.3 multi-mutation**: chain 2–3 AST mutations per bug; inter-procedural data-flow bugs.
- **P10.4 absolute detection**: investigate the 43–52% ceiling on stdlib — are some operator changes semantically inert (e.g., `<` vs `<=` on edge cases)?
