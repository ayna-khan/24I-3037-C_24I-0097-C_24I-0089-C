"""Iteration 2 input contracts and cross-table references, not Phase 1 optima."""
from .models import InvalidInputError
from .network import integer, validate
from .modules import inventory, emergencyqueue, rescue


def validate_case(case, graph_only=False):
    nodes, _ = validate(case.locations, case.roads)
    integer(case.metadata['capacity'], 'capacity')
    for key in ('target_0', 'target_1', 'target_2'):
        if case.metadata[key] not in nodes:
            raise InvalidInputError(f'{key} names an unknown location')
    used, ids = set(), {r.road_no for r in case.roads}
    for wave, roads in case.waves.items():
        integer(wave, 'wave id')  # some master groups start at wave 0
        for rid in roads:
            if rid not in ids or rid in used:
                raise InvalidInputError('unknown or repeated road in waves')
            used.add(rid)
    if graph_only:
        return
    inventory.validate_crates(case.crates, case.metadata['capacity'])
    emergencyqueue.validate_alarms(case.alarms)
    for crate in case.crates:
        integer(crate.cat, 'category')
        integer(crate.expiry, 'expiry')
        integer(crate.serial, 'serial')
        if crate.cat > 4:
            raise InvalidInputError('crate category must be 0..4')
    serials = [c.serial for c in case.crates]
    if len(set(serials)) != len(serials):
        raise InvalidInputError('duplicate crate serial')
    plan = rescue.solve(case.windows, 'count', 'greedy')
    if plan.status == 'INVALID':
        raise InvalidInputError(plan.note)
    # Validate G without solving cubic/quadratic problems during loading.
    if len(case.dims) < 2:
        raise InvalidInputError('a chain requires at least two dimensions')
    for dim in case.dims:
        integer(dim, 'dimension', 1)
    if not case.prices:
        raise InvalidInputError('missing drum prices')
    for price in case.prices:
        integer(price, 'drum price')
