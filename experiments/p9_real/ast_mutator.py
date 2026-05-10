"""AST-level mutation generator for Phase 9.

Operators (PRIORITY 1):
- AOR: + ↔ -, * ↔ /, // ↔ %
- ROR: == ↔ !=, < ↔ <=, > ↔ >=, < ↔ >
- BOR: and ↔ or

Each mutation produces ONE single-point change on the AST and emits the modified
source via ast.unparse(). The driver:
1. Parses the reference module.
2. Enumerates all PRIORITY-1 mutation locations.
3. For each, generates a bugged source string and validates it compiles.
4. Filters to importable mutants.
5. Stratified-samples N mutations.
"""
from __future__ import annotations
import ast
import argparse
import importlib.util
import json
import random
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


# ---- Mutation operators ----

AOR_PAIRS = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.Div,
    ast.Div: ast.Mult,
    ast.FloorDiv: ast.Mod,
    ast.Mod: ast.FloorDiv,
}

ROR_PAIRS = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    # Cross-type: < -> > (paired below by category)
}

BOR_PAIRS = {
    ast.And: ast.Or,
    ast.Or: ast.And,
}


@dataclass
class Mutation:
    operator: str             # "AOR" | "ROR" | "BOR"
    location: tuple[int, int]  # (lineno, col_offset)
    description: str
    bugged_source: str
    bug_id: str = ""


def _enum_AOR(tree: ast.AST):
    """Yield (location, description, mutator_fn)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and type(node.op) in AOR_PAIRS:
            new_op_cls = AOR_PAIRS[type(node.op)]
            old_name = type(node.op).__name__
            new_name = new_op_cls.__name__
            n = node
            def make(new_op_cls=new_op_cls, n=n):
                def fn(t):
                    for nd in ast.walk(t):
                        if nd is n:
                            return new_op_cls()
                    return None
                return fn
            yield (
                (n.lineno, n.col_offset),
                f"AOR {old_name} -> {new_name}",
                make(),
                "AOR",
                n,
                new_op_cls,
            )


def _enum_ROR(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for idx, op in enumerate(node.ops):
                if type(op) in ROR_PAIRS:
                    new_op_cls = ROR_PAIRS[type(op)]
                    old_name = type(op).__name__
                    new_name = new_op_cls.__name__
                    yield (
                        (node.lineno, node.col_offset),
                        f"ROR {old_name} -> {new_name} (idx {idx})",
                        None,
                        "ROR",
                        (node, idx),
                        new_op_cls,
                    )


def _enum_BOR(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and type(node.op) in BOR_PAIRS:
            new_op_cls = BOR_PAIRS[type(node.op)]
            old_name = type(node.op).__name__
            new_name = new_op_cls.__name__
            yield (
                (node.lineno, node.col_offset),
                f"BOR {old_name} -> {new_name}",
                None,
                "BOR",
                node,
                new_op_cls,
            )


def apply_mutation(source: str, target_op: str, target_loc, op_idx, new_op_cls) -> str:
    """Apply a single mutation by re-parsing and rewriting."""
    tree = ast.parse(source)
    if target_op == "AOR":
        target_lineno, target_col = target_loc
        for nd in ast.walk(tree):
            if isinstance(nd, ast.BinOp) and (nd.lineno, nd.col_offset) == (target_lineno, target_col):
                if type(nd.op) in AOR_PAIRS and AOR_PAIRS[type(nd.op)] is new_op_cls:
                    nd.op = new_op_cls()
                    return ast.unparse(tree)
        raise RuntimeError(f"AOR target not found at {target_loc}")
    if target_op == "ROR":
        target_lineno, target_col = target_loc
        for nd in ast.walk(tree):
            if isinstance(nd, ast.Compare) and (nd.lineno, nd.col_offset) == (target_lineno, target_col):
                if op_idx < len(nd.ops) and type(nd.ops[op_idx]) in ROR_PAIRS \
                        and ROR_PAIRS[type(nd.ops[op_idx])] is new_op_cls:
                    nd.ops[op_idx] = new_op_cls()
                    return ast.unparse(tree)
        raise RuntimeError(f"ROR target not found at {target_loc}")
    if target_op == "BOR":
        target_lineno, target_col = target_loc
        for nd in ast.walk(tree):
            if isinstance(nd, ast.BoolOp) and (nd.lineno, nd.col_offset) == (target_lineno, target_col):
                if type(nd.op) in BOR_PAIRS and BOR_PAIRS[type(nd.op)] is new_op_cls:
                    nd.op = new_op_cls()
                    return ast.unparse(tree)
        raise RuntimeError(f"BOR target not found at {target_loc}")
    raise ValueError(f"unknown operator {target_op}")


def validate_compiles(source: str) -> bool:
    """Try to compile and import the bugged source as a module."""
    try:
        compile(source, "<bugged>", "exec")
    except (SyntaxError, ValueError):
        return False
    # Import test
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "bugged_module.py"
        path.write_text(source)
        spec = importlib.util.spec_from_file_location("bugged_module", str(path))
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception:
            return False
    return True


def enumerate_mutations(source: str) -> list[dict]:
    """Enumerate all PRIORITY-1 mutations and validate each."""
    tree = ast.parse(source)
    candidates = []
    candidates.extend(_enum_AOR(tree))
    candidates.extend(_enum_ROR(tree))
    candidates.extend(_enum_BOR(tree))

    valid_mutations = []
    for loc, desc, _, op_cat, target, new_op_cls in candidates:
        op_idx = target[1] if op_cat == "ROR" else None
        try:
            bugged = apply_mutation(source, op_cat, loc, op_idx, new_op_cls)
        except Exception:
            continue
        if not validate_compiles(bugged):
            continue
        valid_mutations.append({
            "operator": op_cat,
            "location": list(loc),
            "description": desc,
            "bugged_source": bugged,
            "op_idx": op_idx,
            "new_op_cls_name": new_op_cls.__name__,
        })
    return valid_mutations


def stratified_sample(mutations: list[dict], n: int, seed: int) -> list[dict]:
    """Stratified sample by operator category."""
    by_cat: dict[str, list[dict]] = {}
    for m in mutations:
        by_cat.setdefault(m["operator"], []).append(m)
    rng = random.Random(seed)
    target_per_cat = max(1, n // len(by_cat)) if by_cat else 0
    sample = []
    for cat, items in by_cat.items():
        rng.shuffle(items)
        sample.extend(items[:target_per_cat])
    rng.shuffle(sample)
    if len(sample) < n:
        # Top up from any remaining
        all_remaining = [m for m in mutations if m not in sample]
        rng.shuffle(all_remaining)
        sample.extend(all_remaining[: n - len(sample)])
    return sample[:n]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--ref", required=True, help="Path to reference Python module")
    p.add_argument("--out", required=True, help="Output directory for bugged files + manifest")
    p.add_argument("--n", type=int, default=30, help="Number of bugs to sample")
    p.add_argument("--seed", type=int, default=20260510)
    p.add_argument("--prefix", default="P9_B", help="Bug ID prefix")
    args = p.parse_args()

    ref_path = Path(args.ref)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    source = ref_path.read_text()
    print(f"Enumerating mutations on {ref_path}...")
    all_mutations = enumerate_mutations(source)
    print(f"  Found {len(all_mutations)} valid (importable) PRIORITY-1 mutations")
    print(f"  By operator: " + ", ".join(
        f"{op}={sum(1 for m in all_mutations if m['operator']==op)}"
        for op in sorted({m["operator"] for m in all_mutations})
    ))

    sample = stratified_sample(all_mutations, args.n, args.seed)
    print(f"  Sampled {len(sample)} bugs (target {args.n})")

    manifest = []
    for i, m in enumerate(sample, 1):
        bid = f"{args.prefix}{i:02d}"
        m["bug_id"] = bid
        (out_dir / f"{bid}.py").write_text(m["bugged_source"])
        manifest.append({
            "bug_id": bid,
            "operator": m["operator"],
            "location": m["location"],
            "description": m["description"],
            "new_op_cls": m["new_op_cls_name"],
        })

    (out_dir / "manifest.json").write_text(json.dumps({
        "ref": str(ref_path),
        "seed": args.seed,
        "total_valid_mutations": len(all_mutations),
        "sampled_n": len(sample),
        "bugs": manifest,
    }, indent=2))
    print(f"  Wrote {len(sample)} bugged files + manifest.json to {out_dir}")


if __name__ == "__main__":
    main()
