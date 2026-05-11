# Paper v1.4 Plan (planner output, frozen 2026-05-11)

## Inputs
- Frozen v1.3.2 manuscript at `docs/paper/v1.0_latex/main.tex` (28 pages, 513 KB PDF)
- Raw experimental artefacts: `experiments/p{1..11}_*/`, `experiments/p5_e3v2/`, `experiments/p9_real/`, `experiments/p10_thirdparty/`, `experiments/p11_provenance/`
- Validation scripts: `experiments/cluster_robust.py`, `cluster_robust_c1.py`, per-phase `analyze_*.py`
- v1.3 → v1.4 protocol document

## Path adjustment
The protocol references `docs/paper/main.tex`; actual path is `docs/paper/v1.0_latex/main.tex`. All streams operate against that path. v1.4 work continues in the same directory; integrator may rename to `docs/paper/v1.4_latex/` at the end if preferred.

## DAG

```
[planner: this doc]
        │
        ▼
[pre-registrations: streams C, D] (BEFORE first reviewer call)
        │
        ├──► [A: writer]         ◄── zero cost, 6 commits, page reduction +1
        ├──► [B: statistician]   ◄── zero cost, mixed-effects on existing data
        │           │
        │ HALT GATE (user GO for $420 API spend)
        │           │
        ├──► [C: P11 replication, n=100] ◄── 600 Codex calls, ~$180, ~4-6h
        └──► [D: naturalistic csv.py]    ◄── 540 calls (3 fam × 30 × 2 × 3) ~$240, ~16-24h harvest
                    │
                    ▼
              [E: integrator]
                    │
                    ▼
       v1.4 manuscript + arXiv tarball + EMSE package
```

## Per-stream DONE criteria

### Stream A (writer, branch `v1.4/writer`)
- 6 sequential commits per protocol (CMDP→tech report; Lemma 2→Eq 17; abstract reframe; title reframe; §8 Wohlin restructure; peer-review trail trim+table).
- `latexmk -pdf` zero-warning.
- Page count ≤ 27.
- `validate_all.sh` exits 0.
- Codex ACCEPT on each of the 6 interventions (sequential, not batched).

### Stream B (statistician, branch `v1.4/statistician`)
- Bug-level long-format CSV exported.
- Mixed-effects logistic model fit (statsmodels MixedLM) on P9+P9-cross-family+P10+P11 = 18 cells.
- `results.json` with point estimates + 95% Wald CIs + LRT p-values.
- Side-by-side table (McNemar vs permutation vs mixed-effects per cell).
- Discrepancies documented if any.
- §A.5 rewrite (mixed-effects primary, permutation comparator, McNemar legacy).
- §7.x cross-phase pooled rewrite.
- Codex ACCEPT before §A.5 commit.

### Stream C (exp-p11-rep, branch `v1.4/exp-p11-rep`)
- `docs/paper/v1.4/preregistration-p11-replication.md` committed BEFORE first reviewer call.
- 600 paired Codex calls completed (≥95% parse rate).
- New 70 bugs per side via frozen-seed AST mutator on same modules, same operator-mix.
- `experiments/p11_replication/results.json` + `analyze.py`.
- §7.9 rewrite with v1.3 n=30 vs v1.4 n=100 table.
- Codex ACCEPT before §7.9 rewrite.

### Stream D (exp-extend, branch `v1.4/exp-extend`, variant=NATURALISTIC)
- Pre-registration with variant field committed BEFORE first reviewer call.
- 25-30 naturalistic CPython csv.py bugs harvested from issue tracker, single-function-scoped, ≤30 LOC diff.
- Reversal patches committed under `experiments/naturalistic_csv/bugs/*.patch`.
- 3 families × 25-30 bugs × 2 conditions = 150-180 paired calls.
- Primary H1: cold > cold_mismatched (cluster-robust paired permutation p < 0.025 per family).
- Out-of-band probe asks reviewer to identify CPython issue number (no-leakage check).
- §7.x integration: "Phase 12: Naturalistic bug benchmark on csv.py".
- Codex ACCEPT before §7.x.

### Stream E (integrator, branch `v1.4/integration`)
- Pre-conditions: A, B, C, D all DONE; all Codex reviews resolved.
- Merge order: writer → statistician → exp-p11-rep → exp-extend.
- `validate_all.sh` exits 0 on integrated manuscript.
- Page count ≤ 27, hard limit 30.
- `latexmk -pdf` zero-warning.
- `docs/paper/v1.4/reproducibility-statement.md` complete.
- Tag `paper-v1.4`.
- `make arxiv-package`.
- `docs/paper/v1.4/emse-submission/` populated.
- Final Codex ACCEPT on integrated manuscript.

## Risk register

| Risk | Mitigation |
|---|---|
| Stream C P11 replication reverses v1.3 conclusion | Protocol halt #6: re-read §1, §7.9, §8 before integration. Empirically informative either way. |
| Stream D naturalistic bugs floor effect (low detection on all conditions) | Protocol halt #7: report floor, defer to v1.5. |
| Mixed-effects fails to converge | Fallback to no module-level random effect; document; no further changes. |
| Codex peer-review issues REJECT | Protocol halt #5: orchestrator adjudicates. |
| Budget overshoot | Hard ceiling $800; orchestrator halts. |
| API rate limits (Gemini quota seen in P11) | Use batched calls with retry/backoff; report drift. |
| Cross-worktree contamination | Forbidden by protocol; agents only read via `git show`. |

## Per-stream API budget

See `budget.md`. Total estimated $500, hard ceiling $800.

## Acceptance for the planner stream itself
- This file committed.
- `coordination.md` initialized.
- `budget.md` committed.
- Pre-registrations for C and D drafted in separate commits before any LLM call from those streams.
