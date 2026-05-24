# BANKING profile — Excerpt

## Purpose

A YAML profile placed at the root of a target repository
(`.banking-profile`) that activates the finance-domain reviewers and
gates referenced by the paper. Without an active profile, the cold and
skeptic reviewers do not run on that repository.

## Schema

```yaml
profile: banking
version: 1.0.0
scope:
  include_paths:
    - <glob, e.g. "src/finance/**/*.py">
    - <glob, e.g. "lib/**/pricing.py">
  exclude_paths:
    - <glob, e.g. "**/tests/**">
  require_contract_on:
    - <glob of functions whose outputs are monetary>
  trigger_dual_agent_review_on:
    - <glob of files where any change requires a 2-of-3 quorum>

reviewers:
  warm:   { family_pool: [opus, sonnet, gemini31, codex] }
  cold:   { family_pool: [codex],   sees: [contract]            }
  skeptic:{ family_pool: [gemini31],sees: [contract, code, intent]}

quorum:
  policy: "2-of-3 asymmetric"
  on_minority_request_changes: ESCALATE

decision_trace:
  enabled: true
  log_path: ".decision-trace/"
gates:
  block_merge_until_quorum: true
  block_merge_on_contract_missing: true
```

## Invariants

1. **Profile presence is required.** A repo without `.banking-profile`
   gets only the project's default reviewers; the finance protocols
   are silent.
2. **Scope is path-based.** Functions outside `include_paths` are not
   subject to contract requirements even if they handle numbers.
3. **Exclusions win.** A path matching both `include_paths` and
   `exclude_paths` is excluded.
4. **Reviewer pools are not the protocol.** The pool is the set of
   model families the role may use; the protocol is the role's
   prompt and what it is allowed to see (`sees:`).
5. **Decision trace is non-optional on `gates.block_merge_until_quorum`.**
   A repo cannot enforce quorum gating without a trace destination.

## Use in the paper

Phases 4, 9, and 10 measure the asymmetric reviewer setup that this
profile activates. The profile itself is not a numerical claim of the
paper; it is the configuration switch under which all the measured
runs were performed.

## What this excerpt does not cover

The framework also defines: profile inheritance (multiple profiles
merging), the protocol-selection guide that translates a profile into
a concrete sequence of protocols at SDLC events, the auto-discovery
heuristics that suggest including a path, the project-board sync
integration, and the autopilot consent flow. None of these affect the
paper's measurements and they are not published here.
