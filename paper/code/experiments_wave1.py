#!/usr/bin/env python3
"""Wave 1 experiments: E2 (T vs 1/lambda_G across graph families), E4 (error rate
under a capped budget), E5 (uniform_majority baseline vs graph_walk_elimination).

Same anti-fabrication rules as experiments.py: repetition counts recorded as run,
raw per-repetition values stored, all numbers land in paper/results/*.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulate import (complete_graph, cycle_graph, star_graph, dumbbell_graph,
                      random_graph, lambda_G, make_theta_bounded)
from algorithms import graph_walk_elimination, uniform_majority

RESULTS = Path(__file__).resolve().parent.parent / "results"
DELTA_CONF = 0.05
K = 3
REPS = 100


def _run_rep(algo, theta, G, k, delta, rng, max_T=None):
    if max_T is None:
        return algo(theta, G, k, delta, rng=rng)
    return algo(theta, G, k, delta, rng=rng, max_T=max_T)


def _stats(T_raw, success_raw, rounds_raw, t0, extra=None):
    T_arr = np.array(T_raw, dtype=float)
    mean, std = float(T_arr.mean()), float(T_arr.std(ddof=1))
    cell = {
        "reps": len(T_raw),
        "success_rate": float(np.mean(success_raw)),
        "T_mean": mean,
        "T_std": std,
        "T_ci95_halfwidth": float(1.96 * std / np.sqrt(len(T_raw))) if len(T_raw) > 1 else 0.0,
        "T_median": float(np.median(T_arr)),
        "rounds_median": float(np.median(rounds_raw)),
        "wall_seconds": time.time() - t0,
        "T_raw": T_raw,
        "success_raw": success_raw,
    }
    if extra:
        cell.update(extra)
    return cell


# ---------------------------------------------------------------------------
# E2: same n, same Delta, four graph families -- T against 1/lambda_G
# ---------------------------------------------------------------------------
def e2(reps: int = REPS, n: int = 50, delta: float = 0.5) -> dict:
    graphs = [
        ("complete", complete_graph(n)),
        ("random_p0.15", random_graph(n, 0.15, np.random.default_rng(7))),
        ("star", star_graph(n)),
        ("dumbbell", dumbbell_graph(n)),
        ("cycle", cycle_graph(n)),
    ]
    theta = make_theta_bounded(n, delta, K)
    truth = set(range(K))
    configs = []
    for name, G in graphs:
        lam = lambda_G(G)
        T_raw, success_raw, rounds_raw = [], [], []
        t0 = time.time()
        for rep in range(reps):
            rng = np.random.default_rng(200_000 + rep)
            S, T, info = _run_rep(graph_walk_elimination, theta, G, K, DELTA_CONF, rng)
            T_raw.append(int(T))
            rounds_raw.append(int(info["rounds"]))
            success_raw.append(bool(set(S) == truth))
        cell = _stats(T_raw, success_raw, rounds_raw, t0,
                      {"graph": name, "n": n, "delta": delta, "lambda_G": lam,
                       "inv_lambda_G": 1.0 / lam, "m_edges": int(len(G["edges"]))})
        configs.append(cell)
        print(f"[E2] {name:>12s}: lambda_G={lam:.5f} 1/lam={1/lam:8.1f} reps={cell['reps']} "
              f"success={cell['success_rate']:.2f} T={cell['T_mean']:.0f} ({cell['wall_seconds']:.0f}s)", flush=True)
    # correlation of log T with log(1/lambda_G) across families
    x = np.log([c["inv_lambda_G"] for c in configs])
    y = np.log([c["T_mean"] for c in configs])
    slope = float(np.polyfit(x, y, 1)[0])
    return {"experiment": "E2", "algorithm": "graph_walk_elimination", "n": n,
            "delta": delta, "delta_conf": DELTA_CONF, "k": K, "ci_level_pct": 95,
            "reps_per_graph": reps, "configs": configs,
            "loglog_slope_T_vs_inv_lambda": slope}


# ---------------------------------------------------------------------------
# E4: capped budget -> error rate curve
# ---------------------------------------------------------------------------
def e4(reps: int = REPS, n: int = 20, delta: float = 0.5) -> dict:
    G = complete_graph(n)
    theta = make_theta_bounded(n, delta, K)
    truth = set(range(K))
    budgets = [1000, 2000, 3000, 4000, 5000, 6000, 8000, 10000, 12000, 16000]
    sweep = []
    for B in budgets:
        T_raw, err_raw = [], []
        t0 = time.time()
        for rep in range(reps):
            rng = np.random.default_rng(300_000 + rep)
            S, T, info = _run_rep(graph_walk_elimination, theta, G, K, DELTA_CONF, rng, max_T=B)
            T_raw.append(int(T))
            err_raw.append(bool(set(S) != truth))
        cell = _stats(T_raw, [not e for e in err_raw], [0] * reps, t0,
                      {"budget": B, "error_rate": float(np.mean(err_raw))})
        sweep.append(cell)
        print(f"[E4] B={B:6d}: reps={cell['reps']} error_rate={cell['error_rate']:.2f} "
              f"T_mean={cell['T_mean']:.0f} ({cell['wall_seconds']:.0f}s)", flush=True)
    return {"experiment": "E4", "algorithm": "graph_walk_elimination", "graph": "complete",
            "n": n, "delta": delta, "delta_conf": DELTA_CONF, "k": K, "ci_level_pct": 95,
            "reps_per_budget": reps, "sweep": sweep}


# ---------------------------------------------------------------------------
# E5: uniform_majority baseline vs graph_walk_elimination
# ---------------------------------------------------------------------------
def e5(reps: int = REPS, n: int = 20, delta: float = 0.5) -> dict:
    out = {"experiment": "E5", "baseline": "uniform_majority", "algorithm": "graph_walk_elimination",
           "n": n, "delta": delta, "delta_conf": DELTA_CONF, "k": K, "ci_level_pct": 95,
           "reps_per_point": reps, "graphs": []}
    theta = make_theta_bounded(n, delta, K)
    truth = set(range(K))
    for gname, G in (("complete", complete_graph(n)), ("cycle", cycle_graph(n))):
        # our algorithm at its delta-correct operating point
        T_raw, success_raw = [], []
        for rep in range(reps):
            rng = np.random.default_rng(400_000 + rep)
            S, T, info = graph_walk_elimination(theta, G, K, DELTA_CONF, rng=rng)
            T_raw.append(int(T))
            success_raw.append(bool(set(S) == truth))
        ours = _stats(T_raw, success_raw, [0] * reps, time.time(),
                      {"graph": gname})
        # baseline budget sweep
        budgets = [500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000]
        sweep = []
        for B in budgets:
            err_raw = []
            for rep in range(reps):
                rng = np.random.default_rng(500_000 + rep)
                S, T, info = uniform_majority(theta, G, K, B, rng=rng)
                err_raw.append(bool(set(S) != truth))
            sweep.append({"budget": B, "reps": reps, "error_rate": float(np.mean(err_raw))})
            print(f"[E5] {gname:>8s} B={B:7d}: baseline error={sweep[-1]['error_rate']:.2f}", flush=True)
        # min budget reaching error <= max(0.05, ours) -- None if never
        target = max(0.05, ours["success_rate"] and (1 - ours["success_rate"]))
        reached = [s["budget"] for s in sweep if s["error_rate"] <= max(0.05, 1 - ours["success_rate"])]
        B_star = min(reached) if reached else None
        ratio = (B_star / ours["T_mean"]) if B_star else None
        out["graphs"].append({
            "graph": gname, "ours": ours, "baseline_sweep": sweep,
            "baseline_min_budget_within_0.05": B_star,
            "budget_ratio_baseline_over_ours": ratio,
        })
        print(f"[E5] {gname:>8s}: ours T={ours['T_mean']:.0f} success={ours['success_rate']:.2f}; "
              f"baseline B*={B_star} ratio={ratio}", flush=True)
    return out



# ---------------------------------------------------------------------------
# E2b: uniform per-edge one-shot estimator (the algorithm analyzed in Thm 4.2):
# sample each edge m times, regularized MLE, output top-k by theta_hat.
# Sweep m per graph family to find m* (success >= 0.95); theory: T* = m* m_edges
# scales like m_edges / (sigma'_min lambda_G Delta^2).
# ---------------------------------------------------------------------------
def uniform_edge_topk(theta, G, k, m, rng):
    import algorithms as A
    edges = G["edges"]
    pairs = np.repeat(edges, m, axis=0)
    winners = A._bt(pairs, theta, rng)
    acc = {}
    A._aggregate(acc, pairs, winners)
    ue = np.array(sorted(acc.keys()))
    counts = np.array([acc[tuple(e)][0] for e in ue])
    wins = np.array([acc[tuple(e)][1] for e in ue])
    theta_hat, _ = A._mle(ue, counts, wins, G["n"])
    S = np.argsort(-theta_hat)[:k].tolist()
    return S, int(m * len(edges))


def e2b(reps: int = 50, n: int = 20, delta: float = 0.5) -> dict:
    graphs = [
        ("complete", complete_graph(n)),
        ("random_p0.2", random_graph(n, 0.2, np.random.default_rng(7))),
        ("star", star_graph(n)),
        ("dumbbell", dumbbell_graph(n)),
        ("cycle", cycle_graph(n)),
    ]
    theta = make_theta_bounded(n, delta, K)
    truth = set(range(K))
    m_grid = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
    families = []
    for name, G in graphs:
        lam = lambda_G(G)
        m_edges = int(len(G["edges"]))
        sweep = []
        m_star = None
        for m in m_grid:
            ok = 0
            for rep in range(reps):
                rng = np.random.default_rng(600_000 + rep)
                S, T = uniform_edge_topk(theta, G, K, m, rng)
                ok += int(set(S) == truth)
            rate = ok / reps
            sweep.append({"m_per_edge": m, "reps": reps, "success_rate": rate,
                          "T_total": int(m * m_edges)})
            if m_star is None and rate >= 0.95:
                m_star = m
                break
        families.append({"graph": name, "m_edges": m_edges, "lambda_G": lam,
                         "inv_lambda_G": 1.0 / lam, "m_edges_over_lambda": m_edges / lam,
                         "m_star": m_star, "T_star": (m_star * m_edges) if m_star else None,
                         "sweep": sweep})
        print(f"[E2b] {name:>12s}: m*={m_star} T*={m_star * m_edges if m_star else None} "
              f"m_edges/lambda={m_edges / lam:.1f}", flush=True)
    # scaling regression of log T* on log(m_edges / lambda_G) across families
    xs = [np.log(f["m_edges_over_lambda"]) for f in families if f["T_star"]]
    ys = [np.log(f["T_star"]) for f in families if f["T_star"]]
    slope = float(np.polyfit(xs, ys, 1)[0]) if len(xs) >= 2 else None
    return {"experiment": "E2b", "estimator": "uniform_edge_topk (one-shot per-edge MLE)",
            "n": n, "delta": delta, "delta_conf": DELTA_CONF, "k": K, "ci_level_pct": 95,
            "reps_per_point": reps, "success_target": 0.95, "families": families,
            "loglog_slope_Tstar_vs_medges_over_lambda": slope}



def e2c(reps: int = 50, n: int = 50, delta: float = 0.5) -> dict:
    """E2c: the lambda_G cost made visible -- place the top-k boundary ACROSS the
    dumbbell bridge (k = n//2) and compare the one-shot estimator's m* against the
    complete graph at the same n, k, Delta."""
    k = n // 2
    graphs = [("complete", complete_graph(n)), ("dumbbell", dumbbell_graph(n))]
    theta = make_theta_bounded(n, delta, k)
    truth = set(range(k))
    m_grid = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]
    families = []
    for name, G in graphs:
        lam = lambda_G(G)
        m_edges = int(len(G["edges"]))
        sweep = []
        m_star = None
        for m in m_grid:
            ok = 0
            for rep in range(reps):
                rng = np.random.default_rng(700_000 + rep)
                S, T = uniform_edge_topk(theta, G, k, m, rng)
                ok += int(set(S) == truth)
            rate = ok / reps
            sweep.append({"m_per_edge": m, "reps": reps, "success_rate": rate,
                          "T_total": int(m * m_edges)})
            if m_star is None and rate >= 0.95:
                m_star = m
                break
        families.append({"graph": name, "k": k, "m_edges": m_edges, "lambda_G": lam,
                         "m_star": m_star, "T_star": (m_star * m_edges) if m_star else None,
                         "sweep": sweep})
        print(f"[E2c] {name:>10s}: k={k} m*={m_star} T*={m_star * m_edges if m_star else None} "
              f"lambda={lam:.4f}", flush=True)
    ratio = None
    if families[0]["T_star"] and families[1]["T_star"]:
        ratio = families[1]["T_star"] / families[0]["T_star"]
    return {"experiment": "E2c", "estimator": "uniform_edge_topk (one-shot per-edge MLE)",
            "n": n, "delta": delta, "ci_level_pct": 95, "reps_per_point": reps,
            "success_target": 0.95, "families": families,
            "T_star_ratio_dumbbell_over_complete": ratio}


def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    for name, fn, fname in (("E1", __import__("experiments").e1, "e1.json"),
                            ("E3", __import__("experiments").e3, "e3.json"),
                            ("E2", e2, "e2.json"), ("E2b", e2b, "e2b.json"),
                            ("E2c", e2c, "e2c.json"), ("E4", e4, "e4.json"), ("E5", e5, "e5.json")):
        out = fn()
        (RESULTS / fname).write_text(json.dumps(out, indent=1))
        print(f"wrote {RESULTS / fname}", flush=True)
    print("\nE2 log-log slope of T vs 1/lambda_G across families:",
          json.load(open(RESULTS / "e2.json"))["loglog_slope_T_vs_inv_lambda"], flush=True)


if __name__ == "__main__":
    main()
