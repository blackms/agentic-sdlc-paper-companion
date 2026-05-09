"""Inject 30 E2 bugs into bankcheck.py reference, producing E2_B01.py..E2_B30.py."""
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
REF = (ROOT / "ref" / "bankcheck.py").read_text()
BUGS = yaml.safe_load((ROOT / "bugs_e2.yaml").read_text())["bugs"]
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
    print(f"OK {bid:8s} {b['category']:22s} ({b['severity']}, {b['function']:30s}) {b['description'][:60]}")

print()
print(f"Generated {ok}/{len(BUGS)} bugged files in {OUT}")
if skipped:
    print(f"Skipped {len(skipped)}:")
    for bid, reason in skipped:
        print(f"  {bid}: {reason}")
