# Companion Repository — Rocchi 2026 v1.4.3

**Paper.** *Conformance, Cost, and Replication in Constrained LLM Coding
Agents.* PDF at [`docs/paper/paper-latex/rocchi-2026-measuring-llm-agents.pdf`](docs/paper/paper-latex/rocchi-2026-measuring-llm-agents.pdf).

**Pre-registration chronology.** Every pre-registration file in this
repository has exactly one commit in its git history (no edits, no
amendments). The chronology — including the orchestrator HALT gate
from [`docs/paper/v1.4/coordination.md`](docs/paper/v1.4/coordination.md)
and the filesystem birth times of each pre-registration — is documented
in [`STATEMENT.md`](STATEMENT.md). Reviewers checking the timing of
pre-registrations against reviewer outputs should read that document
first.

This repository contains exactly the artefacts needed to reproduce the
paper's numerical claims:

- the manuscript LaTeX source + compiled PDF,
- frozen pre-registration documents for every experimental phase,
- raw analyzer scripts and the bug corpora they consume,
- the redacted reviewer outputs (`bugs_found` JSON only — see §Redaction below),
- the master validation runner that checks 32 numerical claims against
  the on-disk results in ≈30 seconds,
- minimal excerpts of the five framework components the paper measures
  by name (Sec. D: CALCULATION-CONTRACT, DUAL-AGENT-REVIEW,
  DECISION-TRACE, BANKING profile, reviewer roles).

This repository **does not** contain the broader agentic-sdlc framework
(40+ protocols, agent/skill definitions, integration layer, business
materials). The framework is a separate proprietary work; its full
protocol bodies are not required to assess the paper, and the excerpts
in `framework-excerpts/` declare what is needed.

## Quick start

```bash
./docs/paper/validations/validate_all.sh
```

Expected output:

```
PASS: 32  FAIL: 0
[validate_all] ALL PASS — no numerical-claim drift from v1.3.2 + v1.4 stream outputs.
```

To also re-run every per-phase analyzer against the redacted raw
reviews (≈2 min, requires `python3` with `scipy` and `statsmodels`):

```bash
RERUN=1 ./docs/paper/validations/validate_all.sh
```

Both modes are expected to produce 32/32 PASS at this repository's
freeze. See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the full
protocol.

## Repository layout

```
docs/paper/
  paper-latex/             LaTeX source + compiled PDF + Makefile + references.bib
  preregistrations/        v1.4 phase-replication and naturalistic pre-regs (frozen 2026-05-11)
  phase-reports/           Per-phase post-hoc reports referenced by §8 of the paper
  tech-reports/            cmdp-extension.md (cited from §3 of the paper as standalone)
  validations/             validate_all.sh — master numerical-claim checker (32 assertions)
  reproducibility-statement.md

framework-excerpts/
  01-calculation-contract.md   schema, invariants, embedding format
  02-dual-agent-review.md      2-of-3 asymmetric quorum, role context restriction
  03-decision-trace.md         immutable hash-chained decision record
  04-banking-profile.md        YAML profile that activates finance protocols
  05-reviewer-roles.md         cold / warm / skeptic role definitions
  README.md                    what this folder is and what it omits

experiments/
  prompts/                 P_compound_interest.txt, P_transfer.txt, free-prompt baselines
  tasks/                   T1, T2 task specifications
  harness/                 oracle_T1.py, oracle_T2.py, aggregate.py
  t2/                      Phase 4 (E1 + 2×2 factorial)
  p5_e2/                   Phase 5 L1 cross-domain falsification (bankcheck.py)
  p5_e3/                   Phase 5 C-T3 abstract-name injection
  p5_e3v2/                 Phase 5 C-T3 concrete-example injection
  p6_e2v2/                 Phase 6 auto-extracted contracts recovery
  p7_parser/               Phase 7 JSON parser (second domain)
  p8_multidomain/          Phase 8 (expression evaluator, regex compiler, HTTP header parser)
  p9_real/                 Phase 9 stdlib (csv.py, urllib/parse.py, json/decoder.py)
  p10_thirdparty/          Phase 10 (dateutil, parsy, chardet)
  p11_provenance/          Phase 11 v1.3 provenance label
  p11_replication/         Phase 11 Amendment A1 saturation
  naturalistic_csv/        Phase 12 naturalistic csv.py bugs (CPython issue tracker)
  mixed_effects/           v1.4 primary inference (BinomialBayesMixedGLM, 14 cells)
  cluster_robust.py        L1 finance-domain joint-miss permutation
  cluster_robust_c1.py     C1 cross-phase permutation + block-bootstrap

tools/
  redact_reviews.py        The script that produced experiments/**/reviews/*.raw.txt
                           in this repo from the originals (see §Redaction).
```

## Claim → script map

| Paper claim | Section | Recompute |
|---|---|---|
| E1: ΔE[u] ∈ [+0.59, +0.78]; eFOSD on 80/80 thresholds; G ∈ [0.21, 1.11] | §4, §8.3 | `experiments/t2/analyze_t2_v2.py` |
| L1: q_symm−mono = 22.91% → q_asymm−multi = 12.28%; ρ̄ 0.62 → 0.29; McNemar p=0.0013 | §5, §8.3 | `experiments/cluster_robust.py` → `experiments/results_cluster_robust.json` |
| L1 cross-domain falsified (bankcheck.py, 5 contrasts, all p ≥ 0.5) | §8.4 | `experiments/p5_e2/analyze_e2.py` |
| C-T3 abstract injection: −6.5 pp, p = 0.95 against H1 | §8.4 | `experiments/p5_e3/analyze_cycle1.py` |
| C-T3 concrete (E3v2): −8.7 pp, p = 0.97 against H1 (n = 92) | §6.5 | `experiments/p5_e3v2/analyze_e3v2.py` |
| P6 recovery: 11 % → 73 % | §8.5 | `experiments/p6_e2v2/parse_and_analyze.py` |
| P7 (JSON parser): +73 pp, McNemar p = 0.0078 | §8.6 | `experiments/p7_parser/analyze_p7.py` |
| P8 (3 hand-written domains): Fisher's combined p = 0.021 | §8.7 | `experiments/p8_multidomain/analyze_p8.py` |
| P9 Codex per-domain Δ (csv/urllib/jsondec): 43.3 / 50.0 / 43.3 pp | §8.8 | `experiments/p9_real/analyze_p9.py` |
| P9 cross-family on csv (Codex / Opus / Gemini 3.1): 43.3 / 26.7 / 60.0 pp | §8.8 | `experiments/p9_real/analyze_cross_family.py` |
| P10 (9 cells × 3 fams × 2 cond): all McNemar p < 10⁻⁴ | §8.8 | `experiments/p10_thirdparty/analyze_p10.py` |
| Cross-phase pooled mixed-effects: β_cond = +4.20 (z = 33.4) | §A.1.4 | `experiments/mixed_effects/fit.py` |
| Cross-phase block-bootstrap pooled Δ = +67.4 pp, CI [+55.2, +79.5] | §8.8 | `experiments/cluster_robust_c1.py` |
| P11 v1.3 H1a/H1b both fail (p ∈ [0.13, 0.34]) | §8.9 | `experiments/p11_provenance/analyze_p11.py` |
| P11 v1.4 (Amendment A1) replication: csv Δ = 0.0 pp, p = 0.61; chardet Δ = −3.3 pp, p = 0.31 | §8.10 | `experiments/p11_replication/analyze.py` |
| P12 naturalistic (n = 8): Codex Δ = 62.5 pp p = 0.029; Opus 12.5 p = 0.50; Gemini 62.5 p = 0.031. Codex leakage = 100 %. 0/3 families clear Bonferroni α = 0.025 | §8.11 | `experiments/naturalistic_csv/analyze.py` |

## Redaction

Every reviewer transcript under `experiments/**/reviews/*.raw.txt` has
been processed by `tools/redact_reviews.py`. Each redacted file
preserves only:

1. A 2-line header recording the SHA-256 and byte length of the
   original transcript.
2. A fenced JSON block containing the reviewer's response —
   `{"bugs_found": [...], "verdict": "ACCEPT" | "REQUEST_CHANGES"}` —
   exactly as the downstream analyzers consume it.

What is removed: the LLM CLI session metadata (model snapshot tag,
workdir, sandbox config), the role-conditioned prompt body, the
embedded contract text, and any free-text prose around the JSON.
A per-folder `reviews_summary.jsonl` records, for every transcript,
the structured metadata sufficient for audit (role, family, condition,
bug_id, raw_sha256, raw_bytes, bugs_found_len, verdict).

The redactor uses the same JSON-extraction algorithm as the owning
analyzer per phase (P9-family or naturalistic-family), so re-running
`RERUN=1 validate_all.sh` produces byte-identical results.json files
to the frozen baseline reported in the manuscript.

Reviewers needing the full original transcripts under NDA — e.g., to
inspect the cold reviewer prompt body or the auto-extracted contract
text — can contact the corresponding author
(`rocchi.b.a@gmail.com`).

## Pre-registration audit

Every empirical claim is backed by a pre-registration whose git commit
timestamp predates the first reviewer call of the phase it covers:

- v0.1 phase pre-registrations: see `experiments/<phase>/PREREGISTRATION.md`.
- v1.4 stream pre-registrations: see `docs/paper/preregistrations/`.

The chain of `docs/paper/phase-reports/PHASE*-report.md` files
documents how the analysis evolved between phases. The `[REFRAMED]`
markers in the manuscript text track every place where the
interpretation changed (e.g., Phase-11 reframing from
"anti-stdlib carelessness" to "label-prior null") and link to the
report that justified the change.

## Citation

See [`CITATION.cff`](CITATION.cff). The paper is licensed under
CC-BY-4.0 (`LICENSE-paper`); the code in this companion repository is
licensed under Apache-2.0 (`LICENSE`).

## Contact

Alessio Rocchi — `rocchi.b.a@gmail.com` — AIGEN Solutions.
