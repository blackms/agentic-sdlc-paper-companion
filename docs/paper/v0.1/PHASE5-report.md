# Phase 5 Report — Three Negative Results

> **Status**: Phase 5 attempted to address the three remaining gaps to tier-1 readiness identified by the v0.2 peer-review synthesis: (E1) tier-comparable model control, (E2) repository-scale tasks, (E3) LLM-grounded learning loop. All three experiments produced **negative or null results**, which we report honestly and which materially change the paper's claims.

## E1 — Alternate-second-model control: deferred

**Plan.** Replace Claude Sonnet 4.6 (`claudeg`, the high-strength reviewer) with Gemini 2.5 Flash (`geminig`, plausibly tier-comparable to Codex) on all 200 T2 bugs. Test whether the central `asymm-multi < symm-mono` contrast survives without the model-strength ceiling.

**Status.** Gemini quota exhausted after 8/200 reviews (T2) and 6/27 reviews (E2). Effect-size estimation requires n ≥ 80 per condition. With only ~3% of the planned reviews completed, the experiment is *not interpretable* and is deferred to Phase 6 with a higher-quota Gemini API tier.

**Honest implication.** The model-strength ceiling confounder identified in §5.6 remains uncontrolled. The Bonferroni-corrected significance reported for P2 in v0.3 stands, but the `asymm-multi`-versus-`asymm-codex` marginal gain (~1 pp) is still not separated from the strength-of-Sonnet effect.

## E2 — Repository-scale tasks: P2 does not generalize across domains

**Plan.** Move beyond the toy `compound_interest` / `transfer` micro-tasks. Use the actual `agentic-sdlc/integration/checks/bankcheck.py` (597 LOC, real codebase) as the bugged target. Inject 30 bugs across 10 categories (boundary-drift, predicate-composition, data-flow, unit-schema, aggregation, dedup, state-leakage, error-masking, ordering, partial-failure), 3 per category, multi-line / multi-function diffs, severity and location pre-registered.

**Execution.** 27 of 30 bugs successfully injected (3 had non-unique substitution targets). Re-ran all seven reviewer roles on the 27 bugs.

### E2 per-condition q (default `missing` parse-failure policy)

| Condition | Detection rates | q = P(≥ 2 miss) | n_eff |
|---|---|---|---|
| `symm-mono` | 0.731, 0.846, 0.846 | **15.38%** (4/26) | 26 |
| `symm-multi` | 0.731, 0.846, **0.958** | **8.33%** (2/24) | 24 |
| `asymm-codex` | warm 0.815, **cold 0.111**, skeptic 0.846 | **26.92%** (7/26) | 26 |
| `asymm-multi` | warm 0.815, **cold 0.111**, claudeg 0.958 | **20.83%** (5/24) | 24 |

### E2 paired McNemar — all contrasts not significant

| Contrast | n_paired | b/c | McNemar p (one-sided) | Verdict |
|---|---|---|---|---|
| `asymm-codex < symm-mono` | 26 | 4/1 | **0.969** | n/s |
| `symm-multi < symm-mono` | 24 | 0/1 | 0.500 | n/s |
| `asymm-multi < symm-mono` | 24 | 3/1 | **0.938** | n/s |
| `asymm-multi < asymm-codex` | 24 | 0/1 | 0.500 | n/s |
| `asymm-multi < symm-multi` | 24 | 3/0 | 1.000 | n/s |

**Mechanism.** The cold contract-first reviewer collapses to 11% detection on `bankcheck.py` because the contract document it consults (`finance_contracts.md`) is from the wrong domain. The `cmd_review_validate`, `cmd_floats_check`, `cmd_review_gate` functions in bankcheck have no relationship to the `compound_interest`/`transfer` contracts the cold reviewer was instructed to derive expectations from. Asymmetric prompts therefore *do not transfer across domains without re-tooling the contract material*.

### Honest claim: P2 is domain-specific

The claim "asymmetric multi-role review reduces joint-miss rate at Bonferroni-corrected significance" must be qualified to: *"... within the domain whose formal contracts the cold reviewer consults"*. On a different code domain (the bankcheck check pipeline), the same prompt structure with the same model fails to reproduce the n=200 result of §5. The 7-percentage-point reduction in `q` going from `symm-mono` (15.4%) to `symm-multi` (8.3%) is suggestive of a non-cold contribution, but it does not survive any reasonable significance test at n=27.

This is the most important external-validity finding of the entire paper. Section 9.7 of the manuscript will be updated to incorporate this caveat.

## E3 — C-T3 LLM-grounded: pattern injection does not improve detection

**Plan.** Convert C-T3 from a simulation-only conjecture to an LLM-grounded test. Split the 200 T2 bugs stratified by category into TRAIN (99) and TEST (101) with `seed = 20260509`. Extract top-5 bug patterns from TRAIN by warm-Codex miss rate (automatic, schema-fixed: the 7 T2 categories). Augment the warm prompt with explicit warnings for the top-5 categories. Re-run warm Codex on the 101 TEST bugs with the augmented prompt. Compare baseline (existing warm reviews) versus injected (new reviews) paired by bug-id.

**Execution.** Top-5 patterns extracted: `off-by-one`, `logic`, `currency`, `atomicity`, `exception`. Cycle-1 reviews completed on 101/101 TEST bugs; 92 paired (parsed in both baseline and injected).

### E3 result

| Slice | n | Baseline detection | Injected detection | Δ | McNemar p (H1: injected>baseline) |
|---|---|---|---|---|---|
| Overall | 92 | 0.750 | 0.685 | **−0.065** | **0.952** |
| Seen-patterns (top-5) | 56 | 0.768 | 0.714 | −0.054 | 0.938 |
| Unseen-patterns | 36 | 0.722 | 0.639 | −0.083 | 0.887 |

**Per-category** (★ = top-5 injected):

| Category | n | Baseline | Injected | Δ |
|---|---|---|---|---|
| ★ atomicity | 4 | 0.750 | 0.500 | **−0.250** |
| contract | 26 | 0.692 | 0.615 | −0.077 |
| ★ currency | 8 | 0.625 | 0.625 | 0.000 |
| ★ exception | 9 | 0.889 | 0.889 | 0.000 |
| ★ logic | 23 | 0.739 | 0.739 | 0.000 |
| ★ off-by-one | 12 | 0.833 | 0.667 | **−0.167** |
| precision | 10 | 0.800 | 0.700 | −0.100 |

The discordant pair count is `b = 12` (baseline catches, injected misses) versus `c = 6` (injected catches, baseline misses). Two-sided McNemar exact `p = 0.238` — not significant in either direction; the *direction* of the effect is, however, slightly negative.

### Hypotheses for the negative result

1. **Prompt overload**: the augmented prompt is ~3× longer than the baseline warm prompt. Codex may dilute attention across the additional content.
2. **Confirmation bias**: the agent enumerates the five injected categories and stops, missing bugs in non-injected categories *and* missing instances of the injected categories that don't match the prompt's description form.
3. **Stochastic noise at n = 92**: even at this size the discordant count `(12, 6)` could be noise. A larger `n` would tighten the confidence interval but is unlikely to flip the direction.

### Honest claim: C-T3 is currently *not* supported on LLM trajectories

In v0.3 we labelled C-T3 a *Conjecture* with simulation-only evidence. Phase 5 was the LLM-grounded test that v0.3 deferred. The result is **null at best, slightly negative at face value**. We therefore:

- Demote C-T3 from "supported by simulation" to "supported by simulation only; LLM-grounded test fails to reproduce the predicted improvement at n = 92".
- Treat this as a *correction*, not a setback: simulation-based predictions about LLM agent behavior are not reliable without LLM-grounded confirmation. The paper's discipline of "what is proven / measured / conjectured" must now move C-T3 from "conjecture with positive simulation" to "conjecture with negative LLM-grounded counter-evidence".

## Summary table — what Phase 5 changed

| Claim | v0.3 status | Post-Phase-5 v0.4 status |
|---|---|---|
| **P1** (Expected-Utility Dominance + eFOSD) | Confirmed n=120, 4 frontier models | **Unchanged** — Phase 5 did not re-test |
| **P2** (Asymmetric-quorum joint-miss bound) | Bonferroni-significant via paired McNemar in 3/3 parse policies (n=200) | **Domain-restricted**: holds in finance domain; does NOT generalize to bankcheck.py (n=27, all contrasts n/s) |
| **C-T3** (Learning-loop convergence) | Simulation-supported conjecture | **Falsified by LLM-grounded test**: pattern injection does not improve detection (Δ=−0.065 at n=92) |

## Threats to validity for Phase 5 itself

- **E2: small n** (27 bugs vs target 30, with 3 substitution failures). Effect sizes hard to estimate at this scale; the directional result (no improvement, possibly worse) is robust to n but the precise magnitudes are not.
- **E2: cold reviewer is the dominant signal**. The 11% detection rate of cold on bankcheck is so low that it inflates `q` for any condition containing it. A cleaner replication would re-engineer the cold contract document for the bankcheck domain *before* re-testing.
- **E3: single cycle**. The simulation in §6 ran 5 cycles; we ran 1 LLM cycle. The negative direction at one cycle does not preclude a different result at five cycles, but it strongly suggests the simulation parameters do not match the LLM regime.
- **E3: prompt design choice**. The injection format ("⚠️ PATTERNS LEARNED ...") is one of many possible injection strategies. A different injection format (e.g. inline examples, chain-of-thought trigger) could plausibly produce a positive result. We do not claim that learning loops on LLMs are *impossible*; we claim that the specific simulation-derived injection strategy *did not work*.

## What this means for the paper

The paper v0.4 must:

1. **Restrict P2 to its domain of validity** (finance contracts visible to the cold reviewer).
2. **Demote C-T3** from "simulation-supported conjecture" to "open question; first LLM-grounded test was negative".
3. **Add a §9.x section "What Phase 5 falsified"** — explicit failure-mode reporting.
4. **Adjust the abstract and introduction** — the headline must be honest about both successes and Phase-5 falsifications.

Phase 5 has *strengthened* the paper's epistemic discipline by demonstrating that two of the three central claims have explicit boundaries we can now report.

## Files produced

```
experiments/p5_e2/
  bugs_e2.yaml                    30 bug schema, 10 categories, severity-pre-registered
  inject_bugs.py                  generator (27/30 successfully injected)
  bugged/E2_B*.py                 27 bugged versions of bankcheck.py
  reviews/{cold,warm,skeptic,simm1-3,claudeg,geminig}_E2_B*.raw.txt   195 reviews (geminig partial)
  parse_e2.py, analyze_e2.py      analyzers
  results/e2_analysis.json        per-condition q + paired McNemar

experiments/p5_e3/
  setup_split.py                  TRAIN/TEST stratified split (seed 20260509)
  split.json                      99 train + 101 test bug ids
  extract_patterns.py             automatic pattern extraction (top-5 by miss-rate)
  patterns_top5.json              [off-by-one, logic, currency, atomicity, exception]
  prompts/warm_injected.txt       augmented prompt with top-5 warnings
  reviews/warm_injected_*.raw.txt 101 cycle-1 reviews
  analyze_cycle1.py               McNemar paired analysis
  results/cycle1_analysis.json    overall + per-category breakdown
```
