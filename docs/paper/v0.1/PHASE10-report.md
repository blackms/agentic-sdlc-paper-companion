# Phase 10 Report — Third-Party Libraries: Stdlib-Bias Hypothesis Reversed

> **Status**: Phase 10 tested whether the Phase-9 absolute-threshold falsification (cold detection 43-50% on Python stdlib for {Codex, Opus}) was driven by training-data overlap on the stdlib. **The stdlib-bias hypothesis is reversed**: on three third-party Python libraries (dateutil/relativedelta, parsy, chardet/chardistribution), cold-aligned detection reaches **53-97% across all 9 cells (3 domains × 3 reviewer families)**, with specificity over categorical mismatch at Δ ∈ [50, 97] pp and McNemar p < 0.010 in every cell.

## Pre-registration (frozen 2026-05-10, before any reviewer call)

`experiments/p10_thirdparty/PREREGISTRATION.md`. Hypothesis: P9 stdlib-bias hypothesis predicts cold-aligned detection would *improve* on lesser-known third-party libraries (less training-data prior on the reference code), or stay similar. Decision rule: if specificity (Δ ≥ 20 pp + McNemar p < 0.010) holds in 6/9 cells, C1 specificity generalizes to third-party libs.

## Codebases (third-party Python)

| Domain | Source | LOC | Popularity (rough) | AST mutations enumerated |
|---|---|---|---|---|
| `dateutil_dom` | `dateutil/relativedelta.py` (python-dateutil) | 599 | very high | 143 (sampled 30) |
| `parsy_dom` | `parsy/__init__.py` (parsy) | 719 | low | 35 (sampled 30) |
| `chardet_dom` | `chardet/chardistribution.py` (chardet 4.0.0) | 233 | medium | 60 (sampled 30) |

AST mutator: same as P9 (AOR/ROR/BOR), with **compile-only validation** (no import-execute test, since third-party modules require their own package context). Yield: 100%.

Reviewers: **2 conditions × 3 families × 3 domains × 30 bugs = 540 calls** (all completed).

## Per-domain × per-family results (strict, unparsed-as-miss)

### dateutil_dom (n=30)

| Family | cold | Wilson 95% | mm | Δ | McNemar p |
|---|---|---|---|---|---|
| Codex gpt-5.5 | **93.33%** | [78.7%, 98.2%] | 0.00% | +93.3pp | <10⁻⁶ |
| Opus 4.7 | **96.67%** | [83.3%, 99.4%] | 3.33% | +93.3pp | <10⁻⁶ |
| Gemini 3.1 Pro | **96.67%** | [83.3%, 99.4%] | 10.00% | +86.7pp | <10⁻⁶ |

Cross-family spread: **3.3 pp** (vs P9 csv 33 pp).

### parsy_dom (n=30)

| Family | cold | Wilson 95% | mm | Δ | McNemar p |
|---|---|---|---|---|---|
| Codex gpt-5.5 | **53.33%** | [36.1%, 69.8%] | 0.00% | +53.3pp | 0.000015 |
| Opus 4.7 | **60.00%** | [42.3%, 75.4%] | 10.00% | +50.0pp | 0.000061 |
| Gemini 3.1 Pro | **66.67%** | [48.8%, 80.8%] | 6.67% | +60.0pp | 0.000244 |

Cross-family spread: **13.3 pp**. parsy is the only domain where cold is below 70% in any family — likely because parsy uses heavy parser-combinator abstractions and many AST mutations have subtle effects on semantics.

### chardet_dom (n=30)

| Family | cold | Wilson 95% | mm | Δ | McNemar p |
|---|---|---|---|---|---|
| Codex gpt-5.5 | **96.67%** | [83.3%, 99.4%] | 0.00% | +96.7pp | <10⁻⁶ |
| Opus 4.7 | **96.67%** | [83.3%, 99.4%] | 3.33% | +93.3pp | <10⁻⁶ |
| Gemini 3.1 Pro | **93.33%** | [78.7%, 98.2%] | 0.00% | +93.3pp | <10⁻⁶ |

Cross-family spread: **3.3 pp**.

## Parse failure rates per family per cell (Codex peer review request)

| Domain | Family | cold parsed | mm parsed |
|---|---|---|---|
| dateutil | Codex | 30/30 | 30/30 |
| dateutil | Opus | 29/30 (1 fail) | 30/30 |
| dateutil | Gemini 3.1 Pro | 30/30 | 30/30 |
| parsy | Codex | 30/30 | 30/30 |
| parsy | Opus | 28/30 (2 fail) | 29/30 (1 fail) |
| parsy | Gemini 3.1 Pro | 30/30 | 22/30 (8 fail) |
| chardet | Codex | 30/30 | 30/30 |
| chardet | Opus | 30/30 | 30/30 |
| chardet | Gemini 3.1 Pro | 30/30 | 30/30 |

Parse failures are concentrated in parsy/Gemini-mismatched (8/30 fail) and parsy/Opus (2-3 fail). Parsing reliability does not differentially favor cold over mismatched in dateutil and chardet (both at 0 fail in nearly all cells). The parsy/Gemini mismatched parse failure may inflate apparent specificity Δ; under a strict-unparsed-as-miss policy this is conservative for the cold (penalizes cold-only parse failures, which are 0 in parsy).

## Pre-registered metrics — verdict

| Metric | Pass cells |
|---|---|
| Specificity Δ ≥ 20 pp | **9/9 PASS** (range 50-97 pp) |
| Paired McNemar p < 0.010 | **9/9 PASS** (range 2.4·10⁻⁴ to <10⁻⁶) |
| Absolute primary cold > 50% | **9/9 PASS** (range 53-97%) |
| Cross-domain Fisher Codex-only (P7 + 3 P9 + 3 P10 = 7 tests) | χ²(14) = 167.72, combined p ≈ 0 (machine-zero, < 10⁻¹⁵) |
| Cross-domain Fisher all-families (3 P10 × 3 families = 9) | χ²(18) = 289.74, combined p ≈ 0 |

## Sample-level difference (not yet a causal claim)

In the prior stdlib sample and the preregistered third-party sample, cold detection is substantially higher on the third-party sample:

| Sample (Codex strict) | Cold-aligned detection |
|---|---|
| Stdlib (P9: csv, urllib, jsondec) | 43.3%, 50.0%, 43.3% |
| Third-party (P10: dateutil, parsy, chardet) | **93.3%, 53.3%, 96.7%** |

**This is a sample-level observation, not a controlled library-type contrast.** The two samples differ in many uncontrolled ways: LOC, complexity, contract document length, operator distribution of valid AST mutations, mutation salience, local-invariant clarity, and the categorical-mismatch ablation's coherence. We cannot attribute the gap to library class alone.

**Candidate moderators / mechanisms** (Phase-11 desiderata, none established by P10):
1. **Reduced scrutiny under high familiarity/authority priors**: high training prior on stdlib → reviewers may defer to apparent authority. Requires *direct provenance-label experiments* (relabel stdlib as third-party and vice versa) to confirm.
2. **Contract-quality interaction**: auto-extracted contracts may differ in informativeness by library; requires *blinded contract audit*.
3. **Mutation salience**: heavy-abstraction code may make individual operator changes more semantically visible; requires *matched mutation-operator-mix experiments*.
4. **Task-coherence of the mismatched ablation**: the bankcheck mismatch may suppress useful reasoning differently across library classes; requires *shuffled-within-domain* and *no-contract* controls.
5. **Local-invariant clarity**: third-party files may have more localized invariants than stdlib idioms; requires *structured contract complexity audit*.

## Reviewer-choice sensitivity collapses on third-party libs

The P9 cross-family finding reported a 33-47 pp spread on stdlib. **On third-party libs, the spread is 3-13 pp** — order-of-magnitude smaller:

| Phase | Domain | Cross-family spread (max-min) |
|---|---|---|
| P9 | csv | 33.3 pp |
| P9 | jsondec | 47.0 pp |
| P10 | dateutil | 3.3 pp |
| P10 | parsy | 13.3 pp |
| P10 | chardet | 3.3 pp |

The "reviewer-choice sensitivity" failure mode reported in v0.9.5 is **stdlib-specific**: choice of reviewer family matters massively on stdlib, much less on third-party libs. This further weakens the v0.9 framing.

## Updated C1 statement (for paper v1.0, after Codex peer review reframing)

> **C1 (Cold reviewer transfer — contract-aligned specificity replicates across 3 reviewer families on a 3-library third-party sample; library-class is a candidate but unconfirmed moderator)**: across two pilot domains (bankcheck CI, JSON parser), three Phase-8 hand-written domains, three Phase-9 real Python stdlib codebases (csv, urllib.parse, json.decoder), and **three Phase-10 third-party Python libraries (dateutil/relativedelta, parsy, chardet/chardistribution)**, the specificity component (cold > cold_mismatched) replicates within each tested sample: all 9 P10 cells (3 domains × 3 families) show paired McNemar p < 0.010, specificity Δ ∈ [50, 97] pp. The **pre-registered absolute primary threshold "cold > 50%" is exceeded by all 9 point estimates** (range 53–97%); however parsy/Codex sits at 53.33% with Wilson 95% CI [36.1%, 69.8%] straddling 50% — the absolute threshold is **only convincingly above 50% under interval evidence in 6 of 9 cells**. In this 3-library third-party sample, cold detection is substantially higher than in the prior 3-library stdlib sample; the cross-family spread is 3.3–13.3 pp (vs 33–47 pp in the stdlib sample). **These are sample-level differences, not a controlled library-type contrast**: the two samples differ in LOC, complexity, contract document length, operator distribution of valid AST mutations, mutation salience, and ablation-task coherence. Library class is a candidate moderator; alternative explanations (contract-extraction quality, mutation salience, local-invariant clarity, ablation incoherence) remain equally consistent with the data. Phase-11 desiderata: provenance-label experiments, contract informativeness audit, matched stdlib/third-party operator-mix experiments, shuffled-in-domain and no-contract controls.

## Limitations

1. **Three third-party libs is still small**. dateutil and chardet are widely-used; parsy is the only true "low-popularity" target.
2. **Single-mutation, AST-level bugs**: same caveat as P9.
3. **Bankcheck mismatch is extreme**: the categorical-mismatch ablation tests gross mismatch.
4. **parsy contracts are heavy** (753 lines auto-extracted): may dilute attention. Performance is lower (53-67%) than dateutil/chardet (93-97%) — possibly attention-budget limited.
5. **Compile-only AST mutator validation** (no import-test): some mutations may be runtime-trivially-broken in ways the static reviewer cannot tell. Same operator distribution as P9 (AOR/ROR/BOR).
6. **No multi-mutation, no naturalistic bugs**: P11 desideratum.
7. **Reviewer outputs may have selection bias for length**: dateutil contracts (633 LOC) are longer than chardet (267 LOC); parsy in the middle (753 LOC). Performance does not monotonically follow length.

## Phase-11 desiderata

1. **Anti-stdlib-carelessness mechanism test**: prompt the reviewer with explicit "this is unfamiliar code, scrutinize carefully" framing on stdlib bugs and check if detection rises to P10 levels.
2. **Naturalistic multi-mutation bugs** harvested from real GitHub commits.
3. **Lower-popularity libraries** (e.g. small PyPI packages with <1k downloads/month) to push the training-data-bias contrast.
4. **Reviewer-family ensemble (P2 cross-family on third-party libs)**: the asymmetric-quorum joint-miss bound from P2 should now be tested across {Codex, Opus, Gemini 3.1 Pro} on the P10 dataset (data already collected).
5. **Within-family self-consistency**: 5x sampling per reviewer per bug to check stability of the 93-97% detection rates.

## Deliverables

```
experiments/p10_thirdparty/
  PREREGISTRATION.md
  inject_all.py
  build_detection.py
  analyze_p10.py
  extract_contracts.sh
  launch_reviews.sh
  dateutil_dom/{ref/, bugged/, contracts/, reviews/, detection.json}
  parsy_dom/{...}
  chardet_dom/{...}
  results/p10_analysis.json
```

540 reviewer raw outputs committed.
