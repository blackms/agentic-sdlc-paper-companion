"""Parse all review raw outputs and extract bugs_found JSON.

Detection: per ogni bug ground-truth, controllo se la lista bugs_found di un reviewer
contiene almeno una entry che matcha le detection_keywords del bug. Match: keyword
presente case-insensitive in qualsiasi entry.
"""
import json
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
REVIEWS = ROOT / "reviews"
BUGS = yaml.safe_load((ROOT / "bugs.yaml").read_text())["bugs"]

ROLES = ["warm", "cold", "skeptic", "simm1", "simm2", "simm3", "claudeg"]


def extract_json(raw_path):
    """Extract bugs_found list from raw codex output. Return list[str] or None."""
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        return None
    text = raw_path.read_text()
    # Codex output ends with the assistant's final message, often the JSON.
    # Try fenced ```json blocks first
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = list(fenced)
    # Try to find inline {...} that contains "bugs_found"
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", text, re.DOTALL):
        candidates.append(m.group(0))
    # Try the very last {...} block (usually the answer)
    all_braces = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    if all_braces:
        candidates.append(all_braces[-1])
    # Multi-line braces fallback
    last_idx = text.rfind("}")
    if last_idx >= 0:
        first_idx = text.rfind("{", 0, last_idx)
        if first_idx >= 0:
            candidates.append(text[first_idx:last_idx + 1])
    for cand in candidates:
        cand = cand.strip()
        try:
            data = json.loads(cand)
            if isinstance(data, dict) and "bugs_found" in data:
                bugs = data["bugs_found"]
                if isinstance(bugs, list):
                    return [str(b) for b in bugs]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def detect_bug(bug, bugs_found):
    """Return True if at least one detection_keyword matches at least one entry."""
    if bugs_found is None:
        return None  # parse failure
    text_join = " ||| ".join(b.lower() for b in bugs_found)
    for kw in bug["detection_keywords"]:
        if kw.lower() in text_join:
            return True
    return False


def main():
    detection = {}  # detection[bid][role] = True/False/None
    parse_status = {}  # parse_status[bid][role] = "ok"/"parse_fail"/"missing"

    for bug in BUGS:
        bid = bug["id"]
        detection[bid] = {}
        parse_status[bid] = {}
        for role in ROLES:
            raw = REVIEWS / f"{role}_{bid}.raw.txt"
            bugs_found = extract_json(raw)
            if bugs_found is None:
                detection[bid][role] = None
                parse_status[bid][role] = "missing" if not raw.exists() else "parse_fail"
                continue
            d = detect_bug(bug, bugs_found)
            detection[bid][role] = d
            parse_status[bid][role] = "ok"
            # Save parsed JSON for inspection
            (REVIEWS / f"{role}_{bid}.parsed.json").write_text(
                json.dumps({"bugs_found": bugs_found, "detected_planted": d}, indent=2)
            )

    # Save full table
    out = {
        "detection": detection,
        "parse_status": parse_status,
        "n_bugs": len(BUGS),
        "roles": ROLES,
    }
    (REVIEWS / "_detection_table.json").write_text(json.dumps(out, indent=2))

    # Summary print
    print("=" * 100)
    print(f"{'bug':4s} | {'function':18s} | {'cat':12s} | warm  cold  skep  simm1 simm2 simm3 | parse")
    print("-" * 100)
    for bug in BUGS:
        bid = bug["id"]
        row = []
        parses = []
        for role in ROLES:
            d = detection[bid][role]
            cell = " ✓ " if d is True else (" ✗ " if d is False else " ? ")
            row.append(cell)
            ps = parse_status[bid][role]
            parses.append("ok" if ps == "ok" else ps[:4])
        print(f"{bid:4s} | {bug['function']:18s} | {bug['category']:12s} | "
              f"{row[0]}   {row[1]}   {row[2]}   {row[3]}   {row[4]}   {row[5]} | {','.join(parses)}")

    # Aggregate per role
    print()
    print("Detection rate per role:")
    for role in ROLES:
        n_ok = sum(1 for bid in detection if detection[bid][role] is True)
        n_parse = sum(1 for bid in detection if detection[bid][role] is not None)
        rate = n_ok / n_parse if n_parse > 0 else 0
        print(f"  {role:8s}: {n_ok}/{n_parse} = {rate:.2%}")

    print(f"\nFile: {REVIEWS / '_detection_table.json'}")


if __name__ == "__main__":
    main()
