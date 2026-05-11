# Pre-flight BLOCKER — Stream C (exp-p11-rep)

**Date**: 2026-05-11 20:30
**Phase**: STEP 1 pre-flight verification
**Status**: HALT — pre-reg n=100 per cell is INFEASIBLE on the frozen reference modules.

## Finding

Pre-registration `preregistration-p11-replication.md` (frozen 2026-05-11 17:00) specifies:

> n = 100 per cell (= 100 truthful + 100 relabeled per side; 200 paired Codex calls per side; **400 total Codex calls**).
> Same 30 P11 bugs reused identically + 70 new AST mutations per side on same modules with same operator-mix proportions.

The frozen `experiments/p9_real/ast_mutator.py` enumerates **all** valid (compiling) PRIORITY-1 single-point mutations from each reference module. Running it on the same modules used in v1.3 yields:

| Module (frozen ref) | Total valid mutations | v1.3 P11 sampled | New available | New by operator |
|---|---|---|---|---|
| `csv_module.py` (csv side, strict validate) | **53** | 30 | **23** | AOR=6, ROR=17, **BOR=0** |
| `chardistribution_module.py` (chardet side, loose compile-only validate per `inject_all.py`) | **60** | 30 (29 unique; one v1.3 location was sampled twice) | **30** (loc-unique 31) | AOR=22, ROR=8, **BOR=0** |

The 70 new mutations per side required by the pre-reg cannot be produced from the frozen modules without:

1. **Changing the reference modules** (e.g., adding another csv stdlib file or another chardet module) — but the pre-reg specifies "same modules"; and changing modules would conflate the test with a difficulty-distribution shift.
2. **Expanding the operator menu** (adding e.g., CRP / UOI / SDL operators from MutPy) — but the pre-reg specifies "AST mutator: `experiments/p9_real/ast_mutator.py` (frozen, sha256 verified)" — same operators.
3. **Relaxing validation** (e.g., dropping the import test) — already loose-validated for chardet via `inject_all.py`; csv would still hit 53 max because the syntactic AOR/ROR/BOR opportunities on `csv_module.py` are exhausted.

Furthermore the **operator-mix-proportion** constraint also fails:

- v1.3 csv was 10/10/10 (1/3 each). The 23 available new csv mutations are 6 AOR + 17 ROR + **0 BOR** — no BOR mutations remain on csv_module.py beyond the 10 v1.3 already used.
- v1.3 chardet was 13/13/4 (43/43/13%). The 30 available new chardet mutations are 22 AOR + 8 ROR + **0 BOR** — no BOR mutations remain on chardistribution_module.py beyond the 4 v1.3 already used.

A stratified top-up that "matches v1.3 operator-mix proportions" therefore **cannot** be constructed at any n > 30 on either side without violating frozen pre-reg constraints.

## Verification commands (reproducible)

```bash
cd .worktrees/exp-p11-rep
python3 - <<'PY'
import sys, json
sys.path.insert(0, 'experiments/p9_real')
import ast_mutator
def loose(src):
    try: compile(src, '<x>', 'exec'); return True
    except Exception: return False
ast_mutator.validate_compiles = loose
from collections import Counter
for label, path in [('csv', 'experiments/p9_real/csv_dom/ref/csv_module.py'),
                    ('chardet', 'experiments/p10_thirdparty/chardet_dom/ref/chardistribution_module.py')]:
    src = open(path).read()
    muts = ast_mutator.enumerate_mutations(src)
    print(label, len(muts), dict(Counter(m['operator'] for m in muts)))
PY
```

## Impact

- 400 paired Codex calls planned ($180 API spend) cannot proceed under the frozen pre-reg.
- Power claim (~0.80 for Δ=10pp at α=0.025) requires n=100 per cell and is therefore unattainable on the frozen modules.
- Drift diagnostic on the 30 reused bugs is still feasible (60 extra calls).

## Options for orchestrator (per "no post-hoc adjustment" discipline, this must be a pre-reg amendment, not a Stream C decision)

A. **Saturation variant**: relax target to "all available mutations per side" — n=53 csv, n=60 chardet (loose). Honest about the constraint. Power for Δ=10pp drops to ~0.55-0.65 per simulation; CI bound only tightens to ~±13-15 pp vs v1.3's ±18 pp. Modest gain over v1.3.

B. **Add a sibling module per side** (e.g., csv stdlib add `_pylib_csv_secondary.py` + chardet `mbcssm_module.py`) — but introduces module-as-confounder. Would need a second pre-reg.

C. **Drop the BOR-proportion constraint** and let new mutations be AOR+ROR only — preserves n=100 if we also raise the strict-validate-csv side via loose-validate (csv loose: still 53, AOR=16, ROR=27, BOR=10; subtract v1.3 10/10/10 → still 6+17 new = 23 max). Does NOT solve csv.

D. **Abort Stream C**, document in §7.9 that v1.3 conclusion stands at n=30 power and that a true high-power replication requires module expansion or operator-menu expansion. Recover $180 budget into Stream D or v1.5.

## Recommendation (from Stream C)

Option **A (saturation)** with a documented operator-mix deviation and revised power calc, OR Option **D (abort)** if the orchestrator wants to preserve pre-reg discipline strictly. Option A is informationally cheap and produces a tighter upper bound on the residual label effect (the explicit Stream C goal); Option D loses zero data but produces no v1.4 information beyond what v1.3 already gave.

Stream C is **PAUSED** until orchestrator decides. No reviewer calls have been issued. No commits to `v1.4/exp-p11-rep` yet beyond this BLOCKER document.

## Audit trail

- Worktree: `.worktrees/exp-p11-rep/`
- Branch: `v1.4/exp-p11-rep`
- Pre-reg cited: `docs/paper/v1.4/preregistration-p11-replication.md` (sha frozen 2026-05-11 17:00)
- Reference modules examined: `experiments/p9_real/csv_dom/ref/csv_module.py`, `experiments/p10_thirdparty/chardet_dom/ref/chardistribution_module.py`
- Mutator: `experiments/p9_real/ast_mutator.py`
- v1.3 manifests: `experiments/p9_real/csv_dom/bugged/manifest.json`, `experiments/p10_thirdparty/chardet_dom/bugged/manifest.json`
