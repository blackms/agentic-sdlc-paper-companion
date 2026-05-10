# P10 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: The Phase-9 specificity finding (cold > cold_mismatched, family-significant on csv_dom) and the cross-family detection-rate spread (Opus 30% < Codex 43% < Gemini 3.1 Pro 63%) generalize to **third-party Python libraries** with less training-data overlap than the Python stdlib.

## Codebases (third-party Python)

| Domain | Source | LOC | Popularity (rough) | Training-data presence |
|---|---|---|---|---|
| `dateutil_dom` | `dateutil/relativedelta.py` (python-dateutil) | 599 | very high | high |
| `parsy_dom` | `parsy/__init__.py` (parsy) | 719 | low (parser combinator niche) | low |
| `chardet_dom` | `chardet/chardistribution.py` (chardet 4.0.0) | 233 | medium | medium |

The dateutil case is included as an "internal control" (popular third-party — should still be well-known to LLMs); parsy is the strongest external-validity test (small audience); chardet sits in the middle.

## AST mutator

Same operators as P9: AOR, ROR, BOR. Validation: **compile-only** (no import-execution test, because third-party modules require their own package context to import). Reviewers receive *static* bugged source files; reviewing static code does not require runtime importability.

## Sampling

Per domain: sample 30 stratified mutations (seed = 20260510). For parsy (only 35 valid mutations), take all 35 if needed.

## Reviewers

Per bug, **two conditions × three families**:
- `cold_aligned`: domain-aligned auto-extracted contracts.
- `cold_mismatched`: bankcheck CI contracts (categorical mismatch from finance to third-party Python utilities).

Three families:
- Codex gpt-5.5
- Claude Opus 4.7
- Gemini 3.1 Pro Preview

Total review calls per domain: 30 × 2 × 3 = 180. Across 3 domains: 540.

## Pre-registered metrics

**Per-domain × per-family**:
- Specificity Δ = cold − cold_mismatched ≥ 20 pp.
- Paired McNemar one-sided (cold > cold_mismatched), p < 0.010 (Bonferroni-stricter).

**Cross-domain Fisher's combined paired McNemar p over P9 + P10 = 6 tests**:
- Codex-only: 4 P9 (csv, urllib, jsondec) + P7 (json_parser) + 3 P10 = 7 tests.
- Threshold p < 0.001.

**Reviewer-choice sensitivity**:
- Report cold-aligned strict rate per family per domain with Wilson 95% CI.
- Report 33-47 pp spread reproduces or shrinks on third-party libs.

## Frozen rules

- AST mutator code committed before any reviewer call (`p9_real/ast_mutator.py` reused, validated compile-only for P10).
- Contracts auto-extracted from the *original* third-party reference (not bugged), with no awareness of which mutations will be tested.
- Sample drawn deterministically (seed = 20260510).
- No iteration on prompts, contracts, or sampling after observing P10 results.
- All raw outputs committed.

## Risk acknowledgement

1. **Third-party library popularity**: dateutil and chardet are still widely-used; parsy is the only true "low-presence" test.
2. **Single-mutation bugs persist**: same limit as P9.
3. **Mutation correlation within a single file** is unchanged.
4. **Bankcheck mismatch is still extreme**: the categorical-mismatch ablation tests gross mismatch, not realistic partially-wrong constraints. Same caveat as P9.

## Decision rules

- If specificity (Δ ≥ 20 pp + McNemar p < 0.010) holds in 6+ of 9 (3 domains × 3 families) cells: **C1 specificity generalizes to third-party libs**.
- If the family-spread (Gemini > Codex > Opus on absolute detection) reproduces across all 3 P10 domains: **reviewer-choice sensitivity is benchmark-stable**.
- If results diverge sharply from P9: **stdlib-bias hypothesis** is supported and the paper must restrict claims to stdlib-like code.
