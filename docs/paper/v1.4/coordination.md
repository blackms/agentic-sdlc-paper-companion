# v1.4 Coordination Log

Append-only. Format: `[YYYY-MM-DD HH:MM] @<from> -> @<to>: <message>`

[2026-05-11 17:00] @orchestrator -> @all: v1.3.2 tagged as `paper-v1.3-frozen`. Worktrees created: writer, statistician, exp-p11-rep, exp-extend, integration. Planner deliverables committed: plan.md, this file, budget.md.

[2026-05-11 17:05] @orchestrator -> @all: streams A (writer) and B (statistician) are GO — zero API cost. Pre-registrations for C (P11 replication, ~$180) and D (naturalistic csv.py, ~$240) must commit BEFORE first reviewer call; orchestrator-level GO required for C+D after pre-reg landing per HALT gate.

[2026-05-11 17:05] @orchestrator -> @writer: GO. 6 sequential interventions per protocol Task A. Branch `v1.4/writer` at `.worktrees/writer/`. Operate on `docs/paper/v1.0_latex/main.tex` (not `docs/paper/main.tex` as the protocol says — paths corrected in plan.md). Each intervention is its own commit, Codex review before integration.

[2026-05-11 17:05] @orchestrator -> @statistician: GO. Branch `v1.4/statistician` at `.worktrees/statistician/`. Bug-level long-format CSV export first, mixed-effects fit second. Tool choice (statsmodels MixedLM vs R lme4) committed in `experiments/mixed_effects/README.md` before fitting.
