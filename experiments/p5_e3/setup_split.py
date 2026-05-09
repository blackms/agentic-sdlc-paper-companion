"""E3 setup: split T2's 200 bugs into TRAIN (100) and TEST (100) deterministically.

Pattern extraction will use TRAIN; cycle 1 (pattern-injected) will be evaluated on TEST.
The 200 bugs are 7-categorized; we stratify to keep category proportions roughly equal.
"""
import yaml
import json
import random
from pathlib import Path

ROOT = Path(__file__).parent
T2_BUGS = yaml.safe_load((ROOT.parent / "t2" / "bugs.yaml").read_text())["bugs"]

rng = random.Random(20260509)

# Stratify by category
by_cat = {}
for b in T2_BUGS:
    by_cat.setdefault(b["category"], []).append(b["id"])

train_ids, test_ids = [], []
for cat, ids in by_cat.items():
    rng.shuffle(ids)
    half = len(ids) // 2
    train_ids.extend(ids[:half])
    test_ids.extend(ids[half:])

# Balance
print(f"TRAIN: {len(train_ids)} bugs")
print(f"TEST:  {len(test_ids)} bugs")
print()
print("Category distribution:")
print(f"  {'category':25s} {'all':>5s} {'train':>6s} {'test':>5s}")
for cat in sorted(by_cat):
    all_n = len(by_cat[cat])
    tr_n = sum(1 for bid in train_ids if any(b["id"] == bid and b["category"] == cat for b in T2_BUGS))
    te_n = sum(1 for bid in test_ids if any(b["id"] == bid and b["category"] == cat for b in T2_BUGS))
    print(f"  {cat:25s} {all_n:>5d} {tr_n:>6d} {te_n:>5d}")

split = {
    "seed": 20260509,
    "train": sorted(train_ids),
    "test": sorted(test_ids),
}
(ROOT / "split.json").write_text(json.dumps(split, indent=2))
print(f"\nSaved: {ROOT / 'split.json'}")
