"""E3 cycle-1 analyzer.

Compares baseline warm Codex (existing T2 reviews) on TEST bugs against
warm Codex with PATTERN-INJECTED prompt (p5_e3/reviews/warm_injected_*).

Both reviews are paired by bug-id (TEST set). McNemar exact test for
'pattern injection improves detection on TEST'.

Per-pattern (category) breakdown:
- Compare detection rate on TEST bugs in seen-pattern categories (top-5)
  vs unseen categories (the rest), at baseline and at injected.
- Same-pattern recurrence: how does detection change for bugs in
  patterns that the system was warned about?
"""
import json
import re
import yaml
from pathlib import Path
from math import comb

ROOT = Path(__file__).parent
T2_REVIEWS = ROOT.parent / "t2" / "reviews"
T2_BUGS = {b["id"]: b for b in yaml.safe_load((ROOT.parent / "t2" / "bugs.yaml").read_text())["bugs"]}
SPLIT = json.loads((ROOT / "split.json").read_text())
PATTERNS = json.loads((ROOT / "patterns_top5.json").read_text())
TOP5 = set(PATTERNS["top5_patterns"])


def parse_review(raw_path):
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
        candidates.append(text[first:last+1])
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


def detect(bug, bugs_found):
    if bugs_found is None:
        return None
    text = " ||| ".join(b.lower() for b in bugs_found)
    return any(kw.lower() in text for kw in bug["detection_keywords"])


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    p = sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)
    return p


def main():
    test_ids = SPLIT["test"]
    print(f"E3 cycle-1 analysis — TEST n={len(test_ids)}")
    print(f"Top-5 patterns injected: {sorted(TOP5)}")
    print()

    paired_bugs = []
    for bid in test_ids:
        bug = T2_BUGS[bid]
        baseline_raw = T2_REVIEWS / f"warm_{bid}.raw.txt"
        injected_raw = ROOT / "reviews" / f"warm_injected_{bid}.raw.txt"
        b_found = parse_review(baseline_raw)
        i_found = parse_review(injected_raw)
        if b_found is None or i_found is None:
            continue
        b_caught = detect(bug, b_found)
        i_caught = detect(bug, i_found)
        paired_bugs.append({
            "bid": bid, "category": bug["category"],
            "in_top5": bug["category"] in TOP5,
            "baseline_caught": b_caught, "injected_caught": i_caught,
        })

    n = len(paired_bugs)
    print(f"Paired bugs (both baseline + injected parsed): {n}")
    if n < 5:
        print("Not enough paired data yet. Re-run after retry completes.")
        return

    # Overall McNemar
    b = sum(1 for x in paired_bugs if x["baseline_caught"] and not x["injected_caught"])  # baseline catches, injected misses (worse)
    c = sum(1 for x in paired_bugs if (not x["baseline_caught"]) and x["injected_caught"])  # baseline misses, injected catches (better)
    p_overall = mcnemar_one_sided(b, c)
    print(f"\n## OVERALL McNemar (one-sided H1: injected > baseline)")
    print(f"  Discordant: baseline-better b={b}, injected-better c={c}")
    print(f"  McNemar p (one-sided H1: c > b) = {p_overall:.4f}")

    baseline_rate = sum(1 for x in paired_bugs if x["baseline_caught"]) / n
    injected_rate = sum(1 for x in paired_bugs if x["injected_caught"]) / n
    print(f"  Detection: baseline {baseline_rate:.3f}, injected {injected_rate:.3f}, "
          f"Δ = {injected_rate - baseline_rate:+.3f}")

    # By in-top5 vs not
    print(f"\n## By PATTERN MEMBERSHIP")
    for label, in_top5 in [("seen-patterns (top-5)", True), ("unseen-patterns", False)]:
        sub = [x for x in paired_bugs if x["in_top5"] == in_top5]
        n_s = len(sub)
        if n_s == 0:
            continue
        baseline_r = sum(1 for x in sub if x["baseline_caught"]) / n_s
        injected_r = sum(1 for x in sub if x["injected_caught"]) / n_s
        b_s = sum(1 for x in sub if x["baseline_caught"] and not x["injected_caught"])
        c_s = sum(1 for x in sub if (not x["baseline_caught"]) and x["injected_caught"])
        p_s = mcnemar_one_sided(b_s, c_s)
        print(f"  {label:25s} n={n_s:>3d}  baseline={baseline_r:.3f}  "
              f"injected={injected_r:.3f}  Δ={injected_r - baseline_r:+.3f}  "
              f"McNemar p={p_s:.4f}")

    # Per-category
    print(f"\n## Per-category")
    cats = sorted({x["category"] for x in paired_bugs})
    for cat in cats:
        sub = [x for x in paired_bugs if x["category"] == cat]
        n_s = len(sub)
        if n_s == 0:
            continue
        baseline_r = sum(1 for x in sub if x["baseline_caught"]) / n_s
        injected_r = sum(1 for x in sub if x["injected_caught"]) / n_s
        in_top5 = "★" if cat in TOP5 else " "
        print(f"  {in_top5} {cat:25s} n={n_s:>3d}  baseline={baseline_r:.3f}  "
              f"injected={injected_r:.3f}  Δ={injected_r - baseline_r:+.3f}")

    out = {
        "n_paired": n,
        "patterns_top5": sorted(TOP5),
        "overall": {"baseline_rate": baseline_rate, "injected_rate": injected_rate,
                    "mcnemar_b": b, "mcnemar_c": c, "mcnemar_p": p_overall},
        "paired_bugs": paired_bugs,
    }
    (ROOT / "results" / "cycle1_analysis.json").parent.mkdir(exist_ok=True)
    (ROOT / "results" / "cycle1_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'cycle1_analysis.json'}")


if __name__ == "__main__":
    main()
