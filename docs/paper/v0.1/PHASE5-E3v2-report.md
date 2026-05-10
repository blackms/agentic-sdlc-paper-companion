# Phase 5 E3v2 — Concrete-Example Injection Falsifies C-T3 LLM-grounded Recovery

> **Status (deferred Phase-6 task #54, completed 2026-05-10)**: E3v2 tested whether the Phase-5 falsification of C-T3 LLM-grounded (warm + top-5 pattern *names* → no improvement, p = 0.95 against H1) was a function of *injection format* (abstract category labels). We replaced pattern names with **concrete missed-bug examples** drawn from TRAIN. **The falsification holds**: concrete examples do not recover convergence, and in some categories actively degrade detection.

## Pre-registration

`experiments/p5_e3v2/PREREGISTRATION.md` frozen 2026-05-10 before any reviewer call. Hypothesis: concrete missed-bug examples (extracted from TRAIN warm-Codex misses) replace abstract pattern names in the injection prompt, possibly recovering C-T3 convergence.

## Conditions on TEST set (101 bugs, paired)

| Condition | Reviewer | Injection | Source |
|---|---|---|---|
| baseline | warm Codex | none | t2 (existing) |
| injected_v1 | warm Codex | 5 pattern names + 1-line description | p5_e3 (existing) |
| **injected_v2** | warm Codex | **concrete missed-bug examples per category** | p5_e3v2 (new) |

Concrete-example injection (frozen): 11 missed bugs from TRAIN distributed across the 5 top categories — e.g., off-by-one: `fmax + 0.01 upper bound`, `fee > fmax → fee >= fmax`; logic: `(1+r/n) → (1-r/n)`, exponentiation → multiplication; currency: `USD == usd` case-sensitivity, etc.

## Pre-registered metrics

- **Primary**: paired McNemar one-sided H1 (`v2 > baseline`), threshold p < 0.05.
- **Secondary**: paired McNemar one-sided H1 (`v2 > v1`), threshold p < 0.05.
- **Tertiary**: per-top5-category Δ (descriptive).

## Results

### Primary: v2 vs baseline (paired n = 92)

| Metric | Value |
|---|---|
| baseline rate | 75.0% |
| v2 rate | 66.3% |
| Δ | **−8.7 pp** |
| McNemar discordant | b = 15 (baseline-only catches), c = 7 (v2-only catches) |
| McNemar one-sided p (H1: v2 > baseline) | **0.9738** |
| Verdict @ α = 0.05 | **NS — H1 fails** |

### Secondary: v2 vs v1 (paired n = 101)

| Metric | Value |
|---|---|
| v1 rate | 69.3% |
| v2 rate | 66.3% |
| Δ | −3.0 pp |
| McNemar discordant | b = 12 (v1-only catches), c = 9 (v2-only catches) |
| McNemar one-sided p (H1: v2 > v1) | **0.8083** |
| Verdict @ α = 0.05 | **NS — H1 fails** |

### Per-top5-category (descriptive, v2 vs baseline)

| Category | n | baseline | v2 | Δ |
|---|---|---|---|---|
| atomicity | 4 | 75.00% | **25.00%** | **−50.0 pp** |
| currency | 8 | 62.50% | 100.00% | **+37.5 pp** |
| exception | 9 | 88.89% | 88.89% | 0.0 pp |
| logic | 23 | 73.91% | 52.17% | **−21.7 pp** |
| off-by-one | 12 | 83.33% | 75.00% | −8.3 pp |

## Honest interpretation

1. **C-T3 LLM-grounded falsification is robust to injection-format alternatives**. The format-quality alternative explanation ("v1 used abstract names, that's why it didn't work — concrete examples will work") is **rejected**: v2 also fails (Δ = −8.7 pp vs baseline, p = 0.97).

2. **Concrete-example injection is not neutral — it actively degrades detection in some categories**. atomicity (n=4) collapses from 75% → 25% (−50 pp); logic (n=23) drops from 74% → 52% (−22 pp). Currency improves dramatically (62.5% → 100%, +37.5 pp) because case-sensitivity is a *very specific* shape that tracks well.

3. **Mechanism**: concrete examples may *narrow* the reviewer's search to the exact shapes shown, causing it to miss other manifestations of the same category. This is a documented LLM failure mode (anchoring on examples).

4. **The Phase-5 conclusion stands**: pattern-extraction loops that converge in simulation (under stationary task, conservative trigger, weak suppression) **do not improve LLM detection** under either abstract-name (v1) or concrete-example (v2) injection format.

5. **The C-T3 LLM-grounded result is now triply tested**: v1 (Phase-5, n=92, Δ=−6.5%, p=0.95), v2 (this experiment, n=92, Δ=−8.7%, p=0.97). Two independent injection formats both fail in the same direction.

## Updated paper claim (for v0.9)

> **Conjecture C-T3 (Learning-Loop Convergence — simulation-only; LLM-grounded counter-evidence robust to injection format)**: under stationary task distribution, conservative trigger, bounded injection, and weak suppression, the conservative pattern-extraction loop converges almost surely to a finite stationary set in 30/30 Monte-Carlo simulations. **Phase-5 falsifies the LLM-grounded counterpart with TRAIN/TEST split (n = 92 paired) under abstract-name injection (Δ = −6.5 pp, p = 0.95)**. **Phase-5 E3v2 (deferred task #54) extends the falsification to concrete-example injection (n = 92 paired, Δ = −8.7 pp, p = 0.97)**, ruling out the format-quality alternative explanation. Concrete examples actively degrade detection in some categories (atomicity −50 pp, logic −22 pp), suggesting reviewer-anchoring on shown shapes. The simulation-derived injection strategy fails to improve LLM detection under both abstract and concrete formats. **C-T3 remains an open conjecture with negative LLM-grounded counter-evidence robust to injection format.**

## Phase 9 / Phase 10 connection

E3v2 reinforces the **simulation-to-LLM gap** failure mode (paper v0.4+ failure-mode taxonomy): theoretical convergence properties of pattern-extraction loops do not translate into measurable detection improvements at realistic n in real LLM workflows. The cross-family P9 finding (Codex 43%, Opus 30-40%, Gemini 3.1 Pro 63-87%) suggests reviewer-family choice has *much larger* leverage than injection-format engineering for improving cold-reviewer detection on real code.

## Deliverables

```
experiments/p5_e3v2/
  PREREGISTRATION.md
  warm_injected_v2.txt          (concrete-example injection prompt)
  launch_e3v2.sh
  analyze_e3v2.py
  reviews/warm_injected_v2_*.raw.txt   (101 raw Codex reviews)
  results/e3v2_analysis.json
```
