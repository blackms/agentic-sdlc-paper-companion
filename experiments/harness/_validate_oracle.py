"""Validate the oracle harness with a known-good reference implementation."""
import tempfile
from pathlib import Path
import subprocess
import sys

REF_T1 = '''
from decimal import Decimal, getcontext
getcontext().prec = 30

def compound_interest(principal, annual_rate, years, compounds_per_year=1):
    """Reference impl with Decimal."""
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

def test_happy():
    assert abs(compound_interest(1000, "0.05", 10, 1) - Decimal("1628.894626777442")) < Decimal("0.01")

def test_zero_rate():
    assert compound_interest(1000, 0, 10) == Decimal("1000")

def test_zero_years():
    assert compound_interest(1000, "0.05", 0) == Decimal("1000")

def test_neg_rate_raises():
    try:
        compound_interest(1000, -0.05, 10)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_neg_years_raises():
    try:
        compound_interest(1000, 0.05, -1)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_n_zero_raises():
    try:
        compound_interest(1000, 0.05, 10, 0)
        assert False, "expected ValueError"
    except ValueError:
        pass
'''


def main():
    sys.path.insert(0, str(Path(__file__).parent))
    import oracle_T1

    with tempfile.TemporaryDirectory() as td:
        fp = Path(td) / "ref.py"
        fp.write_text(REF_T1)
        c, dc = oracle_T1.conformance(str(fp))
        cor, dcor = oracle_T1.correctness(str(fp))
        rob, drob = oracle_T1.robustness(str(fp))
        print(f"REFERENCE T1: conformance={c}/5, correctness={cor:.3f}, robustness={rob:.3f}")
        print("conformance details:", dc)
        if cor < 1.0:
            print("ERROR: ref correctness <1.0")
            for n, s, e in dcor:
                print(f"  {n}: {s} {e}")
            sys.exit(1)
        print("Per-mutant:")
        for n, s, e in drob:
            print(f"  {n}: {s} {e}")
        # Note: robustness on reference depends on whether test cases catch the mutants


if __name__ == "__main__":
    main()
