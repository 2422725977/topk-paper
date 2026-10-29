#!/usr/bin/env python3
"""Generate the paper's figures from results/*.json into paper/figures/*.pdf."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
FIGURES = HERE.parent / "figures"
FIGURES.mkdir(exist_ok=True)

plt.rcParams.update({"font.size": 11, "figure.dpi": 150})


def fig_e3() -> None:
    d = json.load(open(RESULTS / "e3.json"))
    deltas = np.array([c["delta"] for c in d["sweep"]])
    T = np.array([c["T_mean"] for c in d["sweep"]])
    fit = d["fit"]
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.loglog(deltas, T, "o-", label="measured $T$", lw=1.2, ms=4)
    xs = np.linspace(deltas.min(), deltas.max(), 50)
    for key, style, label in [
        ("fit_full_range", "--", "full-range fit"),
        ("fit_small_gap_0.1_0.5", ":", "small-gap fit $[0.1,0.5]$"),
    ]:
        f = fit[key]
        ax.loglog(xs, np.exp(f["log_log_intercept"] + f["log_log_slope"] * np.log(xs)),
                  style, label=f"{label}: slope {f['log_log_slope']:.2f}")
    ax.set_xlabel(r"gap $\Delta$")
    ax.set_ylabel("comparisons $T$")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_e3.pdf")
    plt.close(fig)


def fig_e2b() -> None:
    d = json.load(open(RESULTS / "e2b.json"))
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    xs = np.array([f["m_edges_over_lambda"] for f in d["families"]])
    ys = np.array([f["T_star"] for f in d["families"]])
    names = [f["graph"] for f in d["families"]]
    ax.loglog(xs, ys, "o", ms=7)
    for x, y, name in zip(xs, ys, names):
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(6, 4), fontsize=8)
    # slope-1 guide through the first point (the scaling Theorem 5.1 predicts)
    ref = ys[0] * (xs / xs[0])
    ax.loglog(xs, ref, "k--", lw=0.9, label="slope-1 guide")
    ax.set_xlabel(r"$m_{\rm edges}\,/\,\lambda_G$")
    ax.set_ylabel(r"$T^\star = m^\star m_{\rm edges}$")
    ax.grid(alpha=0.3, which="both")
    slope = d["loglog_slope_Tstar_vs_medges_over_lambda"]
    ax.set_title(f"E2b: one-shot estimator, $T^\\star$ vs $m_{{\\rm edges}}/\\lambda_G$ (fit slope {slope:.2f})",
                 fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_e2b.pdf")
    plt.close(fig)


def fig_e4() -> None:
    d = json.load(open(RESULTS / "e4.json"))
    Bs = np.array([c["budget"] for c in d["sweep"]])
    errs = np.array([c["error_rate"] for c in d["sweep"]])
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.step(Bs, errs, where="post", lw=1.4)
    ax.set_xscale("log")
    ax.set_xlabel("budget $B$ (comparisons)")
    ax.set_ylabel("error rate")
    ax.set_ylim(-0.02, 1.0)
    ax.grid(alpha=0.3)
    ax.axvline(10057, color="gray", ls="--", lw=1)
    ax.annotate("uncapped $T$", (10057, 0.5), textcoords="offset points", xytext=(5, 0), fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig_e4.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_e3()
    fig_e2b()
    fig_e4()
    print("figures written to", FIGURES)
