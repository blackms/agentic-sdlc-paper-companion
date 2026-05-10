# P11 Pre-registration — Provenance-Label Experiment (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: The Phase-10 sample-level difference (stdlib cold detection 43-50% << third-party cold detection 93-97%) is causally moderated by the reviewer's prior expectation about code provenance (familiarity / authority). Codex peer review on P10 explicitly required: *"manipulate provenance labels, familiarity, and contract source"* to demonstrate or refute anti-stdlib carelessness.

## Design

For each bug, two new conditions are added on top of the existing cold-aligned condition:

### Stdlib bugs (csv_dom, P9): 30 bugs

| Condition | Prompt prefix | Existing? |
|---|---|---|
| `cold_truthful_stdlib` | "Reviewing csv.py from the Python standard library" | YES (P9 cold = 13/30 = 43.33%) |
| `cold_relabeled_thirdparty` | "Reviewing a third-party library `csv_processing` (not part of stdlib)" | **NEW (P11)** |

### Third-party bugs (chardet_dom, P10): 30 bugs

| Condition | Prompt prefix | Existing? |
|---|---|---|
| `cold_truthful_thirdparty` | "Reviewing chardistribution.py from the third-party `chardet` library" | YES (P10 cold = 29/30 = 96.67%) |
| `cold_relabeled_stdlib` | "Reviewing `charset_module.py` from the Python standard library" | **NEW (P11)** |

The bugged code is **byte-identical** across conditions. Only the leading 1-line provenance statement changes. The auto-extracted contracts are also **byte-identical** (same domain-aligned contracts in both conditions).

## Reviewer

P11 uses **Codex gpt-5.5** only (the same family that showed the strongest stdlib-vs-third-party gap on identical bugs: csv 43% vs chardet 96.7%). If anti-stdlib carelessness is real, the effect should be largest with the reviewer family that exhibited the largest sample gap. Cross-family extension (Opus, Gemini) deferred to P11.2 if effect direction confirmed.

Total calls: 30 + 30 = **60 Codex review calls**.

## Pre-registered metrics

### Primary (anti-stdlib carelessness hypothesis)

- **H1.csv**: `cold_relabeled_thirdparty` rate > `cold_truthful_stdlib` rate on csv bugs (relabeling stdlib as third-party INCREASES detection). McNemar paired one-sided p < 0.05.
- **H1.chardet**: `cold_relabeled_stdlib` rate < `cold_truthful_thirdparty` rate on chardet bugs (relabeling third-party as stdlib DECREASES detection). McNemar paired one-sided p < 0.05.

### Decision rules

| Outcome | Interpretation |
|---|---|
| Both H1.csv and H1.chardet PASS | **Anti-stdlib carelessness CONFIRMED**: label/familiarity prior causally moderates detection. |
| One passes, one fails | Asymmetric effect; needs deeper investigation. Specify which direction held. |
| Both fail | **Anti-stdlib carelessness REJECTED on this test**; the P9-P10 sample gap is driven by code-intrinsic factors (mutation salience, contract quality, complexity), not by label/familiarity. |

### Secondary (descriptive)

- Per-bug detection flip table (which bugs changed verdict on relabeling).
- Joint contingency table (truthful × relabeled).
- Wilson 95% CI on each rate.

## Frozen rules

- 60 reviewer calls executed in single batch with frozen prompts.
- No prompt iteration after observing P11 results.
- All raw outputs committed.
- Pre-registration document committed before any reviewer call.

## Risk acknowledgement

1. **Single reviewer family**: Codex only. Negative results may be Codex-specific.
2. **Two libraries**: csv (smallest stdlib gap, 43%) and chardet (highest third-party rate, 96.7%) — the strongest contrast. parsy and dateutil are excluded for budget; they sit at intermediate detection rates.
3. **Cover-story plausibility**: the relabel claim ("csv.py is a third-party library called csv_processing") is detectable. If the reviewer mentally recognizes the actual code, the manipulation may fail (positive control would be measuring whether reviewers identify the deception).
4. **Bankcheck mismatch ablation** is NOT re-run; this experiment is contract-aligned-only.

## Cover stories (frozen)

For each csv bug, the prompt header becomes:
```
This code is from `csv_processing`, a niche third-party Python library for CSV manipulation (not part of the Python standard library). The library has approximately 500 downloads/month on PyPI.
```

For each chardet bug, the prompt header becomes:
```
This code is from `charset_module`, part of the Python standard library, available as `from charset_module import ...` since Python 3.10.
```

Both cover stories are factually FALSE (the cover for csv is a fake library; the cover for chardet pretends chardet is stdlib). The reviewer is told to assume the cover is true.
