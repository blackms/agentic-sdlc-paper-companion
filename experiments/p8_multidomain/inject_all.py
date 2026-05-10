"""Inject bugs in all 3 P8 domains."""
import yaml
from pathlib import Path

ROOT = Path(__file__).parent
DOMAINS = [
    ("exprev",  "exprev.py"),
    ("regex",   "regex_compile.py"),
    ("httphdr", "httphdr.py"),
]

for domain, ref_filename in DOMAINS:
    print(f"\n=== {domain} ===")
    dom_root = ROOT / domain
    ref = (dom_root / "ref" / ref_filename).read_text()
    bugs = yaml.safe_load((dom_root / "bugs.yaml").read_text())["bugs"]
    out = dom_root / "bugged"
    out.mkdir(exist_ok=True)
    ok = 0
    skipped = []
    for b in bugs:
        bid = b["id"]
        if b["sub_old"] not in ref:
            skipped.append((bid, "sub_old not found"))
            continue
        bugged = ref.replace(b["sub_old"], b["sub_new"], 1)
        if bugged == ref:
            skipped.append((bid, "no change"))
            continue
        (out / f"{bid}.py").write_text(bugged)
        ok += 1
        print(f"  OK {bid:10s} {b['category']:13s} {b['severity']:6s} {b['description'][:55]}")
    print(f"  {ok}/{len(bugs)} bugged files generated")
    if skipped:
        for bid, reason in skipped:
            print(f"  SKIP {bid}: {reason}")
