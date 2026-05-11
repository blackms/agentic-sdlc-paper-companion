# v1.4 Budget Envelope (planner output, frozen)

## Per-stream API cost estimate

| Stream | Calls | Rate (estimate) | Subtotal | Clock-hours |
|---|---|---|---|---|
| A — writer (textual) | 0 | — | $0 | 6-10 |
| B — statistician (existing data) | 0 | — | $0 | 12-20 |
| C — P11 replication (600 Codex calls) | 600 | ~$0.30/call avg | **$180** | 4-6 |
| D — naturalistic csv.py (3 fam × 30 bugs × 2 cond = 180 calls) | 180 (×3 fam interleaved cost varies) | ~$0.40-0.50/call avg | **$240** | 16-24 (harvest is bottleneck) |
| E — integrator | 0 | — | $0 | 4-6 |
| codex-reviewer (transverse) | ~20-30 review calls | ~$3-4/review | **~$80** | embedded |
| **Total estimated** | | | **~$500** | **42-66h** |

## Hard ceiling
**$800** total (160% of estimate). Orchestrator HALTS if cumulative spend exceeds.

## Per-stream rate-limit budget
- Gemini 3.1 Pro Preview quota: ~30 calls/min sustained before throttling (observed in P10/P11). Streams C and D should use CHUNK ≤ 8 for Gemini.
- Codex gpt-5.5: ~15 calls/min sustained, occasional auth refresh blip (handled by retry).
- Claude Opus 4.7 via `claude -p`: serialized by claude CLI; CHUNK ≤ 6 to stay below rate limits.

## Spend tracking
Each stream that issues calls must commit a `spend.md` file in its experiment directory documenting:
- Number of calls per family
- Approximate $ at completion
- Rate-limit events encountered

## Halt protocol
If cumulative spend approaches $700:
1. Pause running batches (TaskStop on Monitor tasks).
2. Compute partial-result viability (can current data answer the H1?).
3. Report to orchestrator with explicit GO request to continue OR DONE-with-partial-results.

## Why not optimize further
This budget is intentionally generous to cover:
- Codex auth-refresh retries (~10% overhead historically)
- Gemini quota-exhaustion retries (~5-15% in P9-P11)
- Codex peer-review rounds (typically 1-2 per intervention but up to 3 if REVISE returns)
