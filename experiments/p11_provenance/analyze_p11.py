"""P11 provenance-label analyzer.

Compares cold-aligned detection on:
- csv stdlib (P9): truthful (existing) vs relabeled-as-third-party (P11 NEW)
- chardet third-party (P10): truthful (existing) vs relabeled-as-stdlib (P11 NEW)

Tests anti-stdlib carelessness via paired McNemar.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from math import comb, sqrt
from scipy.stats import chi2

ROOT = Path(__file__).parent
P9 = ROOT.parent / "p9_real" / "csv_dom"
P10 = ROOT.parent / "p10_thirdparty" / "chardet_dom"


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


def analyze(domain_dir, p11_tag, truthful_role="cold"):
    det = json.loads((domain_dir / "detection.json").read_text())
    bugs = det["bugs"]
    rev_truthful = domain_dir / "reviews"
    rev_p11 = ROOT / "reviews"
    paired = []
    n_total = len(bugs)
    truthful_caught = relabeled_caught = 0
    truthful_parsed = relabeled_parsed = 0
    for bug in bugs:
        bid = bug["bug_id"]
        tf = extract_json(rev_truthful / f"{truthful_role}_{bid}.raw.txt")
        rf = extract_json(rev_p11 / f"{p11_tag}_{bid}.raw.txt")
        td = detects(bug, tf)
        rd = detects(bug, rf)
        if td is True: truthful_caught += 1
        if td is not None: truthful_parsed += 1
        if rd is True: relabeled_caught += 1
        if rd is not None: relabeled_parsed += 1
        if td is not None and rd is not None:
            paired.append((td, rd))
    return {
        "n_bugs": n_total,
        "truthful": {"caught": truthful_caught, "parsed": truthful_parsed,
                     "rate_strict": truthful_caught / n_total,
                     "wilson95_strict": wilson_ci(truthful_caught, n_total)},
        "relabeled": {"caught": relabeled_caught, "parsed": relabeled_parsed,
                      "rate_strict": relabeled_caught / n_total,
                      "wilson95_strict": wilson_ci(relabeled_caught, n_total)},
        "paired": {
            "n": len(paired),
            "both_caught": sum(1 for t, r in paired if t and r),
            "truth_only": sum(1 for t, r in paired if t and not r),
            "relab_only": sum(1 for t, r in paired if not t and r),
            "both_miss": sum(1 for t, r in paired if not t and not r),
        },
    }


def main():
    print("=== P11 Provenance-Label Analyzer ===\n")

    # csv stdlib → relabeled as third-party
    csv_res = analyze(P9, "csv_relabel_thirdparty")
    print("## csv_dom (P9 stdlib): truthful_stdlib vs relabeled_thirdparty")
    print(f"  truthful_stdlib    : {csv_res['truthful']['caught']}/{csv_res['n_bugs']} = {csv_res['truthful']['rate_strict']:.2%} [Wilson95 {csv_res['truthful']['wilson95_strict'][0]:.2%},{csv_res['truthful']['wilson95_strict'][1]:.2%}]")
    print(f"  relabeled_3rdparty : {csv_res['relabeled']['caught']}/{csv_res['n_bugs']} = {csv_res['relabeled']['rate_strict']:.2%} [Wilson95 {csv_res['relabeled']['wilson95_strict'][0]:.2%},{csv_res['relabeled']['wilson95_strict'][1]:.2%}]")
    delta_csv = (csv_res['relabeled']['rate_strict'] - csv_res['truthful']['rate_strict']) * 100
    print(f"  Δ (relabel - truth): {delta_csv:+.1f}pp")
    p_csv_b = csv_res['paired']['truth_only']
    p_csv_c = csv_res['paired']['relab_only']
    p_csv = mcnemar_one_sided(p_csv_b, p_csv_c)
    print(f"  Paired n={csv_res['paired']['n']} truth_only(b)={p_csv_b} relab_only(c)={p_csv_c}")
    print(f"  McNemar one-sided H1: relab > truth: p = {p_csv:.4f}  {'SIG@0.05' if p_csv < 0.05 else 'NS'}")

    # chardet third-party → relabeled as stdlib (P10 names cold reviewer "cold_codex")
    chardet_res = analyze(P10, "chardet_relabel_stdlib", truthful_role="cold_codex")
    print("\n## chardet_dom (P10 third-party): truthful_thirdparty vs relabeled_stdlib")
    print(f"  truthful_3rdparty : {chardet_res['truthful']['caught']}/{chardet_res['n_bugs']} = {chardet_res['truthful']['rate_strict']:.2%} [Wilson95 {chardet_res['truthful']['wilson95_strict'][0]:.2%},{chardet_res['truthful']['wilson95_strict'][1]:.2%}]")
    print(f"  relabeled_stdlib  : {chardet_res['relabeled']['caught']}/{chardet_res['n_bugs']} = {chardet_res['relabeled']['rate_strict']:.2%} [Wilson95 {chardet_res['relabeled']['wilson95_strict'][0]:.2%},{chardet_res['relabeled']['wilson95_strict'][1]:.2%}]")
    delta_ch = (chardet_res['relabeled']['rate_strict'] - chardet_res['truthful']['rate_strict']) * 100
    print(f"  Δ (relabel - truth): {delta_ch:+.1f}pp")
    p_ch_b = chardet_res['paired']['relab_only']
    p_ch_c = chardet_res['paired']['truth_only']
    p_ch = mcnemar_one_sided(p_ch_b, p_ch_c)
    print(f"  Paired n={chardet_res['paired']['n']} relab_only(b)={p_ch_b} truth_only(c)={p_ch_c}")
    print(f"  McNemar one-sided H1: relab < truth: p = {p_ch:.4f}  {'SIG@0.05' if p_ch < 0.05 else 'NS'}")

    # Verdict on anti-stdlib carelessness
    print("\n## VERDICT on anti-stdlib carelessness")
    csv_pass = p_csv < 0.05
    ch_pass = p_ch < 0.05
    if csv_pass and ch_pass:
        print("  BOTH H1 PASS → anti-stdlib carelessness CONFIRMED (label moderates detection causally)")
    elif csv_pass or ch_pass:
        print(f"  ASYMMETRIC: csv (stdlib→3p) {'PASS' if csv_pass else 'FAIL'}, chardet (3p→stdlib) {'PASS' if ch_pass else 'FAIL'}")
    else:
        print("  BOTH H1 FAIL → anti-stdlib carelessness REJECTED (label does not causally moderate detection)")
        print("  Conclusion: P9-P10 sample gap is driven by code-intrinsic factors, not label/familiarity.")

    out = {
        "csv_dom_relabel_thirdparty": csv_res,
        "chardet_dom_relabel_stdlib": chardet_res,
        "tests": {
            "csv_H1_relab_gt_truth": {"p": p_csv, "b": p_csv_b, "c": p_csv_c, "delta_pp": delta_csv},
            "chardet_H1_relab_lt_truth": {"p": p_ch, "b": p_ch_b, "c": p_ch_c, "delta_pp": delta_ch},
        },
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "p11_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p11_analysis.json'}")


if __name__ == "__main__":
    main()
