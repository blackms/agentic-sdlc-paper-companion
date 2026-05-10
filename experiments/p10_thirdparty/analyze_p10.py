"""P10 third-party libraries analyzer.

Per domain × per family:
- cold and cold_mismatched detection rate (strict, unparsed-as-miss)
- Wilson 95% CI on cold strict
- Paired McNemar one-sided (cold > cold_mismatched), threshold p < 0.010

Cross-domain meta:
- Codex-only Fisher's combined over P7 + 3 P9 + 3 P10 = 7 tests, threshold p < 0.001
- All-families Fisher's combined over 9 tests (3 P10 × 3 families)

Reviewer-choice sensitivity:
- For each P10 domain, the family spread (max - min) on cold strict
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from math import comb, log, sqrt
from scipy.stats import chi2

ROOT = Path(__file__).parent
DOMAINS = ["dateutil_dom", "parsy_dom", "chardet_dom"]
FAMILIES = ["codex", "opus", "gemini31"]
CONDITIONS = ["cold", "cold_mismatched"]


def extract_json(p):
    if not p.exists() or p.stat().st_size == 0:
        return None
    text = p.read_text()
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


def detects(bug, found):
    if found is None:
        return None
    text = " ||| ".join(b for b in found)
    text_l = text.lower()
    line = bug["line"]
    line_set = {line, line - 1, line + 1, line - 2, line + 2}
    if any(re.search(rf"\b{n}\b", text) for n in line_set):
        return True
    enc = (bug.get("enclosing") or "").lower()
    enc_hit = bool(enc) and enc in text_l
    op_hit = any(kw.lower() in text_l for kw in bug["op_keywords"])
    return enc_hit and op_hit


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0, centre - half), min(1, centre + half))


def fisher_combined(p_values):
    p_values = [max(p, 1e-300) for p in p_values]
    chi2_stat = -2 * sum(log(p) for p in p_values)
    df = 2 * len(p_values)
    return chi2_stat, df, 1 - chi2.cdf(chi2_stat, df)


def main():
    results = {}
    for domain in DOMAINS:
        det = json.loads((ROOT / domain / "detection.json").read_text())
        bugs = det["bugs"]
        rev = ROOT / domain / "reviews"
        per_fam = {}
        for fam in FAMILIES:
            cf_caught = mm_caught = parsed_cold = parsed_mm = 0
            paired = []
            for bug in bugs:
                bid = bug["bug_id"]
                cf = extract_json(rev / f"cold_{fam}_{bid}.raw.txt")
                mf = extract_json(rev / f"cold_mismatched_{fam}_{bid}.raw.txt")
                cd = detects(bug, cf)
                md = detects(bug, mf)
                if cd is True:
                    cf_caught += 1
                if cd is not None:
                    parsed_cold += 1
                if md is True:
                    mm_caught += 1
                if md is not None:
                    parsed_mm += 1
                if cd is not None and md is not None:
                    paired.append((cd, md))
            n_total = len(bugs)
            cold_strict = cf_caught / n_total
            mm_strict = mm_caught / n_total
            ci_lo, ci_hi = wilson_ci(cf_caught, n_total)
            n_paired = len(paired)
            b = sum(1 for cd, md in paired if not cd and md)
            c = sum(1 for cd, md in paired if cd and not md)
            p_mc = mcnemar_one_sided(b, c)
            per_fam[fam] = {
                "cold_caught": cf_caught, "cold_parsed": parsed_cold,
                "mm_caught": mm_caught, "mm_parsed": parsed_mm,
                "n_total": n_total,
                "cold_strict": cold_strict, "mm_strict": mm_strict,
                "wilson95_strict": [ci_lo, ci_hi],
                "delta_strict": cold_strict - mm_strict,
                "mcnemar": {"n_paired": n_paired, "b": b, "c": c, "p": p_mc},
            }
        results[domain] = per_fam

        print(f"\n=== {domain} (n={len(bugs)}) ===")
        for fam in FAMILIES:
            v = per_fam[fam]
            print(f"  {fam:10s}: cold={v['cold_strict']:.2%} [{v['wilson95_strict'][0]:.2%},{v['wilson95_strict'][1]:.2%}] "
                  f"mm={v['mm_strict']:.2%} Δ={v['delta_strict']*100:+.1f}pp "
                  f"McNemar n={v['mcnemar']['n_paired']} b={v['mcnemar']['b']} c={v['mcnemar']['c']} p={v['mcnemar']['p']:.6f} "
                  f"{'SIG' if v['mcnemar']['p'] < 0.010 else 'NS'}")
        # Family spread
        cold_rates = [per_fam[f]["cold_strict"] for f in FAMILIES]
        spread = (max(cold_rates) - min(cold_rates)) * 100
        print(f"  cold-strict spread across families: {spread:.1f}pp (min={min(cold_rates)*100:.1f}, max={max(cold_rates)*100:.1f})")

    # Cross-domain Fisher (Codex-only): P7 + 3 P9 + 3 P10 = 7
    print("\n" + "=" * 80)
    print("CROSS-DOMAIN FISHER COMBINED (Codex-only, P7 + 3 P9 + 3 P10 = 7 tests)")
    print("=" * 80)
    p_values = [0.0078, 0.000122, 0.000031, 0.000122]  # P7 + 3 P9
    print(f"  P7+P9 (already): p_values={p_values}")
    for d in DOMAINS:
        p = results[d]["codex"]["mcnemar"]["p"]
        p_values.append(p)
        print(f"  {d:13s} (codex): p = {p:.6f}")
    chi2_stat, df, pc = fisher_combined(p_values)
    print(f"\n  Fisher χ²({df}) = {chi2_stat:.4f}")
    print(f"  Combined p = {pc:.6e}")
    print(f"  PRIMARY p<0.001: {'SIGNIFICANT' if pc < 0.001 else 'not'}")

    # All-families Fisher combined for P10 (9 tests)
    print("\n" + "=" * 80)
    print("P10 ALL-FAMILIES Fisher combined (9 tests = 3 domains × 3 families)")
    print("=" * 80)
    p_all = []
    for d in DOMAINS:
        for fam in FAMILIES:
            p = results[d][fam]["mcnemar"]["p"]
            p_all.append(p)
    chi2_stat2, df2, pc2 = fisher_combined(p_all)
    print(f"  Fisher χ²({df2}) = {chi2_stat2:.4f}, combined p = {pc2:.6e}")

    out = {
        "domains": results,
        "fisher_codex_only": {"chi2": chi2_stat, "df": df, "p": pc, "p_values": p_values},
        "fisher_all_families": {"chi2": chi2_stat2, "df": df2, "p": pc2, "p_values": p_all},
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "p10_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p10_analysis.json'}")


if __name__ == "__main__":
    main()
