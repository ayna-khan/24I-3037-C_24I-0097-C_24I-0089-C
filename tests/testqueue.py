"""Unit, boundary, malformed-input, reference and trap tests for module D."""
import random
import unittest

from tests.helpers import alarm_fixture
from tests.reference.refqueue import check_release, release_order as ref_release

from src.models import Alarm, InvalidInputError, TimeBudgetExceeded
from src.modules import emergencyqueue as D

METHODS = ("heap", "scan")


def ids(plan):
    return [i for i, _ in plan.releases]


class NormalCases(unittest.TestCase):
    def test_hand_example(self):
        alarms = [Alarm(1, 0, 3), Alarm(2, 0, 9), Alarm(3, 0, 9), Alarm(4, 1, 10)]
        for m in METHODS:
            with self.subTest(method=m):
                plan = D.release_order(alarms, m)
                # tick 0: 2 (p9, lower id); tick 1: 4 (p10 arrived); tick 2: 3; tick 3: 1
                self.assertEqual(plan.releases, ((2, 0), (4, 1), (3, 2), (1, 3)))
                self.assertEqual((plan.max_backlog, plan.total_wait, plan.max_wait), (3, 0 + 0 + 2 + 3, 3))

    def test_older_alarm_first_within_a_priority(self):
        alarms = [Alarm(5, 3, 7), Alarm(6, 0, 7), Alarm(7, 3, 7)]
        for m in METHODS:
            with self.subTest(method=m):
                self.assertEqual(ids(D.release_order(alarms, m)), [6, 5, 7])

    def test_ties_by_alarm_id(self):
        alarms = [Alarm(9, 0, 4), Alarm(3, 0, 4), Alarm(7, 0, 4)]
        for m in METHODS:
            with self.subTest(method=m):
                self.assertEqual(ids(D.release_order(alarms, m)), [3, 7, 9])

    def test_idle_gap_leaves_ticks_unused(self):
        alarms = [Alarm(1, 0, 5), Alarm(2, 10, 5)]
        for m in METHODS:
            with self.subTest(method=m):
                self.assertEqual(D.release_order(alarms, m).releases, ((1, 0), (2, 10)))

    def test_one_release_per_tick(self):
        alarms = [Alarm(i, 0, 1 + i % 10) for i in range(1, 40)]
        for m in METHODS:
            ticks = [t for _, t in D.release_order(alarms, m).releases]
            self.assertEqual(ticks, list(range(39)))

    def test_late_urgent_alarm_overtakes_waiting_ones(self):
        alarms = [Alarm(1, 0, 2), Alarm(2, 0, 2), Alarm(3, 1, 10)]
        for m in METHODS:
            self.assertEqual(ids(D.release_order(alarms, m)), [1, 3, 2])

    def test_input_order_does_not_matter(self):
        rng = random.Random(3)
        alarms = [Alarm(i, rng.randint(0, 30), rng.randint(1, 10)) for i in range(1, 80)]
        shuffled = alarms[:]
        rng.shuffle(shuffled)
        for m in METHODS:
            self.assertEqual(D.release_order(alarms, m).releases, D.release_order(shuffled, m).releases)


class BoundaryCases(unittest.TestCase):
    def test_empty_queue_is_reported_not_crashed(self):
        for m in METHODS:
            plan = D.release_order([], m)
            self.assertEqual((plan.status, plan.releases), ("EMPTY", ()))

    def test_single_alarm(self):
        for m in METHODS:
            self.assertEqual(D.release_order([Alarm(1, 5, 1)], m).releases, ((1, 5),))

    def test_priority_limits_are_valid(self):
        for m in METHODS:
            plan = D.release_order([Alarm(1, 0, 1), Alarm(2, 0, 10)], m)
            self.assertEqual(ids(plan), [2, 1])

    def test_alarm_arriving_exactly_at_the_release_tick_competes(self):
        # tick 1: alarm 2 (p9) arrives exactly when the second release happens and beats alarm 3 (p5)
        alarms = [Alarm(1, 0, 1), Alarm(3, 0, 5), Alarm(2, 1, 9)]
        for m in METHODS:
            self.assertEqual(ids(D.release_order(alarms, m)), [3, 2, 1])

    def test_large_burst_at_one_tick(self):
        alarms = [Alarm(i, 0, 1 + (i * 7) % 10) for i in range(1, 3001)]
        expected = sorted(alarms, key=lambda a: (-a.priority, a.tick, a.alarm_id))
        for m in METHODS:
            self.assertEqual(ids(D.release_order(alarms, m)), [a.alarm_id for a in expected])


class MalformedInput(unittest.TestCase):
    def test_bad_alarms(self):
        bad = {"priority 0": Alarm(1, 0, 0), "priority 11": Alarm(1, 0, 11), "negative tick": Alarm(1, -1, 5),
               "float tick": Alarm(1, 1.5, 5), "float priority": Alarm(1, 1, 5.0), "text id": Alarm("a", 1, 5)}
        for name, alarm in bad.items():
            for m in METHODS:
                with self.subTest(case=name, method=m):
                    with self.assertRaises(InvalidInputError):
                        D.release_order([alarm], m)

    def test_duplicate_id(self):
        for m in METHODS:
            with self.assertRaises(InvalidInputError):
                D.release_order([Alarm(1, 0, 5), Alarm(1, 2, 6)], m)

    def test_unknown_method(self):
        with self.assertRaises(InvalidInputError):
            D.release_order([Alarm(1, 0, 5)], "magic")

    def test_time_budget(self):
        alarms = [Alarm(i, 0, 1 + i % 10) for i in range(1, 600)]
        for m in METHODS:
            with self.assertRaises(TimeBudgetExceeded):
                D.release_order(alarms, m, deadline=0.0)


class CampaignAlarms(unittest.TestCase):
    def test_extra_alarms_get_new_ids(self):
        out = D.with_extra_alarms([Alarm(4, 0, 3), Alarm(9, 2, 5)], [(0, 9), (0, 10)])
        self.assertEqual(out[2:], [Alarm(10, 0, 9), Alarm(11, 0, 10)])

    def test_storm_alarm_priority_9_released_first_unless_outranked(self):
        base = [Alarm(1, 0, 4), Alarm(2, 0, 7), Alarm(3, 1, 10)]
        day = D.with_extra_alarms(base, [(0, 9)])
        for m in METHODS:
            self.assertEqual(ids(D.release_order(day, m))[:3], [4, 3, 2])

    def test_medical_alarm_priority_10_loses_tie_to_older_id(self):
        base = [Alarm(1, 0, 10), Alarm(2, 0, 3)]
        day = D.with_extra_alarms(base, [(0, 10)])
        for m in METHODS:
            self.assertEqual(ids(D.release_order(day, m))[:2], [1, 3])

    def test_added_to_empty_stream(self):
        self.assertEqual(D.with_extra_alarms([], [(0, 9)]), [Alarm(1, 0, 9)])


class FifoPolicy(unittest.TestCase):
    def test_fifo_ignores_priority_and_is_worse_for_urgent_alarms(self):
        alarms = [Alarm(1, 0, 1), Alarm(2, 0, 1), Alarm(3, 0, 10)]
        self.assertEqual(ids(D.release_fifo(alarms)), [1, 2, 3])
        self.assertEqual(ids(D.release_heap(alarms)), [3, 1, 2])
        self.assertEqual(dict(D.release_fifo(alarms).releases)[3], 2)

    def test_fifo_idle_gap_and_empty(self):
        self.assertEqual(D.release_fifo([Alarm(1, 0, 5), Alarm(2, 10, 5)]).releases, ((1, 0), (2, 10)))
        self.assertEqual(D.release_fifo([]).status, "EMPTY")


class AgainstReference(unittest.TestCase):
    def test_random_streams(self):
        rng = random.Random(41)
        for _ in range(200):
            n = rng.randint(0, 60)
            span = rng.choice([1, 5, 30, 200])
            alarms = [Alarm(i + 1, rng.randint(0, span), rng.randint(1, 10)) for i in range(n)]
            rng.shuffle(alarms)
            expected = tuple(ref_release(alarms))
            for m in METHODS:
                plan = D.release_order(alarms, m)
                self.assertEqual(plan.releases, expected, (m, alarms))
                if alarms:
                    self.assertEqual(check_release(alarms, plan), [])

    def test_tier_s_streams_of_the_master_dataset(self):
        data = alarm_fixture()
        self.assertGreaterEqual(len(data), 25)
        for cid, alarms in data.items():
            for m in METHODS:
                plan = D.release_order(alarms, m)
                self.assertEqual(plan.releases, tuple(ref_release(alarms)), (cid, m))
                self.assertEqual(check_release(alarms, plan), [], (cid, m))

    def test_heap_and_scan_agree_on_a_busy_stream(self):
        rng = random.Random(8)
        alarms = [Alarm(i + 1, i // 3 + rng.randint(0, 2), rng.randint(1, 10)) for i in range(2500)]
        a, b = D.release_heap(alarms), D.release_scan(alarms)
        self.assertEqual(a.releases, b.releases)
        self.assertEqual((a.max_backlog, a.total_wait, a.max_wait), (b.max_backlog, b.total_wait, b.max_wait))
        self.assertLess(a.ops["comparisons"], b.ops["comparisons"])


if __name__ == "__main__":
    unittest.main()