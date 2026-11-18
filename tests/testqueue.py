"""Unit, boundary, malformed-input, reference and trap tests for module A."""
import random
import unittest

from tests.helpers import crate_fixture
from tests.reference.refinventory import best_value, check_load

from src.models import Crate, InvalidInputError, TimeBudgetExceeded
from src.modules import inventory as A


def mk(*wv, start=1):
    """Crates from (weight, value) pairs, ids start, start+1, ..."""
    return [Crate(start + i, 0, w, v, 100, 1000 + i) for i, (w, v) in enumerate(wv)]


class NormalCases(unittest.TestCase):
    def test_hand_example(self):
        # weights 5,4,6,3 values 10,40,30,50 capacity 10 -> crates 2 and 4 (weight 7, value 90)
        crates = mk((5, 10), (4, 40), (6, 30), (3, 50))
        plan = A.solve_dp(crates, 10)
        self.assertEqual((plan.status, plan.selected, plan.total_weight, plan.total_value),
                         ("OK", (2, 4), 7, 90))

    def test_all_three_methods_agree_on_value(self):
        crates = mk((5, 10), (4, 40), (6, 30), (3, 50))
        values = {m: A.solve(crates, 10, m).total_value for m in ("dp", "brute")}
        self.assertEqual(values["dp"], values["brute"])

    def test_everything_fits(self):
        crates = mk((2, 5), (3, 6), (4, 7))
        plan = A.solve_dp(crates, 100)
        self.assertEqual(plan.selected, (1, 2, 3))

    def test_zero_value_crate_is_not_needed(self):
        crates = mk((2, 0), (3, 6))
        self.assertEqual(A.solve_dp(crates, 10).selected, (2,))

    def test_deterministic_and_order_independent_value(self):
        rng = random.Random(7)
        crates = mk(*[(rng.randint(1, 9), rng.randint(0, 30)) for _ in range(30)])
        first = A.solve_dp(crates, 40)
        self.assertEqual(first, A.solve_dp(crates, 40))
        shuffled = crates[:]
        rng.shuffle(shuffled)
        self.assertEqual(first.total_value, A.solve_dp(shuffled, 40).total_value)


class BoundaryCases(unittest.TestCase):
    def test_crate_exactly_filling_the_truck_is_allowed(self):
        crates = mk((10, 7))
        for method in ("dp", "greedy", "brute"):
            with self.subTest(method=method):
                self.assertEqual(A.solve(crates, 10, method).selected, (1,))

    def test_crate_one_kilo_too_heavy(self):
        for method in ("dp", "greedy", "brute"):
            with self.subTest(method=method):
                plan = A.solve(mk((11, 99)), 10, method)
                self.assertEqual((plan.status, plan.selected, plan.total_value), ("EMPTY", (), 0))

    def test_capacity_zero_is_empty_not_error(self):
        for method in ("dp", "greedy", "brute"):
            with self.subTest(method=method):
                plan = A.solve(mk((1, 5)), 0, method)
                self.assertEqual(plan.status, "EMPTY")
                self.assertIn("capacity", plan.note)

    def test_no_crates_is_empty(self):
        for method in ("dp", "greedy", "brute"):
            with self.subTest(method=method):
                self.assertEqual(A.solve([], 50, method).status, "EMPTY")

    def test_greedy_exact_fit_after_skipping(self):
        # ratio order is crate 1 (w 7), crate 2 (w 5, does not fit after 7), crate 3 (w 3 fits exactly)
        crates = mk((7, 70), (5, 45), (3, 24))
        self.assertEqual(A.solve_greedy(crates, 10).selected, (1, 3))

    def test_exact_fraction_not_float(self):
        # 2^53+1 and 2^53 have the same float ratio but not the same exact ratio; capacity fits one crate.
        big = 2 ** 53
        crates = [Crate(1, 0, 1, big, 1, 1), Crate(2, 0, 1, big + 1, 1, 2)]
        self.assertEqual(A.solve_greedy(crates, 1).selected, (2,))

    def test_ratio_tie_goes_to_lower_crate_id(self):
        crates = mk((5, 10), (5, 10), (4, 8))          # all ratio 2
        self.assertEqual(A.solve_greedy(crates, 5).selected, (1,))
        self.assertEqual(A.solve_greedy(crates, 9).selected, (1, 3))


class MalformedInput(unittest.TestCase):
    def test_bad_capacity(self):
        for bad in (-1, 3.5, "10", None, True):
            with self.subTest(capacity=bad):
                with self.assertRaises(InvalidInputError):
                    A.solve_dp(mk((1, 1)), bad)

    def test_bad_crates(self):
        cases = {"zero weight": mk((0, 5)), "negative weight": mk((-2, 5)), "negative value": mk((2, -5)),
                 "float weight": [Crate(1, 0, 2.5, 5, 1, 1)], "duplicate id": [Crate(1, 0, 2, 5, 1, 1), Crate(1, 0, 3, 6, 1, 2)]}
        for name, crates in cases.items():
            for method in ("dp", "greedy", "brute"):
                with self.subTest(case=name, method=method):
                    with self.assertRaises(InvalidInputError):
                        A.solve(crates, 10, method)

    def test_unknown_method(self):
        with self.assertRaises(InvalidInputError):
            A.solve(mk((1, 1)), 5, "magic")

    def test_brute_force_refuses_large_input(self):
        with self.assertRaises(InvalidInputError):
            A.solve_brute(mk(*[(1, 1)] * 23), 50)

    def test_time_budget(self):
        crates = mk(*[(3, 7)] * 200)
        with self.assertRaises(TimeBudgetExceeded):
            A.solve_dp(crates, 400, deadline=0.0)


class DayValues(unittest.TestCase):
    def test_multiplier_by_category(self):
        crates = [Crate(1, 3, 2, 7, 1, 1), Crate(2, 0, 2, 7, 1, 2), Crate(3, 2, 2, 7, 1, 3)]
        out = A.with_day_values(crates, {3: 2, 2: 3})
        self.assertEqual([c.value for c in out], [14, 7, 21])

    def test_changed_values_can_change_the_load(self):
        crates = [Crate(1, 0, 5, 10, 1, 1), Crate(2, 3, 5, 6, 1, 2)]
        self.assertEqual(A.solve_dp(crates, 5).selected, (1,))
        self.assertEqual(A.solve_dp(A.with_day_values(crates, {3: 2}), 5).selected, (2,))

    def test_bad_multiplier(self):
        with self.assertRaises(InvalidInputError):
            A.with_day_values(mk((1, 1)), {0: 1.5})


class AgainstReferences(unittest.TestCase):
    def test_random_small_instances_against_pareto_reference(self):
        rng = random.Random(41)
        for _ in range(300):
            n = rng.randint(0, 12)
            crates = mk(*[(rng.randint(1, 12), rng.randint(0, 60)) for _ in range(n)])
            cap = rng.randint(0, 40)
            expected = best_value([(c.weight, c.value) for c in crates], cap)
            for method in ("dp", "brute"):
                plan = A.solve(crates, cap, method)
                self.assertEqual(plan.total_value, expected, (method, crates, cap))
                self.assertEqual(check_load(crates, cap, plan), [])
            greedy = A.solve_greedy(crates, cap)
            self.assertLessEqual(greedy.total_value, expected)
            self.assertEqual(check_load(crates, cap, greedy), [])

    def test_tier_s_claims_of_the_master_dataset(self):
        checked = 0
        for cid, (tier, _, cap, claim, crates) in crate_fixture().items():
            if claim is None:
                continue
            checked += 1
            plan = A.solve_dp(crates, cap)
            self.assertEqual(plan.total_value, claim, cid)
            self.assertEqual(check_load(crates, cap, plan), [], cid)
            if len(crates) <= 20:
                self.assertEqual(A.solve_brute(crates, cap).total_value, claim, cid)
        self.assertGreaterEqual(checked, 25)

    def test_dp_on_medium_instance_against_reference(self):
        rng = random.Random(5)
        crates = mk(*[(rng.randint(1, 20), rng.randint(1, 200)) for _ in range(120)])
        cap = 300
        plan = A.solve_dp(crates, cap)
        self.assertEqual(plan.total_value, best_value([(c.weight, c.value) for c in crates], cap))
        self.assertEqual(check_load(crates, cap, plan), [])


class TrapCase47(unittest.TestCase):
    def test_bait_crate_trap(self):
        # the bait crate (11 kg, value 61) has the best ratio, two 10 kg crates (value 55 each) fit instead
        crates = mk((11, 61), (10, 55), (10, 55))
        self.assertEqual(A.solve_greedy(crates, 20).total_value, 61)
        self.assertEqual(A.solve_dp(crates, 20).total_value, 110)

    def test_every_trap47_case_of_the_sample(self):
        seen = 0
        for cid, (tier, case_no, cap, _, crates) in crate_fixture().items():
            if case_no != 47:
                continue
            seen += 1
            dp, greedy = A.solve_dp(crates, cap), A.solve_greedy(crates, cap)
            self.assertGreater(dp.total_value, greedy.total_value, cid)
            self.assertEqual(check_load(crates, cap, dp), [], cid)
            self.assertEqual(check_load(crates, cap, greedy), [], cid)
        self.assertGreaterEqual(seen, 10)


if __name__ == "__main__":
    unittest.main()
