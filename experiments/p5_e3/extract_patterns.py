"""E3 pattern extraction (automatic, schema-fixed).

Reads existing T2 reviews (warm Codex baseline) on TRAIN bugs.
For each bug, determines if warm reviewer caught it (keyword match).
Counts misses by category. Top-5 categories by miss count = patterns to inject.

The pattern schema is FIXED (the 7 T2 categories) and PRE-REGISTERED before the cycle:
  off-by-one / contract / logic / precision / atomicity / currency / exception.
"""
import json
import re
import yaml
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
T2_REVIEWS = ROOT.parent / "t2" / "reviews"
T2_BUGS = {b["id"]: b for b in yaml.safe_load((ROOT.parent / "t2" / "bugs.yaml").read_text())["bugs"]}
SPLIT = json.loads((ROOT / "split.json").read_text())

ALL_CATEGORIES = sorted({b["category"] for b in T2_BUGS.values()})


def parse_review_bugs(raw_path: Path):
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
    return any(kw.lower() in text for kw in bug["detection_keywords"])


def main():
    train_ids = SPLIT["train"]
    miss_by_category = Counter()
    n_by_category = Counter()
    parse_fail = 0
    for bid in train_ids:
        bug = T2_BUGS[bid]
        cat = bug["category"]
        n_by_category[cat] += 1
        raw = T2_REVIEWS / f"warm_{bid}.raw.txt"
        bugs_found = parse_review_bugs(raw)
        d = detect(bug, bugs_found)
        if d is None:
            parse_fail += 1
            continue
        if d is False:
            miss_by_category[cat] += 1

    print("=" * 80)
    print(f"E3 pattern extraction — TRAIN bugs n={len(train_ids)} (parse-fails: {parse_fail})")
    print("=" * 80)
    print(f"\n{'category':25s} {'miss':>6s} {'n':>4s} {'miss-rate':>11s}")
    miss_rates = {}
    for cat in ALL_CATEGORIES:
        rate = miss_by_category[cat] / n_by_category[cat] if n_by_category[cat] else 0
        miss_rates[cat] = rate
        print(f"  {cat:23s} {miss_by_category[cat]:>6d} {n_by_category[cat]:>4d} {rate:>11.3f}")

    # Top-5 patterns by miss-rate (extracted automatically)
    top5 = sorted(miss_rates.items(), key=lambda x: -x[1])[:5]
    print("\nTop-5 patterns to inject (automatic, schema-fixed):")
    for i, (cat, rate) in enumerate(top5, 1):
        print(f"  {i}. {cat:25s} miss-rate {rate:.3f}")

    # Save
    out = {
        "train_n": len(train_ids),
        "parse_fails": parse_fail,
        "miss_by_category": dict(miss_by_category),
        "n_by_category": dict(n_by_category),
        "miss_rates": miss_rates,
        "top5_patterns": [c for c, _ in top5],
    }
    (ROOT / "patterns_top5.json").write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {ROOT / 'patterns_top5.json'}")


if __name__ == "__main__":
    main()
