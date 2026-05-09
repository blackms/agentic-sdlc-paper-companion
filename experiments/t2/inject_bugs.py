"""Generate 30 bugged versions of finance_lib.py from bugs.yaml."""
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
REF = (ROOT / "ref" / "finance_lib.py").read_text()
BUGS = yaml.safe_load((ROOT / "bugs.yaml").read_text())["bugs"]
OUT = ROOT / "bugged"
OUT.mkdir(exist_ok=True)

for b in BUGS:
    bid = b["id"]
    if b["sub_old"] not in REF:
        print(f"WARN: {bid} sub_old not in REF: {b['sub_old'][:60]!r}")
        continue
    bugged = REF.replace(b["sub_old"], b["sub_new"], 1)
    if bugged == REF:
        print(f"WARN: {bid} no change after sub")
        continue
    (OUT / f"{bid}.py").write_text(bugged)
    print(f"OK {bid} {b['function']:20s} {b['category']:12s}  ({b['description'][:50]})")

print(f"\nGenerated {len(list(OUT.glob('B*.py')))} bugged files in {OUT}")
