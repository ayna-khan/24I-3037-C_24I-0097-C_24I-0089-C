"""Serves the static pages and Hamza's JSON API (src.server) from one origin.

src.loader reads every table from the top for each new case, about a minute on
the master dataset. The rows of one case are stored together, so FastBackend
notes once where each case starts and ends, copies just those rows to a
temporary folder and gives that folder to the unchanged loader, which still
parses and validates them.
"""
import shutil
import tempfile
import threading
from functools import lru_cache
from http.server import ThreadingHTTPServer
from pathlib import Path

from src.backend import Backend
from src.loader import SCHEMAS, load_case
from src.server import make_handler

STATIC = Path(__file__).resolve().parent / 'static'
PAGES = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
         '/style.css': ('style.css', 'text/css'), '/draw.js': ('draw.js', 'text/javascript'),
         '/app.js': ('app.js', 'text/javascript')}
TABLES = tuple(t for t in SCHEMAS if t != 'cases')


def index_table(path):
    """(header, {case_id: [(start, end), ...]}), or None if case_id is not the first column."""
    spans, last, start = {}, None, 0
    with Path(path).open('rb') as handle:
        header = handle.readline()
        if header.lstrip(b'\xef\xbb\xbf').split(b',')[0].strip() != b'case_id':
            return None
        position = handle.tell()
        for line in handle:
            key = line[:line.find(b',')]
            if key != last:
                if last is not None:
                    spans.setdefault(last.decode(), []).append((start, position))
                last, start = key, position
            position += len(line)
        if last is not None:
            spans.setdefault(last.decode(), []).append((start, position))
    return header, spans


class FastBackend(Backend):
    """Same results as Backend; only the way the rows of a case are found differs."""

    def __init__(self, master):
        super().__init__(master)
        try:
            index = {t: index_table(self.master / f'{t}.csv') for t in TABLES}
        except (OSError, UnicodeDecodeError):
            index = {}
        # Anything unexpected leaves the original (slow, fully checked) loader in place.
        if index and all(index.values()):
            self._index = index
            self._cases = lru_cache(maxsize=8)(self._load_slice)

    def _load_slice(self, case_id):
        with tempfile.TemporaryDirectory(prefix='gazette-') as temp:
            shutil.copyfile(self.master / 'cases.csv', Path(temp) / 'cases.csv')
            for table, (header, spans) in self._index.items():
                with (self.master / f'{table}.csv').open('rb') as source, \
                        (Path(temp) / f'{table}.csv').open('wb') as out:
                    out.write(header)
                    for start, end in spans.get(str(case_id), ()):
                        source.seek(start)
                        out.write(source.read(end - start))
            return load_case(temp, case_id)


def make_site_handler(backend):
    api = make_handler(backend)
    lock = threading.Lock()  # one calculation at a time, as in src.server

    class Handler(api):
        def do_GET(self):
            page = PAGES.get(self.path.split('?', 1)[0])
            if page is None:
                super().do_GET()
                return
            body = (STATIC / page[0]).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', f'{page[1]}; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            with lock:
                super().do_POST()

    return Handler


def make_server(master, port=8000):
    """Threaded so that an idle browser connection cannot block the next request."""
    if not (Path(master) / 'cases.csv').is_file():
        raise SystemExit(f'No cases.csv in {master!r}; pass --master with the dataset folder.')
    return ThreadingHTTPServer(('127.0.0.1', port), make_site_handler(FastBackend(master)))
