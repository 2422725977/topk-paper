#!/usr/bin/env python3
"""W0.4: Three top-k identification algorithms under Bradley-Terry preferences.

All algorithms may only compare pairs that are edges of the given graph G.  The two
elimination algorithms share one statistical core: per round, fit a regularized BT
maximum-likelihood estimate (MLE) on all data accumulated so far, build per-item
confidence radii from the observed Fisher information, and eliminate items that
cannot be in the top-k because k other actives dominate them lower-bound vs
upper-bound.  They differ ONLY in how comparisons are sampled:

  uniform_majority       -- fixed budget, uniform random edges, win-rate vote (baseline;
                            a valid ranking statistic on balanced graphs like K_n)
  successive_elimination -- rounds; every active item plays c_r comparisons against
                            uniform random G-neighbors; c_r doubles each round
  graph_walk_elimination -- the paper's algorithm; every active item launches a random
                            walk of c_r steps from itself and each traversed edge is
                            one comparison.  Sampling is local: information reaches
                            far items only through the walk, so the graph's algebraic
                            connectivity lambda_G governs how fast per-item information
                            accumulates.

Numerical safeguards (Wave 0 pragmatics, documented for Wave 1 theory):
  * Newton iterates are step-clipped and the MLE can diverge on linearly separable
    (saturated) edge data; the ordering of a diverged MLE is still the data ordering.
  * Confidence radii use the observed Fisher curvature with a small floor (1e-3) so
    saturated edges cannot make radii explode; on truly saturated edges this is a
    heuristic stand-in for a one-sided bound -- the empirical success rate of every
    experiment is reported as measured, never assumed.

Every function returns (S_hat, T, info): estimated top-k set, total comparisons used,
and an info dict (rounds, t_history, capped flag).
"""

from __future__ import annotations

import numpy as np
from scipy.special import expit, log_expit

from simulate import make_theta  # noqa: F401  (re-exported for convenience)

_MU = 1e-6          # ridge pinning the gauge
_MAX_NEWTON = 25
_STEP_CLIP = 10.0
_CURV_FLOOR = 1e-3  # curvature floor for confidence radii
_MAX_ROUNDS = 60
_C_MAX = 1 << 15


# ---------------------------------------------------------------------------
# Graph adjacency in flat CSR form (for vectorized neighbor sampling / walks)
# ---------------------------------------------------------------------------
def _flat_adjacency(G: dict):
    n = G["n"]
    deg = G["adj"].sum(axis=1).astype(int)
    indptr = np.zeros(n + 1, dtype=int)
    indptr[1:] = np.cumsum(deg)
    indices = np.concatenate([np.nonzero(G["adj"][v])[0] for v in range(n)]) if n else np.array([], dtype=int)
    return indptr, indices, deg


def _random_neighbors(indptr: np.ndarray, indices: np.ndarray, deg: np.ndarray,
                      sources: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One uniform random neighbor per entry of `sources` (vectorized)."""
    pick = (rng.random(len(sources)) * deg[sources]).astype(int)
    return indices[indptr[sources] + pick]


# ---------------------------------------------------------------------------
# Regularized BT MLE on aggregated edge data
# ---------------------------------------------------------------------------
def _mle(pairs: np.ndarray, counts: np.ndarray, wins: np.ndarray, n: int):
    """Damped Newton on the BT log-likelihood with ridge _MU.

    pairs: (m,2) undirected edges; counts: (m,) samples; wins: (m,) wins by the FIRST
    endpoint.  Returns (theta_hat centered to zero mean, H = curvature matrix + _MU I).
    """
    i, j = pairs[:, 0], pairs[:, 1]
    pbar = wins / np.maximum(counts, 1)
    u = np.zeros((len(pairs), n))
    u[np.arange(len(pairs)), i] = 1.0
    u[np.arange(len(pairs)), j] = -1.0

    def neg_ll(t: np.ndarray) -> float:
        d = u @ t
        # NLL = -[ p*log sigma(d) + (1-p)*log sigma(-d) ]
        return float(-(counts * (pbar * log_expit(d) + (1 - pbar) * log_expit(-d))).sum()
                     + 0.5 * _MU * t @ t)

    theta = np.zeros(n)
    obj = neg_ll(theta)
    for _ in range(_MAX_NEWTON):
        d = u @ theta
        s = expit(d)
        grad = u.T @ (counts * (s - pbar)) + _MU * theta
        w = counts * s * (1 - s)
        H = u.T @ (u * w[:, None]) + _MU * np.eye(n)
        step = np.linalg.solve(H, grad)
        step = np.clip(step, -_STEP_CLIP, _STEP_CLIP)
        tau = 1.0
        improved = False
        for _ in range(30):
            cand = theta - tau * step
            cand -= cand.mean()  # gauge pinning (pairwise diffs are shift-invariant)
            new_obj = neg_ll(cand)
            if new_obj <= obj + 1e-12:
                theta, obj = cand, new_obj
                improved = True
                break
            tau *= 0.5
        if not improved:
            break
        if np.abs(step).max() < 1e-9:
            break
    d = u @ theta
    s = expit(d)
    # CI curvature: floor the per-sample curvature so saturated (separable) edges
    # cannot drive H -> 0 and explode the radii.  Returned WITHOUT the Newton ridge:
    # the likelihood is shift-invariant, so H is singular along the gauge direction
    # and _confidence_radii must use a pseudo-inverse instead.
    w_ci = counts * np.maximum(s * (1 - s), _CURV_FLOOR)
    H_ci = u.T @ (u * w_ci[:, None])
    return theta, H_ci


def _confidence_radii(H: np.ndarray, n: int, delta: float, round_idx: int) -> np.ndarray:
    """radius_i = sqrt(b * (H^+)_ii), pseudo-inverse over the gauge's orthogonal
    complement; b is a union bound over items x rounds."""
    Hinv_diag = np.linalg.pinv(H).diagonal()
    b = 2.0 * np.log(4.0 * n * max(round_idx, 1) / delta)
    return np.sqrt(b * np.maximum(Hinv_diag, 1e-12))


def _eliminate(theta_hat: np.ndarray, radii: np.ndarray, active: list[int], k: int) -> list[int]:
    lb = {i: theta_hat[i] - radii[i] for i in active}
    ub = {i: theta_hat[i] + radii[i] for i in active}
    lbs = sorted((lb[i] for i in active), reverse=True)
    if len(active) <= k or len(lbs) < k:
        return list(active)
    kth_lb = lbs[k - 1]
    survivors = [i for i in active if ub[i] >= kth_lb]
    if len(survivors) < k:  # safety: never drop below k in one round
        keep = set(sorted(active, key=lambda i: -ub[i])[:k])
        survivors = [i for i in active if i in keep]
    return survivors


def _bt(pairs: np.ndarray, theta: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Vectorized BT outcomes for (m,2) pairs; returns winner index per row."""
    p_first = expit(theta[pairs[:, 0]] - theta[pairs[:, 1]])
    return np.where(rng.random(len(pairs)) < p_first, pairs[:, 0], pairs[:, 1])


def _aggregate(acc: dict, pairs: np.ndarray, winners: np.ndarray) -> None:
    """Accumulate comparisons as unique undirected edges with (count, lo-endpoint-wins).

    Orientation matters: 'first wins' is counted w.r.t. the canonical (lo, hi)
    ordering of the edge, because both sampling directions (i,j) and (j,i) of the
    same undirected edge must land in the same bucket with consistent labels.
    """
    lo = np.minimum(pairs[:, 0], pairs[:, 1])
    hi = np.maximum(pairs[:, 0], pairs[:, 1])
    first_won = (winners == lo).astype(np.int64)
    keys = np.stack([lo, hi], axis=1)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    inv = np.reshape(inv, -1)
    cnt = np.bincount(inv, minlength=len(uniq))
    win = np.bincount(inv, weights=first_won, minlength=len(uniq)).astype(np.int64)
    for e_idx in range(len(uniq)):
        e = (int(uniq[e_idx, 0]), int(uniq[e_idx, 1]))
        c, w = acc.get(e, (0, 0))
        acc[e] = (c + int(cnt[e_idx]), w + int(win[e_idx]))


# ---------------------------------------------------------------------------
# 1) uniform_majority: fixed budget, uniform random edges, normalized win rates
# ---------------------------------------------------------------------------
def uniform_majority(theta: np.ndarray, G: dict, k: int, budget: int,
                     rng: np.random.Generator | None = None) -> tuple[list[int], int, dict]:
    rng = rng or np.random.default_rng()
    edges = G["edges"]
    if len(edges) == 0:
        raise ValueError("graph has no edges")
    idx = rng.integers(0, len(edges), size=budget)
    pairs = edges[idx]
    winners = _bt(pairs, theta, rng)
    plays = np.zeros(G["n"])
    wins = np.zeros(G["n"])
    np.add.at(plays, pairs[:, 0], 1)
    np.add.at(plays, pairs[:, 1], 1)
    np.add.at(wins, winners.astype(int), 1)
    score = np.divide(wins, plays, out=np.full(G["n"], -np.inf), where=plays > 0)
    S = sorted(np.argsort(-score)[:k].tolist())
    return S, int(budget), {"rounds": 1}


# ---------------------------------------------------------------------------
# 2)+3) shared elimination engine
# ---------------------------------------------------------------------------
def _run_elimination(theta: np.ndarray, G: dict, k: int, delta: float,
                     rng: np.random.Generator, scheme: str) -> tuple[list[int], int, dict]:
    n = G["n"]
    indptr, indices, deg = _flat_adjacency(G)
    acc: dict = {}
    active = list(range(n))
    T = 0
    t_history: list[int] = []
    theta_hat = np.zeros(n)
    c = 1
    capped = False
    for r in range(1, _MAX_ROUNDS + 1):
        if scheme == "uniform_neighbors":
            rep = np.repeat(np.array(active, dtype=int), c)
            opp = _random_neighbors(indptr, indices, deg, rep, rng)
            pairs = np.column_stack([rep, opp])
        elif scheme == "random_walk":
            walkers = np.array(active, dtype=int)  # one walk per active item
            steps = []
            for _ in range(c):
                nxt = _random_neighbors(indptr, indices, deg, walkers, rng)
                steps.append(np.column_stack([walkers, nxt]))
                walkers = nxt
            pairs = np.vstack(steps)
        else:
            raise ValueError(scheme)

        winners = _bt(pairs, theta, rng)
        _aggregate(acc, pairs, winners)
        T += len(pairs)
        t_history.append(T)

        ue = np.array(sorted(acc.keys()))
        counts = np.array([acc[tuple(e)][0] for e in ue])
        wins = np.array([acc[tuple(e)][1] for e in ue])
        theta_hat, H = _mle(ue, counts, wins, n)
        radii = _confidence_radii(H, n, delta, r)
        new_active = _eliminate(theta_hat, radii, active, k)
        if len(new_active) == k:
            S = sorted(new_active, key=lambda i: -theta_hat[i])
            return S, T, {"rounds": r, "t_history": t_history, "capped": False}
        active = new_active
        if c < _C_MAX:
            c *= 2
        else:
            capped = True
    S = sorted(active, key=lambda i: -theta_hat[i])[:k]
    return S, T, {"rounds": _MAX_ROUNDS, "t_history": t_history, "capped": capped}


def successive_elimination(theta: np.ndarray, G: dict, k: int, delta: float,
                           rng: np.random.Generator | None = None) -> tuple[list[int], int, dict]:
    """Successive elimination with uniform-neighbor sampling and doubling rounds."""
    rng = rng or np.random.default_rng()
    return _run_elimination(theta, G, k, delta, rng, scheme="uniform_neighbors")


def graph_walk_elimination(theta: np.ndarray, G: dict, k: int, delta: float,
                           rng: np.random.Generator | None = None) -> tuple[list[int], int, dict]:
    """The paper's algorithm: per-item random-walk comparisons + CI elimination."""
    rng = rng or np.random.default_rng()
    return _run_elimination(theta, G, k, delta, rng, scheme="random_walk")
