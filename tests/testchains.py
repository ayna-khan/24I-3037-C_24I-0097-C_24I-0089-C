"""Unit, boundary, malformed-input, reference, master-data, recursion and operation-count tests for module G."""
import csv
import math
import os
import random
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tests.reference.refchains import (brute_drum, check_chain, check_cut, evaluate_bracketing,  # noqa: E402
                                       min_cost_by_merging, ref_chain, ref_drum, ref_greedy)

from src.models import InvalidInputError, TimeBudgetExceeded  # noqa: E402
from src.modules import chains as G  # noqa: E402

FIX = os.path.join(ROOT, "tests", "fixtures")
CHAIN_METHODS = ("dp", "memo", "brute")
DRUM_METHODS = ("dp", "memo", "greedy", "brute")
EXACT_DRUM = ("dp", "memo", "brute")
CLRS_DIMS = [30, 35, 15, 5, 10, 20, 25]
CLRS_PRICES = [1, 5, 8, 9, 10, 17, 17, 20, 24, 30]


def catalan(m):
    return math.comb(2 * m, m) // (m + 1)


def fixtures():
    """({case_id: (tier, case_no, dims)}, {case_id: (tier, case_no, drum_opt or None, prices)}) from the master data sample."""
    chains, drums = {}, {}
    with open(os.path.join(FIX, "pipeline-sample.csv"), newline="") as f:
        for r in csv.DictReader(f):
            entry = chains.setdefault(r["case_id"], [r["tier"], int(r["case_no"]), []])
            entry[2].append(int(r["dim"]))
    with open(os.path.join(FIX, "drum-sample.csv"), newline="") as f:
        for r in csv.DictReader(f):
            entry = drums.setdefault(r["case_id"], [r["tier"], int(r["case_no"]), int(r["drum_opt"]) if r["drum_opt"] else None, []])
            entry[3].append(int(r["price"]))
    return {k: tuple(v) for k, v in chains.items()}, {k: tuple(v) for k, v in drums.items()}


def random_dims(rng, n, high=6):
    return [rng.randint(1, high) for _ in range(n + 1)]


def random_prices(rng, length, high=6):
    return [rng.randint(0, high) for _ in range(length)]


class ChainNormal(unittest.TestCase):
    def test_textbook_example(self):
        for method in CHAIN_METHODS:
            plan = G.solve_chain(CLRS_DIMS, method)
            self.assertEqual((plan.status, plan.bracketing, plan.cost), ("OK", "((A1 (A2 A3)) ((A4 A5) A6))", 15125), method)

    def test_three_matrices_both_brackets(self):
        # (A1 A2) A3 = 10*100*5 + 10*5*50 = 7500; A1 (A2 A3) = 100*5*50 + 10*100*50 = 75000
        for method in CHAIN_METHODS:
            plan = G.solve_chain([10, 100, 5, 50], method)
            self.assertEqual((plan.bracketing, plan.cost), ("((A1 A2) A3)", 7500), method)
        plan = G.solve_chain([50, 5, 100, 10])        # the mirror image: A1 (A2 A3) is better
        self.assertEqual((plan.bracketing, plan.cost), ("(A1 (A2 A3))", 7500))

    def test_default_method_is_dp(self):
        self.assertEqual(G.solve_chain(CLRS_DIMS), G.solve_chain(CLRS_DIMS, "dp"))

    def test_tuple_and_input_not_modified(self):
        dims = [5, 4, 6, 2, 7]
        copy = list(dims)
        for method in CHAIN_METHODS:
            G.solve_chain(dims, method)
        self.assertEqual(dims, copy)
        self.assertEqual(G.solve_chain(tuple(dims)), G.solve_chain(dims))

    def test_equal_cost_splits_take_the_smallest_split_point(self):
        # equal dimensions: every bracketing costs the same, so the smallest split point k = 1 is taken everywhere
        for method in CHAIN_METHODS:
            self.assertEqual(G.solve_chain([5, 5, 5, 5], method).bracketing, "(A1 (A2 A3))", method)
            self.assertEqual(G.solve_chain([5, 5, 5, 5, 5], method).bracketing, "(A1 (A2 (A3 A4)))", method)
            self.assertEqual(G.solve_chain([1, 1, 1, 1], method).cost, 2, method)

    def test_a_tie_in_the_middle_of_a_larger_chain(self):
        # dims 2 3 2 3 2: ((A1 A2) A3) A4 and others; whatever the optimum, dp, memo, brute and the reference agree
        dims = [2, 3, 2, 3, 2]
        expected = ref_chain(dims)
        for method in CHAIN_METHODS:
            plan = G.solve_chain(dims, method)
            self.assertEqual((plan.cost, plan.bracketing), expected, method)

    def test_big_numbers(self):
        dims = [10 ** 9, 3, 10 ** 9, 5]
        for method in CHAIN_METHODS:
            self.assertEqual(G.solve_chain(dims, method).cost, ref_chain(dims)[0], method)


class ChainBoundary(unittest.TestCase):
    def test_one_matrix(self):
        for method in CHAIN_METHODS:
            plan = G.solve_chain([7, 9], method)
            self.assertEqual((plan.status, plan.bracketing, plan.cost), ("OK", "A1", 0), method)
            self.assertIn("single matrix", plan.note)

    def test_two_matrices(self):
        for method in CHAIN_METHODS:
            plan = G.solve_chain([2, 3, 4], method)
            self.assertEqual((plan.status, plan.bracketing, plan.cost), ("OK", "(A1 A2)", 24), method)

    def test_dimensions_of_one(self):
        for method in CHAIN_METHODS:
            plan = G.solve_chain([1, 1], method)
            self.assertEqual((plan.bracketing, plan.cost), ("A1", 0))
            plan = G.solve_chain([1, 1, 1], method)
            self.assertEqual((plan.bracketing, plan.cost), ("(A1 A2)", 1))

    def test_brackets_and_spaces_of_a_long_chain(self):
        plan = G.solve_chain([3] * 9)
        self.assertEqual(plan.bracketing.count("("), 7)
        self.assertEqual(plan.bracketing.count(")"), 7)
        self.assertEqual(plan.bracketing.count(" "), 7)
        self.assertEqual(evaluate_bracketing([3] * 9, plan.bracketing), plan.cost)

    def test_brute_force_limit_and_edge(self):
        dims = [2] * (G.BRUTE_CHAIN_LIMIT + 2)
        plan = G.solve_chain(dims, "brute")
        self.assertEqual((plan.status, plan.bracketing, plan.cost), ("TOO_LARGE", "", 0))
        self.assertIn("limited", plan.note)
        self.assertEqual(G.solve_chain(dims, "dp").status, "OK")
        at_limit = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14][:G.BRUTE_CHAIN_LIMIT + 1]
        self.assertEqual(G.solve_chain(at_limit, "brute").cost, G.solve_chain(at_limit, "dp").cost)


class ChainMalformed(unittest.TestCase):
    BAD = [("none", None), ("empty", []), ("one dimension", [5]), ("string", "123"), ("number", 5), ("dict", {1: 2, 3: 4}),
           ("zero", [3, 0, 4]), ("negative", [3, -1, 4]), ("float", [3, 2.5, 4]), ("whole float", [3, 4.0, 5]),
           ("bool", [True, 2, 3]), ("string entry", ["3", 4]), ("none entry", [3, None, 4]), ("nested", [[3], [4]]),
           ("zero first", [0, 4]), ("zero last", [4, 0])]

    def test_bad_dimensions_give_a_status_not_a_plan_or_a_crash(self):
        for name, dims in self.BAD:
            for method in CHAIN_METHODS:
                plan = G.solve_chain(dims, method)
                self.assertEqual((plan.status, plan.bracketing, plan.cost), ("INVALID", "", 0), (name, method))
                self.assertTrue(plan.note.startswith("invalid input"), name)

    def test_bad_method(self):
        for method in ("greedy", "heap", "", None, 3, ["dp"], "DP"):
            plan = G.solve_chain([2, 3, 4], method)
            self.assertEqual(plan.status, "INVALID", repr(method))
        self.assertIn("only for the drum", G.solve_chain([2, 3, 4], "greedy").note)

    def test_validate_dims_raises_for_direct_callers(self):
        with self.assertRaises(InvalidInputError):
            G.validate_dims([4])
        self.assertEqual(G.validate_dims((2, 3)), [2, 3])


class DrumNormal(unittest.TestCase):
    def test_textbook_example(self):
        expected = {4: ((2, 2), 10), 7: ((1, 6), 18), 10: ((10,), 30)}
        for length, (pieces, price) in expected.items():
            for method in EXACT_DRUM:
                plan = G.solve_drum(CLRS_PRICES, length, method)
                self.assertEqual((plan.status, plan.pieces, plan.price), ("OK", pieces, price), (length, method))

    def test_default_method_is_dp(self):
        self.assertEqual(G.solve_drum(CLRS_PRICES, 8), G.solve_drum(CLRS_PRICES, 8, "dp"))

    def test_equal_price_takes_the_fewest_pieces(self):
        # proportional prices: 3 = 3 = 1 + 2 = 1 + 1 + 1 in price, one piece is the fewest
        for method in EXACT_DRUM:
            self.assertEqual(G.solve_drum([1, 2, 3], 3, method).pieces, (3,), method)
            self.assertEqual(G.solve_drum([4, 8, 12, 16], 4, method).pieces, (4,), method)

    def test_equal_price_and_pieces_take_the_smallest_first_piece(self):
        # (1, 2) and (2, 1) both give 6 with two pieces; (3,) and (1, 1, 1) give 3
        for method in EXACT_DRUM:
            self.assertEqual(G.solve_drum([1, 5, 3], 3, method).pieces, (1, 2), method)

    def test_tie_between_different_piece_counts_and_orders(self):
        prices = [2, 3, 4, 8]                        # L = 4: (4,) = 8, (2, 2) = 6, (1, 1, 2) = 7 ... best is the single piece
        for method in EXACT_DRUM:
            self.assertEqual(G.solve_drum(prices, 4, method).pieces, (4,), method)
        prices = [3, 6, 6, 9]                        # L = 4: (1,3) = 9, (2,2) = 12, (4,) = 9 ... (2,2) wins; (2,2) before (1,1,2)? 12 = 12 too: fewest pieces
        for method in EXACT_DRUM:
            plan = G.solve_drum(prices, 4, method)
            self.assertEqual((plan.price, plan.pieces), (12, (2, 2)), method)

    def test_greedy_is_a_rule_of_thumb(self):
        plan = G.solve_drum([1, 5, 8, 9], 4, "greedy")        # best ratio is length 3 (2.67): 3 + 1 = 9, the optimum is 2 + 2 = 10
        self.assertEqual((plan.status, plan.pieces, plan.price), ("OK", (3, 1), 9))
        self.assertIn("not optimal", plan.note)
        self.assertEqual(G.solve_drum([1, 5, 8, 9], 4, "dp").price, 10)

    def test_greedy_ties_go_to_the_longer_piece(self):
        self.assertEqual(G.solve_drum([2, 4, 6], 3, "greedy").pieces, (3,))
        self.assertEqual(G.solve_drum([2, 4, 5, 8], 4, "greedy").pieces, (4,))             # lengths 1, 2 and 4 have ratio 2, 3 has less
        plan = G.solve_drum([2, 4, 6, 8, 10, 12, 14], 7, "greedy")
        self.assertEqual(plan.pieces, (7,))                                               # all ratios equal: the longest piece

    def test_greedy_compares_exact_fractions(self):
        big = 10 ** 17
        prices = [big + 1, 1, 3 * big]                        # ratios big + 1 and big: a float would call them equal
        plan = G.solve_drum(prices, 3, "greedy")
        self.assertEqual((plan.pieces, plan.price), ((1, 1, 1), 3 * big + 3))

    def test_prices_as_tuple_and_mapping_and_longer_list(self):
        expected = G.solve_drum(CLRS_PRICES, 6)
        self.assertEqual(G.solve_drum(tuple(CLRS_PRICES), 6), expected)
        self.assertEqual(G.solve_drum({k + 1: p for k, p in enumerate(CLRS_PRICES)}, 6), expected)
        self.assertEqual(G.solve_drum(CLRS_PRICES + [-5, "x"], 10).price, 30)        # prices beyond L are not looked at

    def test_input_not_modified(self):
        prices = list(CLRS_PRICES)
        for method in DRUM_METHODS:
            G.solve_drum(prices, 9, method)
        self.assertEqual(prices, CLRS_PRICES)


class DrumBoundary(unittest.TestCase):
    def test_length_one(self):
        for method in DRUM_METHODS:
            plan = G.solve_drum([7, 99], 1, method)
            self.assertEqual((plan.status, plan.pieces, plan.price), ("OK", (1,), 7), method)

    def test_length_two(self):
        for method in EXACT_DRUM:
            self.assertEqual(G.solve_drum([5, 11], 2, method).pieces, (2,))
            self.assertEqual(G.solve_drum([5, 11], 2, method).price, 11)
            self.assertEqual(G.solve_drum([5, 9], 2, method).pieces, (1, 1))          # 5 + 5 = 10 beats 9
            self.assertEqual(G.solve_drum([5, 9], 2, method).price, 10)

    def test_length_zero_is_invalid(self):
        for method in DRUM_METHODS:
            plan = G.solve_drum([1, 2, 3], 0, method)
            self.assertEqual((plan.status, plan.pieces, plan.price), ("INVALID", (), 0), method)
            self.assertIn("must be >= 1", plan.note)

    def test_all_prices_zero(self):
        for method in EXACT_DRUM:
            plan = G.solve_drum([0, 0, 0, 0], 4, method)
            self.assertEqual((plan.status, plan.pieces, plan.price), ("OK", (4,), 0), method)

    def test_brute_force_limit(self):
        prices = list(range(1, 40))
        plan = G.solve_drum(prices, G.BRUTE_DRUM_LIMIT + 1, "brute")
        self.assertEqual((plan.status, plan.pieces, plan.price), ("TOO_LARGE", (), 0))
        self.assertIn("limited", plan.note)
        self.assertEqual(G.solve_drum(prices, 14, "brute").price, G.solve_drum(prices, 14, "dp").price)


class DrumMalformed(unittest.TestCase):
    BAD = [("length zero", [1, 2], 0), ("negative length", [1, 2], -1), ("float length", [1, 2], 2.0), ("string length", [1, 2], "2"),
           ("bool length", [1, 2], True), ("none length", [1, 2], None), ("missing price", [1, 2], 3), ("no prices", [], 1),
           ("none prices", None, 2), ("string prices", "123", 2), ("number prices", 5, 2), ("negative price", [1, -2], 2),
           ("float price", [1, 2.5], 2), ("bool price", [1, True], 2), ("string price", [1, "2"], 2), ("none price", [1, None], 2),
           ("mapping missing a key", {1: 5, 3: 7}, 3), ("mapping with a bad price", {1: 5, 2: -1}, 2)]

    def test_bad_input_gives_a_status_not_a_plan_or_a_crash(self):
        for name, prices, length in self.BAD:
            for method in DRUM_METHODS:
                plan = G.solve_drum(prices, length, method)
                self.assertEqual((plan.status, plan.pieces, plan.price), ("INVALID", (), 0), (name, method))
                self.assertTrue(plan.note.startswith("invalid input"), name)

    def test_bad_method(self):
        for method in ("heap", "", None, 3, ["dp"], "DP"):
            self.assertEqual(G.solve_drum([1, 2], 2, method).status, "INVALID", repr(method))

    def test_validate_drum_raises_for_direct_callers(self):
        with self.assertRaises(InvalidInputError):
            G.validate_drum([1], 2)
        self.assertEqual(G.validate_drum([4, 5], 2), ([0, 4, 5], 2))


class Recursion(unittest.TestCase):
    def test_deeper_than_the_default_recursion_limit(self):
        before = sys.getrecursionlimit()
        stack_before = threading.stack_size()
        prices = [1 + (k * 7) % 11 for k in range(1, 1301)]
        memo, dp = G.solve_drum(prices, 1200, "memo"), G.solve_drum(prices, 1200, "dp")      # 1200 calls deep: above the default limit of 1000
        self.assertEqual(memo.status, "OK")
        self.assertEqual((memo.pieces, memo.price), (dp.pieces, dp.price))
        self.assertEqual(sys.getrecursionlimit(), before)                  # restored
        self.assertEqual(threading.stack_size(), stack_before)

    def test_the_thread_route_for_a_chain(self):
        old = G.DEEP_THRESHOLD
        G.DEEP_THRESHOLD = 10                                              # a 60 matrix chain now goes through the thread
        try:
            dims = [1 + (k * 5) % 9 for k in range(61)]
            memo = G.solve_chain(dims, "memo")
        finally:
            G.DEEP_THRESHOLD = old
        dp = G.solve_chain(dims, "dp")
        self.assertEqual((memo.status, memo.bracketing, memo.cost), (dp.status, dp.bracketing, dp.cost))

    def test_too_deep_is_a_status(self):
        plan = G.solve_drum([1] * (G.MEMO_MAX_DEPTH + 10), G.MEMO_MAX_DEPTH + 5, "memo")
        self.assertEqual((plan.status, plan.pieces, plan.price), ("TOO_LARGE", (), 0))
        self.assertIn("deep", plan.note)
        plan = G.solve_chain([2] * (G.MEMO_MAX_DEPTH + 5), "memo")
        self.assertEqual((plan.status, plan.bracketing), ("TOO_LARGE", ""))

    def test_run_deep_handles_a_very_deep_recursion_and_reports_a_recursion_error(self):
        def descend(k):
            return 0 if k == 0 else 1 + descend(k - 1)
        self.assertEqual(G._run_deep(lambda: descend(15000), 15000), 15000)
        with self.assertRaises(RecursionError):
            G._run_deep(lambda: descend(10 ** 6), 1000)                    # the limit is only depth + 1000

    def test_a_recursion_error_inside_a_method_becomes_too_large(self):
        original = G._run_deep

        def failing(fn, depth):
            raise RecursionError("simulated")
        G._run_deep = failing
        try:
            self.assertEqual(G.solve_drum([1, 2, 3], 3, "memo").status, "TOO_LARGE")
            self.assertEqual(G.solve_chain([1, 2, 3, 4], "memo").status, "TOO_LARGE")
        finally:
            G._run_deep = original

    def test_dp_has_no_recursion_at_all(self):
        plan = G.solve_drum([1] * 3000, 3000, "dp")                       # 3000 > the default recursion limit
        self.assertEqual((plan.status, plan.price), ("OK", 3000))

    def test_the_bracketing_is_built_without_recursion(self):
        n = 5000                                                           # a left-deep chain 5000 brackets deep
        split = {1: {j: j - 1 for j in range(2, n + 1)}}
        text = G._bracketing(split, n)
        self.assertEqual(text.count("("), n - 1)
        self.assertTrue(text.startswith("(" * (n - 1) + "A1 A2) A3)"))
        self.assertTrue(text.endswith(f"A{n})"))


class Invariants(unittest.TestCase):
    def test_checkers_catch_wrong_plans(self):
        dims = [10, 100, 5, 50]
        good = G.solve_chain(dims)
        self.assertEqual(check_chain(dims, good), [])
        self.assertTrue(check_chain(dims, good._replace(cost=good.cost + 1)))
        self.assertTrue(check_chain(dims, good._replace(bracketing="(A1 (A2 A3))")))       # valid but its cost differs
        for broken in ("A1 A2 A3", "((A1 A2) A4)", "(A2 A1)", "((A1 A2 A3))", "(A1 (A2 A3)", "((A1 A2) A3))"):
            self.assertTrue(check_chain(dims, good._replace(bracketing=broken)), broken)
        prices = [1, 5, 8, 9]
        cut = G.solve_drum(prices, 4)
        self.assertEqual(check_cut(prices, 4, cut), [])
        self.assertTrue(check_cut(prices, 4, cut._replace(price=cut.price + 1)))
        self.assertTrue(check_cut(prices, 4, cut._replace(pieces=(2, 1))))                 # adds up to 3
        self.assertTrue(check_cut(prices, 4, cut._replace(pieces=(0, 4))))

    def test_every_plan_of_random_instances_satisfies_the_invariants(self):
        rng = random.Random(5)
        for _ in range(80):
            dims = random_dims(rng, rng.randint(1, 9))
            for method in CHAIN_METHODS:
                self.assertEqual(check_chain(dims, G.solve_chain(dims, method)), [], (dims, method))
            prices = random_prices(rng, rng.randint(1, 12))
            for method in DRUM_METHODS:
                plan = G.solve_drum(prices, len(prices), method)
                self.assertEqual(check_cut(prices, len(prices), plan), [], (prices, method))


class AgainstReferences(unittest.TestCase):
    def test_small_chains_against_exhaustive_references(self):
        rng = random.Random(1)
        for _ in range(150):
            dims = random_dims(rng, rng.randint(1, 8), high=rng.choice((2, 4, 9)))      # small numbers: many ties
            cost, text = ref_chain(dims)
            self.assertEqual(cost, min_cost_by_merging(dims), dims)
            for method in CHAIN_METHODS:
                plan = G.solve_chain(dims, method)
                self.assertEqual((plan.cost, plan.bracketing), (cost, text), (dims, method))

    def test_larger_chains_against_the_reference(self):
        rng = random.Random(2)
        for _ in range(25):
            dims = random_dims(rng, rng.randint(15, 45), high=rng.choice((3, 20)))
            cost, text = ref_chain(dims)
            for method in ("dp", "memo"):
                plan = G.solve_chain(dims, method)
                self.assertEqual((plan.cost, plan.bracketing), (cost, text), method)

    def test_small_drums_against_exhaustive_references(self):
        rng = random.Random(3)
        for _ in range(150):
            length = rng.randint(1, 12)
            prices = random_prices(rng, length, high=rng.choice((2, 5, 20)))              # small numbers: many ties
            price, pieces = ref_drum(prices, length)
            self.assertEqual((price, pieces), brute_drum(prices, length), prices)
            for method in EXACT_DRUM:
                plan = G.solve_drum(prices, length, method)
                self.assertEqual((plan.price, plan.pieces), (price, pieces), (prices, method))

    def test_larger_drums_against_the_reference(self):
        rng = random.Random(4)
        for _ in range(25):
            length = rng.randint(30, 120)
            prices = sorted(random_prices(rng, length, high=60)) if rng.random() < 0.5 else random_prices(rng, length, high=60)
            price, pieces = ref_drum(prices, length)
            for method in ("dp", "memo"):
                plan = G.solve_drum(prices, length, method)
                self.assertEqual((plan.price, plan.pieces), (price, pieces), method)

    def test_greedy_against_its_reference_and_never_above_the_optimum(self):
        rng = random.Random(6)
        for _ in range(100):
            length = rng.randint(1, 40)
            prices = random_prices(rng, length, high=rng.choice((3, 30, 300)))
            greedy = G.solve_drum(prices, length, "greedy")
            self.assertEqual((greedy.price, greedy.pieces), ref_greedy(prices, length), prices)
            self.assertLessEqual(greedy.price, ref_drum(prices, length)[0])


class MasterData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chains, cls.drums = fixtures()

    def test_tier_s_drums_reproduce_the_claims(self):
        checked = 0
        for cid, (tier, _no, claim, prices) in self.drums.items():
            if tier != "S":
                continue
            checked += 1
            length = len(prices)
            plans = {m: G.solve_drum(prices, length, m) for m in DRUM_METHODS}
            for m in EXACT_DRUM:
                self.assertEqual(plans[m].price, claim, (cid, m))
                self.assertEqual(plans[m].pieces, plans["dp"].pieces, (cid, m))
            self.assertLessEqual(plans["greedy"].price, claim, cid)
            self.assertEqual((plans["dp"].price, plans["dp"].pieces), ref_drum(prices, length), cid)
            self.assertEqual(check_cut(prices, length, plans["dp"]), [], cid)
            self.assertEqual(check_cut(prices, length, plans["greedy"]), [], cid)
        self.assertEqual(checked, 20)

    def test_tier_s_chains_against_brute_force_and_reference(self):
        checked = 0
        for cid, (tier, _no, dims) in self.chains.items():
            if tier != "S":
                continue
            checked += 1
            cost, text = ref_chain(dims)
            self.assertEqual(cost, min_cost_by_merging(dims), cid)
            for method in CHAIN_METHODS:
                plan = G.solve_chain(dims, method)
                self.assertEqual((plan.cost, plan.bracketing), (cost, text), (cid, method))
            self.assertEqual(check_chain(dims, G.solve_chain(dims)), [], cid)
        self.assertEqual(checked, 20)

    def test_larger_chains_and_trap_cases(self):
        seen = {"M": 0, "L": 0, "X": 0}
        for cid, (tier, _no, dims) in self.chains.items():
            if tier == "S":
                continue
            seen[tier] += 1
            dims = list(dims[:81])                                          # at most 80 matrices keeps the reference fast
            cost, text = ref_chain(dims)
            for method in ("dp", "memo"):
                plan = G.solve_chain(dims, method)
                self.assertEqual((plan.cost, plan.bracketing), (cost, text), (cid, method))
            self.assertEqual(check_chain(dims, G.solve_chain(dims)), [], cid)
        self.assertEqual(seen, {"M": 2, "L": 1, "X": 4})

    def test_one_full_size_chain(self):
        longest = max(self.chains.items(), key=lambda kv: len(kv[1][2]))
        dims = list(longest[1][2])
        plan = G.solve_chain(dims)
        self.assertEqual(plan.status, "OK")
        self.assertEqual(check_chain(dims, plan), [])
        self.assertGreater(len(dims), 150)                                 # the longest chain of the sample, full size, dp only
        part = dims[:151]                                                  # the memoised recursion on its first 150 matrices
        self.assertEqual(G.solve_chain(part, "memo").cost, G.solve_chain(part, "dp").cost)

    def test_larger_drums_and_trap_cases(self):
        seen = {"M": 0, "L": 0, "X": 0}
        for cid, (tier, _no, _claim, prices) in self.drums.items():
            if tier == "S":
                continue
            seen[tier] += 1
            length = min(len(prices), 600)
            price, pieces = ref_drum(prices, length)
            for method in ("dp", "memo"):
                plan = G.solve_drum(prices, length, method)
                self.assertEqual((plan.price, plan.pieces), (price, pieces), (cid, method))
            greedy = G.solve_drum(prices, length, "greedy")
            self.assertLessEqual(greedy.price, price, cid)
            self.assertEqual(check_cut(prices, length, greedy), [], cid)
        self.assertEqual(seen, {"M": 2, "L": 1, "X": 4})

    def test_prices_of_the_data_are_whole_numbers_from_one_up(self):
        for cid, (_tier, _no, _claim, prices) in self.drums.items():
            self.assertTrue(all(isinstance(p, int) and p >= 1 for p in prices), cid)


class OperationCounts(unittest.TestCase):
    def test_chain_dp_and_memo(self):
        for n in (1, 2, 3, 6, 12):
            dims = [3 + (i * 7) % 5 for i in range(n + 1)]
            dp, memo = G.solve_chain(dims, "dp").ops, G.solve_chain(dims, "memo").ops
            cells, candidates = n * (n - 1) // 2, (n ** 3 - n) // 6
            self.assertEqual((dp["cells"], dp["candidates"], dp["calls"]), (cells, candidates, 1), n)
            self.assertEqual((memo["cells"], memo["candidates"]), (cells, candidates), n)
            self.assertEqual(memo["calls"], 1 + 2 * candidates, n)
            self.assertEqual(dp["pre"]["items_examined"], n + 1)
            self.assertEqual((dp["enumerated"], dp["comparisons"], dp["moves"]), (0, 0, 0))

    def test_chain_brute_counts_catalan_numbers(self):
        for n in range(1, 9):
            ops = G.solve_chain([2 + i % 3 for i in range(n + 1)], "brute").ops
            self.assertEqual(ops["enumerated"], catalan(n - 1), n)

    def test_drum_dp_and_memo(self):
        for length in (1, 2, 5, 40):
            prices = [1 + k % 4 for k in range(length)]
            dp, memo = G.solve_drum(prices, length, "dp").ops, G.solve_drum(prices, length, "memo").ops
            self.assertEqual((dp["cells"], dp["candidates"], dp["calls"]), (length, length * (length + 1) // 2, 1), length)
            self.assertEqual((memo["cells"], memo["candidates"]), (length, length * (length + 1) // 2), length)
            self.assertEqual(memo["calls"], 1 + length * (length + 1) // 2, length)
            self.assertEqual(dp["pre"]["items_examined"], length)

    def test_drum_greedy_counts(self):
        ops = G.solve_drum([1 + k % 7 for k in range(16)], 16, "greedy").ops
        self.assertEqual(ops["moves"], 16 * 4)                          # merge sort of 16 pieces: 4 passes
        self.assertGreater(ops["comparisons"], 0)
        self.assertGreaterEqual(ops["items_examined"], 1)
        self.assertEqual((ops["cells"], ops["candidates"]), (0, 0))

    def test_drum_brute_counts_two_to_the_l_minus_one(self):
        for length in range(1, 12):
            ops = G.solve_drum([1 + k % 5 for k in range(length)], length, "brute").ops
            self.assertEqual(ops["enumerated"], 2 ** (length - 1), length)

    def test_ops_have_the_same_keys_for_every_outcome(self):
        keys = set(G.solve_chain([2, 3, 4]).ops)
        for plan in (G.solve_chain([5]), G.solve_chain(None), G.solve_chain([2, 3], "greedy"), G.solve_chain([2] * 30, "brute"),
                     G.solve_drum([1, 2], 0), G.solve_drum([1, 2, 3], 3, "greedy"), G.solve_drum([1] * 30, 30, "brute")):
            self.assertEqual(set(plan.ops), keys)

    def test_expired_deadline_raises_time_budget(self):
        for method in CHAIN_METHODS:
            with self.assertRaises(TimeBudgetExceeded, msg=method):
                G.solve_chain([2, 3, 4, 5, 6, 7], method, deadline=0.0)
        for method in DRUM_METHODS:
            with self.assertRaises(TimeBudgetExceeded, msg=method):
                G.solve_drum([1, 2, 3, 4, 5, 6], 6, method, deadline=0.0)

    def test_expired_deadline_raises_also_from_the_recursion_thread(self):
        with self.assertRaises(TimeBudgetExceeded):
            G.solve_drum([1] * 800, 700, "memo", deadline=0.0)

    def test_deadline_far_away_changes_nothing(self):
        for method in CHAIN_METHODS:
            self.assertEqual(G.solve_chain(CLRS_DIMS, method, deadline=1e12), G.solve_chain(CLRS_DIMS, method))
        for method in DRUM_METHODS:
            self.assertEqual(G.solve_drum(CLRS_PRICES, 10, method, deadline=1e12), G.solve_drum(CLRS_PRICES, 10, method))

    def test_cubic_and_quadratic_shape(self):
        """Doubling n must multiply the candidates by 8 and doubling L by 4 (a guard against a wrong loop range)."""
        a = G.solve_chain([2 + i % 5 for i in range(41)]).ops["candidates"]
        b = G.solve_chain([2 + i % 5 for i in range(81)]).ops["candidates"]
        self.assertAlmostEqual(b / a, 8, delta=0.5)
        a = G.solve_drum([1 + k % 5 for k in range(100)], 100).ops["candidates"]
        b = G.solve_drum([1 + k % 5 for k in range(200)], 200).ops["candidates"]
        self.assertAlmostEqual(b / a, 4, delta=0.1)


if __name__ == "__main__":
    unittest.main()
