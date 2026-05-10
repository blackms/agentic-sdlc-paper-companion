"""Inject 15 P7 bugs into jsonparse.py reference."""
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
REF = (ROOT / "ref" / "jsonparse.py").read_text()
BUGS = yaml.safe_load((ROOT / "bugs_p7.yaml").read_text())["bugs"]
OUT = ROOT / "bugged"
OUT.mkdir(exist_ok=True)

ok = 0
skipped = []
for b in BUGS:
    bid = b["id"]
    if b["sub_old"] not in REF:
        skipped.append((bid, "sub_old not in ref"))
        continue
    bugged = REF.replace(b["sub_old"], b["sub_new"], 1)
    if bugged == REF:
        skipped.append((bid, "no change"))
        continue
    (OUT / f"{bid}.py").write_text(bugged)
    ok += 1
    print(f"OK {bid:8s} {b['category']:15s} ({b['severity']:6s} {b['function']:18s}) {b['description'][:60]}")

print(f"\nGenerated {ok}/{len(BUGS)} bugged files")
for bid, reason in skipped:
    print(f"  SKIP {bid}: {reason}")
