"""Redact LLM raw review transcripts to protect framework IP.

Each `experiments/**/reviews/*.raw.txt` originally contains, in order:
  1. Codex/Gemini/Claude CLI session metadata (workdir, model id, sandbox config)
  2. The full reviewer **prompt** — including the framework's cold/warm/skeptic
     protocol bodies and the auto-extracted domain contracts (this is IP)
  3. The LLM response, formatted as a fenced JSON block:
       {"bugs_found": [...], "verdict": "ACCEPT" | "REQUEST_CHANGES"}

For the public Companion Repository, we keep only step 3 (the experimental
datum). Steps 1 and 2 are dropped. The original-file SHA-256 and byte length
are recorded in a per-domain `reviews_summary.jsonl` so peer reviewers can
verify that the redacted JSON corresponds to a specific original transcript
held by the author.

The analyzer scripts (`analyze_p9.py`, `analyze_p10.py`, ...) only consume the
JSON `bugs_found` block via regex, so they continue to work unchanged on the
redacted files.

Usage:
    python3 tools/redact_reviews.py [--dry-run] [--sample N] [path ...]

With no path arguments, walks the whole `experiments/` tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

# Two analyzer families produce results.json files in the repo, and they
# differ in JSON extraction. To preserve the frozen baseline (paper v1.4.3)
# byte-for-byte under RERUN=1, the redactor matches each analyzer exactly.
_FENCED = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_INLINE_P9 = re.compile(r"\{[^{}]*\"bugs_found\"[^{}]*\}", re.DOTALL)

# Prompt-template fragments — only used by naturalistic_csv extraction.
_PROMPT_TEMPLATE_FRAGMENTS = (
    '"short description 1"',
    '"ACCEPT" | "REQUEST_CHANGES"',
)


def _find_balanced_json_objects(text: str):
    n = len(text)
    i = 0
    while i < n:
        if text[i] == "{":
            depth = 1
            j = i + 1
            in_str = False
            esc = False
            while j < n and depth > 0:
                c = text[j]
                if in_str:
                    if esc:
                        esc = False
                    elif c == "\\":
                        esc = True
                    elif c == '"':
                        in_str = False
                elif c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                yield text[i:j]
                i = j
                continue
        i += 1


def _extract_p9_style(text: str) -> dict | None:
    """Byte-identical port of experiments/p9_real/analyze_p9.py::extract_json
    (also used by p10/p11/p7/p8/etc.)."""
    candidates: list[str] = []
    candidates.extend(_FENCED.findall(text))
    candidates.extend(m.group(0) for m in _INLINE_P9.finditer(text))
    last = text.rfind("}")
    first = text.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        candidates.append(text[first : last + 1])
    for cand in candidates:
        try:
            data = json.loads(cand.strip())
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, dict) and "bugs_found" in data:
            bugs = data["bugs_found"]
            if isinstance(bugs, list):
                return {
                    "bugs_found": [str(b) for b in bugs],
                    "verdict": data.get("verdict"),
                }
    return None


def _extract_naturalistic_style(text: str) -> dict | None:
    """Byte-identical port of experiments/naturalistic_csv/analyze.py::extract_json.

    Naturalistic prompts contain the JSON schema template as a string literal;
    Codex echoes the prompt back to stdout, so the template appears as a
    candidate JSON object. We skip those candidates by string match, then
    take the LAST successfully-parsed candidate (Codex sometimes emits both
    a partial and a final JSON in the same response).
    """
    cands: list[str] = []
    cands.extend(_FENCED.findall(text))
    cands.extend(_find_balanced_json_objects(text))
    best: dict | None = None
    for c in cands:
        s = c.strip()
        if any(frag in s for frag in _PROMPT_TEMPLATE_FRAGMENTS):
            continue
        try:
            d = json.loads(s)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(d, dict) and "bugs_found" in d:
            bugs = d["bugs_found"]
            if isinstance(bugs, list):
                best = {
                    "bugs_found": [str(b) for b in bugs],
                    "verdict": d.get("verdict"),
                }
    return best


def extract_response(text: str, *, raw_path: Path) -> dict | None:
    """Dispatch to the same extractor the file's owning analyzer uses, so
    that running validate_all.sh with RERUN=1 produces byte-identical
    results.json files to the frozen v1.4.3 baseline."""
    if "naturalistic_csv" in raw_path.parts:
        return _extract_naturalistic_style(text)
    return _extract_p9_style(text)


def sha256(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


# Citation patterns the Phase-12 leakage probe analyzer scans for
# (mirrors experiments/naturalistic_csv/analyze.py::PROBE_CITE_RE).
# These tokens MUST survive redaction in naturalistic probe files,
# otherwise the leakage diagnostic regenerates to 0% and the paper's
# 100% Codex leakage caveat in §8.11 becomes unverifiable.
_PROBE_CITE_RE = re.compile(
    r"(gh-?\d{4,7}|bpo-?\d{4,7}|#\s?\d{4,7})", re.IGNORECASE
)


def _extract_probe_citations(text: str) -> list[str]:
    """All CPython issue citations (gh-NNNNN, bpo-NNNNN, #NNNNN) found in
    the probe transcript text, in order of first appearance."""
    seen: list[str] = []
    for m in _PROBE_CITE_RE.finditer(text):
        tok = m.group(0)
        if tok not in seen:
            seen.append(tok)
    return seen


def parse_filename(name: str) -> dict:
    """Extract role/condition/family/bug_id from `<role>(_<cond>)?(_<family>)?_<bug_id>.raw.txt`.

    Robust to:
      cold_P9c_B01                         -> role=cold,            family=codex,    cond=aligned
      cold_mismatched_P9c_B22              -> role=cold,            family=codex,    cond=mismatched
      cold_opus_P9c_B27                    -> role=cold,            family=opus,     cond=aligned
      cold_mismatched_opus_P9c_B22         -> role=cold,            family=opus,     cond=mismatched
      cold_gemini31_P9c_B05                -> role=cold,            family=gemini31, cond=aligned
      skeptic_P9c_B21                      -> role=skeptic,         family=codex,    cond=na
      warm_P9c_B04                         -> role=warm,            family=codex,    cond=na
      simm1_P9c_B04                        -> role=simm1,           family=codex,    cond=na
    Unknown patterns return tokens as-is in `tokens`.
    """
    stem = name.removesuffix(".raw.txt")
    parts = stem.split("_")
    out: dict = {"role": None, "condition": "na", "family": "codex", "bug_id": None, "tokens": parts}
    # bug_id is the last 1 or 2 tokens (e.g. "P9c_B01" -> ["P9c","B01"])
    if len(parts) >= 2 and re.match(r"^B\d+", parts[-1]) and parts[-2].startswith("P"):
        out["bug_id"] = f"{parts[-2]}_{parts[-1]}"
        prefix = parts[:-2]
    else:
        out["bug_id"] = parts[-1]
        prefix = parts[:-1]
    families = {"opus", "gemini31", "gemini25", "sonnet", "codex"}
    conditions = {"mismatched", "aligned", "relabel", "relabeled", "truth", "truthful"}
    role_tokens = []
    for tok in prefix:
        if tok in families:
            out["family"] = tok
        elif tok in conditions:
            out["condition"] = "mismatched" if tok == "mismatched" else tok
        else:
            role_tokens.append(tok)
    out["role"] = "_".join(role_tokens) if role_tokens else None
    if out["role"] == "cold" and out["condition"] == "na":
        out["condition"] = "aligned"
    return out


def redact_one(raw_path: Path, *, dry_run: bool) -> dict:
    original = raw_path.read_bytes()
    text = original.decode("utf-8", errors="replace")
    meta = parse_filename(raw_path.name)
    resp = extract_response(text, raw_path=raw_path)
    is_probe = "naturalistic_csv" in raw_path.parts and "probe" in raw_path.parts
    citations = _extract_probe_citations(text) if is_probe else []
    record = {
        "file": raw_path.name,
        "role": meta["role"],
        "condition": meta["condition"],
        "family": meta["family"],
        "bug_id": meta["bug_id"],
        "raw_sha256": sha256(original),
        "raw_bytes": len(original),
        "extracted_ok": resp is not None,
    }
    if resp is None:
        record["verdict"] = None
        record["bugs_found_len"] = 0
    else:
        record["verdict"] = resp.get("verdict")
        record["bugs_found_len"] = len(resp.get("bugs_found", []))
    if is_probe:
        record["probe_citations"] = citations
    if not dry_run:
        header = (
            f"// raw_sha256={record['raw_sha256']}\n"
            f"// raw_bytes={record['raw_bytes']}\n"
        )
        # Probe transcripts MUST keep their CPython issue citations so the
        # leakage-diagnostic analyzer can find them. We preserve every
        # distinct citation token in a comment line scanned by
        # naturalistic_csv/analyze.py::parse_probe.
        if is_probe and citations:
            header += "// probe_citations: " + " ".join(citations) + "\n"
        if resp is None:
            new_content = (
                "// REDACTED — no JSON response with bugs_found could be extracted.\n"
                + header
            )
        else:
            new_content = (
                header
                + "```json\n"
                + json.dumps(resp, ensure_ascii=False)
                + "\n```\n"
            )
        raw_path.write_text(new_content)
    return record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sample", type=int, default=0, help="Process only N random files")
    ap.add_argument("paths", nargs="*", default=["experiments"])
    args = ap.parse_args()

    files: list[Path] = []
    for root in args.paths:
        files.extend(Path(root).rglob("*.raw.txt"))
    if args.sample > 0 and len(files) > args.sample:
        random.seed(20260524)
        files = random.sample(files, args.sample)

    by_dir: dict[Path, list[dict]] = {}
    n_ok = 0
    n_fail = 0
    for f in files:
        rec = redact_one(f, dry_run=args.dry_run)
        by_dir.setdefault(f.parent, []).append(rec)
        if rec["extracted_ok"]:
            n_ok += 1
        else:
            n_fail += 1

    if not args.dry_run:
        for d, recs in by_dir.items():
            out = d / "reviews_summary.jsonl"
            with out.open("w") as fh:
                for rec in recs:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"processed: {len(files)}  extracted_ok: {n_ok}  failed: {n_fail}")
    if n_fail and args.dry_run:
        print("\nFailures (sample of 10):")
        for d, recs in by_dir.items():
            for rec in recs:
                if not rec["extracted_ok"]:
                    print(f"  {d}/{rec['file']}  sha256={rec['raw_sha256'][:12]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
