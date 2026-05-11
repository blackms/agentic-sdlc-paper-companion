"""Build the amendment-A1 manifest for the P11 saturation replication.

Selection rule (deterministic):
  1. Enumerate all PRIORITY-1 mutations on each frozen reference module
     using experiments/p9_real/ast_mutator.py.
     - csv side: strict validate (default importable check).
     - chardet side: loose validate (compile-only, mirrors v1.3 inject_all.py).
  2. The 30 v1.3-reused bugs are the keys present in the v1.3 manifest
     (operator, location, new_op_cls). Their source files are taken
     byte-identical from the v1.3 bugged/ directory (NOT re-derived).
  3. The remaining mutations (csv: 23, chardet: 30) are the v1.4_new_amendment_A1
     bugs. We sort them deterministically by (operator, location[0],
     location[1], new_op_cls_name) and assign IDs B31, B32, ...
  4. For each unique bug we emit two manifest rows: condition_left=truthful,
     condition_right=relabeled. The bugged file is the same byte sequence
     for both conditions; only the cover-story prefix differs (frozen, see
     launcher).

Run: python3 experiments/p11_replication/build_manifest.py
"""
from __future__ import annotations
import hashlib
import json
import sys
import importlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # worktree root
sys.path.insert(0, str(ROOT / "experiments" / "p9_real"))

SEED = 20260511  # amendment-A1 epoch; not used for sampling (saturation)

CSV_REF = ROOT / "experiments/p9_real/csv_dom/ref/csv_module.py"
CSV_V13_MANIFEST = ROOT / "experiments/p9_real/csv_dom/bugged/manifest.json"
CSV_V13_BUGGED_DIR = ROOT / "experiments/p9_real/csv_dom/bugged"
CSV_CONTRACTS = ROOT / "experiments/p9_real/csv_dom/contracts/contracts.md"

CHARDET_REF = ROOT / "experiments/p10_thirdparty/chardet_dom/ref/chardistribution_module.py"
CHARDET_V13_MANIFEST = ROOT / "experiments/p10_thirdparty/chardet_dom/bugged/manifest.json"
CHARDET_V13_BUGGED_DIR = ROOT / "experiments/p10_thirdparty/chardet_dom/bugged"
CHARDET_CONTRACTS = ROOT / "experiments/p10_thirdparty/chardet_dom/contracts/contracts.md"

COLD_PROMPT = ROOT / "experiments/p6_e2v2/prompts/cold_bankcheck.txt"
AST_MUTATOR = ROOT / "experiments/p9_real/ast_mutator.py"

OUT_DIR = ROOT / "experiments/p11_replication"
BUGGED_OUT_CSV = OUT_DIR / "bugged_csv"
BUGGED_OUT_CHARDET = OUT_DIR / "bugged_chardet"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def enumerate_side(label: str, ref: Path, v13_manifest_path: Path, loose: bool):
    """Return (all_mutations, v13_keys, new_mutations) using a fresh ast_mutator import."""
    if "ast_mutator" in sys.modules:
        del sys.modules["ast_mutator"]
    import ast_mutator  # noqa: WPS433
    if loose:
        def loose_validate(source: str) -> bool:
            try:
                compile(source, "<bugged>", "exec")
                return True
            except (SyntaxError, ValueError):
                return False
        ast_mutator.validate_compiles = loose_validate

    src = ref.read_text()
    muts = ast_mutator.enumerate_mutations(src)
    v13 = json.loads(v13_manifest_path.read_text())
    v13_keys = set(
        (b["operator"], tuple(b["location"]), b["new_op_cls"]) for b in v13["bugs"]
    )
    new = [
        m for m in muts
        if (m["operator"], tuple(m["location"]), m["new_op_cls_name"]) not in v13_keys
    ]
    # deterministic order: operator alpha, then lineno, col, then new_op_cls_name
    new.sort(key=lambda m: (m["operator"], m["location"][0], m["location"][1], m["new_op_cls_name"]))
    return muts, v13, new


def emit_bugged_files(new_muts, prefix: str, start_id: int, out_dir: Path):
    """Write new bugged .py files with deterministic IDs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for i, m in enumerate(new_muts, start=start_id):
        bid = f"{prefix}{i:02d}"
        path = out_dir / f"{bid}.py"
        path.write_text(m["bugged_source"])
        records.append({
            "bug_id": bid,
            "operator": m["operator"],
            "location": list(m["location"]),
            "description": m["description"],
            "new_op_cls": m["new_op_cls_name"],
            "bugged_path": str(path.relative_to(ROOT)),
        })
    return records


def build_side(label: str, prefix: str, ref: Path, v13_manifest_path: Path,
               v13_bugged_dir: Path, contracts_path: Path, out_dir: Path,
               loose: bool):
    all_muts, v13, new = enumerate_side(label, ref, v13_manifest_path, loose)
    print(f"[{label}] valid={len(all_muts)} v13={len(v13['bugs'])} new={len(new)}")
    # v13 reused: keep their B-IDs and source files byte-identical
    v13_records = []
    for b in v13["bugs"]:
        bid = b["bug_id"]
        src_path = v13_bugged_dir / f"{bid}.py"
        assert src_path.exists(), f"missing v13 bugged: {src_path}"
        v13_records.append({
            "bug_id": bid,
            "source": "v13_reused",
            "operator": b["operator"],
            "location": list(b["location"]),
            "description": b.get("description", ""),
            "new_op_cls": b["new_op_cls"],
            "bugged_path": str(src_path.relative_to(ROOT)),
            "sha256_bugged_file": sha256(src_path),
        })
    # new bugs: assign IDs starting at 31 (v13 was 1..30 / 1..29-unique-but-30-rows)
    new_records = emit_bugged_files(new, prefix, start_id=31, out_dir=out_dir)
    for r in new_records:
        r["source"] = "v14_new_amendment_A1"
        r["sha256_bugged_file"] = sha256(ROOT / r["bugged_path"])

    # Per-operator counts
    v13_ops = Counter(b["operator"] for b in v13["bugs"])
    new_ops = Counter(r["operator"] for r in new_records)
    total_ops = Counter()
    total_ops.update(v13_ops)
    total_ops.update(new_ops)

    # Build manifest rows (one row per unique bug, both conditions)
    rows = []
    for rec in v13_records + new_records:
        rows.append({
            "bug_id": rec["bug_id"],
            "source": rec["source"],
            "condition_left": "truthful",
            "condition_right": "relabeled",
            "operator": rec["operator"],
            "ast_location": rec["location"],
            "new_op_cls": rec["new_op_cls"],
            "bugged_path": rec["bugged_path"],
            "sha256_bugged_file": rec["sha256_bugged_file"],
        })

    side_manifest = {
        "side": label,
        "ref_module": str(ref.relative_to(ROOT)),
        "ref_sha256": sha256(ref),
        "contracts_path": str(contracts_path.relative_to(ROOT)),
        "contracts_sha256": sha256(contracts_path),
        "ast_mutator_sha256": sha256(AST_MUTATOR),
        "loose_validate": loose,
        "v13_seed": 20260510,
        "amendment_seed": SEED,
        "total_valid_mutations": len(all_muts),
        "v13_reused": len(v13_records),
        "v14_new": len(new_records),
        "n_unique_bugs": len(v13_records) + len(new_records),
        "per_operator_counts": {
            "v13_reused": dict(v13_ops),
            "v14_new_amendment_A1": dict(new_ops),
            "total": dict(total_ops),
        },
        "selection_rule": (
            "v13 bugs reused verbatim (same B-IDs, byte-identical bugged "
            "files). v14_new = mutations in enumerate_mutations(ref) NOT in "
            "v13 manifest, sorted by (operator, lineno, col, new_op_cls), "
            "all retained (saturation). v13: strict importable validate. "
            "chardet: compile-only validate (matches v1.3 inject_all.py)."
        ),
        "rows": rows,
    }
    return side_manifest


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BUGGED_OUT_CSV.mkdir(parents=True, exist_ok=True)
    BUGGED_OUT_CHARDET.mkdir(parents=True, exist_ok=True)

    csv_side = build_side(
        "csv", "P9c_B", CSV_REF, CSV_V13_MANIFEST, CSV_V13_BUGGED_DIR,
        CSV_CONTRACTS, BUGGED_OUT_CSV, loose=False,
    )
    chardet_side = build_side(
        "chardet", "P10c_B", CHARDET_REF, CHARDET_V13_MANIFEST, CHARDET_V13_BUGGED_DIR,
        CHARDET_CONTRACTS, BUGGED_OUT_CHARDET, loose=True,
    )

    manifest = {
        "amendment": "A1",
        "amendment_doc": "docs/paper/v1.4/preregistration-p11-replication-amendment-A1.md",
        "preregistration": "docs/paper/v1.4/preregistration-p11-replication.md",
        "header": {
            "csv": {
                "n_unique_bugs": csv_side["n_unique_bugs"],
                "per_operator_counts": csv_side["per_operator_counts"],
            },
            "chardet": {
                "n_unique_bugs": chardet_side["n_unique_bugs"],
                "per_operator_counts": chardet_side["per_operator_counts"],
            },
            "total_paired_codex_calls": (
                2 * csv_side["n_unique_bugs"] + 2 * chardet_side["n_unique_bugs"]
            ),
            "drift_diagnostic_extra_calls": 2 * 30 + 2 * 30,  # both sides, truthful only is preserved in main run; drift = re-run v13 truthful in separate subdir. Comment: 60 extras planned (30/side).
        },
        "csv": csv_side,
        "chardet": chardet_side,
    }
    out_path = OUT_DIR / "manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2, sort_keys=False))
    print(f"wrote {out_path}")

    # sha256 freeze
    freeze_entries = {
        "cold_bankcheck.txt": sha256(COLD_PROMPT),
        "ast_mutator.py": sha256(AST_MUTATOR),
        "csv_module.py": sha256(CSV_REF),
        "chardistribution_module.py": sha256(CHARDET_REF),
        "csv_contracts.md": sha256(CSV_CONTRACTS),
        "chardet_contracts.md": sha256(CHARDET_CONTRACTS),
    }
    # manifest hash AFTER write (without itself)
    manifest_hash = sha256_bytes(out_path.read_bytes())
    freeze_entries["manifest.json"] = manifest_hash
    freeze_path = OUT_DIR / "sha256_freeze.txt"
    with freeze_path.open("w") as fh:
        for k, v in freeze_entries.items():
            fh.write(f"{v}  {k}\n")
    print(f"wrote {freeze_path}")


if __name__ == "__main__":
    main()
