"""Plain data types shared by the loader, the modules and the campaign.

Every module takes and returns these small immutable records, so the data
loader (src/loader.py) and the campaign coordinator can be written without
knowing how a module works inside.
"""
from typing import NamedTuple


class InvalidInputError(ValueError):
    """The input breaks the contract of a module (negative weight, bad tick, ...)."""


class TimeBudgetExceeded(RuntimeError):
    """A run passed its time budget; the experiment harness records it as DNF."""


class Crate(NamedTuple):
    crate_id: int
    cat: int        # 0 food, 1 water, 2 medicine, 3 tools, 4 rare
    weight: int     # whole kilograms, > 0
    value: int      # value of the day, >= 0
    expiry: int
    serial: int


class Alarm(NamedTuple):
    alarm_id: int
    tick: int       # arrival tick, >= 0
    priority: int   # 1 (low) .. 10 (highest)
