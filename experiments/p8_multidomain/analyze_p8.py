"""P8 multi-domain analyzer.

For each of the 3 P8 domains (exprev, regex, httphdr):
- Per-role detection rate
- Pre-registered metrics: cold_aligned > 50%, cold_mismatched < 30%, Δ ≥ 20pp
- Paired McNemar (cold_aligned > cold_mismatched)

Cross-domain meta-analysis:
- Fisher's combined p-value over P7 + 3 P8 McNemar tests
"""
import json
import re
import yaml
from pathlib import Path
from math import comb, log, exp
from scipy.stats import chi2

ROOT = Path(__file__).parent
DOMAINS = ["exprev", "regex", "httphdr"]
ROLES = ["warm", "cold", "cold_mismatched", "skeptic", "simm1", "simm2", "simm3"]


def extract_json(raw_path):
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        return None
    text = raw_path.read_text()
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = list(fenced)
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", text, re.DOTALL):
        candidates.append(m.group(0))
    last = text.rfind("}")
    first = text.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        candidates.append(text[first:last + 1])
    for cand in candidates:
        try:
            data = json.loads(cand.strip())
            if isinstance(data, dict) and "bugs_found" in data:
                bugs = data["bugs_found"]
                if isinstance(bugs, list):
                    return [str(b) for b in bugs]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def detect(bug, found):
    if found is None:
        return None
    text = " ||| ".join(b.lower() for b in found)
    return any(str(kw).lower() in text for kw in bug["detection_keywords"])


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)


def fisher_combined(p_values):
    """Fisher's method to combine p-values: -2 Σ ln(p) ~ χ²(2k)"""
    p_values = [max(p, 1e-300) for p in p_values]
    chi2_stat = -2 * sum(log(p) for p in p_values)
    df = 2 * len(p_values)
    return chi2_stat, df, 1 - chi2.cdf(chi2_stat, df)


def main():
    domain_results = {}
    for domain in DOMAINS:
        bugs = yaml.safe_load((ROOT / domain / "bugs.yaml").read_text())["bugs"]
        bugged_dir = ROOT / domain / "bugged"
        reviews_dir = ROOT / domain / "reviews"
        present_bugs = [b for b in bugs if (bugged_dir / f"{b['id']}.py").exists()]

        detection = {}
        for bug in present_bugs:
            bid = bug["id"]
            detection[bid] = {}
            for role in ROLES:
                raw = reviews_dir / f"{role}_{bid}.raw.txt"
                found = extract_json(raw)
                detection[bid][role] = None if found is None else detect(bug, found)

        # Per-role rate
        rates = {}
        for role in ROLES:
            n_ok = sum(1 for bid in detection if detection[bid][role] is True)
            n_parse = sum(1 for bid in detection if detection[bid][role] is not None)
            rate = n_ok / n_parse if n_parse else 0
            rates[role] = (n_ok, n_parse, rate)

        # Paired McNemar cold_aligned vs cold_mismatched
        common = [bid for bid in detection
                  if detection[bid]["cold"] is not None
                  and detection[bid]["cold_mismatched"] is not None]
        b_only = sum(1 for bid in common
                     if detection[bid]["cold"] is False
                     and detection[bid]["cold_mismatched"] is True)
        c_only = sum(1 for bid in common
                     if detection[bid]["cold"] is True
                     and detection[bid]["cold_mismatched"] is False)
        p_mc = mcnemar_one_sided(b_only, c_only)

        domain_results[domain] = {
            "n_bugs": len(present_bugs),
            "rates": {r: {"caught": v[0], "n_parsed": v[1], "rate": v[2]}
                      for r, v in rates.items()},
            "mcnemar": {"n_paired": len(common), "b": b_only, "c": c_only, "p": p_mc},
            "detection": detection,
        }

        cold_a = rates["cold"][2]
        cold_m = rates["cold_mismatched"][2]
        delta = (cold_a - cold_m) * 100
        print(f"\n=== {domain} (n={len(present_bugs)}) ===")
        for role in ROLES:
            n_ok, n_pa, r = rates[role]
            marker = ""
            if role == "cold":
                marker = "  ← PRIMARY"
            elif role == "cold_mismatched":
                marker = "  ← ABLATION"
            print(f"  {role:18s}: {n_ok}/{n_pa} = {r:.2%}{marker}")
        print(f"  Specificity Δ = {delta:.1f}pp")
        verdict = []
        if cold_a > 0.50:
            verdict.append("PRIMARY✓")
        else:
            verdict.append("PRIMARY✗")
        if cold_m < 0.30:
            verdict.append("ABLATION✓")
        else:
            verdict.append("ABLATION✗")
        if delta >= 20:
            verdict.append("Δ≥20pp✓")
        else:
            verdict.append("Δ≥20pp✗")
        print(f"  Verdict: {' '.join(verdict)}")
        print(f"  McNemar paired: n={len(common)} b={b_only} c={c_only} p={p_mc:.4f}")

    # Cross-domain meta-analysis (Fisher's combined)
    print("\n" + "=" * 80)
    print("CROSS-DOMAIN META-ANALYSIS (Fisher's combined)")
    print("=" * 80)

    # Include P7 (parser) result
    p7_p = 0.0078
    p7_record = {"domain": "json_parser_P7", "p": p7_p, "b": 0, "c": 7, "n": 10}
    print(f"  P7 (json_parser):  p = {p7_p}  (n=10, b=0, c=7)")
    p_values = [p7_p]
    for domain in DOMAINS:
        r = domain_results[domain]["mcnemar"]
        p_values.append(r["p"])
        print(f"  {domain:15s}: p = {r['p']:.4f}  (n={r['n_paired']}, b={r['b']}, c={r['c']})")

    chi2_stat, df, p_combined = fisher_combined(p_values)
    print(f"\n  Fisher combined χ²({df}) = {chi2_stat:.4f}")
    print(f"  Combined p = {p_combined:.6f}")
    print(f"  Verdict: {'SIGNIFICANT' if p_combined < 0.001 else 'not'} at primary threshold (p<0.001)")

    out = {
        "domains": domain_results,
        "p7_external": p7_record,
        "fisher_combined": {"chi2": chi2_stat, "df": df, "p": p_combined,
                            "p_values": p_values},
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "p8_analysis.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p8_analysis.json'}")


if __name__ == "__main__":
    main()
