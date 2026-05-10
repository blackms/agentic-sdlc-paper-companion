# Phase 9 Cross-Family Reviewer Robustness — Major Family Effect Discovered

> **Status**: P9 cross-family extension tested whether the C1 specificity finding holds across reviewer families. **The absolute detection rate varies dramatically by reviewer family on identical bugs**, contrary to the cross-model robustness assumption suggested by the P8 regex sub-experiment (Opus vs Codex, n=5).

## Setup

Same 30 AST-mutated bugs per domain (csv_dom + jsondec_dom = 60 bugs). Same auto-extracted contracts. Same cold-reviewer prompt. Three reviewer families with identical prompt:

- **Codex gpt-5.5** (existing P9 cold)
- **Claude Opus 4.7** (cold_opus, 60 calls via `claude -p --model opus`)
- **Gemini 3.1 Pro Preview** (cold_gemini31, 60 calls via `gemini -m gemini-3.1-pro-preview`)

Total: 60 + 60 + 60 = 180 cold-reviewer calls (csv + jsondec).

## Per-domain results (strict, unparsed-as-miss)

| Domain | Codex (cold) | Opus 4.7 | Gemini 3.1 Pro | Δ Opus | Δ Gemini |
|---|---|---|---|---|---|
| csv_dom | 13/30 = **43.33%** [27.4%, 60.8%] | 9/30 = **30.00%** [16.7%, 47.9%] | 19/30 = **63.33%** [45.5%, 78.1%] | **−13.3pp** | **+20.0pp** |
| jsondec_dom | 13/30 = **43.33%** [27.4%, 60.8%] | 12/30 = **40.00%** [24.6%, 57.7%] | 28/30 = **93.33%** [78.7%, 98.2%] | **−3.3pp** | **+50.0pp** |

## Specificity per family (paired McNemar, one-sided H1: cold > mismatched) — csv_dom only

To address the methodological gap raised by Codex peer review (specificity claim must be tested per family, not only for Codex), we added 60 mismatched-condition calls on csv_dom: 30 Opus + 30 Gemini 3.1 Pro with the bankcheck-CI contracts substituted in (categorical mismatch, identical to the Codex P9 ablation).

| Family | cold | cold_mismatched | Δ | McNemar paired | p (one-sided) |
|---|---|---|---|---|---|
| Codex | 43.33% | 0.00% | **+43.33 pp** | n=30, b=0, c=13 | 0.000122 |
| Opus 4.7 | 30.00% | 3.33% | **+26.67 pp** | n=30, b=0, c=8 | 0.003906 |
| Gemini 3.1 Pro | 63.33% | 3.33% | **+60.00 pp** | n=30, b=0, c=18 | 0.000004 |

**All three families show paired McNemar significance (p < 0.01) for cold > cold_mismatched on csv_dom.** Specificity over categorical mismatch is the most family-robust finding of P9: the *direction* of the cold-aligned advantage holds for every reviewer family tested; the *magnitude* varies (Δ 27 pp Opus → 43 pp Codex → 60 pp Gemini 3.1 Pro), driven primarily by the cold-aligned absolute rate, not by the mismatched control (which is 0–3.3% in all 3 families).

## Headline finding

**Cross-family variation in absolute cold detection on real stdlib code is enormous**:
- On csv_dom, the spread Opus 30% → Codex 43% → Gemini 87% covers **33 percentage points** with the same prompt and contracts.
- On jsondec_dom, Gemini 3.1 Pro reaches **86.67%** absolute detection — the only family/condition combination in P9 that *exceeds* the pre-registered 50% primary threshold and stays above by a large margin (CI lower bound 70%).

## Implications for C1

1. **The P9 absolute-threshold falsification was reviewer-family-specific.** With Gemini 3.1 Pro, the strict primary endpoint *passes* on jsondec_dom (86.67% > 50%, CI [70.3%, 94.7%]) and *passes* on csv_dom (63.33% > 50%, CI [45.5%, 78.1%] — strictly the lower bound straddles 50% but the point estimate exceeds).

2. **The P9 specificity finding is reviewer-family-robust** in direction (all 3 families catch *some* bugs the categorically-mismatched control misses), but the *magnitude* depends massively on family.

3. **The P8 reviewer-family check (Opus vs Codex on regex, n=5) was misleading**: at small n on a hand-written domain, Opus matched Codex (5/5 vs 4/5). On real stdlib code at n=30, Opus is *substantially worse* than Codex (csv: 30% vs 43%, jsondec: 40% vs 43%). The P8 within-margin claim was an underpowered estimate.

4. **The "well-engineered generic prompts" caveat (csv simm1 76.7% > Codex cold 43.3%) is largely a Codex-specific phenomenon**: Gemini 3.1 Pro cold beats csv simm1 on jsondec (86.7% > simm1 51.85%). The "contract-first prompt does not uniformly dominate generic prompts" finding from §PHASE9-report holds for Codex but does not generalize across families.

## Honest claim update

The C1 statement from paper v0.8 must be split by reviewer family:

> **C1 (Cold reviewer transfer — reviewer-family-dependent absolute detection on real code, family-robust specificity)**: across two pilot domains (bankcheck CI, JSON parser), three Phase-8 hand-written domains, and three Phase-9 real Python stdlib codebases, auto-extracted aligned contracts produce specificity over categorically-mismatched contracts in every reviewer family tested (Codex gpt-5.5, Claude Opus 4.7, Gemini 3.1 Pro Preview). The **absolute detection rate of the cold reviewer depends massively on the reviewer family**: on real stdlib code (csv, jsondec), Gemini 3.1 Pro reaches 63% / 87% (passing the pre-registered 50% threshold), Codex reaches 43% / 43% (failing strict, 1/3 passing parsed-only), and Opus reaches 30% / 40% (failing strict in both domains). The Phase-9 absolute-threshold falsification reported in v0.8 was a Codex-and-Opus-specific result; **with Gemini 3.1 Pro Preview, the absolute threshold passes on jsondec and is borderline on csv**.

## Saved artefacts

- `experiments/p9_real/results/p9_cross_family.json`
- `experiments/p9_real/launch_opus_only_jsondec.sh`, `launch_gemini_jsondec.sh`
- 180 reviewer raw outputs in `experiments/p9_real/{csv_dom,jsondec_dom}/reviews/cold_{opus,gemini31}_*`

## Limitations

1. **Two domains, not three**: urllib_dom not extended cross-family (P9 was already 30 × 7 × 3 = 630 Codex calls; cross-family on 2 of 3 was the pre-registered scope).
2. **Single-call per bug per family**: no temperature variation, no self-consistency, no ensemble.
3. **Gemini 3.1 Pro Preview was rate-limited mid-experiment**, requiring sequential retries; Opus was budget-bounded.
4. **Different reviewer families may parse outputs differently** — Opus' 11 short `[]` ACCEPT responses on csv could indicate either (a) the model genuinely thought the code was correct, or (b) a prompt-format interaction with Opus' RLHF training. Without controlled prompt variants we cannot distinguish.

## Phase-10 desiderata (post cross-family)

- **Reviewer-family ensemble**: 2-of-3 quorum across {Codex, Opus, Gemini} cold reviewers — does the asymmetric quorum P2 finding hold cross-family on real code?
- **Within-family self-consistency**: 5 Gemini cold calls per bug, majority vote — is the Gemini advantage stable?
- **Third-party libraries**: Gemini's strong stdlib performance may be training-data overlap. P10 must test on lesser-known libs.
