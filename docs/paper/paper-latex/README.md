# LaTeX Paper — v1.1

Single-document LaTeX manuscript covering Phases 1–11 with full math
formulas, theorem environments, and Codex peer-review trail.

## Build

### Option A: pdflatex
```bash
make
```
runs `pdflatex → bibtex → pdflatex → pdflatex` to resolve cross-refs,
citations, and the table of contents.

### Option B: tectonic (recommended — single-pass, auto-deps)
```bash
brew install tectonic
make tectonic
```

### Option C: latexmk
```bash
latexmk -pdf main.tex
```

## Structure

| File | Section | Phase coverage |
|---|---|---|
| `main.tex` | Master | All |
| `abstract.tex` | Abstract | All |
| `01-introduction.tex` | §1 Introduction | All |
| `02-related-work.tex` | §2 Related Work | — |
| `03-formal-model.tex` | §3 Formal Model (CMDP) | Framework |
| `04-decisional-metric.tex` | §4 Decisional Metric V | P1, P4 |
| `05-asymmetric-verification.tex` | §5 Joint-Miss Bound | P2, P4–5 |
| `06-learning-loop.tex` | §6 Learning Loop | C-T3, P5, E3v2 |
| `07-theorems-propositions.tex` | §7 Theorems & Status | All |
| `08-experiments.tex` | §8 Experiments | P1–P11 |
| `09-discussion.tex` | §9 Discussion + 10 failure modes | All |
| `10-conclusion.tex` | §10 Conclusion + Phase-12 desiderata | All |
| `A1-statistical-methods.tex` | Appendix: stats methods | All |
| `references.bib` | Bibliography (stub — to populate) | — |

## Math conventions

- Verifier kernels: `V`, `V_C`, `V_S` (calligraphic V symbol via `\Ver`).
- Decisional metric: `𝒱` (script V) via `\Vmetric` — disambiguated from `V`.
- Protocols: `\proto` (constrained), `\protoZero` (free prompting).
- Predicates: `\PredC`, `\PredS`.
- Behavior signature: `B = \varphi(\tau)`.
- Indicator: `\ind` (via `dsfont`).

## Phase 11 update

The Phase-11 provenance-label experiment (Codex, n=60 paired) is included
in §8.10 with full result table and verdict. Both pre-registered
hypotheses (H1.csv: relab > truth; H1.chardet: relab < truth) FAIL at
α=0.05. The "anti-stdlib carelessness" mechanism speculated in earlier
drafts is empirically rejected; the abstract reflects this.

## Reproducibility

Every numerical claim in the paper has a recompute script:
- Phase 4: `experiments/p1_p4/validations/cap*_validate.py`
- Phase 5: `experiments/p5_e3/analyze_cycle1.py`, `experiments/p5_e3v2/analyze_e3v2.py`
- Phase 9: `experiments/p9_real/analyze_p9.py`, `analyze_cross_family.py`
- Phase 10: `experiments/p10_thirdparty/analyze_p10.py`
- Phase 11: `experiments/p11_provenance/analyze_p11.py`

## Status

This is **v1.1 draft**, post-Phase 11 reframing. Outstanding items
toward submission:
- Populate `references.bib` (currently 5 stub entries).
- Add figures (currently text-only; no plots).
- One more adversarial peer review pass on the full LaTeX manuscript.
- Phase-12 experiments (no-contract baseline, contract audit, matched-LOC).
