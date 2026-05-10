# P5-E3v2 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: The Phase-5 falsification of C-T3 LLM-grounded (warm + top-5 pattern names → no improvement, p = 0.95 against H1) may be due to **injection-format abstraction**: pattern *names* + 1-line descriptions are too generic to change reviewer behaviour. Concrete missed-bug examples drawn from TRAIN may recover the convergence claim.

## Conditions on TEST set (n = 101 paired-eligible bugs)

| Condition | Reviewer | Injection | Already run? |
|---|---|---|---|
| `baseline` | warm Codex | none | ✅ (`t2/reviews/warm_*.raw.txt`) |
| `injected_v1` | warm Codex | 5 pattern names + brief description | ✅ (`p5_e3/reviews/warm_injected_*.raw.txt`) — Δ = -6.5%, p = 0.95 |
| `injected_v2_examples` | warm Codex | concrete examples per category | NEW (this experiment) |

## Concrete-example injection content (extracted from TRAIN, frozen below)

For each top-5 category, 2-3 concrete missed-bug summaries from the TRAIN set are inserted into the prompt as "PRIOR REVIEW MISSES":

- **off-by-one**: B161 (fmax+0.01 upper bound), B19 (fee > fmax → fee >= fmax), B87 (n incremented before exponent)
- **logic**: B04 ((1+r/n) → (1-r/n)), B06 (exponentiation → multiplication), B150 (from updated by 2*amount)
- **currency**: B117 (no currency check on principal vs rate), B59 (USD == usd, case-insensitive)
- **atomicity**: B169 (modifies fmin/fmax in caller)
- **exception**: B109 (ZeroDivisionError instead of ValueError), B127 (raises base Exception)

## Pre-registered metrics

**Primary**: paired McNemar one-sided test (H1: `injected_v2 > baseline`) on the TEST set, n ≥ 80 paired (parsed both sides). Threshold p < 0.05.

**Secondary**: paired McNemar one-sided test (H1: `injected_v2 > injected_v1`) on the TEST set. Threshold p < 0.05.

**Tertiary**: per-top-5-category detection-rate change (descriptive).

## Frozen rules

- Concrete examples extracted from TRAIN ONLY (no leakage from TEST).
- Same warm-base prompt as injected_v1; only the "PATTERNS" section changes.
- Same TEST set as E3 v1 (101 bugs, ids in `p5_e3/split.json`).
- No iteration on prompt or examples after observing v2 results.
- All raw outputs reported.

## Risk / decision rules

- If `injected_v2 > baseline` (primary): C-T3 LLM-grounded *recovered* under concrete-example format. Update paper to "C-T3 partially recovered with concrete-example injection".
- If `injected_v2 ~ baseline`: C-T3 LLM-grounded falsification **survives** the obvious format-quality alternative explanation. Strengthens the negative finding.
- If `injected_v2 < baseline`: format-quality alternative is *also* worse — confirms C-T3 falsification is not format-driven.

## Cost estimate
- 101 codex review calls.
- Runtime: ~30-45 min with parallel chunked execution.
