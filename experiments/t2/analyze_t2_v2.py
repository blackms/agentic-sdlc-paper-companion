"""T2 v2 analysis with 4 conditions (2x2 design):

  Prompt: SAME (generic)         DIFFERENT (warm/cold/skeptic)
Model SAME (Codex)   simm-mono      asimm-codex
DIFFERENT (Codex+Claude) simm-multi  asimm-multi (PARTIAL: warm Codex + cold Codex + claudeg Claude)

Note: asimm-multi is "partial" because we don't have a Gemini skeptic.
Substitute: warm (Codex) + cold (Codex contract-first) + claudeg (Claude generic-as-skeptic-substitute)
This isolates the model-diversity component of role-asymmetry.
"""
import json
import math
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).parent
DETECT = json.loads((ROOT / "reviews" / "_detection_table.json").read_text())

CONDITIONS = {
    "asimm-codex":  ["warm", "cold", "skeptic"],     # role asymmetry, model fixed
    "simm-mono":    ["simm1", "simm2", "simm3"],     # full baseline (no diversity)
    "simm-multi":   ["simm1", "simm2", "claudeg"],   # model diversity, no role asymmetry
    "asimm-multi":  ["warm", "cold", "claudeg"],     # role asymmetry + model diversity
}


def miss_vectors(roles):
    out = {r: [] for r in roles}
    for bid in sorted(DETECT["detection"].keys()):
        det = DETECT["detection"][bid]
        for r in roles:
            d = det.get(r)
            if d is None:
                out[r].append(None)
            elif d is True:
                out[r].append(0)  # caught
            else:
                out[r].append(1)  # miss
    return out


def phi_corr(a, b):
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
    n_bugs = len(next(iter(miss_dict.values())))
    counts = []
    for i in range(n_bugs):
        vals = [miss_dict[r][i] for r in roles]
        if any(v is None for v in vals):
            continue
        counts.append(sum(vals))
    if not counts:
        return None, 0
    n_2plus = sum(1 for c in counts if c >= 2)
    return n_2plus / len(counts), len(counts)


def fisher_one_sided_less(a_miss, a_n, b_miss, b_n):
    """Fisher exact, alternative='less' on 2x2 table [[a_miss, a_n-a_miss],[b_miss, b_n-b_miss]]."""
    from math import comb
    n = a_n + b_n
    r1 = a_n
    c1 = a_miss + b_miss
    if c1 > n:
        return 1.0
    p = 0.0
    for x in range(0, min(r1, c1) + 1):
        if x > a_miss:
            continue
        if (c1 - x) > b_n:
            continue
        p += comb(r1, x) * comb(b_n, c1 - x) / comb(n, c1)
    return p


def analyze(label, roles):
    miss = miss_vectors(roles)
    detection_rates = {}
    for r in roles:
        n_total = sum(1 for v in miss[r] if v is not None)
        n_miss = sum(1 for v in miss[r] if v == 1)
        detection_rates[r] = (n_total - n_miss, n_total) if n_total > 0 else (0, 0)
    rho_phis = []
    kappas = []
    pair_details = []
    for r1, r2 in combinations(roles, 2):
        phi = phi_corr(miss[r1], miss[r2])
        kappa = cohen_kappa(miss[r1], miss[r2])
        joint_miss = sum(1 for x, y in zip(miss[r1], miss[r2])
                         if x == 1 and y == 1 and x is not None)
        n_pair = sum(1 for x, y in zip(miss[r1], miss[r2])
                     if x is not None and y is not None)
        pair_details.append((r1, r2, phi, kappa, joint_miss, n_pair))
        if phi is not None:
            rho_phis.append(phi)
        if kappa is not None:
            kappas.append(kappa)
    p2, n_eff = p_2of3_miss(miss, roles)
    return {
        "label": label,
        "roles": roles,
        "detection": detection_rates,
        "pairs": pair_details,
        "rho_bar_phi": sum(rho_phis) / len(rho_phis) if rho_phis else None,
        "kappa_bar": sum(kappas) / len(kappas) if kappas else None,
        "p_2of3_miss": p2,
        "n_effective": n_eff,
    }


def main():
    print("=" * 100)
    print(f"T2 V2 ANALYSIS — n={DETECT['n_bugs']} bugs, 2x2 design (prompt × model)")
    print("=" * 100)
    results = {}
    for label, roles in CONDITIONS.items():
        results[label] = analyze(label, roles)
        r = results[label]
        print(f"\n## {label}  roles={roles}")
        for role, (caught, total) in r["detection"].items():
            print(f"   {role:8s} detection {caught}/{total} = "
                  f"{caught/total*100:.1f}%" if total else f"   {role:8s} no data")
        for r1, r2, phi, kappa, jm, np_ in r["pairs"]:
            phi_s = f"{phi:+.3f}" if phi is not None else "NaN"
            kappa_s = f"{kappa:+.3f}" if kappa is not None else "NaN"
            print(f"   pair ({r1:8s},{r2:8s})  phi={phi_s} kappa={kappa_s} "
                  f"joint_miss={jm}/{np_}")
        if r["rho_bar_phi"] is not None:
            print(f"   ρ̄ (phi avg)    = {r['rho_bar_phi']:+.3f}")
        if r["p_2of3_miss"] is not None:
            print(f"   P(2-of-3 miss) = {r['p_2of3_miss']:.2%} (n_eff={r['n_effective']})")

    print()
    print("=" * 100)
    print("HYPOTHESIS TESTS — Fisher exact one-sided 'less'")
    print("=" * 100)

    def cmp(a_label, b_label):
        ra = results[a_label]
        rb = results[b_label]
        a_n = ra["n_effective"]
        b_n = rb["n_effective"]
        a_miss = round(ra["p_2of3_miss"] * a_n)
        b_miss = round(rb["p_2of3_miss"] * b_n)
        p = fisher_one_sided_less(a_miss, a_n, b_miss, b_n)
        delta = ra["p_2of3_miss"] - rb["p_2of3_miss"]
        verdict = "SUPPORTED" if p < 0.05 else ("MARGINAL" if p < 0.10 else "NOT_SUPPORTED")
        print(f"  H1: P({a_label}) < P({b_label})")
        print(f"      P({a_label})={ra['p_2of3_miss']:.2%} ({a_miss}/{a_n})  "
              f"P({b_label})={rb['p_2of3_miss']:.2%} ({b_miss}/{b_n})  "
              f"ΔP={delta:+.2%}  Fisher one-sided p={p:.4f}  → {verdict}")

    cmp("asimm-codex", "simm-mono")     # prompt asymmetry alone
    cmp("simm-multi",  "simm-mono")     # model diversity alone
    cmp("asimm-multi", "simm-mono")     # full effect
    cmp("asimm-multi", "asimm-codex")   # marginal effect of model on top of prompt asymm
    cmp("asimm-multi", "simm-multi")    # marginal effect of prompt on top of model diversity

    (ROOT / "results" / "t2_v2_analysis.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"\nFile: {ROOT / 'results' / 't2_v2_analysis.json'}")


if __name__ == "__main__":
    main()
