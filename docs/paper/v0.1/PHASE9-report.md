# Phase 9 Report — Real Codebases, AST Mutator: Pre-Registered Primary Endpoint Falsified, Specificity Replicated Against Extreme Mismatch

> **Status (post-Codex peer review, REQUEST_CHANGES applied)**: Phase 9 tested C1 on 3 real Python stdlib codebases (`csv.py`, `urllib/parse.py`, `json/decoder.py`) using AST-level mutations (yield 100% vs P8's 44%). Headline: **the pre-registered primary endpoint "cold detection > 50% per domain" is falsified on real stdlib code under the strict (unparsed-as-miss) policy: 0/3 domains exceed the threshold; cold detection is 43.3% / 50.0% / 43.3%, with Wilson 95% CIs all straddling 50%.** The specificity component (cold beats categorically-mismatched contracts) replicates strongly: cold_mismatched = 0% in all 3 domains, Δ ∈ [43, 50] pp strict, per-domain McNemar p ∈ {3.1·10⁻⁵, 1.2·10⁻⁴, 1.2·10⁻⁴}, Fisher's combined p over P7 + 3 P9 = 2.4·10⁻¹¹. **Codex peer review (verbatim)**: *"The honest paper is publishable only if it leads with the failed primary endpoint, removes generalization language, reports denominators/failures/discordant pairs/CIs, and treats generic prompts as serious competitors rather than secondary controls."* We adopt the framing.

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

## Per-domain results (denominator-explicit table)

Format: `caught/parsed = parsed-rate% [strict-rate%]`. Strict policy: unparsed-as-miss.

| Domain | warm | cold (PRIMARY) | cold_mismatched (ABLATION) | skeptic | simm1 | simm2 | simm3 |
|---|---|---|---|---|---|---|---|
| csv_dom | 2/30=6.7% | 13/30=43.3% [43.3%] | **0/30=0.0% [0.0%]** | 18/30=60.0% | 23/30=76.7% | 20/30=66.7% | 18/30=60.0% |
| urllib_dom | 13/30=43.3% | 15/30=50.0% [50.0%] | **0/30=0.0% [0.0%]** | 14/28=50.0% [46.7%] | 13/28=46.4% [43.3%] | 14/29=48.3% [46.7%] | 17/29=58.6% [56.7%] |
| jsondec_dom | 2/30=6.7% | 13/25=52.0% [43.3%] | **0/30=0.0% [0.0%]** | 9/23=39.1% [30.0%] | 14/27=51.9% [46.7%] | 14/25=56.0% [46.7%] | 13/25=52.0% [43.3%] |

Wilson 95% CI on the strict cold rates (the pre-registered primary):
- csv_dom: 43.33% [27.4%, 60.8%]
- urllib_dom: 50.00% [33.2%, 66.9%]
- jsondec_dom: 43.33% [27.4%, 60.8%]

All three CIs include 50%; **none of the three primary point estimates exceeds 50%**.

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

## Honest framing (post-Codex peer review)

The pre-registered primary endpoint **fails**. We lead with the falsification, not the specificity replication.

1. **Primary endpoint (cold > 50%) — FALSIFIED on real stdlib code.** Strict policy: 0/3 domains pass. Wilson 95% CIs all straddle 50%. Absolute cold detection on realistic Python stdlib is in the 27–67% interval; the pre-registered hypothesis is rejected.

2. **Specificity component — replicated against extreme categorical mismatch.** Cold-aligned contracts substantially outperform bankcheck contracts on stdlib parsers (Δ ∈ [43, 50] pp strict, McNemar p < 10⁻³ in each domain, Fisher combined p = 2.4·10⁻¹¹). However:
   - The 0% floor on `cold_mismatched` reflects an **extreme** mismatch (finance contracts on stdlib parsing/CSV/URL code). It does not test realistic partially-wrong-constraint scenarios.
   - The Fisher combination over 4 tests is *evidence for specificity*, not generalization in the sense of "aligned contracts cause high detection".

3. **Generic prompts are serious competitors.** On csv_dom, `simm1` reaches 76.67% vs cold 43.33%. On jsondec_dom, `simm2` reaches 56% vs cold 43.3% strict. The contract-first prompt does *not* uniformly dominate — it dominates only the categorically-mismatched control. **Procedural constraints are not uniquely responsible for high detection; well-engineered generic prompting is sometimes stronger.**

4. **The methodological gain stands.** AST-level mutation yield (100%) replaces P8's text-substitution yield (44%). This is independent of the C1 outcome and is a real contribution.

5. **What is *not* established**: that aligned auto-extracted contracts increase absolute detection on real code; that they uniformly improve over generic prompts; that the specificity finding extends to realistic partially-wrong constraints; that it transfers across reviewer families on stdlib (Opus subagent deferred to P10).

## Updated C1 statement (for paper v0.8)

> **C1 (Cold reviewer transfer — pre-registered primary endpoint falsified on real stdlib code; specificity component replicated against extreme mismatch ablation)**: across two pilot domains (bankcheck CI, JSON parser), three Phase-8 hand-written domains, and three Phase-9 real Python stdlib codebases (csv, urllib.parse, json.decoder, n = 30 AST-level mutations each, yield 100%), the pre-registered primary endpoint "cold detection > 50% per domain" **fails on real stdlib code** under the strict (unparsed-as-miss) policy: 0/3 P9 domains exceed the threshold (43.3% / 50.0% / 43.3%, Wilson 95% CIs [27.4%, 60.8%] / [33.2%, 66.9%] / [27.4%, 60.8%], all straddling 50%). The specificity component replicates against an *extreme* categorical-mismatch ablation: cold_mismatched (bankcheck CI contracts on stdlib) = 0% in all 3 P9 domains, Δ ∈ [43, 50] pp strict, per-domain paired McNemar p ∈ {3.1·10⁻⁵, 1.2·10⁻⁴, 1.2·10⁻⁴}, Fisher's combined paired McNemar p = 2.4·10⁻¹¹ over P7 + 3 P9 (4 tests). The Fisher combination establishes that aligned contracts substantially outperform categorically-mismatched contracts under this ablation; **it does not establish that aligned contracts uniquely cause high detection.** Well-engineered generic prompts are serious comparators: on csv_dom, simm1 reaches 76.67% vs cold 43.33%; on jsondec_dom, simm2 56% vs cold 43.3% strict. **C1's honest claim**: aligned auto-extracted contracts substantially outperform categorically-mismatched contracts on real stdlib code; they do not exceed the 50% absolute-detection threshold and are not uniformly superior to well-engineered generic reasoning prompts.

## Limitations honestly catalogued (P9-specific, post-Codex peer review)

1. **Stdlib training-data bias**: csv/urllib/json are heavily represented in Codex pretraining; this affects both detection rates and false-negative patterns.
2. **Single-mutation bugs**: each bugged file has exactly one AST-level operator change. Naturalistic bugs are typically multi-line and span data-flow patterns.
3. **Mutation correlation within a single file**: 30 mutants on one file are not independent tasks; treating them as such likely overstates precision (Codex peer review).
4. **Equivalent or near-equivalent mutants** may depress absolute detection without reflecting reviewer weakness (e.g., `<` vs `<=` on values that never hit the boundary in tests).
5. **Single reviewer family** (Codex gpt-5.5) — shared failure modes across roles introduce non-independence. Opus subagent deferred to P10.
6. **Extreme ablation**: `cold_mismatched = 0%` reflects bankcheck contracts on stdlib parsers. This tests *gross* mismatch, not realistic partially-wrong-constraint scenarios.
7. **Parsing-failure asymmetry**: jsondec_dom cold parses 25/30 vs cold_mismatched 30/30. Output parseability may correlate with prompt style, biasing parsed-only estimates. Strict policy mitigates but does not eliminate this.
8. **Auto-extracted contract heterogeneity**: contracts differ in length and clue density across domains (csv 52KB / urllib 116KB / jsondec 48KB).
9. **Detection-criterion strictness**: line ±2 OR (enclosing function name + operator keyword). Looser criteria would inflate all rates uniformly; the *contrast* is robust to this choice.
10. **Three files of Python stdlib** is a small, biased sample of "real code" — does not represent agentic coding workflows over multi-file repositories with dependencies.

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
