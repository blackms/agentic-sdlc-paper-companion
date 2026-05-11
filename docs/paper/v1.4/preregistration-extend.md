# Pre-registration — Stream D Extension Experiment (FROZEN BEFORE FIRST CALL)

**Date frozen**: 2026-05-11
**Branch**: `v1.4/exp-extend`
**Working dir**: `.worktrees/exp-extend/experiments/naturalistic_csv/`

## Stream-D-variant

**NATURALISTIC** (default per protocol). Non-Python variant deferred to v1.5.

Rationale: addresses the "AST single-mutation may not generalize to naturalistic bugs" critique that has appeared in every Codex peer-review round since Phase 9. Replicating C1 specificity on real-world bugs harvested from CPython issue history is the highest-leverage external-validity test we can run within the v1.4 budget.

## Motivation

v1.3 / v1.4 P9–P11 use AST single-mutation bugs (AOR/ROR/BOR). The Codex peer-review trail repeatedly flags that naturalistic bugs are multi-line, span data-flow patterns, and may have systematically different detection characteristics. Stream D tests whether the C1 specificity finding (cold > cold_mismatched) replicates on bugs harvested from real CPython csv.py issue history.

## Hypotheses (frozen)

- **H1 primary**: per-family cold > cold_mismatched on naturalistic csv.py bugs (specificity replicates beyond AST mutations).
- **H1 secondary**: per-family naturalistic cold detection rate ≤ AST cold detection rate (naturalistic harder, as widely assumed). Directional, one-sided.
- **H0**: no specificity advantage and no naturalistic-harder effect.

## Reviewers

Three families:
- Codex `gpt-5.5`
- Claude Opus 4.7
- Gemini 3.1 Pro Preview

Same cold prompt + same auto-extracted csv.py contracts as P9.

## Metrics

- **Primary**: per-family cluster-robust paired permutation one-sided p-value (cold > cold_mismatched), n_perm = 20,000.
- **Secondary 1**: per-family McNemar exact one-sided (comparator).
- **Secondary 2**: naturalistic vs AST cold-rate per family (paired McNemar across the 30 bugs, treating "AST" and "naturalistic" as paired conditions on the *same module* but different bug *type* — Wilcoxon signed-rank on cold detection rate).

## α threshold

- **0.025 per family** (Bonferroni-corrected for 3 families on primary H1).
- Family-wise α = 0.075 — slightly above Bonferroni 0.05/3 ≈ 0.017 to preserve power; this is a more permissive threshold than v1.3 P10 and is acknowledged as such.

## Sample size & power

- Target: 25-30 naturalistic bugs.
- 3 families × 30 bugs × 2 conditions (cold, cold_mismatched) = **180 paired calls**.
- Plus the out-of-band probe per bug per family ≈ 90 additional Codex/Opus/Gemini calls.
- **Total ~270 calls. Budget ~$240 with retries.**
- Power at n=30 per cell to detect Δ = 30 pp with α = 0.025 paired one-sided: ~0.85.
- If detection rate floors near 0 % across ALL conditions: **protocol halt #7** — report floor, defer to v1.5.

## Inclusion criteria for naturalistic bugs

- Source: CPython issue tracker (https://github.com/python/cpython/issues), search for closed issues tagged `type-bug` with patches touching `Lib/csv.py` since Python 3.6.
- Single-function-scoped fixes only.
- Patch ≤ 30 lines of net change.
- No API change (no signature modification).
- Reversal patch produces a `csv.py` byte-identical to pre-fix state, importable.
- Bug must be observable from `csv.py` alone (no cross-module dependency for the bug surface).

## Exclusion criteria

- Documentation-only fixes.
- Test-only fixes (no production-code change).
- Refactor-only fixes (no behavioral change).
- Performance fixes with no correctness component.
- Multi-function fixes that cannot be split.

## Harvest protocol

1. Query CPython issue tracker via `gh api` for `repo:python/cpython is:issue is:closed label:type-bug` filtered by file path.
2. For each candidate, fetch the merge commit, isolate the diff to `Lib/csv.py`, verify ≤30 LOC + single function.
3. Generate the reversal patch via `git format-patch -R` on the merge commit.
4. Apply the reversal to the v1.3 csv.py reference; verify it compiles.
5. Save under `experiments/naturalistic_csv/bugs/B{NN}.patch` with metadata file `B{NN}.json` containing: issue URL, original patch URL, affected function, brief bug summary, frozen `expected_detection_keywords` for the analyzer.

## Out-of-band probe (no-leakage check)

After each reviewer call, a separate one-shot probe asks: *"Have you seen this exact bug or its fix in the Python CPython issue tracker? If yes, please cite the issue number."* The probe does NOT enter the detection metric. The cite-rate per family is reported as a leakage diagnostic.

## Decision rules

| Outcome | Interpretation |
|---|---|
| 3/3 families: cold > mm, primary p < 0.025 | C1 specificity **replicates on naturalistic bugs** across families. |
| 2/3 families primary significant | **Partial replication**; report family-specific. |
| 1/3 or 0/3 primary significant | C1 specificity is **AST-mutation-bound** (no transfer to naturalistic); reports caveat in §1, §8.4 external validity. |
| Floor effect (all conditions < 10 % detection) | **Protocol halt #7**: report floor, defer to v1.5. |
| Leakage rate > 30 % in any family | Detection metric is contaminated by training-set memorization; report with strong caveat or exclude that family. |

## Risks acknowledged

1. **Multi-function-scoped bugs may be the majority.** Inclusion criterion is restrictive; harvest may yield < 25 candidates. Mitigation: if harvest < 20 after exhaustive search, document and proceed at n=20 with reduced power.
2. **Bug-fix commits may include refactoring.** Use only the minimum-diff bug-introducing change; verify via line-by-line review of the reversal patch.
3. **Reviewer may have seen the CPython issue in training** (high prior probability for popular fixes). Mitigation: out-of-band probe; report cite-rate.
4. **Detection-keyword definition for naturalistic bugs is harder** than for AST mutations (no operator-level keyword). Inclusion: use the function name, the original bug summary, and any cited error/exception type from the fix commit. Frozen at harvest time.
5. **Family-specific harvest cost is identical** — same 25-30 bugs reviewed by all 3 families.

## Validation script

`experiments/naturalistic_csv/analyze.py` — recomputes per-family Δ, CIs, p-values from raw outputs. Frozen at this pre-registration commit.

## Discipline statements

- Pre-registration committed **before any reviewer call**.
- Harvest is completed and frozen (with sha256 of the bug manifest) BEFORE the first reviewer call.
- No prompt changes from P9/P10 cold protocol (sha256 of `cold_bankcheck.txt` and csv.py contracts verified).
- No iteration on prompts, contracts, harvest, or detection criterion after observing results.
- All raw outputs committed.

## After running

- New §7.x in main paper: "Phase 12: Naturalistic bug benchmark on csv.py".
- Per-family Δ table, side-by-side with v1.3 P9 csv-Codex AST-mutation result.
- Leakage rate diagnostic table.
- One paragraph on harvest yield and what fraction of candidates met inclusion criteria.

## Out of scope for Stream D

- Cross-language (TypeScript variant) — deferred to v1.5.
- Other CPython modules — only csv.py for v1.4 (the module with the lowest cold-detection in P9, so the most informative naturalistic comparator).
- Multi-mutation bug chains — deferred to v1.5.
