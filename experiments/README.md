# Fase 2 — Esperimento pilota

## Scope (onesto)

Questo è un **pilota di scala ridotta**, non un benchmark conclusivo. L'obiettivo è:
1. Validare la **strumentazione** (harness riproducibile, definizione operativa di `B`, calcolo di `η`).
2. Produrre **direction evidence** sui teoremi T1 / T2 / T3.
3. Identificare cosa serve per scalare a una vera Fase 2 (n ≥ 30 per cella, più task, più modelli).

Non aspettarsi p-value robusti con `n = 3` per cella. Aspettarsi: **stime puntuali, ordini di grandezza, falsificazioni qualitative**.

## Design

| Fattore | Livelli |
|---|---|
| Task | T1 = `compound_interest`; T2 = `transfer_with_validation` |
| Condizione | P₀ = prompt libero (1 frase); P = protocollo strutturato (spec-first + TDD + contract) |
| Modello | M1 = Claude (subagent isolato); M2 = Codex (`codex exec`) |
| Replicas | n = 3 per cella |

Totale: **2 × 2 × 2 × 3 = 24 run**.

## Definizione operativa di `B = φ(τ)`

`B` è un vettore a 4 componenti misurate sulla traiettoria τ del run:

| Componente | Definizione | Range |
|---|---|---|
| `B_conformance` | Score di aderenza al protocollo. Per P₀: sempre 0 (non chiediamo conformità). Per P: 5 indicatori binari (presenza spec Given/When/Then; presenza test pre-impl; presenza contratto YAML/docstring formale; commit-style RED/GREEN; nessun float per money-task). | [0, 5] |
| `B_correctness` | Frazione di test ground-truth passati. I test sono **scritti dal proponente del task** (cioè da me, non dal modello), e includono edge case che il modello non vede. | [0, 1] |
| `B_robustness` | Mutation score: frazione di mutanti uccisi dai test prodotti dal modello. Se il modello non produce test → 0. | [0, 1] |
| `B_cost` | Token totali (input + output). Proxy: char_count / 4 quando il modello non riporta token nativi. | ℕ |

`B_correctness` è il **proxy di `Pred_S`** (semantic predictability): viene misurato contro un oracolo non visibile al modello.
`B_conformance` è il **proxy di `Pred_C`** (conformance predictability): aderenza al template procedurale.

## Stima di `H(B|x,P)`

Con `n = 3` repliche, l'entropia è stimata via:
- Discretizzazione di `B_correctness` e `B_robustness` in 4 bucket: {0, (0,0.5], (0.5,0.9], 1}.
- Entropia di Shannon empirica: `H = − Σ_b (count_b/n) log₂(count_b/n)`.
- Riportata con bias-correction Miller-Madow: `H_corrected = H + (K-1)/(2n ln 2)` dove K è il numero di bucket osservati.

**Caveat:** `n = 3` è sotto la soglia critica per stima entropia affidabile. Riportiamo intervalli di confidenza Bayesian (Dirichlet posterior) e li interpretiamo come **direzionali, non conclusivi**.

## Metrica η

Per ogni task `x` e modello `m`:

```
η(x, m) = [H_emp(B|x, P₀) − H_emp(B|x, P)] / [E[K_P] − E[K_P₀]]
```

Aggregato: media non pesata su (x, m). Se per un (x, m) `E[K_P] ≤ E[K_P₀]` riportiamo separatamente come **regime Pareto** (raro).

## Ground truth

Per ogni task: un file `tasks/<task>.expected.py` con:
- Implementazione di riferimento.
- Suite di test (≥ 8 casi: happy path, edge cases, errori).
- Set di mutanti (mutation testing manuale: 6 mutanti per funzione).

## Riproducibilità

- Tutti i prompt sono in `prompts/`.
- Tutti i run output in `runs/<run_id>/` (input prompt + output raw + parsed metrics).
- Harness in `harness/orchestrate.py`.
- Aggregazione in `harness/aggregate.py`.
- Risultati in `results/`.

## Limiti dichiarati

1. **n = 3** è troppo basso per stime entropia robuste.
2. **Modelli**: Claude come "warm self" è un confounder (è anche il modello che progetta l'esperimento). Codex è indipendente.
3. **Task piccoli**: due funzioni isolate non rappresentano la complessità di un sistema reale.
4. **Mutation testing manuale**: 6 mutanti/funzione è basso; bias del proponente nel sceglierli.
5. **Nessun reviewer asimmetrico**: T2 non viene testato in questo pilota — richiede setup separato con bug iniettati e tre reviewer indipendenti.
6. **T3 non testato**: richiede storia di run, fuori scope per il pilota.
