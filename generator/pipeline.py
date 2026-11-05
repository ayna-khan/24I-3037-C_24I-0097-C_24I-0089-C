# pipeline.py - signal pipeline dimensions and drum prices
from common import pick_size


# pipeline and drum
def make_pipeline(rng, tier):
    n = pick_size(rng, tier, "stages")
    return [rng.randint(2, 100) for _ in range(n + 1)]


def make_drum(rng, tier):
    L = pick_size(rng, tier, "drum")
    scale = rng.uniform(150, 330) / L ** 0.7
    prices = [max(1, min(500, round(scale * j ** 0.7 + rng.randint(-5, 15)))) for j in range(1, L + 1)]
    if all(prices[j - 1] * 1 == prices[0] * j for j in range(1, L + 1)):
        prices[-1] += 1                                  # prices must not be proportional to length
    return prices


def drum_best(prices):
    best = [0] * (len(prices) + 1)
    for j in range(1, len(prices) + 1):
        best[j] = max(prices[c - 1] + best[j - c] for c in range(1, j + 1))
    return best[-1]
