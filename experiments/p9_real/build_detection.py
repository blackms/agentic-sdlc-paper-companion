"""Build per-bug detection criteria from AST manifest + reference module.

For each bug:
- The enclosing function/class name (most specific)
- The bug line number
- Operator-keyword set (e.g., '%→//' triggers ['modulo', 'floor division'])

A review is considered DETECTING the bug if `bugs_found` text contains:
- the line number (±2) OR
- the enclosing function/class name AND any operator keyword
"""
from __future__ import annotations
import ast
import json
from pathlib import Path

OP_KEYWORDS = {
    # AOR
    "Add": ["addition", "plus", "+ ", " + "],
    "Sub": ["subtract", "minus", "- ", " - "],
    "Mult": ["multipl", "*", "times"],
    "Div": ["divis", "/", "divide"],
    "FloorDiv": ["floor division", "//", "floordiv"],
    "Mod": ["modulo", "%", "mod "],
    # ROR
    "Eq": ["equal", "==", "equality"],
    "NotEq": ["not equal", "!=", "inequality"],
    "Lt": ["less than", "<", " lt "],
    "LtE": ["less or equal", "<=", " le "],
    "Gt": ["greater than", ">", " gt "],
    "GtE": ["greater or equal", ">=", " ge "],
    # BOR
    "And": ["and ", "logical and", "&&"],
    "Or": ["or ", "logical or", "||"],
}


def find_enclosing(tree: ast.AST, target_line: int) -> str | None:
    """Find the most specific FunctionDef / ClassDef containing target_line."""
    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= target_line <= end:
                candidates.append((end - start, node.name, type(node).__name__))
    if not candidates:
        return None
    candidates.sort()  # most specific (smallest range) first
    return candidates[0][1]


def parse_op_change(description: str) -> tuple[str, str]:
    """Parse 'AOR Mod -> FloorDiv (idx 0)' -> ('Mod', 'FloorDiv')."""
    parts = description.split()
    old_name = parts[1]
    new_name = parts[3]
    return old_name, new_name


def build(domain_dir: Path, ref_path: Path) -> dict:
    source = ref_path.read_text()
    tree = ast.parse(source)
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
        "csv_dom": root / "csv_dom" / "ref" / "csv_module.py",
        "urllib_dom": root / "urllib_dom" / "ref" / "parse_module.py",
        "jsondec_dom": root / "jsondec_dom" / "ref" / "decoder_module.py",
    }
    for d, ref in refs.items():
        out = build(root / d, ref)
        outp = root / d / "detection.json"
        outp.write_text(json.dumps(out, indent=2))
        print(f"  wrote {outp} ({len(out['bugs'])} bugs)")


if __name__ == "__main__":
    main()
