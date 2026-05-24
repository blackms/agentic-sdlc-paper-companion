# Reviewer Roles — Excerpt

The empirical measurements in the paper involve three reviewer roles
operating in different context-restriction regimes. This document
summarizes the role definitions sufficient to interpret the results in
§5, §8.3, §8.4, §8.8, §8.9, §8.10, and §8.11. The full agent
definitions used to instantiate each role at run time (prompt bodies,
self-check chains, tool permissions) are framework IP and not
published.

## warm (stakeholder)

- **Identity.** Behaves as a domain-fluent reviewer who has read the
  issue, the PR description, and the surrounding code.
- **Sees.** The diff, the surrounding module, the linked issue, and
  the CALCULATION-CONTRACT YAML if one is attached.
- **Output.** Same JSON shape as the other roles
  (`{bugs_found, verdict}`); rationale tends to be intent-oriented.
- **Family pool used in the paper.** Phase 4: rotated across Codex,
  Opus, Sonnet, Gemini 2.5 Flash. Phase 9 cross-family: Codex, Opus,
  Gemini 3.1 Pro Preview.

## cold (contract-first)

- **Identity.** Behaves as a formal-methods reviewer with no business
  context; reasons from invariants only.
- **Sees.** **Only the CALCULATION-CONTRACT YAML** and the changed
  code. No issue, no PR description, no surrounding module beyond the
  imports required to parse the code. Has *two phases*: in Phase A,
  derives expected outcomes from the contract alone; in Phase B,
  compares against the code.
- **Output.** Same JSON shape; rationale cites contract clauses by
  name and counterexamples by input class.
- **Family pool used in the paper.** Codex (`gpt-5.5`) across all
  phases as a stable baseline. Phase 9 cross-family adds Opus 4.7 and
  Gemini 3.1 Pro Preview on the `csv` and `jsondec` domains.

## skeptic (adversarial)

- **Identity.** Operates under an explicit "assume the change is
  wrong" prior; success metric is producing a concrete counterexample.
- **Sees.** Diff + contract + intent + surrounding module. Same
  context budget as warm but conditioned on suspicion.
- **Output.** Same JSON shape; rationale typically lists input
  classes rather than line-level findings.
- **Family pool used in the paper.** Same as warm.

## Why context restriction is the load-bearing variable

Phase 4 (§8.3) is a 2×2 factorial that crosses two factors:
{symmetric vs asymmetric context restriction} × {single family vs
multi-family ensemble}. The decisive contrast is the asymmetric
restriction: when the cold reviewer is denied the issue context,
its errors decorrelate from the warm reviewer's errors more than two
warm reviewers (even from different families) do from each other.
This is the mechanism the L1 joint-miss bound makes precise (§5).

## Prompt shape (not the body)

Each role's prompt has the shape:

```
You are a <role-name> reviewer.

You receive:  <context_list_per_role>
You do not receive:  <excluded_list_per_role>

Procedure: <role-specific procedure summary>

Output STRICTLY JSON in one line, no preamble:
{"bugs_found": ["...", "..."], "verdict": "ACCEPT" | "REQUEST_CHANGES"}
```

The contents of `<context_list_per_role>`, the procedure summary,
and the language used (the cold reviewer's procedure is in Italian
in the experiments, because the framework was developed in Italian
and frozen at that point) are the parts that constitute the
framework IP and are intentionally redacted from the raw transcripts
in this companion repository. The transcripts retain only the
reviewer's structured JSON response, which is the experimental datum.
