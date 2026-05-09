"""Aggregate metrics across 12 runs and compute eta, Pred_C, Pred_S, H_emp."""
import json
import math
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent))
import oracle_T1
import oracle_T2

ROOT = Path(__file__).parent.parent
RUNS = ROOT / "runs"
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

ORACLES = {"compound_interest": oracle_T1, "transfer": oracle_T2}


def token_count(filepath):
    """Proxy: char_count of raw output / 4 (tokens approx)."""
    raw = Path(filepath).read_text() if Path(filepath).exists() else ""
    return len(raw) / 4


def discretize(v, kind):
    if kind in ("correctness", "robustness"):
        if v == 0:
            return "0"
        if v <= 0.5:
            return "low"
        if v <= 0.9:
            return "mid"
        return "high"
    if kind == "conformance":
        return f"c{int(round(v))}"
    return str(v)


def shannon(buckets):
    n = sum(buckets.values())
    if n == 0:
        return 0.0
    H = 0.0
    for c in buckets.values():
        if c == 0:
            continue
        p = c / n
        H -= p * math.log2(p)
    K = sum(1 for c in buckets.values() if c > 0)
    miller_madow = (K - 1) / (2 * n * math.log(2)) if n > 1 else 0
    return H + miller_madow


def main():
    runs = []
    candidates = (list(RUNS.glob("codex_*.raw.txt"))
                  + list(RUNS.glob("claude_*.py"))
                  + list(RUNS.glob("opus_*.py"))
                  + list(RUNS.glob("gemini_*.raw.txt")))
    # For codex/gemini, we have raw.txt + .py. For claude/opus, only .py (subagent saved directly).
    seen = set()
    for f in sorted(candidates):
        if f.name.endswith(".raw.txt"):
            stem = f.stem.replace(".raw", "")
            if f.name.startswith("codex_"):
                model = "codex"
            elif f.name.startswith("gemini_"):
                model = "gemini"
            else:
                continue
        elif f.name.endswith(".py"):
            stem = f.stem
            if f.name.startswith("claude_"):
                model = "claude"
            elif f.name.startswith("opus_"):
                model = "opus"
            else:
                continue
        else:
            continue
        if stem in seen:
            continue
        seen.add(stem)
        parts = stem.split("_")
        # codex_compound_interest_P_1 / claude_compound_interest_P_1
        if parts[1] == "compound" and parts[2] == "interest":
            task = "compound_interest"
            cond = parts[3]
            run = parts[4]
        else:
            task = parts[1]
            cond = parts[2]
            run = parts[3]
        py = RUNS / f"{stem}.py"
        raw = RUNS / f"{stem}.raw.txt" if model == "codex" else py  # fallback
        oracle = ORACLES[task]
        if not py.exists() or py.stat().st_size < 50:
            row = {"task": task, "cond": cond, "run": run, "model": model, "valid_py": False,
                   "conformance": 0, "correctness": 0.0, "robustness": 0.0,
                   "tokens": token_count(raw if raw.exists() else py)}
        else:
            try:
                conf, conf_det = oracle.conformance(str(py))
            except Exception as e:
                conf = 0
                conf_det = {"error": str(e)}
            try:
                cor, cor_det = oracle.correctness(str(py))
            except Exception as e:
                cor = 0.0
                cor_det = [("err", str(e))]
            try:
                rob, rob_det = oracle.robustness(str(py))
            except Exception as e:
                rob = 0.0
                rob_det = []
            row = {"task": task, "cond": cond, "run": run, "model": model, "valid_py": True,
                   "conformance": conf, "correctness": cor, "robustness": rob,
                   "tokens": token_count(raw if raw.exists() else py),
                   "conf_indicators": conf_det if isinstance(conf_det, dict) else {}}
        runs.append(row)

    # Save raw runs
    (RESULTS / "runs.json").write_text(json.dumps(runs, indent=2))

    # Aggregate per (task, cond, model)
    cells = defaultdict(list)
    for r in runs:
        cells[(r["task"], r["cond"], r.get("model", "codex"))].append(r)

    summary = []
    for (task, cond, model), rs in sorted(cells.items()):
        if not rs:
            continue
        n = len(rs)
        avg_conf = sum(r["conformance"] for r in rs) / n
        avg_cor = sum(r["correctness"] for r in rs) / n
        avg_rob = sum(r["robustness"] for r in rs) / n
        avg_tok = sum(r["tokens"] for r in rs) / n
        # Empirical entropy on each component
        H_components = {}
        for comp in ("correctness", "robustness", "conformance"):
            buckets = defaultdict(int)
            for r in rs:
                buckets[discretize(r[comp], comp)] += 1
            H_components[comp] = shannon(buckets)
        # H of joint behavioral signature
        joint = defaultdict(int)
        for r in rs:
            key = (discretize(r["correctness"], "correctness"),
                   discretize(r["robustness"], "robustness"),
                   discretize(r["conformance"], "conformance"))
            joint[key] += 1
        H_joint = shannon(joint)
        summary.append({"task": task, "cond": cond, "model": model, "n": n,
                        "avg_conformance": avg_conf, "avg_correctness": avg_cor,
                        "avg_robustness": avg_rob, "avg_tokens": avg_tok,
                        "H_correctness": H_components["correctness"],
                        "H_robustness": H_components["robustness"],
                        "H_conformance": H_components["conformance"],
                        "H_joint": H_joint})

    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2))

    # Compute eta per (task, model)
    eta_table = []
    keys = sorted({(s["task"], s["model"]) for s in summary})
    for task, model in keys:
        s0 = next((s for s in summary if s["task"] == task and s["cond"] == "P0" and s["model"] == model), None)
        sP = next((s for s in summary if s["task"] == task and s["cond"] == "P" and s["model"] == model), None)
        if not s0 or not sP:
            continue
        dH_joint = s0["H_joint"] - sP["H_joint"]
        dH_cor = s0["H_correctness"] - sP["H_correctness"]
        dH_rob = s0["H_robustness"] - sP["H_robustness"]
        dK = sP["avg_tokens"] - s0["avg_tokens"]
        eta_joint = dH_joint / dK if dK != 0 else None
        d_cor = sP["avg_correctness"] - s0["avg_correctness"]
        d_rob = sP["avg_robustness"] - s0["avg_robustness"]
        d_conf = sP["avg_conformance"] - s0["avg_conformance"]
        eta_table.append({"task": task, "model": model,
                          "delta_H_joint": dH_joint,
                          "delta_H_correctness": dH_cor,
                          "delta_H_robustness": dH_rob,
                          "delta_K_tokens": dK,
                          "eta_joint_per_token": eta_joint,
                          "delta_avg_correctness": d_cor,
                          "delta_avg_robustness": d_rob,
                          "delta_avg_conformance": d_conf,
                          "Pred_C_P0": s0["avg_conformance"], "Pred_C_P": sP["avg_conformance"],
                          "Pred_S_P0_correctness": s0["avg_correctness"], "Pred_S_P_correctness": sP["avg_correctness"],
                          "Pred_S_P0_robustness": s0["avg_robustness"], "Pred_S_P_robustness": sP["avg_robustness"]})

    (RESULTS / "eta.json").write_text(json.dumps(eta_table, indent=2))

    # Pretty print
    print("=" * 80)
    print(f"PILOT PHASE 2 — n={len(runs)} runs (Codex-only, downscaled from 24 to 12)")
    print("=" * 80)
    print()
    print("Per-cell summary:")
    for s in summary:
        print(f"  task={s['task']:18s} cond={s['cond']:3s} model={s['model']:6s}  n={s['n']}  "
              f"conf={s['avg_conformance']:.2f}/5  cor={s['avg_correctness']:.2f}  "
              f"rob={s['avg_robustness']:.2f}  tok≈{s['avg_tokens']:.0f}  "
              f"H_joint={s['H_joint']:.3f}")
    print()
    print("Eta tradeoff per (task, model):")
    for e in eta_table:
        print(f"  task={e['task']:18s} model={e['model']}")
        print(f"    ΔH_joint={e['delta_H_joint']:+.3f}  "
              f"ΔH_correctness={e['delta_H_correctness']:+.3f}  "
              f"ΔH_robustness={e['delta_H_robustness']:+.3f}")
        print(f"    ΔK_tokens={e['delta_K_tokens']:+.0f}  "
              f"η_joint/token={e['eta_joint_per_token']:.6f}" if e['eta_joint_per_token'] else "    η undefined")
        print(f"    Pred_C: {e['Pred_C_P0']:.2f} → {e['Pred_C_P']:.2f}  (Δ={e['delta_avg_conformance']:+.2f})")
        print(f"    Pred_S(correctness): {e['Pred_S_P0_correctness']:.2f} → {e['Pred_S_P_correctness']:.2f}  (Δ={e['delta_avg_correctness']:+.2f})")
        print(f"    Pred_S(robustness):  {e['Pred_S_P0_robustness']:.2f} → {e['Pred_S_P_robustness']:.2f}  (Δ={e['delta_avg_robustness']:+.2f})")
    print()
    print(f"Files: {RESULTS}/runs.json summary.json eta.json")


if __name__ == "__main__":
    main()
