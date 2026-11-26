"""Golden checks against the seven-row table in Project Statement 7.4."""
import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from src.campaign import official_calendar, run_campaign
from src.cli import main, campaign_text
from src.models import InvalidInputError, TimeBudgetExceeded
from tests.testhamza import fixture, write_fixture
from time import perf_counter


class OfficialCalendarTests(unittest.TestCase):
    def test_exact_table_and_daily_resets(self):
        c = fixture()
        before = deepcopy(c)
        out = run_campaign(c)
        days = out['days']
        self.assertEqual([d['target'] for d in days], [2, 1, 0, 2, 1, 0, 2])
        self.assertEqual([d['closed_roads'] for d in days], [[], [2], [1], [2], [1], [1, 2], [1, 2]])
        self.assertEqual(days[1]['input']['changed_minutes'], {0: 2, 1: 2, 2: 11})
        self.assertEqual(days[1]['route']['cost'], 10)
        self.assertEqual(days[3]['input']['changed_penalties'], {1: 16})
        self.assertEqual(days[3]['route']['cost'], 18)
        self.assertEqual(days[4]['route']['cost'], 9)
        self.assertEqual([len(d['input']['extra_alarms']) for d in days], [0, 1, 0, 0, 1, 0, 0])
        self.assertEqual(days[1]['input']['extra_alarms'][0]['priority'], 9)
        self.assertEqual(days[4]['input']['extra_alarms'][0]['priority'], 10)
        self.assertEqual([d['input']['multipliers'] for d in days], [{}, {'3': 2}, {'0': 2}, {}, {'2': 3}, {}, {}])
        self.assertTrue(all(not d['input']['changed_minutes'] for d in days if d['day'] != 2))
        self.assertTrue(all(not d['input']['changed_penalties'] for d in days if d['day'] != 4))
        self.assertIsNone(days[6]['load'])
        self.assertEqual(days[6]['dispatch_status'], 'NO_ROUTE')
        self.assertEqual(c, before)
        self.assertTrue(all(all(d['checks'].values()) for d in days))

    def test_one_based_wave_labels_and_modulo(self):
        c = fixture()
        zero_based = run_campaign(c)
        one_based = run_campaign(replace(c, waves={1: (2,), 2: (1,)}))
        self.assertEqual([d['closed_roads'] for d in zero_based['days']],
                         [d['closed_roads'] for d in one_based['days']])
        one_wave = run_campaign(replace(c, waves={7: (2,)}))
        self.assertEqual([d['closed_roads'] for d in one_wave['days']], [[], [2], [2], [2], [2], [2], [2]])

    def test_reachable_evacuation_counts_without_loading(self):
        c = replace(fixture(), waves={0: (0,), 1: (1,)})
        out = run_campaign(c)
        day = out['days'][6]
        self.assertEqual((day['route']['path'], day['route']['cost'], day['load']), ((0, 2), 7, None))
        self.assertTrue(day['trip_made'])
        self.assertEqual(day['dispatch_status'], 'EVACUATION')
        self.assertEqual(out['summary']['evacuation_cost'], 7)
        self.assertEqual(out['summary']['route_cost'], sum(d['route']['cost'] for d in out['days'] if d['trip_made']))

    def test_algorithm_baselines_and_simple_policy(self):
        c = fixture()
        opt, base, simple = [run_campaign(c, policy=p) for p in ('optimized', 'baseline', 'simple')]
        for a, b, s in zip(opt['days'], base['days'], simple['days']):
            self.assertEqual(a['input'], b['input'])
            self.assertEqual(a['input'], s['input'])
            self.assertEqual(a['route']['cost'], b['route']['cost'])
            self.assertEqual(a['rescue']['total'], b['rescue']['total'])
            self.assertEqual(a['alarms']['releases'], b['alarms']['releases'])
            if a['load']:
                self.assertGreaterEqual(a['load']['total_value'], b['load']['total_value'])
        self.assertEqual(base['days'][0]['methods'], dict(A='greedy', B='bellman', C='dpquad', D='scan'))
        self.assertEqual(base['days'][6]['methods']['F'], 'prim')
        self.assertEqual(base['days'][6]['methods']['G_chain'], 'memo')
        self.assertEqual(opt['days'][6]['chain']['cost'], base['days'][6]['chain']['cost'])
        self.assertEqual(opt['days'][6]['drum']['price'], base['days'][6]['drum']['price'])

    def test_no_dispatch_to_unreachable_target(self):
        c = replace(fixture(), waves={0: (0, 2)})
        out = run_campaign(c)
        for d in out['days'][1:]:
            if d['target'] != 0:
                self.assertFalse(d['trip_made'])
                self.assertIsNone(d['load'])
                self.assertEqual(d['dispatch_status'], 'NO_ROUTE')

    def test_invalid_new_fields(self):
        for key, value in [('closure_mode', 'bad')]:
            cal = official_calendar()
            cal[key] = value
            with self.assertRaises(InvalidInputError):
                run_campaign(fixture(), cal)
        for key, value in [('minutes_ratio', [1, 0]), ('minutes_ratio', [1.5, 1]),
                           ('wave_indices', [-1]), ('wave_indices', [True]),
                           ('target_key', 'wrong'), ('all_waves', 1), ('penalty_multiplier', 0)]:
            cal = official_calendar()
            cal['days'][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(InvalidInputError):
                run_campaign(fixture(), cal)
        with self.assertRaises(InvalidInputError):
            run_campaign(replace(fixture(), waves={}))
        with self.assertRaises(TimeBudgetExceeded):
            run_campaign(fixture(), deadline=perf_counter() - 1)

    def test_no_route_or_load_error_is_hidden(self):
        from src.modules import routes
        solve = routes.solve
        def incorrect(*args, **kwargs):
            return solve(*args, **kwargs)._replace(cost=999)
        with patch('src.campaign.routes.solve', side_effect=incorrect), self.assertRaises(InvalidInputError):
            run_campaign(fixture())

    def test_cli_defaults_to_official_and_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            write_fixture(folder)
            path = Path(folder) / 'campaign.json'
            rc = main(['--master', folder, '--output', str(path), 'campaign', '--case', 'demo', '--compare'])
            self.assertEqual(rc, 0)
            reports = json.loads(path.read_text())
            self.assertEqual(set(reports), {'optimized', 'baseline', 'simple'})
            text = campaign_text(reports)
            self.assertIn('Storm', text)
            self.assertIn('Checked:', text)
            self.assertIn('baseline', text)

    def test_benchmark_records_calibration_timeout_as_dnf(self):
        from experiments.runBF import measured
        c = fixture()
        with patch('experiments.runBF.routes.solve', side_effect=TimeBudgetExceeded('test deadline')):
            row = measured('B', 'dijkstra', 'demo', c.locations, c.roads, 2)
        self.assertEqual(row['status'], 'DNF')
        self.assertNotIn('time_s', row)


if __name__ == '__main__':
    unittest.main()
