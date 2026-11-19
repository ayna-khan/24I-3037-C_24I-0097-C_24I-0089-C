"""Tests of the measurement helpers and the pooling rules used by the experiments."""
import math
import unittest

from tests.helpers import ROOT  # noqa: F401  (puts the project root on sys.path)

from experiments import mastersample as ms
from src import measure
from src.models import Alarm, Crate
from src.sorting import merge_sort


class Statistics(unittest.TestCase):
    def test_median_and_iqr(self):
        self.assertEqual(measure.median_iqr([1, 2, 3, 4, 5]), (3, 2))
        self.assertEqual(measure.median_iqr([4]), (4, 0))

    def test_loglog_fit_recovers_a_known_exponent(self):
        xs = [100, 200, 400, 800, 1600]
        f = measure.fit_loglog(xs, [3e-9 * x ** 2 for x in xs])
        self.assertAlmostEqual(f["slope"], 2.0, places=9)
        self.assertAlmostEqual(f["r2"], 1.0, places=9)

    def test_semilog_fit_recovers_a_known_base(self):
        f = measure.fit_semilog([8, 11, 14, 17, 20], [1e-7 * 2 ** n for n in (8, 11, 14, 17, 20)])
        self.assertAlmostEqual(f["base"], 2.0, places=9)

    def test_fit_needs_enough_points(self):
        with self.assertRaises(ValueError):
            measure.fit_loglog([1, 2], [1, 2])

    def test_relative_error(self):
        self.assertAlmostEqual(measure.relative_error(11, 10), 0.1)


class Sorting(unittest.TestCase):
    def test_merge_sort_orders_is_stable_and_counts(self):
        counts = {}
        items = [(3, "a"), (1, "b"), (3, "c"), (2, "d"), (1, "e")]
        out = merge_sort(items, lambda x, y: x[0] < y[0], counts)
        self.assertEqual([x[1] for x in out], ["b", "e", "d", "a", "c"])
        self.assertGreater(counts["comparisons"], 0)
        self.assertEqual(merge_sort([], lambda x, y: x < y, {}), [])


class Pooling(unittest.TestCase):
    CASES = [{"case_id": "g-00", "capacity": "30"}, {"case_id": "g-01", "capacity": "50"}]

    def test_crate_pool_renumbers_and_scales_capacity(self):
        by_case = {"g-00": [Crate(1, 0, 5, 9, 1, 1), Crate(2, 1, 6, 8, 1, 2)], "g-01": [Crate(1, 2, 7, 7, 1, 3), Crate(2, 3, 4, 6, 1, 4)]}
        crates, cap, joined = ms.pool_crates(self.CASES, by_case, 3)
        self.assertEqual([c.crate_id for c in crates], [1, 2, 3])
        self.assertEqual(joined, ["g-00", "g-01"])
        self.assertEqual(cap, (3 * 80) // 4)          # n * sum(W) / sum(crates of the joined cases)
        with self.assertRaises(ValueError):
            ms.pool_crates(self.CASES, by_case, 10)

    def test_alarm_pool_shifts_ticks_past_the_previous_case(self):
        by_case = {"g-00": [Alarm(1, 0, 3), Alarm(2, 4, 5)], "g-01": [Alarm(1, 0, 9), Alarm(2, 2, 1)]}
        alarms, joined = ms.pool_alarms(self.CASES, by_case, 4)
        self.assertEqual([(a.alarm_id, a.tick, a.priority) for a in alarms],
                         [(1, 0, 3), (2, 4, 5), (3, 5, 9), (4, 7, 1)])

    def test_sample_positions_follow_seed_mod_7(self):
        cases = [{"case_id": str(i), "tier": "S"} for i in range(30)]
        self.assertEqual([c["case_id"] for c in ms.sample_cases(cases, "S", 3, seed=41)], ["6", "13", "20"])


if __name__ == "__main__":
    unittest.main()