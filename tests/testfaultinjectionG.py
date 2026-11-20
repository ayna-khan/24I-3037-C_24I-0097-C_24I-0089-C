"""Fault injection for module G: plant one realistic bug at a time and check that tests/testchains.py fails.

    python -m tests.testfaultinjectionG        (about 8 minutes; writes results/fault-injection-G.txt)

For every fault the repository is copied to a temporary folder, one piece of src/modules/chains.py is
replaced by a wrong one, and `python -m unittest tests.testchains` runs there. A fault is CAUGHT when at
least one test fails or errors; it ESCAPED when all tests still pass (the test suite would then be too weak).
If the text to be replaced is not found, the fault is reported as NOT APPLIED and the run counts as failed:
a silent no-op would make the report look better than it is.
Under `python -m unittest discover` this file is skipped (set LIFELINE_FAULTS=1 to run it there too).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join("src", "modules", "chains.py")
REPORT = os.path.join(ROOT, "results", "fault-injection-G.txt")

# (id, what is wrong, kind of fault, text to find, text to put instead)
FAULTS = [
    ("G1", "chain DP: a later split replaces an equal-cost earlier one (<= instead of <)", "wrong tie rule",
     "if c < best:", "if c <= best:"),
    ("G2", "chain memo: a later split replaces an equal-cost earlier one (<= instead of <)", "wrong tie rule",
     "if top is None or c < top:", "if top is None or c <= top:"),
    ("G3", "chain DP: the cost of a product uses p(k+1) instead of p(k)", "wrong index",
     "c = row[k] + col[k + 1] + left * p[k] * right", "c = row[k] + col[k + 1] + left * p[k + 1] * right"),
    ("G4", "bracketing string: no space between the two factors", "wrong output format",
     'stack.extend([")", (k + 1, j), " ", (i, k), "("])', 'stack.extend([")", (k + 1, j), "", (i, k), "("])'),
    ("G5", "chain brute force: a later bracketing replaces an equal-cost earlier one", "wrong tie rule",
     "if best_cost is None or c < best_cost:", "if best_cost is None or c <= best_cost:"),
    ("G6", "chain DP: counts one split candidate too many per cell", "wrong operation count",
     'ops["candidates"] += count * (length - 1)', 'ops["candidates"] += count * length'),
    ("G7", "drum DP: a later first piece replaces an equal one (price and pieces equal)", "wrong tie rule",
     "< top_pieces:     # equal price, strictly fewer pieces",
     "<= top_pieces:     # equal price, strictly fewer pieces"),
    ("G8", "drum DP: equal prices no longer prefer fewer pieces", "wrong tie rule",
     "elif v == top and 1 + pieces[l - k] < top_pieces:     # equal price, strictly fewer pieces",
     "elif v == top and False:     # equal price, strictly fewer pieces"),
    ("G9", "drum memo: a later first piece replaces an equal one (price and pieces equal)", "wrong tie rule",
     "elif v == top and 1 + pieces[l - k] < top_pieces:\n                top_pieces, top_k = 1 + pieces[l - k], k",
     "elif v == top and 1 + pieces[l - k] <= top_pieces:\n                top_pieces, top_k = 1 + pieces[l - k], k"),
    ("G10", "drum DP: the first candidate (one piece of length 1) is overpriced by 1", "wrong boundary condition",
     "top = pr[1] + best[l - 1]", "top = pr[1] + best[l - 1] + 1"),
    ("G11", "greedy: the piece with the LOWEST price per length comes first", "wrong comparison direction",
     "    return left > right", "    return left < right"),
    ("G12", "greedy: equal ratios go to the shorter piece", "wrong tie rule",
     "    return a[0] > b[0]", "    return a[0] < b[0]"),
    ("G13", "greedy: the ratio is compared as a float instead of an exact fraction", "inexact comparison",
     "    left = a[1] * b[0]\n    right = b[1] * a[0]", "    left = a[1] / a[0]\n    right = b[1] / b[0]"),
    ("G14", "a chain of one dimension (n = 0) is accepted", "missing validation check",
     "if len(out) < 2:", "if len(out) < 1:"),
    ("G15", "a dimension of 0 is accepted", "wrong boundary condition (validation)",
     "if d < 1:", "if d < 0:"),
    ("G16", "a drum of length 0 is accepted", "wrong boundary condition (validation)",
     "if length < 1:", "if length < 0:"),
    ("G17", "missing prices are no longer detected", "missing validation check",
     "if len(prices) < length:", "if False:"),
    ("G18", "the recursion limit is not raised for the memoised methods", "missing safeguard",
     "sys.setrecursionlimit(max(old_limit, depth + 1000))", "sys.setrecursionlimit(old_limit)"),
    ("G19", "the time budget is never checked", "missing deadline check",
     "if deadline is not None and perf_counter() > deadline:", "if False:"),
    ("G20", "greedy is accepted as a method for a chain", "missing validation check",
     "CHAIN_FUNCS = {\"dp\": _chain_dp, \"memo\": _chain_memo, \"brute\": _chain_brute}",
     "CHAIN_FUNCS = {\"dp\": _chain_dp, \"memo\": _chain_memo, \"brute\": _chain_brute, \"greedy\": _chain_dp}"),
]


def copy_repository(dst):
    for folder in ("src", "tests"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(dst, folder),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def run_fault(workdir, original, fault):
    fid, what, kind, old, new = fault
    if original.count(old) != 1:
        return "NOT APPLIED", [f"text found {original.count(old)} times, expected once"]
    with open(os.path.join(workdir, TARGET), "w", encoding="utf-8", newline="\n") as f:
        f.write(original.replace(old, new))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("LIFELINE_FAULTS", None)
    proc = subprocess.run([sys.executable, "-m", "unittest", "tests.testchains"], cwd=workdir, env=env,
                          capture_output=True, text=True, timeout=600)
    failing = re.findall(r"^(?:FAIL|ERROR): (\w+)", proc.stderr, flags=re.M)
    if proc.returncode == 0:
        return "ESCAPED", []
    return "CAUGHT", failing


def run_all():
    with open(os.path.join(ROOT, TARGET), encoding="utf-8") as f:                 # universal newlines: CRLF or LF, the same text
        original = f.read()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        copy_repository(tmp)
        for fault in FAULTS:
            outcome, failing = run_fault(tmp, original, fault)
            results.append((fault, outcome, failing))
            print(f"{outcome:<11} {fault[0]} {fault[1]}", flush=True)
    return results


def write_report(results):
    lines = [f"Fault-injection results for module G (tests/testchains.py against {len(FAULTS)} planted bugs of src/modules/chains.py)", ""]
    for (fid, what, kind, _old, _new), outcome, failing in results:
        lines.append(f"{outcome:<11} {fid} {what}  [{kind}]")
        if failing:
            shown = ", ".join(failing[:4]) + (f" ... ({len(failing)} in total)" if len(failing) > 4 else f" ({len(failing)} in total)")
            lines.append(f"            failing tests: {shown}")
        elif outcome != "CAUGHT":
            lines.append("            no test failed" if outcome == "ESCAPED" else "            the planted text was not found in chains.py")
    ok = all(o == "CAUGHT" for _, o, _ in results)
    lines += ["", "ALL FAULTS CAUGHT" if ok else "SOME FAULTS ESCAPED OR WERE NOT APPLIED"]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return ok


@unittest.skipUnless(os.environ.get("LIFELINE_FAULTS"), "slow: run `python -m tests.testfaultinjectionG`")
class FaultInjectionG(unittest.TestCase):
    def test_every_planted_fault_is_caught(self):
        results = run_all()
        write_report(results)
        self.assertGreaterEqual(len(results), 3)
        for (fid, what, *_), outcome, _failing in results:
            self.assertEqual(outcome, "CAUGHT", f"{fid} {what}")


if __name__ == "__main__":
    sys.exit(0 if write_report(run_all()) else 1)
