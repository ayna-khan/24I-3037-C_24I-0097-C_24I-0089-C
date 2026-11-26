"""Fault injection for module C: plant one realistic bug at a time and check that tests/testrescue.py fails.

    python -m tests.testfaultinjectionC        (about 1 minute; writes results/fault-injection-C.txt)

For every fault the repository is copied to a temporary folder, one piece of src/modules/rescue.py is
replaced by a wrong one, and `python -m unittest tests.testrescue` runs there. A fault is CAUGHT when at
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
TARGET = os.path.join("src", "modules", "rescue.py")
REPORT = os.path.join(ROOT, "results", "fault-injection-C.txt")

# (id, what is wrong, kind of fault, text to find, text to put instead)
FAULTS = [
    ("C1", "touching windows are not compatible in the greedy rule (> instead of >=)", "wrong boundary condition",
     "if last_finish is None or w.start >= last_finish:", "if last_finish is None or w.start > last_finish:"),
    ("C2", "windows with the same finish are ordered by id descending", "wrong tie rule",
     "    return a.window_id < b.window_id", "    return a.window_id > b.window_id"),
    ("C3", "the windows are ordered by start instead of finish", "wrong sort key",
     "        return a.finish < b.finish", "        return a.start < b.start"),
    ("C4", "binary search of the DP: a window that finishes exactly at the start is not counted as compatible", "wrong boundary condition",
     "            if finishes[mid] <= w.start:", "            if finishes[mid] < w.start:"),
    ("C5", "back-tracking of the DP steps back one window instead of jumping to p(i)", "wrong back-tracking",
     "            chosen.append(order[i - 1])\n            i = pred[i]", "            chosen.append(order[i - 1])\n            i -= 1"),
    ("C6", "the quadratic DP treats touching windows as overlapping", "wrong boundary condition",
     "if finishes[j] <= s and f[j] > best_f:", "if finishes[j] < s and f[j] > best_f:"),
    ("C7", "brute force treats touching windows as overlapping", "wrong boundary condition",
     "if items[i].start < items[j].finish and items[j].start < items[i].finish:",
     "if items[i].start <= items[j].finish and items[j].start <= items[i].finish:"),
    ("C8", "day rule changed: a window is unavailable when (id + day) % 5 == 1", "wrong rule",
     "if (wid + day) % UNAVAILABLE_MODULUS != 0:", "if (wid + day) % UNAVAILABLE_MODULUS != 1:"),
    ("C9", "duplicate window ids are no longer detected", "missing validation check",
     "if w.window_id in seen:", "if False:"),
    ("C10", "a window with finish equal to start is accepted", "wrong boundary condition (validation)",
     "if w.finish <= w.start:", "if w.finish < w.start:"),
    ("C11", "the total of objective 'count' is the sum of the values", "wrong total",
     'total = len(chosen) if objective == "count" else sum(w.value for w in chosen)',
     "total = sum(w.value for w in chosen)"),
    ("C12", "no windows is reported as an OK plan instead of EMPTY", "wrong status",
     'return RescuePlan("EMPTY", (), 0, ops, note)', 'return RescuePlan("OK", (), 0, ops, note)'),
    ("C13", "the time budget is never checked", "missing deadline check",
     "if deadline is not None and perf_counter() > deadline:", "if False:"),
    ("C14", "unknown objective is not refused", "missing validation check",
     'if not (isinstance(objective, str) and objective in OBJECTIVES):', 'if False:'),
]


def copy_repository(dst):
    for folder in ("src", "tests"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(dst, folder),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def run_fault(workdir, original, fault):
    fid, what, kind, old, new = fault
    if original.count(old) != 1:
        return "NOT APPLIED", [f"text found {original.count(old)} times, expected once"]
    with open(os.path.join(workdir, TARGET), "w", encoding="utf-8", newline="") as f:
        f.write(original.replace(old, new))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("LIFELINE_FAULTS", None)
    proc = subprocess.run([sys.executable, "-m", "unittest", "tests.testrescue"], cwd=workdir, env=env,
                          capture_output=True, text=True, timeout=600)
    failing = re.findall(r"^(?:FAIL|ERROR): (\w+)", proc.stderr, flags=re.M)
    if proc.returncode == 0:
        return "ESCAPED", []
    return "CAUGHT", failing


def run_all():
    with open(os.path.join(ROOT, TARGET), encoding="utf-8", newline="") as f:
        original = f.read().replace("\r\n", "\n")   # a Windows checkout has CRLF, the planted texts use LF
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        copy_repository(tmp)
        for fault in FAULTS:
            outcome, failing = run_fault(tmp, original, fault)
            results.append((fault, outcome, failing))
            print(f"{outcome:<11} {fault[0]} {fault[1]}", flush=True)
    return results


def write_report(results):
    lines = ["Fault-injection results for module C (tests/testrescue.py against 14 planted bugs of src/modules/rescue.py)", ""]
    for (fid, what, kind, _old, _new), outcome, failing in results:
        lines.append(f"{outcome:<11} {fid} {what}  [{kind}]")
        if failing:
            shown = ", ".join(failing[:4]) + (f" ... ({len(failing)} in total)" if len(failing) > 4 else f" ({len(failing)} in total)")
            lines.append(f"            failing tests: {shown}")
        elif outcome != "CAUGHT":
            lines.append("            no test failed" if outcome == "ESCAPED" else "            the planted text was not found in rescue.py")
    ok = all(o == "CAUGHT" for _, o, _ in results)
    lines += ["", "ALL FAULTS CAUGHT" if ok else "SOME FAULTS ESCAPED OR WERE NOT APPLIED"]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return ok


@unittest.skipUnless(os.environ.get("LIFELINE_FAULTS"), "slow: run `python -m tests.testfaultinjectionC`")
class FaultInjectionC(unittest.TestCase):
    def test_every_planted_fault_is_caught(self):
        results = run_all()
        write_report(results)
        self.assertGreaterEqual(len(results), 3)
        for (fid, what, *_), outcome, _failing in results:
            self.assertEqual(outcome, "CAUGHT", f"{fid} {what}")


if __name__ == "__main__":
    sys.exit(0 if write_report(run_all()) else 1)
