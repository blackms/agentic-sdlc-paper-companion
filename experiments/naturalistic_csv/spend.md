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
| cold (initial) | 2026-05-11 | 24 + retries | ~$8 |
| mismatched | 2026-05-11 | 24 | (pending) |
| probe | 2026-05-11 | 24 | (pending) |

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
