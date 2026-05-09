# T2 — transfer_with_validation

Funzione di trasferimento fra due conti con validazione. Dominio finance, modellazione di un effect esterno.

## Specifica formale (oracolo, **non visibile al modello**)

```
transfer(account_from: Account, account_to: Account, amount: Decimal) -> Receipt
```

Dove `Account` ha `balance: Decimal` e `currency: str`. `Receipt` ha `from_id`, `to_id`, `amount`, `timestamp`.

Validazioni richieste:
1. `amount > 0`
2. `account_from.balance >= amount` (saldo sufficiente)
3. `account_from.currency == account_to.currency` (stessa valuta — niente FX implicita)
4. `account_from != account_to` (no self-transfer)

Effetti:
- `account_from.balance -= amount`
- `account_to.balance += amount`
- Restituisce `Receipt`

## Casi di test ground truth (10)

| # | from.bal | to.bal | amount | currency | expected | tipo |
|---|---|---|---|---|---|---|
| 1 | 100 EUR | 50 EUR | 30 | EUR | from=70, to=80, receipt | happy |
| 2 | 100 EUR | 0 EUR | 100 | EUR | from=0, to=100 | esatto saldo |
| 3 | 100 EUR | 0 EUR | 100.01 | EUR | ValueError | saldo insufficiente |
| 4 | 100 EUR | 50 EUR | 0 | EUR | ValueError | amount=0 |
| 5 | 100 EUR | 50 EUR | -10 | EUR | ValueError | amount negativo |
| 6 | 100 EUR | 50 USD | 10 | mixed | ValueError | currency mismatch |
| 7 | 100 EUR | 50 EUR | 10 | (same account) | ValueError | self-transfer |
| 8 | 100 EUR | 50 EUR | 10 | EUR | from.bal e to.bal aggiornati ATOMICALLY (anche se receipt fallisce, niente stato parziale) | atomicità |
| 9 | 0 EUR | 50 EUR | 10 | EUR | ValueError | from a zero |
| 10 | 100 EUR | 50 EUR | 100 | EUR | from=0, to=150 | edge: tutto |

## Mutanti per mutation testing (6)

- M1: `amount > 0` → `amount >= 0`
- M2: `balance >= amount` → `balance > amount`
- M3: rimosso check currency
- M4: rimosso check self-transfer
- M5: `from -= amount; to += amount` → `from += amount; to += amount` (bug aritmetico)
- M6: ordine swap: `to += amount; from -= amount` (atomicità: in caso di errore intermedio lo stato è inconsistente)

## Vincoli del protocollo P (per money-task)

- Calculation contract embedded come docstring formale
- `Decimal`, no float
- Test scritti prima
- Validazione ESPLICITA delle 4 condizioni
- Atomicità (transazionale o tramite snapshot/rollback)
