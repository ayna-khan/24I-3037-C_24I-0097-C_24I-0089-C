"""Merge sort written for this project, with operation counting.

The statement does not allow a library sort to do the core work of an
evaluated algorithm, so the ordering steps of modules A and D use this one.
Counted operations follow the 'Ordering' family of Section 7.3: one key
comparison per call of `before`, and one element move per element written
into the output list.
"""


def merge_sort(items, before, counts):
    """Return a new list with `items` ordered so that earlier elements are 'before' later ones.

    `before(a, b)` must return True when a has to come strictly before b.
    The sort is stable. `counts` is a dict with the keys 'comparisons' and 'moves'.
    """
    n = len(items)
    if n < 2:
        return list(items)
    src = list(items)
    dst = [None] * n
    comparisons = 0
    moves = 0
    width = 1
    while width < n:                      # bottom-up: runs of 1, 2, 4, ...
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            i, j, k = lo, mid, lo
            while i < mid and j < hi:
                comparisons += 1
                if before(src[j], src[i]):    # take from the right only if strictly before
                    dst[k] = src[j]
                    j += 1
                else:
                    dst[k] = src[i]
                    i += 1
                k += 1
                moves += 1
            while i < mid:
                dst[k] = src[i]
                i += 1
                k += 1
                moves += 1
            while j < hi:
                dst[k] = src[j]
                j += 1
                k += 1
                moves += 1
        src, dst = dst, src
        width *= 2
    counts["comparisons"] = counts.get("comparisons", 0) + comparisons
    counts["moves"] = counts.get("moves", 0) + moves
    return src
