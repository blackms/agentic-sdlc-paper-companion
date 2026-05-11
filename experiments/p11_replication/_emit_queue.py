"""Emit the work queue for launch_p11_replication.sh.

Usage:
  python3 _emit_queue.py main    # 226 lines: <side>|<cond>|<bid>|<src>|<bugged_path>
  python3 _emit_queue.py drift   # 60 lines:  <side>|truthful_v14|<bid>|v13_reused|<bugged_path>
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def main(kind: str) -> int:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "experiments" / "p11_replication" / "manifest.json").read_text())
    seen = set()
    if kind == "main":
        for side_key in ("csv", "chardet"):
            for row in manifest[side_key]["rows"]:
                bid = row["bug_id"]
                key = (side_key, bid)
                if key in seen:
                    continue
                seen.add(key)
                for cond in ("truthful", "relabeled"):
                    print(f"{side_key}|{cond}|{bid}|{row['source']}|{row['bugged_path']}")
    elif kind == "drift":
        for side_key in ("csv", "chardet"):
            for row in manifest[side_key]["rows"]:
                if row["source"] != "v13_reused":
                    continue
                bid = row["bug_id"]
                key = (side_key, bid)
                if key in seen:
                    continue
                seen.add(key)
                print(f"{side_key}|truthful_v14|{bid}|v13_reused|{row['bugged_path']}")
    else:
        print(f"unknown kind: {kind}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "main"))
