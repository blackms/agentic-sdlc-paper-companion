"""E3v2 analyzer: warm Codex with CONCRETE-EXAMPLE injection vs baseline + v1.

Hypothesis: concrete missed-bug examples may recover the C-T3 LLM-grounded
convergence claim that pattern-name injection (E3 v1) failed to produce.

Tests:
- Primary: McNemar one-sided H1 (v2 > baseline) on TEST set
- Secondary: McNemar one-sided H1 (v2 > v1) on TEST set
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from math import comb
import yaml

ROOT = Path(__file__).parent
T2_REVIEWS = ROOT.parent / "t2" / "reviews"
T2_BUGS = {b["id"]: b for b in yaml.safe_load((ROOT.parent / "t2" / "bugs.yaml").read_text())["bugs"]}
SPLIT = json.loads((ROOT.parent / "p5_e3" / "split.json").read_text())
TOP5 = set(json.loads((ROOT.parent / "p5_e3" / "patterns_top5.json").read_text())["top5_patterns"])


def parse_review(p):
    if not p.exists() or p.stat().st_size == 0:
        return None
    t = p.read_text()
    cands = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", t, re.DOTALL)
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", t, re.DOTALL):
        cands.append(m.group(0))
    last = t.rfind("}")
    first = t.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        cands.append(t[first:last + 1])
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


def detect(bug, found):
    if found is None:
        return None
    txt = " ||| ".join(b.lower() for b in found)
    return any(kw.lower() in txt for kw in bug["detection_keywords"])


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)


def main():
    test_ids = SPLIT["test"]
    rows = []
    for bid in test_ids:
        bug = T2_BUGS.get(bid)
        if not bug:
            continue
        baseline = T2_REVIEWS / f"warm_{bid}.raw.txt"
        v1 = ROOT.parent / "p5_e3" / "reviews" / f"warm_injected_{bid}.raw.txt"
        v2 = ROOT / "reviews" / f"warm_injected_v2_{bid}.raw.txt"
        b_f = parse_review(baseline)
        v1_f = parse_review(v1)
        v2_f = parse_review(v2)
        rows.append({
            "bid": bid, "category": bug["category"], "in_top5": bug["category"] in TOP5,
            "baseline": detect(bug, b_f) if b_f is not None else None,
            "v1": detect(bug, v1_f) if v1_f is not None else None,
            "v2": detect(bug, v2_f) if v2_f is not None else None,
        })

    print(f"E3v2 analyzer — TEST n={len(rows)}")

    # Primary: v2 vs baseline
    paired_b = [r for r in rows if r["baseline"] is not None and r["v2"] is not None]
    n_b = len(paired_b)
    b_only = sum(1 for r in paired_b if r["baseline"] and not r["v2"])
    c_only = sum(1 for r in paired_b if not r["baseline"] and r["v2"])
    p_b = mcnemar_one_sided(b_only, c_only)
    base_rate = sum(1 for r in paired_b if r["baseline"]) / n_b if n_b else 0
    v2_rate_b = sum(1 for r in paired_b if r["v2"]) / n_b if n_b else 0
    print(f"\n## PRIMARY: v2 vs baseline (paired n={n_b})")
    print(f"  baseline rate: {base_rate:.3f}")
    print(f"  v2 rate:       {v2_rate_b:.3f}  (Δ = {v2_rate_b - base_rate:+.3f})")
    print(f"  discordant:    b={b_only} (baseline-only) c={c_only} (v2-only)")
    print(f"  McNemar p (one-sided H1: v2 > baseline) = {p_b:.4f}")
    print(f"  Verdict @ α=0.05: {'SIG' if p_b < 0.05 else 'NS'}")

    # Secondary: v2 vs v1
    paired_v = [r for r in rows if r["v1"] is not None and r["v2"] is not None]
    n_v = len(paired_v)
    b_only_v = sum(1 for r in paired_v if r["v1"] and not r["v2"])
    c_only_v = sum(1 for r in paired_v if not r["v1"] and r["v2"])
    p_v = mcnemar_one_sided(b_only_v, c_only_v)
    v1_rate = sum(1 for r in paired_v if r["v1"]) / n_v if n_v else 0
    v2_rate_v = sum(1 for r in paired_v if r["v2"]) / n_v if n_v else 0
    print(f"\n## SECONDARY: v2 vs v1 (paired n={n_v})")
    print(f"  v1 rate: {v1_rate:.3f}")
    print(f"  v2 rate: {v2_rate_v:.3f}  (Δ = {v2_rate_v - v1_rate:+.3f})")
    print(f"  discordant: b={b_only_v} (v1-only) c={c_only_v} (v2-only)")
    print(f"  McNemar p (one-sided H1: v2 > v1) = {p_v:.4f}")
    print(f"  Verdict @ α=0.05: {'SIG' if p_v < 0.05 else 'NS'}")

    # Per-top5 category breakdown (descriptive)
    print(f"\n## Per-top5-category v2 vs baseline (descriptive)")
    for cat in sorted(TOP5):
        rs = [r for r in paired_b if r["category"] == cat]
        if not rs:
            continue
        bn = sum(1 for r in rs if r["baseline"]) / len(rs)
        vn = sum(1 for r in rs if r["v2"]) / len(rs)
        print(f"  {cat:14s} (n={len(rs):2d}): baseline {bn:.2%}  v2 {vn:.2%}  Δ {vn - bn:+.2%}")

    out = {
        "n_rows": len(rows),
        "primary": {
            "n_paired": n_b, "baseline_rate": base_rate, "v2_rate": v2_rate_b,
            "delta": v2_rate_b - base_rate,
            "mcnemar_b": b_only, "mcnemar_c": c_only, "p": p_b,
        },
        "secondary": {
            "n_paired": n_v, "v1_rate": v1_rate, "v2_rate": v2_rate_v,
            "delta": v2_rate_v - v1_rate,
            "mcnemar_b": b_only_v, "mcnemar_c": c_only_v, "p": p_v,
        },
        "rows": rows,
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "e3v2_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'e3v2_analysis.json'}")


if __name__ == "__main__":
    main()
