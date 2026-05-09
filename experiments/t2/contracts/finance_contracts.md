# Contratti formali (per cold contract-first reviewer)

Questi sono i **contratti dichiarati** delle 5 funzioni in `finance_lib.py`. Il cold reviewer riceve SOLO questo documento, NON il codice. Sulla base dei contratti deve identificare violazioni potenziali.

---

## `compound_interest(principal, annual_rate, years, compounds_per_year=1) -> Decimal`

**Inputs**:
- `principal` ≥ 0 (Decimal)
- `annual_rate` ≥ 0 (Decimal)
- `years` ≥ 0 (int)
- `compounds_per_year` ≥ 1 (int)

**Output**: `M = principal · (1 + annual_rate / compounds_per_year) ^ (compounds_per_year · years)`

**Invarianti**:
- I1: `M ≥ principal` ∀ inputs validi (monotonicità in t)
- I2: `M = principal` se `years = 0` o `principal = 0` o `annual_rate = 0`
- I3: monotonicità in r e t
- I4: determinismo: stesso input → stesso output
- I5: precisione: NO float per money, solo Decimal

**Errori**: `ValueError` se rate < 0, years < 0, compounds_per_year < 1.

---

## `loan_payment(principal, monthly_rate, months) -> Decimal`

**Inputs**:
- `principal` ≥ 0 (Decimal)
- `monthly_rate` ≥ 0 (Decimal)
- `months` > 0 (int)

**Output (formula amortizzazione)**:
- se `monthly_rate == 0`: `principal / months`
- altrimenti: `principal · r · (1+r)^months / ((1+r)^months − 1)`

**Invarianti**:
- I1: `payment > 0` per tutti gli input validi con principal > 0
- I2: `payment · months ≥ principal` (rimborso totale ≥ capitale)
- I3: continuità a `r → 0`: il limite della formula generale = `principal/months`
- I4: NO float per money

**Errori**: `ValueError` se principal < 0, rate < 0, months ≤ 0.

---

## `transfer(account_from, account_to, amount) -> Receipt`

**Inputs**:
- `account_from`, `account_to`: `Account` con `balance: Decimal`, `currency: str`, `id: str`
- `amount`: Decimal > 0

**Output**: `Receipt(from_id, to_id, amount)` se successo.

**Invarianti**:
- I1: **conservazione**: `from.balance + to.balance` prima = dopo
- I2: **atomicità**: se qualsiasi validazione/operazione fallisce, NESSUN balance modificato
- I3: stesso currency obbligatorio
- I4: no self-transfer
- I5: balance ≥ 0 sempre dopo l'operazione (no overdraft)
- I6: NO float

**Errori**: `ValueError` se amount ≤ 0, currency mismatch, self-transfer, balance < amount.

---

## `apply_fee(amount, fee_pct, fee_min, fee_max) -> Decimal`

**Inputs**:
- `amount` ≥ 0 (Decimal)
- `fee_pct` ≥ 0 (Decimal)
- `fee_min` ≥ 0 (Decimal)
- `fee_max` ≥ 0 (Decimal)
- `fee_min ≤ fee_max`

**Output**: `amount − clip(amount · fee_pct, fee_min, fee_max)`

**Invarianti**:
- I1: il risultato è ≤ amount (la fee viene SOTTRATTA)
- I2: la fee effettiva è in [fee_min, fee_max]
- I3: NO float

**Errori**: `ValueError` se uno qualunque degli input è negativo o se `fee_min > fee_max`.

---

## `fx_convert(amount, from_currency, to_currency, rates) -> Decimal`

**Inputs**:
- `amount` ≥ 0 (Decimal)
- `from_currency`, `to_currency`: str (codici ISO 4217)
- `rates`: dict `{(from, to): Decimal}` lookup table

**Output**:
- Se `from == to`: `amount` (identità)
- Altrimenti: `amount · rates[(from, to)]`

**Invarianti**:
- I1: identità per stessa currency
- I2: NO float per rate o amount
- I3: errore esplicito se rate mancante (no silent fallback)

**Errori**: `ValueError` se amount < 0, rate non disponibile.
