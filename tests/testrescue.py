"""Unit, boundary, malformed-input, reference, master-data and operation-count tests for module C."""
import csv
import math
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.reference.refrescue import best_total, brute_total, check_plan, earliest_finish_ids  # noqa: E402

from src.models import InvalidInputError, TimeBudgetExceeded  # noqa: E402
from src.modules import rescue as R  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "windows-sample.csv")
METHODS = ("greedy", "dp", "dpquad", "brute")
EXACT = ("dp", "dpquad", "brute")
OBJECTIVES = ("count", "value")


def mk(*sfv, first=1):
    """Windows from (start, finish, value) triples, ids first, first + 1, ..."""
    return [R.Window(first + i, s, f, v) for i, (s, f, v) in enumerate(sfv)]


def windows_fixture():
    """{case_id: (tier, case_no, count_opt or None, value_opt or None, [Window, ...])} from the master data sample."""
    out = {}
    with open(FIXTURE, newline="") as f:
        for r in csv.DictReader(f):
            entry = out.setdefault(r["case_id"], [r["tier"], int(r["case_no"]),
                                                    int(r["count_opt"]) if r["count_opt"] else None,
                                                    int(r["value_opt"]) if r["value_opt"] else None, []])
            entry[4].append(R.Window(int(r["window_id"]), int(r["start"]), int(r["finish"]), int(r["value"])))
    return {k: tuple(v) for k, v in out.items()}


def random_windows(rng, n, horizon=40, longest=12, max_value=9):
    out = []
    for i in range(n):
        s = rng.randint(0, horizon - 1)
        out.append(R.Window(i + 1, s, s + rng.randint(1, longest), rng.randint(0, max_value)))
    return out


class NormalCases(unittest.TestCase):
    def test_hand_example_count(self):
        # ids 1..5 = [0,3] [2,5] [4,7] [6,9] [3,6]. Order of finish: 1, 2, 5, 3, 4. The rule takes 1, skips 2
        # (starts at 2 < 3), takes 5 (starts at 3, touching), skips 3 (4 < 6), takes 4 (starts at 6, touching).
        wins = mk((0, 3, 1), (2, 5, 1), (4, 7, 1), (6, 9, 1), (3, 6, 1))
        plan = R.solve(wins, "count", "greedy")
        self.assertEqual((plan.status, plan.chosen, plan.total), ("OK", (1, 4, 5), 3))
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).total, 3, method)

    def test_long_valuable_window_blocks_two_short_ones(self):
        wins = mk((0, 10, 100), (0, 5, 10), (5, 10, 10))
        self.assertEqual(R.solve(wins, "count", "greedy").chosen, (2, 3))
        for method in ("dp", "dpquad", "brute"):
            plan = R.solve(wins, "value", method)
            self.assertEqual((plan.chosen, plan.total), ((1,), 100), method)
        greedy = R.solve(wins, "value", "greedy")
        self.assertEqual(greedy.total, 20)                   # greedy is not optimal for the value
        self.assertIn("not optimal", greedy.note)

    def test_shipped_methods_are_the_default(self):
        wins = mk((0, 10, 100), (0, 5, 10), (5, 10, 10))
        self.assertEqual(R.solve(wins, "count"), R.solve(wins, "count", "greedy"))
        self.assertEqual(R.solve(wins, "value"), R.solve(wins, "value", "dp"))
        self.assertEqual(R.solve(wins), R.solve(wins, "count", "greedy"))

    def test_same_finish_lower_id_first(self):
        wins = [R.Window(7, 0, 10, 5), R.Window(3, 2, 10, 5)]
        for method in ("greedy", "dp", "dpquad"):
            self.assertEqual(R.solve(wins, "count", method).chosen, (3,), method)
            self.assertEqual(R.solve(wins, "value", method).chosen, (3,), method)

    def test_equal_total_does_not_take_the_later_window(self):
        # id 1 = [0,10] worth 20; ids 2, 3 = [0,5] and [5,10] worth 10 each: both options total 20.
        # Order of finish: 2, 1, 3. Window 3 gives 20 again, not strictly more, so it is not taken: {1}.
        wins = mk((0, 10, 20), (0, 5, 10), (5, 10, 10))
        for method in ("dp", "dpquad"):
            self.assertEqual(R.solve(wins, "value", method).chosen, (1,), method)
        self.assertEqual(R.solve(wins, "value", "brute").total, 20)

    def test_set_does_not_depend_on_input_order(self):
        rng = random.Random(3)
        wins = random_windows(rng, 30)
        for objective in OBJECTIVES:
            for method in ("greedy", "dp"):
                expected = R.solve(wins, objective, method).chosen
                for _ in range(5):
                    shuffled = wins[:]
                    rng.shuffle(shuffled)
                    self.assertEqual(R.solve(shuffled, objective, method).chosen, expected)

    def test_input_is_not_modified(self):
        wins = mk((5, 9, 1), (0, 3, 2), (3, 5, 3))
        copy = list(wins)
        for method in METHODS:
            R.solve(wins, "value", method)
        self.assertEqual(wins, copy)

    def test_tuples_and_plain_objects_are_accepted(self):
        class Plain:
            def __init__(self, i, s, f, v):
                self.window_id, self.start, self.finish, self.value = i, s, f, v
        as_tuples = [(1, 0, 5, 3), (2, 5, 9, 4)]
        as_objects = [Plain(1, 0, 5, 3), Plain(2, 5, 9, 4)]
        self.assertEqual(R.solve(as_tuples, "value", "dp").total, 7)
        self.assertEqual(R.solve(as_objects, "value", "dp").total, 7)

    def test_selected_is_chosen(self):
        plan = R.solve(mk((0, 5, 1)), "count")
        self.assertEqual(plan.selected, plan.chosen)


class DayFilter(unittest.TestCase):
    def test_rule(self):
        wins = [R.Window(i, 0, 5, 1) for i in range(1, 21)]
        for day in range(0, 8):
            kept = [w.window_id for w in R.available_on_day(wins, day)]
            self.assertEqual(kept, [i for i in range(1, 21) if (i + day) % 5 != 0], f"day {day}")

    def test_one_in_five_is_removed(self):
        wins = [R.Window(i, 0, 5, 1) for i in range(1, 11)]
        self.assertEqual([w.window_id for w in R.available_on_day(wins, 1)], [1, 2, 3, 5, 6, 7, 8, 10])
        self.assertEqual([w.window_id for w in R.available_on_day(wins, 5)], [1, 2, 3, 4, 6, 7, 8, 9])

    def test_order_objects_and_input_are_kept(self):
        wins = [R.Window(9, 0, 5, 1), R.Window(2, 0, 5, 1), R.Window(4, 0, 5, 1), R.Window(3, 0, 5, 1)]
        copy = list(wins)
        out = R.available_on_day(wins, 1)                    # ids 9 and 4 are unavailable on day 1
        self.assertEqual(wins, copy)
        self.assertEqual(out, [wins[1], wins[3]])
        self.assertTrue(out[0] is wins[1])
        self.assertEqual(R.available_on_day(tuple(wins), 1), out)

    def test_all_unavailable_and_empty(self):
        wins = [R.Window(5, 0, 5, 1), R.Window(10, 6, 9, 2)]
        left = R.available_on_day(wins, 5)
        self.assertEqual(left, [])
        for objective in OBJECTIVES:
            for method in METHODS:
                plan = R.solve(left, objective, method)
                self.assertEqual((plan.status, plan.chosen, plan.total), ("EMPTY", (), 0))
                self.assertTrue(plan.note)
        self.assertEqual(R.available_on_day([], 3), [])

    def test_solve_after_filter_never_uses_an_unavailable_window(self):
        rng = random.Random(11)
        wins = random_windows(rng, 40)
        for day in range(1, 8):
            avail = R.available_on_day(wins, day)
            for objective in OBJECTIVES:
                plan = R.solve(avail, objective)
                self.assertFalse([i for i in plan.chosen if (i + day) % 5 == 0])
                self.assertEqual(plan.total, best_total(avail, objective))

    def test_bad_day_raises(self):
        wins = [R.Window(1, 0, 5, 1)]
        for bad in ("3", 2.0, None, True, [1]):
            with self.assertRaises(InvalidInputError, msg=repr(bad)):
                R.available_on_day(wins, bad)

    def test_bad_windows_raise(self):
        with self.assertRaises(InvalidInputError):
            R.available_on_day(5, 1)
        with self.assertRaises(InvalidInputError):
            R.available_on_day([(1.5, 0, 5, 1)], 1)
        with self.assertRaises(InvalidInputError):
            R.available_on_day([None], 1)


class Boundary(unittest.TestCase):
    def test_touching_windows_are_compatible(self):
        wins = mk((0, 10, 5), (10, 20, 7))
        for method in METHODS:
            for objective in OBJECTIVES:
                plan = R.solve(wins, objective, method)
                self.assertEqual(plan.chosen, (1, 2), (method, objective))
        self.assertEqual(R.solve(wins, "value", "dp").total, 12)

    def test_overlap_by_one_minute_is_not_compatible(self):
        wins = mk((0, 10, 5), (9, 20, 7))
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).total, 1, method)
        self.assertEqual(R.solve(wins, "value", "dp").chosen, (2,))

    def test_touching_in_either_direction_and_chain(self):
        wins = mk((20, 30, 1), (10, 20, 1), (0, 10, 1), (30, 40, 1))
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).chosen, (1, 2, 3, 4), method)

    def test_one_window(self):
        wins = mk((4, 9, 6))
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method)[:3], ("OK", (1,), 1), method)
            self.assertEqual(R.solve(wins, "value", method)[:3], ("OK", (1,), 6), method)

    def test_window_of_value_zero(self):
        wins = mk((0, 5, 0))
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).total, 1, method)
            plan = R.solve(wins, "value", method)
            self.assertEqual((plan.status, plan.chosen, plan.total), ("EMPTY", (), 0), method)
            self.assertIn("positive value", plan.note)
        wins = mk((0, 5, 0), (5, 9, 3))
        self.assertEqual(R.solve(wins, "value", "dp").chosen, (2,))

    def test_no_windows(self):
        for objective in OBJECTIVES:
            for method in METHODS:
                plan = R.solve([], objective, method)
                self.assertEqual((plan.status, plan.chosen, plan.total), ("EMPTY", (), 0))
                self.assertIn("no windows", plan.note)

    def test_identical_windows_choose_the_lowest_id(self):
        wins = [R.Window(8, 0, 5, 3), R.Window(2, 0, 5, 3), R.Window(5, 0, 5, 3)]
        for method in ("greedy", "dp", "dpquad"):
            self.assertEqual(R.solve(wins, "count", method).chosen, (2,), method)

    def test_nested_windows(self):
        wins = mk((0, 100, 50), (10, 20, 5), (30, 40, 6), (50, 60, 7))
        self.assertEqual(R.solve(wins, "count", "greedy").chosen, (2, 3, 4))
        self.assertEqual(R.solve(wins, "value", "dp").chosen, (1,))          # 50 against 18

    def test_start_zero_and_large_minutes(self):
        wins = [R.Window(1, 0, 1, 1), R.Window(2, 10 ** 9, 10 ** 9 + 5, 1)]
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).chosen, (1, 2), method)

    def test_negative_and_big_ids_are_whole_numbers(self):
        wins = [R.Window(-3, 0, 5, 1), R.Window(10 ** 12, 5, 9, 1)]
        self.assertEqual(R.solve(wins, "count").chosen, (-3, 10 ** 12))

    def test_brute_force_limit(self):
        wins = mk(*[(i, i + 1, 1) for i in range(R.BRUTE_FORCE_LIMIT + 1)])
        plan = R.solve(wins, "count", "brute")
        self.assertEqual((plan.status, plan.chosen, plan.total), ("INVALID", (), 0))
        self.assertIn("limited", plan.note)
        self.assertEqual(R.solve(wins, "count", "greedy").total, R.BRUTE_FORCE_LIMIT + 1)

    def test_brute_force_at_sixteen_windows(self):
        wins = mk(*[(i, i + 2, 1 + i % 4) for i in range(16)])
        self.assertEqual(R.solve(wins, "value", "brute").total, R.solve(wins, "value", "dp").total)


class Malformed(unittest.TestCase):
    BAD = [
        ("float start", [(1, 0.5, 5, 1)]), ("float id", [(1.0, 0, 5, 1)]), ("string value", [(1, 0, 5, "9")]),
        ("none field", [(1, None, 5, 1)]), ("bool field", [(1, 0, True, 1)]), ("bool id", [(True, 0, 5, 1)]),
        ("finish equals start", [(1, 5, 5, 1)]), ("finish before start", [(1, 9, 3, 1)]),
        ("negative start", [(1, -1, 5, 1)]), ("negative value", [(1, 0, 5, -1)]),
        ("duplicate id", [(1, 0, 5, 1), (1, 6, 9, 1)]), ("three fields", [(1, 0, 5)]),
        ("five fields", [(1, 0, 5, 1, 7)]), ("none window", [None]), ("string window", ["abcd"]),
        ("number window", [7]), ("good then bad", [(1, 0, 5, 1), (2, 3, 1, 1)]),
    ]

    def test_bad_windows_give_a_status_not_a_plan_or_a_crash(self):
        for name, wins in self.BAD:
            for objective in OBJECTIVES:
                for method in METHODS:
                    plan = R.solve(wins, objective, method)
                    self.assertEqual((plan.status, plan.chosen, plan.total), ("INVALID", (), 0), (name, objective, method))
                    self.assertTrue(plan.note.startswith("invalid input"), name)

    def test_windows_that_are_not_a_list(self):
        for bad in (None, 5, 3.5):
            plan = R.solve(bad, "count", "greedy")
            self.assertEqual(plan.status, "INVALID")

    def test_bad_objective_or_method(self):
        wins = mk((0, 5, 1))
        for objective in ("speed", "", None, 3, ["count"], "COUNT"):
            self.assertEqual(R.solve(wins, objective, "dp").status, "INVALID", repr(objective))
        for method in ("heap", "", 3, ["dp"], "DP"):
            self.assertEqual(R.solve(wins, "count", method).status, "INVALID", repr(method))

    def test_invalid_is_checked_even_when_a_method_would_not_look(self):
        wins = [(1, 0, 5, 1), (2, 7, 3, 1)]                  # the second window is broken
        for method in METHODS:
            self.assertEqual(R.solve(wins, "count", method).status, "INVALID", method)

    def test_validate_windows_raises_for_direct_callers(self):
        with self.assertRaises(InvalidInputError):
            R.validate_windows([(1, 5, 5, 1)])
        self.assertEqual(R.validate_windows([(1, 0, 5, 1)]), [R.Window(1, 0, 5, 1)])


class Invariants(unittest.TestCase):
    def test_check_plan_catches_a_wrong_plan(self):
        wins = mk((0, 10, 1), (5, 15, 1))
        bad = R.RescuePlan("OK", (1, 2), 2, {}, "")
        self.assertTrue(check_plan(wins, "count", bad))
        wrong_total = R.RescuePlan("OK", (1,), 9, {}, "")
        self.assertTrue(check_plan(wins, "count", wrong_total))
        self.assertFalse(check_plan(wins, "count", R.solve(wins, "count")))

    def test_every_plan_of_random_instances_satisfies_the_invariants(self):
        rng = random.Random(5)
        for k in range(120):
            wins = random_windows(rng, rng.randint(0, 12 if k % 2 else 40))     # brute force only on the small ones
            for objective in OBJECTIVES:
                for method in METHODS:
                    if method == "brute" and len(wins) > 12:
                        continue
                    plan = R.solve(wins, objective, method)
                    self.assertEqual(check_plan(wins, objective, plan), [], (objective, method, wins))


class AgainstReferences(unittest.TestCase):
    def test_small_instances_against_brute_force_reference(self):
        rng = random.Random(1)
        for _ in range(120):
            wins = random_windows(rng, rng.randint(1, 8), horizon=14, longest=6)
            for objective in OBJECTIVES:
                expected = brute_total(wins, objective)
                self.assertEqual(best_total(wins, objective), expected)
                for method in METHODS:
                    got = R.solve(wins, objective, method).total
                    if (objective, method) == ("value", "greedy"):
                        self.assertLessEqual(got, expected, wins)        # the greedy rule ignores values
                    else:
                        self.assertEqual(got, expected, (objective, method, wins))

    def test_larger_instances_against_timeline_reference(self):
        rng = random.Random(2)
        for _ in range(60):
            wins = random_windows(rng, rng.randint(20, 90), horizon=rng.choice((60, 200)), longest=rng.choice((8, 40)))
            for objective in OBJECTIVES:
                expected = best_total(wins, objective)
                dp = R.solve(wins, objective, "dp")
                quad = R.solve(wins, objective, "dpquad")
                self.assertEqual((dp.total, quad.total), (expected, expected))
                greedy = R.solve(wins, objective, "greedy")
                if objective == "count":
                    self.assertEqual(greedy.total, expected)
                else:
                    self.assertLessEqual(greedy.total, expected)

    def test_greedy_set_is_the_earliest_finish_set(self):
        rng = random.Random(4)
        for _ in range(80):
            wins = random_windows(rng, rng.randint(1, 60), horizon=50, longest=10)
            self.assertEqual(R.solve(wins, "count", "greedy").chosen, earliest_finish_ids(wins))

    def test_dp_and_dpquad_choose_equally_good_sets_with_many_ties(self):
        rng = random.Random(6)
        for _ in range(60):
            wins = random_windows(rng, 25, horizon=20, longest=5, max_value=2)
            a, b = R.solve(wins, "value", "dp"), R.solve(wins, "value", "dpquad")
            self.assertEqual(a.total, b.total)
            self.assertEqual(check_plan(wins, "value", b), [])


class MasterData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = windows_fixture()

    def test_tier_s_cases_reproduce_the_claims(self):
        checked = 0
        for cid, (tier, _no, count_opt, value_opt, wins) in self.cases.items():
            if tier != "S":
                continue
            checked += 1
            self.assertEqual(R.solve(wins, "count", "greedy").total, count_opt, cid)
            self.assertEqual(R.solve(wins, "count", "dp").total, count_opt, cid)
            self.assertEqual(R.solve(wins, "value", "dp").total, value_opt, cid)
            self.assertEqual(R.solve(wins, "value", "dpquad").total, value_opt, cid)
            self.assertLessEqual(R.solve(wins, "value", "greedy").total, value_opt, cid)
            if len(wins) <= 14:
                self.assertEqual(R.solve(wins, "count", "brute").total, count_opt, cid)
                self.assertEqual(R.solve(wins, "value", "brute").total, value_opt, cid)
        self.assertEqual(checked, 20)

    def test_tier_s_plans_satisfy_the_invariants(self):
        for cid, (tier, _no, _c, _v, wins) in self.cases.items():
            if tier != "S":
                continue
            for objective in OBJECTIVES:
                for method in ("greedy", "dp", "dpquad"):
                    self.assertEqual(check_plan(wins, objective, R.solve(wins, objective, method)), [], (cid, objective, method))

    def test_touching_pairs_exist_and_are_used(self):
        """The generator plants touching windows (start of one = finish of another): the plans must be allowed to use them."""
        used = 0
        for cid, (tier, _no, _c, _v, wins) in self.cases.items():
            if tier != "S":
                continue
            by_id = {w.window_id: w for w in wins}
            ids = R.solve(wins, "count", "greedy").chosen
            chosen = sorted((by_id[i] for i in ids), key=lambda w: w.start)
            used += sum(1 for a, b in zip(chosen, chosen[1:]) if a.finish == b.start)
        self.assertGreater(used, 0)

    def test_larger_and_trap_cases(self):
        seen = {"M": 0, "L": 0, "X": 0}
        for cid, (tier, no, _c, _v, wins) in self.cases.items():
            if tier == "S":
                continue
            seen[tier] += 1
            for objective in OBJECTIVES:
                expected = best_total(wins, objective)
                dp = R.solve(wins, objective, "dp")
                self.assertEqual(dp.total, expected, (cid, objective))
                self.assertEqual(check_plan(wins, objective, dp), [], (cid, objective))
                self.assertEqual(R.solve(wins, objective, "dpquad").total, expected, (cid, objective))
            greedy = R.solve(wins, "count", "greedy")
            self.assertEqual(greedy.chosen, earliest_finish_ids(wins), cid)
            self.assertEqual(greedy.total, best_total(wins, "count"), cid)
            self.assertLessEqual(R.solve(wins, "value", "greedy").total, best_total(wins, "value"), cid)
        self.assertEqual(seen, {"M": 2, "L": 1, "X": 4})

    def test_every_day_of_the_week_on_the_sample(self):
        for cid, (tier, _no, _c, _v, wins) in self.cases.items():
            if tier not in ("S", "M"):
                continue
            for day in range(1, 8):
                avail = R.available_on_day(wins, day)
                plan = R.solve(avail, "value", "dp")
                self.assertFalse([i for i in plan.chosen if (i + day) % 5 == 0], (cid, day))
                self.assertEqual(plan.total, best_total(avail, "value"), (cid, day))

    def test_pooled_windows_keep_the_optimum_of_the_parts(self):
        """Cases shifted by 1440 minutes do not overlap, so the optimum of a pool is the sum of the optima of its cases."""
        parts = [w for cid, (t, _n, _c, _v, w) in self.cases.items() if t == "S"][:5]
        pooled, offset = [], 0
        for part in parts:
            for w in part:
                pooled.append(R.Window(len(pooled) + 1, w.start + offset, w.finish + offset, w.value))
            offset += 1440
        for objective in OBJECTIVES:
            self.assertEqual(R.solve(pooled, objective, "dp").total, sum(R.solve(p, objective, "dp").total for p in parts))


class OperationCounts(unittest.TestCase):
    def test_greedy(self):
        wins = mk(*[(i, i + 3, 1) for i in range(0, 16)])
        ops = R.solve(wins, "count", "greedy").ops
        self.assertEqual(ops["items_examined"], 16)
        self.assertEqual(ops["moves"], 16 * 4)               # merge sort: n written per pass, ceil(log2 16) = 4 passes
        self.assertGreater(ops["comparisons"], 0)
        self.assertEqual((ops["probes"], ops["cells"], ops["subsets"], ops["calls"]), (0, 0, 0, 1))
        self.assertEqual(ops["pre"]["items_examined"], 16)

    def test_dp(self):
        m = 200
        rng = random.Random(8)
        wins = [w._replace(value=max(1, w.value)) for w in random_windows(rng, m, horizon=500, longest=30)]
        ops = R.solve(wins, "value", "dp").ops
        self.assertEqual((ops["cells"], ops["items_examined"]), (m, m))
        self.assertLessEqual(ops["probes"], m * (m.bit_length()))
        self.assertGreater(ops["probes"], m)
        self.assertGreater(ops["comparisons"], 0)

    def test_dpquad(self):
        m = 60
        rng = random.Random(9)
        wins = [w._replace(value=max(1, w.value)) for w in random_windows(rng, m, horizon=200, longest=20)]
        ops = R.solve(wins, "value", "dpquad").ops
        self.assertEqual(ops["items_examined"], m * (m - 1) // 2)
        self.assertEqual(ops["cells"], m)
        self.assertEqual(ops["probes"], 0)

    def test_brute(self):
        n = 9
        wins = mk(*[(i, i + 2, 1) for i in range(n)])
        ops = R.solve(wins, "count", "brute").ops
        self.assertEqual(ops["subsets"], 2 ** n)
        self.assertEqual(ops["pre"]["pair_tests"], n * (n - 1) // 2)

    def test_value_objective_drops_zero_value_windows_from_the_work(self):
        wins = mk((0, 5, 0), (5, 9, 4), (9, 12, 0))
        ops = R.solve(wins, "value", "dp").ops
        self.assertEqual(ops["cells"], 1)
        self.assertEqual(ops["pre"]["items_examined"], 3)

    def test_ops_have_the_same_keys_for_every_outcome(self):
        keys = set(R.solve(mk((0, 5, 1)), "count").ops)
        for plan in (R.solve([], "count"), R.solve([(1, 5, 5, 1)], "count"), R.solve(mk((0, 5, 1)), "nope"),
                     R.solve(mk((0, 5, 1)), "value", "brute")):
            self.assertEqual(set(plan.ops), keys)

    def test_expired_deadline_raises_time_budget(self):
        rng = random.Random(10)
        wins = random_windows(rng, 15)
        for method in METHODS:
            with self.assertRaises(TimeBudgetExceeded, msg=method):
                R.solve(wins, "count", method, deadline=0.0)

    def test_deadline_far_away_changes_nothing(self):
        rng = random.Random(12)
        wins = random_windows(rng, 40)
        for method in METHODS:
            self.assertEqual(R.solve(wins, "value", method, deadline=1e12).total, R.solve(wins, "value", method).total)

    def test_n_log_n_shape(self):
        """Doubling n must not quadruple the sort work of the greedy rule (a guard against an accidental O(n^2) sort)."""
        rng = random.Random(13)
        a = R.solve(random_windows(rng, 1000, horizon=5000), "count", "greedy").ops
        b = R.solve(random_windows(rng, 2000, horizon=5000), "count", "greedy").ops
        ratio = (b["comparisons"] + b["moves"]) / (a["comparisons"] + a["moves"])
        self.assertLess(ratio, 2.4)
        self.assertGreater(ratio, 1.9)
        self.assertTrue(2000 * math.log2(2000) * 1.2 > b["comparisons"])


if __name__ == "__main__":
    unittest.main()
