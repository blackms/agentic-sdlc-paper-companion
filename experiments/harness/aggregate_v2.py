"""Aggregate v2 — applica metriche di Codex R4 (expected utility + V).

T1'' (Codex-approved):  E_P[u(B)] > E_P0[u(B)]  con
    u(b) = α·correctness + β·robustness + γ·conformance/5,  α+β+γ = 1.

G(P; P_0) = ΔE[u] / log(K_P / K_P0)         efficienza per costo
V(P; P_0) = ΔE[u] − λ · log(K_P / K_P0)     beneficio netto decisionale
"""
import json
import math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
runs = json.loads((RESULTS / "runs.json").read_text())

# Pesi della utility — ugual peso fra le tre componenti
ALPHA = BETA = GAMMA = 1 / 3
LAMBDA = 0.5  # peso del costo nella V


def utility(r):
    return ALPHA * r["correctness"] + BETA * r["robustness"] + GAMMA * (r["conformance"] / 5.0)


cells = defaultdict(list)
for r in runs:
    cells[(r["task"], r["cond"], r.get("model", "codex"))].append(r)

print("=" * 80)
print("METRICHE V2 — T1'' (Codex-approved expected-utility form) + G + V")
print("=" * 80)
print(f"u(b) = {ALPHA:.3f}·correctness + {BETA:.3f}·robustness + {GAMMA:.3f}·conf/5")
print(f"V(P;P0) = ΔE[u] − λ·log(K_P/K_P0)   con λ = {LAMBDA}")
print()

per_cell = {}
for (task, cond, model), rs in sorted(cells.items()):
    n = len(rs)
    Eu = sum(utility(r) for r in rs) / n
    Etok = sum(r["tokens"] for r in rs) / n
    # bootstrap CI95 of E[u]
    import random
    boots = []
    rng = random.Random(0)
    for _ in range(1000):
        s = [utility(rs[rng.randrange(n)]) for _ in range(n)]
        boots.append(sum(s) / n)
    boots.sort()
    ci_lo, ci_hi = boots[25], boots[975]
    per_cell[(task, cond, model)] = (Eu, Etok, n, ci_lo, ci_hi)
    print(f"  {task:18s} {cond:3s} {model:6s}  n={n}  "
          f"E[u]={Eu:.3f} [95%CI {ci_lo:.3f}–{ci_hi:.3f}]  E[K]={Etok:.0f}")

print()
print("Tradeoff per (task, model):")
results_v2 = []
keys = sorted({(t, m) for t, _, m in per_cell})
for task, model in keys:
    Eu0, K0, _, _, _ = per_cell[(task, "P0", model)]
    EuP, KP, _, _, _ = per_cell[(task, "P", model)]
    dEu = EuP - Eu0
    log_ratio = math.log(KP / K0)
    G = dEu / log_ratio if log_ratio > 0 else None
    V = dEu - LAMBDA * log_ratio
    print(f"  task={task}, model={model}")
    print(f"    E[u | P0] = {Eu0:.3f}    E[u | P] = {EuP:.3f}    ΔE[u] = {dEu:+.3f}")
    print(f"    log(K_P/K_P0) = {log_ratio:.3f}    K_P = {KP:.0f}    K_P0 = {K0:.0f}")
    if G is not None:
        print(f"    G = ΔE[u] / log(K_P/K_P0) = {G:+.3f}  utility-points / log-token")
    print(f"    V = ΔE[u] − {LAMBDA}·log(K_P/K_P0) = {V:+.3f}    "
          f"({'PROCEED' if V > 0 else 'DO_NOT_PROCEED'})")
    results_v2.append({
        "task": task, "model": model,
        "Eu_P0": Eu0, "Eu_P": EuP, "delta_Eu": dEu,
        "K_P0": K0, "K_P": KP,
        "log_K_ratio": log_ratio,
        "G": G,
        "V": V,
        "verdict": "PROCEED" if V > 0 else "DO_NOT_PROCEED",
    })

# Sensitivity analysis on lambda
print()
print("Sensitivity di V(λ) — per quale λ la decisione cambia?")
for r in results_v2:
    if r["log_K_ratio"] > 0:
        lambda_breakeven = r["delta_Eu"] / r["log_K_ratio"]
        print(f"  task={r['task']:18s} model={r['model']:6s}  λ_breakeven = {lambda_breakeven:.3f}")

# Stochastic dominance check on z = utility (per task)
print()
print("Stochastic dominance test — P(Z ≥ t) per Z=u(B):")
for task, model in sorted({(t, m) for t, _, m in per_cell}):
    rs0 = cells[(task, "P0", model)]
    rsP = cells[(task, "P", model)]
    u0 = sorted([utility(r) for r in rs0])
    uP = sorted([utility(r) for r in rsP])
    print(f"  task={task} model={model}")
    thresholds = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    for t in thresholds:
        p0 = sum(1 for u in u0 if u >= t) / len(u0)
        pP = sum(1 for u in uP if u >= t) / len(uP)
        dom = "P ≥ P0" if pP >= p0 else "P < P0 ✗"
        print(f"    t={t:.1f}:  P_P0(Z≥t) = {p0:.2f}   P_P(Z≥t) = {pP:.2f}   {dom}")

(RESULTS / "v2_metrics.json").write_text(json.dumps(results_v2, indent=2))
print()
print(f"Saved: {RESULTS / 'v2_metrics.json'}")
