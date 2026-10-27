#!/usr/bin/env python3
"""W0.1: Fetch real paper metadata (arXiv API + Semantic Scholar) and generate refs.bib.

Anti-fabrication rule (SPEC sec 6.2): refs.bib is generated ONLY by this script from
API responses -- never hand-written. Every entry carries a real arXiv id verified by
the arXiv API itself (a paper only enters the corpus if arXiv returned its Atom record).

Stdlib only; sleeps >=3s between requests per arXiv API etiquette.

Outputs (next to this script):
  refs_raw.json   -- full metadata incl. abstracts + citation counts (input for SURVEY.md)
  refs.bib        -- generated BibTeX
"""

import json
import re
import ssl
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARXIV_API = "https://export.arxiv.org/api/query"
S2_API = "https://api.semanticscholar.org/graph/v1/paper"
SLEEP = 3.0          # seconds between arXiv requests
MAX_TOTAL = 35       # refs.bib budget (SPEC: 25-35)
PER_DIRECTION = 8    # relevance-rank cap per direction

# ---------------------------------------------------------------------------
# Search program.
# DIRECTIONS = the 5 retrieval directions mandated by SPEC sec 3.
# SEEDS = exact-title / narrow queries that must land in the corpus regardless
#         of how arXiv relevance ranks them.
# ---------------------------------------------------------------------------
DIRECTIONS = [
    ("dueling_bandits",
     'all:"dueling bandits"',
     ("dueling", "bandit", "preference")),
    ("topk_pairwise",
     'all:"top-k" AND all:"pairwise comparisons"',
     ("top-k", "top k", "pairwise comparison", "rank")),
    ("bt_sample_complexity",
     'all:"Bradley-Terry" AND all:"sample complexity"',
     ("bradley", "pairwise", "comparison", "sample")),
    ("ranking_pairwise",
     'all:"ranking from pairwise comparisons"',
     ("ranking", "rank", "pairwise", "comparison")),
    ("graph_bandit",
     'all:"graph" AND all:"bandit" AND all:"sample complexity"',
     ("bandit", "feedback graph", "comparison graph", "graph", "arm")),
]

SEEDS = [
    ("chen2015spectral_mle", 'ti:"Spectral MLE"'),
    ("heckel2018approximate", 'ti:"Approximate ranking from pairwise comparisons"'),
    ("negahban2017rank_centrality", 'ti:"Rank Centrality"'),
    ("jamieson2011active_ranking", 'ti:"Active ranking using pairwise comparisons"'),
    ("shah2018simple_robust", 'ti:"Simple, robust and optimal ranking from pairwise comparisons"'),
    ("shah_minimax", 'ti:"sharp minimax bounds"'),
    ("yue2012k_armed", 'all:"the k-armed dueling bandits problem"'),
    ("szorenyi2015copeland", 'all:"copeland" AND all:"rank elicitation"'),
    ("copeland_recent", 'ti:"copeland winners" AND all:"dueling"'),
    ("suh2017mnl_topk", 'ti:"top-k ranking under the multinomial logit"'),
    ("noisy_sorting", 'ti:"noisy sorting"'),
    ("feedback_graphs", 'ti:"feedback graphs without the graphs"'),
    ("preference_bandits_survey", 'all:"preference-based bandits" AND cat:cs.LG'),
    ("monotone_adversary", 'ti:"top-k ranking with a monotone adversary"'),
    ("bt_general_graphs_2026", 'ti:"Bradley-Terry model under general comparison graphs"'),
    ("graph_monotone_2026", 'ti:"Graph-monotone entrywise guarantees"'),
    ("chen2019topk_random_graph", 'ti:"Spectral method and regularized MLE"'),
    ("osting2012design", 'ti:"Optimal data collection for informative rankings"'),
]

# Titles containing these substrings are off-topic for this paper (screened out).
EXCLUDE = ("causal", "robustness certification", "submodular", "graph neural network",
           "feedback arc set", "differentially private", "retrieval")


def http_get(url: str, timeout: int = 30) -> bytes:
    # This macOS box: anaconda Python's OpenSSL store and /etc/ssl/cert.pem both lack
    # the roots arxiv.org (Google "Certainly") uses, so urllib SSL-verify fails while
    # curl (macOS trust store) succeeds. Route HTTP through curl, fall back to urllib.
    try:
        proc = subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout), url],
            capture_output=True, check=True,
        )
        return proc.stdout
    except FileNotFoundError:
        ctx = ssl.create_default_context(cafile="/etc/ssl/cert.pem")
        req = urllib.request.Request(url, headers={"User-Agent": "topk-paper-refs/0.1 (research)"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read()


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()


def fetch_arxiv(query: str, max_results: int = 20) -> list[dict]:
    q = urllib.parse.quote(query)
    url = f"{ARXIV_API}?search_query={q}&start=0&max_results={max_results}&sortBy=relevance"
    raw = http_get(url)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    out = []
    for entry in root.findall("a:entry", ns):
        eid = clean(entry.findtext("a:id", "", ns))          # e.g. http://arxiv.org/abs/1605.00275v2
        m = re.search(r"abs/([0-9]+\.[0-9]+)(v\d+)?$", eid) or re.search(r"abs/([^/v]+)(v\d+)?$", eid)
        if not m:
            continue
        arxiv_id = m.group(1)
        title = clean(entry.findtext("a:title", "", ns))
        summary = clean(entry.findtext("a:summary", "", ns))
        authors = [clean(a.findtext("a:name", "", ns)) for a in entry.findall("a:author", ns)]
        published = clean(entry.findtext("a:published", "", ns))[:4]
        if not title:
            continue
        out.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "authors": authors,
            "year": published or None,
            "abstract": summary,
            "citationCount": None,
            "directions": [],
            "from_seed": False,
        })
    return out


def fetch_s2_citation_count(arxiv_id: str) -> int | None:
    url = f"{S2_API}/arXiv:{arxiv_id}?fields=citationCount"
    for attempt in range(2):
        try:
            data = json.loads(http_get(url))
            return data.get("citationCount")
        except Exception:
            time.sleep(5)
    return None


def title_relevant(title: str, keywords: tuple) -> bool:
    t = title.lower()
    if any(x in t for x in EXCLUDE):
        return False
    return any(k in t for k in keywords)


def seed_ok(p: dict) -> bool:
    t = p["title"].lower()
    return not any(x in t for x in EXCLUDE)


def bibtex_key(p: dict) -> str:
    first = p["authors"][0] if p["authors"] else "unknown"
    last = re.sub(r"[^a-z]", "", first.split()[-1].lower()) or "anon"
    year = p["year"] or "nd"
    word = re.sub(r"[^a-z]", "", (p["title"].split() or ["x"])[0].lower()) or "x"
    return f"{last}{year}{word}"


def bibtex_escape(s: str) -> str:
    return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")


def main() -> int:
    corpus: dict[str, dict] = {}
    failed_queries: list[tuple[str, str]] = []
    n_arxiv_calls = 0

    def add(papers: list[dict], direction: str | None, is_seed: bool) -> int:
        n_added = 0
        for p in papers:
            pid = p["arxiv_id"]
            if pid not in corpus:
                if not is_seed:
                    continue
                corpus[pid] = p
                n_added += 1
            if is_seed:
                corpus[pid]["from_seed"] = True
            if direction and direction not in corpus[pid]["directions"]:
                corpus[pid]["directions"].append(direction)
        return n_added

    print("== seeds (must-have papers) ==")
    for label, query in SEEDS:
        try:
            papers = fetch_arxiv(query, max_results=3)
            n_arxiv_calls += 1
        except Exception as e:
            failed_queries.append((label, repr(e)))
            continue
        if papers:
            # Seeds are narrow title queries; take the top non-excluded hit.
            top = next((p for p in papers if seed_ok(p)), None)
            if top is not None:
                add([top], None, is_seed=True)
                print(f"[seed] {label}: {top['arxiv_id']} | {top['title'][:72]}", flush=True)
            else:
                print(f"[seed] {label}: hit only excluded titles (dropped)", flush=True)
        else:
            print(f"[seed] {label}: NO HIT (dropped -- query stays logged)", flush=True)
        time.sleep(SLEEP)

    print("\n== directions (SPEC sec 3) ==")
    for name, query, keywords in DIRECTIONS:
        try:
            papers = fetch_arxiv(query, max_results=25)
            n_arxiv_calls += 1
        except Exception as e:
            failed_queries.append((name, repr(e)))
            continue
        kept = 0
        for p in papers:  # arXiv relevance order
            pid = p["arxiv_id"]
            if pid in corpus:
                if name not in corpus[pid]["directions"]:
                    corpus[pid]["directions"].append(name)
                kept += 1
                continue
            if title_relevant(p["title"], keywords) and kept < PER_DIRECTION:
                corpus[pid] = p
                corpus[pid]["directions"].append(name)
                kept += 1
        in_dir = sum(1 for p in corpus.values() if name in p["directions"])
        print(f"[dir] {name}: fetched {len(papers)}, kept this pass {kept}, tagged in corpus {in_dir}", flush=True)
        time.sleep(SLEEP)

    # Enforce refs.bib budget: drop non-seed papers tagged by fewest directions first.
    overflow = len(corpus) - MAX_TOTAL
    if overflow > 0:
        by_tag = sorted(
            (p for p in corpus.values() if not p["from_seed"]),
            key=lambda p: (len(p["directions"]), p["arxiv_id"]),
        )
        for p in by_tag[:overflow]:
            del corpus[p["arxiv_id"]]

    # Semantic Scholar citation counts, best effort (rate limits are common).
    s2_ok = s2_fail = 0
    for p in sorted(corpus.values(), key=lambda x: x["arxiv_id"]):
        cc = fetch_s2_citation_count(p["arxiv_id"])
        if cc is None:
            s2_fail += 1
        else:
            p["citationCount"] = cc
            s2_ok += 1
        time.sleep(SLEEP)

    papers = sorted(corpus.values(), key=lambda p: (-(p["citationCount"] or 0), p["year"] or 0))

    raw = {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tool": "fetch_refs.py (arXiv Atom API + Semantic Scholar Graph API)",
        "n_papers": len(papers),
        "s2_citation_ok": s2_ok,
        "s2_citation_fail": s2_fail,
        "failed_queries": failed_queries,
        "direction_counts": {name: sum(1 for p in papers if name in p["directions"]) for name, _, _ in DIRECTIONS},
        "papers": papers,
    }
    (HERE / "refs_raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["% Auto-generated by fetch_refs.py -- DO NOT EDIT BY HAND (SPEC sec 6.2).",
             f"% {len(papers)} entries, all arXiv ids verified via arXiv Atom API at fetch time.",
             ""]
    for p in papers:
        authors = " and ".join(bibtex_escape(a) for a in p["authors"])
        lines.append(
            f"@article{{{bibtex_key(p)},\n"
            f"  title  = {{{bibtex_escape(p['title'])}}},\n"
            f"  author = {{{authors}}},\n"
            f"  year   = {{{p['year'] or ''}}},\n"
            f"  journal= {{arXiv preprint arXiv:{p['arxiv_id']}}},\n"
            f"  eprint = {{{p['arxiv_id']}}},\n"
            f"  url    = {{https://arxiv.org/abs/{p['arxiv_id']}}}\n"
            f"}}\n"
        )
    (HERE / "refs.bib").write_text("\n".join(lines), encoding="utf-8")

    print(f"\n=== arXiv calls: {n_arxiv_calls}; corpus: {len(papers)} papers; S2 citationCount ok={s2_ok} fail={s2_fail}")
    print(f"=== direction counts: {raw['direction_counts']}")
    if failed_queries:
        print(f"=== FAILED QUERIES: {failed_queries}")
    print(f"=== wrote {HERE/'refs.bib'} and {HERE/'refs_raw.json'}")
    if not (25 <= len(papers) <= MAX_TOTAL):
        print("!!! corpus size outside 25-35", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
