import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.models import Alarm, Crate  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")


def crate_fixture():
    """{case_id: (tier, case_no, capacity, cargo_opt or None, [Crate, ...])} from the sample of the master data."""
    out = {}
    with open(os.path.join(FIX, "crates-sample.csv"), newline="") as f:
        for r in csv.DictReader(f):
            entry = out.setdefault(r["case_id"], [r["tier"], int(r["case_no"]), int(r["capacity"]),
                                                    int(r["cargo_opt"]) if r["cargo_opt"] else None, []])
            entry[4].append(Crate(int(r["crate_id"]), int(r["cat"]), int(r["weight"]), int(r["value"]),
                                  int(r["expiry"]), int(r["serial"])))
    return {k: tuple(v) for k, v in out.items()}


def alarm_fixture():
    out = {}
    with open(os.path.join(FIX, "incidents-sample.csv"), newline="") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["case_id"], []).append(Alarm(int(r["alarm_id"]), int(r["tick"]), int(r["priority"])))
    return out
