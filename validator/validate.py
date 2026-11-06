"""validate.py - checks cases.xlsx. It recomputes everything from the sheets and does not import the generator.

    python validator/validate.py cases.xlsx            full check of 50 cases
    python validator/validate.py file.xlsx --partial   fewer cases (used for the broken copies)

prints PASS or the broken rules for every case.
"""
import sys
from bisect import bisect_left, bisect_right
from collections import defaultdict
from fractions import Fraction

from openpyxl import load_workbook

from checks_exact import exhaustive_drum, exhaustive_knapsack, exhaustive_windows, held_karp, min_cover_branching
from checks_routes import bfs_hops, route_costs
from checks_text import count_regex, edit_distance, greedy_value

ALPHABET = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
HEADERS = {
    "cases": "case_id group_seed case_no tier scenario capacity target_0 target_1 target_2 edit_bound tour_length sensor_nodes sensor_k safety_vars rations_target",
    "crates": "case_id crate_id cat weight value expiry serial",
    "locations": "case_id loc_id type penalty",
    "roads": "case_id road_no u v minutes cable",
    "waves": "case_id wave_no road_no",
    "radio_log": "case_id part text",
    "radio_patterns": "case_id pattern_no pattern count",
    "radio_reports": "case_id report_a report_b",
    "windows": "case_id window_id start finish value",
    "incidents": "case_id alarm_id tick priority",
    "sites": "case_id site_no x y",
    "tour": "case_id step site_no",
    "pipeline_dims": "case_id idx dim",
    "drum_prices": "case_id length price",
    "sensor_edges": "case_id u v",
    "sensor_cover": "case_id node",
    "safety_rules": "case_id rule_no lit_1 lit_2 lit_3",
    "safety_planted": "case_id switch value",
    "rations": "case_id item value planted",
    "claims": "case_id cargo_opt window_count_opt window_value_opt drum_opt tour_opt cover_min",
}
HEADERS = {k: v.split() for k, v in HEADERS.items()}
# size ranges for tiers (S, M, L)
SIZE = {
    "crates": ((8, 20), (40, 200), (500, 1500)), "V": ((6, 12), (30, 150), (500, 2000)),
    "log": ((200, 500), (2000, 10000), (20000, 100000)), "report": ((10, 30), (30, 150), (200, 1000)),
    "windows": ((8, 20), (50, 300), (1000, 3000)), "alarms": ((10, 40), (200, 1000), (2000, 5000)),
    "sites": ((5, 9), (10, 16), (200, 500)), "stages": ((4, 8), (15, 60), (100, 300)),
    "drum": ((5, 14), (40, 200), (500, 2000)), "sensors": ((6, 14), (20, 40), (100, 400)),
    "vars": ((6, 15), (20, 50), (20, 50)), "rations": ((8, 20), (24, 40), (50, 100)),
}


def size_range(name, tier):
    return SIZE[name]["SML".index("L" if tier == "X" else tier)]


# loading the workbook
def load(path):
    wb = load_workbook(path, read_only=True, data_only=False)
    names = wb.sheetnames
    data = {}
    for name in names:
        rows = list(wb[name].iter_rows(values_only=True))
        data[name] = rows
    return names, data


def group(rows, header_len):
    """puts the rows (without header) in a dict: case_id -> rows"""
    out = defaultdict(list)
    for r in rows[1:]:
        out[r[0]].append(tuple(r[:header_len]))
    return out


# small helper functions
def is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)








# checks of one case
def check_case(cid, S, errors, summary):
    """runs V1..V8 on one case. errors gets the messages, summary keeps facts for the global rules"""
    def bad(code, msg):
        errors.append(f"{code}: {msg}".replace("_", " "))

    rows = {name: S[name].get(cid, []) for name in S}
    if len(rows["cases"]) != 1:
        bad("V1", "need exactly one row in sheet cases")
        return
    (_c, seed, k, tier, scen, cap, t0, t1, t2, edit_bound, tour_len, s_nodes, s_k, s_vars, r_target) = rows["cases"][0]
    if not all(is_int(x) for x in (seed, k, scen, cap, t0, t1, t2, edit_bound, tour_len, s_nodes, s_k, s_vars, r_target)):
        bad("V1", "non-integer number in sheet cases")
        return
    expect_tier = "S" if k < 20 else "M" if k < 40 else "L" if k < 46 else "X"
    if cid != f"{seed}-{k:02d}":
        bad("V1", f"case_id {cid} does not match group_seed-case_no")
    if tier != expect_tier:
        bad("V1", f"tier {tier}, expected {expect_tier}")
    if scen != k % 6 + 1:
        bad("V1", f"scenario {scen}, expected {k % 6 + 1}")
    summary["tier"], summary["k"], summary["study"] = expect_tier, k, k % 6 + 1
    study = k % 6 + 1
    rng = lambda name: size_range(name, expect_tier)

    # crates
    cr = rows["crates"]
    n = len(cr)
    lo, hi = (1500, 3000) if k == 46 else (12, 60) if k == 47 else rng("crates")
    if not lo <= n <= hi:
        bad("V2", f"{n} crates outside {lo}..{hi}")
    if [c[1] for c in cr] != list(range(1, n + 1)):
        bad("V3", "crate_id not 1..n in order")
    for c in cr:
        _, _id, cat, w, v, e, ser = c
        if not all(is_int(x) for x in c[1:]):
            bad("V2", f"crate {_id} has a non-integer field")
            break
        if not (0 <= cat <= 4 and 1 <= w <= 20 and 10 <= v <= 100 and 0 <= e <= 999 and 10_000_000 <= ser <= 99_999_999):
            bad("V2", f"crate {_id} field out of range")
            break
    if len({c[6] for c in cr}) != n:
        bad("V3", "serial numbers not distinct")
    crates = [c[1:] for c in cr]
    total_w = sum(c[2] for c in crates)
    if not (cap >= 1 and 10 * cap >= total_w and 10 * cap <= 7 * total_w):
        bad("V2", f"capacity {cap} is not 10%..70% of total weight {total_w}")
    cats = [c[1] for c in crates]
    pct = lambda group_: 100 * sum(1 for c in cats if c in group_) / max(1, n)
    greedy = greedy_value(crates, cap)

    def dp_best():
        best = [0] * (cap + 1)
        for _id, _c, w, v, _e, _s in crates:
            for c in range(cap, w - 1, -1):
                best[c] = max(best[c], best[c - w] + v)
        return best[cap]
    exact = dp_best()
    summary["greedy_fails"] = greedy < exact

    # network
    loc, rd = rows["locations"], rows["roads"]
    V, E = len(loc), len(rd)
    lo, hi = (1500, 3000) if k == 48 else rng("V")
    if not lo <= V <= hi:
        bad("V2", f"V={V} outside {lo}..{hi}")
    if [l[1] for l in loc] != list(range(V)):
        bad("V3", "loc_id not 0..V-1")
    if V and not (loc[0][2] == "D" and loc[0][3] == 0):
        bad("V2", "location 0 must be depot with penalty 0")
    pen = [l[3] for l in loc]
    types = [l[2] for l in loc]
    if any(t not in ("D", "S", "H", "J") for t in types) or types[1:].count("D") or "S" not in types or "H" not in types:
        bad("V2", "bad location types")
    if any(p not in (0, 1, 2, 4, 6) for p in pen):
        bad("V2", "penalty not in {0,1,2,4,6}")
    if not (V - 1 <= E <= 3 * V):
        bad("V2", f"E={E} outside V-1..3V")
    if [r[1] for r in rd] != list(range(E)):
        bad("V3", "road_no not 0..E-1")
    seen_pairs, adj = set(), [[] for _ in range(V)]
    roads_ok = True
    for _c, rn, u, v, mins, cable in rd:
        if not all(is_int(x) for x in (u, v, mins, cable)) or not (0 <= u < v < V):
            bad("V3", f"road {rn}: ends invalid or u>=v")
            roads_ok = False
            break
        if (u, v) in seen_pairs:
            bad("V3", f"road {rn}: repeated pair")
            roads_ok = False
            break
        seen_pairs.add((u, v))
        if not (1 <= mins <= 60 and 1 <= cable <= 100):
            bad("V2", f"road {rn}: minutes/cable out of range")
        adj[u].append((v, rn))
        adj[v].append((u, rn))
    hops0 = None
    if roads_ok and V:
        hops0 = bfs_hops(V, adj)
        if -1 in hops0:
            bad("V4", "network not connected before closures")
    targets = [t0, t1, t2]
    if len(set(targets)) != 3 or any(not (0 <= t < V) or types[t] not in ("S", "H") for t in targets):
        bad("V3", "targets must be 3 distinct existing shelters/hospitals")

    # waves
    wv = rows["waves"]
    wave_nos = sorted({w[1] for w in wv})
    if not (2 <= len(wave_nos) <= 5) or wave_nos != list(range(1, len(wave_nos) + 1)):
        bad("V2", f"waves must be numbered 1..w with 2<=w<=5, got {wave_nos}")
    road_seen = set()
    for wn in wave_nos:
        members = [w[2] for w in wv if w[1] == wn]
        if not (1 <= len(members) <= max(1, E // 4)):
            bad("V4", f"wave {wn} has {len(members)} roads (limit {max(1, E // 4)})")
        for r in members:
            if r in road_seen:
                bad("V4", f"road {r} is in two waves")
            if not (is_int(r) and 0 <= r < E):
                bad("V3", f"wave {wn}: road {r} does not exist")
            road_seen.add(r)
    union_closed = road_seen

    # radio
    parts = rows["radio_log"]
    if [p[1] for p in parts] != list(range(1, len(parts) + 1)):
        bad("V5", "log parts not in order 1,2,...")
    if any(not isinstance(p[2], str) or len(p[2]) > 10000 for p in parts):
        bad("V5", "log part is not text or longer than 10000")
    log = "".join(str(p[2]) for p in parts)
    if set(log) - ALPHABET:
        bad("V2", "log has symbols outside the alphabet")
    lo, hi = (50000, 100000) if k == 49 else rng("log")
    if not lo <= len(log) <= hi:
        bad("V2", f"log length {len(log)} outside {lo}..{hi}")
    pats = rows["radio_patterns"]
    lens = [2, 4, 8, 12, 20, 40]
    if [p[1] for p in pats] != list(range(6)) or [len(str(p[2])) for p in pats] != lens:
        bad("V5", "need six patterns 0..5 of lengths 2,4,8,12,20,40")
    else:
        counts = [count_regex(log, p[2]) for p in pats]
        for p, c in zip(pats, counts):
            if p[3] != c:
                bad("V5", f"pattern {p[1]} count is {p[3]}, true count {c}")
        if sum(1 for c in counts if c > 0) < 2 or all(c > 0 for c in counts):
            bad("V5", "at least two patterns must occur and at least one must not")
    rep = rows["radio_reports"]
    if len(rep) != 1:
        bad("V5", "need exactly one row in radio_reports")
    else:
        a, b = rep[0][1], rep[0][2]
        lo, hi = rng("report")
        if not (isinstance(a, str) and isinstance(b, str) and lo <= len(a) <= hi and lo <= len(b) <= hi) or set(a + b) - ALPHABET:
            bad("V2", "reports: length or alphabet wrong")
        else:
            true_d = edit_distance(a, b)
            if not (true_d <= edit_bound <= len(a) + len(b)):
                bad("V5", f"edit_bound {edit_bound} not in [{true_d}, {len(a) + len(b)}]")

    # windows
    wn_ = rows["windows"]
    lo, hi = rng("windows")
    if not lo <= len(wn_) <= hi:
        bad("V2", f"{len(wn_)} windows outside {lo}..{hi}")
    if [w[1] for w in wn_] != list(range(1, len(wn_) + 1)):
        bad("V3", "window_id not 1..n")
    for w in wn_:
        _c, wid, s, f, v = w
        if not (is_int(s) and is_int(f) and 0 <= s < f <= 1440 and 5 <= f - s <= 480 and 1 <= v <= 100):
            bad("V2", f"window {wid} out of range")
            break
    wins = [(w[2], w[3], w[4]) for w in wn_]
    touching = sum(1 for a in wins for b in wins if a[1] == b[0])
    if len(wins) >= 8 and touching < 2:
        bad("V2", "fewer than two touching window pairs")
    starts, finishes = sorted(w[0] for w in wins), sorted(w[1] for w in wins)
    overlap_total = sum(bisect_left(starts, f) - bisect_right(finishes, s) - 1 for s, f, _ in wins)
    avg_overlap = overlap_total / max(1, len(wins))

    # incidents
    inc = rows["incidents"]
    lo, hi = rng("alarms")
    if not lo <= len(inc) <= hi:
        bad("V2", f"{len(inc)} alarms outside {lo}..{hi}")
    if [a[1] for a in inc] != list(range(1, len(inc) + 1)):
        bad("V3", "alarm_id not 1..n")
    ticks = [a[2] for a in inc]
    pris = [a[3] for a in inc]
    if ticks and (ticks[0] != 0 or any(ticks[i] > ticks[i + 1] for i in range(len(ticks) - 1))):
        bad("V2", "ticks must start at 0 and never decrease")
    if any(not (is_int(p) and 1 <= p <= 10) for p in pris):
        bad("V2", "priority outside 1..10")
    n_al = len(inc)
    rate_ok_num = n_al, (ticks[-1] + 1) if ticks else 1       # alarms per tick = n_al / (last tick + 1)
    if expect_tier in ("M", "L"):
        if not (12 * rate_ok_num[1] <= 10 * n_al <= 18 * rate_ok_num[1]):
            bad("V2", f"alarms per tick {n_al / rate_ok_num[1]:.2f} outside 1.2..1.8")
        if len(set(pris)) < 6 or 1 not in pris:
            bad("V2", "need >=6 distinct priorities including 1")

    # sites and tour
    st, tr = rows["sites"], rows["tour"]
    lo, hi = rng("sites")
    n_sites = len(st)
    if not lo <= n_sites <= hi:
        bad("V2", f"{n_sites} sites outside {lo}..{hi}")
    if [s[1] for s in st] != list(range(n_sites)):
        bad("V3", "site_no not 0..n-1")
    pts = [(s[2], s[3]) for s in st]
    if any(not (is_int(x) and is_int(y) and 0 <= x <= 999 and 0 <= y <= 999) for x, y in pts) or len(set(pts)) != n_sites:
        bad("V2", "site coordinates out of range or two sites equal")
    order = [t[2] for t in tr]
    if [t[1] for t in tr] != list(range(len(tr))) or sorted(order) != list(range(n_sites)) or (order and order[0] != 0):
        bad("V6", "tour is not a permutation of all sites starting at 0")
    else:
        d = lambda a, b: abs(pts[a][0] - pts[b][0]) + abs(pts[a][1] - pts[b][1])
        length = sum(d(order[i], order[(i + 1) % n_sites]) for i in range(n_sites))
        if length != tour_len:
            bad("V6", f"tour_length {tour_len}, true closed length {length}")
        if expect_tier in ("L", "X"):
            seen, cur, nn_len = {0}, 0, 0
            for _ in range(n_sites - 1):
                nxt = min((j for j in range(n_sites) if j not in seen), key=lambda j: (d(cur, j), j))
                nn_len += d(cur, nxt)
                seen.add(nxt)
                cur = nxt
            nn_len += d(cur, 0)
            if tour_len > nn_len:
                bad("V6", f"tour_length {tour_len} longer than nearest-neighbour tour {nn_len}")

    # pipeline, drum
    pd, dp_ = rows["pipeline_dims"], rows["drum_prices"]
    lo, hi = rng("stages")
    n_st = len(pd) - 1
    if not lo <= n_st <= hi or [p[1] for p in pd] != list(range(len(pd))) or any(not (is_int(p[2]) and 2 <= p[2] <= 100) for p in pd):
        bad("V2", "pipeline_dims: n+1 integers 2..100 with idx 0..n, n in range")
    lo, hi = rng("drum")
    prices = [p[2] for p in dp_]
    if not lo <= len(prices) <= hi or [p[1] for p in dp_] != list(range(1, len(prices) + 1)):
        bad("V2", "drum length out of range or not 1..L")
    elif any(not (is_int(p) and 1 <= p <= 500) for p in prices):
        bad("V2", "drum price not a positive integer up to 500")
    elif all(prices[j - 1] * 1 == prices[0] * j for j in range(1, len(prices) + 1)):
        bad("V2", "drum prices are all proportional to length")

    # sensors
    se, sc = rows["sensor_edges"], rows["sensor_cover"]
    lo, hi = rng("sensors")
    if not lo <= s_nodes <= hi:
        bad("V2", f"sensor_nodes {s_nodes} outside {lo}..{hi}")
    edges = [(e[1], e[2]) for e in se]
    if any(not (is_int(u) and is_int(v) and 0 <= u < v < s_nodes) for u, v in edges) or len(set(edges)) != len(edges):
        bad("V3", "sensor edge invalid (loop, u>=v, outside nodes or repeated)")
    if len(edges) < s_nodes - 1:
        bad("V2", "fewer than n-1 sensor edges")
    cover = [c[1] for c in sc]
    if not (2 <= s_k <= s_nodes // 2) or len(cover) != s_k or len(set(cover)) != s_k or any(not (is_int(c) and 0 <= c < s_nodes) for c in cover):
        bad("V6", "planted cover: need sensor_k distinct nodes with 2<=k<=n/2")
    elif any(u not in cover and v not in cover for u, v in edges):
        bad("V6", "planted cover misses an edge")

    # safety
    sr, sp = rows["safety_rules"], rows["safety_planted"]
    lo, hi = rng("vars")
    if not lo <= s_vars <= hi:
        bad("V2", f"safety_vars {s_vars} outside {lo}..{hi}")
    planted = {p[1]: p[2] for p in sp}
    if sorted(planted) != list(range(1, s_vars + 1)) or any(v not in (0, 1) for v in planted.values()):
        bad("V6", "safety_planted must give 0/1 for switches 1..vars")
    if [r[1] for r in sr] != list(range(len(sr))):
        bad("V3", "rule_no not 0..R-1")
    rule_bad = False
    for r in sr:
        lits = r[2:5]
        if not all(is_int(l) and l != 0 and 1 <= abs(l) <= s_vars for l in lits) or len({abs(l) for l in lits}) != 3:
            bad("V2", f"rule {r[1]}: literals must be three non-zero integers on three different switches")
            rule_bad = True
            break
        if not any((l > 0) == (planted.get(abs(l)) == 1) for l in lits):
            bad("V6", f"planted assignment breaks rule {r[1]}")
            rule_bad = True
            break
    ratio = len(sr) / s_vars if s_vars else 0
    if not 2.0 <= ratio <= 6.0:
        bad("V2", f"rules per switch {ratio:.2f} outside 2.0..6.0")
    summary["ratio"] = ratio

    # rations
    ra = rows["rations"]
    lo, hi = rng("rations")
    if not lo <= len(ra) <= hi or [r[1] for r in ra] != list(range(len(ra))):
        bad("V2", "rations: count out of range or item not 0..n-1")
    if any(not (is_int(r[2]) and 1 <= r[2] <= 1000 and r[3] in (0, 1)) for r in ra):
        bad("V2", "ration value must be 1..1000 and planted 0/1")
    if r_target <= 0 or sum(r[2] for r in ra if r[3] == 1) != r_target:
        bad("V6", "planted rations do not add up to rations_target (positive)")

    # claims (tier s)
    cl = rows["claims"]
    if expect_tier == "S":
        if len(cl) != 1:
            bad("V5", "tier S needs one row in claims")
        else:
            try:
                got = dict(zip(HEADERS["claims"][1:], cl[0][1:]))
                truth = {
                    "cargo_opt": exhaustive_knapsack(crates, cap),
                    "window_count_opt": exhaustive_windows(wins, False),
                    "window_value_opt": exhaustive_windows(wins, True),
                    "drum_opt": exhaustive_drum(prices),
                    "tour_opt": held_karp(pts),
                    "cover_min": min_cover_branching(edges, s_nodes),
                }
                for key, val in truth.items():
                    if got[key] != val:
                        bad("V5", f"claim {key} is {got[key]}, true value {val}")
            except Exception as ex:               # a broken sheet can make a check impossible
                bad("V5", f"claims could not be checked ({type(ex).__name__})")
    elif cl:
        bad("V5", "claims must be empty for tiers other than S")

    # cheapest / fewest-roads routes (needed by v7, v8)
    costly_target = False
    ratio_ok = False
    if roads_ok and V and hops0 is not None and -1 not in hops0:
        dist, best_fewest = route_costs(V, rd, pen, hops0)
        for t in targets:
            if 0 <= t < V:
                if best_fewest[t] > dist[t]:
                    costly_target = True
                if 2 * best_fewest[t] >= 3 * dist[t]:       # fewest-roads route costs at least 1.5 times the cheapest
                    ratio_ok = True
    summary["costly"] = costly_target

    # v7: signature rules (cases 0..45)
    if k <= 45:
        deg2 = 2 * E / V if V else 0                      # average degree
        if study == 1:
            if not 2.2 <= deg2 <= 3.2: bad("V7", f"delta: average degree {deg2:.2f} not in 2.2..3.2")
            if 5 * sum(1 for p in pen if p >= 2) < 2 * V: bad("V7", "delta: fewer than 40% locations with penalty >= 2")
            if len(wave_nos) < 3: bad("V7", "delta: fewer than 3 waves")
            if 100 * sum(1 for c in cats if c in (0, 1)) < 55 * n: bad("V7", "delta: food+water crates below 55%")
        elif study == 2:
            if not 2.0 <= deg2 <= 2.6: bad("V7", f"earthquake: average degree {deg2:.2f} not in 2.0..2.6")
            if 100 * sum(1 for c in cats if c in (2, 3)) < 45 * n: bad("V7", "earthquake: medicine+tool crates below 45%")
            if pris and sum(pris) < 6 * len(pris): bad("V7", "earthquake: mean alarm priority below 6.0")
        elif study == 3:
            if 4 * types.count("S") < V: bad("V7", "cyclone: fewer than 25% shelters")
            if len(wave_nos) < 3: bad("V7", "cyclone: fewer than 3 waves")
            if avg_overlap < 2: bad("V7", f"cyclone: windows overlap {avg_overlap:.2f} others on average (<2)")
            if len(set(log)) < 30: bad("V7", f"cyclone: log uses {len(set(log))} symbols (<30)")
        elif study == 4:
            if deg2 < 3.5: bad("V7", f"flash flood: average degree {deg2:.2f} < 3.5")
            if expect_tier in ("M", "L") and 2 * n_al < 3 * rate_ok_num[1]: bad("V7", "flash flood: fewer than 1.5 alarms per tick")
            if 10 * cats.count(4) < n: bad("V7", "flash flood: rare crates below 10%")
        elif study == 5:
            if deg2 > 2.4: bad("V7", f"landslide: average degree {deg2:.2f} > 2.4")
            if any(len(a) > 4 for a in adj): bad("V7", "landslide: a location has more than 4 roads")
            if hops0 and max(hops0) < V // 4: bad("V7", f"landslide: farthest location {max(hops0)} roads away (< {V // 4})")
            if len(wave_nos) < 3: bad("V7", "landslide: fewer than 3 waves")
            if roads_ok and V:
                after = bfs_hops(V, adj, 0, skip=union_closed)
                if all(after[t] != -1 for t in targets if 0 <= t < V):
                    bad("V7", "landslide: all targets still reachable after all waves")
        elif study == 6:
            if 100 * sum(1 for c in cats if c in (2, 1)) < 55 * n: bad("V7", "outbreak: medicine+water crates below 55%")
            if 2 * sum(1 for c in crates if c[4] <= 300) < n: bad("V7", "outbreak: fewer than half of the crates expire by hour 300")
            if log and 4 * max(log.count(ch) for ch in set(log)) < len(log): bad("V7", "outbreak: top symbol below 25% of log")

    # v8: trap rules
    if k == 46:
        fields = {
            "value": [c[3] for c in crates], "weight": [c[2] for c in crates], "expiry": [c[4] for c in crates],
            "serial": [c[5] for c in crates], "value_per_kg": [Fraction(c[3], c[2]) for c in crates],
        }
        mono = [name for name, seq in fields.items()
                if all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1)) or all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))]
        if len(mono) < 3:
            bad("V8", f"trap 46: only {len(mono)} monotone fields {mono}")
    if k == 47 and 10 * greedy > 6 * exact:
        bad("V8", f"trap 47: greedy reaches {greedy} of {exact} (> 60%)")
    if k == 48:
        far = bfs_hops(V, adj, hops0.index(max(hops0))) if hops0 else [0]
        if max(max(far), max(hops0 or [0])) < 500:
            bad("V8", "trap 48: no pair of locations 500 roads apart")
        if not ratio_ok:
            bad("V8", "trap 48: no target whose fewest-roads route costs >= 1.5 x cheapest")
    if k == 49:
        n_log = len(log)
        run_ok = False
        for m_ in range(1, 9):                           # longest stretch that repeats a block of m symbols
            best = run = 0
            for i in range(m_, n_log):
                run = run + 1 if log[i] == log[i - m_] else 0
                best = max(best, run)
            if 10 * (best + m_) >= 9 * n_log:
                run_ok = True
                break
        if not run_ok:
            bad("V8", "trap 49: less than 90% of the log repeats one block of <= 8 symbols")
        near = 0
        for p in pats:
            pat = str(p[2])
            prefix = pat[:-1]
            starts_n = n_log - len(pat) + 1
            hits = sum(1 for i in range(starts_n) if log.startswith(prefix, i))
            if 2 * hits >= starts_n:
                near += 1
        if near < 4:
            bad("V8", f"trap 49: only {near} patterns whose (length-1) prefix matches at half of the start positions")

    # facts needed for the rules over all cases
    summary["module_hashes"] = {
        "crates": hash(tuple(crates)), "roads": hash(tuple(tuple(r[1:]) for r in rd)),
        "locations": hash(tuple(tuple(r[1:]) for r in loc)), "log": hash(log), "windows": hash(tuple(wins)),
        "incidents": hash(tuple(tuple(r[1:]) for r in inc)), "sites": hash(tuple(pts)),
        "pipeline": hash(tuple(p[2] for p in pd)), "drum": hash(tuple(prices)),
        "sensors": hash(tuple(edges)), "safety": hash(tuple(tuple(r[2:]) for r in sr)),
        "rations": hash(tuple(tuple(r[2:]) for r in ra)),
    }
    summary["sizes"] = {"crates": n, "V": V, "E": E, "log": len(log), "windows": len(wins), "alarms": n_al, "sites": n_sites}


# checks of the whole workbook
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    partial = "--partial" in sys.argv
    if not args:
        print(__doc__)
        return 2
    names, data = load(args[0])
    global_errors = []
    expected = list(HEADERS)
    if names != expected:
        global_errors.append(f"V1: sheets are {names}, expected {expected}")
    S = {}
    for name in expected:
        if name not in data:
            global_errors.append(f"V1: sheet {name} missing")
            S[name] = {}
            continue
        rows = data[name]
        if not rows or [str(h) for h in rows[0][:len(HEADERS[name])]] != HEADERS[name] or len(rows[0]) != len(HEADERS[name]):
            global_errors.append(f"V1: sheet {name} has wrong header")
        for r in rows[1:]:
            if any(isinstance(x, str) and x.startswith("=") for x in r):
                global_errors.append(f"V1: sheet {name} contains a formula")
                break
        S[name] = group(rows, len(HEADERS[name]))
    for name in expected:                                  # rows must be sorted by case_id and then the second column
        rows = data.get(name, [])[1:]
        keys = [(r[0], r[1] if len(r) > 1 and not isinstance(r[1], str) else 0) for r in rows]
        if keys != sorted(keys):
            global_errors.append(f"V1: sheet {name} is not sorted by case_id then second column")

    case_ids = sorted(S["cases"])
    seed_vals = {r[0][1] for r in S["cases"].values() if r}
    if not partial:
        want = [f"{next(iter(seed_vals), 0)}-{k:02d}" for k in range(50)]
        if case_ids != want or len(S["cases"]) != 50 or any(len(v) != 1 for v in S["cases"].values()):
            global_errors.append("V1: need exactly 50 distinct case_ids seed-00 .. seed-49, one row each in sheet cases")
    for name in expected:                                  # every row must belong to a case listed in sheet cases
        extra = set(S[name]) - set(case_ids)
        if extra:
            global_errors.append(f"V3: sheet {name} has rows of unknown cases {sorted(extra)[:3]}")

    results, summaries = {}, {}
    for cid in case_ids:
        errs, summ = [], {}
        try:
            check_case(cid, S, errs, summ)
        except Exception as ex:                            # bad data should be reported, not crash the validator
            errs.append(f"V1: case could not be checked ({type(ex).__name__}: {ex})")
        results[cid], summaries[cid] = errs, summ

    # variety rules (they need all 50 cases)
    if not partial:
        vs = [s for s in summaries.values() if "tier" in s]
        if sum(1 for s in vs if s["tier"] == "S" and s.get("greedy_fails")) < 5:
            global_errors.append("V7: variety 1 - fewer than 5 tier-S cases where greedy by value per kg is not optimal")
        if sum(1 for s in vs if s["tier"] == "S" and s.get("costly")) < 5:
            global_errors.append("V7: variety 2 - fewer than 5 tier-S cases where fewest roads costs more than cheapest")
        ml = [s["ratio"] for s in vs if s["tier"] in ("M", "L")]
        if len(ml) != 26 or any(not 2.5 <= r <= 6.0 for r in ml) or sum(r < 3.5 for r in ml) < 5 \
                or sum(3.5 <= r <= 4.8 for r in ml) < 8 or sum(r > 4.8 for r in ml) < 5:
            global_errors.append("V7: variety 3 - safety rules per switch not spread as required over the 26 M/L cases")
        for module in next(iter(summaries.values()), {}).get("module_hashes", {}):
            hashes = [s["module_hashes"][module] for s in vs if "module_hashes" in s]
            if len(hashes) != len(set(hashes)):
                global_errors.append(f"V7: variety 4 - two cases are equal in module {module}")

    # report
    failed = 0
    print(f"Validating {args[0]}  ({'partial' if partial else 'full'} mode)")
    for e in global_errors:
        print("  GLOBAL FAIL", e.replace("_", " "))
    for cid in case_ids:
        if results[cid]:
            failed += 1
            print(f"{cid}: FAIL")
            for e in results[cid]:
                print(f"    {e}")
        else:
            print(f"{cid}: PASS")
    ok = not global_errors and not failed
    print(f"RESULT: {'PASS' if ok else 'FAIL'}  ({len(case_ids) - failed} of {len(case_ids)} cases pass, {len(global_errors)} global failures)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
