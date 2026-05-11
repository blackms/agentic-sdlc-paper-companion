# Naturalistic csv.py — Spend Log

Per-call cost estimate (cf. budget.md):
- Codex (gpt-5.5 via ChatGPT subscription): nominal $0.30-0.50/call.
- Claude Opus 4.7 via `claude -p`: ~$0.30-0.40/call at typical csv prompt size.
- Gemini 3.1 Pro Preview via `gemini`: ~$0.05-0.10/call (much cheaper).

Average across the 3 families: ~$0.30/call.

## Plan

| Phase | Calls | Est cost |
|---|---|---|
| cold (3 fam × 8 bugs) | 24 | ~$7.20 |
| mismatched (3 fam × 8 bugs) | 24 | ~$7.20 |
| probe (3 fam × 8 bugs) | 24 | ~$7.20 |
| Retries (~25% overhead) | ~18 | ~$5.40 |
| **Total** | ~90 | **~$27** |

Well under the $240 budget envelope. Reason: harvest yielded n=8 instead of
target 25-30, dramatically reducing the call count.

## Actuals

| Batch | Date | Calls | Notes |
|---|---|---|---|
| cold v1 (invalidated by bug-injection bug) | 2026-05-11 18:48 | ~18 | ~$5 wasted; bugged files were byte-identical to ref due to `git apply` silently skipping inside worktree |
| cold v2 (correct) | 2026-05-11 19:01--19:14 | 24 + ~5 retries | ~$8 |
| mismatched | 2026-05-11 19:14--19:17 | 24 | ~$7 |
| probe | 2026-05-11 19:17--19:32 | 24 + ~8 retries (opus 'NO' completeness mismatch + gemini 429 + worker exit) | ~$3 (probe responses are short) |
| **TOTAL** | | ~$23 actual | well below $240 budget |

## Rate-limit / auth events

- 2026-05-11 18:45-18:51: Initial CHUNK=6 fan-out caused
  Codex `Auth(TokenRefreshFailed)` races. 2 of 8 codex outputs
  truncated to prompt-echo only with the auth error appended.
  Mitigation: refactor to serial-per-family (one worker per family,
  serial bugs within family). Re-running. No additional spend.

- Empty Opus output observed (opus_B08.raw.txt = 0 bytes) on first
  pass; will retry on a second pass after cold batch completes.

- Gemini sometimes returns only the "Ripgrep is not available."
  fallback line with no model response; will retry.

- Probe phase encountered Gemini 3.1 Pro Preview rate-limit
  exhaustion (HTTP 429 `MODEL_CAPACITY_EXHAUSTED`) on B01--B02 and
  intermittent "Tool execution denied by policy" errors under
  `--approval-mode plan` (the gemini CLI tried to invoke shell
  tools on prompts containing `#`-prefixed comments). Mitigated by
  re-running the gemini probe family after stale processes were
  reaped; all 8 gemini probes eventually returned (1 cite, 7 no-cite
  or empty errors treated as no-cite by the analyzer).
