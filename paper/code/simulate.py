#!/usr/bin/env python3
"""W0.3: Bradley-Terry sampler + comparison-graph generators + measured algebraic connectivity.

Graph G is represented as a dict:
    {"n": int, "adj": np.ndarray(bool, (n,n)), "edges": np.ndarray(int, (m,2))}
lambda_G is the second-smallest eigenvalue of the graph Laplacian, computed with
numpy's eigvalsh on the *actual* Laplacian matrix -- no closed-form approximations
(SPEC sec 5: 图参数必须实测).

Run as a script to print the measured lambda_G of all five graph families plus a
BT-sampler sanity check.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
def _finish(n: int, adj: np.ndarray) -> dict:
    edges = np.array(sorted({tuple(sorted((int(i), int(j)))) for i, j in zip(*np.nonzero(np.triu(adj)))}),
                     dtype=int).reshape(-1, 2)
    return {"n": n, "adj": adj.astype(bool), "edges": edges}


def complete_graph(n: int) -> dict:
    adj = np.ones((n, n), dtype=bool)
    np.fill_diagonal(adj, False)
    return _finish(n, adj)


def cycle_graph(n: int) -> dict:
    adj = np.zeros((n, n), dtype=bool)
    for i in range(n):
        adj[i, (i + 1) % n] = True
        adj[(i + 1) % n, i] = True
    return _finish(n, adj)


def star_graph(n: int) -> dict:
    adj = np.zeros((n, n), dtype=bool)
    adj[0, 1:] = True
    adj[1:, 0] = True
    return _finish(n, adj)


def random_graph(n: int, p: float, rng: np.random.Generator | None = None, ensure_connected: bool = True) -> dict:
    rng = rng or np.random.default_rng()
    while True:
        upper = rng.random((n, n)) < p
        adj = np.triu(upper, 1) | np.triu(upper, 1).T
        if not ensure_connected or is_connected(adj):
            return _finish(n, adj)


def dumbbell_graph(n: int) -> dict:
    """Two cliques of size n//2 joined by a single bridge edge (classic bottleneck)."""
    assert n >= 6 and n % 2 == 0, "use an even n >= 6"
    h = n // 2
    adj = np.zeros((n, n), dtype=bool)
    adj[:h, :h] = ~np.eye(h, dtype=bool)          # left clique
    adj[h:, h:] = ~np.eye(n - h, dtype=bool)      # right clique
    adj[h - 1, h] = True                          # bridge
    adj[h, h - 1] = True
    return _finish(n, adj)


# ---------------------------------------------------------------------------
# Graph analysis
# ---------------------------------------------------------------------------
def laplacian(G: dict) -> np.ndarray:
    adj = G["adj"].astype(float)
    deg = adj.sum(axis=1)
    return np.diag(deg) - adj


def lambda_G(G: dict) -> float:
    """Second-smallest eigenvalue of the Laplacian (algebraic connectivity), measured."""
    eig = np.linalg.eigvalsh(laplacian(G))
    return float(np.sort(eig)[1])


def is_connected(adj: np.ndarray) -> bool:
    n = adj.shape[0]
    if n == 0:
        return True
    seen = np.zeros(n, dtype=bool)
    stack = [0]
    seen[0] = True
    while stack:
        v = stack.pop()
        for w in np.nonzero(adj[v])[0]:
            if not seen[w]:
                seen[w] = True
                stack.append(int(w))
    return bool(seen.all())


def graph_distance(G: dict) -> np.ndarray:
    """All-pairs hop distance via BFS from each node (used for diagnostics)."""
    adj = G["adj"]
    n = G["n"]
    dist = np.full((n, n), np.inf)
    for s in range(n):
        dist[s, s] = 0
        frontier = [s]
        d = 0
        while frontier:
            d += 1
            nxt = []
            for v in frontier:
                for w in np.nonzero(adj[v])[0]:
                    if np.isinf(dist[s, w]):
                        dist[s, w] = d
                        nxt.append(int(w))
            frontier = nxt
    return dist


# ---------------------------------------------------------------------------
# Bradley-Terry sampler
# ---------------------------------------------------------------------------
def sigmoid(x: float | np.ndarray) -> float | np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def cmp(i: int, j: int, theta: np.ndarray, rng: np.random.Generator) -> int:
    """One Bradley-Terry comparison of items i and j; returns the winner's index."""
    p_i = sigmoid(float(theta[i]) - float(theta[j]))
    return i if rng.random() < p_i else j


def cmp_batch(pairs: np.ndarray, theta: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Vectorized BT comparisons for an (m,2) array of pairs; returns winners (m,)."""
    logits = theta[pairs[:, 0]] - theta[pairs[:, 1]]
    p_first = sigmoid(logits)
    return np.where(rng.random(len(pairs)) < p_first, pairs[:, 0], pairs[:, 1])


def make_theta(n: int, gap: float, rng: np.random.Generator) -> np.ndarray:
    """Sorted utilities with adjacent gaps ~ gap: theta_i = (n-1-i)*gap (item 0 strongest)."""
    return (n - 1 - np.arange(n)) * float(gap)


# ---------------------------------------------------------------------------
# Script entry: print measured lambda_G for the five graph families + BT sanity
# ---------------------------------------------------------------------------
def main() -> None:
    rng = np.random.default_rng(0)
    print(f"{'graph':<28s} {'n':>4s} {'m(edges)':>9s} {'lambda_G (measured)':>20s}")
    rows = []
    for name, G in [
        ("complete", complete_graph(20)),
        ("random (p=0.2, seed 0)", random_graph(20, 0.2, np.random.default_rng(0))),
        ("cycle", cycle_graph(20)),
        ("star", star_graph(20)),
        ("dumbbell (2x10 cliques)", dumbbell_graph(20)),
    ]:
        lam = lambda_G(G)
        rows.append((name, G["n"], len(G["edges"]), lam))
        print(f"{name:<28s} {G['n']:>4d} {len(G['edges']):>9d} {lam:>20.6f}")

    print("\nBT sampler sanity (n large, theta=[2,0], empirical P(i beats j) vs sigmoid(2)):"),
    th = np.array([2.0, 0.0])
    wins = sum(cmp(0, 1, th, rng) == 0 for _ in range(100_000))
    print(f"  empirical = {wins/100_000:.4f}, sigmoid(2) = {float(sigmoid(2)):.4f}")

    print("\nExpected: complete ~ n = 20; star ~ 1; cycle ~ 4*pi^2/n^2 = "
          f"{4 * np.pi**2 / 400:.4f}; dumbbell small (bottleneck); random between cycle and complete.")


if __name__ == "__main__":
    main()
