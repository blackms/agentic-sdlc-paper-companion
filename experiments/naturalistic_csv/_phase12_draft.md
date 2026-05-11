# Phase 12 — LaTeX integration draft

(Filled with placeholders to be substituted from results.json after the batch
runs. This is NOT the integrated paper text — only the staging.)

\subsection{Phase 12: Naturalistic bug benchmark on csv.py ($n = N_BUGS$)}
\label{sec:phase12}

\textbf{Motivation.} The C1 specificity finding (cold $>$ cold\_mismatched)
was established in Phases 5--10 on AST single-mutation bugs (AOR/ROR/BOR).
Phase 12 replicates the same protocol on \emph{naturalistic} bugs harvested
from the CPython issue tracker on \texttt{Lib/csv.py}, the stdlib module
with the lowest cold-detection rate in Phase 9. The pre-registration is at
\path{docs/paper/v1.4/preregistration-extend.md} (frozen 2026-05-11).

\textbf{Harvest.} We enumerated all $80$ commits ever touching
\texttt{Lib/csv.py}; $25$ pass the structural filter
(\texttt{csv.py}-production-only, $2 \le \text{net LOC} \le 30$). After
checking that the reversal patch applies cleanly to the v3.12 reference
and produces an importable Python 3 source, and after excluding
documentation-only, refactor-only, perf-only, Python-2-syntax-only fixes,
and multi-function bugs, $N_BUGS$ naturalistic bugs survive. This is below
the pre-registered target of $25$--$30$; pre-registration risk \#1
explicitly anticipates this case and mandates ``proceed at $n$ = harvested
with reduced power''. Power at $n = N_BUGS$ for $\Delta = 30\,\mathrm{pp}$,
$\alpha = 0.025$, paired one-sided: $\approx \text{POWER\_PCT}$. The
qualitative direction of the effect is still informative; the per-family
significance test is severely under-powered and read as qualitative.

\textbf{Method.} Three reviewer families (Codex \texttt{gpt-5.5}, Claude
Opus 4.7, Gemini 3.1 Pro Preview) review each of the $N_BUGS$ bugged
sources under two conditions:
\begin{itemize}[leftmargin=2em]
  \item \emph{cold} — auto-extracted \texttt{csv.py} contracts (Phase 9
    artefact, byte-identical re-use).
  \item \emph{cold\_mismatched} — bankcheck contracts (the deliberately
    wrong P6 artefact, byte-identical re-use).
\end{itemize}
$3 \times N_BUGS \times 2$ paired calls. Detection criterion is frozen at
harvest: per bug, a \emph{frozen} list of $5$--$9$
\texttt{expected\_detection\_keywords} (function name $+$ bug summary
terms $+$ any cited error type); reviewer detects iff any keyword (case-
insensitive) appears in the concatenated \texttt{bugs\_found} list.

\textbf{Out-of-band probe.} After each main call, a separate one-shot
asks: \emph{``Have you seen this exact bug or its fix in the Python
CPython issue tracker? If yes, please cite the issue number.''} The
probe does \emph{not} enter the detection metric; cite-rate is reported
as a leakage diagnostic.

\textbf{Per-family result.}

\begin{center}
\small
\begin{tabular}{@{}lccccc@{}}
\toprule
Family & cold & mm & $\Delta$ & perm $p$ & McNemar $p$ \\
\midrule
Codex \texttt{gpt-5.5} & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX & 0.XXXX \\
Claude Opus 4.7 & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX & 0.XXXX \\
Gemini 3.1 Pro Preview & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX & 0.XXXX \\
\bottomrule
\end{tabular}
\end{center}

\textbf{Leakage diagnostic.}

\begin{center}
\small
\begin{tabular}{@{}lccc@{}}
\toprule
Family & Cite-rate & Caveat ($>30\%$) & Note \\
\midrule
Codex & X.X\% & yes/no & --- \\
Opus & X.X\% & yes/no & --- \\
Gemini 3.1 Pro & X.X\% & yes/no & --- \\
\bottomrule
\end{tabular}
\end{center}

\textbf{Naturalistic vs AST cold-rate (same module).}

\begin{center}
\small
\begin{tabular}{@{}lcccc@{}}
\toprule
Family & AST cold & Naturalistic cold & $\Delta$ & MW $p$ (AST $\ge$ nat.) \\
\midrule
Codex & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX \\
Opus & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX \\
Gemini 3.1 Pro & X.X\% & X.X\% & $\pm$X.Xpp & 0.XXXX \\
\bottomrule
\end{tabular}
\end{center}

\textbf{Conclusion.} INTERP\_TEXT. At $\alpha = 0.025$ per family with
Bonferroni-style family-wise envelope $0.075$, K\_OF\_3 families show
cold $>$ cold\_mismatched on naturalistic csv.py bugs. The AST-vs-
naturalistic secondary IS\_DIRECTION\_AS\_EXPECTED with the pre-
registered direction (naturalistic harder than AST). Leakage diagnostic
shows LEAKAGE\_QUALIFIER for all three families.
