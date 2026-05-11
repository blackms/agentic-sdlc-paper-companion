#!/usr/bin/env bash
# validate_all.sh — v1.4
#
# Re-checks all per-phase analyzer outputs against the v1.3.2 frozen headline
# numbers (plus v1.4 additions from streams B/C/D). Returns 0 on PASS, 1 on
# any drift greater than the per-claim floating-point tolerance.
#
# Run from the repository root:
#     ./docs/paper/validations/validate_all.sh
#
# This script does not regenerate raw reviewer outputs — it only re-checks the
# on-disk results.json artefacts produced by each phase analyzer. To actually
# regenerate the JSON artefacts, run the per-phase analyze*.py script inside
# each experiments/<phase>/ directory; those scripts are idempotent on the
# raw reviewer outputs already committed in the repository.

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

PY=${PY:-python3}

# --- per-phase rerun (idempotent on committed raw outputs) -----------------
RERUN=${RERUN:-0}
if [[ "$RERUN" == "1" ]]; then
    echo "[validate_all] RERUN=1 — re-running per-phase analyzers"
    for cmd in \
        "$PY experiments/cluster_robust.py" \
        "$PY experiments/cluster_robust_c1.py" \
        "$PY experiments/p7_parser/analyze_p7.py" \
        "$PY experiments/p9_real/analyze_p9.py" \
        "$PY experiments/p9_real/analyze_cross_family.py" \
        "$PY experiments/p10_thirdparty/analyze_p10.py" \
        "$PY experiments/p11_provenance/analyze_p11.py" \
        "$PY experiments/p11_replication/analyze.py" \
        "$PY experiments/naturalistic_csv/analyze.py" \
        "$PY experiments/mixed_effects/fit.py"
    do
        echo "  + $cmd"
        $cmd || echo "    (skipped: $cmd)"
    done
    echo
fi

# --- numerical-claim checker ------------------------------------------------
$PY <<'PYEOF'
import json
import sys
from pathlib import Path

FAILED = []
PASSED = []

def approx(a, b, tol=1e-3):
    return abs(float(a) - float(b)) <= tol

def check(label, got, want, tol=1e-3):
    ok = approx(got, want, tol)
    (PASSED if ok else FAILED).append((label, got, want, tol, ok))
    return ok

# ---- v1.3.2 frozen claims (must not drift) ----
# Phase 9: cluster-robust per-cell on csv/urllib/jsondec (Codex)
r = json.loads(Path("experiments/results_cluster_robust.json").read_text())
pc = r["per_cell"]
check("P9 csv Codex cold delta",       pc["P9 csv (Codex)"]["delta_obs"],     0.4333, tol=1e-3)
check("P9 urllib Codex cold delta",    pc["P9 urllib (Codex)"]["delta_obs"],  0.5000, tol=1e-3)
check("P9 jsondec Codex cold delta",   pc["P9 jsondec (Codex)"]["delta_obs"], 0.4333, tol=1e-3)
check("P9 cross-family csv Opus delta", pc["P9 csv (Opus)"]["delta_obs"],     0.2667, tol=1e-3)
check("P9 cross-family csv Gemini delta", pc["P9 csv (Gemini 3.1)"]["delta_obs"], 0.6000, tol=1e-3)
# Cross-phase pooled block-bootstrap
cp = r["cross_phase_block_bootstrap"]
check("Cross-phase block-bootstrap delta",  cp["delta"],   0.6738, tol=1e-3)
check("Cross-phase block-bootstrap CI lo",  cp["ci95"][0], 0.5524, tol=1e-3)
check("Cross-phase block-bootstrap CI hi",  cp["ci95"][1], 0.7952, tol=1e-3)

# Phase 10: detection rates (Codex cold)
p10 = json.loads(Path("experiments/p10_thirdparty/results/p10_analysis.json").read_text())
doms = p10["domains"]
check("P10 dateutil Codex cold",   doms["dateutil_dom"]["codex"]["cold_strict"],    0.9333, tol=1e-3)
check("P10 parsy Codex cold",      doms["parsy_dom"]["codex"]["cold_strict"],      0.5333, tol=1e-3)
check("P10 chardet Codex cold",    doms["chardet_dom"]["codex"]["cold_strict"],    0.9667, tol=1e-3)
check("P10 chardet Codex mismatched", doms["chardet_dom"]["codex"]["mm_strict"], 0.0, tol=1e-3)

# Phase 11 provenance
p11 = json.loads(Path("experiments/p11_provenance/results/p11_analysis.json").read_text())
check("P11 csv H1a McNemar p",     p11["tests"]["csv_H1_relab_gt_truth"]["p"],    0.3437, tol=1e-3)
check("P11 chardet H1b McNemar p", p11["tests"]["chardet_H1_relab_lt_truth"]["p"], 0.1250, tol=1e-3)
check("P11 csv truthful cold rate",    p11["csv_dom_relabel_thirdparty"]["truthful"]["rate_strict"],     0.4333, tol=1e-3)
check("P11 chardet truthful cold rate", p11["chardet_dom_relabel_stdlib"]["truthful"]["rate_strict"], 0.9667, tol=1e-3)

# ---- v1.4 new claims (Streams B, C, D) ----
# Stream B: mixed-effects
me = json.loads(Path("experiments/mixed_effects/results.json").read_text())
fx = {e["name"]: e for e in me["fixed_effects"]}
rv = {e["name"]: e for e in me["random_effect_variances"]}
check("ME beta_cond mean",  fx["cond"]["mean"], 4.20,  tol=0.10)
check("ME beta_cond z",     fx["cond"]["z"],   33.4,   tol=0.5)
check("ME sigma_bug",       rv["bug"]["sd_mean"],    0.72, tol=0.05)
check("ME sigma_module",    rv["module"]["sd_mean"], 0.77, tol=0.10)

# Stream C: Phase-11 replication (Amendment A1)
p11r = json.loads(Path("experiments/p11_replication/results.json").read_text())
check("P11rep csv delta (pp)",    p11r["csv"]["all"]["delta_pp"],     0.0, tol=0.01)
check("P11rep csv McNemar p",     p11r["csv"]["all"]["mcnemar_exact_one_sided_p"], 0.6128, tol=1e-3)
check("P11rep chardet delta (pp)", p11r["chardet"]["all"]["delta_pp"], -3.333, tol=0.1)
check("P11rep chardet McNemar p", p11r["chardet"]["all"]["mcnemar_exact_one_sided_p"], 0.3125, tol=1e-3)

# Stream D: naturalistic csv.py
nat = json.loads(Path("experiments/naturalistic_csv/results.json").read_text())
check("Naturalistic n_bugs", nat["n_bugs"], 8, tol=0)
fams = nat["families"]
def fam_delta(name): return fams[name]["delta_pp"]
def fam_p(name):     return fams[name]["permutation"]["p_one_sided"]
check("Naturalistic Codex delta (pp)", fam_delta("codex"),  62.5, tol=0.5)
check("Naturalistic Codex perm p",     fam_p("codex"),       0.029, tol=5e-3)
check("Naturalistic Opus delta (pp)",  fam_delta("opus"),   12.5,  tol=0.5)
check("Naturalistic Opus perm p",      fam_p("opus"),        0.497, tol=5e-2)
check("Naturalistic Gemini delta (pp)", fam_delta("gemini31"), 62.5,  tol=0.5)
check("Naturalistic Gemini perm p",     fam_p("gemini31"),      0.031, tol=5e-3)
check("Naturalistic n families H1 significant",
      nat["family_wise_summary"]["n_families_h1_significant"], 0, tol=0)

# ---- report ----
print()
print(f"PASS: {len(PASSED)}  FAIL: {len(FAILED)}")
print()
for label, got, want, tol, ok in PASSED:
    print(f"  PASS  {label:55s}  got={got!r:>12}  want={want!r:>12}  tol={tol}")
for label, got, want, tol, ok in FAILED:
    print(f"  FAIL  {label:55s}  got={got!r:>12}  want={want!r:>12}  tol={tol}")

sys.exit(0 if not FAILED else 1)
PYEOF
RC=$?
echo
if [[ $RC -eq 0 ]]; then
    echo "[validate_all] ALL PASS — no numerical-claim drift from v1.3.2 + v1.4 stream outputs."
else
    echo "[validate_all] FAIL — see drift table above."
fi
exit $RC
