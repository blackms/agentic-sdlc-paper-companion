# Phase 6 Report — Component-Level Domain Transfer Recovered

> **Status**: Phase 6 attempted to recover at least one positive empirical claim from Phase 5's three negative results. P6.1 (E2v2) succeeds at the *component* level — the cold reviewer is domain-transferable when contracts are auto-extracted from a domain-aligned reference — but does not produce aggregate Bonferroni significance for the asymm-multi vs symm-mono primary contrast on bankcheck.py at n=27.

## P6.1 — Cold reviewer domain transfer

### Pre-registration (frozen 2026-05-10)

The protocol was committed in `experiments/p6_e2v2/PREREGISTRATION.md` before any Phase-6 LLM calls were made. Key elements:

- Auto-extract contracts from `experiments/p5_e2/ref/bankcheck.py` via a single Codex extraction call. The extraction prompt explicitly instructs the model to describe *specified behavior* and to ignore bugs/failures.
- Pipeline frozen: same 27 bugs (B01..B30 minus the 3 with non-unique substitution targets). Only `cold` reviewer prompt is updated; warm/skeptic/symm/claudeg are reused unchanged from P5.
- **Primary metric**: paired McNemar one-sided p < 0.05 (uncorrected) on `q(asymm-multi) < q(symm-mono)`, n_paired ≥ 20.
- **Secondary metric**: cold reviewer detection rate > 50% (P5 baseline 11%).
- No iteration: if either metric fails, the result is reported as-is.

### Auto-extracted contracts

A single Codex call on the 597-LOC `bankcheck.py` reference produced `bankcheck_contracts.md` (662 lines, 56 KB). Contracts cover all public functions (`Reporter.*`, `load_yaml_file`, `load_json_file`, `load_profile`, `cmd_*`, etc.) with: signature, preconditions, postconditions, invariants, side-effects.

We checked the contract document for bug-awareness leakage: 3 occurrences of "missing"/"fail"/"wrong", all of them in the legitimate context of describing normal exception conditions (e.g., "Returns `EXIT_FAIL` if any checked function is missing a contract block") — none referencing the planted bugs.

### Per-role detection rate at n = 27

| Role | P5 (finance contracts) | P6.1 (bankcheck contracts) | Δ |
|---|---|---|---|
| warm | 81.48% | 81.48% | 0 (unchanged) |
| **cold** | **11.11%** | **73.08%** | **+62 pp** |
| skeptic | 84.62% | 84.62% | 0 |
| simm1 | 73.08% | 73.08% | 0 |
| simm2 | 84.62% | 84.62% | 0 |
| simm3 | 84.62% | 84.62% | 0 |
| claudeg | 95.83% | 95.83% | 0 |

The cold reviewer's detection rate jumps from 11% to 73%, **passing the pre-registered secondary threshold of 50%**.

### Per-condition q (≥ 2 reviewer miss)

| Condition | P5 (finance contracts) | P6.1 (bankcheck contracts) |
|---|---|---|
| `asymm-codex` | **26.92%** (7/26) | **15.38%** (4/26) |
| `symm-mono` | 15.38% (4/26) | 15.38% (4/26) |
| `symm-multi` | 8.33% (2/24) | 8.33% (2/24) |
| `asymm-multi` | **20.83%** (5/24) | **12.50%** (3/24) |

`asymm-codex` and `asymm-multi` both improve substantially when the cold reviewer is domain-aligned — from 26.92% to 15.38% (asymm-codex) and from 20.83% to 12.50% (asymm-multi).

### Pre-registered primary metric: not significant

Paired McNemar exact one-sided test for `q(asymm-multi) < q(symm-mono)`:

```
n_paired = 24
discordant: b = 1 (asymm-multi misses, symm-mono catches)
            c = 1 (asymm-multi catches, symm-mono misses)
McNemar one-sided p = 0.7500
```

The primary metric **fails**. Discordant pairs `(b=1, c=1)` are perfectly symmetric: there is no aggregate signal of asymm-multi superiority over symm-mono on bankcheck.py at this n.

The same is true for the four other contrasts:

| Contrast | n_paired | b/c | McNemar p | Verdict |
|---|---|---|---|---|
| `asymm-codex < symm-mono` | 26 | 1/1 | 0.7500 | n/s |
| `symm-multi < symm-mono` | 24 | 0/1 | 0.5000 | n/s |
| **`asymm-multi < symm-mono` (PRIMARY)** | 24 | 1/1 | **0.7500** | **n/s** |
| `asymm-multi < asymm-codex` | 24 | 1/1 | 0.7500 | n/s |
| `asymm-multi < symm-multi` | 24 | 1/0 | 1.0000 | n/s |

### Interpretation

**What P6.1 confirms (positive claim)**: the cold reviewer prompt structure is *domain-transferable* when contracts are auto-extracted from a domain-aligned reference. Detection rises from 11% (with finance contracts misaligned with bankcheck) to 73% (with bankcheck contracts) at n = 27. This is a 62-point improvement and validates the cold component of the asymmetric review under explicit domain alignment.

**What P6.1 does not establish (negative)**: aggregate `asymm-multi` superiority over `symm-mono` on bankcheck.py. The primary McNemar test returns symmetric discordant counts (b = 1, c = 1, p = 0.75) — not under-powered, but symmetrically null at the per-bug level. We cannot claim that asymmetric multi-role review (with the cold ri-tooled) outperforms three symmetric replicas of generic Codex on this domain at n = 27.

**Why scaling to n = 80 was not pursued**: with discordant `(b, c) = (1, 1)` at n = 24, the empirical signal is symmetric, not directionally biased. Adding more bugs raises power for *detecting an effect that is biased in some direction*, but it cannot manufacture directional bias from symmetric data. Codex peer review (verbatim): *"Il campione è piccolo, ma l'evidenza primaria è sostanzialmente assente, non solo sotto-potenziata."* We accept this assessment and do not budget Phase-6 LLM credit for scaling that is unlikely to flip the direction.

### Recoverable claim (post peer review)

> **C1 (Component-level transfer)**: The cold contract-first reviewer's detection rate is recoverable under domain shift when contracts are auto-extracted from the new domain's reference (bankcheck: 11% → 73%, n = 27, secondary metric pre-registered at 50%). The aggregate asymm-multi superiority — the full-protocol claim of P2 — remains *inconclusive* on bankcheck under the pre-registered primary endpoint.

This is a strictly weaker claim than P2 in finance, but it is *not nothing*: it identifies the cold reviewer as the structural component that fails under domain shift and recovers under contract realignment.

## P6.4, P6.3, P6.2 — not pursued in this phase

- **P6.4 (multi-domain)**: a parser-domain replication was the recommended path to claim *generality* of C1. Not pursued in this Phase-6 increment because the marginal evidence value depends on whether the field accepts C1 as standalone.
- **P6.3 (Gemini retry)**: not pursued; quota status unchanged.
- **P6.2 (injection alternatives)**: deferred per design (low priority after E3 negative).

These remain Phase-7 work if the field signals that C1 alone is insufficient.

## Updates to the paper

The v0.5 paper should:

1. **Promote C1 to a labelled claim** ("Component-level domain transfer of cold contract-first review") in the abstract, alongside P1, P2, C-T3.
2. **Add §5.x "Phase-6 partial recovery"** documenting the pre-registration, the auto-extraction pipeline, and the primary/secondary metric outcomes.
3. **Update §9.x failure-mode catalogue**: the *out-of-domain prompt collapse* failure mode (introduced in v0.4) is now *paired with a documented recovery mechanism*. The mode itself does not disappear — finance prompts still fail on bankcheck, and ad-hoc reuse without re-tooling will fail — but a concrete recovery is now empirically demonstrated.
4. **No change to P2's domain restriction**: aggregate transfer remains inconclusive; the v0.4 abstract wording stays.

## Files

```
experiments/p6_e2v2/
  PREREGISTRATION.md                   frozen protocol (2026-05-10)
  contracts/bankcheck_contracts.md     auto-extracted, 662 lines, 56 KB
  contracts/bankcheck_contracts_raw.txt  full Codex extraction transcript
  prompts/cold_bankcheck.txt           cold prompt with %CONTRACTS% slot
  reviews/cold_E2_B*.raw.txt           27 cold reviews (pre-registered)
  parse_and_analyze.py                 reproducibility script
  results/e2v2_analysis.json           detection table + per-condition q
```

## Honest summary

Phase 6 recovered **one positive component-level claim** out of three Phase-5 negative results. C1 supports the framing of the paper as a *measurement methodology with explicit boundaries and explicit recoveries* rather than a global theory. The aggregate P2-on-bankcheck claim remains inconclusive and is reported as such. Phase 5's E3 negative on C-T3 is unaffected by Phase 6.
