"""Build per-bug detection criteria for P10 (mirrors p9_real/build_detection.py)."""
from __future__ import annotations
import ast
import json
from pathlib import Path

OP_KEYWORDS = {
    "Add": ["addition", "plus", "+ ", " + "],
    "Sub": ["subtract", "minus", "- ", " - "],
    "Mult": ["multipl", "*", "times"],
    "Div": ["divis", "/", "divide"],
    "FloorDiv": ["floor division", "//", "floordiv"],
    "Mod": ["modulo", "%", "mod "],
    "Eq": ["equal", "==", "equality"],
    "NotEq": ["not equal", "!=", "inequality"],
    "Lt": ["less than", "<", " lt "],
    "LtE": ["less or equal", "<=", " le "],
    "Gt": ["greater than", ">", " gt "],
    "GtE": ["greater or equal", ">=", " ge "],
    "And": ["and ", "logical and", "&&"],
    "Or": ["or ", "logical or", "||"],
}


def find_enclosing(tree, target_line):
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= target_line <= end:
                candidates.append((end - start, node.name))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def parse_op_change(desc):
    parts = desc.split()
    return parts[1], parts[3]


def build(domain_dir, ref_path):
    src = ref_path.read_text()
    tree = ast.parse(src)
    manifest = json.loads((domain_dir / "bugged" / "manifest.json").read_text())
    enriched = []
    for bug in manifest["bugs"]:
        line = bug["location"][0]
        old_op, new_op = parse_op_change(bug["description"])
        enclosing = find_enclosing(tree, line)
        kw_old = OP_KEYWORDS.get(old_op, [])
        kw_new = OP_KEYWORDS.get(new_op, [])
        enriched.append({
            "bug_id": bug["bug_id"],
            "operator": bug["operator"],
            "line": line,
            "old_op": old_op,
            "new_op": new_op,
            "enclosing": enclosing,
            "op_keywords": list({*kw_old, *kw_new}),
            "description": bug["description"],
        })
    return {"ref": str(ref_path), "bugs": enriched}


def main():
    root = Path(__file__).parent
    refs = {
        "dateutil_dom": root / "dateutil_dom" / "ref" / "relativedelta_module.py",
        "parsy_dom":    root / "parsy_dom"    / "ref" / "parsy_module.py",
        "chardet_dom":  root / "chardet_dom"  / "ref" / "chardistribution_module.py",
    }
    for d, ref in refs.items():
        out = build(root / d, ref)
        outp = root / d / "detection.json"
        outp.write_text(json.dumps(out, indent=2))
        print(f"  wrote {outp} ({len(out['bugs'])} bugs)")


if __name__ == "__main__":
    main()
