# P6.1 Pre-registration (FROZEN before run)

**Date frozen**: 2026-05-10
**Hypothesis**: P2 (asymmetric multi-role review) transfers to non-finance code when the cold reviewer receives domain-aligned contracts.

## Protocol

1. Auto-extract contracts from `experiments/p5_e2/ref/bankcheck.py` using a single Codex extraction call (no bug-specific guidance). Save to `p6_e2v2/contracts/bankcheck_contracts.md`.
2. Run cold reviewer with `bankcheck_contracts.md` (substituted into the cold prompt) on all 27 bugs B01-B30 (less the 3 not injected).
3. Re-run warm and skeptic Codex reviewers (no change from E2; included to allow asymm-multi reconstruction).
4. Re-use simm1/simm2/simm3/claudeg from E2 (no model change, prompt unchanged).
5. Aggregate identically to E2 with cap5_validate logic; primary test: McNemar paired one-sided.

## Pre-registered primary metric

**P0 metric**: `q(asymm-multi) < q(symm-mono)` paired McNemar p < 0.05 (uncorrected) on n_paired ≥ 20.

**Secondary metric**: cold reviewer detection rate > 50% (Phase 5 baseline 11%).

## Frozen rules (no post-hoc changes)

- Contracts are extracted from REF only, never from bugged code or failure data.
- Pipeline is frozen: same 27 bugs, same prompts (only `cold` is updated with new contracts).
- All raw outputs reported, including bugs missed.
- No iteration: if P6.1 fails, we report it as-is and proceed to P6.4.

## Risk acknowledgement

Even if P6.1 succeeds, the claim is restricted to: *"P2 transfers when cold reviewer receives domain-aligned contracts"*. We do NOT claim general domain transferability without P6.4.
