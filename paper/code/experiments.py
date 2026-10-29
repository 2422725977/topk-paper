#!/usr/bin/env python3
"""W0.5: E1 (complete-graph scaling of T in n and Delta) and E3 (power-law slope of T vs Delta).

E1: complete graph, n in {10,20,50} x Delta in {0.2,0.5,1.0}, delta=0.05, k=3,
    100 repetitions per config.  Measures the comparisons T consumed by the paper's
    algorithm (graph_walk_elimination) and the empirical success rate; under the
    theory T ~ (n/Delta^2) * log(n/delta) / lambda_G with lambda_G = n for K_n,
    so T should be proportional to n/Delta^2.
E3: n=20, complete graph, Delta swept over 0.1..1.5, 100 repetitions per point;
    fits the log-log slope of T_mean vs Delta (theory: -2).

Raw per-repetition values are written to paper/results/e1.json and e3.json so that
every number quoted in the paper is greppable (SPEC sec 6.1).  Repetition counts are
recorded as actually run -- never rounded (SPEC sec 6.4).
"""

from __future__ import annotations

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
REPS = 100


def truth_topk(n: int, k: int) -> set[int]:
    return set(range(k))  # make_theta is decreasing in i


def run_cell(n: int, delta: float, reps: int, seed0: int = 0) -> dict:
    G = complete_graph(n)
    lam = lambda_G(G)
    theta = make_theta_bounded(n, delta, K)
    truth = truth_topk(n, K)
    T_raw, success_raw, rounds_raw = [], [], []
    t0 = time.time()
    for rep in range(reps):
        rng = np.random.default_rng(seed0 * 1_000_003 + rep)
        S, T, info = graph_walk_elimination(theta, G, K, DELTA_CONF, rng=rng)
        T_raw.append(int(T))
        rounds_raw.append(int(info["rounds"]))
        success_raw.append(bool(set(S) == truth))
    T_arr = np.array(T_raw, dtype=float)
    mean, std = float(T_arr.mean()), float(T_arr.std(ddof=1))
    ci = float(1.96 * std / np.sqrt(reps))
    return {
        "n": n,
        "delta": delta,
        "reps": reps,
        "lambda_G": lam,
        "success_rate": float(np.mean(success_raw)),
        "T_mean": mean,
        "T_std": std,
        "T_ci95_halfwidth": ci,
        "T_median": float(np.median(T_arr)),
        "n_over_delta2": n / delta**2,
        "T_over_n_delta2": mean / (n / delta**2),
        "rounds_median": float(np.median(rounds_raw)),
        "wall_seconds": time.time() - t0,
        "T_raw": T_raw,
        "success_raw": success_raw,
    }


def e1(reps: int = REPS) -> dict:
    out = {"experiment": "E1", "algorithm": "graph_walk_elimination", "graph": "complete",
           "delta_conf": DELTA_CONF, "k": K, "reps_per_config": reps, "ci_level_pct": 95,
           "description": "T vs n/Delta^2 on the complete graph with bounded-range "
                          "(tanh, B=3) utilities; algorithm is delta-correct with delta=0.05 "
                          "so its consumption is the T of interest",
           "configs": []}
    for n in (10, 20, 50):
        for delta in (0.2, 0.5, 1.0):
            cell = run_cell(n, delta, reps)
            out["configs"].append(cell)
            print(f"[E1] n={n:3d} Delta={delta:.1f}: reps={cell['reps']} success={cell['success_rate']:.2f} "
                  f"T_mean={cell['T_mean']:.0f} +- {cell['T_ci95_halfwidth']:.0f} "
                  f"T/(n/Delta^2)={cell['T_over_n_delta2']:.1f} ({cell['wall_seconds']:.1f}s)", flush=True)
    return out


def e3(reps: int = REPS) -> dict:
    n = 20
    deltas = [round(0.1 * i, 1) for i in range(1, 16)]  # 0.1 .. 1.5
    sweep = []
    for i, delta in enumerate(deltas):
        cell = run_cell(n, delta, reps, seed0=10_000 + i)
        sweep.append(cell)
        print(f"[E3] Delta={delta:.1f}: reps={cell['reps']} success={cell['success_rate']:.2f} "
              f"T_mean={cell['T_mean']:.0f} ({cell['wall_seconds']:.1f}s)", flush=True)
    x = np.log([c["delta"] for c in sweep])
    y = np.log([c["T_mean"] for c in sweep])

    def _fit(xs, ys):
        slope, intercept = np.polyfit(xs, ys, 1)
        y_hat = slope * xs + intercept
        ss_res = float(((ys - y_hat) ** 2).sum())
        ss_tot = float(((ys - ys.mean()) ** 2).sum())
        return {"log_log_slope": float(slope), "log_log_intercept": float(intercept),
                "r_squared": 1.0 - ss_res / ss_tot, "n_points": int(len(xs))}

    # Full sweep plus the small-gap subrange: for the Bradley-Terry model the
    # Delta^-2 law is a small-gap statement (the per-comparison information about a
    # gap of size Delta carries a sigma'(Delta) factor that decays once Delta ~ 1),
    # so the slope over Delta in [0.1, 0.5] is the cleaner check of the exponent.
    full = _fit(np.array(x), np.array(y))
    small_mask = np.array([c["delta"] <= 0.5 for c in sweep])
    small = _fit(np.array(x)[small_mask], np.array(y)[small_mask])
    # sigma'-normalized fit: the per-comparison Fisher information about a gap Delta
    # in the BT model carries a factor sigma'(Delta) = sigmoid'(Delta); the Delta^-2
    # count scaling is the small-gap statement.  Normalizing T by sigma'(Delta)
    # removes that model-intrinsic decay before fitting the exponent.
    sig_prime = np.array([float(_sigmoid_prime(c["delta"])) for c in sweep])
    y_adj = np.log([c["T_mean"] for c in sweep]) - np.log(sig_prime / 0.25)
    adj_full = _fit(np.array(x), y_adj)
    adj_small = _fit(np.array(x)[small_mask], y_adj[small_mask])
    fit = {"log_log_slope": full["log_log_slope"], "log_log_intercept": full["log_log_intercept"],
           "r_squared": full["r_squared"], "n_points": full["n_points"], "theory_slope": -2.0,
           "fit_full_range": full, "fit_small_gap_0.1_0.5": small,
           "fit_full_range_sigpr_adjusted": adj_full,
           "fit_small_gap_sigpr_adjusted": adj_small,
           "note": "small-gap and sigma'(Delta)-adjusted fits isolate the Delta^-2 "
                   "exponent from the BT information decay at large gaps"}
    return {"experiment": "E3", "algorithm": "graph_walk_elimination", "graph": "complete",
            "n": n, "delta_conf": DELTA_CONF, "k": K, "reps_per_point": reps,
            "ci_level_pct": 95,
            "lambda_G": lambda_G(complete_graph(n)), "sweep": sweep, "fit": fit}


def _sigmoid_prime(d: float) -> float:
    s = 1.0 / (1.0 + np.exp(-d))
    return float(s * (1 - s))


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    e1_out = e1()
    (RESULTS / "e1.json").write_text(json.dumps(e1_out, indent=1))
    print("wrote", RESULTS / "e1.json", flush=True)
    e3_out = e3()
    (RESULTS / "e3.json").write_text(json.dumps(e3_out, indent=1))
    print("wrote", RESULTS / "e3.json", flush=True)
    print(f"\nE3 fitted log-log slope: {e3_out['fit']['log_log_slope']:.3f} "
          f"(theory -2.0), R^2 = {e3_out['fit']['r_squared']:.4f}", flush=True)


if __name__ == "__main__":
    main()
