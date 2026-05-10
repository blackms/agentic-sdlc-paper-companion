"""P7 analyzer: detection by role, with cold-aligned vs cold-mismatched ablation."""
import json
import re
import yaml
from pathlib import Path
from math import comb

ROOT = Path(__file__).parent
REVIEWS = ROOT / "reviews"
BUGS = yaml.safe_load((ROOT / "bugs_p7.yaml").read_text())["bugs"]

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


def main():
    detection = {}
    for bug in BUGS:
        bid = bug["id"]
        if not (ROOT / "bugged" / f"{bid}.py").exists():
            continue
        detection[bid] = {}
        for role in ROLES:
            raw = REVIEWS / f"{role}_{bid}.raw.txt"
            found = extract_json(raw)
            d = None if found is None else detect(bug, found)
            detection[bid][role] = d

    print("=" * 100)
    print(f"P7 — JSON parser, n={len(detection)} bugs (15 across 7 categories)")
    print("=" * 100)

    print("\nDetection rate per role:")
    rates = {}
    for role in ROLES:
        n_ok = sum(1 for bid in detection if detection[bid][role] is True)
        n_parse = sum(1 for bid in detection if detection[bid][role] is not None)
        rate = n_ok / n_parse if n_parse else 0
        rates[role] = (n_ok, n_parse, rate)
        marker = ""
        if role == "cold":
            marker = "  ← PRIMARY: aligned (parser contracts)"
        elif role == "cold_mismatched":
            marker = "  ← ABLATION: mismatched (bankcheck contracts on parser)"
        print(f"  {role:18s}: {n_ok}/{n_parse} = {rate:.2%}{marker}")

    print()
    print("Pre-registered metrics:")
    cold_aligned_rate = rates["cold"][2]
    cold_mismatched_rate = rates["cold_mismatched"][2]
    delta = cold_aligned_rate - cold_mismatched_rate

    print(f"  Primary (cold aligned > 50%):                    {cold_aligned_rate:.2%}  "
          f"{'PASS' if cold_aligned_rate > 0.50 else 'FAIL'}")
    print(f"  Ablation (cold mismatched < 30%):                {cold_mismatched_rate:.2%}  "
          f"{'PASS' if cold_mismatched_rate < 0.30 else 'FAIL'}")
    print(f"  Specificity (aligned − mismatched ≥ 20pp):       Δ={delta * 100:.1f}pp  "
          f"{'PASS' if delta >= 0.20 else 'FAIL'}")

    # Paired McNemar: cold_aligned vs cold_mismatched
    print()
    print("Paired McNemar (cold_aligned vs cold_mismatched, same bugs):")
    common = [bid for bid in detection
              if detection[bid]["cold"] is not None and detection[bid]["cold_mismatched"] is not None]
    b = sum(1 for bid in common if detection[bid]["cold"] is False and detection[bid]["cold_mismatched"] is True)
    c = sum(1 for bid in common if detection[bid]["cold"] is True and detection[bid]["cold_mismatched"] is False)
    p = mcnemar_one_sided(b, c)
    print(f"  n_paired = {len(common)}, b = {b} (aligned miss / mismatched catch), "
          f"c = {c} (aligned catch / mismatched miss)")
    print(f"  McNemar one-sided p (H1: aligned > mismatched) = {p:.4f}  "
          f"{'BONF✓' if p < 0.010 else ('α=0.05✓' if p < 0.05 else 'n/s')}")

    # 2x2 conditions for full P2 transferability test
    print()
    print("Per-condition q (≥ 2 reviewer miss):")
    CONDITIONS = {
        "asymm-codex":           ["warm", "cold", "skeptic"],
        "asymm-codex-mismatched": ["warm", "cold_mismatched", "skeptic"],
        "symm-mono":             ["simm1", "simm2", "simm3"],
    }

    cond_q = {}
    for label, roles in CONDITIONS.items():
        misses = []
        for bid in detection:
            vals = [detection[bid][r] for r in roles]
            if any(v is None for v in vals):
                continue
            misses.append(1 if sum(1 for v in vals if v is False) >= 2 else 0)
        n_eff = len(misses)
        miss_count = sum(misses)
        q = miss_count / n_eff if n_eff else 0
        cond_q[label] = (q, miss_count, n_eff)
        print(f"  {label:25s}: q = {q:.4f} ({miss_count}/{n_eff})")

    # Save
    out = {
        "preregistered": True,
        "phase": "P7",
        "n_bugs": len(detection),
        "rates": {r: {"caught": v[0], "n_parsed": v[1], "rate": v[2]} for r, v in rates.items()},
        "metrics": {
            "primary_cold_aligned": cold_aligned_rate,
            "ablation_cold_mismatched": cold_mismatched_rate,
            "specificity_delta_pp": delta * 100,
            "mcnemar_p": p, "mcnemar_b": b, "mcnemar_c": c, "n_paired": len(common),
        },
        "conditions": {l: {"q": q, "miss": m, "n_eff": n} for l, (q, m, n) in cond_q.items()},
        "detection": detection,
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "p7_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p7_analysis.json'}")


if __name__ == "__main__":
    main()
