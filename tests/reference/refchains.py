"""Independent reference for module G. Kept apart from src/ on purpose.

Different methods from the shipped ones, with the same tie rules (see src/modules/chains.py):
  chain
    min_cost_by_merging   exhaustive search over the ORDER in which neighbouring matrices are multiplied,
                          memoised on the tuple of dimensions that is left (no split table, no intervals);
    ref_chain             cached top-down recursion on intervals that stores only costs; the bracketing is
                          rebuilt afterwards by taking the SMALLEST split point whose cost adds up to the optimum;
    evaluate_bracketing   parses a bracketing string, checks it and recomputes its cost from the dimensions.
  drum
    ref_drum              a "push" DP (a piece is added to every shorter drum) that keeps (price, number of pieces)
                          for every length; the cut is rebuilt by taking, again and again, the smallest first piece
                          that is still consistent with the optimum;
    brute_drum            every composition of the length in lexicographic order, itertools-free recursion;
    ref_greedy            greedy by price per length with fractions.Fraction and sorted().
It also holds the invariant checkers used by the tests.
"""
import sys
from fractions import Fraction
from functools import lru_cache


# --------------------------------------------------------------------------- chain
def min_cost_by_merging(dims):
    """Least number of scalar multiplications, by trying every order of multiplying neighbours (n <= 14)."""
    @lru_cache(maxsize=None)
    def best(rest):
        if len(rest) == 2:
            return 0
        out = None
        for i in range(1, len(rest) - 1):                    # multiply the matrices on both sides of rest[i]
            c = rest[i - 1] * rest[i] * rest[i + 1] + best(rest[:i] + rest[i + 1:])
            if out is None or c < out:
                out = c
        return out
    return best(tuple(dims))


def ref_chain(dims):
    """(cost, bracketing) with the tie rule 'smallest split point'."""
    p = list(dims)
    n = len(p) - 1
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old, 4 * n + 1000))
    try:
        @lru_cache(maxsize=None)
        def cost(i, j):
            if i == j:
                return 0
            return min(cost(i, k) + cost(k + 1, j) + p[i - 1] * p[k] * p[j] for k in range(i, j))

        def text(i, j):
            if i == j:
                return f"A{i}"
            for k in range(i, j):                            # smallest k first
                if cost(i, k) + cost(k + 1, j) + p[i - 1] * p[k] * p[j] == cost(i, j):
                    return "(" + text(i, k) + " " + text(k + 1, j) + ")"
            raise AssertionError("no split reaches the optimum")

        return cost(1, n), text(1, n)
    finally:
        sys.setrecursionlimit(old)


def evaluate_bracketing(dims, text):
    """Parse `text`; return its cost, or raise ValueError if it is not a valid bracketing of A1 .. An."""
    n = len(dims) - 1
    tokens, i = [], 0
    while i < len(text):
        c = text[i]
        if c in "() ":
            if c != " ":
                tokens.append(c)
            i += 1
        elif c == "A":
            j = i + 1
            while j < len(text) and text[j].isdigit():
                j += 1
            if j == i + 1:
                raise ValueError("matrix name without a number")
            tokens.append(int(text[i + 1:j]))
            i = j
        else:
            raise ValueError(f"unexpected character {c!r}")
    stack, leaves = [], []          # operands: (rows, cols, cost); '(' markers
    for t in tokens:
        if t == "(":
            stack.append("(")
        elif t == ")":
            if len(stack) < 3 or stack[-3] != "(" or "(" in (stack[-1], stack[-2]):
                raise ValueError("a bracket pair must hold exactly two factors")
            (r2, c2, k2), (r1, c1, k1) = stack.pop(), stack.pop()
            stack.pop()
            if c1 != r2:
                raise ValueError("factors do not fit")
            stack.append((r1, c2, k1 + k2 + r1 * c1 * c2))
        else:
            if not 1 <= t <= n:
                raise ValueError(f"matrix A{t} does not exist")
            leaves.append(t)
            stack.append((dims[t - 1], dims[t], 0))
    if leaves != list(range(1, n + 1)):
        raise ValueError("the matrices must appear once each, in the order A1 ... An")
    if len(stack) != 1 or stack[0] == "(":
        raise ValueError("unbalanced brackets or several results")
    if n >= 2 and not text.startswith("("):
        raise ValueError("a product must be in brackets")
    return stack[0][2]


def check_chain(dims, plan):
    """Invariants of a chain plan; returns a list of violated rules (empty list = fine)."""
    problems = []
    if plan.status != "OK":
        if plan.bracketing or plan.cost:
            problems.append("status is not OK but a bracketing or a cost is reported")
        return problems
    try:
        recomputed = evaluate_bracketing(dims, plan.bracketing)
    except ValueError as exc:
        return [f"invalid bracketing: {exc}"]
    if recomputed != plan.cost:
        problems.append(f"reported cost {plan.cost} differs from the cost {recomputed} of the bracketing")
    return problems


# --------------------------------------------------------------------------- drum
def ref_drum(prices, length):
    """(price, pieces) with the tie rule 'most price, then fewest pieces, then lexicographically smallest cut'."""
    best = [(0, 0)] + [(-1, 0)] * length                    # (price, number of pieces); -1 = not computed yet
    for l in range(length):                                 # push: add one more piece to a drum of length l
        for k in range(1, length - l + 1):
            cand = (best[l][0] + prices[k - 1], best[l][1] + 1)
            old = best[l + k]
            if cand[0] > old[0] or (cand[0] == old[0] and cand[1] < old[1]):
                best[l + k] = cand
    out, rest = [], length
    while rest > 0:                                         # rebuild: the smallest first piece that is still optimal
        for k in range(1, rest + 1):
            if (best[rest - k][0] + prices[k - 1], best[rest - k][1] + 1) == best[rest]:
                out.append(k)
                rest -= k
                break
    return best[length][0], tuple(out)


def brute_drum(prices, length):
    """The same answer by trying every composition of `length` in lexicographic order (length <= 16)."""
    best = [None]

    def go(rest, cut):
        if rest == 0:
            key = (sum(prices[k - 1] for k in cut), -len(cut))
            if best[0] is None or key > best[0][0]:         # strictly better only: the first (lexicographic) of the best stays
                best[0] = (key, tuple(cut))
            return
        for k in range(1, rest + 1):
            go(rest - k, cut + [k])

    go(length, [])
    return best[0][0][0], best[0][1]


def ref_greedy(prices, length):
    """Greedy by price per length with exact fractions; ties: the longer piece first."""
    order = sorted(range(1, length + 1), key=lambda k: (-Fraction(prices[k - 1], k), -k))
    rest, cut = length, []
    for k in order:
        if k <= rest:
            m = rest // k
            cut += [k] * m
            rest -= m * k
    return sum(prices[k - 1] for k in cut), tuple(cut)


def check_cut(prices, length, plan):
    """Invariants of a cut plan; returns a list of violated rules (empty list = fine)."""
    problems = []
    if plan.status != "OK":
        if plan.pieces or plan.price:
            problems.append("status is not OK but pieces or a price are reported")
        return problems
    pieces = list(plan.pieces)
    if not pieces:
        return ["status OK but no pieces"]
    if any(not isinstance(k, int) or k < 1 or k > length for k in pieces):
        problems.append("a piece has a length outside 1 .. L")
        return problems
    if sum(pieces) != length:
        problems.append(f"the pieces add up to {sum(pieces)}, not to {length}")
    if sum(prices[k - 1] for k in pieces) != plan.price:
        problems.append("reported price differs from the prices of the pieces")
    return problems
