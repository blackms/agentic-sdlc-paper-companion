"""P6.1 E2v2 parse + analyze.

Builds a detection table using:
- cold from p6_e2v2/reviews/ (NEW: domain-aligned bankcheck contracts)
- warm, skeptic, simm1, simm2, simm3, claudeg from p5_e2/reviews/ (UNCHANGED from E2)

Same parsing/detection logic as p5_e2/parse_e2.py.
Compares P6.1 results against pre-registered metrics.
"""
import json
import re
import yaml
from pathlib import Path
from itertools import combinations
from math import comb

ROOT = Path(__file__).parent
P5_REVIEWS = ROOT.parent / "p5_e2" / "reviews"
P6_REVIEWS = ROOT / "reviews"
BUGS = yaml.safe_load((ROOT.parent / "p5_e2" / "bugs_e2.yaml").read_text())["bugs"]

ROLES = ["warm", "cold", "skeptic", "simm1", "simm2", "simm3", "claudeg"]


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


def detect_bug(bug, bugs_found):
    if bugs_found is None:
        return None
    text_join = " ||| ".join(b.lower() for b in bugs_found)
    for kw in bug["detection_keywords"]:
        if kw.lower() in text_join:
            return True
    return False


def mcnemar_one_sided(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return sum(comb(n, k) for k in range(0, b + 1)) / (2 ** n)


def main():
    detection = {}
    for bug in BUGS:
        bid = bug["id"]
        if not (ROOT.parent / "p5_e2" / "bugged" / f"{bid}.py").exists():
            continue
        detection[bid] = {}
        for role in ROLES:
            if role == "cold":
                raw = P6_REVIEWS / f"cold_{bid}.raw.txt"
            else:
                raw = P5_REVIEWS / f"{role}_{bid}.raw.txt"
            bugs_found = extract_json(raw)
            d = None if bugs_found is None else detect_bug(bug, bugs_found)
            detection[bid][role] = d

    print("=" * 100)
    print(f"P6.1 E2v2 — bankcheck.py with DOMAIN-ALIGNED cold reviewer (n={len(detection)})")
    print("=" * 100)

    # Per-role detection rate
    print("\nDetection rate per role:")
    for role in ROLES:
        n_ok = sum(1 for bid in detection if detection[bid][role] is True)
        n_parse = sum(1 for bid in detection if detection[bid][role] is not None)
        rate = n_ok / n_parse if n_parse else 0
        marker = ""
        if role == "cold":
            marker = "  ← P5 baseline 11%; threshold > 50%"
        print(f"  {role:8s}: {n_ok}/{n_parse} = {rate:.2%}{marker}")

    # 2x2 conditions
    CONDITIONS = {
        "asymm-codex": ["warm", "cold", "skeptic"],
        "symm-mono":   ["simm1", "simm2", "simm3"],
        "symm-multi":  ["simm1", "simm2", "claudeg"],
        "asymm-multi": ["warm", "cold", "claudeg"],
    }

    def joint_2of3(roles):
        out = []
        for bid in sorted(detection):
            vals = []
            for r in roles:
                d = detection[bid][r]
                if d is None:
                    vals = None
                    break
                vals.append(0 if d is True else 1)
            if vals is None:
                continue
            out.append((bid, 1 if sum(vals) >= 2 else 0))
        return out

    print("\nPer-condition q (≥ 2 reviewer miss):")
    cond_results = {}
    for label, roles in CONDITIONS.items():
        j = joint_2of3(roles)
        n_eff = len(j)
        miss_count = sum(v for _, v in j)
        q = miss_count / n_eff if n_eff else 0
        cond_results[label] = (j, q, miss_count, n_eff)
        print(f"  {label:14s}: q = {q:.4f} ({miss_count}/{n_eff})")

    # Pre-registered primary: paired McNemar asymm-multi < symm-mono
    print("\nPre-registered PRIMARY metric (paired McNemar):")
    contrasts = [
        ("asymm-codex", "symm-mono"),
        ("symm-multi",  "symm-mono"),
        ("asymm-multi", "symm-mono"),
        ("asymm-multi", "asymm-codex"),
        ("asymm-multi", "symm-multi"),
    ]
    for a, b in contrasts:
        ja, _, _, _ = cond_results[a]
        jb, _, _, _ = cond_results[b]
        ja_d = dict(ja); jb_d = dict(jb)
        common = sorted(set(ja_d) & set(jb_d))
        n_paired = len(common)
        b_only = sum(1 for bid in common if ja_d[bid] == 1 and jb_d[bid] == 0)
        c_only = sum(1 for bid in common if ja_d[bid] == 0 and jb_d[bid] == 1)
        p = mcnemar_one_sided(b_only, c_only)
        mark = "BONF✓" if p < 0.010 else ("α=0.05✓" if p < 0.05 else "n/s")
        primary = "  ← PRIMARY" if (a, b) == ("asymm-multi", "symm-mono") else ""
        print(f"  {a:12s} < {b:12s}: n={n_paired:>2d} b={b_only}/c={c_only} "
              f"McNemar p={p:.4f} {mark}{primary}")

    # Save
    out = {
        "preregistered": True,
        "phase": "P6.1 E2v2",
        "n_bugs": len(detection),
        "detection": detection,
        "per_condition_q": {l: {"q": q, "miss": m, "n_eff": n}
                             for l, (_, q, m, n) in cond_results.items()},
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "e2v2_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'e2v2_analysis.json'}")


if __name__ == "__main__":
    main()
