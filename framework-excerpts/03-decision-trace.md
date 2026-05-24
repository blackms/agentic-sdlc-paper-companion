# DECISION-TRACE — Excerpt

## Purpose

Persist an immutable, hash-chained record for every accept/reject
decision the framework makes (calculation contract gate, dual-agent
review quorum, policy escalation), so that any decision can be
reconstructed later from the trace alone without re-reading the source
code at the decision time.

The paper cites DECISION-TRACE as the audit substrate that anchors the
held-out condition `Y_S(τ) ⊥ h_t` in §3 — oracle verdicts can be
verified post-hoc against a frozen trace rather than recomputed against
a possibly-changed history.

## Record schema

Each decision appends one record to a per-repository append-only log:

```yaml
record_id:     <ulid>
parent_id:     <ulid of previous record in this chain, or null at genesis>
ts:            <ISO 8601 UTC, monotonic per chain>
event:         <contract_check | quorum_vote | escalation | override>
actor:         <reviewer id | agent id | human handle>
subject:
  kind:        <function | file | pr | branch | release>
  ref:         <stable reference, e.g. file_sha + line range>
  contract_id: <name@version, if applicable>
verdict:       <ACCEPT | REQUEST_CHANGES | ESCALATE>
inputs_hash:   <sha256 of the canonicalized inputs the actor saw>
rationale:     <short human-readable text>
links:         [ <related record_id>, … ]
prev_chain_hash: <sha256(prev record canonical form)>
this_chain_hash: <sha256(this record canonical form, including prev_chain_hash)>
```

Each `this_chain_hash` is computed over the canonicalized record
including `prev_chain_hash`, so any insertion, reordering, or
modification of an earlier record invalidates every downstream hash.

## Invariants

1. **Append-only.** Records are never edited or deleted; corrections
   append a new record with `event: override` referencing the original.
2. **Total order per chain.** `ts` is monotonic per chain; ties broken
   by `record_id` lexicographic order.
3. **Hash continuity.** For every non-genesis record:
   `prev_chain_hash == sha256_canonical(record[parent_id])`.
4. **No external references in rationale.** The rationale field is
   self-contained text; it must not require fetching another resource
   to interpret. (This is what makes the trace audit-survivable.)
5. **Inputs hash binds the actor's view.** `inputs_hash` covers exactly
   what the actor saw (contract YAML, code excerpt, role-conditioned
   prompt), so two records with the same `inputs_hash` necessarily
   exposed their actor to identical evidence.

## Example record

```yaml
record_id:     01HZRT9P4Q8X8MQ2WJYDE7G2VA
parent_id:     01HZRT9P3K7N2QZ8DE9YPRW2C8
ts:            2026-05-11T17:32:08Z
event:         quorum_vote
actor:         dual-agent-review:asymm-multi
subject:
  kind:        pr
  ref:         agentic-sdlc@9f3a1b2:#247
  contract_id: compute_floor_division_steps@1.0.0
verdict:       ACCEPT
inputs_hash:   3f4b…ab12
rationale:     |
  warm:ACCEPT (1/2 invariants verified), cold:ACCEPT (3/3 invariants
  verified against contract @1.0.0), skeptic:REQUEST_CHANGES (1 counter
  example, not blocking under 2-of-3 policy). Quorum=2 ACCEPT.
links:         [01HZRT9P3K7N2QZ8DE9YPRW2C8]
prev_chain_hash: 7a91…c4dd
this_chain_hash: 8b02…91e7
```

## Use in the paper

- §3 (held-out condition): the existence of the trace is what makes
  `Pred_C` and `Pred_S` post-hoc-verifiable without re-running the
  reviewer ensemble. Pre-registrations and reviewer outputs in the
  companion repository together act as a public-facing DECISION-TRACE
  for the experimental runs themselves.
- §6 (Learning Loop, C-T3): the loop's induction step requires a
  ground-truth signal that the reviewer was wrong; the trace fills the
  role of the immutable evidence pointer.
- §9 (failure modes 1, 2, 5): oracle leakage and conformance-without-
  semantics are operationally detectable only if every accepted
  decision left a verifiable trace.

## What this excerpt does not cover

Implementation specifics — the on-disk format, the storage backend
(SQLite + append-only file, git notes, etc.), the canonicalization
function used for hashing, the GC/retention policy, the integration
into pre-commit and CI hooks, and the tooling that surfaces the chain
to humans — are part of the framework IP and not published.
