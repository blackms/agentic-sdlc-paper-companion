# Amendment A1 to Pre-registration — Phase 11 Replication (Stream C)

**Date frozen**: 2026-05-11 21:00
**Parent**: `preregistration-p11-replication.md` (frozen 2026-05-11 17:00)
**Trigger**: Stream C pre-flight feasibility BLOCKER documented at `.worktrees/exp-p11-rep/experiments/p11_replication/PREFLIGHT-BLOCKER.md` (commit `2fa803f`).

## Reason for amendment

The parent pre-reg specified `n = 100 per cell` and `70 new AST mutations per side with same operator-mix proportions as v1.3`. Pre-flight enumeration on the frozen reference modules established that this is mathematically infeasible:

| Module (frozen ref) | Max valid AST mutations | v1.3 used | New available | Per-operator new |
|---|---|---|---|---|
| `csv_module.py` (strict validate) | 53 | 30 | 23 | AOR=6, ROR=17, **BOR=0** |
| `chardistribution_module.py` (loose compile-validate) | 60 | 30 | 30 | AOR=22, ROR=8, **BOR=0** |

The 70-new-mutations-per-side requirement cannot be satisfied without changing the modules, expanding the operator menu, or violating frozen sha256 hashes. The operator-mix-match (in particular the BOR contribution) is also impossible because BOR is exhausted on both modules at v1.3.

This is an error in the parent pre-reg author's feasibility planning, not a result of post-hoc adjustment after seeing reviewer data. **Zero reviewer calls were issued before this amendment.**

## What the amendment changes

| Field | Parent pre-reg | Amendment A1 |
|---|---|---|
| Sample size | 100 per cell | **saturation**: 53 csv + 60 chardet (= 113 unique bug specs per side × 2 conditions = 226 paired Codex calls per side, total ~452). |
| New-mutation operator-mix | match v1.3 proportions | **drop the proportion-match constraint**: use ALL available new mutations (csv: 6 AOR + 17 ROR + 0 BOR = 23 new; chardet: 22 AOR + 8 ROR + 0 BOR = 30 new). Report observed mix and the resulting per-operator counts. |
| Power claim | 0.80 to detect Δ=10pp at base ~45-50% | **0.55-0.65** at n=53 / n=60 per side, computed via simulation in `power_amendment_A1.py`. Reported honestly. |
| Drift diagnostic | included | unchanged (60 extra calls). |
| Cover stories | byte-identical | unchanged. |
| Prompts | byte-identical | unchanged. |
| Decision rules | unchanged | unchanged (α=0.025 per cell Bonferroni). |
| Validation script | `analyze.py` recomputes | unchanged. |

## What the amendment does NOT change

- H1a/H1b (same direction, same null).
- Primary McNemar exact + secondary cluster-robust permutation + bootstrap CI on Δ.
- Bonferroni α = 0.025 per cell.
- All prompts and contracts byte-identical to v1.3.
- Out-of-band drift diagnostic on the 30 reused bugs.
- All risks 1-4 from parent pre-reg remain.

## Total Codex calls under amendment

- Truthful csv: 53 calls (30 reused = re-run for drift + 23 new)
- Relabeled csv: 53 calls
- Truthful chardet: 60 calls (30 reused for drift + 30 new)
- Relabeled chardet: 60 calls
- **Subtotal: 226 calls.** Plus retry buffer (~30) → ~256 calls. ~$77 budget (vs $180 in parent pre-reg).

**Budget freed: ~$103** — added to Stream D / Stream E buffer (does NOT lift the $800 ceiling).

## Honest framing for §7.9

The v1.4 P11 replication will be reported as: *"saturation replication at the maximum n the frozen modules allow under the v1.3 AST-mutator operator set, with explicit operator-mix deviation documented in `preregistration-p11-replication-amendment-A1.md`. Power for Δ=10pp at α=0.025 is ~0.55-0.65, an improvement over v1.3's ~0.30-0.35 but below the originally planned 0.80. The amendment preserves H1 direction and α; it relaxes only the sample size and the operator-proportion constraint."*

If both H1a and H1b fail to reach α=0.025, the v1.3 conclusion ("anti-stdlib carelessness as the dominant mechanism: not supported") stands at higher power, with the residual undetectable label effect bounded by the observed 95% CIs (expected to be ~±13-15pp vs v1.3's ~±18pp).

## Audit trail

- Stream C BLOCKER doc: `.worktrees/exp-p11-rep/experiments/p11_replication/PREFLIGHT-BLOCKER.md`
- Pre-flight commit on `v1.4/exp-p11-rep`: `2fa803f`
- This amendment committed BEFORE Stream C resumes; zero reviewer calls between BLOCKER and resume.

## Decision

Stream C is GO under Amendment A1. Saturation variant. No further pre-reg changes after this; if Amendment A1 also turns out infeasible during STEP 2, abort.
