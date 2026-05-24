# Framework Excerpts

This directory contains **minimal excerpts** of the five framework components
that the paper measures by name. Each excerpt declares purpose, schema, and
invariants in enough detail to interpret the empirical results, but
deliberately omits the operational steps and anti-pattern guards that
constitute the full protocol bodies.

| File | Paper section | What it documents |
|------|---------------|-------------------|
| `01-calculation-contract.md` | §3, §4, §5, §8.3 | Per-function YAML contract embedded in source; the object both `warm` and `cold` reviewers consume. |
| `02-dual-agent-review.md` | §5, §8.3, §8.4 | The 2-of-3 asymmetric quorum measured in the L1 joint-miss bound. |
| `03-decision-trace.md` | §3, §6, §9 | The immutable per-decision record cited as the audit substrate. |
| `04-banking-profile.md` | §3 | The YAML profile that activates the finance-domain protocols on a target repository. |
| `05-reviewer-roles.md` | §5, §8 | Role definitions and prompt-shape summary for `cold`, `warm`, `skeptic`. |

**What is NOT in these excerpts (and is intentionally outside the public
companion repository):** the operational steps each protocol prescribes, the
anti-pattern tables, the guard-rails, and the prompt bodies that ship with
the framework. The paper's empirical claims are about the *interface* and
*statistical behavior* of these components, which the excerpts cover; they
are not about the full operational protocol library.

Reviewers who need the full protocol bodies to assess the paper can request
them from the corresponding author (contact in `CITATION.cff`) under an NDA
covering only the framework IP.
