"""Small JSON-ready service layer for Adan's frontend. No frontend dependency."""
from pathlib import Path
from functools import lru_cache

from .loader import load_case, read_cases
from .campaign import run_campaign
from .modules import routes, networkplan, chains


class Backend:
    def __init__(self, master):
        self.master = Path(master)
        self._cases = lru_cache(maxsize=8)(lambda cid: load_case(self.master, cid))

    def list_cases(self):
        return read_cases(self.master)

    def case(self, case_id):
        from dataclasses import asdict
        return asdict(self._cases(case_id))

    def route(self, case_id, target, method='dijkstra', blocked=()):
        c = self._cases(case_id)
        return routes.solve(c.locations, c.roads, target, method, blocked)._asdict()

    def network(self, case_id, blocked=(), method='kruskal', reachable_only=True):
        c = self._cases(case_id)
        subset = None
        if reachable_only:
            subset = routes.solve(c.locations, c.roads, 0, blocked=blocked).reachable
        return networkplan.solve(c.locations, c.roads, method, blocked, subset)._asdict()

    def campaign(self, case_id, calendar=None, policy='optimized'):
        return run_campaign(self._cases(case_id), calendar, policy)

    def chain(self, case_id, method='dp'):
        return chains.solve_chain(self._cases(case_id).dims, method)._asdict()

    def drum(self, case_id, length=None, method='dp'):
        prices = self._cases(case_id).prices
        return chains.solve_drum(prices, len(prices) if length is None else length, method)._asdict()
