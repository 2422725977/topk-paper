#!/usr/bin/env python3
"""W0.4 tests: on easy instances (n=5, obvious gaps, complete graph) all three
algorithms must return the exact top-k 100% of the time (SPEC Wave 0 W0.4)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulate import complete_graph, cycle_graph, star_graph, make_theta
from algorithms import uniform_majority, successive_elimination, graph_walk_elimination

TRIALS = 100
BUDGET_MAJORITY = 2000


def topk_true(theta: np.ndarray, k: int) -> set[int]:
    return set(np.argsort(-theta)[:k].tolist())


def run_all(theta, G, k, delta, seeds=TRIALS, budget=BUDGET_MAJORITY):
    """Run the three algorithms over `seeds` seeds; assert exact top-k every time."""
    truth = topk_true(theta, k)
    stats = {"uniform_majority": [0, 0, []], "successive_elimination": [0, 0, []],
             "graph_walk_elimination": [0, 0, []]}
    for seed in range(seeds):
        rng = np.random.default_rng(seed)
        S, T, info = uniform_majority(theta, G, k, budget, rng=np.random.default_rng(seed * 7 + 1))
        stats["uniform_majority"][0] += int(set(S) == truth)
        stats["uniform_majority"][1] += 1
        stats["uniform_majority"][2].append(T)

        S, T, info = successive_elimination(theta, G, k, delta, rng=np.random.default_rng(seed))
        stats["successive_elimination"][0] += int(set(S) == truth)
        stats["successive_elimination"][1] += 1
        stats["successive_elimination"][2].append(info["rounds"])

        S, T, info = graph_walk_elimination(theta, G, k, delta, rng=np.random.default_rng(seed))
        stats["graph_walk_elimination"][0] += int(set(S) == truth)
        stats["graph_walk_elimination"][1] += 1
        stats["graph_walk_elimination"][2].append(info["rounds"])
    return stats


@pytest.mark.parametrize("k", [1, 2, 3])
def test_easy_gap2_complete(k):
    theta = np.array([4.0, 2.0, 0.0, -2.0, -4.0])  # adjacent gap Delta = 2
    st = run_all(theta, complete_graph(5), k, delta=0.05)
    for name, (ok, tot, rounds) in st.items():
        assert ok == tot == TRIALS, f"{name} k={k}: {ok}/{tot} correct; rounds med={np.median(rounds):.0f}"


@pytest.mark.parametrize("k", [1, 2])
def test_gap1_complete(k):
    theta = np.array([2.0, 1.0, 0.0, -1.0, -2.0])  # adjacent gap Delta = 1 (runner's example)
    st = run_all(theta, complete_graph(5), k, delta=0.05)
    for name, (ok, tot, rounds) in st.items():
        assert ok == tot == TRIALS, f"{name} k={k}: {ok}/{tot} correct; rounds med={np.median(rounds):.0f}"


def test_elimination_on_sparse_graphs_smoke():
    """Robustness smoke: cycle and star, n=6, big gaps, both elimination algorithms."""
    theta = np.array([5.0, 3.0, 1.0, -1.0, -3.0, -5.0])  # gap 2
    for G in (cycle_graph(6), star_graph(6)):
        for algo in (successive_elimination, graph_walk_elimination):
            for seed in range(20):
                S, T, info = algo(theta, G, 2, 0.05, rng=np.random.default_rng(seed))
                assert set(S) == {0, 1}, f"{algo.__name__} on {G['n']}-node graph seed {seed}: got {S}"
                assert not info.get("capped", False)


def test_returns_k_items_and_counts_T():
    theta = make_theta(8, 1.0, np.random.default_rng(0))
    G = complete_graph(8)
    for algo, args in [
        (uniform_majority, (1500,)),
        (successive_elimination, (0.05,)),
        (graph_walk_elimination, (0.05,)),
    ]:
        S, T, info = algo(theta, G, 3, *args, rng=np.random.default_rng(3))
        assert len(S) == 3 and len(set(S)) == 3
        assert T > 0
        assert set(S) == {0, 1, 2}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
