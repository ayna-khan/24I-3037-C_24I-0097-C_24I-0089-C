"""Samples and pooled instances of the master dataset for the experiments of A and D.

Stand-in reader: it streams only the CSV tables it needs (crates, incidents,
cases) with the standard csv module, so the 84 MB files never sit in memory.
If the group's src/loader.py takes over, only these functions have to be
re-pointed; the pooling rules below are the ones of Section 4.3.

Rules used (also listed in the README):
  * master order = row order of cases.csv; a tier is the sub-list of its cases;
  * sample of N cases of a tier with group seed s: positions s mod 7,
    s mod 7 + 7, ... of the tier list, first N;
  * pool: the consecutive tier cases that follow, starting at the first case of
    the sample, joined until they hold enough elements, ids renumbered from 1;
  * crates are appended; the pooled capacity is floor(n * sum(W) / sum(crates))
    over the joined cases, which keeps the capacity per crate of the data;
  * alarm ticks of the i-th case are shifted past the last (shifted) tick of the
    previous case, alarm ids are renumbered from 1 in (tick, original id) order.
"""
import csv
import os

from src.models import Alarm, Crate

GROUP_SEED = 41


def read_cases(master_dir):
    with open(os.path.join(master_dir, "cases.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tier_cases(cases, tier):
    return [c for c in cases if c["tier"] == tier]


def sample_cases(cases, tier, n, seed=GROUP_SEED):
    """The cases of `tier` at positions seed mod 7, +7, +14, ..., first n, in master order."""
    pool = tier_cases(cases, tier)
    return [pool[i] for i in range(seed % 7, len(pool), 7)][:n]


def consecutive_cases(cases, tier, first_case_id, count):
    pool = tier_cases(cases, tier)
    start = next(i for i, c in enumerate(pool) if c["case_id"] == first_case_id)
    return pool[start:start + count]


def read_crates(master_dir, case_ids):
    """{case_id: [Crate, ...]} in file order, for the wanted case ids only."""
    wanted = set(case_ids)
    out = {cid: [] for cid in wanted}
    with open(os.path.join(master_dir, "crates.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case_id"] in wanted:
                out[r["case_id"]].append(Crate(int(r["crate_id"]), int(r["cat"]), int(r["weight"]),
                                               int(r["value"]), int(r["expiry"]), int(r["serial"])))
    return out


def read_alarms(master_dir, case_ids):
    wanted = set(case_ids)
    out = {cid: [] for cid in wanted}
    with open(os.path.join(master_dir, "incidents.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["case_id"] in wanted:
                out[r["case_id"]].append(Alarm(int(r["alarm_id"]), int(r["tick"]), int(r["priority"])))
    return out


def pool_crates(cases_in_order, crates_by_case, n):
    """(crates, capacity, joined case ids) for a pool of exactly n crates, ids 1..n."""
    joined, crates, total_w, total_n = [], [], 0, 0
    for c in cases_in_order:
        joined.append(c["case_id"])
        crates.extend(crates_by_case[c["case_id"]])
        total_w += int(c["capacity"])
        total_n += len(crates_by_case[c["case_id"]])
        if len(crates) >= n:
            break
    if len(crates) < n:
        raise ValueError(f"the cases offered hold only {len(crates)} crates, {n} needed")
    renumbered = [cr._replace(crate_id=i + 1) for i, cr in enumerate(crates[:n])]
    return renumbered, (n * total_w) // total_n, joined


def pool_alarms(cases_in_order, alarms_by_case, m):
    """(alarms, joined case ids) for a pool of exactly m alarms, ids 1..m."""
    joined, out, offset = [], [], 0
    for c in cases_in_order:
        joined.append(c["case_id"])
        part = sorted(alarms_by_case[c["case_id"]], key=lambda a: (a.tick, a.alarm_id))
        for a in part:
            out.append(a._replace(tick=a.tick + offset))
        offset = out[-1].tick + 1
        if len(out) >= m:
            break
    if len(out) < m:
        raise ValueError(f"the cases offered hold only {len(out)} alarms, {m} needed")
    return [a._replace(alarm_id=i + 1) for i, a in enumerate(out[:m])], joined
