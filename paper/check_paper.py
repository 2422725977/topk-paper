#!/usr/bin/env python3
"""W0.6: anti-fabrication number checker (SPEC sec 6.1).

Rule: every result number that appears in the paper's .tex sources must be
greppable in paper/results/*.json.  This script scans all .tex files under paper/,
extracts numeric tokens, and exits nonzero listing any token that cannot be found.

What is extracted: decimal numbers and integers of >= 2 digits in non-comment text.
What is deliberately NOT extracted (structural, not results):
  * LaTeX comments (% ... to end of line)
  * arguments of \\cite/\\ref/\\eqref/\\label/\\url/\\href/\\bibitem/\\includegraphics...
  * numbers preceded by Theorem/Lemma/Table/Figure/Section/Algorithm/... keywords
  * bare years 1900-2099 (citation years)

Self-test (`--selftest`): builds a temporary .tex containing real numbers taken
from results/*.json plus the planted fake 0.98765 (and a fake hidden in a comment),
asserts the fake is flagged, the comment-fake and real numbers are not, then deletes
the temporary file.  SPEC sec 6.6 requires this self-test to be reproducible.

Matching is by word-bounded string, with a float-normalized retry (0.50 -> 0.5).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent
RESULTS = PAPER / "results"

REF_CMD = re.compile(
    r"\\(?:cite|ref|eqref|label|url|href|bibitem|bibliography|input|include|"
    r"includegraphics|addbibresource|pgfplotsset|usepackage)(?:\[[^\]]*\])?\{[^}]*\}")
STRUCTURAL = re.compile(
    r"(?:Theorem|Lemma|Proposition|Corollary|Conjecture|Definition|Assumption|Table|"
    r"Figure|Fig\.|Section|Appendix|Algorithm|Equation|Eq\.|Remark)(?:\s|\~)+\d+(?:\.\d+)*", re.I)
NUM = re.compile(r"\d+\.\d+|\d{2,}")
YEAR = re.compile(r"^(?:19|20)\d{2}$")


def strip_comments(tex: str) -> str:
    out = []
    for line in tex.splitlines():
        # find an unescaped %
        m = re.search(r"(?<!\\)%", line)
        out.append(line[:m.start()] if m else line)
    return "\n".join(out)


def extract_numbers(tex: str) -> list[tuple[str, str]]:
    tex = strip_comments(tex)
    tex = REF_CMD.sub(" ", tex)
    tex = STRUCTURAL.sub(" ", tex)
    found = []
    for m in NUM.finditer(tex):
        tok = m.group(0)
        if YEAR.match(tok):
            continue
        ctx = tex[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
        found.append((tok, ctx))
    return found


def results_corpus() -> str:
    if not RESULTS.exists():
        return ""
    parts = []
    for p in sorted(RESULTS.glob("*.json")):
        parts.append(p.read_text())
    return "\n".join(parts)


def token_in_corpus(tok: str, corpus: str) -> bool:
    if re.search(rf"(?<![\w.]){re.escape(tok)}(?![\w.])", corpus):
        return True
    # float-normalized retry (0.50 -> 0.5, 1.0 -> 1)
    try:
        val = float(tok)
    except ValueError:
        return False
    for s in (repr(val), f"{val:g}", f"{val:.{len(tok.split('.')[-1])}f}" if "." in tok else str(int(val))):
        if s != tok and re.search(rf"(?<![\w.]){re.escape(s)}(?![\w.])", corpus):
            return True
    return False


def check_tex_files(paths: list[Path]) -> list[tuple[Path, str, str]]:
    corpus = results_corpus()
    if not corpus:
        print(f"ERROR: no results JSONs under {RESULTS} -- nothing to verify against", file=sys.stderr)
        raise SystemExit(2)
    unmatched = []
    for p in paths:
        for tok, ctx in extract_numbers(p.read_text()):
            if not token_in_corpus(tok, corpus):
                unmatched.append((p, tok, ctx))
    return unmatched


def selftest() -> int:
    corpus = results_corpus()
    if not corpus:
        print("selftest SKIPPED: no results JSONs yet", file=sys.stderr)
        return 2
    # pick a guaranteed-real integer from e1.json (a raw per-rep T) and a real decimal
    e1 = json.loads((RESULTS / "e1.json").read_text()) if (RESULTS / "e1.json").exists() else None
    if e1 is None:
        print("selftest SKIPPED: e1.json missing", file=sys.stderr)
        return 2
    real_T = str(e1["configs"][0]["T_raw"][0])
    real_delta = str(e1["configs"][0]["delta"])

    tmp = PAPER / "check_selftest_tmp.tex"
    good = PAPER / "check_selftest_clean.tex"
    try:
        tmp.write_text(f"""% selftest: planted fake must be flagged
\\section{{Fake}}
\\cite{{shah2015estimation}} reports (2018) that Theorem~4.1 holds; see Table~\\ref{{tab:x}}.
Real measured value T = {real_T} at Delta = {real_delta}.
The planted fake success rate is 0.98765.
% planted fake inside a comment: 0.11111 (must be ignored)
\\label{{tab:x}}
""")
        good.write_text(f"""% selftest: only real + structural numbers
\\cite{{heckel2018approximate}} (2018), Theorem~4.1, Table~\\ref{{tab:y}}.
T = {real_T}, Delta = {real_delta}.
\\label{{tab:y}}
""")
        fake_found = [tok for _, tok, _ in check_tex_files([tmp])]
        clean_found = [tok for _, tok, _ in check_tex_files([good])]
        ok_fake = "0.98765" in fake_found
        ok_comment = "0.11111" not in fake_found
        ok_clean = len(clean_found) == 0
        print(f"selftest: planted fake 0.98765 flagged = {ok_fake}; "
              f"comment-fake 0.11111 ignored = {ok_comment}; clean file has 0 unmatched = {ok_clean}")
        print(f"selftest: unmatched in fake file = {fake_found}")
        if not (ok_fake and ok_comment and ok_clean):
            print("selftest FAILED", file=sys.stderr)
            return 1
        return 0
    finally:
        tmp.unlink(missing_ok=True)
        good.unlink(missing_ok=True)


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    tex_files = sorted(PAPER.rglob("*.tex"))
    if not tex_files:
        print("no .tex files under paper/ yet -- nothing to check (Wave 0); exit 0")
        return 0
    unmatched = check_tex_files(tex_files)
    if unmatched:
        print(f"FAIL: {len(unmatched)} number(s) in .tex not found in results/*.json:")
        for p, tok, ctx in unmatched:
            print(f"  {p.relative_to(PAPER)}: {tok}   ...{ctx}...")
        return 1
    n_numbers = sum(len(extract_numbers(p.read_text())) for p in tex_files)
    print(f"OK: all {n_numbers} numeric tokens in {len(tex_files)} .tex file(s) "
          f"are greppable in results/*.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
