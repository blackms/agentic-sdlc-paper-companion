"""Phase 12 — Naturalistic CPython csv.py bug benchmark analyzer.

Per family × per bug × per condition (cold, mismatched):
  - Parse reviewer JSON {bugs_found, verdict} from raw output.
  - Apply keyword detection criterion (frozen at harvest):
    reviewer detects the bug iff any expected_detection_keyword from
    the bug metadata is present (case-insensitive) in the concatenated
    bugs_found list.

Primary H1 per family:
  cluster-robust paired permutation (cold > cold_mismatched), n_perm=20000.

Secondary 1 per family: McNemar exact one-sided (comparator).

Secondary 2 cross-phase (naturalistic vs AST cold-rate on same csv module
per family). Since the bugs differ between AST (P9c_B*) and naturalistic
(B*), the comparison is unpaired: Mann-Whitney U on per-bug cold detection
(0/1 per bug).

Leakage diagnostic: parse the probe output per family × per bug and report
the rate at which the reviewer cites a CPython issue number (gh-NNNNN or
bpo-NNNNN). The probe does NOT enter the detection metric.

Floor-effect halt #7 (pre-reg): if cold + mismatched + probe detection all
< 10% across ALL families, write FLOOR_EFFECT flag and refuse to integrate.

Output:
  results.json             — per-family Δ, CIs, p-values + meta
  leakage_diagnostic.json  — per-family cite-rate and example citations
"""
from __future__ import annotations

import json
import re
import sys
from math import comb, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"
REVIEWS = ROOT / "reviews"
FAMILIES = ["codex", "opus", "gemini31"]
CONDITIONS = ["cold", "mismatched"]


def extract_json(p: Path):
    """Recover a bugs_found list from a raw reviewer output file."""
    if not p.exists() or p.stat().st_size == 0:
        return None
    text = p.read_text(errors="replace")
    cands = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", text, re.DOTALL):
        cands.append(m.group(0))
    last = text.rfind("}")
    first = text.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        cands.append(text[first:last + 1])
    for c in cands:
        try:
            d = json.loads(c.strip())
            if isinstance(d, dict) and "bugs_found" in d:
                bugs = d["bugs_found"]
                if isinstance(bugs, list):
                    return [str(b) for b in bugs]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def detect_naturalistic(bug, found):
    """Frozen detection criterion: any keyword (case-insensitive) hits."""
    if found is None:
        return None
    text_l = " ||| ".join(found).lower()
    for kw in bug["expected_detection_keywords"]:
        if kw.lower() in text_l:
            return True
    return False


def mcnemar_one_sided(b, c):
    """Exact one-sided binomial test on discordants. H1: b > c."""
    n = b + c
    if n == 0:
        return 1.0
    # p = P(B >= b | n) under H0 p=0.5
    return sum(comb(n, k) for k in range(b, n + 1)) / (2 ** n)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [max(0.0, centre - half), min(1.0, centre + half)]


def cluster_perm_test(paired, n_perm=20000, seed=20260511):
    """Paired permutation test on (cold, mm) outcomes. Sign-flip per pair."""
    import random
    rng = random.Random(seed)
    n = len(paired)
    if n == 0:
        return {"n": 0, "delta_obs": 0.0, "p_one": 1.0, "p_two": 1.0,
                "ci95": [0.0, 0.0]}
    deltas = [int(c) - int(m) for c, m in paired]
    delta_obs = sum(deltas) / n
    cnt_two = 0
    cnt_one = 0
    for _ in range(n_perm):
        s = 0
        for d in deltas:
            s += -d if rng.random() < 0.5 else d
        dp = s / n
        if abs(dp) >= abs(delta_obs):
            cnt_two += 1
        if dp >= delta_obs:
            cnt_one += 1
    p_one = (cnt_one + 1) / (n_perm + 1)
    p_two = (cnt_two + 1) / (n_perm + 1)
    # Percentile bootstrap CI on delta
    boots = []
    for _ in range(n_perm):
        sample = [rng.choice(paired) for _ in range(n)]
        s = sum(int(c) - int(m) for c, m in sample) / n
        boots.append(s)
    boots.sort()
    lo = boots[int(0.025 * n_perm)]
    hi = boots[int(0.975 * n_perm)]
    return {"n": n, "delta_obs": delta_obs, "p_one": p_one, "p_two": p_two,
            "ci95": [lo, hi]}


def mann_whitney_u(a, b):
    """Two-sample Mann-Whitney U, one-sided H1: median(a) >= median(b).
    Returns (u, p_normal_approx). For binary data this reduces to a
    comparison of proportions; we use the normal approximation with
    tie correction since n is small.
    """
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return (0.0, 1.0)
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    # Assign average ranks
    ranks = [0.0] * (n1 + n2)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg = (i + j) / 2 + 1  # average rank, 1-indexed
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    sum_a = sum(r for r, (_, g) in zip(ranks, combined) if g == 0)
    u_a = sum_a - n1 * (n1 + 1) / 2
    # One-sided p (a > b): use normal approx (a higher rank sum = lower U for a's competitor)
    mu = n1 * n2 / 2
    # Tie correction
    # Compute sum_t = Σ (t_i^3 - t_i) over tied groups
    tie_corr = 0
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        t = j - i + 1
        tie_corr += t ** 3 - t
        i = j + 1
    sigma2 = n1 * n2 * (n1 + n2 + 1) / 12
    if tie_corr:
        sigma2 -= n1 * n2 * tie_corr / (12 * (n1 + n2) * (n1 + n2 - 1))
    if sigma2 <= 0:
        return (u_a, 1.0)
    z = (u_a - mu) / sqrt(sigma2)
    # One-sided p: P(U_a >= u_a)
    from math import erf
    p = 0.5 * (1 - erf(z / sqrt(2)))
    return (u_a, p)


PROBE_CITE_RE = re.compile(r"(gh-?\d{4,7}|bpo-?\d{4,7}|#\s?\d{4,7})", re.IGNORECASE)


def parse_probe(p: Path):
    """Return (raw_text, cited_issue_or_None) for a probe output."""
    if not p.exists() or p.stat().st_size == 0:
        return (None, None)
    text = p.read_text(errors="replace")
    m = PROBE_CITE_RE.search(text)
    return (text, m.group(0) if m else None)


def main():
    manifest = json.loads(MANIFEST.read_text())
    bugs = manifest["bugs"]
    n_bugs = len(bugs)

    # Per family × condition: list of (bug_id, detected, parsed)
    results = {fam: {cond: [] for cond in CONDITIONS} for fam in FAMILIES}
    parse_failures = {fam: {cond: 0 for cond in CONDITIONS} for fam in FAMILIES}

    for fam in FAMILIES:
        for cond in CONDITIONS:
            for bug in bugs:
                bid = bug["bug_id"]
                p = REVIEWS / cond / f"{fam}_{bid}.raw.txt"
                found = extract_json(p)
                if found is None:
                    detected = None
                    parse_failures[fam][cond] += 1
                else:
                    detected = bool(detect_naturalistic(bug, found))
                results[fam][cond].append({
                    "bug_id": bid,
                    "raw_path": str(p.relative_to(ROOT)),
                    "found": found,
                    "detected": detected,
                })

    # Compute per-family stats
    out = {
        "n_bugs": n_bugs,
        "families": {},
        "manifest_ref": "manifest.json",
        "alpha_per_family": 0.025,
        "n_perm": 20000,
    }

    floor_signals = []  # collect detection-rate-low signals across families

    for fam in FAMILIES:
        cold_outcomes = results[fam]["cold"]
        mm_outcomes = results[fam]["mismatched"]
        paired = []
        for cd, md in zip(cold_outcomes, mm_outcomes):
            assert cd["bug_id"] == md["bug_id"]
            # strict: parse-failure treated as miss
            c = bool(cd["detected"]) if cd["detected"] is not None else False
            m = bool(md["detected"]) if md["detected"] is not None else False
            paired.append((c, m))
        n = len(paired)
        n_cold = sum(c for c, _ in paired)
        n_mm = sum(m for _, m in paired)
        cold_rate = n_cold / n if n else 0.0
        mm_rate = n_mm / n if n else 0.0
        # McNemar discordants
        b = sum(1 for c, m in paired if c and not m)  # cold wins
        c_disc = sum(1 for c, m in paired if not c and m)  # mm wins
        mcn_p = mcnemar_one_sided(b, c_disc)
        perm = cluster_perm_test(paired, n_perm=out["n_perm"], seed=20260511)
        cold_ci = wilson_ci(n_cold, n)
        mm_ci = wilson_ci(n_mm, n)
        family_block = {
            "n_bugs": n,
            "cold": {
                "n_detected": n_cold,
                "rate": cold_rate,
                "wilson_ci95": cold_ci,
                "parse_failures": parse_failures[fam]["cold"],
            },
            "mismatched": {
                "n_detected": n_mm,
                "rate": mm_rate,
                "wilson_ci95": mm_ci,
                "parse_failures": parse_failures[fam]["mismatched"],
            },
            "delta_pp": (cold_rate - mm_rate) * 100,
            "permutation": {
                "delta_obs": perm["delta_obs"],
                "p_one_sided": perm["p_one"],
                "p_two_sided": perm["p_two"],
                "ci95": [v * 100 for v in perm["ci95"]],
                "n_perm": out["n_perm"],
            },
            "mcnemar": {
                "discordant_cold_wins": b,
                "discordant_mm_wins": c_disc,
                "p_one_sided": mcn_p,
            },
            "h1_significant_at_0_025": perm["p_one"] < 0.025,
            "raw_paired": [
                {"bug_id": p_["bug_id"], "cold": c, "mm": m, "cold_parsed": cd_["detected"] is not None, "mm_parsed": md_["detected"] is not None}
                for p_, c, m, cd_, md_ in zip(cold_outcomes, [c for c, _ in paired], [m for _, m in paired], cold_outcomes, mm_outcomes)
            ],
        }
        out["families"][fam] = family_block
        # Floor signal: cold AND mm AND probe all <10%
        if cold_rate < 0.10 and mm_rate < 0.10:
            floor_signals.append(fam)

    # Secondary 2: naturalistic vs AST cold-rate (P9 csv same module)
    # P9c uses Codex cold_codex (or cold for legacy). Detection JSON path:
    p9_detection = (ROOT.parent / "p9_real" / "csv_dom" / "detection.json")
    p9_reviews = (ROOT.parent / "p9_real" / "csv_dom" / "reviews")
    out["naturalistic_vs_ast_csv"] = {}
    if p9_detection.exists():
        # Per family, compute AST cold detection rate on the existing P9 csv outputs.
        # The P9 csv naming is `cold_<BID>.raw.txt` (Codex) and `cold_<fam>_<BID>.raw.txt` for others.
        # Reuse the cluster_robust.detects function via import.
        sys.path.insert(0, str(ROOT.parent))
        from cluster_robust import extract_json as p9_extract, detects as p9_detects
        p9 = json.loads(p9_detection.read_text())
        ast_bugs = p9["bugs"]
        for fam in FAMILIES:
            # cold-role prefix
            if fam == "codex":
                role = "cold"
            elif fam == "opus":
                role = "cold_opus"
            else:
                role = "cold_gemini31"
            ast_outcomes = []
            for bug in ast_bugs:
                bid = bug["bug_id"]
                pth = p9_reviews / f"{role}_{bid}.raw.txt"
                fnd = p9_extract(pth)
                d = p9_detects(bug, fnd) if fnd is not None else None
                ast_outcomes.append(bool(d) if d is not None else False)
            nat_outcomes = [c for c, _ in zip([fb["detected"] for fb in results[fam]["cold"]], range(n_bugs))]
            nat_outcomes = [bool(d) if d is not None else False for d in nat_outcomes]
            # Mann-Whitney U: one-sided H1: AST cold rate >= naturalistic cold rate
            # (pre-reg: naturalistic <= AST)
            u, p_uw = mann_whitney_u(ast_outcomes, nat_outcomes)
            out["naturalistic_vs_ast_csv"][fam] = {
                "n_ast": len(ast_outcomes),
                "n_naturalistic": len(nat_outcomes),
                "ast_cold_rate": sum(ast_outcomes) / len(ast_outcomes) if ast_outcomes else 0.0,
                "naturalistic_cold_rate": sum(nat_outcomes) / len(nat_outcomes) if nat_outcomes else 0.0,
                "delta_ast_minus_naturalistic_pp": (
                    (sum(ast_outcomes) / len(ast_outcomes) if ast_outcomes else 0.0)
                    - (sum(nat_outcomes) / len(nat_outcomes) if nat_outcomes else 0.0)
                ) * 100,
                "mann_whitney_u": u,
                "p_one_sided_ast_geq_natural": p_uw,
            }
    else:
        out["naturalistic_vs_ast_csv"]["note"] = "P9 csv detection.json not found; AST comparison skipped."

    # Probe (leakage) — parse all probe outputs
    probe = {fam: {"n_total": 0, "n_cited": 0, "n_parsed": 0, "citations": {}} for fam in FAMILIES}
    for fam in FAMILIES:
        for bug in bugs:
            bid = bug["bug_id"]
            p = REVIEWS / "probe" / f"{fam}_{bid}.raw.txt"
            text, cite = parse_probe(p)
            probe[fam]["n_total"] += 1
            if text is not None:
                probe[fam]["n_parsed"] += 1
            if cite is not None:
                probe[fam]["n_cited"] += 1
                probe[fam]["citations"][bid] = cite
        probe[fam]["cite_rate"] = probe[fam]["n_cited"] / max(probe[fam]["n_total"], 1)
        probe[fam]["high_leakage_caveat"] = probe[fam]["cite_rate"] > 0.30

    # Floor-effect check: all families both cold AND mm both < 10%
    if len(floor_signals) == len(FAMILIES):
        # also require probe detection low (we use no-cite as low signal)
        all_probe_low = all(probe[fam]["cite_rate"] < 0.10 for fam in FAMILIES)
        if all_probe_low:
            out["FLOOR_EFFECT_HALT"] = {
                "triggered": True,
                "criteria": (
                    "cold_rate < 0.10 AND mismatched_rate < 0.10 AND "
                    "probe cite_rate < 0.10 in ALL families"
                ),
                "action": "Pre-reg halt #7 — refuse integration, defer to v1.5.",
                "families": list(floor_signals),
            }
        else:
            out["FLOOR_EFFECT_HALT"] = {
                "triggered": False,
                "note": "cold+mm < 10% but probe cite-rate not low; not a floor.",
                "families": list(floor_signals),
            }
    else:
        out["FLOOR_EFFECT_HALT"] = {"triggered": False}

    out["family_wise_summary"] = {
        "n_families_h1_significant": sum(1 for fam in FAMILIES if out["families"][fam]["h1_significant_at_0_025"]),
        "interpretation": None,
    }
    n_sig = out["family_wise_summary"]["n_families_h1_significant"]
    if n_sig == 3:
        out["family_wise_summary"]["interpretation"] = "C1 specificity REPLICATES on naturalistic bugs across all 3 families."
    elif n_sig == 2:
        out["family_wise_summary"]["interpretation"] = "Partial replication (2/3 families)."
    elif n_sig == 1:
        out["family_wise_summary"]["interpretation"] = "Weak replication (1/3 families)."
    else:
        out["family_wise_summary"]["interpretation"] = "C1 specificity does NOT replicate on naturalistic bugs (0/3 families)."

    (ROOT / "results.json").write_text(json.dumps(out, indent=2, default=str))
    (ROOT / "leakage_diagnostic.json").write_text(json.dumps(probe, indent=2))
    print("=" * 78)
    print(f"Naturalistic csv.py benchmark — n_bugs={n_bugs}")
    print("=" * 78)
    for fam in FAMILIES:
        fb = out["families"][fam]
        print(f"  {fam:10s}: cold={fb['cold']['rate']*100:5.1f}% mm={fb['mismatched']['rate']*100:5.1f}% Δ={fb['delta_pp']:+5.1f}pp perm_p={fb['permutation']['p_one_sided']:.4f} mcnemar_p={fb['mcnemar']['p_one_sided']:.4f}  sig@0.025={fb['h1_significant_at_0_025']}")
    print(f"\nFamily-wise: {n_sig}/3 — {out['family_wise_summary']['interpretation']}")
    print(f"\nLeakage:")
    for fam in FAMILIES:
        pf = probe[fam]
        print(f"  {fam:10s}: cited={pf['n_cited']}/{pf['n_total']} ({pf['cite_rate']*100:.1f}%)  caveat={pf['high_leakage_caveat']}")
    print(f"\nFloor-effect halt #7: triggered={out['FLOOR_EFFECT_HALT'].get('triggered')}")
    print(f"\nResults written to: {ROOT/'results.json'}")
    print(f"Leakage written to: {ROOT/'leakage_diagnostic.json'}")


if __name__ == "__main__":
    main()
