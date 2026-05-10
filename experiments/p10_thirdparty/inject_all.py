"""P10 injection driver — uses p9 ast_mutator with compile-only validation."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "p9_real"))

import ast_mutator

# Loose validation: compile-only (no import-execute)
def loose_validate(source):
    try:
        compile(source, "<bugged>", "exec")
        return True
    except (SyntaxError, ValueError):
        return False

ast_mutator.validate_compiles = loose_validate

ROOT = Path(__file__).parent
DOMAINS = [
    ("dateutil_dom", "P10d", "ref/relativedelta_module.py"),
    ("parsy_dom",    "P10p", "ref/parsy_module.py"),
    ("chardet_dom",  "P10c", "ref/chardistribution_module.py"),
]

for domain, prefix, ref in DOMAINS:
    out_dir = ROOT / domain / "bugged"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = (ROOT / domain / ref).read_text()
    print(f"\n=== {domain} ===")
    muts = ast_mutator.enumerate_mutations(src)
    print(f"  enumerated {len(muts)} valid mutations")
    sample = ast_mutator.stratified_sample(muts, 30, 20260510)
    print(f"  sampled {len(sample)}")
    manifest = []
    for i, m in enumerate(sample, 1):
        bid = f"{prefix}_B{i:02d}"
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
        "ref": ref,
        "seed": 20260510,
        "total_valid_mutations": len(muts),
        "sampled_n": len(sample),
        "bugs": manifest,
    }, indent=2))
    print(f"  wrote {out_dir}/")
