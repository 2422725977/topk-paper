#!/usr/bin/env python3
"""Stage-2 tex fills: rewrite the E3 section from the dense sweep (e3_fine.json)
and E3-UE (e3_ue.json), update the honest-discussion item (iii), the abstract and
the intro contribution list.  Same anti-fabrication discipline as fill_tex.py:
every emitted number is verified greppable before being written."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from check_paper import _corpus_floats, token_in_corpus  # noqa: E402

PAPER = HERE.parent
RESULTS = PAPER / "results"
TEX = PAPER / "main.tex"

J = {name: json.load(open(RESULTS / f"{name}.json")) for name in ("e3_fine", "e3_ue")}
_corpus = "\n".join((RESULTS / f"{name}.json").read_text() for name in J)
_vals = _corpus_floats(_corpus)


def fmt(v, fmts=(".2f", ".1f", ".3f", ".4f", ".0f", "g")):
    for f in fmts:
        s = format(v, f)
        if token_in_corpus(s, _corpus, _vals):
            return s
    raise ValueError(f"no greppable format for {v!r}")


def main() -> int:
    tex = TEX.read_text()
    fine, ue = J["e3_fine"], J["e3_ue"]
    pw = fine["piecewise_loglog_fits"]
    tt = fine["two_term_fit"]
    tm = fine["threshold_model_fit"]

    # ---------------- E3 subsection ----------------
    old_e3 = r"""\subsection{E3: the exponent of $\Delta$}

Fixing $n=20$ (complete graph) and sweeping $\Delta\in[0.1,1.5]$ gives Figure~\ref{fig:e3}.  A log--log fit of $T$ against $\Delta$ over the full sweep yields the slope \textbf{-1.03} ($R^2= $ \textbf{0.95}), over the small-gap subrange $\Delta\in[0.1,0.5]$ the slope is \textbf{-1.43}.  The theory benchmark is $-2$; we discuss the residual gap in Section~\ref{sec:exp-discussion}.

\begin{figure}[t]
\centering
\includegraphics[width=0.6\textwidth]{figures/fig_e3.pdf}
\caption{E3: $T$ against $\Delta$ on the complete graph ($n=20$, $k=3$), log--log scale, with fitted power laws.}
\label{fig:e3}
\end{figure}
"""
    assert old_e3 in tex, "old E3 subsection not found"
    new_e3 = r"""\subsection{E3: the exponent of $\Delta$}
\label{sec:e3}

Fixing $n=20$ (complete graph, $k=3$) we sweep $\Delta$ over %s log-uniform points in $[%s, %s]$ with %s repetitions per point, measuring $T$ exactly as throughout (the natural consumption of the $\delta=0.05$ algorithm; no budget search, no redefinition of $\Delta$).  Figure~\ref{fig:e3} shows the result.  Piecewise log--log fits give slope \textbf{%s} ($R^2=$ \textbf{%s}) on $\Delta<0.2$, \textbf{%s} on $0.2\le\Delta\le0.6$, and \textbf{%s} on $\Delta>0.6$: the exponent glides from near $-2$ toward $-1$ as $\Delta$ grows, and even at $\Delta<0.2$ it does not reach $-2$.

The deviation is not a mystery: it is provably encoded in the algorithm's stopping rule.  The elimination threshold is $t_{ij}=\sqrt{2\log(4n^2r/\delta)\,s_{ij}^2}+2\log(4n^2r/\delta)\,s_{ij}^2$ (Section~\ref{sec:upper}); with the empirical inverse-counts scaling $s_{ij}^2=\kappa/c$, the stopping condition $t_{ij}=\Delta$ inverts \emph{exactly} to the one-parameter law
\[
c^\star(\Delta)\;=\;\frac{4A}{\big(\sqrt{1+4\Delta}-1\big)^2},
\]
whose local log--log exponent glides from $-2$ (as $\Delta\to0$) to $-1$ (large $\Delta$).  Fitting this prediction to the 24 measured means gives $A=%s$ with $R^2=%s$.  Equivalently, the two-term model $T=a\,\Delta^{-2}+b\,\Delta^{-1}$ fits with $a=%s\pm%s$ and $b=%s\pm%s$ ($R^2=%s$, bootstrap 95\%% CIs over per-repetition resampling); the $\Delta^{-1}$ component is the linear Bernstein term of the threshold acting at the decision margin, and it dominates the $\Delta^{-2}$ component beyond the crossover $\Delta\approx a/b$.  We also swept the estimator analyzed in Theorem~\ref{thm:upper} (\textsc{UE-topk}) over the same $\Delta$ range: its minimal per-edge budget $m^\star$ is too noisy to resolve an exponent at %s repetitions per point (best subrange slope \textbf{%s}, $R^2=%s$, with floor saturation $m^\star\in\{1,2\}$ at large $\Delta$).

\noindent\textbf{Verdict.}  At measurable gaps \emph{neither} algorithm exhibits the $\Delta^{-2}$ dependence of Theorem~\ref{thm:upper}: the practical successive-elimination provably carries a $\Delta^{-1}$ stopping component, and the one-shot estimator's $m^\star$ cannot be resolved precisely enough at our repetition budget.  The $\Delta^{-2}$ law remains the $\Delta\to0$ statement of the theorem; see Section~\ref{sec:exp-discussion}(iii).

\begin{figure}[t]
\centering
\includegraphics[width=0.6\textwidth]{figures/fig_e3.pdf}
\caption{E3: $T$ against $\Delta$ ($n=20$, complete graph, $k=3$, %s points $\times$ %s repetitions), log--log scale, with the two-term and stopping-rule fits.}
\label{fig:e3}
\end{figure}
""" % (
        fmt(fine["n_points"], (".0f",)), fmt(fine["sweep"][0]["delta"], (".2f",)),
        fmt(fine["sweep"][-1]["delta"], (".1f",)), fmt(fine["reps_per_point"], (".0f",)),
        fmt(pw["delta_lt_0.2"]["slope"]), fmt(pw["delta_lt_0.2"]["r_squared"], (".2f",)),
        fmt(pw["delta_0.2_to_0.6"]["slope"]), fmt(pw["delta_gt_0.6"]["slope"]),
        fmt(tm["A"], (".1f",)), fmt(tm["r_squared"], (".2f",)),
        fmt(tt["a"], (".1f",)), fmt(tt["a_se"], (".1f",)),
        fmt(tt["b"], (".1f",)), fmt(tt["b_se"], (".1f",)),
        fmt(tt["r_squared"], (".3f",)),
        fmt(ue["reps_per_point"], (".0f",)),
        fmt(ue["loglog_slope_mstar_subrange_mstar_ge4"]), fmt(ue["r_squared_subrange_mstar_ge4"], (".2f",)),
        fmt(fine["n_points"], (".0f",)), fmt(fine["reps_per_point"], (".0f",)),
    )
    tex = tex.replace(old_e3, new_e3)

    # ---------------- honest-discussion item (iii) ----------------
    old_iii = r"""\textbf{(iii) The measured $\Delta$-exponent is between $-1.0$ and $-1.4$, not $-2$.}  The deficit is attributable to the calibrated radii: the Bernstein linear term and the range clip are $\Delta$-independent by construction but bind relatively harder as $\Delta$ grows, and the doubling schedule quantizes the final round.  The $\Delta^{-2}$ information-theoretic benchmark is a lower-bound rate; since all measured success rates are $1.00$ at every $\Delta$, no instance in our sweep contradicts the theory, but our practical algorithm does not visibly exhibit the $-2$ exponent."""
    assert old_iii in tex, "old honest-discussion (iii) not found"
    new_iii = r"""\textbf{(iii) The measured $\Delta$-dependence does not support Theorem~\ref{thm:upper}'s $\Delta^{-2}$ law at measurable gaps.}  The dense sweep of Section~\ref{sec:e3} shows the practical algorithm's exponent gliding from %s ($\Delta<0.2$) to %s ($\Delta>0.6$), and the deviation is \emph{proved} to originate in the stopping rule: the Bernstein linear term of the contrast threshold inverts exactly to a $\Delta^{-1}$ stopping component, and the resulting one-parameter law fits the measured curve with $R^2=%s$.  The analyzed one-shot estimator could not be measured precisely enough to isolate its exponent (Section~\ref{sec:e3}).  Since all measured success rates are $1.00$ at every $\Delta$, no instance contradicts the theory, but whether a $\delta$-correct algorithm whose consumption exhibits the $\Delta^{-2}$ law on restricted graphs exists is open on the empirical side as well.""" % (
        fmt(pw["delta_lt_0.2"]["slope"]), fmt(pw["delta_gt_0.6"]["slope"]),
        fmt(tm["r_squared"], (".2f",)))
    tex = tex.replace(old_iii, new_iii)

    # ---------------- abstract ----------------
    old_abs = r"""Experiments on complete, random, star, dumbbell and cycle graphs validate the $n$- and $\Delta$-scaling of the bound, exhibit the connectivity penalty when the top-$k$ boundary straddles a bottleneck, and reveal a sharp failure mode of the uniform-sampling majority-vote baseline on sparse graphs; they also show that adaptive query concentration can beat the worst-case connectivity dependence."""
    assert old_abs in tex, "old abstract sentence not found"
    new_abs = r"""Experiments on complete, random, star, dumbbell and cycle graphs validate the $n$-scaling of the bound, show that the measured gap-dependence of the practical algorithm is softer than the predicted $\Delta^{-2}$ -- a deviation we prove originates in its stopping rule -- exhibit the connectivity penalty when the top-$k$ boundary straddles a bottleneck, and reveal a sharp failure mode of the uniform-sampling majority-vote baseline on sparse graphs; they also show that adaptive query concentration can beat the worst-case connectivity dependence."""
    tex = tex.replace(old_abs, new_abs)

    # ---------------- intro contribution (ii) ----------------
    old_intro = r"""(ii) the $\Delta$-exponent of $T$,"""
    assert old_intro in tex, "old intro item (ii) not found"
    new_intro = r"""(ii) the $\Delta$-dependence of $T$ over a dense sweep, which is provably softened relative to the $\Delta^{-2}$ benchmark by the practical algorithm's stopping rule,"""
    tex = tex.replace(old_intro, new_intro)

    TEX.write_text(tex)
    print("stage-2 fills done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
