"""Local JSON HTTP adapter for the frontend: python -m src.server."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .backend import Backend
from .models import InvalidInputError, TimeBudgetExceeded


def make_handler(backend):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, data):
            body = json.dumps(data, allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/health':
                self.reply(200, {'status': 'OK'})
            elif self.path == '/cases':
                try:
                    self.reply(200, backend.list_cases())
                except InvalidInputError as exc:
                    self.reply(422, {'status': 'INVALID', 'note': str(exc)})
            else:
                self.reply(404, {'status': 'NOT_FOUND'})

        def do_POST(self):
            methods = {f'/{name}': getattr(backend, name) for name in
                       ('case', 'route', 'network', 'campaign', 'chain', 'drum')}
            if self.path not in methods:
                self.reply(404, {'status': 'NOT_FOUND'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1024 * 1024:
                    raise InvalidInputError('request body must be 1..1048576 bytes')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise InvalidInputError('request body must be a JSON object')
                self.reply(200, methods[self.path](**data))
            except (InvalidInputError, ValueError, TypeError) as exc:
                self.reply(422, {'status': 'INVALID', 'note': str(exc)})
            except TimeBudgetExceeded as exc:
                self.reply(408, {'status': 'DNF', 'note': str(exc)})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', default='MASTER')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    with HTTPServer(('127.0.0.1', args.port), make_handler(Backend(args.master))) as server:
        print(f'LIFELINE API: http://127.0.0.1:{args.port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
