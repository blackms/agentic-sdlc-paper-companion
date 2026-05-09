"""E2 review parser. Same logic as t2/parse_reviews.py but for the bankcheck.py benchmark.

Uses bugs_e2.yaml for ground truth + detection_keywords.
Generates _detection_table.json compatible with t2 analyzer.
"""
import json
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
REVIEWS = ROOT / "reviews"
BUGS = yaml.safe_load((ROOT / "bugs_e2.yaml").read_text())["bugs"]

ROLES = ["warm", "cold", "skeptic", "simm1", "simm2", "simm3", "claudeg", "geminig"]


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


def main():
    detection = {}
    parse_status = {}
    for bug in BUGS:
        bid = bug["id"]
        # Skip bugs that weren't successfully injected (no .py)
        if not (ROOT / "bugged" / f"{bid}.py").exists():
            continue
        detection[bid] = {}
        parse_status[bid] = {}
        for role in ROLES:
            raw = REVIEWS / f"{role}_{bid}.raw.txt"
            bugs_found = extract_json(raw)
            if bugs_found is None:
                detection[bid][role] = None
                parse_status[bid][role] = "missing" if not raw.exists() else "parse_fail"
            else:
                d = detect_bug(bug, bugs_found)
                detection[bid][role] = d
                parse_status[bid][role] = "ok"
                (REVIEWS / f"{role}_{bid}.parsed.json").write_text(
                    json.dumps({"bugs_found": bugs_found, "detected_planted": d}, indent=2))

    out = {"detection": detection, "parse_status": parse_status,
           "n_bugs": len(detection), "roles": ROLES}
    (REVIEWS / "_detection_table.json").write_text(json.dumps(out, indent=2))

    print("=" * 100)
    print(f"E2 parse — n_bugs={len(detection)}")
    print("=" * 100)
    print(f"{'bug':8s} {'cat':22s} {'sev':6s}", end=" | ")
    for role in ROLES:
        print(f"{role[:7]:>7s}", end=" ")
    print(" | parse")
    print("-" * 130)
    for bug in BUGS:
        bid = bug["id"]
        if bid not in detection:
            continue
        row = []
        parses = []
        for role in ROLES:
            d = detection[bid][role]
            cell = " ✓ " if d is True else (" ✗ " if d is False else " ? ")
            row.append(cell)
            ps = parse_status[bid][role]
            parses.append("ok" if ps == "ok" else ps[:4])
        print(f"{bid:8s} {bug['category']:22s} {bug['severity']:6s}", end=" | ")
        for cell in row:
            print(f"{cell:>7s}", end=" ")
        print(f" | {','.join(parses)}")

    print()
    print("Detection rate per role:")
    for role in ROLES:
        n_ok = sum(1 for bid in detection if detection[bid][role] is True)
        n_parse = sum(1 for bid in detection if detection[bid][role] is not None)
        rate = n_ok / n_parse if n_parse > 0 else 0
        print(f"  {role:8s}: {n_ok}/{n_parse} = {rate:.2%}")


if __name__ == "__main__":
    main()
