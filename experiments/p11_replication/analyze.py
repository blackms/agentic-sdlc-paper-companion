"""P11 replication analyzer — Amendment A1 (saturation).

Inputs:
  - experiments/p11_replication/manifest.json
  - experiments/p11_replication/reviews/<side>_<cond>_<bid>.raw.txt
  - experiments/p11_replication/drift_diagnostic/<side>_truthful_v14_<bid>.raw.txt
  - v1.3 truthful reviewer outputs (for drift baseline):
      csv:      experiments/p9_real/csv_dom/reviews/cold_<bid>.raw.txt
      chardet:  experiments/p10_thirdparty/chardet_dom/reviews/cold_codex_<bid>.raw.txt
  - v1.3 detection.json (AST line/function ground truth):
      experiments/p9_real/csv_dom/detection.json
      experiments/p10_thirdparty/chardet_dom/detection.json
  - For v1.4-new bugs, detection.json must be derived from manifest.json
    (location -> line). Function-name match is best-effort against the
    reference module's AST.

Outputs:
  - experiments/p11_replication/results.json
  - experiments/p11_replication/drift_diagnostic.json
"""
from __future__ import annotations
import ast
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path
from math import comb, sqrt

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "experiments" / "p11_replication"

CSV_V13_REV = ROOT / "experiments/p9_real/csv_dom/reviews"
CHARDET_V13_REV = ROOT / "experiments/p10_thirdparty/chardet_dom/reviews"

# v1.3 op-keyword map (copied verbatim from experiments/p9_real/build_detection.py)
OP_KEYWORDS = {
    "Add": ["addition", "plus", "+ ", " + "],
    "Sub": ["subtract", "minus", "- ", " - "],
    "Mult": ["multipl", "*", "times"],
    "Div": ["divis", "/", "divide"],
    "FloorDiv": ["floor division", "//", "floordiv"],
    "Mod": ["modulo", "%", "mod "],
    "Eq": ["equal", "==", "equality"],
    "NotEq": ["not equal", "!=", "inequality"],
    "Lt": ["less than", "<", " lt "],
    "LtE": ["less or equal", "<=", " le "],
    "Gt": ["greater than", ">", " gt "],
    "GtE": ["greater or equal", ">=", " ge "],
    "And": ["and ", "logical and", "&&"],
    "Or": ["or ", "logical or", "||"],
}


def _parse_op_change(description: str) -> tuple[str, str]:
    parts = description.split()
    return parts[1], parts[3]
CSV_DETECTION = ROOT / "experiments/p9_real/csv_dom/detection.json"
CHARDET_DETECTION = ROOT / "experiments/p10_thirdparty/chardet_dom/detection.json"
CSV_REF = ROOT / "experiments/p9_real/csv_dom/ref/csv_module.py"
CHARDET_REF = ROOT / "experiments/p10_thirdparty/chardet_dom/ref/chardistribution_module.py"


# ---- JSON extraction (matches analyze_p11.py v1.3) ----

def extract_json(p: Path):
    if not p.exists() or p.stat().st_size == 0:
        return None
    text = p.read_text(errors="replace")
    cands = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    for m in re.finditer(r"\{[^{}]*\"bugs_found\"[^{}]*\}", text, re.DOTALL):
        cands.append(m.group(0))
    last = text.rfind("}")
    first = text.rfind("{", 0, last) if last >= 0 else -1
    if first >= 0:
        cands.append(text[first:last + 1])
    for c in cands:
        try:
            d = json.loads(c.strip())
            if isinstance(d, dict) and "bugs_found" in d:
                bugs = d["bugs_found"]
                if isinstance(bugs, list):
                    return [str(b) for b in bugs]
        except (json.JSONDecodeError, TypeError):
            continue
    return None


# ---- Detection ground truth ----

def line_function_map(ref_path: Path) -> dict[int, str]:
    """Map line numbers to enclosing function name in the reference module."""
    src = ref_path.read_text()
    tree = ast.parse(src)
    line_to_fn: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno + 1) or node.lineno + 1
            for ln in range(node.lineno, end + 1):
                line_to_fn[ln] = node.name
    return line_to_fn


def build_detection_index(side: str, manifest_side: dict) -> dict:
    """Return {bug_id: {"line": int, "function": str|None}} for ALL bugs on this side."""
    if side == "csv":
        det_v13 = json.loads(CSV_DETECTION.read_text())
        line_fn = line_function_map(CSV_REF)
    else:
        det_v13 = json.loads(CHARDET_DETECTION.read_text())
        line_fn = line_function_map(CHARDET_REF)
    # v1.3 detection.json shape: {"ref": "...", "bugs": [{bug_id, line, enclosing, op_keywords, ...}]}
    by_bid = {}
    if isinstance(det_v13, list):
        for entry in det_v13:
            by_bid[entry["bug_id"]] = entry
    elif isinstance(det_v13, dict):
        if "bugs" in det_v13:
            for entry in det_v13["bugs"]:
                by_bid[entry["bug_id"]] = entry
        else:
            by_bid = dict(det_v13)
    out = {}
    for row in manifest_side["rows"]:
        bid = row["bug_id"]
        if bid in out:
            continue
        if row["source"] == "v13_reused" and bid in by_bid:
            ent = by_bid[bid]
            out[bid] = {
                "line": int(ent["line"]),
                "function": ent.get("enclosing") or ent.get("function"),
                "op_keywords": ent.get("op_keywords", []),
            }
        else:
            ln = int(row["ast_location"][0])
            new_op = row.get("new_op_cls", "")
            old_op = _infer_original_op(
                CSV_REF if side == "csv" else CHARDET_REF,
                row["operator"], row["ast_location"], new_op,
            )
            kw = sorted(set(OP_KEYWORDS.get(old_op, []) + OP_KEYWORDS.get(new_op, [])))
            out[bid] = {
                "line": ln,
                "function": line_fn.get(ln),
                "op_keywords": kw,
            }
    return out


def _infer_original_op(ref_path: Path, op_cat: str, location, new_op_name: str) -> str:
    """Re-parse the ref module and find the original operator at the given AST
    location. AOR/BOR live on .op; ROR is in .ops list — we cannot uniquely pick
    an index from (line, col) alone (same Compare node can have multiple ops),
    so we fall back to the unique pair whose forward mutation lands on new_op_name.
    """
    try:
        src = ref_path.read_text()
        tree = ast.parse(src)
    except Exception:
        return ""
    target = tuple(location)
    if op_cat == "AOR":
        AOR_PAIRS_FWD = {"Add": "Sub", "Sub": "Add", "Mult": "Div", "Div": "Mult",
                          "FloorDiv": "Mod", "Mod": "FloorDiv"}
        for n in ast.walk(tree):
            if isinstance(n, ast.BinOp) and (n.lineno, n.col_offset) == target:
                old = type(n.op).__name__
                if AOR_PAIRS_FWD.get(old) == new_op_name:
                    return old
        return ""
    if op_cat == "BOR":
        for n in ast.walk(tree):
            if isinstance(n, ast.BoolOp) and (n.lineno, n.col_offset) == target:
                return type(n.op).__name__
        return ""
    if op_cat == "ROR":
        ROR_PAIRS_FWD = {"Eq": "NotEq", "NotEq": "Eq", "Lt": "LtE", "LtE": "Lt",
                          "Gt": "GtE", "GtE": "Gt"}
        for n in ast.walk(tree):
            if isinstance(n, ast.Compare) and (n.lineno, n.col_offset) == target:
                for op in n.ops:
                    old = type(op).__name__
                    if ROR_PAIRS_FWD.get(old) == new_op_name:
                        return old
        return ""
    return ""


def detects(bug_info: dict, found: list[str] | None) -> bool | None:
    """Detection criterion identical to v1.3 analyze_p11.py:
      hit if (line ± 2 numeric match) OR (enclosing-function AND op_keyword).

    Returns True/False, or None if the response was unparseable.
    """
    if found is None:
        return None
    text = " ||| ".join(b for b in found)
    text_l = text.lower()
    line = bug_info["line"]
    line_set = {line, line - 1, line + 1, line - 2, line + 2}
    if any(re.search(rf"\b{n}\b", text) for n in line_set):
        return True
    enc = (bug_info.get("function") or "").lower()
    op_keywords = bug_info.get("op_keywords") or []
    enc_hit = bool(enc) and enc in text_l
    op_hit = any(kw.lower() in text_l for kw in op_keywords)
    return enc_hit and op_hit


# ---- Stats ----

def mcnemar_exact_one_sided(b: int, c: int, direction: str) -> float:
    """Exact binomial paired McNemar, one-sided.

    direction: "relabeled_gt_truthful" → relabeled detects more (b = relabeled-only).
               "relabeled_lt_truthful" → truthful detects more (c = truthful-only).
    """
    n = b + c
    if n == 0:
        return 1.0
    if direction == "relabeled_gt_truthful":
        # P(B >= b | n, p=0.5)
        k = b
    elif direction == "relabeled_lt_truthful":
        # P(B <= b) where B is relabeled-only; equivalent P(C >= c)
        k = c
    else:
        raise ValueError(direction)
    p = sum(comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, max(0.0, p))


def wilson(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_robust_permutation(pairs: list[tuple[int, int]], direction: str,
                               n_perm: int = 20000, seed: int = 20260511) -> float:
    """One-sided paired permutation by sign-flip within each (truthful,
    relabeled) pair, cluster level = the bug (each pair = 1 cluster).

    pairs: list of (truthful_caught, relabeled_caught) in {0,1}.
    direction: "relabeled_gt_truthful" or "relabeled_lt_truthful".
    """
    rng = random.Random(seed)
    diffs = [r - t for t, r in pairs]
    obs = sum(diffs)
    count = 0
    for _ in range(n_perm):
        s = 0
        for d in diffs:
            s += d if rng.random() < 0.5 else -d
        if direction == "relabeled_gt_truthful":
            if s >= obs:
                count += 1
        else:
            if s <= obs:
                count += 1
    return (count + 1) / (n_perm + 1)


def bootstrap_ci_delta(pairs: list[tuple[int, int]], n_boot: int = 10000,
                       seed: int = 20260511):
    rng = random.Random(seed)
    n = len(pairs)
    if n == 0:
        return (0.0, 0.0, 0.0)
    obs_delta = (sum(r for _, r in pairs) - sum(t for t, _ in pairs)) / n
    deltas = []
    for _ in range(n_boot):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        d = (sum(r for _, r in sample) - sum(t for t, _ in sample)) / n
        deltas.append(d)
    deltas.sort()
    lo = deltas[int(0.025 * n_boot)]
    hi = deltas[int(0.975 * n_boot)]
    return (obs_delta, lo, hi)


def ks_two_sample(a: list[float], b: list[float]) -> tuple[float, float]:
    """Two-sample two-sided KS statistic + asymptotic p (Smirnov)."""
    a = sorted(a); b = sorted(b)
    na, nb = len(a), len(b)
    if na == 0 or nb == 0:
        return (0.0, 1.0)
    data_all = sorted(set(a + b))
    def cdf(arr, x):
        # count <= x
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] <= x:
                lo = mid + 1
            else:
                hi = mid
        return lo / len(arr)
    D = max(abs(cdf(a, x) - cdf(b, x)) for x in data_all)
    if D == 0.0:
        return (0.0, 1.0)
    en = math.sqrt(na * nb / (na + nb))
    # Asymptotic two-sided p
    lam = (en + 0.12 + 0.11 / en) * D
    s = 0.0
    for j in range(1, 101):
        s += (-1) ** (j - 1) * math.exp(-2 * (lam ** 2) * (j ** 2))
    p = max(0.0, min(1.0, 2 * s))
    return (D, p)


# ---- Verdict loaders ----

REVIEWS = EXP / "reviews"
DRIFT = EXP / "drift_diagnostic"


def load_pair(side: str, bid: str, det: dict) -> tuple[int | None, int | None]:
    """Return (truthful, relabeled) detection in {0,1,None}."""
    tf = extract_json(REVIEWS / f"{side}_truthful_{bid}.raw.txt")
    rf = extract_json(REVIEWS / f"{side}_relabeled_{bid}.raw.txt")
    td = detects(det[bid], tf)
    rd = detects(det[bid], rf)
    return (None if td is None else int(td), None if rd is None else int(rd))


def load_v13_truthful(side: str, bid: str, det: dict) -> int | None:
    if side == "csv":
        p = CSV_V13_REV / f"cold_{bid}.raw.txt"
    else:
        p = CHARDET_V13_REV / f"cold_codex_{bid}.raw.txt"
    out = extract_json(p)
    d = detects(det[bid], out)
    return None if d is None else int(d)


def load_v14_drift(side: str, bid: str, det: dict) -> int | None:
    out = extract_json(DRIFT / f"{side}_truthful_v14_{bid}.raw.txt")
    d = detects(det[bid], out)
    return None if d is None else int(d)


def analyze_side(side: str, manifest_side: dict, direction: str) -> dict:
    det = build_detection_index(side, manifest_side)
    pairs = []          # all rows
    pairs_v13 = []      # 30 v13_reused
    pairs_v14 = []      # v14_new only
    parse_fail = 0
    unique_bids = []
    for row in manifest_side["rows"]:
        bid = row["bug_id"]
        if bid in unique_bids:
            continue
        unique_bids.append(bid)
        t, r = load_pair(side, bid, det)
        if t is None or r is None:
            parse_fail += 1
            continue
        pairs.append((t, r))
        if row["source"] == "v13_reused":
            pairs_v13.append((t, r))
        else:
            pairs_v14.append((t, r))

    def cell_stats(prs: list[tuple[int, int]]):
        n = len(prs)
        if n == 0:
            return None
        # contingency
        a = sum(1 for t, r in prs if t == 1 and r == 1)
        b = sum(1 for t, r in prs if t == 0 and r == 1)
        c = sum(1 for t, r in prs if t == 1 and r == 0)
        d = sum(1 for t, r in prs if t == 0 and r == 0)
        truthful_rate = (a + c) / n
        relabeled_rate = (a + b) / n
        delta_pct = (relabeled_rate - truthful_rate) * 100.0
        mcnemar_p = mcnemar_exact_one_sided(b, c, direction)
        perm_p = cluster_robust_permutation(prs, direction)
        d_obs, lo, hi = bootstrap_ci_delta(prs)
        return {
            "n_pairs": n,
            "contingency_a_t1r1": a,
            "contingency_b_t0r1": b,
            "contingency_c_t1r0": c,
            "contingency_d_t0r0": d,
            "truthful_rate": truthful_rate,
            "relabeled_rate": relabeled_rate,
            "delta_pp": delta_pct,
            "delta_bootstrap_obs_pp": d_obs * 100,
            "delta_bootstrap_ci95_pp": [lo * 100, hi * 100],
            "mcnemar_exact_one_sided_p": mcnemar_p,
            "cluster_perm_p_n20000": perm_p,
            "wilson95_truthful": wilson(a + c, n),
            "wilson95_relabeled": wilson(a + b, n),
        }

    return {
        "side": side,
        "direction": direction,
        "n_unique_bugs": len(unique_bids),
        "parse_failures": parse_fail,
        "all": cell_stats(pairs),
        "v13_reused": cell_stats(pairs_v13),
        "v14_new": cell_stats(pairs_v14),
    }


def per_bug_truthful_rate(prs: list[tuple[int, int]]) -> list[float]:
    return [t for t, _ in prs]


def drift_analysis(side: str, manifest_side: dict) -> dict:
    det = build_detection_index(side, manifest_side)
    v13_only = [row for row in manifest_side["rows"] if row["source"] == "v13_reused"]
    seen = set()
    pairs = []  # (v13_truthful, v14_truthful) for the 30 reused bugs
    parse_fail = 0
    for row in v13_only:
        bid = row["bug_id"]
        if bid in seen:
            continue
        seen.add(bid)
        a = load_v13_truthful(side, bid, det)
        b = load_v14_drift(side, bid, det)
        if a is None or b is None:
            parse_fail += 1
            continue
        pairs.append((a, b))
    n = len(pairs)
    if n == 0:
        return {"side": side, "n_pairs": 0, "parse_failures": parse_fail}
    a11 = sum(1 for x, y in pairs if x == 1 and y == 1)
    b01 = sum(1 for x, y in pairs if x == 0 and y == 1)
    c10 = sum(1 for x, y in pairs if x == 1 and y == 0)
    d00 = sum(1 for x, y in pairs if x == 0 and y == 0)
    v13_rate = (a11 + c10) / n
    v14_rate = (a11 + b01) / n
    delta_pct = (v14_rate - v13_rate) * 100
    # Two-sided McNemar = two one-sided p-values; report both directions
    p_up = mcnemar_exact_one_sided(b01, c10, "relabeled_gt_truthful")  # v14 > v13
    p_down = mcnemar_exact_one_sided(b01, c10, "relabeled_lt_truthful")  # v14 < v13
    return {
        "side": side,
        "n_pairs": n,
        "parse_failures": parse_fail,
        "v13_truthful_rate": v13_rate,
        "v14_truthful_rate": v14_rate,
        "delta_pp_v14_minus_v13": delta_pct,
        "contingency": {"a_v13y_v14y": a11, "b_v13n_v14y": b01,
                         "c_v13y_v14n": c10, "d_v13n_v14n": d00},
        "mcnemar_p_v14_gt_v13": p_up,
        "mcnemar_p_v14_lt_v13": p_down,
        "magnitude_abs_pp": abs(delta_pct),
    }


def per_bug_detection_rates(prs: list[tuple[int, int]], idx: int) -> list[int]:
    """Per-bug detection (0 or 1) for cell `idx` (0=truthful, 1=relabeled)."""
    return [p[idx] for p in prs]


def ks_distributions(side: str, manifest_side: dict, cell_res: dict) -> dict:
    """KS on per-bug truthful detection rates: v13_reused vs v14_new."""
    det = build_detection_index(side, manifest_side)
    v13_t = []
    v14_t = []
    seen = set()
    for row in manifest_side["rows"]:
        bid = row["bug_id"]
        if bid in seen:
            continue
        seen.add(bid)
        t, r = load_pair(side, bid, det)
        if t is None:
            continue
        if row["source"] == "v13_reused":
            v13_t.append(t)
        else:
            v14_t.append(t)
    D_t, p_t = ks_two_sample(v13_t, v14_t)
    return {
        "side": side,
        "n_v13_reused": len(v13_t),
        "n_v14_new": len(v14_t),
        "v13_truthful_mean": sum(v13_t) / len(v13_t) if v13_t else None,
        "v14_truthful_mean": sum(v14_t) / len(v14_t) if v14_t else None,
        "ks_D_truthful": D_t,
        "ks_p_truthful": p_t,
    }


def main():
    manifest = json.loads((EXP / "manifest.json").read_text())
    # H1a (csv): relabeled (third-party label) > truthful (stdlib) → +
    csv_result = analyze_side("csv", manifest["csv"], direction="relabeled_gt_truthful")
    # H1b (chardet): relabeled (stdlib label) < truthful (third-party) → −
    chardet_result = analyze_side("chardet", manifest["chardet"],
                                  direction="relabeled_lt_truthful")

    # KS on per-bug truthful detection: v13_reused vs v14_new
    csv_ks = ks_distributions("csv", manifest["csv"], csv_result)
    chardet_ks = ks_distributions("chardet", manifest["chardet"], chardet_result)

    # Decision rule (per pre-reg; α = 0.025 per cell Bonferroni)
    def verdict(side: dict, alpha: float = 0.025) -> str:
        cell = side["all"]
        if cell is None:
            return "no_data"
        p = cell["mcnemar_exact_one_sided_p"]
        delta = cell["delta_pp"]
        sign_ok = (
            (side["direction"] == "relabeled_gt_truthful" and delta > 0)
            or (side["direction"] == "relabeled_lt_truthful" and delta < 0)
        )
        if p < alpha and sign_ok:
            return "H1_supported"
        if p < alpha and not sign_ok:
            return "sign_reversal_HALT6"
        return "null_not_rejected"

    # Halt #6 check vs v1.3 directional trend.
    # v1.3 P11 results (from experiments/p11_provenance/results or analyze_p11):
    # We compare sign of v1.4 delta against v1.3 sign.
    v13_trends = {
        "csv": "positive_or_zero",     # v1.3 Δ ~ 0..+6pp (no significant effect; trend mild positive)
        "chardet": "negative_or_zero",  # v1.3 Δ ~ 0..−10pp (mild negative)
    }
    def halt6_check(side_name: str, side_result: dict) -> dict:
        cell = side_result["all"]
        if cell is None:
            return {"flip_vs_v13": False, "v14_delta_pp": None}
        delta = cell["delta_pp"]
        expected = side_result["direction"]
        # FLIP if v1.4 is significant AND opposite-sign to v1.3 trend.
        p = cell["mcnemar_exact_one_sided_p"]
        sig = p < 0.025
        # opposite direction:
        v13_sign = v13_trends[side_name]
        flip = False
        if sig:
            if v13_sign == "positive_or_zero" and delta < 0:
                flip = True
            if v13_sign == "negative_or_zero" and delta > 0:
                flip = True
        return {"flip_vs_v13": flip, "v14_delta_pp": delta, "v14_mcnemar_p": p,
                "v13_trend": v13_sign, "halt6_triggered": flip}

    out = {
        "amendment": "A1",
        "alpha_per_cell": 0.025,
        "csv": csv_result,
        "chardet": chardet_result,
        "ks": {"csv": csv_ks, "chardet": chardet_ks},
        "verdict": {
            "csv_H1a": verdict(csv_result),
            "chardet_H1b": verdict(chardet_result),
        },
        "halt6": {
            "csv": halt6_check("csv", csv_result),
            "chardet": halt6_check("chardet", chardet_result),
        },
    }
    (EXP / "results.json").write_text(json.dumps(out, indent=2))
    print(f"wrote {EXP / 'results.json'}")

    drift = {
        "amendment": "A1",
        "description": "v1.3 truthful (Codex output on disk) vs v1.4 truthful re-run on the same 30 v1.3-reused bugs per side.",
        "csv": drift_analysis("csv", manifest["csv"]),
        "chardet": drift_analysis("chardet", manifest["chardet"]),
    }
    (EXP / "drift_diagnostic.json").write_text(json.dumps(drift, indent=2))
    print(f"wrote {EXP / 'drift_diagnostic.json'}")


if __name__ == "__main__":
    main()
