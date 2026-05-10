"""P9 multi-domain analyzer.

For each domain:
- Per-role detection rate
- Pre-registered metrics: cold > 50%, cold_mismatched < 30%, Δ ≥ 20pp
- Paired McNemar (one-sided) cold vs cold_mismatched
- Bonferroni-stricter α = 0.010 from original 5-test family

Cross-domain:
- Fisher's combined p over P7 + 3 P9 = 4 tests; primary threshold p < 0.001
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from math import comb, log
from scipy.stats import chi2

ROOT = Path(__file__).parent
DOMAINS = ["csv_dom", "urllib_dom", "jsondec_dom"]
DOMAIN_PREFIX = {"csv_dom": "P9c", "urllib_dom": "P9u", "jsondec_dom": "P9j"}
ROLES = ["warm", "cold", "cold_mismatched", "skeptic", "simm1", "simm2", "simm3"]


def extract_json(raw_path: Path):
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


def detects(bug: dict, found: list[str] | None) -> bool | None:
    """A review detects the bug iff `bugs_found` text contains:
    - the bug line (or ±2 neighbours) AS A NUMBER, OR
    - the enclosing fn/class name AND at least one operator keyword.
    """
    if found is None:
        return None
    text = " ||| ".join(b for b in found)
    text_l = text.lower()

    line = bug["line"]
    line_set = {line, line - 1, line + 1, line - 2, line + 2}
    line_hit = any(re.search(rf"\b{n}\b", text) for n in line_set)
    if line_hit:
        return True

    enc = (bug.get("enclosing") or "").lower()
    enc_hit = bool(enc) and enc in text_l
    op_hit = any(kw.lower() in text_l for kw in bug["op_keywords"])
    return enc_hit and op_hit


def mcnemar_one_sided(b: int, c: int) -> float:
    """One-sided exact McNemar: P(B' >= c | n=b+c, p=0.5).
    Tests H1: cold > cold_mismatched (i.e., c large).
    """
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)


def fisher_combined(p_values: list[float]):
    p_values = [max(p, 1e-300) for p in p_values]
    chi2_stat = -2 * sum(log(p) for p in p_values)
    df = 2 * len(p_values)
    return chi2_stat, df, 1 - chi2.cdf(chi2_stat, df)


def analyze_domain(domain: str) -> dict:
    prefix = DOMAIN_PREFIX[domain]
    detection_data = json.loads((ROOT / domain / "detection.json").read_text())
    bugs = detection_data["bugs"]
    reviews_dir = ROOT / domain / "reviews"

    detection: dict[str, dict[str, bool | None]] = {}
    for bug in bugs:
        bid = bug["bug_id"]
        detection[bid] = {}
        for role in ROLES:
            raw = reviews_dir / f"{role}_{bid}.raw.txt"
            found = extract_json(raw)
            detection[bid][role] = detects(bug, found)

    rates = {}
    rates_strict = {}
    for role in ROLES:
        n_ok = sum(1 for bid in detection if detection[bid][role] is True)
        n_parsed = sum(1 for bid in detection if detection[bid][role] is not None)
        n_total = len(bugs)
        rate = n_ok / n_parsed if n_parsed else 0
        rate_strict = n_ok / n_total if n_total else 0
        rates[role] = (n_ok, n_parsed, rate)
        rates_strict[role] = (n_ok, n_total, rate_strict)

    # Paired McNemar cold vs cold_mismatched
    common = [bid for bid in detection
              if detection[bid]["cold"] is not None
              and detection[bid]["cold_mismatched"] is not None]
    b = sum(1 for bid in common
            if detection[bid]["cold"] is False
            and detection[bid]["cold_mismatched"] is True)
    c = sum(1 for bid in common
            if detection[bid]["cold"] is True
            and detection[bid]["cold_mismatched"] is False)
    p_mc = mcnemar_one_sided(b, c)

    return {
        "n_bugs": len(bugs),
        "rates": {r: {"caught": v[0], "n_parsed": v[1], "rate": v[2]}
                  for r, v in rates.items()},
        "rates_strict_unparsed_as_miss": {
            r: {"caught": v[0], "n_total": v[1], "rate": v[2]}
            for r, v in rates_strict.items()},
        "mcnemar": {"n_paired": len(common), "b": b, "c": c, "p": p_mc},
        "detection": detection,
    }


def main():
    results = {}
    for domain in DOMAINS:
        r = analyze_domain(domain)
        results[domain] = r
        cold_a = r["rates"]["cold"]["rate"]
        cold_m = r["rates"]["cold_mismatched"]["rate"]
        delta = (cold_a - cold_m) * 100
        print(f"\n=== {domain} (n={r['n_bugs']}) ===")
        for role in ROLES:
            n_ok = r["rates"][role]["caught"]
            n_pa = r["rates"][role]["n_parsed"]
            rate = r["rates"][role]["rate"]
            mark = ""
            if role == "cold":
                mark = "  ← PRIMARY"
            elif role == "cold_mismatched":
                mark = "  ← ABLATION"
            print(f"  {role:18s}: {n_ok}/{n_pa} = {rate:.2%}{mark}")
        print(f"  Specificity Δ = {delta:.1f}pp")
        v = []
        v.append("PRIMARY✓" if cold_a > 0.50 else "PRIMARY✗")
        v.append("ABLATION✓" if cold_m < 0.30 else "ABLATION✗")
        v.append("Δ≥20pp✓" if delta >= 20 else "Δ≥20pp✗")
        print(f"  Verdict (parsed): {' '.join(v)}")
        cold_strict = r["rates_strict_unparsed_as_miss"]["cold"]["rate"]
        cold_m_strict = r["rates_strict_unparsed_as_miss"]["cold_mismatched"]["rate"]
        delta_strict = (cold_strict - cold_m_strict) * 100
        vs = []
        vs.append("PRIMARY✓" if cold_strict > 0.50 else "PRIMARY✗")
        vs.append("ABLATION✓" if cold_m_strict < 0.30 else "ABLATION✗")
        vs.append("Δ≥20pp✓" if delta_strict >= 20 else "Δ≥20pp✗")
        print(f"  STRICT (unparsed=miss): cold={cold_strict:.2%} mm={cold_m_strict:.2%} Δ={delta_strict:.1f}pp  {' '.join(vs)}")
        mc = r["mcnemar"]
        print(f"  McNemar paired: n={mc['n_paired']} b={mc['b']} c={mc['c']} p={mc['p']:.6f}")
        thr = 0.010
        print(f"  vs α={thr}: {'SIG' if mc['p'] < thr else 'NS'}")

    # Cross-domain Fisher (P7 + 3 P9)
    print("\n" + "=" * 80)
    print("CROSS-DOMAIN FISHER COMBINED (P7 + 3 P9)")
    print("=" * 80)
    p7_p = 0.0078
    print(f"  P7 (json_parser): p = {p7_p}  (n=10, b=0, c=7)")
    p_values = [p7_p]
    for d in DOMAINS:
        r = results[d]["mcnemar"]
        p_values.append(r["p"])
        print(f"  {d:15s}: p = {r['p']:.6f}  (n={r['n_paired']}, b={r['b']}, c={r['c']})")
    chi2_stat, df, pc = fisher_combined(p_values)
    print(f"\n  Fisher χ²({df}) = {chi2_stat:.4f}")
    print(f"  Combined p = {pc:.6e}")
    print(f"  PRIMARY threshold p<0.001: {'SIGNIFICANT' if pc < 0.001 else 'not'}")

    out = {
        "domains": results,
        "p7_external": {"domain": "json_parser_P7", "p": p7_p, "b": 0, "c": 7, "n": 10},
        "fisher_combined": {"chi2": chi2_stat, "df": df, "p": pc, "p_values": p_values},
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "p9_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p9_analysis.json'}")


if __name__ == "__main__":
    main()
