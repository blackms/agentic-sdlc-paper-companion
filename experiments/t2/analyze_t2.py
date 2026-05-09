"""Compute Cohen kappa, phi, P(2-of-3 miss), rho_bar for asimm vs simm setups.

ASIMM: warm, cold, skeptic
SIMM:  simm1, simm2, simm3

Per ogni coppia (i,j), miss matrix m_i ∈ {0,1} (1 = MISS, cioè bug NON catturato).
- phi (Pearson on indicators) = corr(m_i, m_j)
- Cohen kappa
- P(2-of-3 miss) = frac(bugs where ≥ 2 reviewer missed)
"""
import json
import math
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).parent
DETECT = json.loads((ROOT / "reviews" / "_detection_table.json").read_text())

ASIMM_ROLES = ["warm", "cold", "skeptic"]
SIMM_ROLES = ["simm1", "simm2", "simm3"]


def miss_vectors(roles):
    """Return dict role -> list of {0,1,None} per bug. 1 = miss."""
    out = {r: [] for r in roles}
    for bid, det in DETECT["detection"].items():
        for r in roles:
            d = det[r]
            if d is None:
                out[r].append(None)
            elif d is True:
                out[r].append(0)  # caught
            else:
                out[r].append(1)  # miss
    return out


def phi_corr(a, b):
    """Phi coefficient (Pearson on binary). Skip None."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    if n < 2:
        return None
    mean_a = sum(x for x, _ in pairs) / n
    mean_b = sum(y for _, y in pairs) / n
    num = sum((x - mean_a) * (y - mean_b) for x, y in pairs)
    var_a = sum((x - mean_a) ** 2 for x, _ in pairs)
    var_b = sum((y - mean_b) ** 2 for _, y in pairs)
    if var_a == 0 or var_b == 0:
        return None
    return num / math.sqrt(var_a * var_b)


def cohen_kappa(a, b):
    """Cohen kappa on binary outcomes. Skip None."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    if n == 0:
        return None
    n00 = sum(1 for x, y in pairs if x == 0 and y == 0)
    n01 = sum(1 for x, y in pairs if x == 0 and y == 1)
    n10 = sum(1 for x, y in pairs if x == 1 and y == 0)
    n11 = sum(1 for x, y in pairs if x == 1 and y == 1)
    p_obs = (n00 + n11) / n
    pa1 = (n10 + n11) / n
    pb1 = (n01 + n11) / n
    p_e = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    if abs(p_e - 1) < 1e-9:
        return None
    return (p_obs - p_e) / (1 - p_e)


def p_2of3_miss(miss_dict, roles):
    """Frac of bugs where >= 2 of the 3 reviewers missed."""
    n_bugs = len(next(iter(miss_dict.values())))
    miss_count = []
    for i in range(n_bugs):
        vals = [miss_dict[r][i] for r in roles]
        if any(v is None for v in vals):
            continue
        miss_count.append(sum(vals))
    if not miss_count:
        return None, 0
    n_2plus = sum(1 for c in miss_count if c >= 2)
    return n_2plus / len(miss_count), len(miss_count)


def analyze(label, roles):
    print(f"\n=== {label} ({roles}) ===")
    miss = miss_vectors(roles)
    # Detection rate per reviewer
    for r in roles:
        n_total = sum(1 for v in miss[r] if v is not None)
        n_miss = sum(1 for v in miss[r] if v == 1)
        if n_total > 0:
            print(f"  {r:8s}: detection {(n_total - n_miss)}/{n_total} = "
                  f"{(n_total - n_miss)/n_total:.1%}, miss = {n_miss/n_total:.1%}")
    print()
    # Pairwise correlation
    rho_phis = []
    kappas = []
    for r1, r2 in combinations(roles, 2):
        phi = phi_corr(miss[r1], miss[r2])
        kappa = cohen_kappa(miss[r1], miss[r2])
        joint_miss = sum(1 for x, y in zip(miss[r1], miss[r2])
                         if x == 1 and y == 1 and x is not None)
        n_pair = sum(1 for x, y in zip(miss[r1], miss[r2])
                     if x is not None and y is not None)
        print(f"  rho({r1:8s}, {r2:8s}) phi={phi if phi is None else f'{phi:+.3f}'}  "
              f"kappa={kappa if kappa is None else f'{kappa:+.3f}'}  "
              f"joint_miss={joint_miss}/{n_pair}")
        if phi is not None:
            rho_phis.append(phi)
        if kappa is not None:
            kappas.append(kappa)
    if rho_phis:
        print(f"  rho_bar (phi avg) = {sum(rho_phis)/len(rho_phis):+.3f}")
    if kappas:
        print(f"  kappa_bar = {sum(kappas)/len(kappas):+.3f}")
    p2, n_eff = p_2of3_miss(miss, roles)
    print(f"  P(2-of-3 miss) = {p2:.2%}    (n_effective = {n_eff} bugs)" if p2 is not None
          else "  P(2-of-3 miss) undefined")
    return {
        "label": label,
        "rho_bar_phi": sum(rho_phis) / len(rho_phis) if rho_phis else None,
        "kappa_bar": sum(kappas) / len(kappas) if kappas else None,
        "p_2of3_miss": p2,
        "n_effective": n_eff,
    }


def main():
    print("=" * 80)
    print("T2 ANALYSIS — review asimmetrica vs simmetrica baseline")
    print(f"n_bugs total = {DETECT['n_bugs']}")
    print("=" * 80)
    a = analyze("ASIMM (warm + cold + skeptic)", ASIMM_ROLES)
    s = analyze("SIMM (3× generic)", SIMM_ROLES)

    print()
    print("=" * 80)
    print("HYPOTHESIS TEST")
    print("=" * 80)
    if a["p_2of3_miss"] is not None and s["p_2of3_miss"] is not None:
        diff = a["p_2of3_miss"] - s["p_2of3_miss"]
        print(f"  P_asimm(2-of-3 miss) = {a['p_2of3_miss']:.2%}")
        print(f"  P_simm (2-of-3 miss) = {s['p_2of3_miss']:.2%}")
        print(f"  ΔP = P_asimm − P_simm = {diff:+.2%}")
        print(f"  H1 (P_asimm < P_simm)  →  {'SUPPORTED' if diff < 0 else 'NOT SUPPORTED'}")
    if a["rho_bar_phi"] is not None and s["rho_bar_phi"] is not None:
        print(f"  ρ̄_asimm = {a['rho_bar_phi']:+.3f}")
        print(f"  ρ̄_simm  = {s['rho_bar_phi']:+.3f}")
        print(f"  Δρ̄ = ρ̄_asimm − ρ̄_simm = {a['rho_bar_phi'] - s['rho_bar_phi']:+.3f}")
        print(f"  T2 condition (ρ̄_asimm < ρ̄_simm)  →  "
              f"{'SUPPORTED' if a['rho_bar_phi'] < s['rho_bar_phi'] else 'NOT SUPPORTED'}")

    out = {"asimm": a, "simm": s}
    (ROOT / "results" / "t2_analysis.json").write_text(json.dumps(out, indent=2))
    print(f"\nFile: {ROOT / 'results' / 't2_analysis.json'}")


if __name__ == "__main__":
    main()
