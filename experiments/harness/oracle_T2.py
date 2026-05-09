"""Ground truth oracle for T2 transfer."""
from decimal import Decimal
import importlib.util
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@dataclass
class _Acc:
    id: str
    balance: Decimal
    currency: str


def make_accounts(b1, c1, b2, c2, same=False):
    a = _Acc("A", Decimal(str(b1)), c1)
    b = a if same else _Acc("B", Decimal(str(b2)), c2)
    return a, b


GROUND_TRUTH = [
    (("100", "EUR", "50", "EUR", False), "30", "happy", "ok", ("70", "80")),
    (("100", "EUR", "0", "EUR", False), "100", "exact_balance", "ok", ("0", "100")),
    (("100", "EUR", "0", "EUR", False), "100.01", "insufficient", "raises", None),
    (("100", "EUR", "50", "EUR", False), "0", "amount_zero", "raises", None),
    (("100", "EUR", "50", "EUR", False), "-10", "amount_neg", "raises", None),
    (("100", "EUR", "50", "USD", False), "10", "currency_mismatch", "raises", None),
    (("100", "EUR", "50", "EUR", True), "10", "self_transfer", "raises", None),
    (("0", "EUR", "50", "EUR", False), "10", "from_zero", "raises", None),
    (("100", "EUR", "50", "EUR", False), "100", "transfer_all", "ok", ("0", "150")),
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
    mod, err = load_module(filepath, f"model_{Path(filepath).stem}")
    if err:
        return 0.0, [("load", "FAIL", err)]
    fn = getattr(mod, "transfer", None)
    if fn is None:
        return 0.0, [("missing", "FAIL", "no transfer")]
    Acc = getattr(mod, "Account", None)
    results = []
    passed = 0
    for setup, amt, name, kind, expected_bal in GROUND_TRUTH:
        b1, c1, b2, c2, same = setup
        try:
            if Acc is not None:
                try:
                    a = Acc(id="A", balance=Decimal(str(b1)), currency=c1)
                    b = a if same else Acc(id="B", balance=Decimal(str(b2)), currency=c2)
                except TypeError:
                    try:
                        a = Acc("A", Decimal(str(b1)), c1)
                        b = a if same else Acc("B", Decimal(str(b2)), c2)
                    except Exception as ee:
                        results.append((name, "FAIL", f"cant_construct: {ee}"))
                        continue
            else:
                a, b = make_accounts(b1, c1, b2, c2, same=same)
            try:
                receipt = fn(a, b, Decimal(amt))
                if kind == "raises":
                    results.append((name, "FAIL", "expected raise"))
                    continue
                want_from, want_to = expected_bal
                if Decimal(str(a.balance)) == Decimal(want_from) and Decimal(str(b.balance)) == Decimal(want_to):
                    results.append((name, "PASS", ""))
                    passed += 1
                else:
                    results.append((name, "FAIL", f"bal {a.balance}/{b.balance} expected {want_from}/{want_to}"))
            except Exception as e:
                if kind == "raises":
                    if isinstance(e, (ValueError, AssertionError)):
                        results.append((name, "PASS", f"raised {type(e).__name__}"))
                        passed += 1
                    else:
                        results.append((name, "FAIL", f"wrong exc: {type(e).__name__}: {e}"))
                else:
                    results.append((name, "FAIL", f"raised {type(e).__name__}: {e}"))
        except Exception as e:
            results.append((name, "FAIL", f"setup error: {e}"))
    return passed / len(GROUND_TRUTH), results


MUTANTS = [
    ("M1_amount_ge0", lambda s: s.replace("amount > 0", "amount >= 0").replace("amount <= 0", "amount < 0")),
    ("M2_balance_gt", lambda s: s.replace("balance >= amount", "balance > amount").replace("balance < amount", "balance <= amount")),
    ("M3_no_currency", lambda s: s.replace('currency !=', 'currency =='.replace('==','!=', 0)).replace("currency_mismatch", "_disabled")),
    ("M4_no_self_check", lambda s: s.replace("account_from is account_to", "False").replace("a is b", "False").replace("from_id == to_id", "False")),
    ("M5_arith_swap", lambda s: s.replace("from.balance -= amount", "from.balance += amount").replace("account_from.balance -= amount", "account_from.balance += amount")),
    ("M6_order_swap", lambda s: s),  # placeholder; complex to mutate textually
]


def robustness(filepath):
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
    total_applicable = sum(1 for _, s, _ in detail if s not in ("SKIP_NO_CHANGE",))
    if total_applicable == 0:
        return 0.0, detail
    return killed / total_applicable, detail


def conformance(filepath):
    src = Path(filepath).read_text().lower()
    indicators = {}
    indicators["spec_gwt"] = any(k in src for k in ["given", "when", "then", "scenario:"])
    indicators["pre_impl_tests"] = src.count("def test") >= 5 or src.count("assert ") >= 8
    indicators["formal_contract"] = any(k in src for k in ["contract:", "invariant", "deterministic", "atomicity", "atomic"])
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
