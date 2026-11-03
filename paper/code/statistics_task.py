#!/usr/bin/env python3
"""Statistics task (nature-statistics): Wilson score intervals for all reported
success/error rates, and a full-grid re-measurement of E2b with interpolated
95%-success thresholds and bootstrap confidence intervals (reviewer R2-M2).

Unit of analysis: one algorithm repetition (fresh RNG stream) with the instance
fixed per configuration; rates are binomial point estimates over repetitions."""
import json, math, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate import complete_graph, cycle_graph, star_graph, dumbbell_graph, random_graph, lambda_G, make_theta_bounded
from experiments_wave1 import uniform_edge_topk

RESULTS = Path(__file__).resolve().parent.parent / "results"
Z = 1.959963985

def wilson(k, n, z=Z):
    if n == 0:
        return None
    p = k / n
    denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return [round(center - half, 4), round(center + half, 4)]

def add_wilson(obj):
    """Recursively add wilson95 to any dict carrying success_rate/error_rate + reps."""
    if isinstance(obj, dict):
        for key in ("success_rate", "error_rate"):
            if key in obj and isinstance(obj.get("reps", obj.get("reps_per_point", obj.get("reps_per_config", None))), int):
                rate = obj[key]
                n = obj["reps"] if "reps" in obj else obj.get("reps_per_point", obj.get("reps_per_config"))
                k = round(rate * n)
                obj["wilson95"] = wilson(k, n)
        for v in obj.values():
            add_wilson(v)
    elif isinstance(obj, list):
        for v in obj:
            add_wilson(v)

for name in ("e1", "e2", "e2b", "e2c", "e2d", "e3", "e3_fine", "e3_ue", "e4", "e5"):
    p = RESULTS / f"{name}.json"
    d = json.load(open(p))
    add_wilson(d)
    json.dump(d, open(p, "w"), indent=1)
print("Wilson intervals added to all result files")

# ---- key intervals quoted in the manuscript ----
e4 = json.load(open(RESULTS / "e4.json"))
print("E4 B_cap=1000 error 0.09 Wilson:", e4["sweep"][0]["wilson95"])
print("E4 B_cap=2000 error 0.02 Wilson:", e4["sweep"][1]["wilson95"])
e5 = json.load(open(RESULTS / "e5.json"))
print("E5 complete baseline @4000 error 0.01 Wilson:", e5["graphs"][0]["baseline_sweep"][3]["wilson95"])
print("E5 cycle baseline @128000 error 0.90 Wilson:", e5["graphs"][1]["baseline_sweep"][-1]["wilson95"])

# ---- E2b v2: full-grid sweep + interpolated m95 + bootstrap CI ----
K, REPS, DELTA = 3, 200, 0.5
truth = set(range(K))
families = [
    ("complete", complete_graph(20), [1, 2, 4, 8, 16, 32, 64]),
    ("random", random_graph(20, 0.2, np.random.default_rng(7)), [1, 2, 4, 8, 16, 32, 64, 128, 256]),
    ("star", star_graph(20), [1, 2, 4, 8, 16, 32, 64, 128]),
    ("dumbbell", dumbbell_graph(20), [1, 2, 4, 8, 16, 32, 64, 128]),
    ("cycle", cycle_graph(20), [1, 2, 4, 8, 16, 32, 64, 128, 256]),
]
def m95_from(rates, ms, target=0.95):
    """Logistic-in-log-m fit; return interpolated m at the target success rate."""
    ms = np.array(ms, dtype=float); rs = np.array(rates, dtype=float)
    ok = (rs > 0.02) & (rs < 0.98)
    if ok.sum() < 3:
        ok = np.ones(len(rs), dtype=bool)
    x, y = np.log(ms[ok]), np.log(np.clip(rs[ok], 1e-3, 1-1e-3)/(1-np.clip(rs[ok], 1e-3, 1-1e-3)))
    beta, alpha = np.polyfit(x, y, 1)
    if beta <= 0:
        return None
    return float(np.exp((math.log(target/(1-target)) - alpha) / beta))

t0 = time.time()
fam_out = []
rng_master = np.random.default_rng(424242)
for name, G, grid in families:
    lam = lambda_G(G)
    m_edges = int(len(G["edges"]))
    th = make_theta_bounded(20, DELTA, K)
    truth = set(range(K))
    grid_out = []
    rates = []
    for m in grid:
        succ = np.zeros(REPS, dtype=bool)
        for rep in range(REPS):
            rng = np.random.default_rng(2_000_000 + 77*rep)
            S, T = uniform_edge_topk(th, G, K, m, rng)
            succ[rep] = (set(S) == truth)
        grid_out.append({"m_per_edge": m, "reps": REPS, "success_rate": float(succ.mean()),
                         "wilson95": wilson(int(succ.sum()), REPS), "T_total": int(m*m_edges)})
        rates.append(succ)
        if succ.mean() >= 0.999 and len(grid_out) >= 4:
            pass  # keep sweeping the full grid for interpolation
    flat = [(m, r) for m, rr in zip(grid, rates) for r in rr]  # not used; bootstrap below
    m95_hat = m95_from([g["success_rate"] for g in grid_out], grid)
    # bootstrap over repetitions
    boots = []
    for b in range(2000):
        rs_b = [rng_master.choice(r, size=REPS, replace=True).mean() for r in rates]
        mb = m95_from(rs_b, grid)
        if mb is not None:
            boots.append(mb)
    lo, hi = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))) if boots else (None, None)
    T95 = m95_hat * m_edges if m95_hat else None
    fam_out.append({"graph": name, "m_edges": m_edges, "lambda_G": lam,
                    "m_edges_over_lambda": m_edges/lam,
                    "m95_interpolated": m95_hat,
                    "m95_bootstrap_ci95": [lo, hi],
                    "T95_interpolated": T95,
                    "T95_ci95": [lo*m_edges if lo else None, hi*m_edges if hi else None],
                    "grid": grid_out})
    print(f"[E2b-v2] {name:>9s}: m95={m95_hat:.1f} CI[{lo:.1f},{hi:.1f}] T95={T95:.0f} ({time.time()-t0:.0f}s)", flush=True)

# slope of log T95 vs log(m_edges/lambda_G) with bootstrap CI
xs = np.log([f["m_edges_over_lambda"] for f in fam_out])
ys = np.log([f["T95_interpolated"] for f in fam_out])
slope, ic = np.polyfit(xs, ys, 1)
r2 = 1 - ((ys-(slope*xs+ic))**2).sum()/((ys-ys.mean())**2).sum()
boot_slopes = []
for b in range(2000):
    idx = rng_master.integers(0, len(fam_out), len(fam_out))
    xbi = xs[idx]; ybi = ys[idx]
    if len(set(xbi)) < 2:
        continue
    sb, _ = np.polyfit(xbi, ybi, 1)
    boot_slopes.append(sb)
slope_ci = [float(np.percentile(boot_slopes, 2.5)), float(np.percentile(boot_slopes, 97.5))]
out = {"experiment": "E2b-v2", "estimator": "uniform_edge_topk", "n": 20, "delta": DELTA,
       "k": K, "delta_conf": 0.05, "ci_level_pct": 95, "reps_per_point": REPS,
       "method": "full-grid sweep with logistic-in-log-m interpolation of the 95% success threshold, bootstrap CIs over repetitions (2000 resamples)",
       "families": fam_out,
       "loglog_slope_T95_vs_medges_over_lambda": float(slope),
       "slope_bootstrap_ci95": slope_ci, "r_squared": float(r2)}
(RESULTS / "e2b_v2.json").write_text(json.dumps(out, indent=1))
print(f"slope: {slope:.3f} CI {slope_ci}  R2={r2:.4f}; wrote e2b_v2.json ({time.time()-t0:.0f}s)")
