# CALCULATION-CONTRACT — Excerpt

## Purpose

Declare a machine-parsable, language-agnostic contract for every function
that produces a number with monetary or financial meaning, so that
correctness, determinism, and explainability can be verified by automation
and by independent reviewers.

A function with a contract is the elementary unit on which the paper's
`cold` reviewer operates: it reads only the contract YAML (not the
implementation) to derive expected behavior, then compares with the code.

## Embedding

The contract is embedded inside the function's documentation block
(docstring, block comment, Javadoc, ...), delimited by sentinel lines so a
parser can extract it without parsing the host language:

```
---contract
... yaml body ...
---
```

## Schema (canonical fields)

```yaml
name: <function name; must match the symbol>
version: <semver of this contract>
inputs:
  - name: <param name>
    type: <decimal | int | bool | string | timestamp | array<…> | object<…>>
    unit: <none | percent | basis_points | shares | contracts | seconds | …>
    currency: <none | ISO 4217 | dynamic>
    domain: <textual or symbolic constraint, e.g. "[0, 1]", "non-negative">
output:
  type:    <as above>
  unit:    <as above>
  currency: <as above>
invariants:
  pre:           [ <precondition>, … ]
  post:          [ <postcondition>, … ]
  conservation: [ <conservation law tying inputs to output, with epsilon if float>, … ]
determinism:
  deterministic: <true | false>
  sources_of_nondeterminism: [ clock | rng | network | fs | set-iteration | … ]
explainability:
  trace_returned:  <true | false>
  trace_fields:    [ <field name>, … ]
  rationale_field: <name of human-readable rationale field, if any>
external_effect: <true | false>
references:
  - <link to spec, paper, regulation, or ADR>
```

## Example

```yaml
---contract
name: compute_floor_division_steps
version: 1.0.0
inputs:
  - name: principal
    type: decimal
    unit: none
    currency: dynamic
    domain: positive
output:
  type: int
  unit: none
invariants:
  pre:  [ "principal > 0", "step_size > 0" ]
  post: [ "result >= 0", "result * step_size <= principal" ]
  conservation:
    - "principal == result * step_size + remainder, with remainder in [0, step_size)"
determinism:
  deterministic: true
external_effect: false
---
```

## Use in the paper

- §3 (Formal Model): each contract instantiates `Pred_C(τ; P)` for one
  function — the verifier kernel `V_C` accepts a trajectory iff every
  invariant in the contract holds for the produced output.
- §8.3 (Phase 4): the warm reviewer sees the contract and the code; the
  cold reviewer sees the contract only. The asymmetric ensemble of §5 is
  built on top of this distinction.
- §8.8 (Phases 9–10): per-domain contracts are auto-extracted from third-
  party module docstrings using the same schema. The contract SHA-256
  hashes recorded in `experiments/p9_real/sha256_freeze.txt` and per-domain
  `contracts/contracts.md` are the audit anchors.

## What this excerpt does not cover

The full protocol additionally prescribes: when to write a contract vs.
when not to, the Given/When/Then specification phase that precedes the
contract, embedding sentinels per language, the TDD cycle that produces a
contract+test pair, the auto-extraction pipeline used in §8.8 to lift
contracts from existing third-party code, the dual-agent review gate that
checks contract↔implementation consistency, and the anti-pattern catalogue.
These are the proprietary parts of the framework and are not published.
