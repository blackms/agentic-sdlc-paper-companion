# P8 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: C1 (cold reviewer domain transfer via auto-extracted contracts) generalizes from 2 to 5 domains.

## Domains added in P8

| Domain | Description | LOC target | Heterogeneity vs prior |
|---|---|---|---|
| **exprev** | Expression evaluator (math, AST, operator precedence) | ~170 | New: AST data structure |
| **regex** | Regex compiler (Thompson NFA construction) | ~200 | New: FSM, algorithmic |
| **httphdr** | HTTP header parser (case-insensitive keys, multi-value) | ~150 | New: networking semantics |

Combined with P6.1 (bankcheck) and P7 (JSON parser), Phase 8 brings the total to **5 domains**.

## Protocol per domain

1. Hand-write reference implementation, idiomatic Python, type-hinted.
2. Inject 12 bugs across 6 categories (off-by-one, contract, logic, precision/encoding, atomicity/state, exception). 2 bugs/category.
3. Auto-extract contracts from REF via single Codex call (no bug-aware guidance).
4. Run cold reviewer ALIGNED (domain contracts) on all 12 bugs.
5. **Ablation**: run cold reviewer MISMATCHED (parser_contracts.md from P7 on the new domain).
6. Run warm + skeptic + 3×simm + claudeg.
7. **Reviewer-family variation**: in regex domain, run additional `cold_opus` (Claude Opus 4.7 as cold reviewer with regex contracts).

## Pre-registered metrics

**Per-domain primary**: cold detection (aligned) > 50%.
**Per-domain ablation**: cold detection (mismatched) < 30%.
**Per-domain specificity**: aligned − mismatched ≥ 20pp.
**Per-domain paired McNemar (aligned > mismatched)**: report p-value.

**Cross-domain meta-analysis** (combining P7 + 3 new domains = 4 with paired tests):
- Fisher's combined p-value over the 4 McNemar tests; primary verdict combined p < 0.001.
- Random-effects meta-regression on effect sizes if heterogeneity allows.

**Reviewer-family variation (regex only)**:
- `cold_opus` aligned detection compared to `cold_codex` aligned detection.
- If both pass primary threshold → reviewer-family robustness supported.

## Frozen rules

- All references written before contract extraction.
- Contracts extracted from REF only.
- No iteration on bug substitutions after seeing reviewer outputs.
- All 12 bugs per domain reported regardless of result.

## Risk acknowledgement

Even if all 3 domains pass: 5 hand-written domains is still not "real codebases at scale". Phase 9 desiderata: SWE-bench-style multi-file repair, real GitHub repos, naturalistic bugs.
