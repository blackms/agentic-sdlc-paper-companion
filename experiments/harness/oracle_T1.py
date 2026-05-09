"""Ground truth oracle for T1 compound_interest. Not visible to the models."""
from decimal import Decimal, getcontext
import importlib.util
import sys
import traceback
from pathlib import Path

getcontext().prec = 30


def reference(principal, annual_rate, years, compounds_per_year=1):
    p = Decimal(str(principal))
    r = Decimal(str(annual_rate))
    t = int(years)
    n = int(compounds_per_year)
    if r < 0:
        raise ValueError("rate negative")
    if t < 0:
        raise ValueError("years negative")
    if n < 1:
        raise ValueError("n<1")
    return p * (Decimal(1) + r / n) ** (n * t)


GROUND_TRUTH = [
    (1000, "0.05", 10, 1, "happy", "ok"),
    (1000, "0.05", 10, 12, "monthly", "ok"),
    (1000, "0", 10, 1, "rate_zero", "ok"),
    (1000, "0.05", 0, 1, "years_zero", "ok"),
    (0, "0.05", 10, 1, "principal_zero", "ok"),
    (1000, "-0.05", 10, 1, "rate_neg", "raises"),
    (1000, "0.05", -1, 1, "years_neg", "raises"),
    (1000, "0.05", 10, 0, "n_zero", "raises"),
]


def load_module(filepath, modname):
    spec = importlib.util.spec_from_file_location(modname, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    return mod, None


def correctness(filepath):
    """Run the model's function against the 8 ground-truth cases. Return frac passed."""
    mod, err = load_module(filepath, f"model_{Path(filepath).stem}")
    if err:
        return 0.0, [("load", "FAIL", err)]
    fn = getattr(mod, "compound_interest", None)
    if fn is None:
        return 0.0, [("missing", "FAIL", "no compound_interest")]
    results = []
    passed = 0
    for p, r, t, n, name, kind in GROUND_TRUTH:
        try:
            got = fn(p, r, t, n)
            if kind == "raises":
                results.append((name, "FAIL", f"expected raise, got {got}"))
                continue
            try:
                ref = reference(p, r, t, n)
            except Exception as e:
                results.append((name, "FAIL", f"ref raised: {e}"))
                continue
            got_d = Decimal(str(got))
            diff = abs(got_d - ref)
            tol = Decimal("0.01")
            if diff <= tol:
                results.append((name, "PASS", ""))
                passed += 1
            else:
                results.append((name, "FAIL", f"got {got_d} expected {ref}"))
        except Exception as e:
            if kind == "raises":
                results.append((name, "PASS", f"raised {type(e).__name__}"))
                passed += 1
            else:
                results.append((name, "FAIL", f"raised {type(e).__name__}: {e}"))
    return passed / len(GROUND_TRUTH), results


MUTANTS = [
    ("M1_rn_swap", lambda src: src.replace("annual_rate / compounds_per_year", "annual_rate * compounds_per_year").replace("r/n", "r*n").replace("r / n", "r * n")),
    ("M2_nt_swap", lambda src: src.replace("compounds_per_year * years", "compounds_per_year + years").replace("n*t", "n+t").replace("n * t", "n + t")),
    ("M3_years_boundary", lambda src: src.replace("years < 0", "years <= 0").replace("years >= 0", "years > 0")),
    ("M4_n_boundary", lambda src: src.replace("compounds_per_year < 1", "compounds_per_year <= 1").replace("compounds_per_year >= 1", "compounds_per_year > 1").replace("n < 1", "n <= 1")),
    ("M5_rate_check_removed", lambda src: src.replace('if annual_rate < 0', 'if False').replace('if r < 0', 'if False').replace("rate negative", "rate negative_disabled")),
    ("M6_sign_flip", lambda src: src.replace("(1 + ", "(1 - ", 1).replace("Decimal(1) + ", "Decimal(1) - ", 1)),
]


def robustness(filepath):
    """Apply mutants to model's source, run model's tests against mutated. Frac killed."""
    src = Path(filepath).read_text()
    if "def test" not in src and "assert" not in src:
        return 0.0, []
    killed = 0
    detail = []
    for name, mutator in MUTANTS:
        mutated = mutator(src)
        if mutated == src:
            detail.append((name, "SKIP_NO_CHANGE", ""))
            continue
        mut_path = Path(filepath).parent / f"_mut_{Path(filepath).stem}_{name}.py"
        mut_path.write_text(mutated)
        mod, err = load_module(str(mut_path), f"mut_{Path(filepath).stem}_{name}")
        if err:
            killed += 1
            detail.append((name, "KILLED_BY_LOAD", err))
            continue
        test_funcs = [getattr(mod, n) for n in dir(mod) if n.startswith("test")]
        if not test_funcs:
            detail.append((name, "NO_TESTS", ""))
            continue
        died = False
        for tf in test_funcs:
            try:
                tf()
            except (Exception, BaseException) as exc:
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                died = True
                break
        if died:
            killed += 1
            detail.append((name, "KILLED", ""))
        else:
            detail.append((name, "SURVIVED", ""))
    total_applicable = sum(1 for _, status, _ in detail if status not in ("SKIP_NO_CHANGE",))
    if total_applicable == 0:
        return 0.0, detail
    return killed / total_applicable, detail


def conformance(filepath):
    """Score 0..5 for protocol conformance. Only meaningful when condition=P."""
    src = Path(filepath).read_text().lower()
    score = 0
    indicators = {}
    indicators["spec_gwt"] = any(k in src for k in ["given", "when", "then", "scenario:"])
    indicators["pre_impl_tests"] = src.count("def test") >= 5 or src.count("assert ") >= 5
    indicators["formal_contract"] = any(k in src for k in ["contract:", "invariant", "deterministic", "no-float"])
    indicators["red_green_markers"] = any(k in src for k in ["[red]", "[green]", "red phase", "green phase", "tdd"])
    indicators["no_float"] = "decimal" in src and "from decimal" in src
    score = sum(1 for v in indicators.values() if v)
    return score, indicators


if __name__ == "__main__":
    import sys
    fp = sys.argv[1]
    c, dc = conformance(fp)
    cor, dcor = correctness(fp)
    rob, drob = robustness(fp)
    print(f"conformance={c}/5 details={dc}")
    print(f"correctness={cor:.3f}")
    for n, s, e in dcor:
        print(f"  {n}: {s} {e}")
    print(f"robustness={rob:.3f}")
    for n, s, e in drob:
        print(f"  {n}: {s} {e}")
