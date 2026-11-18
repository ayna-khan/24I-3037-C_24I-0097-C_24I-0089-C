"""Deliberate fault-injection tests for modules A and D (Section 7.2).

Each fault breaks one line of a COPY of src/ (the real code is never touched),
then runs the unit-test files of A and D against that copy. The fault counts as
'caught' when the suite fails. Run `python -m tests.testfaultinjection` for a
table; results are also written to results/fault-injection-AD.txt.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITE = ["tests.testinventory", "tests.testqueue"]

# (name, file, text to find (must occur exactly once), replacement, what kind of fault)
FAULTS = [
    ("A1 boundary: crate that exactly fills the truck is dropped",
     "src/modules/inventory.py",
     "items = [c for c in crates if c.weight <= capacity and c.value > 0]",
     "items = [c for c in crates if c.weight < capacity and c.value > 0]",
     "wrong boundary condition"),
    ("A2 greedy tie rule reversed (ratio tie goes to the higher crate id)",
     "src/modules/inventory.py",
     "    return a.crate_id < b.crate_id\n",
     "    return a.crate_id > b.crate_id\n",
     "wrong tie rule"),
    ("A3 ratio compared as a float instead of an exact fraction",
     "src/modules/inventory.py",
     "    left = a.value * b.weight\n    right = b.value * a.weight\n",
     "    left = a.value / a.weight\n    right = b.value / b.weight\n",
     "inexact comparison"),
    ("A4 greedy fits a crate only if it leaves room (< instead of <=)",
     "src/modules/inventory.py",
     "if load + c.weight <= capacity:",
     "if load + c.weight < capacity:",
     "wrong boundary condition"),
    ("A5 DP validation call removed (bad weights accepted)",
     "src/modules/inventory.py",
     "    validate_crates(crates, capacity)\n    ops = {\"items_examined\": len(crates), \"cells\": 0, \"calls\": 1}",
     "    ops = {\"items_examined\": len(crates), \"cells\": 0, \"calls\": 1}",
     "missing validation check"),
    ("D1 alarm id tie rule reversed in the heap key",
     "src/modules/emergencyqueue.py",
     "key = (-a.priority, a.tick, a.alarm_id)",
     "key = (-a.priority, a.tick, -a.alarm_id)",
     "wrong tie rule"),
    ("D2 older alarms lose to newer ones within a priority (tick descending)",
     "src/modules/emergencyqueue.py",
     "key = (-a.priority, a.tick, a.alarm_id)",
     "key = (-a.priority, -a.tick, a.alarm_id)",
     "wrong tie rule"),
    ("D3 alarm arriving exactly at the current tick is not yet present",
     "src/modules/emergencyqueue.py",
     "        while i < m and arr[i].tick <= now:                    # push the arrivals of this tick",
     "        while i < m and arr[i].tick < now:                    # push the arrivals of this tick",
     "wrong boundary condition"),
    ("D4 priority check removed from the validation layer of D",
     "src/modules/emergencyqueue.py",
     "        if not PRIORITY_MIN <= a.priority <= PRIORITY_MAX:",
     "        if False:",
     "missing validation check"),
    ("D5 the scan baseline keeps the LEAST urgent alarm",
     "src/modules/emergencyqueue.py",
     "            if key < best_key:\n                best = j",
     "            if key > best_key:\n                best = j",
     "wrong comparison direction"),
]

def run_fault(fault):
    """Return (caught, failing test names, output tail) for one fault."""
    name, rel, old, new, _ = fault
    tmp = tempfile.mkdtemp(prefix="lifeline_fault_")
    try:
        for part in ("src", "tests"):
            shutil.copytree(os.path.join(ROOT, part), os.path.join(tmp, part),
                            ignore=shutil.ignore_patterns("__pycache__"))
        path = os.path.join(tmp, rel)
        text = open(path, encoding="utf-8").read()
        if text.count(old) != 1:
            raise AssertionError(f"{name}: the text to break occurs {text.count(old)} times, expected 1")
        open(path, "w", encoding="utf-8").write(text.replace(old, new))
        proc = subprocess.run([sys.executable, "-m", "unittest"] + SUITE, cwd=tmp,
                              capture_output=True, text=True, timeout=300)
        out = proc.stderr
        failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+) \(", out, re.M)))
        return proc.returncode != 0, failing, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class FaultInjection(unittest.TestCase):
    def test_every_injected_fault_is_caught_by_the_suite(self):
        for fault in FAULTS:
            with self.subTest(fault=fault[0]):
                caught, failing, _ = run_fault(fault)
                self.assertTrue(caught, f"the suite did NOT fail for: {fault[0]}")
                self.assertTrue(failing)

    def test_at_least_three_faults_defined(self):
        self.assertGreaterEqual(len(FAULTS), 3)


def main():
    lines = ["Fault-injection results for modules A and D", ""]
    all_caught = True
    for fault in FAULTS:
        caught, failing, _ = run_fault(fault)
        all_caught &= caught
        lines.append(f"{'CAUGHT' if caught else 'MISSED'}  {fault[0]}  [{fault[4]}]")
        lines.append(f"        failing tests: {', '.join(failing[:4])}{' ...' if len(failing) > 4 else ''} ({len(failing)} in total)")
    lines.append("")
    lines.append("ALL FAULTS CAUGHT" if all_caught else "SOME FAULTS WERE NOT CAUGHT")
    text = "\n".join(lines)
    print(text)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "fault-injection-AD.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return 0 if all_caught else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "unittest":
        unittest.main(argv=sys.argv[:1])
    sys.exit(main())
