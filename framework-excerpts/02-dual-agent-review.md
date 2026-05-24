# DUAL-AGENT-REVIEW — Excerpt

## Purpose

Force every functional change touching contract-covered code through an
asymmetric ensemble of independent reviewers, so that error decorrelation
between reviewers lowers the joint-miss probability below what any single
reviewer or any symmetric ensemble can achieve.

This is the protocol whose statistical properties are quantified by claim
**L1** (asymmetric-quorum joint-miss bound) in the paper.

## Reviewer roles

| Role | Sees | Optimizes for |
|------|------|---------------|
| `warm` (stakeholder / business) | The full code change and the surrounding context (issue, PR description, related modules). | Stakeholder intent; "does the change deliver the requested behavior?" |
| `cold` (contract-first) | Only the function's CALCULATION-CONTRACT YAML, plus the changed code. No issue, no PR description, no other context. | Contract conformance; "does the code satisfy every invariant declared in the contract, ignoring intent?" |
| `skeptic` (adversarial) | The full code change, the contract, AND a prompt instructing it to assume the change is wrong until proven otherwise. | Counterexamples; "what input class breaks this code?" |

Each reviewer emits a structured verdict:

```json
{"bugs_found": ["<short description 1>", "<short description 2>", "…"],
 "verdict": "ACCEPT" | "REQUEST_CHANGES"}
```

## Quorum policy (2-of-3 asymmetric)

The change is accepted iff at least two of the three reviewers emit
`ACCEPT`. By design, the three reviewers consume **non-overlapping**
context windows, which empirically reduces mean pairwise error
correlation `ρ̄` from ~0.62 (symmetric three-monoculture) to ~0.29
(this protocol), and the joint-miss probability from 22.91% to 12.28%
on the Phase 4 finance domain (n = 200 bugs × 1,400 reviews,
paired McNemar p = 0.0013).

See paper §5 for the closed-form joint-miss bound, §8.3 (Phase 4) for the
2×2 factorial empirical validation, and §8.4 (Phase 5) for the
cross-domain falsification on `bankcheck.py`.

## Factorial design measured in the paper (§8.3)

| Cell | Composition | Joint-miss q | ρ̄ |
|------|-------------|--------------|------|
| symm-mono | 3 × same family, identical prompt | 0.2291 | 0.62 |
| symm-multi | 3 × different families, identical prompt | 0.1874 | 0.49 |
| asymm-codex | warm/cold/skeptic, all Codex | 0.1655 | 0.37 |
| asymm-multi | warm/cold/skeptic, three families | 0.1228 | 0.29 |

## What this excerpt does not cover

The full protocol additionally specifies: which classes of changes
require which reviewer subset, the gating logic that blocks merge until
quorum is reached, the escalation policy on `REQUEST_CHANGES` minorities,
the exact prompt bodies for each role (these are framework IP), the
operator that selects three reviewers from a configurable family pool,
and the audit trail that DECISION-TRACE writes on every quorum event.
These are not published.
