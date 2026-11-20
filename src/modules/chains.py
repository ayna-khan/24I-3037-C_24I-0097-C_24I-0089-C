"""Module G: chains and cuts (how to multiply the signal matrices, how to cut the drum).

Problem 1, matrix chain. Dimensions p0, p1, ..., pn describe n matrices A1 ... An, where Ai is
p(i-1) x p(i). A product of a p x q matrix and a q x r matrix costs p*q*r scalar multiplications.
Output: the bracketing with the fewest scalar multiplications, written as a string such as
"((A1 A2) A3)" (one matrix: "A1"; every product is in its own pair of brackets, factors separated
by one space), and its cost.

Problem 2, drum cutting. Prices price(1), ..., price(L) for the pieces of length 1..L. Output: a cut
of a drum of length L into whole pieces (lengths add up to L) with the maximum total price, as the
list of piece lengths in cutting order, and the total price.

Methods (see the README for the choice and the measurements):
  dp      primary, both problems: bottom-up dynamic programming with a split table.
          Chain: cost[i][j] = min over k of cost[i][k] + cost[k+1][j] + p(i-1) p(k) p(j), O(n^3) time,
          O(n^2) space. Drum: best[l] = max over k of price(k) + best[l-k], O(L^2) time, O(L) space.
  memo    baseline, both: the same recurrences as a memoised recursion (top-down). Same counts of
          cells and split candidates as dp, plus the recursive calls. The recursion is as deep as n
          (chain) or L (drum); `solve_*` runs it in a thread with a large stack and a raised
          recursion limit, and answers status TOO_LARGE above MEMO_MAX_DEPTH instead of crashing.
  greedy  baseline, drum only: pieces ordered by price per length (best first, compared as exact
          fractions, ties: longer piece first), each length is cut as often as it still fits. O(L log L),
          a rule of thumb that is NOT optimal (note in the plan).
  brute   baseline for small inputs: every bracketing of the chain (Catalan number of n - 1, n <= 12)
          or every cut of the drum (2^(L-1) compositions, L <= 20).

Tie rules (the same in every method and in the reference of the tests).
  * Chain: among splits of equal cost the SMALLEST split point k (the left part A_i..A_k as short as
    possible) is taken, in every sub-chain. A split is replaced only when strictly cheaper.
  * Drum: among cuts of equal total price the one with the FEWEST pieces; among those the one whose
    list of pieces (in cutting order) is lexicographically smallest, i.e. the smallest first piece, then the
    smallest second piece, and so on. In the DP this is: replace the candidate first piece only when the
    price is strictly higher, or equal with strictly fewer pieces.
  The cost or price is unique; with these rules the bracketing or the list of pieces is unique too, so
  dp, memo and brute return exactly the same answer. `greedy` is not an optimiser: it returns its own
  deterministic cut.

Contract of all methods: a bracketing's cost recomputed from the string equals the reported cost;
the pieces add up to L and their prices add up to the reported price; broken input (fewer than two
dimensions, a dimension that is not a whole number >= 1, L not a whole number >= 1, a missing or
negative or fractional price, a method that does not exist for the problem) is status 'INVALID'
with a note; a size that a method refuses (brute force above its limit, recursion deeper than
MEMO_MAX_DEPTH) is status 'TOO_LARGE' with a note. Nothing of this raises. Only a passed time budget
raises TimeBudgetExceeded (the experiment harness records it as DNF).
"""
import sys
import threading
from collections.abc import Mapping, Sequence
from time import perf_counter
from typing import NamedTuple

from ..models import InvalidInputError, TimeBudgetExceeded
from ..sorting import merge_sort

BRUTE_CHAIN_LIMIT = 12          # matrices: Catalan(11) = 58 786 bracketings
BRUTE_DRUM_LIMIT = 20           # length: 2^19 = 524 288 cuts
MEMO_MAX_DEPTH = 20000          # deepest recursion that the memoised methods accept
DEEP_THRESHOLD = 500            # recursion depth above which a thread with a large stack is used
STACK_BYTES = 128 * 1024 * 1024
CHAIN_METHODS = ("dp", "memo", "brute")
DRUM_METHODS = ("dp", "memo", "greedy", "brute")


class ChainPlan(NamedTuple):
    status: str         # 'OK', 'INVALID' or 'TOO_LARGE'
    bracketing: str     # e.g. "((A1 A2) A3)"; '' when the status is not OK
    cost: int           # scalar multiplications
    ops: dict           # operation counts, defined in the README
    note: str = ""


class CutPlan(NamedTuple):
    status: str         # 'OK', 'INVALID' or 'TOO_LARGE'
    pieces: tuple       # piece lengths in cutting order; () when the status is not OK
    price: int          # total price
    ops: dict
    note: str = ""


# ----------------------------------------------------------------- helpers
def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _new_ops():
    return {"comparisons": 0, "moves": 0, "items_examined": 0, "cells": 0, "candidates": 0,
            "enumerated": 0, "calls": 1, "pre": {"items_examined": 0}}


def _check_budget(deadline):
    if deadline is not None and perf_counter() > deadline:
        raise TimeBudgetExceeded("module G exceeded its time budget")


def validate_dims(dims):
    """The dimensions as a list of whole numbers >= 1 (at least two of them), or raise InvalidInputError."""
    if isinstance(dims, (str, bytes, Mapping)) or dims is None:
        raise InvalidInputError(f"dimensions must be a list of whole numbers, got {type(dims).__name__}")
    try:
        out = list(dims)
    except TypeError:
        raise InvalidInputError(f"dimensions must be a list of whole numbers, got {type(dims).__name__}") from None
    if len(out) < 2:
        raise InvalidInputError(f"a chain needs at least two dimensions (n >= 1 matrices), got {len(out)}")
    for i, d in enumerate(out):
        if not _is_int(d):
            raise InvalidInputError(f"dimension p{i} must be a whole number, got {d!r}")
        if d < 1:
            raise InvalidInputError(f"dimension p{i} must be >= 1, got {d}")
    return out


def validate_drum(prices, length):
    """(table, L) where table[k] is the price of length k (table[0] = 0), or raise InvalidInputError.

    `prices` is a list or tuple whose entry 0 is the price of length 1 (entries beyond `length` are not
    looked at), or a mapping {length: price}. Every price must be a whole number >= 0.
    """
    if not _is_int(length):
        raise InvalidInputError(f"the length of the drum must be a whole number, got {length!r}")
    if length < 1:
        raise InvalidInputError(f"the length of the drum must be >= 1, got {length}")
    table = [0] * (length + 1)
    if isinstance(prices, Mapping):
        for k in range(1, length + 1):
            if k not in prices:
                raise InvalidInputError(f"no price for length {k}")
            table[k] = prices[k]
    elif isinstance(prices, Sequence) and not isinstance(prices, (str, bytes)):
        if len(prices) < length:
            raise InvalidInputError(f"{len(prices)} prices given for a drum of length {length}: the price of length {len(prices) + 1} is missing")
        for k in range(1, length + 1):
            table[k] = prices[k - 1]
    else:
        raise InvalidInputError(f"prices must be a list or a mapping, got {type(prices).__name__}")
    for k in range(1, length + 1):
        if not _is_int(table[k]):
            raise InvalidInputError(f"the price of length {k} must be a whole number, got {table[k]!r}")
        if table[k] < 0:
            raise InvalidInputError(f"the price of length {k} must be >= 0, got {table[k]}")
    return table, length


def _chain_invalid(ops, note):
    return ChainPlan("INVALID", "", 0, ops, "invalid input: " + note)


def _cut_invalid(ops, note):
    return CutPlan("INVALID", (), 0, ops, "invalid input: " + note)


def _run_deep(fn, depth):
    """Call fn() so that a recursion of about `depth` frames is safe.

    Up to DEEP_THRESHOLD frames fn runs here. Deeper, the recursion limit is raised for the call and fn runs
    in a thread with a large stack, so that a deep recursion cannot overflow the C stack of the main thread.
    Raises RecursionError or RuntimeError if even that is not possible; the callers turn those into TOO_LARGE.
    """
    if depth <= DEEP_THRESHOLD:
        return fn()
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(old_limit, depth + 1000))
    old_stack = threading.stack_size()
    box = {}

    def target():
        try:
            box["value"] = fn()
        except BaseException as exc:                 # handed back to the calling thread
            box["error"] = exc

    try:
        try:
            threading.stack_size(STACK_BYTES)
        except (ValueError, RuntimeError):
            pass                                     # keep the default stack size
        worker = threading.Thread(target=target)
        worker.start()
        worker.join()
    finally:
        try:
            threading.stack_size(old_stack)
        except (ValueError, RuntimeError):
            pass
        sys.setrecursionlimit(old_limit)
    if "error" in box:
        raise box["error"]
    return box["value"]


def _bracketing(split, n):
    """The bracketing string of the split table (iteratively: no recursion, whatever n)."""
    out = []
    stack = [(1, n)]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            out.append(item)
            continue
        i, j = item
        if i == j:
            out.append(f"A{i}")
            continue
        k = split[i][j]
        stack.extend([")", (k + 1, j), " ", (i, k), "("])        # reversed: "(" is popped first
    return "".join(out)


# ------------------------------------------------------ chain: bottom-up DP
def _chain_dp(p, ops, deadline):
    _check_budget(deadline)
    n = len(p) - 1
    cost = [[0] * (n + 2) for _ in range(n + 2)]       # cost[i][j] for 1 <= i <= j <= n
    cost_t = [[0] * (n + 2) for _ in range(n + 2)]     # cost_t[j][i] = cost[i][j], for a fast inner loop
    split = [[0] * (n + 2) for _ in range(n + 2)]
    for length in range(2, n + 1):
        _check_budget(deadline)
        count = n - length + 1
        for i in range(1, count + 1):
            j = i + length - 1
            row, col = cost[i], cost_t[j]
            left, right = p[i - 1], p[j]
            best = row[i] + col[i + 1] + left * p[i] * right          # first candidate: k = i
            best_k = i
            for k in range(i + 1, j):
                c = row[k] + col[k + 1] + left * p[k] * right
                if c < best:                                          # strictly cheaper only: smallest k wins ties
                    best = c
                    best_k = k
            row[j] = col[i] = best
            split[i][j] = best_k
        ops["cells"] += count
        ops["candidates"] += count * (length - 1)
    return ChainPlan("OK", _bracketing(split, n), cost[1][n], ops,
                     "single matrix: no product" if n == 1 else "")


# ---------------------------------------------- chain: memoised recursion
def _chain_memo(p, ops, deadline):
    _check_budget(deadline)
    n = len(p) - 1
    memo = [[None] * (n + 2) for _ in range(n + 2)]
    split = [[0] * (n + 2) for _ in range(n + 2)]
    state = {"calls": 0, "cells": 0, "candidates": 0}

    def best(i, j):
        state["calls"] += 1
        if i == j:
            return 0
        known = memo[i][j]
        if known is not None:
            return known
        left, right = p[i - 1], p[j]
        top = None
        top_k = i
        for k in range(i, j):
            c = best(i, k) + best(k + 1, j) + left * p[k] * right
            if top is None or c < top:                                # strictly cheaper only: smallest k wins ties
                top = c
                top_k = k
        state["candidates"] += j - i
        state["cells"] += 1
        if state["cells"] & 0xFF == 0:
            _check_budget(deadline)
        memo[i][j] = top
        split[i][j] = top_k
        return top

    total = _run_deep(lambda: best(1, n), n + 2)
    ops["calls"] = state["calls"]
    ops["cells"] = state["cells"]
    ops["candidates"] = state["candidates"]
    return ChainPlan("OK", _bracketing(split, n), total, ops, "single matrix: no product" if n == 1 else "")


# --------------------------------------------------- chain: all bracketings
def _chain_brute(p, ops, deadline):
    n = len(p) - 1
    if n > BRUTE_CHAIN_LIMIT:
        return ChainPlan("TOO_LARGE", "", 0, ops, f"brute force is limited to {BRUTE_CHAIN_LIMIT} matrices, got {n}")
    _check_budget(deadline)

    def trees(i, j):
        """Every bracketing of Ai..Aj as (cost, text), split point ascending, left part outer loop."""
        if i == j:
            yield 0, f"A{i}"
            return
        for k in range(i, j):
            step = p[i - 1] * p[k] * p[j]
            for left_cost, left_text in trees(i, k):
                for right_cost, right_text in trees(k + 1, j):
                    yield left_cost + right_cost + step, f"({left_text} {right_text})"

    best_cost, best_text, seen = None, "", 0
    for c, text in trees(1, n):
        seen += 1
        if seen & 0xFFF == 0:
            _check_budget(deadline)
        if best_cost is None or c < best_cost:                        # first of the cheapest: the same tie rule
            best_cost, best_text = c, text
    ops["enumerated"] = seen
    return ChainPlan("OK", best_text, best_cost, ops, "single matrix: no product" if n == 1 else "")


CHAIN_FUNCS = {"dp": _chain_dp, "memo": _chain_memo, "brute": _chain_brute}


def solve_chain(dims, method="dp", deadline=None):
    """Entry point for the campaign: the bracketing of the chain with the fewest scalar multiplications.

    method 'dp' (shipped), 'memo' or 'brute' (baselines). Never raises for bad input: the plan then has
    status 'INVALID' (or 'TOO_LARGE' for a size the method refuses) and a note.
    """
    ops = _new_ops()
    if not isinstance(method, str) or method not in CHAIN_FUNCS:
        extra = " ('greedy' exists only for the drum)" if method == "greedy" else ""
        return _chain_invalid(ops, f"unknown method {method!r} for a chain; choose one of {list(CHAIN_METHODS)}{extra}")
    try:
        p = validate_dims(dims)
    except InvalidInputError as exc:
        return _chain_invalid(ops, str(exc))
    ops["pre"]["items_examined"] = len(p)
    n = len(p) - 1
    if method == "memo" and n + 2 > MEMO_MAX_DEPTH:
        return ChainPlan("TOO_LARGE", "", 0, ops, f"the memoised recursion would be {n + 2} calls deep; the limit is {MEMO_MAX_DEPTH}")
    try:
        return CHAIN_FUNCS[method](p, ops, deadline)
    except (RecursionError, RuntimeError, MemoryError) as exc:
        if isinstance(exc, TimeBudgetExceeded):
            raise
        return ChainPlan("TOO_LARGE", "", 0, ops, f"recursion failed ({type(exc).__name__}); use method 'dp'")


# --------------------------------------------------------- drum: bottom-up DP
def _drum_dp(pr, length, ops, deadline):
    _check_budget(deadline)
    best = [0] * (length + 1)
    pieces = [0] * (length + 1)
    first = [0] * (length + 1)
    for l in range(1, length + 1):
        if l & 0xFF == 0:
            _check_budget(deadline)
        top = pr[1] + best[l - 1]                    # first candidate: k = 1
        top_pieces = 1 + pieces[l - 1]
        top_k = 1
        for k in range(2, l + 1):
            v = pr[k] + best[l - k]
            if v > top:                              # strictly better price
                top = v
                top_pieces = 1 + pieces[l - k]
                top_k = k
            elif v == top and 1 + pieces[l - k] < top_pieces:     # equal price, strictly fewer pieces
                top_pieces = 1 + pieces[l - k]
                top_k = k
        best[l] = top
        pieces[l] = top_pieces
        first[l] = top_k
    ops["cells"] += length
    ops["candidates"] += length * (length + 1) // 2
    return CutPlan("OK", _pieces_from(first, length), best[length], ops)


def _pieces_from(first, length):
    out = []
    rest = length
    while rest > 0:
        k = first[rest]
        out.append(k)
        rest -= k
    return tuple(out)


# ------------------------------------------------- drum: memoised recursion
def _drum_memo(pr, length, ops, deadline):
    _check_budget(deadline)
    best = [0] * (length + 1)
    pieces = [0] * (length + 1)
    first = [0] * (length + 1)
    done = [False] * (length + 1)
    done[0] = True
    state = {"calls": 0, "cells": 0, "candidates": 0}

    def solve(l):
        state["calls"] += 1
        if done[l]:
            return
        top, top_pieces, top_k = -1, 0, 0
        for k in range(1, l + 1):
            solve(l - k)
            v = pr[k] + best[l - k]
            if v > top:
                top, top_pieces, top_k = v, 1 + pieces[l - k], k
            elif v == top and 1 + pieces[l - k] < top_pieces:
                top_pieces, top_k = 1 + pieces[l - k], k
        state["candidates"] += l
        state["cells"] += 1
        if state["cells"] & 0xFF == 0:
            _check_budget(deadline)
        best[l], pieces[l], first[l], done[l] = top, top_pieces, top_k, True

    _run_deep(lambda: solve(length), length + 2)
    ops["calls"] = state["calls"]
    ops["cells"] = state["cells"]
    ops["candidates"] = state["candidates"]
    return CutPlan("OK", _pieces_from(first, length), best[length], ops)


# ----------------------------------------------------- drum: greedy by ratio
def _ratio_before(a, b):
    """True if piece a precedes piece b: price(a)/a > price(b)/b (exact, by cross-multiplication); ties: the longer piece first."""
    left = a[1] * b[0]
    right = b[1] * a[0]
    if left != right:
        return left > right
    return a[0] > b[0]


def _drum_greedy(pr, length, ops, deadline):
    _check_budget(deadline)
    counts = {"comparisons": 0, "moves": 0}
    order = merge_sort([(k, pr[k]) for k in range(1, length + 1)], _ratio_before, counts)
    ops["comparisons"] += counts["comparisons"]
    ops["moves"] += counts["moves"]
    rest = length
    out = []
    total = 0
    for k, price in order:
        ops["items_examined"] += 1
        if k <= rest:
            m = rest // k
            out.extend([k] * m)
            total += m * price
            rest -= m * k
            if rest == 0:
                break
    return CutPlan("OK", tuple(out), total, ops,
                   "greedy by price per length: a rule of thumb, not optimal in general")


# ----------------------------------------------------- drum: all cuts
def _drum_brute(pr, length, ops, deadline):
    if length > BRUTE_DRUM_LIMIT:
        return CutPlan("TOO_LARGE", (), 0, ops, f"brute force is limited to a drum of length {BRUTE_DRUM_LIMIT}, got {length}")
    _check_budget(deadline)
    best = {"price": -1, "pieces": 0, "cut": ()}
    seen = [0]
    path = []

    def cut(rest, price):
        if rest == 0:
            seen[0] += 1
            if seen[0] & 0xFFF == 0:
                _check_budget(deadline)
            n = len(path)
            if price > best["price"] or (price == best["price"] and n < best["pieces"]):     # first of the best: lexicographic rule
                best["price"], best["pieces"], best["cut"] = price, n, tuple(path)
            return
        for k in range(1, rest + 1):
            path.append(k)
            cut(rest - k, price + pr[k])
            path.pop()

    cut(length, 0)
    ops["enumerated"] = seen[0]
    return CutPlan("OK", best["cut"], best["price"], ops)


DRUM_FUNCS = {"dp": _drum_dp, "memo": _drum_memo, "greedy": _drum_greedy, "brute": _drum_brute}


def solve_drum(prices, length, method="dp", deadline=None):
    """Entry point for the campaign: the cut of a drum of `length` with the maximum total price.

    prices[0] is the price of length 1 (or a mapping {length: price}); method 'dp' (shipped), 'memo', 'greedy'
    or 'brute' (baselines). Never raises for bad input: the plan then has status 'INVALID' (or 'TOO_LARGE' for a
    size the method refuses) and a note.
    """
    ops = _new_ops()
    if not isinstance(method, str) or method not in DRUM_FUNCS:
        return _cut_invalid(ops, f"unknown method {method!r}; choose one of {list(DRUM_METHODS)}")
    try:
        table, length = validate_drum(prices, length)
    except InvalidInputError as exc:
        return _cut_invalid(ops, str(exc))
    ops["pre"]["items_examined"] = length
    if method == "memo" and length + 2 > MEMO_MAX_DEPTH:
        return CutPlan("TOO_LARGE", (), 0, ops, f"the memoised recursion would be {length + 2} calls deep; the limit is {MEMO_MAX_DEPTH}")
    try:
        return DRUM_FUNCS[method](table, length, ops, deadline)
    except (RecursionError, RuntimeError, MemoryError) as exc:
        if isinstance(exc, TimeBudgetExceeded):
            raise
        return CutPlan("TOO_LARGE", (), 0, ops, f"recursion failed ({type(exc).__name__}); use method 'dp'")
