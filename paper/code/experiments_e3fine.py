#!/usr/bin/env python3
"""E3-fine: dense log-uniform Delta sweep to diagnose the Delta-dependence of T.

Motivation (Wave-1 finding): the full-range log-log slope of T vs Delta was -1.03
against the theory's -2.  Diagnosis (code-level, provable): the elimination
threshold t_ij = sqrt(2 x s_ij^2) + 2 x s_ij^2 contains an additive Bernstein
linear term; with s^2 = kappa/c the stopping condition t = Delta inverts to
c*(Delta) = 4a / (sqrt(1+4*Delta)-1)^2  (a = 2 x kappa), whose local log-log
exponent glides from -2 (Delta -> 0) to -1 (large Delta).  This sweep measures
that curve densely and fits:
  (i)   piecewise log-log slopes over Delta<0.2, 0.2-0.6, >0.6;
  (ii)  the two-term model T = a Delta^-2 + b Delta^-1 (OLS + bootstrap CIs);
  (iii) the threshold-derived one-parameter model T = A / (sqrt(1+4 Delta)-1)^2.
T is measured exactly as before: natural consumption of the delta=0.05 algorithm,
no bisection, no redefinition of Delta or the success criterion.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulate import complete_graph, lambda_G, make_theta_bounded
from algorithms import graph_walk_elimination

RESULTS = Path(__file__).resolve().parent.parent / "results"
DELTA_CONF = 0.05
K = 3
REPS = 200
N = 20


def main() -> int:
    import os
    out_path = RESULTS / "e3_fine.json"
    if "--fits-only" in sys.argv and out_path.exists():
        prev = json.load(open(out_path))
        return finalize(prev["sweep"], prev)
    rng0 = np.random.default_rng(0)
    G = complete_graph(N)
    lam = lambda_G(G)
    theta = make_theta_bounded(N, 1.0, K)  # shape fixed; per-Delta instances below
    truth = set(range(K))
    deltas = np.exp(np.linspace(np.log(0.05), np.log(2.0), 24))
    sweep = []
    t0all = time.time()
    for i, delta in enumerate(deltas):
        delta = round(float(delta), 4)
        th = make_theta_bounded(N, delta, K)
        T_raw, success_raw, rounds_raw = [], [], []
        t0 = time.time()
        for rep in range(REPS):
            rng = np.random.default_rng(900_000 + 97 * i + rep)
            S, T, info = graph_walk_elimination(th, G, K, DELTA_CONF, rng=rng)
            T_raw.append(int(T))
            rounds_raw.append(int(info["rounds"]))
            success_raw.append(bool(set(S) == truth))
        T_arr = np.array(T_raw, dtype=float)
        cell = {
            "delta": delta, "reps": REPS,
            "success_rate": float(np.mean(success_raw)),
            "T_mean": float(T_arr.mean()),
            "T_std": float(T_arr.std(ddof=1)),
            "T_ci95_halfwidth": float(1.96 * T_arr.std(ddof=1) / np.sqrt(REPS)),
            "T_median": float(np.median(T_arr)),
            "rounds_median": float(np.median(rounds_raw)),
            "wall_seconds": time.time() - t0,
            "T_raw": T_raw,
        }
        sweep.append(cell)
        print(f"[E3f] Delta={delta:.4f}: success={cell['success_rate']:.3f} "
              f"T={cell['T_mean']:.0f} +- {cell['T_ci95_halfwidth']:.0f} ({cell['wall_seconds']:.0f}s)",
              flush=True)

    return finalize(sweep, None)


def finalize(sweep, prev):
    lam = prev["lambda_G"] if prev else lambda_G(complete_graph(N))
    t0all = prev["wall_seconds_total"] if prev else 0.0
    # ---------------- fits ----------------
    d = np.array([c["delta"] for c in sweep])
    m = np.array([c["T_mean"] for c in sweep])
    se = np.array([c["T_ci95_halfwidth"] for c in sweep])

    def loglog_fit(mask):
        x, y = np.log(d[mask]), np.log(m[mask])
        slope, intercept = np.polyfit(x, y, 1)
        yhat = slope * x + intercept
        r2 = 1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        return {"slope": float(slope), "intercept": float(intercept), "r_squared": float(r2),
                "n_points": int(mask.sum()),
                "range": [float(d[mask].min()), float(d[mask].max())]}

    pieces = {
        "delta_lt_0.2": loglog_fit(d < 0.2),
        "delta_0.2_to_0.6": loglog_fit((d >= 0.2) & (d <= 0.6)),
        "delta_gt_0.6": loglog_fit(d > 0.6),
        "full": loglog_fit(np.ones_like(d, dtype=bool)),
    }

    # two-term OLS: T = a/d^2 + b/d, with bootstrap CIs over repetitions
    def two_term_fit(idx):
        X = np.column_stack([d[idx] ** -2, d[idx] ** -1])
        y = m[idx]
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ coef
        dof = max(len(idx) - 2, 1)
        s2 = (resid ** 2).sum() / dof
        cov = s2 * np.linalg.inv(X.T @ X)
        return coef, np.sqrt(np.diag(cov))

    coef, se_coef = two_term_fit(np.ones_like(d, dtype=bool))
    rng = np.random.default_rng(12345)
    boots = []
    for _ in range(2000):
        idx = np.arange(len(d))
        sample_idx = []
        for i in idx:  # resample repetitions within each Delta, recompute mean
            reps = np.array(sweep[i]["T_raw"])
            sample_idx.append(np.mean(rng.choice(reps, size=REPS, replace=True)))
        mb = np.array(sample_idx)
        X = np.column_stack([d ** -2, d ** -1])
        cb, *_ = np.linalg.lstsq(X, mb, rcond=None)
        boots.append(cb)
    boots = np.array(boots)
    boot_ci = {
        "a": [float(np.percentile(boots[:, 0], 2.5)), float(np.percentile(boots[:, 0], 97.5))],
        "b": [float(np.percentile(boots[:, 1], 2.5)), float(np.percentile(boots[:, 1], 97.5))],
    }
    yhat2 = coef[0] * d ** -2 + coef[1] * d ** -1
    r2_two = 1 - ((m - yhat2) ** 2).sum() / ((m - m.mean()) ** 2).sum()

    # threshold-derived one-parameter model: T = A / (sqrt(1+4d)-1)^2
    basis = 1.0 / (np.sqrt(1 + 4 * d) - 1) ** 2
    A_fit = float((basis @ m) / (basis @ basis))
    yhat3 = A_fit * basis
    r3 = 1 - ((m - yhat3) ** 2).sum() / ((m - m.mean()) ** 2).sum()
    # local exponent of the threshold model at each sampled Delta
    local_exp = -2.0 * d * (2.0 / np.sqrt(1 + 4 * d)) / (np.sqrt(1 + 4 * d) - 1)  # d/dDelta ln(sqrt(1+4d)-1) = 2/(sqrt(1+4d))

    out = {
        "experiment": "E3-fine", "algorithm": "graph_walk_elimination", "graph": "complete",
        "n": N, "k": K, "delta_conf": DELTA_CONF, "ci_level_pct": 95,
        "reps_per_point": REPS, "n_points": len(sweep),
        "lambda_G": lam,
        "sweep": sweep,
        "piecewise_loglog_fits": pieces,
        "two_term_fit": {"model": "T = a/Delta^2 + b/Delta",
                         "a": float(coef[0]), "a_se": float(se_coef[0]),
                         "b": float(coef[1]), "b_se": float(se_coef[1]),
                         "a_bootstrap_ci95": boot_ci["a"],
                         "b_bootstrap_ci95": boot_ci["b"],
                         "r_squared": float(r2_two)},
        "threshold_model_fit": {"model": "T = A/(sqrt(1+4*Delta)-1)^2 (from the exact stopping-rule algebra)",
                                "A": A_fit, "r_squared": float(r3),
                                "local_exponent_at_points": {f"{dd:.4f}": float(le)
                                                             for dd, le in zip(d, local_exp)}},
        "wall_seconds_total": t0all,
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "e3_fine.json").write_text(json.dumps(out, indent=1))
    print(f"\npiecewise slopes: " + ", ".join(f"{k}: {v['slope']:.3f} (R2 {v['r_squared']:.3f}, n={v['n_points']})"
                                              for k, v in pieces.items()))
    print(f"two-term fit: a={coef[0]:.1f} +- {se_coef[0]:.1f}, b={coef[1]:.1f} +- {se_coef[1]:.1f}, R2={r2_two:.4f}")
    print(f"threshold model: A={A_fit:.1f}, R2={r3:.4f}")
    print("wrote", RESULTS / "e3_fine.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
