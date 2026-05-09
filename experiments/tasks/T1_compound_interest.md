# T1 — compound_interest

Funzione di calcolo dell'interesse composto. Dominio finance, tipo di task per cui il sistema è progettato.

## Specifica formale (oracolo, **non visibile al modello**)

`compound_interest(principal, annual_rate, years, compounds_per_year=1) -> Decimal`

Restituisce il montante finale dato:
- `principal`: capitale iniziale (Decimal o str interpretabile come Decimal)
- `annual_rate`: tasso annuo come frazione decimale (es. 0.05 = 5%)
- `years`: durata in anni (int ≥ 0)
- `compounds_per_year`: capitalizzazioni/anno (int ≥ 1, default 1)

Formula: `M = P · (1 + r/n)^(n·t)`

## Casi di test ground truth (8)

| # | principal | rate | years | n | expected (Decimal) | tipo |
|---|---|---|---|---|---|---|
| 1 | 1000 | 0.05 | 10 | 1 | 1628.894626777442 | happy |
| 2 | 1000 | 0.05 | 10 | 12 | 1647.009497625746 | mensile |
| 3 | 1000 | 0.0 | 10 | 1 | 1000.000000000000 | rate zero |
| 4 | 1000 | 0.05 | 0 | 1 | 1000.000000000000 | years zero |
| 5 | 0 | 0.05 | 10 | 1 | 0.000000000000 | principal zero |
| 6 | 1000 | -0.05 | 10 | 1 | (deve sollevare ValueError) | rate negativo |
| 7 | 1000 | 0.05 | -1 | 1 | (deve sollevare ValueError) | years negativi |
| 8 | 1000 | 0.05 | 10 | 0 | (deve sollevare ValueError) | n=0 |

## Mutanti per mutation testing (6)

- M1: `r/n` → `r*n` (operator swap)
- M2: `n*t` → `n+t`
- M3: `years >= 0` → `years > 0` (boundary off-by-one)
- M4: `compounds_per_year >= 1` → `compounds_per_year > 1` (boundary)
- M5: rimosso check su rate negativa
- M6: `1 +` → `1 -` in `(1 + r/n)`

Mutation score = mutanti uccisi dai test del modello / 6.

## Vincoli ricorsivi (per condizione P)

Il protocollo richiede:
- Spec Given/When/Then esplicita prima del codice
- Almeno 5 test scritti PRIMA dell'implementazione (RED phase)
- Uso di `Decimal`, **no float** per money
- Docstring formale con invarianti (monotonicità rispetto a t e r)
- Nessun lookup esterno, deterministico
