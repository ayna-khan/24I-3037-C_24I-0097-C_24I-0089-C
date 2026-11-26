"""Independent references, contract checks and campaign integration for B/F."""
import csv
import json
import random
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

from src.models import Crate, Alarm, InvalidInputError, TimeBudgetExceeded
from src.network import Location, Road
from src.loader import CaseData, SCHEMAS, load_case, read_cases, verify_checksums
from src.modules import routes, networkplan, rescue
from src.campaign import run_campaign, validate_calendar
from src.backend import Backend
from src.validation import validate_case
from src.cli import main


def fixture():
    return CaseData(dict(case_id='demo', tier='S', capacity=4, target_0=2, target_1=1, target_2=0),
                    (Location(0, 'D', 0), Location(1, 'J', 8), Location(2, 'H', 0)),
                    (Road(0, 0, 1, 1, 2), Road(1, 1, 2, 1, 3), Road(2, 0, 2, 7, 10)),
                    {0: (2,), 1: (1,)}, (Crate(1, 3, 2, 5, 20, 100), Crate(2, 0, 3, 6, 300, 101)),
                    (Alarm(1, 0, 1), Alarm(2, 0, 10)),
                    (rescue.Window(1, 0, 2, 1), rescue.Window(2, 0, 4, 10), rescue.Window(3, 2, 3, 1)),
                    (10, 20, 5), (1, 5, 6, 7))


def calendar():
    return dict(name='test', inventory_mode='daily', days=[{'day': day} for day in range(1, 8)])


def write_fixture(root):
    """Tiny CSV dataset with exactly the production schema (no master dependency)."""
    c = fixture()
    meta = dict.fromkeys(SCHEMAS['cases'].split(), 0)
    meta.update(c.metadata, group_seed=41, case_no=0, scenario=1, tier='S')
    records = dict(cases=[meta], locations=[dict(case_id='demo', loc_id=n.loc_id, type=n.kind, penalty=n.penalty) for n in c.locations],
                   roads=[dict(case_id='demo', **r._asdict()) for r in c.roads],
                   waves=[dict(case_id='demo', wave_no=w, road_no=r) for w, ids in c.waves.items() for r in ids],
                   crates=[dict(case_id='demo', **r._asdict()) for r in c.crates],
                   incidents=[dict(case_id='demo', **r._asdict()) for r in c.alarms],
                   windows=[dict(case_id='demo', **r._asdict()) for r in c.windows],
                   pipeline_dims=[dict(case_id='demo', idx=i, dim=d) for i, d in enumerate(c.dims)],
                   drum_prices=[dict(case_id='demo', length=i, price=p) for i, p in enumerate(c.prices, 1)])
    for table, rows in records.items():
        with (Path(root) / f'{table}.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMAS[table].split())
            writer.writeheader()
            writer.writerows(rows)


def reference_distances(nodes, roads, blocked):
    """Floyd-Warshall, structurally independent of the shipped path methods."""
    ids = [n.loc_id for n in nodes]
    penalties = {n.loc_id: n.penalty for n in nodes}
    d = {(u, v): (0 if u == v else float('inf')) for u in ids for v in ids}
    for r in roads:
        if r.road_no not in blocked:
            d[r.u, r.v] = min(d[r.u, r.v], r.minutes + penalties[r.v])
            d[r.v, r.u] = min(d[r.v, r.u], r.minutes + penalties[r.u])
    for k in ids:
        for u in ids:
            for v in ids:
                d[u, v] = min(d[u, v], d[u, k] + d[k, v])
    return {v: (None if d[0, v] == float('inf') else d[0, v]) for v in ids}


def reference_forest(nodes, roads, blocked):
    """Exhaustive subsets: smallest cable cost preserving open-road reachability."""
    ids = {n.loc_id for n in nodes}
    edges = [r for r in roads if r.road_no not in blocked]

    def closure(part):
        adj = {v: {v} for v in ids}
        for r in part:
            adj[r.u].add(r.v)
            adj[r.v].add(r.u)
        for k in ids:
            for v in ids:
                if k in adj[v]:
                    adj[v].update(adj[k])
        return adj

    target = closure(edges)
    components = len({frozenset(v) for v in target.values()})
    return min(sum(r.cable for r in part) for part in combinations(edges, len(ids) - components)
               if closure(part) == target)


class RouteTests(unittest.TestCase):
    def test_destination_penalty_and_direction(self):
        c = fixture()
        self.assertEqual(routes.solve(c.locations, c.roads, 2).cost, 7)
        self.assertEqual(routes.solve(c.locations, c.roads, 1).cost, 9)
        self.assertEqual(routes.solve(c.locations, c.roads, 0, source=1).cost, 1)

    def test_shortest_hops_not_shortest_cost(self):
        c = fixture()
        p = routes.solve(c.locations, c.roads, 2, blocked=(2,))
        self.assertEqual((p.path, p.cost), ((0, 1, 2), 10))
        n = tuple(x._replace(penalty=0) for x in c.locations)
        p = routes.solve(n, c.roads, 2)
        self.assertEqual((p.path, p.fewest_path, p.cost, p.fewest_cost), ((0, 1, 2), (0, 2), 2, 7))

    def test_disconnected_and_source(self):
        c = fixture()
        p = routes.solve(c.locations, c.roads, 2, blocked=(1, 2))
        self.assertEqual((p.status, p.cost, p.path, p.reachable), ('NO_ROUTE', None, (), (0, 1)))
        self.assertEqual(routes.solve(c.locations, c.roads, 0).path, (0,))

    def test_invalid(self):
        c = fixture()
        for roads_, target, blocked in [(c.roads, 99, ()), (c.roads, True, ()),
                                        (c.roads, 2, (99,)), (c.roads + c.roads, 2, ()),
                                        ((c.roads[0]._replace(minutes=-1),), 2, ())]:
            with self.subTest(target=target, blocked=blocked), self.assertRaises(InvalidInputError):
                routes.solve(c.locations, roads_, target, blocked=blocked)

    def test_deadline(self):
        c = fixture()
        with self.assertRaises(TimeBudgetExceeded):
            routes.solve(c.locations, c.roads, 2, deadline=perf_counter() - 1)

    def test_independent_reference_random(self):
        rng = random.Random(41)
        for _ in range(40):
            nodes = [Location(i, 'J', rng.randrange(10)) for i in range(6)]
            roads_ = [Road(k, u, v, rng.randrange(1, 20), rng.randrange(1, 20))
                      for k, (u, v) in enumerate(combinations(range(6), 2)) if rng.random() < .4]
            blocked = {r.road_no for r in roads_ if rng.random() < .2}
            expected = reference_distances(nodes, roads_, blocked)
            for method in ('dijkstra', 'bellman'):
                plan = routes.solve(nodes, roads_, 5, method, blocked)
                self.assertEqual(plan.distances, expected)
                if plan.path:
                    by_id = {r.road_no: r for r in roads_}
                    self.assertEqual(sum(by_id[r].minutes + nodes[v].penalty
                                         for r, v in zip(plan.road_ids, plan.path[1:])), plan.cost)

    def test_deterministic(self):
        c = fixture()
        self.assertEqual(routes.solve(c.locations, c.roads, 2), routes.solve(c.locations[::-1], c.roads[::-1], 2))


class NetworkTests(unittest.TestCase):
    def test_known_optimum(self):
        c = fixture()
        for method in ('kruskal', 'prim'):
            p = networkplan.solve(c.locations, c.roads, method)
            self.assertEqual((p.cost, p.road_ids), (5, (0, 1)))

    def test_forest_and_subset(self):
        c = fixture()
        p = networkplan.solve(c.locations, c.roads, blocked=(1, 2))
        self.assertEqual((p.status, p.cost, p.components), ('FOREST', 2, ((0, 1), (2,))))
        self.assertEqual(networkplan.solve(c.locations, c.roads, vertices=(0,)).cost, 0)
        self.assertEqual(networkplan.solve(c.locations, c.roads, vertices=()).status, 'EMPTY')

    def test_bad_subset_method_deadline(self):
        c = fixture()
        for kw in (dict(vertices=[99]), dict(method='bad'), dict(blocked=[99])):
            with self.assertRaises(InvalidInputError):
                networkplan.solve(c.locations, c.roads, **kw)
        with self.assertRaises(TimeBudgetExceeded):
            networkplan.solve(c.locations, c.roads, deadline=perf_counter() - 1)

    def test_exhaustive_reference_random(self):
        rng = random.Random(42)
        for _ in range(40):
            nodes = [Location(i, 'J', 0) for i in range(5)]
            edges = [Road(k, u, v, 1, rng.randrange(1, 20)) for k, (u, v) in enumerate(combinations(range(5), 2))
                     if rng.random() < .6]
            blocked = {r.road_no for r in edges if rng.random() < .2}
            expected = reference_forest(nodes, edges, blocked)
            for method in ('kruskal', 'prim'):
                p = networkplan.solve(nodes, edges, method, blocked)
                self.assertEqual(p.cost, expected)
                self.assertEqual(len(p.road_ids), len(nodes) - len(p.components))


class CampaignTests(unittest.TestCase):
    def test_events_and_nonmutation(self):
        c, cal = fixture(), calendar()
        cal['days'][1].update(multipliers={'3': 3}, extra_alarms=[[0, 9]])
        cal['days'][2].update(close_waves=[0])
        cal['days'][3].update(close_waves=[1])
        cal['days'][4].update(open_roads=[2])
        cal['days'][6].update(review=True, load=False)
        before = deepcopy((c, cal))
        out = run_campaign(c, cal)
        self.assertEqual(out['days'][1]['load']['total_value'], 15)
        self.assertEqual(len(out['days'][1]['alarms']['releases']), 3)
        self.assertEqual(out['days'][3]['route']['status'], 'NO_ROUTE')
        self.assertIsNone(out['days'][3]['load'])
        self.assertEqual(out['days'][4]['route']['status'], 'OK')
        self.assertEqual(out['days'][6]['chain']['cost'], 1000)
        self.assertEqual(out['summary']['route_cost'], sum(d['route']['cost'] for d in out['days']
                         if d['load'] and d['load']['selected']))
        self.assertEqual((c, cal), before)

    def test_calls_teammate_interfaces(self):
        c, cal = fixture(), calendar()
        with patch('src.campaign.rescue.available_on_day', wraps=rescue.available_on_day) as filt:
            out = run_campaign(c, cal)
            self.assertEqual(filt.call_count, 7)
        for d in out['days']:
            self.assertTrue(all((wid + d['day']) % 5 for wid in d['rescue']['chosen']))

    def test_consume_and_expiry(self):
        c, cal = fixture(), calendar()
        cal['inventory_mode'] = 'consume'
        out = run_campaign(c, cal)
        self.assertEqual(out['summary']['delivered_value'], 11)
        cal['days'][0]['hour'] = 301
        self.assertEqual(run_campaign(c, cal)['days'][0]['load']['status'], 'EMPTY')

    def test_simple_policy_and_count(self):
        c, cal = fixture(), calendar()
        cal['days'][0]['objective'] = 'count'
        simple = run_campaign(c, cal, 'simple')
        opt = run_campaign(c, cal)
        self.assertEqual(simple['days'][0]['alarms']['releases'][0][0], 1)
        self.assertEqual(opt['days'][0]['alarms']['releases'][0][0], 2)
        self.assertEqual(opt['days'][0]['rescue']['total'], simple['days'][0]['rescue']['total'])

    def test_bad_calendars(self):
        c = fixture()
        for key, value in [('day', 0), ('target', 99), ('close_waves', [99]), ('typo', 1),
                           ('load', 1), ('multipliers', {'0': -1}), ('extra_alarms', [[0, 11]])]:
            cal = calendar()
            cal['days'][0][key] = value
            with self.subTest(key=key), self.assertRaises(InvalidInputError):
                run_campaign(c, cal)
        with self.assertRaises(InvalidInputError):
            run_campaign(c, {'days': []})


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_fixture(self.root)

    def test_roundtrip_and_backend(self):
        c = load_case(self.root, 'demo')
        self.assertEqual(c.locations, fixture().locations)
        self.assertEqual(c.dims, fixture().dims)
        api = Backend(self.root)
        self.assertEqual(api.route('demo', 2)['cost'], 7)
        self.assertEqual(api.network('demo')['cost'], 5)
        self.assertEqual(api.chain('demo')['cost'], 1000)
        self.assertEqual(api.drum('demo', 4)['price'], 10)
        self.assertEqual(len(api.campaign('demo', calendar())['days']), 7)
        self.assertEqual(api.case('demo')['metadata']['case_id'], 'demo')

    def test_malformed_numeric(self):
        path = self.root / 'roads.csv'
        path.write_text(path.read_text().replace('demo,0,0,1,1,2', 'demo,0,0,1,1.5,2'))
        with self.assertRaises(InvalidInputError):
            load_case(self.root, 'demo')

    def test_duplicate_case_and_unknown(self):
        with self.assertRaises(InvalidInputError):
            load_case(self.root, 'missing')
        path = self.root / 'cases.csv'
        text = path.read_text()
        path.write_text(text + text.splitlines()[1] + '\n')
        with self.assertRaises(InvalidInputError):
            read_cases(self.root)

    def test_cross_table_corruption(self):
        c = fixture()
        for bad in (replace(c, waves={1: (999,)}), replace(c, roads=c.roads + c.roads),
                    replace(c, dims=(1,)), replace(c, prices=(-1,)),
                    replace(c, crates=(c.crates[0]._replace(cat=9),))):
            with self.assertRaises(InvalidInputError):
                validate_case(bad)

    def test_checksum_corruption(self):
        import hashlib
        path = self.root / 'cases.csv'
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        (self.root / 'CHECKSUMS.txt').write_text(f'{digest}  cases.csv\n')
        self.assertEqual(verify_checksums(self.root), ['cases.csv'])
        path.write_text('damaged')
        with self.assertRaises(InvalidInputError):
            verify_checksums(self.root)

    def test_cli_json_and_failure(self):
        output = self.root / 'out.json'
        rc = main(['--master', str(self.root), '--output', str(output), 'route', '--case', 'demo', '--target', '2'])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(output.read_text())['cost'], 7)
        with patch('builtins.print'):
            self.assertEqual(main(['--master', str(self.root), 'route', '--case', 'missing', '--target', '2']), 2)


if __name__ == '__main__':
    unittest.main()
