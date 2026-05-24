# Reproducibility Statement — v1.4 (peer-review companion)

This document enumerates every artefact required to recompute the
numerical claims in Rocchi 2026 v1.4.3 from scratch, in the layout
of **this companion repository**. The original development repository
contained the same artefacts under slightly different paths plus the
proprietary protocol library; this companion is the slice that
peer reviewers need.

## 1. Repository layout

| Class | Path |
|---|---|
| Manuscript LaTeX | `docs/paper/paper-latex/main.tex` (entry point) + included `.tex` files |
| Compiled PDF | `docs/paper/paper-latex/rocchi-2026-measuring-llm-agents.pdf` |
| Pre-registrations | `docs/paper/preregistrations/*.md` + per-phase `experiments/<phase>/PREREGISTRATION.md` |
| Phase reports | `docs/paper/phase-reports/PHASE*.md` |
| CMDP extension tech report | `docs/paper/tech-reports/cmdp-extension.md` |
| Framework excerpts (Sec. D objects named in the paper) | `framework-excerpts/*.md` |
| Per-phase raw artefacts (redacted) | `experiments/<phase>/` |
| Per-phase analyzers | `experiments/<phase>/analyze*.py` |
| Cross-phase analyzers | `experiments/cluster_robust.py`, `experiments/cluster_robust_c1.py` |
| Mixed-effects fit | `experiments/mixed_effects/fit.py` |
| Validation runner | `docs/paper/validations/validate_all.sh` |
| Redaction tool | `tools/redact_reviews.py` |

## 2. Pre-registrations (frozen BEFORE first reviewer call per phase)

Phase pre-registrations live inside each experiment directory as
`PREREGISTRATION.md` (Phases 6, 7, 8, 9, 10, 11 provenance, and 5-E3v2).
The v1.4 streams (C and D) place their pre-registrations under
`docs/paper/preregistrations/`:

| Phase | Path |
|---|---|
| Phase 5-E3v2 (C-T3 concrete injection) | `experiments/p5_e3v2/PREREGISTRATION.md` |
| Phase 6 (auto-extracted contracts) | `experiments/p6_e2v2/PREREGISTRATION.md` |
| Phase 7 (JSON parser) | `experiments/p7_parser/PREREGISTRATION.md` |
| Phase 8 (multi-domain) | `experiments/p8_multidomain/PREREGISTRATION.md` |
| Phase 9 (real stdlib) | `experiments/p9_real/PREREGISTRATION.md` |
| Phase 10 (third-party) | `experiments/p10_thirdparty/PREREGISTRATION.md` |
| Phase 11 provenance | `experiments/p11_provenance/PREREGISTRATION.md` |
| Phase 11 replication (Stream C, parent) | `docs/paper/preregistrations/phase11-replication.md` |
| Phase 11 replication, Amendment A1 (saturation) | `docs/paper/preregistrations/phase11-replication-amendment-A1.md` |
| Phase 12 naturalistic (Stream D) | `docs/paper/preregistrations/phase12-naturalistic.md` |

Phase reports (post-hoc) are under `docs/paper/phase-reports/`.

## 3. Reviewer prompt fingerprints

The following SHA-256 hashes pin the exact byte contents of the prompts
used throughout the experiments. Re-running with these hashes
guarantees byte-identical reviewer input.

```
78c30abf1f1df2cf4207193437c7cc68186b4dc175af37122fecbff2f0cd1e27  experiments/prompts/P_compound_interest.txt
e925a65ad0f0e80f18a231971420beac362eb008c2e9b4e126c4231ad5ca2765  experiments/prompts/P_transfer.txt
f2f7be15c684f05902c5ec7fae76e23e199ca1ad29d421a862749398450e7948  experiments/prompts/P0_compound_interest.txt
78af00e806fc50b7e21c8b32f9e5be5bc22f573bcca6969915030873364866f4  experiments/prompts/P0_transfer.txt
```

## 4. Contract fingerprints (per phase)

The Phase-9 stdlib contracts in the companion repository have the same
SHA-256 as the source repository (the paper's reproducibility statement):

```
fa28fb23b50fa6e7a083e796ee592be97d60de885c97a0645c58ba7c0769b32d  experiments/p9_real/csv_dom/contracts/contracts.md
a9630d2cdec6efcbf95bea9298005334b158cbf03e8a015405b21e368717d9dd  experiments/p9_real/urllib_dom/contracts/contracts.md
c9d7277ec34f1a83e11764c232cbe288d88ec45f826e8fa8524c9064022db8b8  experiments/p9_real/jsondec_dom/contracts/contracts.md
```

The Phase-10 third-party contracts have been **trimmed** for the
companion: in the source repository each `.md` file is a raw capture
of a Codex CLI session (the contract-extractor session) that includes
the OpenAI Codex CLI banner and absolute filesystem paths under
`/Users/alessiorocchi/`. For the public companion we strip the 16
lines preceding the first `# Contracts:` heading so no developer-
machine paths leak. The contract body — what the cold reviewer
actually sees at run time — is byte-identical to the original.

Source-repository hashes (banner included):
```
70228fa4cc6309928a5434de16788cf18354a6c31e5dc221fd16017d60db3105  experiments/p10_thirdparty/chardet_dom/contracts/contracts.md (original)
5e21c98ff1a9d29b8dbe38a9947f22ca05d48059bfa2e0ca14fe8e13d5fe17ea  experiments/p10_thirdparty/dateutil_dom/contracts/contracts.md (original)
598b792417769bb5565ccc34b65e6bae9a6a5c802fc79f5222f623219f96559b  experiments/p10_thirdparty/parsy_dom/contracts/contracts.md (original)
```

Companion-repository hashes (banner stripped):
```
e4416782383009fb0264986c0179913a0c4b54685d6acf645eeb930b83c22abb  experiments/p10_thirdparty/chardet_dom/contracts/contracts.md (companion)
37cb0e44f549b1f60028a5c6ff0a6ee5f67398a28830bb8d115a9765f2fe66d5  experiments/p10_thirdparty/dateutil_dom/contracts/contracts.md (companion)
222b2d54045c32f00dfd3f87653b6fc265db60e1ceaf2e2481a730728be73227  experiments/p10_thirdparty/parsy_dom/contracts/contracts.md (companion)
```

The analyzers do not read `contracts.md` — only the cold reviewer
prompt does, and the cold reviewer outputs are already frozen in
`experiments/p10_thirdparty/*/reviews/*.raw.txt`. Stripping the banner
therefore does not affect `validate_all.sh` numerics: both default
and `RERUN=1` modes pass 32/32 in the companion.

The Phase-11 replication and Phase-12 naturalistic phases each freeze
their own complete reviewer-input set inside the experiment directory:

- `experiments/p11_replication/sha256_freeze.txt`
- `experiments/naturalistic_csv/sha256_freeze.txt`

## 5. How to reproduce

```bash
# 1. Sanity check: re-validate all current numerical claims (≈30s)
./docs/paper/validations/validate_all.sh

# 2. (Optional) regenerate every analyzer output from the redacted raw
#    reviews — same byte-for-byte numbers as step 1 by design.
RERUN=1 ./docs/paper/validations/validate_all.sh

# 3. Recompile the manuscript
cd docs/paper/paper-latex && make
```

Expected output of step 1 (and 2): **`PASS: 32  FAIL: 0`**, exit code 0.
At companion-repo freeze (2026-05-24) both modes produced this result.

To recompute reviewer outputs from scratch (i.e., re-call the LLMs):
this is intentionally outside the scope of the companion repository.
The frozen reviewer outputs in `experiments/**/reviews/*.raw.txt` were
collected against specific Codex/Opus/Gemini snapshots in May 2026 and
contain the role-conditioned prompts plus the reviewer responses. The
companion repository redacts the **prompts** (which contain framework
IP) and keeps the **JSON response blocks** (which are the experimental
data). The raw_sha256 of each original transcript is preserved in the
per-folder `reviews_summary.jsonl` files for audit; reviewers needing
the full original transcripts under NDA can request them from the
corresponding author.

## 6. Raw-output redaction

Every `experiments/**/reviews/*.raw.txt` has been processed by
`tools/redact_reviews.py` (committed in this repo). For each file:

- The reviewer's JSON response (`{bugs_found, verdict}`) is retained
  verbatim, fenced as ` ```json `, preserving the analyzer-visible
  contract.
- The CLI session metadata, the role-conditioned prompt body, the
  embedded contract text, and any free-text prose are dropped.
- A header records `// raw_sha256=...` and `// raw_bytes=...` of the
  original file.
- A per-`reviews/` sidecar `reviews_summary.jsonl` lists, for every
  file: role, family, condition, bug_id, raw_sha256, raw_bytes,
  bugs_found_len, verdict, and an extraction-success flag.

The redactor uses the same JSON-extraction algorithm as the
corresponding analyzer (P9-family for `experiments/p9_real`,
`p10_thirdparty`, `p11_*`, `p7_parser`, `p8_multidomain`, `t2`, `p5_*`,
`p6_e2v2`; naturalistic-family for `experiments/naturalistic_csv`).
This guarantees that re-running an analyzer over the redacted reviews
produces byte-identical results to the frozen baseline that the
manuscript reports.

## 7. Drift policy

The v1.4 acceptance criterion is that no numerical claim drifts from
v1.3.2 except those introduced by Streams B (mixed-effects),
C (Phase-11 replication), and D (Phase-12 naturalistic). The validator
(`validate_all.sh`) encodes this contract as 32 explicit assertions.
At the time of this companion-repo freeze, both `validate_all.sh` and
`RERUN=1 validate_all.sh` pass 32/32.
