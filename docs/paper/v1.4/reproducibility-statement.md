# Reproducibility Statement — v1.4

Frozen 2026-05-11. This document enumerates every artefact required to
recompute the numerical claims in the v1.4 manuscript from scratch.

## 1. Repository layout

| Class | Path |
|---|---|
| Manuscript LaTeX | `docs/paper/paper-latex/main.tex` (entry point) + included `.tex` files |
| Compiled PDF | `docs/paper/paper-latex/rocchi-2026-measuring-llm-agents.pdf` |
| arXiv tarball | `docs/paper/v1.4/arxiv-package.tar.gz` |
| EMSE submission package | `docs/paper/v1.4/emse-submission/` |
| Per-phase raw artefacts | `experiments/<phase>/` |
| Per-phase analyzers | `experiments/<phase>/analyze*.py` |
| Cross-phase analyzers | `experiments/cluster_robust.py`, `experiments/cluster_robust_c1.py` |
| Mixed-effects fit | `experiments/mixed_effects/fit.py` |
| Validation runner | `docs/paper/validations/validate_all.sh` |
| Run log (validation) | `docs/paper/validations/validate_all.log` |

## 2. Pre-registrations (committed BEFORE first reviewer call per phase)

| Phase | Pre-registration path | Frozen |
|---|---|---|
| Phase 4 (E1) | `docs/paper/v0.1/prereg-phase4.md` | 2025-Q4 |
| Phase 5 (L1 cross-domain, C-T3 LLM-grounded) | `docs/paper/v0.1/prereg-phase5.md` | 2025-Q4 |
| Phase 7 (JSON parser) | `docs/paper/v0.1/prereg-phase7.md` | 2025-Q4 |
| Phase 9 (real stdlib) | `docs/paper/v0.1/prereg-phase9.md` | 2025-Q4 |
| Phase 10 (third-party) | `docs/paper/v0.1/prereg-phase10.md` | 2025-Q4 |
| Phase 11 (provenance falsification) | `docs/paper/v0.1/prereg-phase11.md` | 2025-Q4 |
| Phase 11 replication (Stream C, parent) | `docs/paper/v1.4/preregistration-p11-replication.md` | 2026-05-11 17:00 |
| Phase 11 replication, Amendment A1 (saturation) | `docs/paper/v1.4/preregistration-p11-replication-amendment-A1.md` | 2026-05-11 21:00 |
| Phase 12 naturalistic (Stream D) | `docs/paper/v1.4/preregistration-extend.md` | 2026-05-11 17:00 |
| v1.4 orchestrator plan | `docs/paper/v1.4/plan.md` | 2026-05-11 |
| v1.4 coordination log (append-only) | `docs/paper/v1.4/coordination.md` | 2026-05-11 — 2026-05-12 |
| v1.4 budget log | `docs/paper/v1.4/budget.md` | 2026-05-11 |
| CMDP extension (technical report) | `docs/paper/v1.4/cmdp-extension-techreport.md` | 2026-05-11 |

Each Phase-12 pre-registration item also points to its frozen-content sha256
file inside the corresponding experiment directory (see §5).

## 3. Reviewer prompt fingerprints

The following sha256 hashes pin the exact byte contents of the prompts used
throughout the experiments. Re-running with the same hashes guarantees
byte-identical reviewer input.

```
78c30abf1f1df2cf4207193437c7cc68186b4dc175af37122fecbff2f0cd1e27  experiments/prompts/P_compound_interest.txt
e925a65ad0f0e80f18a231971420beac362eb008c2e9b4e126c4231ad5ca2765  experiments/prompts/P_transfer.txt
f2f7be15c684f05902c5ec7fae76e23e199ca1ad29d421a862749398450e7948  experiments/prompts/P0_compound_interest.txt
78af00e806fc50b7e21c8b32f9e5be5bc22f573bcca6969915030873364866f4  experiments/prompts/P0_transfer.txt
```

## 4. Contract fingerprints (per phase)

```
fa28fb23b50fa6e7a083e796ee592be97d60de885c97a0645c58ba7c0769b32d  experiments/p9_real/csv_dom/contracts/contracts.md
a9630d2cdec6efcbf95bea9298005334b158cbf03e8a015405b21e368717d9dd  experiments/p9_real/urllib_dom/contracts/contracts.md
c9d7277ec34f1a83e11764c232cbe288d88ec45f826e8fa8524c9064022db8b8  experiments/p9_real/jsondec_dom/contracts/contracts.md
70228fa4cc6309928a5434de16788cf18354a6c31e5dc221fd16017d60db3105  experiments/p10_thirdparty/chardet_dom/contracts/contracts.md
5e21c98ff1a9d29b8dbe38a9947f22ca05d48059bfa2e0ca14fe8e13d5fe17ea  experiments/p10_thirdparty/dateutil_dom/contracts/contracts.md
598b792417769bb5565ccc34b65e6bae9a6a5c802fc79f5222f623219f96559b  experiments/p10_thirdparty/parsy_dom/contracts/contracts.md
```

The Phase-11 replication and Phase-12 naturalistic phases each freeze their
own complete reviewer-input set inside the experiment directory:

- `experiments/p11_replication/sha256_freeze.txt` — modules, AST mutator, cold
  prompt, contracts, bugged sources, and manifest for Phase-11 replication
  under Amendment A1.
- `experiments/naturalistic_csv/sha256_freeze.txt` — harvested CPython
  `csv.py` bugs, reversal patches, bugged sources, cold prompt, contracts,
  bankcheck contracts (for mismatched condition), out-of-band probe prompt,
  and manifest for Phase 12.

## 5. Validation scripts (re-runnable)

| Script | Purpose |
|---|---|
| `docs/paper/validations/validate_all.sh` | Re-checks 32 numerical claims spanning P9, P10, P11 provenance, P11 replication, naturalistic Phase 12, and the cross-phase mixed-effects fit against the on-disk results JSON; returns non-zero on drift above a per-claim floating-point tolerance. Optional `RERUN=1` re-runs every per-phase analyzer first. |
| `experiments/cluster_robust.py` | Cluster-robust paired permutation for finance-only contrasts. |
| `experiments/cluster_robust_c1.py` | Cluster-robust paired permutation + block-bootstrap for C1 cross-phase (14 cells). |
| `experiments/p7_parser/analyze_p7.py` | Phase 7 (JSON parser). |
| `experiments/p9_real/analyze_p9.py` | Phase 9 (real stdlib, in-family). |
| `experiments/p9_real/analyze_cross_family.py` | Phase 9 (Codex/Opus/Gemini on csv). |
| `experiments/p10_thirdparty/analyze_p10.py` | Phase 10 (third-party). |
| `experiments/p11_provenance/analyze_p11.py` | Phase 11 (provenance falsification, v1.3, n=30). |
| `experiments/p11_replication/analyze.py` | Phase 11 replication (Amendment A1 saturation, n=53/60). |
| `experiments/naturalistic_csv/analyze.py` | Phase 12 (naturalistic csv.py, n=8). |
| `experiments/mixed_effects/fit.py` | BinomialBayesMixedGLM fit on 14-cell long format; per-bug + per-module random effects, library-class moderator. |
| `experiments/mixed_effects/comparison_tables.py` | Side-by-side McNemar / permutation / mixed-effects per-cell and pooled tables. |

`docs/paper/validations/validate_all.log` records the most recent run (exit
status 0, 32/32 PASS at v1.4 freeze).

## 6. Model snapshot identifiers per phase

| Phase | Codex | Claude Opus | Claude Sonnet | Gemini |
|---|---|---|---|---|
| Phases 1--5 (pilot, E1, L1, C-T3) | `gpt-5.5` | 4.7 | 4.6 | 2.5 Flash |
| Phase 6--7 (recovery, JSON parser) | `gpt-5.5` | 4.7 | 4.6 | 2.5 Flash |
| Phase 8 (multi-domain) | `gpt-5.5` | — | — | — |
| Phase 9 (real stdlib, in-family) | `gpt-5.5` | — | — | — |
| Phase 9 (cross-family on csv) | `gpt-5.5` | 4.7 | — | 3.1 Pro Preview |
| Phase 10 (third-party, 9 cells) | `gpt-5.5` | 4.7 | — | 3.1 Pro Preview |
| Phase 11 provenance | `gpt-5.5` | — | — | — |
| Phase 11 replication (Stream C, A1) | `gpt-5.5` | — | — | — |
| Phase 12 naturalistic (Stream D) | `gpt-5.5` | 4.7 | — | 3.1 Pro Preview |

Within-phase comparisons use a single model snapshot; cross-phase aggregation
involving Gemini introduces the version-skew confounder described in §8.4
(Conclusion validity) of the manuscript.

## 7. Raw-output coverage

| Phase | Reviewer calls | Raw output path |
|---|---|---|
| Phase 4 (E1 + 2x2 factorial) | 1{,}400 | `experiments/runs/` (T1, T2 sub-directories) |
| Phase 5 (L1 cross-domain) | 135 | `experiments/p5_e2/` (raw + analyzer) |
| Phase 5 (C-T3 abstract-name) | 184 | `experiments/p5_e3/` |
| E3v2 (C-T3 concrete-example) | 184 | `experiments/p5_e3v2/` |
| Phase 6 (auto-extracted contracts) | 27 paired | `experiments/p6_e2v2/` |
| Phase 7 (JSON parser) | 105 | `experiments/p7_parser/reviews/` |
| Phase 8 (3 hand-written domains) | 224 | `experiments/p8_multidomain/` |
| Phase 9 (3 stdlib × 7 roles) | 630 | `experiments/p9_real/<dom>/reviews/` |
| Phase 9 cross-family on csv | 60 | `experiments/p9_real/csv_dom/reviews_<fam>/` |
| Phase 10 (3 third-party × 3 fam × 2 cond × 30 bugs) | 540 | `experiments/p10_thirdparty/<dom>/reviews/` |
| Phase 11 provenance (csv↔chardet relabel) | 120 | `experiments/p11_provenance/reviews/` |
| Phase 11 replication (Amendment A1) | 226 main + 60 drift | `experiments/p11_replication/reviews/`, `.../drift_diagnostic/` |
| Phase 12 naturalistic (3 fam × 8 bugs × {cold,mm,probe}) | 72 | `experiments/naturalistic_csv/reviews/` |

## 8. How to reproduce end-to-end

```bash
# 1. Sanity check: re-validate all current numerical claims
./docs/paper/validations/validate_all.sh

# 2. (Optional) regenerate every analyzer output from raw reviews
RERUN=1 ./docs/paper/validations/validate_all.sh

# 3. Recompile the manuscript
cd docs/paper/paper-latex && make
```

To recompute reviewer outputs from scratch, the launcher scripts inside each
phase directory (`launch_p11_replication.sh`, `launch_cold.sh`,
`launch_mismatched.sh`, `launch_probe.sh`, etc.) issue paired API calls via
the same Codex/Opus/Gemini CLI binaries used at runtime. Each launcher is
resume-safe and re-issues only missing outputs.

## 9. Drift policy

The v1.4 acceptance criterion is that **no numerical claim drifts from v1.3.2
except those introduced by Streams B (mixed-effects new numbers), C (n=53/60
Phase-11 replication), and D (n=8 naturalistic)**. The validator
(`validate_all.sh`) encodes this contract as 32 explicit assertions. Any
future change that fails this contract must be accompanied by an updated
manuscript text and an updated validator (RED-GREEN: change the validator
first, watch it fail against the old paper, update the paper, watch it pass).
