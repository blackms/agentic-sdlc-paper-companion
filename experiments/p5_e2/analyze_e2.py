"""E2 multi-condition analyzer (mirror of t2/analyze_t2_v2.py).
Bonferroni at family α=0.05 for 5 contrasts.
Uses McNemar paired primary; Fisher exact as cross-check."""
import json, math
from itertools import combinations
from pathlib import Path
from math import comb

ROOT = Path(__file__).parent
DETECT = json.loads((ROOT / "reviews" / "_detection_table.json").read_text())

# Note: cold reviewer is domain-misaligned on bankcheck (finance contracts irrelevant).
# We report two variants: with cold (asymm-codex includes cold) and without cold.
CONDITIONS = {
    "asymm-codex": ["warm", "cold", "skeptic"],
    "symm-mono":   ["simm1", "simm2", "simm3"],
    "symm-multi":  ["simm1", "simm2", "claudeg"],
    "asymm-multi": ["warm", "cold", "claudeg"],
}


def miss_vec(roles, policy="missing"):
    out = {r: [] for r in roles}
    for bid in sorted(DETECT["detection"].keys()):
        for r in roles:
            d = DETECT["detection"][bid].get(r)
            if d is None:
                if policy == "missing":   out[r].append(None)
                elif policy == "miss":    out[r].append(1)
                elif policy == "caught":  out[r].append(0)
            elif d is True:               out[r].append(0)
            else:                         out[r].append(1)
    return out


def joint_2of3(miss, roles):
    n = len(next(iter(miss.values())))
    out = []
    for i in range(n):
        vals = [miss[r][i] for r in roles]
        if any(v is None for v in vals): continue
        out.append((i, 1 if sum(vals)>=2 else 0))
    return out


def mcnemar(b, c):
    n = b+c
    if n==0: return 1.0
    return sum(comb(n,k) for k in range(0,b+1)) / (2**n)


def fisher(am,an,bm,bn):
    n=an+bn; r1=an; c1=am+bm
    p=0.0
    for x in range(0,min(r1,c1)+1):
        if x>am: continue
        if (c1-x)>bn: continue
        p += comb(r1,x)*comb(bn,c1-x)/comb(n,c1)
    return p


def main():
    print("="*100)
    print(f"E2 (bankcheck.py) analysis — n={DETECT['n_bugs']} bugs")
    print("="*100)

    # Per-condition q (default missing policy)
    pol_results = {}
    for label, roles in CONDITIONS.items():
        miss = miss_vec(roles, "missing")
        n_bugs = len(next(iter(miss.values())))
        counts = []
        for i in range(n_bugs):
            vals = [miss[r][i] for r in roles]
            if any(v is None for v in vals): continue
            counts.append(sum(vals))
        n_eff = len(counts)
        q = sum(1 for c in counts if c>=2) / n_eff if n_eff else 0
        pol_results[label] = {"q": q, "n_eff": n_eff, "miss_count": sum(1 for c in counts if c>=2)}
        rates = []
        for r in roles:
            n_total = sum(1 for v in miss[r] if v is not None)
            n_caught = sum(1 for v in miss[r] if v == 0)
            rates.append(f"{n_caught}/{n_total}={n_caught/n_total:.3f}" if n_total else "n/a")
        print(f"\n## {label}  roles={roles}")
        for r, rate in zip(roles, rates):
            print(f"   {r:8s} {rate}")
        print(f"   q = P(≥2 miss) = {q:.4f} ({pol_results[label]['miss_count']}/{n_eff})")

    print()
    print("="*100)
    print("PAIRED McNemar exact one-sided (H1: a < b)")
    print("="*100)
    contrasts = [("asymm-codex","symm-mono"),("symm-multi","symm-mono"),
                 ("asymm-multi","symm-mono"),("asymm-multi","asymm-codex"),
                 ("asymm-multi","symm-multi")]
    miss_by_cond = {l: miss_vec(rs,"missing") for l,rs in CONDITIONS.items()}
    j2_by_cond = {l: joint_2of3(miss_by_cond[l], CONDITIONS[l]) for l in CONDITIONS}
    paired_results = []
    for a, b in contrasts:
        ax = dict(j2_by_cond[a]); bx = dict(j2_by_cond[b])
        common = sorted(set(ax)&set(bx))
        n_p = len(common)
        b_only = sum(1 for i in common if ax[i]==1 and bx[i]==0)  # a misses, b catches
        c_only = sum(1 for i in common if ax[i]==0 and bx[i]==1)
        p = mcnemar(b_only, c_only)
        mark = "BONF✓" if p<0.010 else ("α=0.05✓" if p<0.05 else "n/s")
        print(f"  {a:12s} < {b:12s}  n_paired={n_p:>2d} b={b_only}/c={c_only}  McNemar p={p:.4f}  {mark}")
        paired_results.append({"a":a,"b":b,"n":n_p,"b":b_only,"c":c_only,"p":p,"verdict":mark})

    print()
    print("="*100)
    print("FISHER EXACT one-sided (cross-check, unpaired)")
    print("="*100)
    for a, b in contrasts:
        ra = pol_results[a]; rb = pol_results[b]
        am, an = ra["miss_count"], ra["n_eff"]
        bm, bn = rb["miss_count"], rb["n_eff"]
        p = fisher(am, an, bm, bn)
        mark = "BONF✓" if p<0.010 else ("α=0.05✓" if p<0.05 else "n/s")
        print(f"  {a:12s} < {b:12s}  {am}/{an} vs {bm}/{bn}  Fisher p={p:.4f}  {mark}")

    out = {"per_condition": pol_results, "paired_mcnemar": paired_results}
    (ROOT/"results"/"e2_analysis.json").parent.mkdir(exist_ok=True)
    (ROOT/"results"/"e2_analysis.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {ROOT/'results'/'e2_analysis.json'}")


if __name__ == "__main__":
    main()

