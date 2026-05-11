# Constrained MDP Construction for Procedurally-Constrained LLM Coding Agents: Technical Report

**Companion technical report to:** *A Measurement Framework for Constrained LLM Coding Agents: An Empirical Study of Conformance, Cost, and Cross-Domain Replication* (Rocchi, 2026; the "main paper").

**Status:** Standalone technical report. Not peer-reviewed as part of the main paper.

**Repository path:** `docs/paper/v1.4/cmdp-extension-techreport.md`

---

## Abstract

This technical report gives the full constrained Markov decision process (CMDP) construction with regime modes, escalation map, and mode-conditioned action sets for a procedurally-constrained LLM coding agent. The construction extends the load-bearing primitives of §3 of the main paper but is **not used** by any empirical result of the main paper; placing it in the main text would lend a sense of rigor without supporting any result (i.e., "math washing"). It is published separately as an interface for future work that needs explicit policy-space dynamics, per-mode cost budgets, or formal interaction with human-in-the-loop verifiers. No empirical claim of the main paper depends on this construction.

---

## 1. State, history, and Markovianity

The state at step *t* is the tuple

```
σ_t = (h_t, α_t, m_t) ∈ Σ,                                  (1)
```

where *α_t* is the artefact-bag accumulator (the multiset of files, test results, and decision-trace records produced up to step *t*) and *m_t ∈ M* is the regime mode (below). Markovianity is constructed by including the full history *h_t* in *σ_t*.

## 2. Regime modes and the policy under escalation

A naïve CMDP becomes incoherent when a verifier triggers an escalation that changes the policy space mid-trajectory. We resolve this by augmenting the state with the regime mode:

```
M = { autonomous, restricted, human-in-loop, terminated }.
```

The verifier outcome vector *v_t* drives mode transitions through the escalation map *Ω(σ_t, v_t) → m_{t+1}*, and the action set itself is mode-conditioned:

```
A_auton = A,    A_restr ⊊ A,    A_HIL = {yield},    A_term = {ε}.    (2)
```

The `yield` and *ε* actions are absorbing.

## 3. Feasibility predicate and environment transition

A **feasibility predicate** *C: Σ × A → {0, 1}* rules out infeasible actions: TDD enforces *C(σ, edit_impl) = 0* whenever no failing test exists in *σ*; the banking profile enforces *C(σ, merge) = 0* whenever the calculation contract is missing.

The environment transition kernel is

```
δ(σ_{t+1} | σ_t, a_t, v_t),    v_t ∈ {acc, rej, esc}^K.       (3)
```

## 4. Why this is not used in the main paper

The empirical claims of the main paper (E1 utility dominance, L1 joint-miss reduction, C-T3 simulation convergence, C1 contract-aligned specificity) are all expressed at the level of *φ(τ)* and *P_B^{P,x}*. They do not require:

- explicit state *σ_t* beyond the history *h_t*;
- mode-conditioned action sets *A_m*;
- escalation map *Ω*;
- per-mode cost budgets.

Future work that wants to derive properties of *V* (the decisional cost-aware metric of the main paper) from the policy-space structure (e.g., optimal mode-conditioned action distributions, per-mode safety guarantees, formal verification of escalation strategies) will need the construction here. The main paper as written makes no claim that requires it; placing the construction in §3 of the main text would be **math washing**, in the sense that the formalism would lend a sense of rigor without supporting any result.

## 5. Intended use as an interface for future work

We expect the construction to be useful for at least the following research programs:

- Deriving optimal mode-conditioned action distributions for a fixed protocol *P*.
- Per-mode safety guarantees under bounded verifier-noise assumptions.
- Formal verification of escalation strategies in regulated domains (banking, medical, aviation).
- Cost-budgeted policy synthesis where total token cost is constrained in expectation across the mode trajectory.

In each case the user should specify the per-mode action sets *A_m*, the escalation map *Ω*, and the feasibility predicate *C* explicitly, and verify that the empirical setting of interest can in fact be expressed through *φ(τ)* and *P_B^{P,x}* of the main paper.

---

## References

The construction here extends and depends only on the load-bearing primitives fixed in §3 of the main paper. For all citations to the LLM-coding-agent, mutation-testing, stochastic-dominance, and CMDP literatures, see the reference list of the main paper (Rocchi, 2026, `docs/paper/v1.0_latex/references.bib`).

- Rocchi, A. (2026). *A Measurement Framework for Constrained LLM Coding Agents: An Empirical Study of Conformance, Cost, and Cross-Domain Replication.* Manuscript v1.4. `docs/paper/v1.0_latex/main.tex` in the companion repository.
