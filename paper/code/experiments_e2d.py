#!/usr/bin/env python3
"""E2d: n-scaling of the analyzed one-shot estimator (UE-topk) on the complete graph.
Addresses the review point that Theorem 5.1's n-dependence was never measured:
theorem predicts m* ~ log(n/delta)/(sigma_min lambda_G Delta^2) with lambda_G = n,
so T* = m* m_edges grows linearly in n up to the log factor."""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate import complete_graph, lambda_G, make_theta_bounded
from experiments_wave1 import uniform_edge_topk

RESULTS = Path(__file__).resolve().parent.parent / "results"
K, REPS, DELTA = 3, 50, 0.5
truth = set(range(K))
m_grid = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
families = []
for n in (10, 20, 50):
    G = complete_graph(n)
    lam = lambda_G(G)
    th = make_theta_bounded(n, DELTA, K)
    m_star = None; rows = []
    for m in m_grid:
        ok = 0
        for rep in range(REPS):
            rng = np.random.default_rng(1_100_000 + rep)
            S, T = uniform_edge_topk(th, G, K, m, rng)
            ok += int(set(S) == truth)
        rate = ok / REPS
        rows.append({"m_per_edge": m, "reps": REPS, "success_rate": rate, "T_total": int(m*len(G["edges"]))})
        if m_star is None and rate >= 0.95:
            m_star = m; break
    families.append({"n": n, "m_edges": int(len(G["edges"])), "lambda_G": lam,
                     "m_star": m_star, "T_star": (m_star*len(G["edges"])) if m_star else None, "sweep": rows})
    print(f"[E2d] n={n}: m*={m_star} T*={m_star*len(G['edges']) if m_star else None}", flush=True)
xs = np.log([f["n"] for f in families if f["T_star"]])
ys = np.log([f["T_star"] for f in families if f["T_star"]])
slope, intercept = np.polyfit(xs, ys, 1)
r2 = 1 - ((ys-(slope*xs+intercept))**2).sum()/((ys-ys.mean())**2).sum()
out = {"experiment": "E2d", "estimator": "uniform_edge_topk (analyzed in Theorem 5.1)",
       "graph": "complete", "delta": DELTA, "k": K, "delta_conf": 0.05, "ci_level_pct": 95,
       "reps_per_point": REPS, "success_target": 0.95, "families": families,
       "loglog_slope_Tstar_vs_n": float(slope), "loglog_intercept": float(intercept),
       "r_squared": float(r2), "theory_note": "T* = Theta(n log(n/delta)/Delta^2) on K_n, i.e. log-log slope 1 up to the log(n/delta) factor"}
(RESULTS/"e2d.json").write_text(json.dumps(out, indent=1))
print(f"slope of log T* vs log n: {slope:.3f} (R2={r2:.4f}); theory ~1 + log-factor")
