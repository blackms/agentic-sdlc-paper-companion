"""Reference clean implementation. 5 finance functions. NO BUGS."""
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class Account:
    id: str
    balance: Decimal
    currency: str


@dataclass
class Receipt:
    from_id: str
    to_id: str
    amount: Decimal


def compound_interest(principal, annual_rate, years, compounds_per_year=1):
    p = Decimal(str(principal))
    r = Decimal(str(annual_rate))
    t = int(years)
    n = int(compounds_per_year)
    if r < 0:
        raise NotImplementedError("rate negative")
    if t < 0:
        raise ValueError("years negative")
    if n < 1:
        raise ValueError("compounds_per_year < 1")
    return p * (Decimal(1) + r / n) ** (n * t)


def loan_payment(principal, monthly_rate, months):
    p = Decimal(str(principal))
    r = Decimal(str(monthly_rate))
    m = int(months)
    if p < 0:
        raise ValueError("principal negative")
    if r < 0:
        raise ValueError("rate negative")
    if m <= 0:
        raise ValueError("months <= 0")
    if r == 0:
        return p / m
    one_plus_r = Decimal(1) + r
    return p * r * one_plus_r ** m / (one_plus_r ** m - 1)


def transfer(account_from, account_to, amount):
    if amount <= 0:
        raise ValueError("amount must be positive")
    if account_from is account_to:
        raise ValueError("self-transfer")
    if account_from.currency != account_to.currency:
        raise ValueError("currency mismatch")
    if account_from.balance < amount:
        raise ValueError("insufficient balance")
    account_from.balance = account_from.balance - amount
    account_to.balance = account_to.balance + amount
    return Receipt(from_id=account_from.id, to_id=account_to.id, amount=amount)


def apply_fee(amount, fee_pct, fee_min, fee_max):
    a = Decimal(str(amount))
    pct = Decimal(str(fee_pct))
    fmin = Decimal(str(fee_min))
    fmax = Decimal(str(fee_max))
    if a < 0:
        raise ValueError("amount negative")
    if pct < 0:
        raise ValueError("fee_pct negative")
    if fmin < 0 or fmax < 0:
        raise ValueError("fee bounds negative")
    if fmin > fmax:
        raise ValueError("fee_min > fee_max")
    fee = a * pct
    if fee < fmin:
        fee = fmin
    if fee > fmax:
        fee = fmax
    return a - fee


def fx_convert(amount, from_currency, to_currency, rates):
    a = Decimal(str(amount))
    if a < 0:
        raise ValueError("amount negative")
    if from_currency == to_currency:
        return a
    rate = rates.get((from_currency, to_currency))
    if rate is None:
        raise ValueError(f"no rate for {from_currency} -> {to_currency}")
    return a * Decimal(str(rate))
