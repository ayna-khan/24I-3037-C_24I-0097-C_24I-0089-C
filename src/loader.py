"""Streaming CSV loader for campaign tables; no pandas/Excel conversion.

Only requested cases are retained. Errors name the table and CSV row. Other
module tables remain on disk. File order of cases.csv defines master order.
"""
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from .models import Alarm, Crate, InvalidInputError
from .network import Location, Road
from .modules.rescue import Window

SCHEMAS = {
    'cases': 'case_id group_seed case_no tier scenario capacity target_0 target_1 target_2 edit_bound tour_length sensor_nodes sensor_k safety_vars rations_target',
    'locations': 'case_id loc_id type penalty',
    'roads': 'case_id road_no u v minutes cable',
    'waves': 'case_id wave_no road_no',
    'crates': 'case_id crate_id cat weight value expiry serial',
    'incidents': 'case_id alarm_id tick priority',
    'windows': 'case_id window_id start finish value',
    'pipeline_dims': 'case_id idx dim',
    'drum_prices': 'case_id length price',
}
TEXT = {'case_id', 'orig_case_id', 'tier', 'type', 'group_no'}


@dataclass(frozen=True)
class CaseData:
    metadata: dict
    locations: tuple
    roads: tuple
    waves: dict
    crates: tuple = ()
    alarms: tuple = ()
    windows: tuple = ()
    dims: tuple = ()
    prices: tuple = ()


def _rows(master, table, wanted=None):
    path = Path(master) / f'{table}.csv'
    try:
        with path.open(newline='', encoding='utf-8-sig') as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames or []
            if len(fields) != len(set(fields)) or not set(SCHEMAS[table].split()) <= set(fields):
                raise InvalidInputError(f'{path}: missing or duplicate columns')
            for row_no, row in enumerate(reader, 2):
                if None in row or any(value is None for value in row.values()):
                    raise InvalidInputError(f'{path}:{row_no}: wrong number of columns')
                if wanted is not None and row['case_id'] not in wanted:
                    continue
                try:
                    yield {k: (v if k in TEXT else int(v)) for k, v in row.items()}
                except ValueError as exc:
                    raise InvalidInputError(f'{path}:{row_no}: non-integer numeric cell') from exc
    except OSError as exc:
        raise InvalidInputError(f'Cannot read {path}: {exc}') from exc


def read_cases(master):
    rows = list(_rows(master, 'cases'))
    ids = [r['case_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise InvalidInputError('cases.csv: duplicate case id')
    for r in rows:
        if not r['case_id'] or r['tier'] not in ('S', 'M', 'L', 'X') or r['capacity'] < 0:
            raise InvalidInputError('cases.csv: invalid case id, tier or capacity')
    return rows


def verify_checksums(master):
    """Stream SHA-256 verification of the supplied manifest (optional, all tables)."""
    root = Path(master).resolve()
    checked = []
    try:
        for line in (root / 'CHECKSUMS.txt').read_text(encoding='utf-8-sig').splitlines():
            if not line.strip():
                continue
            digest, name = line.split(maxsplit=1)
            name = name.lstrip('*')
            path = (root / name).resolve()
            if root not in path.parents:
                raise InvalidInputError('checksum file names a file outside the dataset')
            h = hashlib.sha256()
            with path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    h.update(chunk)
            if h.hexdigest() != digest.lower():
                raise InvalidInputError(f'Checksum mismatch: {name}')
            checked.append(name)
    except (OSError, ValueError) as exc:
        raise InvalidInputError(f'Invalid checksum manifest: {exc}') from exc
    if not checked:
        raise InvalidInputError('Empty checksum manifest')
    return checked


def load_cases(master, case_ids, graph_only=False):
    wanted = set(case_ids)
    metadata = {r['case_id']: r for r in read_cases(master) if r['case_id'] in wanted}
    if wanted - metadata.keys():
        raise InvalidInputError(f'Unknown case ids: {sorted(wanted - metadata.keys())}')
    tables = ['locations', 'roads', 'waves']
    if not graph_only:
        tables += ['crates', 'incidents', 'windows', 'pipeline_dims', 'drum_prices']
    grouped = {name: {cid: [] for cid in wanted} for name in tables}
    for table in tables:
        for row in _rows(master, table, wanted):
            grouped[table][row['case_id']].append(row)
    out = {}
    for cid, meta in metadata.items():
        def rows(table):
            return grouped.get(table, {}).get(cid, [])

        waves = {}
        for r in rows('waves'):
            waves.setdefault(r['wave_no'], []).append(r['road_no'])
        dims, prices = rows('pipeline_dims'), rows('drum_prices')
        for table, values, key, start in [('pipeline_dims', dims, 'idx', 0), ('drum_prices', prices, 'length', 1)]:
            if values and sorted(r[key] for r in values) != list(range(start, start + len(values))):
                raise InvalidInputError(f'{cid}: {table} indices must be consecutive and unique')
        case = CaseData(meta,
            tuple(Location(r['loc_id'], r['type'], r['penalty']) for r in rows('locations')),
            tuple(Road(*(r[k] for k in ('road_no', 'u', 'v', 'minutes', 'cable'))) for r in rows('roads')),
            {w: tuple(ids) for w, ids in waves.items()},
            tuple(Crate(*(r[k] for k in Crate._fields)) for r in rows('crates')),
            tuple(Alarm(*(r[k] for k in Alarm._fields)) for r in rows('incidents')),
            tuple(Window(*(r[k] for k in Window._fields)) for r in rows('windows')),
            tuple(r['dim'] for r in sorted(dims, key=lambda r: r['idx'])),
            tuple(r['price'] for r in sorted(prices, key=lambda r: r['length'])))
        from .validation import validate_case
        validate_case(case, graph_only)
        out[cid] = case
    return out


def load_case(master, case_id):
    return load_cases(master, [case_id])[case_id]
