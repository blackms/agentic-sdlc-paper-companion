"""P9 cross-family analyzer.

Compares cold reviewer detection across 3 reviewer families:
- Codex gpt-5.5 (existing P9 cold)
- Claude Opus 4.7 (cold_opus)
- Gemini 3.1 Pro Preview (cold_gemini31)

For domains: csv_dom (full triple), jsondec_dom (Opus only if Gemini quota fails).

Tests reviewer-family robustness of the C1 specificity finding.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from math import comb, sqrt
from scipy.stats import chi2

ROOT = Path(__file__).parent
DOMAINS = ["csv_dom", "jsondec_dom"]
FAMILIES = ["cold", "cold_opus", "cold_gemini31"]


def extract_json(raw_path: Path):
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        return None
    text = raw_path.read_text()
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    cands = list(fenced)
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


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0, centre - half), min(1, centre + half))


def main():
    results = {}
    for domain in DOMAINS:
        det_data = json.loads((ROOT / domain / "detection.json").read_text())
        bugs = det_data["bugs"]
        rev = ROOT / domain / "reviews"
        per_fam = {}
        for fam in FAMILIES:
            caught = parsed = 0
            for bug in bugs:
                bid = bug["bug_id"]
                raw = rev / f"{fam}_{bid}.raw.txt"
                found = extract_json(raw)
                d = detects(bug, found)
                if d is None:
                    continue
                parsed += 1
                if d:
                    caught += 1
            n_total = len(bugs)
            rate_strict = caught / n_total if n_total else 0
            rate_parsed = caught / parsed if parsed else 0
            ci_lo, ci_hi = wilson_ci(caught, n_total)
            per_fam[fam] = {
                "caught": caught,
                "parsed": parsed,
                "n_total": n_total,
                "rate_parsed": rate_parsed,
                "rate_strict": rate_strict,
                "wilson95_strict": [ci_lo, ci_hi],
            }
        results[domain] = per_fam
        print(f"\n=== {domain} (n_bugs={len(bugs)}) ===")
        for fam in FAMILIES:
            v = per_fam[fam]
            print(f"  {fam:18s}: {v['caught']}/{v['parsed']} parsed = {v['rate_parsed']:.2%} | "
                  f"strict {v['caught']}/{v['n_total']} = {v['rate_strict']:.2%} "
                  f"[Wilson95 {v['wilson95_strict'][0]:.2%},{v['wilson95_strict'][1]:.2%}]")

        # Cross-family Δ vs Codex
        codex = per_fam["cold"]["rate_strict"]
        for fam in ["cold_opus", "cold_gemini31"]:
            other = per_fam[fam]["rate_strict"]
            if per_fam[fam]["parsed"] > 0:
                delta = (other - codex) * 100
                print(f"  Δ {fam} vs cold(codex): {delta:+.1f}pp strict")

    out = {"domains": results}
    (ROOT / "results" / "p9_cross_family.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT / 'results' / 'p9_cross_family.json'}")


if __name__ == "__main__":
    main()
