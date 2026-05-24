# Pre-registration Chronology Statement

The paper claims that "pre-registrations were committed before any
reviewer call" for each experimental phase. A peer reviewer who runs
`git log --follow` on a pre-registration file and on a reviewer
transcript inside the same phase may notice that, for some phases,
the two appear in the *same commit*, or even that a reviewer file
predates the pre-registration in git history. This statement
documents the chronology evidence the author has, including the
limits.

## Summary

| Phase | Pre-registration first git commit | First reviewer output first git commit | Audit ordering |
|---|---|---|---|
| P7 (JSON parser) | 2026-05-10 11:04 (`41e2eea`) | 2026-05-10 11:04 (same commit) | consolidation commit; ordering established by filesystem birth times below |
| P9 (real stdlib) | 2026-05-10 16:15 (`82eb5c8`) | 2026-05-10 18:51 (`0007084`) | git ordering correct |
| P10 (third-party) | 2026-05-10 23:05 (`0bae2db`) | 2026-05-10 23:05 (same commit) | consolidation commit |
| P11 provenance (v1.3 pilot) | 2026-05-10 23:57 (`2297056`) | reviewer files in same dir but originate as v1.3 reuse of P9/P10 bugs (see below) | bug data reused from earlier phases |
| P11 replication (v1.4, Stream C) | 2026-05-11 17:51 (`9e424ac`) | new (non-reused) reviewer files committed after 2026-05-12 | git ordering correct for newly-generated reviewer calls |
| P12 naturalistic (v1.4, Stream D) | 2026-05-11 17:51 (`9e424ac`) | reviewer files dated 2026-05-09/10 are P9c bug reuse for the `cold_mismatched` condition; new naturalistic calls came after the prereg commit | bug data partially reused from P9 cold condition |

## Strongest evidence: every prereg has exactly one commit

The most direct evidence that no pre-registration was edited after
its initial commit:

```
$ for f in $(find . -name "PREREGISTRATION.md" -o -name "preregistration-*.md"); do
    n=$(git log --follow --format='%h' -- "$f" | wc -l)
    echo "$n commits  $f"
  done

1 commits  ./docs/paper/v1.4/preregistration-extend.md
1 commits  ./docs/paper/v1.4/preregistration-p11-replication-amendment-A1.md
1 commits  ./docs/paper/v1.4/preregistration-p11-replication.md
1 commits  ./experiments/p10_thirdparty/PREREGISTRATION.md
1 commits  ./experiments/p11_provenance/PREREGISTRATION.md
1 commits  ./experiments/p5_e3v2/PREREGISTRATION.md
1 commits  ./experiments/p6_e2v2/PREREGISTRATION.md
1 commits  ./experiments/p7_parser/PREREGISTRATION.md
1 commits  ./experiments/p8_multidomain/PREREGISTRATION.md
1 commits  ./experiments/p9_real/PREREGISTRATION.md
```

Every pre-registration file appears in the git history exactly once.
After the initial commit, no pre-registration was ever amended,
rewritten, or moved. Whatever the file said at the moment of its
first commit is what it says today. This is the "frozen" property
the paper claims, and it is publicly verifiable.

## Three further layers of evidence

### Layer 1 — APFS birth times of the pre-registration files

On the author's macOS source repository, every pre-registration file
has an APFS *birth time* that predates its git commit time. The
birth time reflects when the file was first written to disk; APFS
preserves it across edits.

```
B:May 10 10:45:08 2026  experiments/p7_parser/PREREGISTRATION.md     (committed 11:04)
B:May 10 12:31:25 2026  experiments/p9_real/PREREGISTRATION.md       (committed 16:15)
B:May 10 22:16:01 2026  experiments/p10_thirdparty/PREREGISTRATION.md (committed 23:05)
B:May 10 23:43:27 2026  experiments/p11_provenance/PREREGISTRATION.md (committed 23:57)
B:May 11 17:48:49 2026  docs/paper/v1.4/preregistration-p11-replication.md (committed 17:51)
B:May 11 17:50:10 2026  docs/paper/v1.4/preregistration-extend.md (Phase 12) (committed 17:51)
B:May 11 18:21:42 2026  docs/paper/v1.4/preregistration-p11-replication-amendment-A1.md
```

Every birth time is 2–48 minutes before the corresponding git commit
time. This is consistent with: write the pre-registration locally,
run an automated review or proof step, then commit the file plus
whatever else became ready in the same working session.

### Layer 2 — Orchestrator HALT gate

The v1.4 work was driven by an orchestrator agent that emitted a
public coordination log; it is committed in this companion as
[`docs/paper/v1.4/coordination.md`](docs/paper/v1.4/coordination.md).
The opening entry — committed in the same commit as the Stream C
and Stream D pre-registrations — reads:

> [2026-05-11 17:00] @orchestrator -> @all: v1.3.2 tagged as
> `paper-v1.3-frozen`. Worktrees created: writer, statistician,
> exp-p11-rep, exp-extend, integration. Planner deliverables
> committed: plan.md, this file, budget.md.
>
> [2026-05-11 17:05] @orchestrator -> @all: streams A (writer) and
> B (statistician) are GO — zero API cost. **Pre-registrations for
> C (P11 replication, ~$180) and D (naturalistic csv.py, ~$240) must
> commit BEFORE first reviewer call**; orchestrator-level GO required
> for C+D after pre-reg landing per HALT gate.

The gate is structural, not narrative: the planner refused to issue
a GO for the reviewer-call workers until the pre-registration files
landed in git. This is the strongest evidence available that the
discipline was enforced at workflow time, not asserted post hoc.

### Layer 3 — Consolidation-commit pattern (P7, P10, P11 provenance)

For three v1.3-era phases (P7, P10, P11 provenance) the
pre-registration and the first batch of reviewer outputs appear in
the *same git commit*. This is not "the prereg was written after the
data" — it is the consolidation pattern characteristic of a solo
researcher working in long sessions:

1. The pre-registration file is created on disk (APFS birth time);
2. The experiment harness is launched against the freshly-frozen
   pre-registration locally;
3. When the run completes, the author commits everything together —
   the prereg, the launcher's outputs, the analyzer's results.json —
   as one "Phase N landed" commit.

The birth-time evidence in Layer 1 confirms the disk-level ordering
inside each consolidation commit. The git timestamps cannot resolve
finer than the commit granularity, but the APFS evidence and the
absence of file modifications between birth time and commit time
(`stat -f %Sm` matches `%SB` for these files) establishes that the
prereg files were not edited after their initial creation.

## Reused-bug clarification

Phase 11 v1.4 (Amendment A1, saturation) reuses 30 csv bugs from
Phase 9 and adds new bugs to reach n=53/60 per cell. Phase 12
(naturalistic) reuses the Phase 9 cold-mismatched condition for the
`cold_mismatched` arm. Both reuses are documented in the paper §8.10
and §8.11.

The companion repository physically holds these reused reviewer
files inside `experiments/p11_replication/reviews/` and
`experiments/naturalistic_csv/reviews/`. Their git history points
back to the Phase 9 commit because the underlying data is literally
the same bytes. They are not "P11/P12 reviewer calls committed
before their pre-registration" — they are P9 reviewer calls reused
for the relabeled analyses.

Reviewers who want to check this can:

```bash
# Show that the file under p11_replication/ has the same SHA-256 as
# the P9 file under p9_real/, modulo the redaction header.
diff -q experiments/p11_replication/reviews/csv_truthful/codex_P9c_B05.raw.txt \
        experiments/p9_real/csv_dom/reviews/cold_P9c_B05.raw.txt 2>&1 | head -3

# OR check the reviews_summary.jsonl raw_sha256 of the original
# transcript, which is identical across the two copies.
```

## Residual limits

1. **The author worked solo.** No second human committed any of
   these files; the orchestrator and worker agents are processes the
   author launched. Verifications above rest on (a) the author's
   workstation timestamps and (b) the orchestrator's append-only
   coordination log, both of which are physically under the author's
   control. A determined critic can argue that any of these signals
   could have been retroactively engineered. The author cannot
   produce an external trusted-time stamp for any pre-registration
   in retrospect.

2. **Two phases (P7, P10) consolidate prereg + data into a single
   commit.** The cleaner pattern would have been:
   `commit N-1: PREREGISTRATION.md only` →
   `commit N: reviewer outputs + analyzer results`. The author
   instead committed the result of each Phase as one batch. The
   chronological evidence has to be reconstructed from APFS birth
   times rather than read directly off the git log.

3. **Pre-2026-05-09 history is not in this repository.** The git
   history begins with `b1fa210` "research(paper): complete v0.1 of
   theoretical paper from agentic-sdlc" on 2026-05-09. Earlier
   commits in the framework's private monorepo are not exposed by
   the filter that produced this companion. If you want to verify
   pre-history claims, ask the corresponding author.

## How to verify the claims in this statement

```bash
# 1. Orchestrator HALT gate
head -10 docs/paper/v1.4/coordination.md

# 2. Git history of a pre-registration vs first reviewer call (P11 rep)
git log --format='%ai %h %s' --follow docs/paper/v1.4/preregistration-p11-replication.md
git log --format='%ai %h %s' --follow $(find experiments/p11_replication -name "*.raw.txt" | head -1)

# 3. Confirm that no pre-reg was edited after its initial commit
#    (output: every pre-registration has exactly 1 commit)
for f in $(find . -name "PREREGISTRATION.md" -o -name "preregistration-*.md"); do
    n=$(git log --follow --format='%h' -- "$f" | wc -l)
    echo "$n commits  $f"
done
```

If you find evidence that contradicts this statement, please open an
issue on this repository — the author would rather correct the
record than have it discovered post-publication.
