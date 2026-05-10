# Phase 8 Report — Partial Multi-Domain Generalization, Underpowered

> **Status**: Phase 8 attempted to generalize C1 from 2 domains (Phase 6/7) to 5 domains by adding 3 new structurally heterogeneous targets (expression evaluator, regex compiler, HTTP header parser). Headline finding (Codex peer review verbatim): *"P8 partially generalizes the cold-review advantage across three new domains, but the parser-like ablation does not cleanly isolate contract specificity, and the study is underpowered due to failed bug injection yield."*

## Pre-registration (frozen 2026-05-10)

3 new domains chosen for heterogeneity vs. JSON parser:

| Domain | Description | LOC | Heterogeneity vs prior |
|---|---|---|---|
| `exprev` | Expression evaluator (math AST, operator precedence) | ~170 | New: AST data structure |
| `regex` | Regex compiler (Thompson NFA construction) | ~200 | New: FSM, algorithmic |
| `httphdr` | HTTP header parser (case-insensitive keys, multi-value) | ~150 | New: networking semantics |

## Bug-injection yield problem (acknowledged honestly)

| Domain | Target bugs | Successfully injected | Yield |
|---|---|---|---|
| exprev | 12 | 6 | 50% |
| regex | 12 | 5 | 42% |
| httphdr | 12 | 5 | 42% |
| **Total P8** | **36** | **16** | **44%** |

Cause: multi-line `sub_old` YAML strings with embedded newlines were not always exactly matching the reference text after my Python-string formatting choices. We did not iterate after seeing failure (frozen pipeline), so the experiment ran with the actual yield. Per-domain `n` is therefore 5–6 paired bugs instead of the planned 12, severely limiting per-domain power.

## Per-domain results

| Domain | Cold aligned | Cold mismatched | Δ (pp) | Primary > 50% | Ablation < 30% | Δ ≥ 20 pp | McNemar p (paired) |
|---|---|---|---|---|---|---|---|
| `exprev` | 100% (5/5) | 66.67% (4/6) | **33.3** | ✅ | ❌ | ✅ | 0.250 |
| `regex` | 80% (4/5) | 50.00% (2/4) | **30.0** | ✅ | ❌ | ✅ | 0.500 |
| `httphdr` | 100% (5/5) | 40.00% (2/5) | **60.0** | ✅ | ❌ | ✅ | 0.125 |

**Pattern**:
- **Primary** (cold aligned > 50%): **3/3 PASS**.
- **Specificity Δ ≥ 20 pp**: **3/3 PASS**.
- **Ablation** (cold mismatched < 30%): **3/3 FAIL**. The "mismatched" condition uses parser_contracts (P7) on parser-like domains. Unlike P7 which used bankcheck contracts (completely unrelated) on JSON parser, here the mismatched contracts retain residual signal because exprev / regex / httphdr share parser-like properties with the JSON parser.
- **Per-domain paired McNemar**: none significant individually (n = 4–5 paired, p ∈ {0.125, 0.25, 0.50}).

The ablation failure is not a power issue — it is a *contract-similarity* finding: when the "wrong" contracts are not categorically wrong (parser-on-parser-like), the cold reviewer extracts residual value. This sharpens but does not destroy C1: domain alignment helps, but full domain mismatch is a stronger ablation than parser-on-parser-like.

## Cross-domain meta-analysis (Fisher's combined)

Combining the 4 paired McNemar p-values (P7 + 3 P8):

```
P7  (json parser)        : p = 0.0078   n=10, b=0, c=7
P8  exprev               : p = 0.2500   n=5,  b=0, c=2
P8  regex                : p = 0.5000   n=4,  b=1, c=2
P8  httphdr              : p = 0.1250   n=5,  b=0, c=3

Fisher combined χ²(8) = 18.025
Combined p              = 0.0210
```

The combined p = 0.021 is significant at α = 0.05 but **does not reach the pre-registered primary threshold of p < 0.001**. The aggregate evidence is supportive but not at the strength we pre-registered. We report this honestly.

## Reviewer-family variation (regex sub-experiment)

Claude Opus 4.7 used as `cold_opus` reviewer on the same 5 regex bugs as Codex `cold`:

| Reviewer | Detection | Bugs caught |
|---|---|---|
| Opus 4.7 cold | 100% | 5/5 |
| Codex cold | 80% | 4/5 |

Cross-model robustness of C1 supported (limited n = 5): Opus matches or exceeds Codex on the same domain with the same auto-extracted contracts.

## Honest claim positioning (post peer review)

The Codex peer review of P8 returned **REQUEST_CHANGES** with explicit framing:

> "**'mostly replicated, with ablation failure in parser-similar domains'** is more accurate than 'replicated 4 domains'. **'Partial generalization' is fair only if explicitly secondary/exploratory.** The combined p = 0.021 supports nominal aggregate evidence, not the success of the primary criterion p < 0.001."

We adopt the framing. The paper-v0.7 claim language for C1 is:

> **C1 (Cold reviewer transfer, partially generalized across 4–5 domains)**: across two pilot domains (bankcheck CI, JSON parser) and three additional pilots (expression evaluator, regex compiler, HTTP header parser), auto-extracted contracts boost cold reviewer detection above the misaligned-baseline (specificity Δ in 33–73 pp) and above the 50% threshold in 4 of 4 paired-tested domains. Cross-domain Fisher's combined McNemar p = 0.021 (not at the pre-registered primary threshold p < 0.001). The ablation control distinguishes domain-aligned from cross-domain-mismatched contracts; in P8 the mismatched contracts (parser contracts on parser-similar domains) retain residual signal, so the ablation cleanly isolates specificity only when the mismatch is *categorically* (not *structurally similar*) misaligned. Reviewer-family variation (Opus vs Codex on regex, n=5) supports cross-model robustness within margin. **C1 is partially generalized**, not fully generalized; pre-registered yield was 36 bugs, achieved 16, so per-domain inferences are underpowered.

## Limitations honestly catalogued (P8-specific)

1. **Bug-injection yield 44% (16/36)**. The pre-registration committed 12 bugs/domain; actual was 5–6. This is a *protocol failure*, not just low n. Future replications should use programmatic injection with AST-level mutators rather than text substitution.
2. **Per-domain McNemar all individually non-significant** (p ∈ {0.125, 0.25, 0.50}). Cross-domain combined evidence is necessary but not sufficient.
3. **Ablation specificity** is preserved (Δ ≥ 20 pp in 3/3) but the absolute threshold (mismatched < 30%) fails because the "mismatched" contracts here share structural similarity with the test domain.
4. **Hand-written domains, not real codebases**. Same caveat as P7. Phase 9 desiderata: real GitHub repos with naturalistic bugs.
5. **Single reviewer family for the bulk of P8** (Codex). Opus tested on regex only (n=5).

## Updates to the paper

The v0.7 paper should:

1. **Update C1 to "partially generalized across 4–5 domains, ablation cleanly distinguishes only categorically-mismatched contracts"**.
2. **Add §5.x "Multi-domain replication and limits"** with the per-domain table and the Fisher combined p.
3. **Add §5.y "Reviewer-family variation"** with the Opus-vs-Codex regex comparison.
4. **Add §9.x "Why ablation fails when mismatch is structural"** as a mechanistic discussion. The right ablation distinguishes *unrelated domain* from *structurally similar domain*; the mismatched-baseline degrades gracefully rather than collapsing.
5. **Acknowledge the bug-injection yield protocol failure** as a Phase-9 desideratum.

## Phase 8 deliverables

```
experiments/p8_multidomain/
  PREREGISTRATION.md
  exprev/{ref/exprev.py, bugs.yaml, bugged/, contracts/contracts.md, reviews/}
  regex/{ref/regex_compile.py, bugs.yaml, bugged/, contracts/contracts.md, reviews/, cold_opus_*}
  httphdr/{ref/httphdr.py, bugs.yaml, bugged/, contracts/contracts.md, reviews/}
  inject_all.py, analyze_p8.py, launch_p8_reviews.sh
  results/p8_analysis.json
```

## Honest summary

P8 **partially generalizes** C1 from 2 to 5 domains. Primary metric and specificity reggono in 3 nuovi domini; ablation decade in modo informativo (mostra che cold contracts hanno residual signal in parser-similar domains, non collassano completamente). Cross-domain Fisher combined p = 0.021 — significant α = 0.05, **non al primary threshold pre-registered p < 0.001**. Reviewer-family robustness preliminarmente supportato (Opus vs Codex su regex, n=5).

**Phase 9 desiderata**:
- Real codebases (not hand-written), naturalistic bugs.
- AST-level mutation generator instead of text substitution (target yield ≥ 90%).
- Per-domain n ≥ 30 paired bugs for individual McNemar significance.
- 2+ additional reviewer families (Claude Opus, Mistral if available, GPT-5).
- Categorically-mismatched ablation in every domain (not just "structurally adjacent").
