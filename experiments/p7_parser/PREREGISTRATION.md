# P7 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: C1 (component-level domain transfer of cold reviewer) generalizes to a second domain.

## Domain choice: JSON parser

Rationale (Codex+Gemini convergence): clear semantic contracts, standard reference, minimal ML-pipeline ambiguity, parser logic familiar but explicit.

**Caveat**: parser code is in Codex training data. We mitigate via:
- Ablation control with MISMATCHED contracts.
- Per-bug attribution (we report cold detection, not just aggregate).

## Protocol

1. Hand-write a minimal JSON parser reference (~150 LOC, plain Python, recursive descent). NOT copied from real library.
2. Inject 15 single-line bugs across 7 categories (same taxonomy as T2): off-by-one, contract, logic, precision, atomicity, currency, exception. (Currency/precision adapted to parser context: numeric literal handling.)
3. Auto-extract contracts from the parser REF via single Codex call (no bug-aware guidance) → `parser_contracts.md`.
4. Run cold reviewer on all 15 bugs with parser_contracts (PRIMARY).
5. **Ablation**: run cold reviewer on all 15 bugs with bankcheck_contracts (MISMATCHED domain) → expected low detection.
6. Run warm + skeptic + 3×simm + claudeg with no change.

## Pre-registered metrics

**Primary (replication of C1 in parser domain)**: cold detection rate with aligned parser contracts > 50%.

**Secondary (ablation)**: cold detection rate with mismatched bankcheck contracts < 30% AND aligned > mismatched + 20 percentage points.

If both metrics pass → C1 generalizes (component-level domain transfer is replicable across two unrelated domains).
If primary passes but ablation fails → "auto-extracted contracts help, but specificity matters less than expected" (weaker claim).
If primary fails → C1 is single-domain only.

## Frozen rules

- Parser REF written before contract extraction or bug injection.
- Contracts extracted ONLY from REF, never from bugged versions or failure traces.
- Same prompts as P6 (only %CONTRACTS% slot changes).
- All 15 bugs reported regardless of result.
- No iteration: results are accepted as-is.

## Risk acknowledgement

Even if both metrics pass, the claim is restricted to: *"C1 generalizes from finance/CI domain to parser domain"*. Two domains is not "general"; we acknowledge in the paper.
