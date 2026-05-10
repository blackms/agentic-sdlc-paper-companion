# P9 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: C1 (cold reviewer transfer via auto-extracted contracts) generalizes to real Python codebases when bugs are AST-level mutations.

## Real codebases (stdlib Python)

| Domain | Source | LOC |
|---|---|---|
| `csv_dom` | `csv.py` (Python stdlib) | 451 |
| `urllib_dom` | `urllib/parse.py` (Python stdlib) | 1246 |
| `jsondec_dom` | `json/decoder.py` (Python stdlib) | 356 |

These are real, actively-maintained, widely-used modules. **Training-data bias**: stdlib Python is heavily represented in Codex / Opus pretraining corpora; this is acknowledged as a limitation but mitigated by:
- Same bias affects every reviewer condition equally (cold aligned vs cold mismatched vs warm vs symm).
- The contrast tested by C1 is *aligned vs mismatched contracts*, both seeing the same bugged code.
- Phase-10 desideratum: replicate on uncommon third-party libraries with less training-data presence.

## AST-level mutation generator

Operators (PRIORITY 1, high signal/noise):
- **AOR** Arithmetic Operator Replacement: `+ ↔ -`, `* ↔ /`, `// ↔ %`
- **ROR** Relational Operator Replacement: `== ↔ !=`, `< ↔ <=`, `> ↔ >=`, `< ↔ >`
- **BOR** Boolean Operator Replacement: `and ↔ or`

Excluded (PRIORITY 2, too noisy):
- CR (constant replacement) — frequent trivial mutants
- SDL (statement deletion) — high crash rate

The mutator visits the AST of each module, enumerates all PRIORITY-1 mutation locations, generates one bugged file per mutation, and **filters out mutants that fail to import** (basic syntax/runtime sanity).

Target yield: ≥ 90% (i.e., ≤ 10% trivial-failure mutants).

## Sampling

Per domain:
- Enumerate all PRIORITY-1 mutations on the reference module.
- Filter to those that produce a valid (importable) bugged module.
- Sample 30 mutations stratified by operator (AOR/ROR/BOR) and by source location.
- If fewer than 30 valid mutations exist, take all and document.

## Reviewers

Per bug:
- `cold_aligned`: Codex with auto-extracted domain contracts.
- `cold_mismatched_categorical`: Codex with bankcheck contracts (categorical mismatch from CI/finance to stdlib parser).
- `warm` Codex with warm prompt.
- `skeptic` Codex with skeptic prompt.
- `simm1`, `simm2`, `simm3` Codex with generic prompt.
- (On 2 of 3 domains): `cold_opus` Claude Opus 4.7 with auto-extracted contracts.

Total reviewer calls: 30 × 7 × 3 = 630 Codex + 30 × 2 = 60 Opus = 690.

## Pre-registered metrics

Per-domain:
- **Primary**: cold detection (aligned) > 50%.
- **Ablation**: cold detection (categorical mismatched) < 30%.
- **Specificity**: Δ ≥ 20pp.
- **Per-domain paired McNemar**: p < 0.010 (Bonferroni-corrected for the 3 P9 domains, family α = 0.05 → per-test α = 0.0167; we use stricter α = 0.010 from the original 5-test family).

Cross-domain meta-analysis:
- Fisher's combined p-value over P7 + 3 P9 = 4 paired McNemar tests.
- **Primary threshold**: combined p < 0.001.
- Random-effects meta-regression on log-odds-ratios reported descriptively.

Reviewer-family variation (regex P8 + 2 P9 domains):
- Compare Codex cold vs Opus cold detection rates per domain. If Δ < 10pp, robustness supported.

## Frozen rules

- AST mutator code committed before any Codex/Opus call.
- Contracts auto-extracted from the *original* stdlib reference (not bugged), with no awareness of which mutations will be tested.
- 30-bug sample drawn deterministically (`seed=20260510`).
- No iteration on prompts, contracts, or sampling after observing results.
- All raw outputs reported.

## Risk acknowledgement

Even if all metrics pass:
- Training-data bias on stdlib limits external validity to "code Codex/Opus has plausibly seen during training".
- Phase-10 desideratum: lesser-known third-party libraries.
- Single bug per file (single-mutation); naturalistic bugs are typically multi-line.
